use std::time::Duration;

use crawlfox::{Client, ClientOptions, ScrapeOptions, SearchOptions};
use serde_json::json;

fn client() -> Option<Client> {
    let key = std::env::var("CRAWLFOX_API_KEY").ok()?;
    Some(
        Client::new(ClientOptions {
            api_key: Some(key),
            ..Default::default()
        })
        .expect("client"),
    )
}

#[tokio::test]
async fn live_scrape_formats() {
    let Some(client) = client() else {
        eprintln!("skip live test: CRAWLFOX_API_KEY not set");
        return;
    };

    let md = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(md.markdown.as_ref().unwrap().len() > 10);

    let html = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["html".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(html.html.as_ref().unwrap().contains("<"));

    let raw = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["rawHtml".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(raw.raw_html.as_ref().unwrap().len() > 10);

    let links = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["links".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(links.links.is_some());

    let images = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["images".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(images.images.is_some());

    let emails = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["emails".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(emails.emails.is_some());

    let extracted = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["json".into()]),
                json_options: Some(json!({ "selectors": { "heading": "h1" } })),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(extracted.json.is_some());

    let get = client.scrape_get("https://example.com").await.unwrap();
    assert!(get.markdown.as_ref().unwrap().len() > 10);
}

#[tokio::test]
async fn live_search_engines_stream_batch_logs() {
    let Some(client) = client() else {
        eprintln!("skip live test: CRAWLFOX_API_KEY not set");
        return;
    };

    for engine in ["google", "duckduckgo"] {
        let hits = client
            .search(
                "python asyncio",
                SearchOptions {
                    engine: Some(engine.into()),
                    num: Some(3),
                    ..Default::default()
                },
            )
            .await
            .unwrap_or_else(|e| panic!("{engine} search failed: {e:?}"));
        assert!(
            !hits.web.unwrap_or_default().is_empty(),
            "{engine} returned no hits"
        );
    }

    match client
        .search(
            "weather",
            SearchOptions {
                engine: Some("bing".into()),
                num: Some(3),
                ..Default::default()
            },
        )
        .await
    {
        Ok(hits) => assert!(!hits.web.unwrap_or_default().is_empty(), "bing returned no hits"),
        Err(e) => eprintln!("bing search skipped: {e:?}"),
    }

    let events = client
        .search_stream(
            "python asyncio",
            SearchOptions {
                engine: Some("google".into()),
                num: Some(12),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(events.iter().any(|e| e.event_type == "page"));
    assert!(events.iter().any(|e| e.event_type == "done"));

    let batch = client
        .batch(
            vec![
                "https://example.com/".into(),
                "https://example.org/".into(),
            ],
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert_eq!(batch.data.len(), 2);
    assert!(batch.data[0].markdown.as_ref().unwrap().len() > 10);

    let page = client
        .scrape(
            "https://example.com/",
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    let id = page
        .metadata
        .as_ref()
        .and_then(|m| m.scrape_id.clone())
        .expect("scrapeId");

    let mut row = None;
    for _ in 0..8 {
        tokio::time::sleep(Duration::from_secs(2)).await;
        if let Ok(r) = client.get_log(&id).await {
            row = Some(r);
            break;
        }
    }
    let row = row.expect("get_log should succeed after ingest");
    assert_eq!(row.status, 200);
    let stored = client.get_log_result(&id).await.unwrap();
    assert!(stored.get("markdown").is_some() || stored.get("metadata").is_some());
}
