from __future__ import annotations

import os
from typing import Any, Literal, Optional

import httpx

ScrapeFormat = Literal[
    "markdown",
    "html",
    "rawHtml",
    "text",
    "json",
    "links",
    "images",
    "emails",
]

SearchEngine = Literal["google", "bing", "duckduckgo"]

DEFAULT_API_URL = "https://api.crawlfox.io"


class CrawlFoxError(Exception):
    """Raised when the CrawlFox API returns a non-success response."""

    def __init__(
        self,
        message: str,
        status: int,
        *,
        code: Optional[str] = None,
        retryable: Optional[bool] = None,
        body: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.retryable = retryable
        self.body = body or {}


class CrawlFox:
    """Official CrawlFox client for scrape, batch, and search."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        api_url: str = DEFAULT_API_URL,
        timeout: float = 120.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("CRAWLFOX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CrawlFox API key required. Pass api_key or set CRAWLFOX_API_KEY."
            )
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self._client = client
        self._owns_client = client is None

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "CrawlFox":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def scrape(
        self,
        url: str,
        *,
        formats: Optional[list[ScrapeFormat]] = None,
        extract_main_content: Optional[bool] = None,
        skip_cache: Optional[bool] = None,
        zdr: Optional[bool] = None,
        timeout: Optional[int] = None,
        json_options: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"url": url}
        if formats is not None:
            body["formats"] = formats
        if extract_main_content is not None:
            body["extractMainContent"] = extract_main_content
        if skip_cache is not None:
            body["skipCache"] = skip_cache
        if zdr is not None:
            body["zdr"] = zdr
        if timeout is not None:
            body["timeout"] = timeout
        if json_options is not None:
            body["jsonOptions"] = json_options
        return self._post("/v1/scrape", body)

    def batch(
        self,
        urls: list[str],
        *,
        formats: Optional[list[ScrapeFormat]] = None,
        extract_main_content: Optional[bool] = None,
        skip_cache: Optional[bool] = None,
        zdr: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"urls": urls}
        if formats is not None:
            body["formats"] = formats
        if extract_main_content is not None:
            body["extractMainContent"] = extract_main_content
        if skip_cache is not None:
            body["skipCache"] = skip_cache
        if zdr is not None:
            body["zdr"] = zdr
        if timeout is not None:
            body["timeout"] = timeout
        return self._post("/v1/batch", body)

    def search(
        self,
        q: str,
        *,
        engine: Optional[SearchEngine] = None,
        num: Optional[int] = None,
        start: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"q": q}
        if engine is not None:
            body["engine"] = engine
        if num is not None:
            body["num"] = num
        if start is not None:
            body["start"] = start
        if country is not None:
            body["country"] = country
        if language is not None:
            body["language"] = language
        return self._post("/v1/search", body)

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        res = self._http().post(
            f"{self.api_url}{path}",
            json=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        if res.is_success:
            return res.json()
        payload: dict[str, Any] = {}
        try:
            payload = res.json()
        except Exception:
            pass
        message = payload.get("message") or payload.get("title") or res.reason_phrase
        raise CrawlFoxError(
            str(message),
            res.status_code,
            code=payload.get("code"),
            retryable=payload.get("retryable"),
            body=payload,
        )
