from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

import httpx

from crawlfox._transport import (
    DEFAULT_API_URL,
    batch_body,
    batch_from_envelope,
    default_headers,
    document_from_envelope,
    raise_or_json,
    require_batch_urls,
    require_query,
    require_url,
    resolve_api_key,
    resolve_api_url,
    scrape_body,
    scrape_get_path,
    search_body,
    search_from_envelope,
    with_retries,
)
from crawlfox.normalize import normalize_keys
from crawlfox.types import (
    BatchScrapeResult,
    Document,
    LogRow,
    RedactPii,
    ScrapeFormat,
    SearchData,
    SearchEngine,
    SearchStreamEvent,
)


class CrawlFox:
    """Official CrawlFox sync client (Firecrawl-style return shapes)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        api_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 2,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.api_key = resolve_api_key(api_key)
        self.api_url = resolve_api_url(api_url)
        self.timeout = timeout
        self.max_retries = max_retries
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
        formats: Optional[List[ScrapeFormat]] = None,
        skip_cache: Optional[bool] = None,
        zdr: Optional[bool] = None,
        timeout: Optional[int] = None,
        json_options: Optional[Dict[str, Any]] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        redact_pii: Optional[RedactPii] = None,
        extract_main_content: Optional[bool] = None,
    ) -> Document:
        body = scrape_body(
            require_url(url),
            formats=formats,
            skip_cache=skip_cache,
            zdr=zdr,
            timeout=timeout,
            json_options=json_options,
            country=country,
            language=language,
            location=location,
            redact_pii=redact_pii,
            extract_main_content=extract_main_content,
        )
        return document_from_envelope(self._post("/v1/scrape", body))

    def scrape_get(self, url: str) -> Document:
        return document_from_envelope(self._get(scrape_get_path(require_url(url))))

    def batch(
        self,
        urls: List[str],
        *,
        formats: Optional[List[ScrapeFormat]] = None,
        skip_cache: Optional[bool] = None,
        zdr: Optional[bool] = None,
        timeout: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        redact_pii: Optional[RedactPii] = None,
        extract_main_content: Optional[bool] = None,
    ) -> BatchScrapeResult:
        body = batch_body(
            require_batch_urls(urls),
            formats=formats,
            skip_cache=skip_cache,
            zdr=zdr,
            timeout=timeout,
            country=country,
            language=language,
            location=location,
            redact_pii=redact_pii,
            extract_main_content=extract_main_content,
        )
        return batch_from_envelope(self._post("/v1/batch", body))

    def search(
        self,
        query: str,
        *,
        engine: Optional[SearchEngine] = None,
        num: Optional[int] = None,
        start: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> SearchData:
        body = search_body(
            require_query(query),
            engine=engine,
            num=num,
            start=start,
            country=country,
            language=language,
        )
        return search_from_envelope(self._post("/v1/search", body))

    def search_stream(
        self,
        query: str,
        *,
        engine: Optional[SearchEngine] = None,
        num: Optional[int] = None,
        start: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Iterator[SearchStreamEvent]:
        import json

        body = search_body(
            require_query(query),
            engine=engine,
            num=num,
            start=start,
            country=country,
            language=language,
        )

        def send() -> httpx.Response:
            req = self._http().build_request(
                "POST",
                f"{self.api_url}/v1/search/stream",
                json=body,
                headers=default_headers(self.api_key),
            )
            res = self._http().send(req, stream=True)
            if not res.is_success:
                raise_or_json(res)
            return res

        res = with_retries(send, max_retries=self.max_retries)
        try:
            for line in res.iter_lines():
                if not line:
                    continue
                raw = json.loads(line)
                yield SearchStreamEvent.model_validate(
                    normalize_keys(raw) if isinstance(raw, dict) else raw
                )
        finally:
            res.close()

    def get_log(self, log_id: str) -> LogRow:
        return LogRow.model_validate(self._get(f"/v1/logs/{log_id}"))

    def get_log_result(self, log_id: str) -> Any:
        return self._get(f"/v1/logs/{log_id}/result")

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        def send() -> Dict[str, Any]:
            res = self._http().post(
                f"{self.api_url}{path}",
                json=body,
                headers=default_headers(self.api_key),
            )
            return raise_or_json(res)

        return with_retries(send, max_retries=self.max_retries)

    def _get(self, path: str) -> Dict[str, Any]:
        def send() -> Dict[str, Any]:
            res = self._http().get(
                f"{self.api_url}{path}",
                headers=default_headers(self.api_key),
            )
            return raise_or_json(res)

        return with_retries(send, max_retries=self.max_retries)
