use std::time::Duration;

use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE, USER_AGENT};
use serde_json::{json, Value};

use crate::error::{Error, ErrorBody};
use crate::types::{
    BatchEnvelope, BatchScrapeResult, Document, LogRow, SDK_VERSION, ScrapeEnvelope, ScrapeOptions,
    SearchData, SearchEnvelope, SearchOptions, SearchStreamEvent,
};
use crate::DEFAULT_API_URL;

#[derive(Debug, Clone, Default)]
pub struct ClientOptions {
    pub api_key: Option<String>,
    pub api_url: Option<String>,
    pub timeout: Option<Duration>,
    pub max_retries: Option<u32>,
}

#[derive(Debug, Clone)]
pub struct Client {
    api_key: String,
    api_url: String,
    max_retries: u32,
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
            max_retries: options.max_retries.unwrap_or(2),
            http,
        })
    }

    pub async fn scrape(&self, url: impl Into<String>, options: ScrapeOptions) -> Result<Document, Error> {
        let mut body = serde_json::to_value(&options)?;
        body["url"] = json!(url.into());
        let env: ScrapeEnvelope = self.request("POST", "/v1/scrape", Some(body)).await?;
        Ok(env.into_document())
    }

    pub async fn scrape_get(&self, url: impl AsRef<str>) -> Result<Document, Error> {
        let encoded: String = url
            .as_ref()
            .bytes()
            .map(|b| match b {
                b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'.' | b'_' | b'~' => {
                    (b as char).to_string()
                }
                _ => format!("%{b:02X}"),
            })
            .collect();
        let env: ScrapeEnvelope = self
            .request("GET", &format!("/v1/scrape/{encoded}"), None)
            .await?;
        Ok(env.into_document())
    }

    pub async fn batch(
        &self,
        urls: Vec<String>,
        mut options: ScrapeOptions,
    ) -> Result<BatchScrapeResult, Error> {
        options.json_options = None;
        let mut body = serde_json::to_value(&options)?;
        body["urls"] = json!(urls);
        let env: BatchEnvelope = self.request("POST", "/v1/batch", Some(body)).await?;
        Ok(env.into_result())
    }

    pub async fn search(&self, q: impl Into<String>, options: SearchOptions) -> Result<SearchData, Error> {
        let mut body = serde_json::to_value(&options)?;
        body["q"] = json!(q.into());
        let env: SearchEnvelope = self.request("POST", "/v1/search", Some(body)).await?;
        Ok(env.into_data())
    }

    pub async fn search_stream(
        &self,
        q: impl Into<String>,
        options: SearchOptions,
    ) -> Result<Vec<SearchStreamEvent>, Error> {
        let mut body = serde_json::to_value(&options)?;
        body["q"] = json!(q.into());
        let res = self.send("POST", "/v1/search/stream", Some(body)).await?;
        let status = res.status();
        let text = res.text().await?;
        if !status.is_success() {
            let parsed: ErrorBody = serde_json::from_str(&text).unwrap_or_default();
            return Err(Error::from_status(status.as_u16(), parsed));
        }
        let mut events = Vec::new();
        for line in text.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            events.push(serde_json::from_str(trimmed)?);
        }
        Ok(events)
    }

    pub async fn get_log(&self, id: impl AsRef<str>) -> Result<LogRow, Error> {
        let path = format!("/v1/logs/{}", id.as_ref());
        self.request("GET", &path, None).await
    }

    pub async fn get_log_result(&self, id: impl AsRef<str>) -> Result<Value, Error> {
        let path = format!("/v1/logs/{}/result", id.as_ref());
        self.request("GET", &path, None).await
    }

    async fn request<T: serde::de::DeserializeOwned>(
        &self,
        method: &str,
        path: &str,
        body: Option<Value>,
    ) -> Result<T, Error> {
        let attempts = self.max_retries + 1;
        let mut last: Option<Error> = None;
        for i in 0..attempts {
            let res = self.send(method, path, body.clone()).await?;
            let status = res.status();
            let bytes = res.bytes().await?;
            if !status.is_success() {
                let parsed: ErrorBody = serde_json::from_slice(&bytes).unwrap_or_default();
                let err = Error::from_status(status.as_u16(), parsed);
                if i + 1 < attempts && err.should_retry() {
                    last = Some(err);
                    std::thread::sleep(Duration::from_millis(200 * (1 << i)));
                    continue;
                }
                return Err(err);
            }
            return Ok(serde_json::from_slice(&bytes)?);
        }
        Err(last.unwrap_or_else(|| Error::from_status(0, ErrorBody::default())))
    }

    async fn send(
        &self,
        method: &str,
        path: &str,
        body: Option<Value>,
    ) -> Result<reqwest::Response, Error> {
        let mut headers = HeaderMap::new();
        let auth = format!("Bearer {}", self.api_key);
        let auth_value = HeaderValue::from_str(&auth).map_err(|e| Error::Api {
            status: 0,
            code: None,
            retryable: None,
            message: format!("invalid API key header: {e}"),
            body: ErrorBody::default(),
        })?;
        headers.insert(AUTHORIZATION, auth_value);
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        headers.insert(
            USER_AGENT,
            HeaderValue::from_str(&format!("crawlfox-rust/{SDK_VERSION}")).expect("ua"),
        );
        let url = format!("{}{path}", self.api_url);
        let builder = match method {
            "GET" => self.http.get(url),
            _ => self.http.post(url).json(&body.unwrap_or_else(|| json!({}))),
        };
        Ok(builder.headers(headers).send().await?)
    }
}
