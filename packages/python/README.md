# crawlfox-py

Official Python SDK for the [CrawlFox](https://crawlfox.io) scrape + search API.

## Install

```bash
pip install crawlfox-py
```

## Quickstart

```python
from crawlfox import CrawlFox

app = CrawlFox(api_key="cfx_YOUR_API_KEY")
# or: export CRAWLFOX_API_KEY=cfx_...

# Scrape → Document (Firecrawl-style)
doc = app.scrape("https://example.com", formats=["markdown", "links"])
print(doc.markdown)
print(doc.metadata.source_url, doc.metadata.status_code)

# Search → SearchData
results = app.search("crawlfox web scraping", engine="google", num=5)
for hit in results.web or []:
    print(hit.position, hit.title, hit.url)

# Batch → list of Documents
batch = app.batch(["https://example.org", "https://example.net"], formats=["markdown"])
for page in batch.data:
    print(page.markdown[:80] if page.markdown else None)
```

## Async

```python
import asyncio
from crawlfox import AsyncCrawlFox

async def main():
    async with AsyncCrawlFox(api_key="cfx_...") as app:
        doc = await app.scrape("https://example.com", formats=["markdown"])
        print(doc.markdown)
        serp = await app.search("crawlfox", num=3)
        print(len(serp.web or []))

asyncio.run(main())
```

## Return shapes

Typed models (Pydantic) with **snake_case** fields — same idea as Firecrawl:

| Method | Returns | Access |
|--------|---------|--------|
| `scrape` / `scrape_get` | `Document` | `doc.markdown`, `doc.metadata.source_url` |
| `search` | `SearchData` | `results.web[i].url` |
| `search_stream` | `SearchStreamEvent` | `event.type`, `event.data` |
| `batch` | `BatchScrapeResult` | `batch.data[i].markdown` |
| `get_log` / `get_log_result` | `LogRow` / JSON | `row.status` |

API camelCase (`sourceURL`, `rawHtml`, …) is normalized automatically.

## Errors

```python
from crawlfox import CrawlFox, CrawlFoxError

try:
    CrawlFox().scrape("https://example.com")
except CrawlFoxError as e:
    print(e.status, e.code, e.retryable, e.message)
```

## Docs

https://docs.crawlfox.io/#integrations-sdk-python
