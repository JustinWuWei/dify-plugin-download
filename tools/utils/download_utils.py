import os
import re
import tempfile
from typing import Optional
from urllib.parse import urlparse, unquote

from httpx import Response, Timeout, Client
from yarl import URL


def download_to_temp(method: str, url: str, timeout: int = 120) -> tuple[str, Optional[str], Optional[str]]:
    """
    Download a file to a temporary file,
    and return the file path, MIME type, and file name.
    """""
    with Client(timeout=Timeout(timeout), follow_redirects=True) as client:
        with client.stream(method, url) as response:
            try:
                response.raise_for_status()
            except Exception as e:
                raise ValueError(
                    f"Failed to download file from {url}, HTTP status code: {response.status_code}, error: {e}")

            content_type = response.headers.get('content-type', '')
            mime_type = content_type.split(';')[0].strip() if content_type else None

            filename = guess_file_name(url, response)

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file_path = temp_file.name
                # Stream the response content to the temporary file
                for chunk in response.iter_bytes():
                    temp_file.write(chunk)

    return file_path, mime_type, filename


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
