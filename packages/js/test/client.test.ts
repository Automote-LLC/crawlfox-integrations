import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { CrawlFox, CrawlFoxError } from "../src/index.js";

describe("CrawlFox client", () => {
  it("requires an API key", () => {
    const prev = process.env.CRAWLFOX_API_KEY;
    delete process.env.CRAWLFOX_API_KEY;
    assert.throws(() => new CrawlFox(), /API key required/);
    process.env.CRAWLFOX_API_KEY = prev;
  });

  it("scrape sends correct request and returns a Document", async () => {
    const calls: { url: string; init: RequestInit }[] = [];
    const fetchMock = async (url: string | URL | Request, init?: RequestInit) => {
      calls.push({ url: String(url), init: init ?? {} });
      return new Response(
        JSON.stringify({
          success: true,
          data: { markdown: "# Hello", metadata: { statusCode: 200 } },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    };

    const client = new CrawlFox({ apiKey: "cfx_test", fetch: fetchMock });
    const res = await client.scrape("https://example.com", {
      formats: ["markdown"],
      skipCache: true,
      country: "de",
      language: "de",
      redactPII: true,
    });

    assert.equal(res.success, true);
    assert.equal(res.markdown, "# Hello");
    assert.equal(calls.length, 1);
    assert.match(calls[0].url, /\/v1\/scrape$/);
    const headers = calls[0].init.headers as Record<string, string>;
    assert.equal(headers.Authorization, "Bearer cfx_test");
    assert.match(headers["User-Agent"], /^crawlfox-js\//);
    const body = JSON.parse(String(calls[0].init.body));
    assert.equal(body.url, "https://example.com");
    assert.deepEqual(body.formats, ["markdown"]);
    assert.equal(body.skipCache, true);
    assert.equal(body.country, "de");
    assert.equal(body.redactPII, true);
  });

  it("search sends query body", async () => {
    let body: Record<string, unknown> = {};
    const fetchMock = async (_url: string | URL | Request, init?: RequestInit) => {
      body = JSON.parse(String(init?.body));
      return new Response(
        JSON.stringify({
          success: true,
          data: { web: [{ url: "https://example.com", title: "Ex" }] },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    };

    const client = new CrawlFox({ apiKey: "cfx_test", fetch: fetchMock });
    const res = await client.search("crawlfox", { engine: "google", num: 5 });
    assert.equal(res.web?.[0]?.url, "https://example.com");
    assert.equal(body.q, "crawlfox");
    assert.equal(body.engine, "google");
    assert.equal(body.num, 5);
  });

  it("batch returns documents under data", async () => {
    const fetchMock = async () =>
      new Response(
        JSON.stringify({
          success: true,
          count: 1,
          results: [{ success: true, data: { markdown: "# A" } }],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    const client = new CrawlFox({ apiKey: "cfx_test", fetch: fetchMock });
    const batch = await client.batch(["https://example.org"], { formats: ["markdown"] });
    assert.equal(batch.data[0].markdown, "# A");
  });

  it("retries retryable errors then succeeds", async () => {
    let n = 0;
    const fetchMock = async () => {
      n += 1;
      if (n === 1) {
        return new Response(
          JSON.stringify({
            code: "RATE_LIMIT_EXCEEDED",
            message: "slow down",
            retryable: true,
          }),
          { status: 429, headers: { "content-type": "application/json" } },
        );
      }
      return new Response(
        JSON.stringify({ success: true, data: { markdown: "# ok" } }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    };
    const client = new CrawlFox({ apiKey: "cfx_test", fetch: fetchMock, maxRetries: 2 });
    const res = await client.scrape("https://example.com");
    assert.equal(res.markdown, "# ok");
    assert.equal(n, 2);
  });

  it("throws CrawlFoxError on non-retryable failure", async () => {
    const fetchMock = async () =>
      new Response(
        JSON.stringify({
          code: "MONTHLY_QUOTA_EXCEEDED",
          message: "Quota exceeded",
          retryable: false,
        }),
        { status: 429, headers: { "content-type": "application/json" } },
      );

    const client = new CrawlFox({ apiKey: "cfx_test", fetch: fetchMock });
    await assert.rejects(
      () => client.scrape("https://example.com"),
      (err: unknown) => {
        assert.ok(err instanceof CrawlFoxError);
        assert.equal(err.status, 429);
        assert.equal(err.code, "MONTHLY_QUOTA_EXCEEDED");
        return true;
      },
    );
  });

  it("searchStream yields NDJSON events", async () => {
    const ndjson = [
      JSON.stringify({ type: "page", data: { web: [{ url: "https://a.com" }] } }),
      JSON.stringify({ type: "done", partial: false, creditsUsed: 1, id: "x" }),
      "",
    ].join("\n");
    const fetchMock = async () =>
      new Response(ndjson, {
        status: 200,
        headers: { "content-type": "application/x-ndjson" },
      });
    const client = new CrawlFox({ apiKey: "cfx_test", fetch: fetchMock });
    const events = [];
    for await (const ev of client.searchStream("q", { num: 20 })) {
      events.push(ev);
    }
    assert.equal(events.length, 2);
    assert.equal(events[0].type, "page");
    assert.equal(events[1].type, "done");
  });

  it("getLog hits /v1/logs/:id", async () => {
    let url = "";
    const fetchMock = async (u: string | URL | Request) => {
      url = String(u);
      return new Response(
        JSON.stringify({
          id: "abc",
          started_at_ms: 1,
          duration_ms: 2,
          url: "https://example.com",
          status: 200,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    };
    const client = new CrawlFox({ apiKey: "cfx_test", fetch: fetchMock });
    const row = await client.getLog("abc");
    assert.match(url, /\/v1\/logs\/abc$/);
    assert.equal(row.status, 200);
  });
});
