from __future__ import annotations

from typing import Any, Optional, Type

from crawlfox import CrawlFox
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ScrapeInput(BaseModel):
    url: str = Field(description="Fully-qualified URL to scrape")


class SearchInput(BaseModel):
    query: str = Field(description="Search query")
    num: int = Field(default=5, description="Number of results (1-100)")


class CrawlFoxScrape(BaseTool):
    name: str = "crawlfox_scrape"
    description: str = "Scrape a web page and return clean markdown via CrawlFox."
    args_schema: Type[BaseModel] = ScrapeInput
    api_key: Optional[str] = None

    def _run(self, url: str) -> dict[str, Any]:
        client = CrawlFox(api_key=self.api_key)
        doc = client.scrape(url, formats=["markdown"])
        return doc.model_dump(exclude_none=True)


class CrawlFoxSearch(BaseTool):
    name: str = "crawlfox_search"
    description: str = "Search the web and return organic results via CrawlFox."
    args_schema: Type[BaseModel] = SearchInput
    api_key: Optional[str] = None

    def _run(self, query: str, num: int = 5) -> dict[str, Any]:
        client = CrawlFox(api_key=self.api_key)
        return client.search(query, num=num).model_dump(exclude_none=True)
