"""Shared request helpers for sync and async clients."""

from __future__ import annotations

import time
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import quote

from crawlfox.normalize import normalize_keys
from crawlfox.types import (
    SDK_VERSION,
    BatchScrapeResult,
    Document,
    DocumentMetadata,
    LogRow,
    RedactPii,
    ScrapeFormat,
    SearchData,
    SearchEngine,
    SearchResultWeb,
    SearchStreamEvent,
)

DEFAULT_API_URL = "https://api.crawlfox.io"


def resolve_api_key(api_key: Optional[str]) -> str:
    import os

    key = api_key or os.environ.get("CRAWLFOX_API_KEY")
    if not key:
        raise ValueError(
            "CrawlFox API key required. Pass api_key or set CRAWLFOX_API_KEY."
        )
    return key


def default_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": f"crawlfox-py/{SDK_VERSION}",
    }


def is_retryable_error(err: Any) -> bool:
    flag = getattr(err, "retryable", None)
    if flag is False:
        return False
    if flag is True:
        return True
    return getattr(err, "status", None) in (502, 503, 504)


def wire_formats(formats: Optional[List[ScrapeFormat]]) -> Optional[List[str]]:
    if formats is None:
        return None
    out: List[str] = []
    for f in formats:
        out.append("rawHtml" if f == "raw_html" else f)
    return out


def scrape_body(
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
) -> Dict[str, Any]:
    # extract_main_content is accepted and ignored (gateway dropped the flag).
    _ = extract_main_content
    body: Dict[str, Any] = {"url": url}
    wf = wire_formats(formats)
    if wf is not None:
        body["formats"] = wf
    if skip_cache is not None:
        body["skipCache"] = skip_cache
    if zdr is not None:
        body["zdr"] = zdr
    if timeout is not None:
        body["timeout"] = timeout
    if json_options is not None:
        body["jsonOptions"] = json_options
    if country is not None:
        body["country"] = country
    if language is not None:
        body["language"] = language
    if location is not None:
        body["location"] = location
    if redact_pii is not None:
        body["redactPII"] = redact_pii
    return body


def batch_body(
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
) -> Dict[str, Any]:
    body = scrape_body(
        "",
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
    del body["url"]
    body["urls"] = urls
    return body


def search_body(
    query: str,
    *,
    engine: Optional[SearchEngine] = None,
    num: Optional[int] = None,
    start: Optional[int] = None,
    country: Optional[str] = None,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"q": query}
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
    return body


def scrape_get_path(url: str) -> str:
    return "/v1/scrape/" + quote(url, safe="")


def document_from_envelope(envelope: Dict[str, Any]) -> Document:
    norm = normalize_keys(envelope)
    assert isinstance(norm, dict)
    data = norm.get("data") if isinstance(norm.get("data"), dict) else norm
    assert isinstance(data, dict)
    meta = data.get("metadata")
    metadata = None
    if isinstance(meta, dict):
        metadata = DocumentMetadata.model_validate(meta)
    return Document(
        markdown=data.get("markdown"),
        html=data.get("html"),
        raw_html=data.get("raw_html"),
        json_=data.get("json"),
        links=data.get("links"),
        images=data.get("images"),
        emails=data.get("emails"),
        metadata=metadata,
        success=norm.get("success", True) if "success" in norm else True,
        error=norm.get("error") or data.get("error"),
    )


def search_from_envelope(envelope: Dict[str, Any]) -> SearchData:
    norm = normalize_keys(envelope)
    assert isinstance(norm, dict)
    data = norm.get("data") if isinstance(norm.get("data"), dict) else {}
    assert isinstance(data, dict)
    web_raw = data.get("web") or []
    web: List[SearchResultWeb] = []
    for item in web_raw:
        if isinstance(item, dict):
            web.append(SearchResultWeb.model_validate(item))
    return SearchData(
        web=web,
        credits_used=norm.get("credits_used"),
        id=norm.get("id"),
        success=norm.get("success", True),
    )


def raise_or_json(res: Any) -> Dict[str, Any]:
    from crawlfox.types import CrawlFoxError

    if res.is_success:
        return res.json()
    payload: Dict[str, Any] = {}
    try:
        payload = res.json()
    except Exception:
        pass
    message = payload.get("message") or payload.get("title") or getattr(
        res, "reason_phrase", "request failed"
    )
    raise CrawlFoxError(
        str(message),
        res.status_code,
        code=payload.get("code"),
        retryable=payload.get("retryable"),
        body=payload,
    )


def batch_from_envelope(envelope: Dict[str, Any]) -> BatchScrapeResult:
    norm = normalize_keys(envelope)
    assert isinstance(norm, dict)
    docs: List[Document] = []
    for item in norm.get("results") or []:
        if isinstance(item, dict):
            docs.append(document_from_envelope(item))
    return BatchScrapeResult(
        success=bool(norm.get("success", True)),
        count=norm.get("count", len(docs)),
        data=docs,
    )


def iter_ndjson_lines(text: str) -> Iterator[SearchStreamEvent]:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        import json

        raw = json.loads(stripped)
        yield SearchStreamEvent.model_validate(normalize_keys(raw) if isinstance(raw, dict) else {"type": "page"})


def with_retries(send, *, max_retries: int):
    from crawlfox.types import CrawlFoxError

    last: Optional[CrawlFoxError] = None
    attempts = max_retries + 1
    for i in range(attempts):
        try:
            return send()
        except CrawlFoxError as err:
            last = err
            if i >= attempts - 1 or not is_retryable_error(err):
                raise
            time.sleep(0.2 * (2 ** i))
    assert last is not None
    raise last
