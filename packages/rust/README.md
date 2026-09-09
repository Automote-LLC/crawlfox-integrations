# crawlfox (Rust)

Official Rust SDK for the [CrawlFox](https://crawlfox.io) scrape + search API.

```toml
[dependencies]
crawlfox = { git = "https://github.com/Automote-LLC/crawlfox-integrations", path = "packages/rust" }
```

Path dependency while developing:

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
    println!("{}", page.data.as_ref().and_then(|d| d.markdown.as_deref()).unwrap_or(""));

    let results = client
        .search(
            "crawlfox web scraping",
            SearchOptions {
                engine: Some("google".into()),
                num: Some(5),
                ..Default::default()
            },
        )
        .await?;
    if let Some(web) = results.data.and_then(|d| d.web) {
        for hit in web {
            println!("{} {}", hit.title.unwrap_or_default(), hit.url);
        }
    }

    let batch = client
        .batch(
            vec![
                "https://example.org".into(),
                "https://example.net".into(),
            ],
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                ..Default::default()
            },
        )
        .await?;
    for item in batch.results {
        println!("{:?}", item.data.and_then(|d| d.markdown));
    }
    Ok(())
}
```

Add `tokio` with `macros` and `rt-multi-thread` to run the example.

## Errors

```rust
match client.scrape("https://example.com", Default::default()).await {
    Err(e) => println!("{:?} {:?}", e.status(), e.code()),
    Ok(page) => println!("{:?}", page.data),
}
```

## Docs

https://docs.crawlfox.io
