from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from crawlfox._transport import (
    DEFAULT_API_URL,
    batch_body,
    batch_from_envelope,
    document_from_envelope,
    resolve_api_key,
    scrape_body,
    search_body,
    search_from_envelope,
)
from crawlfox._transport import raise_or_json
from crawlfox.types import (
    BatchScrapeResult,
    Document,
    ScrapeFormat,
    SearchData,
    SearchEngine,
)


class AsyncCrawlFox:
    """Async CrawlFox client — mirrors ``CrawlFox`` with ``await``.

    Example::

        import asyncio
        from crawlfox import AsyncCrawlFox

        async def main():
            app = AsyncCrawlFox(api_key="cfx_...")
            doc = await app.scrape("https://example.com", formats=["markdown"])
            print(doc.markdown)
            await app.close()

        asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        api_url: str = DEFAULT_API_URL,
        timeout: float = 120.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = resolve_api_key(api_key)
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
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
        extract_main_content: Optional[bool] = None,
        skip_cache: Optional[bool] = None,
        zdr: Optional[bool] = None,
        timeout: Optional[int] = None,
        json_options: Optional[Dict[str, Any]] = None,
    ) -> Document:
        body = scrape_body(
            url,
            formats=formats,
            extract_main_content=extract_main_content,
            skip_cache=skip_cache,
            zdr=zdr,
            timeout=timeout,
            json_options=json_options,
        )
        return document_from_envelope(await self._post("/v1/scrape", body))

    async def batch(
        self,
        urls: List[str],
        *,
        formats: Optional[List[ScrapeFormat]] = None,
        extract_main_content: Optional[bool] = None,
        skip_cache: Optional[bool] = None,
        zdr: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> BatchScrapeResult:
        body = batch_body(
            urls,
            formats=formats,
            extract_main_content=extract_main_content,
            skip_cache=skip_cache,
            zdr=zdr,
            timeout=timeout,
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
            query,
            engine=engine,
            num=num,
            start=start,
            country=country,
            language=language,
        )
        return search_from_envelope(await self._post("/v1/search", body))

    async def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        res = await self._http().post(
            f"{self.api_url}{path}",
            json=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        return raise_or_json(res)
