# crawlfox-py

Official Python SDK for the [CrawlFox](https://crawlfox.io) API.

Scrape a URL into markdown (and other formats), search Google or DuckDuckGo, scrape up to 100 URLs in one call, and look up your own request logs.

Get a key from the [CrawlFox dashboard](https://crawlfox.io). Send it as `Authorization: Bearer`. Do not put keys in frontend code.

## Install

```bash
pip install crawlfox-py
```

Python 3.9+.

```bash
export CRAWLFOX_API_KEY=cfx_...
```

Or pass `api_key=` to the client. Optional `CRAWLFOX_API_URL` (default `https://api.crawlfox.io`).

## Quickstart

```python
from crawlfox import CrawlFox

app = CrawlFox()  # uses CRAWLFOX_API_KEY

doc = app.scrape("https://example.com", formats=["markdown", "links"])
print(doc.markdown)
print(doc.metadata.source_url, doc.metadata.status_code)

results = app.search("rust async tutorial", engine="google", num=10)
for hit in results.web or []:
    print(hit.position, hit.title, hit.url)

batch = app.batch(["https://example.com/", "https://example.org/"], formats=["markdown"])
print(batch.count, batch.data[0].markdown)
```

Use a context manager to close the HTTP client:

```python
with CrawlFox(api_key="cfx_...") as app:
    print(app.scrape("https://example.com").markdown)
```

Fields are snake_case on the models (`source_url`, `raw_html`, `skip_cache`). The API's camelCase is normalized for you.

## Scrape

`POST /v1/scrape`. The server renders blocked and JavaScript-heavy pages. One credit per page, including cache hits. Failed calls are free.

```python
doc = app.scrape(
    "https://example.com/",
    formats=["markdown", "html", "links"],
    skip_cache=True,
    timeout=90000,
    country="us",
    language="en",
)
```

### Formats

Default is `["markdown"]`.

| Value | Attribute |
| --- | --- |
| `markdown` | `doc.markdown` |
| `html` | `doc.html` |
| `rawHtml` | `doc.raw_html` |
| `links` | `doc.links` |
| `images` | `doc.images` |
| `emails` | `doc.emails` |
| `json` | `doc.json` (needs `json_options`) |

### Structured fields (`json`)

No separate extract endpoint. CSS selectors, deterministic, no model in the loop.

```python
doc = app.scrape(
    "https://example.com/product/42",
    formats=["json"],
    json_options={"selectors": {"title": "h1", "price": ".price"}},
)
print(doc.json)
```

Other kwargs: `skip_cache`, `timeout` (ms, default 90000, max 90000), `country`, `language`, `location`, `redact_pii`, `zdr`, `extract_main_content`.

```python
doc = app.scrape_get("https://example.com")  # GET /v1/scrape/:url
```

## Search

`POST /v1/search`. Engines: `google` (default) and `duckduckgo`. Bing is not live (`engine="bing"` returns 400).

Credits: 1 per 10 requested results. `num=20` costs 2 credits. Failed calls are free. `num` is 1 to 100. Google `start` goes up to 90.

```python
google = app.search("python asyncio", engine="google", num=10, country="us", language="en")
ddg = app.search("python asyncio", engine="duckduckgo", num=10)
```

Hits: `url`, `title`, `description`, `position`.

### Streaming search

```python
for event in app.search_stream("rust async tutorial", num=20):
    if event.type == "page":
        print(event.data)
    if event.type == "done":
        print("done", event.partial, event.credits_used)
```

## Batch scrape

`POST /v1/batch`. Up to 100 URLs. Same formats for every URL. Order preserved. One credit per successful URL. `timeout` is per URL. `json_options` is omitted.

```python
batch = app.batch(
    ["https://example.com/", "https://example.org/"],
    formats=["markdown"],
    skip_cache=False,
)
for page in batch.data:
    print(page.markdown[:80] if page.markdown else None)
```

## Logs

Free. Your own request ids only.

```python
row = app.get_log(id)
stored = app.get_log_result(id)
```

## Async

```python
import asyncio
from crawlfox import AsyncCrawlFox

async def main():
    async with AsyncCrawlFox() as app:
        doc = await app.scrape("https://example.com", formats=["markdown"])
        serp = await app.search("crawlfox", num=3)
        print(doc.markdown, len(serp.web or []))

asyncio.run(main())
```

`AsyncCrawlFox` has the same methods (`scrape`, `scrape_get`, `batch`, `search`, `search_stream`, `get_log`, `get_log_result`).

## Errors

```python
from crawlfox import CrawlFox, CrawlFoxError

try:
    CrawlFox().scrape("https://example.com")
except CrawlFoxError as e:
    print(e.status, e.code, e.retryable, e.message)
```

Retries use `502` / `503` / `504` and `retryable: true`. Stable codes include `MISSING_URL`, `INVALID_URL`, `UPSTREAM_TIMEOUT`, `BOT_WALL`, `NO_PUBLIC_CONTENT`.

OpenAPI: https://crawlfox.io/openapi.json

## Credits

No per-minute cap. Scrape is 1 credit per page. Search is 1 credit per 10 requested results.

## License

MIT.

## Docs

https://docs.crawlfox.io
