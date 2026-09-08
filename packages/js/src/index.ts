import {
  BatchScrapeResult,
  CrawlFoxClientOptions,
  CrawlFoxError,
  CrawlFoxErrorBody,
  Document,
  LogRow,
  SDK_VERSION,
  ScrapeOptions,
  SearchData,
  SearchOptions,
  SearchResult,
  SearchStreamEvent,
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

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryable(err: CrawlFoxError): boolean {
  if (err.retryable === false) return false;
  if (err.retryable === true) return true;
  return err.status === 502 || err.status === 503 || err.status === 504;
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

function documentFromEnvelope(envelope: Record<string, unknown>): Document {
  const data =
    envelope.data && typeof envelope.data === "object"
      ? (envelope.data as Record<string, unknown>)
      : envelope;
  return {
    ...data,
    success: (envelope.success as boolean | undefined) ?? true,
    error: (envelope.error as string | undefined) ?? (data.error as string | undefined),
  };
}

function searchFromEnvelope(envelope: Record<string, unknown>): SearchData {
  const data =
    envelope.data && typeof envelope.data === "object"
      ? (envelope.data as { web?: SearchResult[] })
      : {};
  return {
    success: (envelope.success as boolean | undefined) ?? true,
    web: data.web,
    creditsUsed: envelope.creditsUsed as number | undefined,
    id: envelope.id as string | undefined,
  };
}

function scrapeBody(url: string, options: ScrapeOptions): Record<string, unknown> {
  const body: Record<string, unknown> = { url };
  Object.assign(body, options);
  return body;
}

function batchBody(urls: string[], options: Omit<ScrapeOptions, "jsonOptions">): Record<string, unknown> {
  const { jsonOptions: _, ...rest } = options as ScrapeOptions;
  return { urls, ...rest };
}

/**
 * Official CrawlFox JavaScript client for scrape, batch, search, and logs.
 *
 * @example
 * ```ts
 * import { CrawlFox } from "crawlfox";
 *
 * const client = new CrawlFox({ apiKey: process.env.CRAWLFOX_API_KEY });
 * const page = await client.scrape("https://example.com", { formats: ["markdown"] });
 * console.log(page.markdown);
 * ```
 */
export class CrawlFox {
  private readonly apiKey: string;
  private readonly apiUrl: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;
  private readonly fetchFn: typeof fetch;

  constructor(options: CrawlFoxClientOptions = {}) {
    this.apiKey = resolveApiKey(options.apiKey);
    this.apiUrl = (options.apiUrl ?? DEFAULT_API_URL).replace(/\/$/, "");
    this.timeoutMs = options.timeoutMs ?? 120_000;
    this.maxRetries = options.maxRetries ?? 2;
    this.fetchFn = options.fetch ?? fetch;
  }

  /** Scrape a single URL (`POST /v1/scrape`). Returns a Document. */
  async scrape(url: string, options: ScrapeOptions = {}): Promise<Document> {
    const envelope = await this.post<Record<string, unknown>>(
      "/v1/scrape",
      scrapeBody(url, options),
    );
    return documentFromEnvelope(envelope);
  }

  /** Markdown-only GET scrape of a percent-encoded URL. */
  async scrapeGet(url: string): Promise<Document> {
    const envelope = await this.request<Record<string, unknown>>(
      "GET",
      `/v1/scrape/${encodeURIComponent(url)}`,
    );
    return documentFromEnvelope(envelope);
  }

  /** Scrape up to 100 URLs with the same options (`jsonOptions` is omitted). */
  async batch(
    urls: string[],
    options: Omit<ScrapeOptions, "jsonOptions"> = {},
  ): Promise<BatchScrapeResult> {
    const envelope = await this.post<{
      success?: boolean;
      count?: number;
      results?: Record<string, unknown>[];
    }>("/v1/batch", batchBody(urls, options));
    const data = (envelope.results ?? []).map(documentFromEnvelope);
    return {
      success: envelope.success ?? true,
      count: envelope.count ?? data.length,
      data,
    };
  }

  /** Search the web (Google or DuckDuckGo). */
  async search(q: string, options: SearchOptions = {}): Promise<SearchData> {
    const envelope = await this.post<Record<string, unknown>>("/v1/search", {
      q,
      ...options,
    });
    return searchFromEnvelope(envelope);
  }

  /** Same search as NDJSON events (`page` / `done` / `error`). */
  async *searchStream(
    q: string,
    options: SearchOptions = {},
  ): AsyncGenerator<SearchStreamEvent> {
    const res = await this.send("POST", "/v1/search/stream", { q, ...options });
    if (!res.ok) {
      throw await parseError(res);
    }
    if (!res.body) {
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      buf += decoder.decode(value ?? new Uint8Array(), { stream: !done });
      const lines = buf.split("\n");
      buf = done ? "" : (lines.pop() ?? "");
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        yield JSON.parse(trimmed) as SearchStreamEvent;
      }
      if (done) break;
    }
    const last = buf.trim();
    if (last) yield JSON.parse(last) as SearchStreamEvent;
  }

  /** Status and timing of one of your own past requests. */
  async getLog(id: string): Promise<LogRow> {
    return this.request<LogRow>("GET", `/v1/logs/${encodeURIComponent(id)}`);
  }

  /** Stored result body of a past scrape. */
  async getLogResult(id: string): Promise<unknown> {
    return this.request<unknown>("GET", `/v1/logs/${encodeURIComponent(id)}/result`);
  }

  private post<T>(path: string, body: Record<string, unknown>): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  private async request<T>(
    method: string,
    path: string,
    body?: Record<string, unknown>,
  ): Promise<T> {
    let last: CrawlFoxError | undefined;
    const attempts = this.maxRetries + 1;
    for (let i = 0; i < attempts; i++) {
      try {
        const res = await this.send(method, path, body);
        if (!res.ok) {
          const err = await parseError(res);
          if (i < attempts - 1 && isRetryable(err)) {
            last = err;
            await sleep(200 * 2 ** i);
            continue;
          }
          throw err;
        }
        return (await res.json()) as T;
      } catch (err) {
        if (err instanceof CrawlFoxError) {
          throw err;
        }
        throw err;
      }
    }
    throw last ?? new CrawlFoxError("Request failed", 0);
  }

  private async send(
    method: string,
    path: string,
    body?: Record<string, unknown>,
  ): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const res = await this.fetchFn(`${this.apiUrl}${path}`, {
        method,
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
          "User-Agent": `crawlfox-js/${SDK_VERSION}`,
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      return res;
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        throw new CrawlFoxError("Request timed out", 408, { retryable: true });
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
}

export * from "./types.js";
