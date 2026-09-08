#!/usr/bin/env node
/**
 * Live smoke against api.crawlfox.io. Key from env only — never hardcode.
 */
import { CrawlFox } from "../src/index.ts";

const key = process.env.CRAWLFOX_API_KEY;
if (!key) {
  console.error("CRAWLFOX_API_KEY required");
  process.exit(1);
}

const client = new CrawlFox({ apiKey: key, timeoutMs: 90_000, maxRetries: 1 });

const scrape = await client.scrape("https://example.com", { formats: ["markdown"] });
if (!scrape.markdown || scrape.markdown.length < 10) {
  console.error("scrape failed", scrape);
  process.exit(1);
}
console.log("scrape ok", scrape.markdown.slice(0, 60).replace(/\n/g, " "));

const search = await client.search("crawlfox", { engine: "google", num: 3 });
const n = search.web?.length ?? 0;
if (n < 1) {
  console.error("search returned no hits", search);
  process.exit(1);
}
console.log("search ok", n, "hits", search.web?.[0]?.url);

const batch = await client.batch(["https://example.com"], { formats: ["markdown"] });
if (!batch.data?.[0]?.markdown) {
  console.error("batch failed", batch);
  process.exit(1);
}
console.log("batch ok", batch.data[0].markdown.slice(0, 40).replace(/\n/g, " "));
console.log("LIVE_SMOKE_PASS");
