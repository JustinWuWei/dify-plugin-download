from collections.abc import Generator
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

        for idx, input_url in enumerate(urls):
            url = parse_url(input_url)
            if not url:
                continue  # 跳过无效URL
            if url.scheme not in ["http", "https"]:
                continue  # 跳过不支持的URL

            file_path, mime_type, filename = download_to_temp(method="GET", url=str(url))
            try:
                downloaded_file_bytes = Path(file_path).read_bytes()
                output_filename = None
                if custom_output_filenames and idx < len(custom_output_filenames):
                    output_filename = custom_output_filenames[idx]
                yield self.create_blob_message(
                    blob=downloaded_file_bytes,
                    meta={
                        "mime_type": mime_type,
                        "filename": output_filename or filename,
                    }
                )
            finally:
                if file_path and Path(file_path).exists():
                    Path(file_path).unlink()
