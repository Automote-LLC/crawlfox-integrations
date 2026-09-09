# crawlfox (Rust)

Official Rust SDK for the [CrawlFox](https://crawlfox.io) API.

Scrape a URL, search Google or DuckDuckGo, batch up to 100 URLs, stream search, and read logs.

Get a key from the [dashboard](https://crawlfox.io). Set `CRAWLFOX_API_KEY` or pass `api_key`.

```toml
[dependencies]
crawlfox = { git = "https://github.com/Automote-LLC/crawlfox-integrations", path = "packages/rust" }
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
```

While developing against a checkout:

```toml
crawlfox = { path = "../crawlfox-integrations/packages/rust" }
```

## Quickstart

```rust
use crawlfox::{Client, ClientOptions, ScrapeOptions, SearchOptions};

#[tokio::main]
async fn main() -> Result<(), crawlfox::Error> {
    let client = Client::new(ClientOptions {
        api_key: std::env::var("CRAWLFOX_API_KEY").ok(),
        ..Default::default()
    })?;

    let page = client
        .scrape(
            "https://example.com",
            ScrapeOptions {
                formats: Some(vec!["markdown".into(), "links".into()]),
                ..Default::default()
            },
        )
        .await?;
    println!("{}", page.markdown.as_deref().unwrap_or(""));

    let results = client
        .search(
            "rust async tutorial",
            SearchOptions {
                engine: Some("google".into()),
                num: Some(10),
                ..Default::default()
            },
        )
        .await?;
    for hit in results.web.unwrap_or_default() {
        println!("{} {}", hit.title.unwrap_or_default(), hit.url);
    }

    let batch = client
        .batch(
            vec!["https://example.com/".into(), "https://example.org/".into()],
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                ..Default::default()
            },
        )
        .await?;
    for doc in batch.data {
        println!("{:?}", doc.markdown);
    }
    Ok(())
}
```

`scrape` returns a `Document` (fields on the struct). `search` returns `SearchData` with `web`. `batch` returns `BatchScrapeResult` with `data`.

## Scrape

Formats: `markdown`, `html`, `rawHtml`, `json`, `links`, `images`, `emails`. Default markdown.

`json_options` is a JSON value of CSS selectors when you include `"json"`. There is no separate extract endpoint.

Also: `skip_cache`, `timeout` (ms), `country`, `language`, `location`, `redact_pii`, `zdr`.

```rust
let page = client.scrape_get("https://example.com").await?;
```

## Search

Engines: `google`, `duckduckgo`. `num` 1 to 100. `start` for offset. Credits: 1 per 10 requested results.

`search_stream` returns NDJSON events (`page` / `done` / `error`).

## Logs

```rust
let row = client.get_log(id).await?;
let stored = client.get_log_result(id).await?;
```

## Errors

```rust
match client.scrape("https://example.com", Default::default()).await {
    Err(e) => println!("{:?} {:?}", e.status(), e.code()),
    Ok(page) => println!("{:?}", page.markdown),
}
```

Retries on 502/503/504 and `retryable: true`.

## Docs

https://docs.crawlfox.io
