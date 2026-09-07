use std::time::Duration;

use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde_json::{json, Value};

use crate::error::{Error, ErrorBody};
use crate::types::{
    BatchScrapeResponse, ScrapeOptions, ScrapeResponse, SearchOptions, SearchResponse,
};
use crate::DEFAULT_API_URL;

#[derive(Debug, Clone, Default)]
pub struct ClientOptions {
    /// API key (`cfx_…`). Defaults to `CRAWLFOX_API_KEY`.
    pub api_key: Option<String>,
    /// Base URL. Defaults to `https://api.crawlfox.io`.
    pub api_url: Option<String>,
    /// Request timeout. Defaults to 120 seconds.
    pub timeout: Option<Duration>,
}

/// Official CrawlFox client for scrape, batch, and search.
#[derive(Debug, Clone)]
pub struct Client {
    api_key: String,
    api_url: String,
    http: reqwest::Client,
}

impl Client {
    pub fn new(options: ClientOptions) -> Result<Self, Error> {
        let api_key = options
            .api_key
            .or_else(|| std::env::var("CRAWLFOX_API_KEY").ok())
            .filter(|k| !k.is_empty())
            .ok_or(Error::MissingApiKey)?;
        let api_url = options
            .api_url
            .unwrap_or_else(|| DEFAULT_API_URL.to_string())
            .trim_end_matches('/')
            .to_string();
        let timeout = options.timeout.unwrap_or(Duration::from_secs(120));
        let http = reqwest::Client::builder().timeout(timeout).build()?;
        Ok(Self {
            api_key,
            api_url,
            http,
        })
    }

    /// Scrape a single URL.
    pub async fn scrape(
        &self,
        url: impl Into<String>,
        options: ScrapeOptions,
    ) -> Result<ScrapeResponse, Error> {
        let mut body = serde_json::to_value(&options)?;
        body["url"] = json!(url.into());
        self.post("/v1/scrape", body).await
    }

    /// Scrape up to 100 URLs with the same options (`jsonOptions` is omitted).
    pub async fn batch(
        &self,
        urls: Vec<String>,
        mut options: ScrapeOptions,
    ) -> Result<BatchScrapeResponse, Error> {
        options.json_options = None;
        let mut body = serde_json::to_value(&options)?;
        body["urls"] = json!(urls);
        self.post("/v1/batch", body).await
    }

    /// Search the web (Google, Bing, or DuckDuckGo).
    pub async fn search(
        &self,
        q: impl Into<String>,
        options: SearchOptions,
    ) -> Result<SearchResponse, Error> {
        let mut body = serde_json::to_value(&options)?;
        body["q"] = json!(q.into());
        self.post("/v1/search", body).await
    }

    async fn post<T: serde::de::DeserializeOwned>(
        &self,
        path: &str,
        body: Value,
    ) -> Result<T, Error> {
        let mut headers = HeaderMap::new();
        let auth = format!("Bearer {}", self.api_key);
        let auth_value = HeaderValue::from_str(&auth).map_err(|e| {
            Error::Api {
                status: 0,
                code: None,
                retryable: None,
                message: format!("invalid API key header: {e}"),
                body: ErrorBody::default(),
            }
        })?;
        headers.insert(AUTHORIZATION, auth_value);
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));

        let res = self
            .http
            .post(format!("{}{path}", self.api_url))
            .headers(headers)
            .json(&body)
            .send()
            .await?;

        let status = res.status();
        let bytes = res.bytes().await?;
        if !status.is_success() {
            let parsed: ErrorBody = serde_json::from_slice(&bytes).unwrap_or_default();
            return Err(Error::from_status(status.as_u16(), parsed));
        }
        Ok(serde_json::from_slice(&bytes)?)
    }
}
