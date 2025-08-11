import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import DoneAndNotDoneFutures, wait, FIRST_EXCEPTION
from pathlib import Path
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.utils.download_utils import download_to_temp
from tools.utils.file_utils import force_delete_path
from tools.utils.param_utils import parse_common_params


class MultipleFileDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        params = parse_common_params(tool_parameters)
        urls = params.urls
        custom_output_filenames = params.custom_output_filenames

        if not urls or not isinstance(urls, list) or len(urls) == 0:
            raise ValueError("Missing or invalid 'url' parameter. It must be a list of URLs.")

        futures = []
        cancel_event = threading.Event()
        with ThreadPoolExecutor() as executor:
            try:
                for idx, url in enumerate(urls):
                    if not url or url.scheme not in ["http", "https"]:
                        continue

                    custom_output_filename = custom_output_filenames[idx] \
                        if idx < len(custom_output_filenames) and custom_output_filenames[idx] else None

                    # print(f"{idx} : {custom_output_filename}, {url}")

                    future = executor.submit(
                        download_to_temp,
                        params.request_method,
                        str(url),
                        params.request_timeout,
                        params.ssl_certificate_verify,
                        params.request_headers,
                        params.request_body_str,
                        params.proxy_url,
                        cancel_event,
                        custom_output_filename,
                        idx=idx,
                    )
                    futures.append(future)

                # Wait for all futures to complete or for first exception to occur
                waited: DoneAndNotDoneFutures = wait(
                    futures,
                    timeout=params.request_timeout * 30,
                    return_when=FIRST_EXCEPTION)
                done = waited.done
                not_done = waited.not_done
                if not_done and len(not_done) > 0:
                    self.handle_partial_done(cancel_event, done, not_done)
                else:
                    yield from self.handle_all_done(done)
            finally:
                # Force shutdown the executor if an exception occurs
                if executor:
                    executor.shutdown(wait=False, cancel_futures=True)

    def handle_all_done(self, done) -> Generator[ToolInvokeMessage, None, None]:
        # all completed without exceptions
        sorted_done = sorted(done, key=lambda f: f.result()[0])  # sort by index
        for future in sorted_done:
            idx, file_path, mime_type, filename = future.result()
            try:
                downloaded_file_bytes = Path(file_path).read_bytes()
                yield self.create_blob_message(
                    blob=downloaded_file_bytes,
                    meta={
                        "mime_type": mime_type,
                        "filename": filename,
                    }
                )
            finally:
                # Clean up the downloaded temporary files
                force_delete_path(file_path)

    def handle_partial_done(self, cancel_event, done, not_done):
        # cancel all downloads by setting the cancel event
        cancel_event.set()
        # cancel unfinished futures
        for future in not_done:
            future.cancel()
        done_without_exception = [f for f in done if not f.exception()]
        done_with_exception = [f for f in done if f.exception()]
        # Clean up the downloaded temporary files for those that completed without exceptions
        for f in done_without_exception:
            file_path, mime_type, filename = f.result()
            force_delete_path(file_path)
        # Raise the first exception encountered in the futures
        for f in done_with_exception:
            if f.exception():
                raise f.exception()
