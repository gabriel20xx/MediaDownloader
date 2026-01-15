import time
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError, ConnectionError, ReadTimeout, ChunkedEncodingError

from .output import output, Level


def retry_request(
    url, user_agent, debug_logger, max_retries=3, sleep_time=5, base_urls=None
):
    """Perform a GET request with retries and optional base URL fallbacks.

    Always returns a `requests.Response` on success or `None` on failure so callers
    can reliably access `.content`/`.text`.
    """

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com/",
        }
    )

    def candidate_urls():
        if base_urls:
            return [urljoin(base_url, url) for base_url in base_urls]
        return [url]

    last_error = None

    for attempt in range(1, max_retries + 1):
        for candidate in candidate_urls():
            try:
                response = session.get(candidate, timeout=20)
                response.raise_for_status()
                return response
            except HTTPError as e:
                last_error = e
                status_code = e.response.status_code if e.response else "unknown"
                message = f"{candidate} returned {status_code}. Retrying ({attempt}/{max_retries})..."
                output(message, debug_logger, Level.WARNING)
            except (ConnectionError, ReadTimeout, ChunkedEncodingError) as e:
                last_error = e
                message = f"Failed to retrieve {candidate}: {e}. Retrying ({attempt}/{max_retries})..."
                output(message, debug_logger, Level.WARNING)
        time.sleep(sleep_time)

    message = (
        f"Reached the maximum number of retries ({max_retries}). Could not retrieve the page."
    )
    if last_error:
        message += f" Last error: {last_error}"
    output(message, debug_logger, Level.ERROR)
    return None
