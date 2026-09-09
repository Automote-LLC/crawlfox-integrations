export const SDK_VERSION = "0.1.3";

/** Output formats the gateway accepts. `text` was removed (400 FORMAT_UNAVAILABLE). */
export type ScrapeFormat =
  | "markdown"
  | "html"
  | "rawHtml"
  | "json"
  | "links"
  | "images"
  | "emails";

export type SelectorRule =
  | string
  | { selector: string; attr?: string; multiple?: boolean };

export interface JsonOptions {
  selectors: Record<string, SelectorRule>;
}

export interface Location {
  country?: string;
  languages?: string[];
}

export type RedactPiiMode = "accurate" | "aggressive" | "fast";
export type RedactPiiEntity =
  | "PERSON"
  | "EMAIL"
  | "PHONE"
  | "LOCATION"
  | "FINANCIAL"
  | "SECRET";
export type RedactPiiReplaceStyle = "tag" | "mask" | "remove";

export type RedactPii =
  | boolean
  | {
      mode?: RedactPiiMode;
      entities?: RedactPiiEntity[];
      replaceStyle?: RedactPiiReplaceStyle;
    };

export interface ScrapeOptions {
  formats?: ScrapeFormat[];
  skipCache?: boolean;
  zdr?: boolean;
  timeout?: number;
  jsonOptions?: JsonOptions;
  country?: string;
  language?: string;
  location?: Location;
  redactPII?: RedactPii;
}

export type SearchEngine = "google" | "bing" | "duckduckgo";

export interface SearchOptions {
  engine?: SearchEngine;
  num?: number;
  start?: number;
  country?: string;
  language?: string;
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
  contentType?: string;
  favicon?: string;
  [key: string]: unknown;
}

/** Scraped document: fields sit on the object, not under `.data`. */
export interface Document {
  success?: boolean;
  markdown?: string;
  html?: string;
  rawHtml?: string;
  links?: string[];
  images?: string[];
  emails?: string[];
  json?: unknown;
  metadata?: ScrapeMetadata;
  error?: string;
  [key: string]: unknown;
}

export interface BatchScrapeResult {
  success: boolean;
  count?: number;
  data: Document[];
}

export interface SearchResult {
  url: string;
  title?: string;
  description?: string;
  position?: number;
}

export interface SearchData {
  success?: boolean;
  web?: SearchResult[];
  creditsUsed?: number;
  id?: string;
}

export type SearchStreamEvent =
  | { type: "page"; data?: { web?: SearchResult[] } }
  | {
      type: "done";
      partial?: boolean;
      creditsUsed?: number;
      id?: string;
    }
  | { type: "error"; code?: string; message?: string; [key: string]: unknown };

export interface LogRow {
  id: string;
  started_at_ms: number;
  duration_ms: number;
  url: unknown;
  status: number;
  final_outcome?: string | null;
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
  /** HTTP round-trip timeout in ms. Defaults to 120_000. */
  timeoutMs?: number;
  /** Extra attempts after retryable API or network errors. Defaults to 2. */
  maxRetries?: number;
  /** Custom fetch implementation (for tests or edge runtimes). */
  fetch?: typeof fetch;
  /** Base delay for exponential backoff, in ms. Defaults to 200. */
  retryBackoffMs?: number;
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

export const MAX_BATCH_URLS = 100;
