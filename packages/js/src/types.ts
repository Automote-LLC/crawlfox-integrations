/** Output format for scrape requests. */
export type ScrapeFormat =
  | "markdown"
  | "html"
  | "rawHtml"
  | "text"
  | "json"
  | "links"
  | "images"
  | "emails";

export interface JsonOptions {
  selectors?: Record<string, string>;
}

export interface ScrapeOptions {
  formats?: ScrapeFormat[];
  extractMainContent?: boolean;
  skipCache?: boolean;
  zdr?: boolean;
  timeout?: number;
  jsonOptions?: JsonOptions;
}

export interface ScrapeMetadata {
  title?: string;
  description?: string;
  language?: string;
  sourceURL?: string;
  url?: string;
  statusCode?: number;
  scrapeId?: string;
  creditsUsed?: number;
  cacheState?: "hit" | "miss";
  [key: string]: unknown;
}

export interface ScrapeData {
  markdown?: string;
  html?: string;
  rawHtml?: string;
  text?: string;
  links?: string[];
  json?: Record<string, unknown>;
  metadata?: ScrapeMetadata;
  [key: string]: unknown;
}

export interface ScrapeResponse {
  success: boolean;
  data?: ScrapeData;
  metadata?: Record<string, unknown>;
}

export interface BatchScrapeResponse {
  success: boolean;
  count?: number;
  results: ScrapeResponse[];
}

export interface SearchResult {
  url: string;
  title?: string;
  description?: string;
  position?: number;
}

export interface SearchOptions {
  engine?: "google" | "bing" | "duckduckgo";
  num?: number;
  start?: number;
  country?: string;
  language?: string;
}

export interface SearchResponse {
  success: boolean;
  data?: {
    web?: SearchResult[];
  };
  creditsUsed?: number;
  id?: string;
}

export interface CrawlFoxErrorBody {
  code?: string;
  status?: number;
  retryable?: boolean;
  title?: string;
  message?: string;
  remediation?: string;
}

export interface CrawlFoxClientOptions {
  /** API key (`cfx_…`). Defaults to `process.env.CRAWLFOX_API_KEY`. */
  apiKey?: string;
  /** Base URL. Defaults to `https://api.crawlfox.io`. */
  apiUrl?: string;
  /** Request timeout in ms. Defaults to 120_000. */
  timeoutMs?: number;
  /** Custom fetch implementation (for tests or edge runtimes). */
  fetch?: typeof fetch;
}

export class CrawlFoxError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly retryable?: boolean;
  readonly body?: CrawlFoxErrorBody;

  constructor(message: string, status: number, body?: CrawlFoxErrorBody) {
    super(message);
    this.name = "CrawlFoxError";
    this.status = status;
    this.code = body?.code;
    this.retryable = body?.retryable;
    this.body = body;
  }
}
