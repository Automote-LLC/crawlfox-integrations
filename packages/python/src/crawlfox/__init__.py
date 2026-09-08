"""Official CrawlFox Python SDK."""

from crawlfox.client import CrawlFox
from crawlfox.client_async import AsyncCrawlFox
from crawlfox.types import (
    BatchScrapeResult,
    CrawlFoxError,
    Document,
    DocumentMetadata,
    LogRow,
    SearchData,
    SearchResultWeb,
    SearchStreamEvent,
)

__all__ = [
    "AsyncCrawlFox",
    "BatchScrapeResult",
    "CrawlFox",
    "CrawlFoxError",
    "Document",
    "DocumentMetadata",
    "LogRow",
    "SearchData",
    "SearchResultWeb",
    "SearchStreamEvent",
]
__version__ = "0.1.0"
