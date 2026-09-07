use serde::Deserialize;
use thiserror::Error;

#[derive(Debug, Clone, Default, Deserialize)]
pub struct ErrorBody {
    pub code: Option<String>,
    pub status: Option<u16>,
    pub retryable: Option<bool>,
    pub title: Option<String>,
    pub message: Option<String>,
    pub remediation: Option<String>,
}

#[derive(Debug, Error)]
pub enum Error {
    #[error("{message}")]
    Api {
        status: u16,
        code: Option<String>,
        retryable: Option<bool>,
        message: String,
        body: ErrorBody,
    },
    #[error("CrawlFox API key required. Pass api_key or set CRAWLFOX_API_KEY.")]
    MissingApiKey,
    #[error(transparent)]
    Http(#[from] reqwest::Error),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
}

impl Error {
    pub fn from_status(status: u16, body: ErrorBody) -> Self {
        let message = body
            .message
            .clone()
            .or_else(|| body.title.clone())
            .unwrap_or_else(|| format!("CrawlFox request failed ({status})"));
        Error::Api {
            status,
            code: body.code.clone(),
            retryable: body.retryable,
            message,
            body,
        }
    }

    pub fn status(&self) -> Option<u16> {
        match self {
            Error::Api { status, .. } => Some(*status),
            _ => None,
        }
    }

    pub fn code(&self) -> Option<&str> {
        match self {
            Error::Api { code, .. } => code.as_deref(),
            _ => None,
        }
    }
}
