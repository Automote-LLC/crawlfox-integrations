use crawlfox::{Client, ClientOptions, Error, ScrapeOptions, SearchOptions};
use serde_json::json;
use wiremock::matchers::{header, method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

#[test]
fn requires_api_key() {
    // SAFETY: this test is single-threaded and only clears our own key.
    unsafe { std::env::remove_var("CRAWLFOX_API_KEY") };
    let err = Client::new(ClientOptions::default()).unwrap_err();
    assert!(matches!(err, Error::MissingApiKey));
}

#[tokio::test]
async fn scrape_sends_correct_request() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/scrape"))
        .and(header("Authorization", "Bearer cfx_test"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "success": true,
            "data": { "markdown": "# Hello", "metadata": { "statusCode": 200 } }
        })))
        .mount(&server)
        .await;

    let client = Client::new(ClientOptions {
        api_key: Some("cfx_test".into()),
        api_url: Some(server.uri()),
        timeout: None,
    })
    .unwrap();

    let res = client
        .scrape(
            "https://example.com",
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                skip_cache: Some(true),
                ..Default::default()
            },
        )
        .await
        .unwrap();

    assert!(res.success);
    assert_eq!(res.data.unwrap().markdown.as_deref(), Some("# Hello"));
}

#[tokio::test]
async fn search_sends_query_body() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/search"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "success": true,
            "data": { "web": [{ "url": "https://example.com", "title": "Ex" }] }
        })))
        .mount(&server)
        .await;

    let client = Client::new(ClientOptions {
        api_key: Some("cfx_test".into()),
        api_url: Some(server.uri()),
        timeout: None,
    })
    .unwrap();

    let res = client
        .search(
            "crawlfox",
            SearchOptions {
                engine: Some("google".into()),
                num: Some(5),
                ..Default::default()
            },
        )
        .await
        .unwrap();

    assert_eq!(
        res.data.unwrap().web.unwrap()[0].url,
        "https://example.com"
    );
}

#[tokio::test]
async fn batch_returns_results() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/batch"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "success": true,
            "count": 1,
            "results": [{ "success": true, "data": { "markdown": "# A" } }]
        })))
        .mount(&server)
        .await;

    let client = Client::new(ClientOptions {
        api_key: Some("cfx_test".into()),
        api_url: Some(server.uri()),
        timeout: None,
    })
    .unwrap();

    let res = client
        .batch(
            vec!["https://example.org".into()],
            ScrapeOptions {
                formats: Some(vec!["markdown".into()]),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    assert!(res.success);
    assert_eq!(res.results[0].data.as_ref().unwrap().markdown.as_deref(), Some("# A"));
}

#[tokio::test]
async fn throws_on_failure() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/scrape"))
        .respond_with(ResponseTemplate::new(429).set_body_json(json!({
            "code": "MONTHLY_QUOTA_EXCEEDED",
            "message": "Quota exceeded",
            "retryable": false
        })))
        .mount(&server)
        .await;

    let client = Client::new(ClientOptions {
        api_key: Some("cfx_test".into()),
        api_url: Some(server.uri()),
        timeout: None,
    })
    .unwrap();

    let err = client
        .scrape("https://example.com", ScrapeOptions::default())
        .await
        .unwrap_err();
    assert_eq!(err.status(), Some(429));
    assert_eq!(err.code(), Some("MONTHLY_QUOTA_EXCEEDED"));
}
