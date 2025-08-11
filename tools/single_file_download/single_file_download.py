from collections.abc import Generator
from pathlib import Path
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.utils.download_utils import download_to_temp
from tools.utils.file_utils import force_delete_path
from tools.utils.param_utils import parse_common_params


class SingleFileDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        params = parse_common_params(tool_parameters)
        url = params.urls[0] if len(params.urls) > 0 else None
        custom_output_filename = params.custom_output_filenames[0] if len(params.custom_output_filenames) > 0 else None
        if not url:
            raise ValueError("Missing or invalid URL.")
        if url.scheme not in ["http", "https"]:
            raise ValueError("Invalid URL format. URL must start with 'http://' or 'https://'.")

        file_path, mime_type, filename = download_to_temp(
            method=params.request_method,
            url=str(url),
            timeout=params.request_timeout,
            ssl_certificate_verify=params.ssl_certificate_verify,
            http_headers=params.request_headers,
            request_body=params.request_body_str,
            proxy_url=params.proxy_url,
            custom_filename=custom_output_filename,
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
            force_delete_path(file_path)
