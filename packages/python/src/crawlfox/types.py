"""Typed response models for the CrawlFox Python SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

SDK_VERSION = "0.1.0"

ScrapeFormat = Literal[
    "markdown",
    "html",
    "rawHtml",
    "raw_html",
    "json",
    "links",
    "images",
    "emails",
]

SearchEngine = Literal["google", "bing", "duckduckgo"]

RedactPiiMode = Literal["accurate", "aggressive", "fast"]
RedactPiiEntity = Literal["PERSON", "EMAIL", "PHONE", "LOCATION", "FINANCIAL", "SECRET"]
RedactPiiReplaceStyle = Literal["tag", "mask", "remove"]
RedactPii = Union[bool, Dict[str, Any]]


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
    content_type: Optional[str] = None
    favicon: Optional[str] = None


class Document(BaseModel):
    """A scraped document returned from ``scrape`` / batch items."""

    model_config = ConfigDict(extra="allow", protected_namespaces=())

    markdown: Optional[str] = None
    html: Optional[str] = None
    raw_html: Optional[str] = None
    json_: Optional[Any] = Field(default=None, validation_alias="json", serialization_alias="json")
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    emails: Optional[List[str]] = None
    metadata: Optional[DocumentMetadata] = None
    success: Optional[bool] = None
    error: Optional[str] = None

    @property
    def json(self) -> Optional[Any]:  # noqa: A003
        return self.json_


class SearchResultWeb(BaseModel):
    model_config = ConfigDict(extra="allow")

    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None


class SearchData(BaseModel):
    model_config = ConfigDict(extra="allow")

    web: Optional[List[SearchResultWeb]] = None
    credits_used: Optional[float] = None
    id: Optional[str] = None
    success: Optional[bool] = None


class SearchStreamEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    data: Optional[Dict[str, Any]] = None
    partial: Optional[bool] = None
    credits_used: Optional[float] = None
    id: Optional[str] = None
    code: Optional[str] = None
    message: Optional[str] = None


class BatchScrapeResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool = True
    count: Optional[int] = None
    data: List[Document] = Field(default_factory=list)


class LogRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    started_at_ms: int
    duration_ms: int
    url: Any = None
    status: int
    final_outcome: Optional[str] = None


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
