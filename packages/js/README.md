# crawlfox

Official JavaScript and TypeScript SDK for the [CrawlFox](https://crawlfox.io) API.

Scrape a URL into markdown (and other formats), search Google or DuckDuckGo, scrape up to 100 URLs in one call, and look up your own request logs.

Get a key from the [CrawlFox dashboard](https://crawlfox.io). Send it as `Authorization: Bearer`. Create and rotate keys there. Do not put keys in frontend code.

## Install

```bash
npm install crawlfox
```

Node 18 or newer.

```bash
export CRAWLFOX_API_KEY=cfx_...
```

Or pass `apiKey` to the client. Optional `CRAWLFOX_API_URL` (default `https://api.crawlfox.io`).

## Quickstart

```ts
import { CrawlFox, CrawlFoxError } from "crawlfox";

const app = new CrawlFox(); // uses CRAWLFOX_API_KEY

const page = await app.scrape("https://example.com");
console.log(page.markdown);
console.log(page.metadata?.title, page.metadata?.statusCode);

const hits = await app.search("rust async tutorial", { engine: "google", num: 10 });
for (const hit of hits.web ?? []) {
  console.log(hit.position, hit.title, hit.url);
}

const batch = await app.batch(
  ["https://example.com/", "https://example.org/"],
  { formats: ["markdown"] },
);
console.log(batch.count, batch.data[0]?.markdown);
```

The HTTP API wraps scrape payloads in `{ success, data }`. This client unwraps that. Markdown, html, links, and metadata sit on the returned object.

## Scrape

`POST /v1/scrape`. Blocked and JavaScript-heavy pages are rendered on the server. One credit per page, including cached pages. Failed calls are free. Extra formats on the same URL do not add credits.

```ts
const page = await app.scrape("https://example.com/", {
  formats: ["markdown", "html", "links"],
  skipCache: true,
  timeout: 90000,
  country: "us",
  language: "en",
});
```

### Formats

`formats` defaults to `["markdown"]`.

| Value | Field on the document |
| --- | --- |
| `markdown` | `page.markdown` |
| `html` | `page.html` |
| `rawHtml` | `page.rawHtml` |
| `links` | `page.links` |
| `images` | `page.images` |
| `emails` | `page.emails` |
| `json` | `page.json` (needs `jsonOptions`) |

### Structured fields (`json`)

There is no separate extract endpoint. Include `"json"` in `formats` and map keys to CSS selectors. Extraction is deterministic. It does not call a model.

```ts
const page = await app.scrape("https://example.com/product/42", {
  formats: ["json"],
  jsonOptions: {
    selectors: {
      title: "h1",
      price: ".price",
      stock: { selector: "[data-stock]", attr: "data-stock" },
    },
  },
});
console.log(page.json);
```

### Other scrape options

| Option | Notes |
| --- | --- |
| `skipCache` | Fetch the page again instead of a cached result |
| `timeout` | Per-page wait in milliseconds. Default 90000. Below 1000 is rejected. Above 90000 is capped |
| `country` / `language` | Localization hints |
| `location` | `{ country, languages }` |
| `redactPII` | `true`, or `{ mode, entities, replaceStyle }` |
| `zdr` | Forwarded when you need zero data retention on the request |

### GET scrape

Lightweight markdown scrape of a percent-encoded URL (`GET /v1/scrape/:url`):

```ts
const page = await app.scrapeGet("https://example.com");
```

## Search

`POST /v1/search`. Ranked organic results in `hits.web`. Engines: `google` (default) and `duckduckgo`. `engine: "bing"` is not live yet (the API returns 400).

Credits: 1 per 10 requested results, rounded up. `num: 20` costs 2 credits, even if fewer hits come back. Failed calls are free.

```ts
const google = await app.search("python asyncio", {
  engine: "google",
  num: 10,
  start: 0,
  country: "us",
  language: "en",
});

const ddg = await app.search("python asyncio", { engine: "duckduckgo", num: 10 });
```

| Option | Notes |
| --- | --- |
| `q` | Query (first argument) |
| `engine` | `google` or `duckduckgo` |
| `num` | 1 to 100. Results arrive in pages of 10. Default 10 |
| `start` | Offset. Google supports up to 90 |
| `country` | Two-letter code, for example `us` |
| `language` | Two-letter code, for example `en` |

Each hit has `url`, `title`, `description`, and `position`.

### Streaming search

For larger `num`, `POST /v1/search/stream` sends NDJSON. Events are `page`, `done`, and `error`. A final `done` can set `partial: true` when fewer results arrive than requested.

```ts
for await (const event of app.searchStream("rust async tutorial", { num: 20 })) {
  if (event.type === "page") {
    console.log(event.data?.web?.length);
  }
  if (event.type === "done") {
    console.log("done", event.partial, event.creditsUsed);
  }
  if (event.type === "error") {
    console.error(event.code, event.message);
  }
}
```

## Batch scrape

`POST /v1/batch`. Up to 100 URLs. Same formats for every URL. Results stay in input order. One credit per successful URL. Failed URLs are free. `timeout` applies per URL, not to the whole batch. `jsonOptions` is not sent on batch.

```ts
const batch = await app.batch(
  ["https://example.com/", "https://example.org/"],
  { formats: ["markdown"], skipCache: false, timeout: 90000 },
);

for (const doc of batch.data) {
  console.log(doc.metadata?.sourceURL, doc.markdown?.slice(0, 80));
}
```

## Logs

Look up a past request you made. Log reads are free.

```ts
const row = await app.getLog(id);
console.log(row.status, row.duration_ms, row.final_outcome);

const stored = await app.getLogResult(id);
```

`getLog` is `GET /v1/logs/:id`. `getLogResult` is `GET /v1/logs/:id/result` (stored scrape body).

## Client options

```ts
const app = new CrawlFox({
  apiKey: process.env.CRAWLFOX_API_KEY,
  apiUrl: "https://api.crawlfox.io",
  timeoutMs: 120_000, // HTTP client timeout
  maxRetries: 2,
  retryBackoffMs: 200,
});
```

Retries apply to `502` / `503` / `504` and to errors the API marks `retryable: true`. Quota and validation errors are not retried.

## Credits and limits

There is no per-minute request cap. Credits are the limit.

- Scrape: 1 credit per page (cached or fresh)
- Search: 1 credit per 10 requested results (`num`)
- Failed calls: free

## Errors

Failed requests throw `CrawlFoxError` with `status`, `code`, `retryable`, and `body`. Branch on `code`. HTTP status text can change. Codes stay stable.

```ts
try {
  await app.scrape("https://example.com");
} catch (err) {
  if (err instanceof CrawlFoxError) {
    console.error(err.status, err.code, err.retryable, err.message);
  }
}
```

Examples from the API: `MISSING_URL`, `INVALID_URL`, `UPSTREAM_TIMEOUT` (retryable), `UPSTREAM_NOT_FOUND`, `BOT_WALL` (retryable), `NO_PUBLIC_CONTENT`.

OpenAPI: https://crawlfox.io/openapi.json

## Requirements

- Node 18+
- ESM and CommonJS builds (`import` / `require`)
- Types in the package (`dist/index.d.ts`)

## License

MIT. See `LICENSE` in the repo.

## Docs

- API: https://docs.crawlfox.io
- Dashboard: https://crawlfox.io
- MCP (Claude, Cursor): `https://mcp.crawlfox.io/mcp`
