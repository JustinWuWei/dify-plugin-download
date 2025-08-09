import asyncio
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.utils.download_utils import download_to_temp, parse_url


class MultipleFileDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        urls = tool_parameters.get("urls", "").split("\n")
        custom_output_filenames = tool_parameters.get("output_filename", "").split("\n")
        if not urls or not isinstance(urls, list) or len(urls) == 0:
            raise ValueError("Missing or invalid 'urls' parameter. It must be a list of URLs.")

        def sync_download_single(idx, input_url):
            url = parse_url(input_url)
            if not url or url.scheme not in ["http", "https"]:
                return None
            file_path, mime_type, filename = download_to_temp(method="GET", url=str(url))
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
                    loop.run_in_executor(executor, sync_download_single, idx, input_url)
                    for idx, input_url in enumerate(urls)
                ]
                return await asyncio.gather(*tasks)

        results = asyncio.run(async_download_all())
        for result in results:
            if result:
                yield self.create_blob_message(blob=result["blob"], meta=result["meta"])
