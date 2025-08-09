import asyncio
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Mapping, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from yarl import URL

from tools.utils.download_utils import download_to_temp, parse_url
from tools.utils.param_utils import parse_json_string_dict


class MultipleFileDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        urls: list[URL] = [parse_url(s) for s in tool_parameters.get("urls", "").split("\n") if s and parse_url(s)]
        request_method: str = tool_parameters.get("request_method", "GET")
        request_timeout = float(tool_parameters.get("request_timeout", "30"))
        request_headers = parse_json_string_dict(tool_parameters.get("request_headers", "{}"))
        request_body_str: Optional[str] = tool_parameters.get("request_body_str")
        ssl_certificate_verify: bool = tool_parameters.get("ssl_certificate_verify", "false") == "true"
        custom_output_filenames = tool_parameters.get("output_filename", "").split("\n")
        if not urls or not isinstance(urls, list) or len(urls) == 0:
            raise ValueError("Missing or invalid 'urls' parameter. It must be a list of URLs.")

        def sync_download_single(idx: int,
                                 url: URL,
                                 http_timeout: float,
                                 ssl_certificate_verify: bool,
                                 http_method: str,
                                 http_headers: Mapping[str, str],
                                 request_body: str,
                                 ):
            if not url or url.scheme not in ["http", "https"]:
                return None
            file_path, mime_type, filename = download_to_temp(
                method=http_method,
                url=str(url),
                timeout=http_timeout,
                ssl_certificate_verify=ssl_certificate_verify,
                http_headers=http_headers,
                request_body=request_body,
            )
            try:
                downloaded_file_bytes = Path(file_path).read_bytes()
                output_filename = None
                if custom_output_filenames and idx < len(custom_output_filenames):
                    output_filename = custom_output_filenames[idx]
                return {
                    "blob": downloaded_file_bytes,
                    "meta": {
                        "mime_type": mime_type,
                        "filename": output_filename or filename,
                    }
                }
            finally:
                # Clean up the downloaded temporary files
                Path(file_path).unlink(missing_ok=True)

        async def async_download_all():
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                tasks = [
                    loop.run_in_executor(
                        executor, sync_download_single,
                        idx, input_url, request_timeout, ssl_certificate_verify, request_method, request_headers,
                        request_body_str,
                    )
                    for idx, input_url in enumerate(urls)
                ]
                return await asyncio.gather(*tasks)

        results = asyncio.run(async_download_all())
        for result in results:
            if result:
                yield self.create_blob_message(**result)
