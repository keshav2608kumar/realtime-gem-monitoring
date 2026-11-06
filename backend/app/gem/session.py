"""
GeM BidWatch — GemSession
Manages CSRF token + session cookies for bidplus.gem.gov.in.
Automatically refreshes when expired (403 response).
"""
import logging
import urllib.request
import urllib.parse
import ssl
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)


class GemSession:
    """
    Maintains a valid session with bidplus.gem.gov.in.
    Usage:
        session = GemSession()
        session.refresh()
        response = session.post(url, payload_dict)
    """

    BASE_URL = "https://bidplus.gem.gov.in"
    SESSION_INIT_URL = f"{BASE_URL}/advance-search"

    def __init__(self):
        self._csrf_token: Optional[str] = None
        self._last_refresh: float = 0
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE
        self._cookie_jar = urllib.request.HTTPCookieProcessor()
        self._opener = urllib.request.build_opener(
            self._cookie_jar,
            urllib.request.HTTPSHandler(context=self._ctx)
        )
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def refresh(self) -> None:
        """Fetch the page to get a fresh CSRF cookie + session."""
        logger.info("Refreshing GeM session...")
        req = urllib.request.Request(
            self.SESSION_INIT_URL,
            headers={**self._headers, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
        )
        with self._opener.open(req, timeout=20) as resp:
            resp.read()

        # Extract CSRF from cookie jar (most reliable)
        self._csrf_token = None
        for cookie in self._cookie_jar.cookiejar:
            if cookie.name == "csrf_gem_cookie":
                self._csrf_token = cookie.value
                break

        if not self._csrf_token:
            raise RuntimeError("Failed to extract CSRF token from GeM session")

        self._last_refresh = time.time()
        logger.info(f"Session refreshed. CSRF token: {self._csrf_token[:8]}...")

    def post(self, url: str, payload: dict, retries: int = 3) -> dict:
        """
        Make a POST request with the current session.
        Auto-refreshes session on 403.
        Returns parsed JSON dict.
        """
        import json

        if not self._csrf_token:
            self.refresh()

        for attempt in range(1, retries + 1):
            try:
                post_body = urllib.parse.urlencode({
                    "payload": json.dumps(payload),
                    "csrf_bd_gem_nk": self._csrf_token,
                }).encode("utf-8")

                post_headers = {
                    **self._headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": self.SESSION_INIT_URL,
                    "Origin": self.BASE_URL,
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                }

                req = urllib.request.Request(url, data=post_body, headers=post_headers)
                with self._opener.open(req, timeout=20) as resp:
                    return json.loads(resp.read().decode("utf-8", errors="ignore"))

            except urllib.error.HTTPError as e:
                if e.code == 403 and attempt < retries:
                    logger.warning(f"403 on attempt {attempt}, refreshing session...")
                    self.refresh()
                    time.sleep(1)
                elif e.code == 500:
                    logger.error(f"Server 500 from GeM for URL {url}")
                    raise
                else:
                    raise

        raise RuntimeError(f"Failed POST to {url} after {retries} attempts")

    def post_raw(self, url: str, form_data: dict, retries: int = 3) -> dict:
        """
        Make a POST request with raw form fields (no payload wrapping).
        Used for city-list-adv, state-list-adv, etc.
        """
        import json

        if not self._csrf_token:
            self.refresh()

        for attempt in range(1, retries + 1):
            try:
                post_body = urllib.parse.urlencode({
                    **form_data,
                    "csrf_bd_gem_nk": self._csrf_token,
                }).encode("utf-8")

                post_headers = {
                    **self._headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": self.SESSION_INIT_URL,
                    "Origin": self.BASE_URL,
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                }

                req = urllib.request.Request(url, data=post_body, headers=post_headers)
                with self._opener.open(req, timeout=20) as resp:
                    return json.loads(resp.read().decode("utf-8", errors="ignore"))

            except urllib.error.HTTPError as e:
                if e.code == 403 and attempt < retries:
                    logger.warning(f"403 on attempt {attempt}, refreshing session...")
                    self.refresh()
                    time.sleep(1)
                else:
                    raise

        raise RuntimeError(f"Failed POST to {url} after {retries} attempts")
