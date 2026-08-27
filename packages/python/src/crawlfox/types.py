"""Typed response models for the CrawlFox Python SDK.

Typed models = Pydantic classes that describe the shape of API responses so
you get attribute access (`doc.markdown`) and editor autocomplete instead of
raw nested dicts (`doc["data"]["markdown"]`). Field names are snake_case,
matching Firecrawl's Python SDK.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

ScrapeFormat = Literal[
    "markdown",
    "html",
    "rawHtml",
    "raw_html",
    "text",
    "json",
    "links",
    "images",
    "emails",
]

SearchEngine = Literal["google", "bing", "duckduckgo"]


class DocumentMetadata(BaseModel):
    """Metadata for a scraped page (API camelCase normalized to snake_case)."""

    model_config = ConfigDict(extra="allow")

    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    source_url: Optional[str] = None
    url: Optional[str] = None
    status_code: Optional[int] = None
    scrape_id: Optional[str] = None
    credits_used: Optional[float] = None
    cache_state: Optional[str] = None


class Document(BaseModel):
    """A scraped document — Firecrawl-style return from ``scrape`` / batch items."""

    model_config = ConfigDict(extra="allow", protected_namespaces=())

    markdown: Optional[str] = None
    html: Optional[str] = None
    raw_html: Optional[str] = None
    text: Optional[str] = None
    # Named json_ to avoid shadowing BaseModel.json(); still accepts API key "json".
    json_: Optional[Any] = Field(default=None, validation_alias="json", serialization_alias="json")
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    emails: Optional[List[str]] = None
    metadata: Optional[DocumentMetadata] = None
    success: Optional[bool] = None
    error: Optional[str] = None

    @property
    def json(self) -> Optional[Any]:  # noqa: A003 — Firecrawl-compatible alias
        return self.json_


class SearchResultWeb(BaseModel):
    """One organic search hit."""

    model_config = ConfigDict(extra="allow")

    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None


class SearchData(BaseModel):
    """Search results — Firecrawl-style return from ``search``."""

    model_config = ConfigDict(extra="allow")

    web: Optional[List[SearchResultWeb]] = None
    credits_used: Optional[float] = None
    id: Optional[str] = None
    success: Optional[bool] = None


class BatchScrapeResult(BaseModel):
    """Batch scrape response."""

    model_config = ConfigDict(extra="allow")

    success: bool = True
    count: Optional[int] = None
    data: List[Document] = Field(default_factory=list)


class CrawlFoxError(Exception):
    """Raised when the CrawlFox API returns a non-success response."""

    def __init__(
        self,
        message: str,
        status: int,
        *,
        code: Optional[str] = None,
        retryable: Optional[bool] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.retryable = retryable
        self.body = body or {}
