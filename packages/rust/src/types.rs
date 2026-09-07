use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Default, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ScrapeOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub formats: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub extract_main_content: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub skip_cache: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub zdr: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub timeout: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub json_options: Option<Value>,
}

#[derive(Debug, Clone, Default, Serialize)]
pub struct SearchOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub engine: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub num: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub start: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub country: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub language: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ScrapeMetadata {
    pub title: Option<String>,
    pub description: Option<String>,
    pub language: Option<String>,
    pub source_url: Option<String>,
    pub url: Option<String>,
    pub status_code: Option<i32>,
    pub scrape_id: Option<String>,
    pub credits_used: Option<f64>,
    pub cache_state: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ScrapeData {
    pub markdown: Option<String>,
    pub html: Option<String>,
    pub raw_html: Option<String>,
    pub text: Option<String>,
    pub links: Option<Vec<String>>,
    pub images: Option<Vec<String>>,
    pub emails: Option<Vec<String>>,
    pub json: Option<Value>,
    pub metadata: Option<ScrapeMetadata>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct ScrapeResponse {
    pub success: bool,
    pub data: Option<ScrapeData>,
    pub metadata: Option<Value>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct BatchScrapeResponse {
    pub success: bool,
    pub count: Option<u32>,
    #[serde(default)]
    pub results: Vec<ScrapeResponse>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SearchResult {
    pub url: String,
    pub title: Option<String>,
    pub description: Option<String>,
    pub position: Option<i32>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SearchResponse {
    pub success: bool,
    pub credits_used: Option<f64>,
    pub id: Option<String>,
    pub data: Option<SearchData>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct SearchData {
    pub web: Option<Vec<SearchResult>>,
}
