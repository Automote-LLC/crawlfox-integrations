from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from crawlfox import CrawlFox, CrawlFoxError


def test_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRAWLFOX_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key required"):
        CrawlFox()


def test_scrape_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={"success": True, "data": {"markdown": "# Hi"}},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cf = CrawlFox(api_key="cfx_test", client=client)
    result = cf.scrape("https://example.com", formats=["markdown"], skip_cache=True)

    assert result["success"] is True
    assert result["data"]["markdown"] == "# Hi"
    assert captured["url"].endswith("/v1/scrape")
    assert captured["auth"] == "Bearer cfx_test"
    assert captured["body"]["url"] == "https://example.com"
    assert captured["body"]["formats"] == ["markdown"]
    assert captured["body"]["skipCache"] is True


def test_search_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"success": True, "data": {"web": [{"url": "https://x.com"}]}},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cf = CrawlFox(api_key="cfx_test", client=client)
    result = cf.search("crawlfox", engine="google", num=5)

    assert result["data"]["web"][0]["url"] == "https://x.com"
    assert captured["body"]["q"] == "crawlfox"
    assert captured["body"]["engine"] == "google"
    assert captured["body"]["num"] == 5


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

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cf = CrawlFox(api_key="cfx_test", client=client)
    with pytest.raises(CrawlFoxError) as exc:
        cf.scrape("https://example.com")
    assert exc.value.status == 429
    assert exc.value.code == "MONTHLY_QUOTA_EXCEEDED"
