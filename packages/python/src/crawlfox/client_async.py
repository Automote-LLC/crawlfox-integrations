from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from crawlfox._transport import (
    DEFAULT_API_URL,
    batch_body,
    batch_from_envelope,
    default_headers,
    document_from_envelope,
    is_retryable_error,
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
)
from crawlfox.normalize import normalize_keys
from crawlfox.types import (
    BatchScrapeResult,
    CrawlFoxError,
    Document,
    LogRow,
    RedactPii,
    ScrapeFormat,
    SearchData,
    SearchEngine,
    SearchStreamEvent,
)


class AsyncCrawlFox:
    """Async CrawlFox client. Same methods as ``CrawlFox``, used with ``await``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        api_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 2,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = resolve_api_key(api_key)
        self.api_url = resolve_api_url(api_url)
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = client
        self._owns_client = client is None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncCrawlFox":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def scrape(
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
        return document_from_envelope(await self._post("/v1/scrape", body))

    async def scrape_get(self, url: str) -> Document:
        return document_from_envelope(await self._get(scrape_get_path(require_url(url))))

    async def batch(
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
        return batch_from_envelope(await self._post("/v1/batch", body))

    async def search(
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
        return search_from_envelope(await self._post("/v1/search", body))

    async def search_stream(
        self,
        query: str,
        *,
        engine: Optional[SearchEngine] = None,
        num: Optional[int] = None,
        start: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> AsyncIterator[SearchStreamEvent]:
        body = search_body(
            require_query(query),
            engine=engine,
            num=num,
            start=start,
            country=country,
            language=language,
        )
        req = self._http().build_request(
            "POST",
            f"{self.api_url}/v1/search/stream",
            json=body,
            headers=default_headers(self.api_key),
        )
        res = await self._http().send(req, stream=True)
        try:
            if not res.is_success:
                raise_or_json(res)
            async for line in res.aiter_lines():
                if not line:
                    continue
                raw = json.loads(line)
                yield SearchStreamEvent.model_validate(
                    normalize_keys(raw) if isinstance(raw, dict) else raw
                )
        finally:
            await res.aclose()

    async def get_log(self, log_id: str) -> LogRow:
        return LogRow.model_validate(await self._get(f"/v1/logs/{log_id}"))

    async def get_log_result(self, log_id: str) -> Any:
        return await self._get(f"/v1/logs/{log_id}/result")

    async def _retry(self, send):
        last: Optional[CrawlFoxError] = None
        attempts = self.max_retries + 1
        for i in range(attempts):
            try:
                return await send()
            except CrawlFoxError as err:
                last = err
                if i >= attempts - 1 or not is_retryable_error(err):
                    raise
                await asyncio.sleep(0.2 * (2 ** i))
            except httpx.RequestError as err:
                last = CrawlFoxError(str(err), 0, retryable=True)
                if i >= attempts - 1:
                    raise last
                await asyncio.sleep(0.2 * (2 ** i))
        assert last is not None
        raise last

    async def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        async def send() -> Dict[str, Any]:
            res = await self._http().post(
                f"{self.api_url}{path}",
                json=body,
                headers=default_headers(self.api_key),
            )
            return raise_or_json(res)

        return await self._retry(send)

    async def _get(self, path: str) -> Dict[str, Any]:
        async def send() -> Dict[str, Any]:
            res = await self._http().get(
                f"{self.api_url}{path}",
                headers=default_headers(self.api_key),
            )
            return raise_or_json(res)

        return await self._retry(send)
