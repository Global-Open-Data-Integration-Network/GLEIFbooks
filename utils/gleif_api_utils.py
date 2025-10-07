import time
import requests
from typing import Optional, Dict, Any


class GLEIFAPI:
    """
    Minimal client for GLEIF's JSON:API.

    - Reuses a single HTTP session
    - Exponential backoff on transient errors
    - Convenience methods for LEI attributes and ISINs (with pagination)
    - Helper to build summary and long-form DataFrames
    """

    def __init__(
        self,
        base_url: str = "https://api.gleif.org/api/v1",
        accept: str = "application/vnd.api+json",
        timeout: int = 30,
        retries: int = 3,
        backoff: float = 1.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Accept": accept}
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.session = requests.Session()

    def _get(self, path_or_url: str, params: Optional[Dict[str, Any]] = None):
        """
        GET with basic retries/backoff. Accepts either a full URL or a path.
        """
        url = (
            path_or_url
            if path_or_url.startswith("http")
            else f"{self.base_url}/{path_or_url.lstrip('/')}"
        )
        for i in range(self.retries):
            resp = self.session.get(
                url, headers=self.headers, params=params, timeout=self.timeout
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                time.sleep(self.backoff ** (i + 1))
                continue
            raise RuntimeError(
                f"GET {url} failed ({resp.status_code}): {resp.text[:300]}"
            )

        return {}

    def fetch_lei_attrs(self, lei: str):
        """
        Return the attributes block for a single LEI record.
        """
        payload = self._get(f"lei-records/{lei}")
        return (payload.get("data") or {}).get("attributes", {}) or {}
