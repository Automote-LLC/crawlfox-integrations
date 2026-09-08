use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const SDK_VERSION: &str = "0.1.0";

#[derive(Debug, Clone, Default, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Location {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub country: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub languages: Option<Vec<String>>,
}

#[derive(Debug, Clone, Default, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ScrapeOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub formats: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub skip_cache: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub zdr: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub timeout: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub json_options: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub country: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub language: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub location: Option<Location>,
    #[serde(skip_serializing_if = "Option::is_none", rename = "redactPII")]
    pub redact_pii: Option<Value>,
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
pub struct Document {
    #[serde(default)]
    pub success: Option<bool>,
    pub markdown: Option<String>,
    pub html: Option<String>,
    pub raw_html: Option<String>,
    pub links: Option<Vec<String>>,
    pub images: Option<Vec<String>>,
    pub emails: Option<Vec<String>>,
    pub json: Option<Value>,
    pub metadata: Option<ScrapeMetadata>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub(crate) struct ScrapeEnvelope {
    success: bool,
    data: Option<Document>,
    error: Option<String>,
}

impl ScrapeEnvelope {
    pub(crate) fn into_document(self) -> Document {
        let mut doc = self.data.unwrap_or_default();
        doc.success = Some(self.success);
        if doc.error.is_none() {
            doc.error = self.error;
        }
        doc
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct BatchScrapeResult {
    pub success: bool,
    pub count: Option<u32>,
    #[serde(default)]
    pub data: Vec<Document>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub(crate) struct BatchEnvelope {
    success: bool,
    count: Option<u32>,
    #[serde(default)]
    results: Vec<ScrapeEnvelope>,
}

impl BatchEnvelope {
    pub(crate) fn into_result(self) -> BatchScrapeResult {
        BatchScrapeResult {
            success: self.success,
            count: self.count,
            data: self.results.into_iter().map(|e| e.into_document()).collect(),
        }
    }
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
pub struct SearchData {
    pub success: Option<bool>,
    pub web: Option<Vec<SearchResult>>,
    pub credits_used: Option<f64>,
    pub id: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(rename_all = "camelCase")]
pub(crate) struct SearchEnvelope {
    success: bool,
    credits_used: Option<f64>,
    id: Option<String>,
    data: Option<SearchInner>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct SearchInner {
    pub web: Option<Vec<SearchResult>>,
}

impl SearchEnvelope {
    pub(crate) fn into_data(self) -> SearchData {
        SearchData {
            success: Some(self.success),
            web: self.data.and_then(|d| d.web),
            credits_used: self.credits_used,
            id: self.id,
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct SearchStreamEvent {
    #[serde(rename = "type")]
    pub event_type: String,
    pub data: Option<SearchInner>,
    pub partial: Option<bool>,
    #[serde(rename = "creditsUsed")]
    pub credits_used: Option<f64>,
    pub id: Option<String>,
    pub code: Option<String>,
    pub message: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct LogRow {
    pub id: String,
    pub started_at_ms: i64,
    pub duration_ms: i32,
    pub url: Value,
    pub status: i32,
    pub final_outcome: Option<String>,
}
