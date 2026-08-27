from __future__ import annotations

from typing import Any, Iterator, Literal, Optional

from crawlfox import CrawlFox
from langchain_core.documents import Document
from langchain_core.document_loaders.base import BaseLoader

LoaderMode = Literal["scrape", "search"]


class CrawlFoxLoader(BaseLoader):
    """Load web pages or search results as LangChain Documents via CrawlFox."""

    def __init__(
        self,
        *,
        url: Optional[str] = None,
        query: Optional[str] = None,
        mode: LoaderMode = "scrape",
        api_key: Optional[str] = None,
        formats: Optional[list[str]] = None,
        search_num: int = 5,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        if mode == "scrape" and not url:
            raise ValueError("url is required when mode='scrape'")
        if mode == "search" and not query:
            raise ValueError("query is required when mode='search'")
        self.url = url
        self.query = query
        self.mode = mode
        self.formats = formats or ["markdown"]
        self.search_num = search_num
        self.metadata = metadata or {}
        self.client = CrawlFox(api_key=api_key)

    def lazy_load(self) -> Iterator[Document]:
        if self.mode == "scrape":
            yield from self._load_scrape()
        else:
            yield from self._load_search()

    def _load_scrape(self) -> Iterator[Document]:
        assert self.url is not None
        doc = self.client.scrape(self.url, formats=self.formats)  # type: ignore[arg-type]
        text = doc.markdown or doc.text or doc.html or ""
        meta = {**self.metadata, "source": self.url}
        if doc.metadata:
            meta.update(doc.metadata.model_dump(exclude_none=True))
        yield Document(page_content=str(text), metadata=meta)

    def _load_search(self) -> Iterator[Document]:
        assert self.query is not None
        result = self.client.search(self.query, num=self.search_num)
        for item in result.web or []:
            content = f"{item.title or ''}\n{item.description or ''}".strip() or item.url
            meta = {**self.metadata, "source": item.url, "title": item.title}
            yield Document(page_content=content, metadata=meta)
