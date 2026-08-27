from __future__ import annotations

from typing import Any, Optional, Type

from crawlfox import CrawlFox
from pydantic import BaseModel, Field

try:
    # CrewAI >= 0.80 often re-exports tools from crewai.tools
    from crewai.tools import BaseTool  # type: ignore
except ImportError:
    try:
        from crewai_tools import BaseTool  # type: ignore
    except ImportError:  # pragma: no cover
        from langchain_core.tools import BaseTool  # type: ignore


class ScrapeSchema(BaseModel):
    url: str = Field(..., description="URL to scrape")


class SearchSchema(BaseModel):
    query: str = Field(..., description="Search query")
    num: int = Field(5, description="Number of results")


class CrawlFoxScrapeWebsiteTool(BaseTool):
    name: str = "CrawlFox scrape website"
    description: str = (
        "Scrape a single URL with CrawlFox and return clean markdown. "
        "Use for reading one page into an agent workflow."
    )
    args_schema: Type[BaseModel] = ScrapeSchema
    api_key: Optional[str] = None

    def _run(self, url: str) -> str:
        client = CrawlFox(api_key=self.api_key)
        doc = client.scrape(url, formats=["markdown"])
        return doc.markdown or ""


class CrawlFoxSearchTool(BaseTool):
    name: str = "CrawlFox search web"
    description: str = (
        "Search Google/Bing/DuckDuckGo via CrawlFox and return ranked organic results."
    )
    args_schema: Type[BaseModel] = SearchSchema
    api_key: Optional[str] = None

    def _run(self, query: str, num: int = 5) -> Any:
        client = CrawlFox(api_key=self.api_key)
        return client.search(query, num=num).model_dump(exclude_none=True)
