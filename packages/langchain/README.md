# langchain-crawlfox

LangChain document loader and tools for [CrawlFox](https://crawlfox.io).

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
