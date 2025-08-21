import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import DoneAndNotDoneFutures, wait, FIRST_EXCEPTION
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.utils.download_utils import download_to_temp, handle_partial_done, handle_all_done
from tools.utils.param_utils import parse_common_params


class DownloadToTextTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        params = parse_common_params(tool_parameters)
        urls = params.urls

        if not urls or not isinstance(urls, list) or len(urls) == 0:
            raise ValueError("Missing or invalid 'url' parameter. It must be a list of URLs.")

        futures = []
        cancel_event = threading.Event()
        with ThreadPoolExecutor() as executor:
            try:
                for idx, url in enumerate(urls):
                    if not url or url.scheme not in ["http", "https"]:
                        continue

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
                        None,
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
                    handle_partial_done(cancel_event, done, not_done)
                else:
                    yield from handle_all_done(self, done, is_to_file=False)
            finally:
                # Force shutdown the executor if an exception occurs
                if executor:
                    executor.shutdown(wait=False, cancel_futures=True)
