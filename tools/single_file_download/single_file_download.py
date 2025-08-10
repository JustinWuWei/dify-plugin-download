from collections.abc import Generator
from pathlib import Path
from typing import Any, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.utils.download_utils import download_to_temp, parse_url
from tools.utils.param_utils import parse_json_string_dict


class SingleFileDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        input_url = tool_parameters.get("url")
        request_method: str = tool_parameters.get("request_method", "GET")
        custom_output_filename = tool_parameters.get("output_filename")
        request_timeout = float(tool_parameters.get("request_timeout", "30"))
        request_headers = parse_json_string_dict(tool_parameters.get("request_headers"))
        request_body_str: Optional[str] = tool_parameters.get("request_body_str")
        ssl_certificate_verify: bool = tool_parameters.get("ssl_certificate_verify", "false") == "true"
        proxy_url: Optional[str] = tool_parameters.get("proxy_url")
        url = parse_url(input_url)
        if not url:
            raise ValueError("Missing or invalid URL.")
        if url.scheme not in ["http", "https"]:
            raise ValueError("Invalid URL format. URL must start with 'http://' or 'https://'.")

        file_path, mime_type, filename = download_to_temp(
            method=request_method,
            url=str(url),
            timeout=request_timeout,
            ssl_certificate_verify=ssl_certificate_verify,
            http_headers=request_headers,
            request_body=request_body_str,
            proxy_url=proxy_url,
        )
        try:
            downloaded_file_bytes = Path(file_path).read_bytes()

            yield self.create_blob_message(
                blob=downloaded_file_bytes,
                meta={
                    "mime_type": mime_type,
                    "filename": custom_output_filename or filename,
                }
            )
        finally:
            # Clean up the downloaded temporary file
            Path(file_path).unlink(missing_ok=True)
