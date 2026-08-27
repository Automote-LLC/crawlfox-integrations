from __future__ import annotations

from typing import Any, List, Literal, Optional

from crawlfox import CrawlFox
from llama_index.core.schema import Document

ReaderMode = Literal["scrape", "search"]


class CrawlFoxWebReader:
    """Load web pages or search hits as LlamaIndex Documents via CrawlFox."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        mode: ReaderMode = "scrape",
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        self.client = CrawlFox(api_key=api_key)
        self.mode = mode
        self.params = params or {}

    def load_data(
        self,
        *,
        url: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[Document]:
        if self.mode == "scrape":
            if not url:
                raise ValueError("url is required for scrape mode")
            result = self.client.scrape(
                url,
                formats=self.params.get("formats", ["markdown"]),
                extract_main_content=self.params.get("extract_main_content"),
                skip_cache=self.params.get("skip_cache"),
            )
            data = result.get("data") or {}
            text = data.get("markdown") or data.get("text") or ""
            meta = {**(data.get("metadata") or {}), "url": url}
            return [Document(text=str(text), metadata=meta)]

        if not query:
            raise ValueError("query is required for search mode")
        result = self.client.search(
            query,
            engine=self.params.get("engine"),
            num=self.params.get("num", 5),
        )
        docs: List[Document] = []
        for item in (result.get("data") or {}).get("web") or []:
            title = item.get("title") or ""
            desc = item.get("description") or ""
            link = item.get("url") or ""
            docs.append(
                Document(
                    text=f"{title}\n{desc}".strip() or link,
                    metadata={"url": link, "title": title},
                )
            )
        return docs
