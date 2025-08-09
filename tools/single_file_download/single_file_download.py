from collections.abc import Generator
from pathlib import Path
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.utils.download_utils import download_to_temp, parse_url


class SingleFileDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        input_url = tool_parameters.get("url")
        custom_output_filename = tool_parameters.get("output_filename")
        http_timeout = float(tool_parameters.get("http_timeout", "30"))
        ssl_certificate_verify: bool = tool_parameters.get("ssl_certificate_verify", "false") == "true"
        url = parse_url(input_url)
        if not url:
            raise ValueError("Missing or invalid URL.")
        if url.scheme not in ["http", "https"]:
            raise ValueError("Invalid URL format. URL must start with 'http://' or 'https://'.")

        file_path, mime_type, filename = download_to_temp(
            method="GET", url=str(url), timeout=http_timeout,
            ssl_certificate_verify=ssl_certificate_verify)
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
