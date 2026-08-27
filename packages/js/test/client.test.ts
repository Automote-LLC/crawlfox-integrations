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

  it("scrape sends correct request", async () => {
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
    });

    assert.equal(res.success, true);
    assert.equal(res.data?.markdown, "# Hello");
    assert.equal(calls.length, 1);
    assert.match(calls[0].url, /\/v1\/scrape$/);
    const headers = calls[0].init.headers as Record<string, string>;
    assert.equal(headers.Authorization, "Bearer cfx_test");
    const body = JSON.parse(String(calls[0].init.body));
    assert.equal(body.url, "https://example.com");
    assert.deepEqual(body.formats, ["markdown"]);
    assert.equal(body.skipCache, true);
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
    assert.equal(res.data?.web?.[0]?.url, "https://example.com");
    assert.equal(body.q, "crawlfox");
    assert.equal(body.engine, "google");
    assert.equal(body.num, 5);
  });

  it("throws CrawlFoxError on failure", async () => {
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
});
