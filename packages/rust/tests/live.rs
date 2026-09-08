use crawlfox::{Client, ClientOptions, ScrapeOptions, SearchOptions};

#[tokio::test]
async fn live_scrape_search() {
    let Ok(key) = std::env::var("CRAWLFOX_API_KEY") else {
        eprintln!("skip live test: CRAWLFOX_API_KEY not set");
        return;
    };
    let client = Client::new(ClientOptions {
        api_key: Some(key),
        ..Default::default()
    })
    .unwrap();
    let doc = client
        .scrape(
            "https://example.com",
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(doc.markdown.as_ref().unwrap().len() > 10);
    let hits = client
        .search(
            "crawlfox",
            SearchOptions {
                engine: Some("google".into()),
                num: Some(3),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(!hits.web.unwrap().is_empty());
}
