import {
  BatchScrapeResponse,
  CrawlFoxClientOptions,
  CrawlFoxError,
  CrawlFoxErrorBody,
  ScrapeOptions,
  ScrapeResponse,
  SearchOptions,
  SearchResponse,
} from "./types.js";

const DEFAULT_API_URL = "https://api.crawlfox.io";

function resolveApiKey(explicit?: string): string {
  const key = explicit ?? process.env.CRAWLFOX_API_KEY;
  if (!key) {
    throw new Error(
      "CrawlFox API key required. Pass apiKey or set CRAWLFOX_API_KEY.",
    );
  }
  return key;
}

async function parseError(res: Response): Promise<CrawlFoxError> {
  let body: CrawlFoxErrorBody | undefined;
  try {
    body = (await res.json()) as CrawlFoxErrorBody;
  } catch {
    // ignore
  }
  const message =
    body?.message ?? body?.title ?? `CrawlFox request failed (${res.status})`;
  return new CrawlFoxError(message, res.status, body);
}

/**
 * Official CrawlFox JavaScript client for scrape, batch, and search.
 *
 * @example
 * ```ts
 * import { CrawlFox } from "crawlfox";
 *
 * const client = new CrawlFox({ apiKey: process.env.CRAWLFOX_API_KEY });
 * const page = await client.scrape("https://example.com", { formats: ["markdown"] });
 * console.log(page.data?.markdown);
 * ```
 */
export class CrawlFox {
  private readonly apiKey: string;
  private readonly apiUrl: string;
  private readonly timeoutMs: number;
  private readonly fetchFn: typeof fetch;

  constructor(options: CrawlFoxClientOptions = {}) {
    this.apiKey = resolveApiKey(options.apiKey);
    this.apiUrl = (options.apiUrl ?? DEFAULT_API_URL).replace(/\/$/, "");
    this.timeoutMs = options.timeoutMs ?? 120_000;
    this.fetchFn = options.fetch ?? fetch;
  }

  /** Scrape a single URL. */
  async scrape(url: string, options: ScrapeOptions = {}): Promise<ScrapeResponse> {
    return this.post<ScrapeResponse>("/v1/scrape", { url, ...options });
  }

  /** Scrape up to 100 URLs with the same options. */
  async batch(
    urls: string[],
    options: Omit<ScrapeOptions, "jsonOptions"> = {},
  ): Promise<BatchScrapeResponse> {
    return this.post<BatchScrapeResponse>("/v1/batch", { urls, ...options });
  }

  /** Search the web (Google, Bing, or DuckDuckGo). */
  async search(q: string, options: SearchOptions = {}): Promise<SearchResponse> {
    return this.post<SearchResponse>("/v1/search", { q, ...options });
  }

  private async post<T>(path: string, body: Record<string, unknown>): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const res = await this.fetchFn(`${this.apiUrl}${path}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok) {
        throw await parseError(res);
      }
      return (await res.json()) as T;
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        throw new CrawlFoxError("Request timed out", 408);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
}

export * from "./types.js";
