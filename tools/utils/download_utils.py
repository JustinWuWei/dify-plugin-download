import os
import re
import tempfile
import threading
from typing import Optional, Mapping
from urllib.parse import urlparse, unquote

from httpx import Response, Client, Limits
from yarl import URL

from tools.utils.file_utils import force_delete_path


class ClientHolder:
    default_client: Client

    def __init__(self):
        self.default_client = Client(
            http2=True,
            follow_redirects=True,
            verify=True,
            default_encoding="utf-8",
            proxy=None,
            limits=Limits(max_connections=200, max_keepalive_connections=50, keepalive_expiry=60),
        )

    def get_client(self, proxy_url: Optional[str], ssl_certificate_verify: bool) -> tuple[Client, bool]:
        """
        :param proxy_url:
        :param ssl_certificate_verify:
        :return:
            Client: httpx client
            bool: whether should be manually closed after use
        """
        if proxy_url or not ssl_certificate_verify:
            return Client(
                http2=True,
                follow_redirects=True,
                verify=ssl_certificate_verify,
                default_encoding="utf-8",
                proxy=proxy_url,
            ), True
        else:
            # should not be closed manually after use as its shared default client
            return self.default_client, False


client_holder = ClientHolder()


def download_to_temp(method: str, url: str,
                     timeout: float = 5.0,
                     ssl_certificate_verify: bool = True,
                     http_headers: Mapping[str, str] = None,
                     request_body: Optional[str] = None,
                     proxy_url: Optional[str] = None,
                     cancel_event: threading.Event = None,
                     custom_filename: Optional[str] = None,
                     idx: int = 0,
                     ) -> tuple[int, Optional[str], Optional[str], Optional[str]]:
    """
    Download a file to a temporary file,
    and return the file path, MIME type, and file name.
    """""
    client, should_close_client = client_holder.get_client(proxy_url, ssl_certificate_verify)
    try:
        with client.stream(
                method=method,
                url=url,
                headers=http_headers,
                timeout=timeout,
                content=request_body.encode("utf-8") if request_body else None,
        ) as response:
            try:
                response.raise_for_status()
            except Exception as e:
                raise ValueError(
                    f"Failed to download file from {url}, HTTP status code: {response.status_code}, error: {e}")

            # check if the download is cancelled
            if cancel_event and cancel_event.is_set():
                return idx, None, None, None

            content_type = response.headers.get('content-type')
            mime_type: Optional[str] = content_type.split(';')[0].strip() if content_type else None

            filename = custom_filename or guess_file_name(url, response)

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file_path = temp_file.name
                try:
                    # Stream the response content to the temporary file
                    for chunk in response.iter_bytes(chunk_size=8192):
                        # check if the download is cancelled
                        if cancel_event and cancel_event.is_set():
                            return idx, None, None, None

                        temp_file.write(chunk)
                except:
                    force_delete_path(file_path)
                    file_path = None
                finally:
                    temp_file.close()

        return idx, file_path, mime_type, filename
    finally:
        if should_close_client:
            client.close()


def guess_file_name(url: str, response: Response) -> Optional[str]:
    filename = None

    # Get filename from possible Content-Disposition header
    content_disposition = response.headers.get('content-disposition', '')
    if content_disposition:
        # Expected value：filename="example.txt"
        match = re.search(r'filename\*?=["\']?(?:.*\')?([^"\';]+)["\']?', content_disposition, re.IGNORECASE)
        if match:
            filename = unquote(match.group(1).strip())

    # Parsing URL to get the filename if not found in headers
    if not filename:
        parsed = urlparse(url)
        path = parsed.path
        if path:
            filename = unquote(os.path.basename(path))

    return filename


def parse_url(url: str) -> Optional[URL]:
    """
    Parse a URL and return a yarl.URL object or None if parsing fails.
    """
    try:
        return URL(url)
    except ValueError as e:
        return None
