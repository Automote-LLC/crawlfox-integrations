# crawlfox

Official JavaScript / TypeScript SDK for the [CrawlFox](https://crawlfox.io) scrape and search API.

There is no crawl or sitemap endpoint on CrawlFox today. This client covers what the gateway actually ships: scrape, batch scrape, search, and request logs.

## Install

```bash
npm install crawlfox
```

Node 18+. Set `CRAWLFOX_API_KEY` or pass `apiKey`. Optional `CRAWLFOX_API_URL` (default `https://api.crawlfox.io`).

## Quickstart

```ts
import { CrawlFox, CrawlFoxError } from "crawlfox";

const app = new CrawlFox(); // or { apiKey: "cfx_..." }

const page = await app.scrape("https://example.com");
console.log(page.markdown); // Document fields sit on the object (Firecrawl-style)

const hits = await app.search("crawlfox", { engine: "google", num: 5 });
console.log(hits.web?.[0]?.url);

const batch = await app.batch(["https://example.org"], { formats: ["markdown"] });
console.log(batch.data[0]?.markdown);
```

## Options

```ts
await app.scrape("https://example.com", {
  formats: ["markdown", "links", "html"],
  skipCache: true,
  country: "us",
  language: "en",
  redactPII: true,
});
```

`formats` defaults to `["markdown"]`. Batch accepts at most 100 URLs.

## Errors

Failed requests throw `CrawlFoxError` (`status`, `code`, `retryable`). Quota `429` is **not** retried. `502`/`503`/`504` and `{ retryable: true }` are retried with exponential backoff.

```ts
try {
  await app.scrape("https://example.com");
} catch (err) {
  if (err instanceof CrawlFoxError) {
    console.error(err.status, err.code, err.retryable);
  }
}
```

## Other methods

- `scrapeGet(url)` — `GET /v1/scrape/:url`
- `searchStream(q, opts)` — NDJSON `page` / `done` / `error`
- `getLog(id)` / `getLogResult(id)` — your own request logs

## Docs

https://docs.crawlfox.io
