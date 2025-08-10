import concurrent
import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import DoneAndNotDoneFutures
from pathlib import Path
from typing import Any, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from yarl import URL

from tools.utils.download_utils import download_to_temp, parse_url
from tools.utils.param_utils import parse_json_string_dict


class MultipleFileDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        urls: list[URL] = [parse_url(s) for s in tool_parameters.get("url", "").split("\n") if s and parse_url(s)]
        request_method: str = tool_parameters.get("request_method", "GET")
        request_timeout = float(tool_parameters.get("request_timeout", "30"))
        request_headers = parse_json_string_dict(tool_parameters.get("request_headers"))
        request_body_str: Optional[str] = tool_parameters.get("request_body_str")
        ssl_certificate_verify: bool = tool_parameters.get("ssl_certificate_verify", "false") == "true"
        custom_output_filenames = tool_parameters.get("output_filename", "").split("\n")
        proxy_url: Optional[str] = tool_parameters.get("proxy_url")
        if not urls or not isinstance(urls, list) or len(urls) == 0:
            raise ValueError("Missing or invalid 'urls' parameter. It must be a list of URLs.")

        with ThreadPoolExecutor() as executor:
            try:
                futures = []
                cancel_event = threading.Event()
                for idx, url in enumerate(urls):
                    if not url or url.scheme not in ["http", "https"]:
                        continue

                    custom_output_filename = custom_output_filenames[idx] \
                        if idx < len(custom_output_filenames) and custom_output_filenames[idx] else None

                    future = executor.submit(download_to_temp,
                                             request_method,
                                             str(url),
                                             request_timeout,
                                             ssl_certificate_verify,
                                             request_headers,
                                             request_body_str,
                                             proxy_url,
                                             cancel_event)
                    futures.append(future)

                waited: DoneAndNotDoneFutures = concurrent.futures.wait(
                    futures,
                    timeout=request_timeout * 10,
                    return_when=concurrent.futures.FIRST_EXCEPTION)
                done = waited.done
                not_done = waited.not_done

                if len(not_done) > 0:

                    print(f"{len(not_done)} of {len(futures)} URLs failed to download.")
                    cancel_event.set()

                    # cancel unfinished futures
                    for future in not_done:
                        future.cancel()

                    done_without_exception = [f for f in done if not f.exception()]
                    done_with_exception = [f for f in done if f.exception()]

                    for f in done_without_exception:
                        file_path, mime_type, filename = f.result()
                        Path(file_path).unlink()

                    for f in done_with_exception:
                        if f.exception():
                            raise f.exception()
                else:
                    for future in done:
                        file_path, mime_type, filename = future.result()
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
                            # Clean up the downloaded temporary files
                            Path(file_path).unlink(missing_ok=True)
            finally:
                # Force shutdown the executor if an exception occurs
                if executor:
                    executor.shutdown(wait=False, cancel_futures=True)
