from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from crawlfox import AsyncCrawlFox, CrawlFox, CrawlFoxError, Document, SearchData


def test_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRAWLFOX_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key required"):
        CrawlFox()


def test_scrape_returns_document() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "markdown": "# Hi",
                    "rawHtml": "<html></html>",
                    "metadata": {
                        "sourceURL": "https://example.com",
                        "statusCode": 200,
                        "scrapeId": "abc",
                        "creditsUsed": 1.0,
                        "cacheState": "miss",
                    },
                },
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cf = CrawlFox(api_key="cfx_test", client=client)
    doc = cf.scrape(
        "https://example.com",
        formats=["markdown"],
        skip_cache=True,
        country="de",
        redact_pii=True,
    )

    assert isinstance(doc, Document)
    assert doc.markdown == "# Hi"
    assert doc.raw_html == "<html></html>"
    assert doc.metadata is not None
    assert doc.metadata.source_url == "https://example.com"
    assert doc.metadata.status_code == 200
    assert doc.metadata.cache_state == "miss"
    assert captured["url"].endswith("/v1/scrape")
    assert captured["auth"] == "Bearer cfx_test"
    assert captured["body"]["skipCache"] is True
    assert captured["body"]["country"] == "de"
    assert captured["body"]["redactPII"] is True


def test_retries_then_succeeds() -> None:
    hits = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        hits["n"] += 1
        if hits["n"] == 1:
            return httpx.Response(
                429,
                json={"code": "RATE_LIMIT_EXCEEDED", "message": "slow", "retryable": True},
            )
        return httpx.Response(200, json={"success": True, "data": {"markdown": "# ok"}})

    cf = CrawlFox(
        api_key="cfx_test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    doc = cf.scrape("https://example.com")
    assert doc.markdown == "# ok"
    assert hits["n"] == 2


def test_search_stream() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text='{"type":"page","data":{"web":[{"url":"https://a.com"}]}}\n{"type":"done","creditsUsed":1}\n',
        )

    cf = CrawlFox(
        api_key="cfx_test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    events = list(cf.search_stream("q", num=20))
    assert events[0].type == "page"
    assert events[1].type == "done"
    assert events[1].credits_used == 1


def test_get_log() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/v1/logs/abc")
        return httpx.Response(
            200,
            json={
                "id": "abc",
                "started_at_ms": 1,
                "duration_ms": 2,
                "url": "https://example.com",
                "status": 200,
            },
        )

    cf = CrawlFox(
        api_key="cfx_test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    row = cf.get_log("abc")
    assert row.status == 200


def test_search_returns_search_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["q"] == "crawlfox"
        assert body["num"] == 5
        return httpx.Response(
            200,
            json={
                "success": True,
                "creditsUsed": 1,
                "id": "serp_1",
                "data": {"web": [{"url": "https://x.com", "title": "X", "position": 1}]},
            },
        )

    transport = httpx.MockTransport(handler)
    cf = CrawlFox(api_key="cfx_test", client=httpx.Client(transport=transport))
    result = cf.search("crawlfox", engine="google", num=5)

    assert isinstance(result, SearchData)
    assert result.web is not None and result.web[0].url == "https://x.com"
    assert result.credits_used == 1
    assert result.id == "serp_1"


def test_batch_returns_documents() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
                "count": 1,
                "results": [
                    {"success": True, "data": {"markdown": "# A", "metadata": {"statusCode": 200}}}
                ],
            },
        )

    cf = CrawlFox(
        api_key="cfx_test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    batch = cf.batch(["https://example.org"], formats=["markdown"])
    assert batch.success
    assert len(batch.data) == 1
    assert batch.data[0].markdown == "# A"
    assert batch.data[0].metadata is not None
    assert batch.data[0].metadata.status_code == 200


def test_error_response() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={
                "code": "MONTHLY_QUOTA_EXCEEDED",
                "message": "Quota exceeded",
                "retryable": False,
            },
        )

    cf = CrawlFox(
        api_key="cfx_test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(CrawlFoxError) as exc:
        cf.scrape("https://example.com")
    assert exc.value.status == 429
    assert exc.value.code == "MONTHLY_QUOTA_EXCEEDED"


@pytest.mark.asyncio
async def test_async_scrape() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "data": {"markdown": "# Async"}},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        app = AsyncCrawlFox(api_key="cfx_test", client=http)
        doc = await app.scrape("https://example.com", formats=["markdown"])
        assert doc.markdown == "# Async"
