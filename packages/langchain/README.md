# langchain-crawlfox

LangChain document loader and tools backed by CrawlFox scrape and search.

```bash
pip install langchain-crawlfox crawlfox-py
```

```python
from langchain_crawlfox import CrawlFoxLoader, CrawlFoxScrape, CrawlFoxSearch

docs = CrawlFoxLoader(url="https://example.com", mode="scrape").load()
print(docs[0].page_content)

scrape = CrawlFoxScrape()
search = CrawlFoxSearch()
```

Set `CRAWLFOX_API_KEY`. Loader `mode="scrape"` fetches one URL as markdown.

Docs: https://docs.crawlfox.io
