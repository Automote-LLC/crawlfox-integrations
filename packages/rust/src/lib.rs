//! Official CrawlFox Rust SDK for scrape, batch, and search.

mod client;
mod error;
mod types;

pub use client::{Client, ClientOptions};
pub use error::Error;
pub use types::{
    BatchScrapeResult, Document, Location, LogRow, ScrapeMetadata, ScrapeOptions, SearchData,
    SearchOptions, SearchResult, SearchStreamEvent, SDK_VERSION,
};

pub const DEFAULT_API_URL: &str = "https://api.crawlfox.io";
