import { tool } from "ai";
import { z } from "zod";
import { CrawlFox, type CrawlFoxClientOptions } from "crawlfox";

function client(options?: CrawlFoxClientOptions) {
  return new CrawlFox(options);
}

export function scrape(options?: CrawlFoxClientOptions) {
  const c = client(options);
  return tool({
    description: "Scrape a URL with CrawlFox.",
    parameters: z.object({
      url: z.string().url(),
      formats: z.array(z.enum(["markdown", "html", "text", "links"])).optional(),
    }),
    execute: async ({ url, formats }) => {
      const result = await c.scrape(url, { formats: formats ?? ["markdown"] });
      return result.data ?? result;
    },
  });
}

export function search(options?: CrawlFoxClientOptions) {
  const c = client(options);
  return tool({
    description: "Search the web with CrawlFox.",
    parameters: z.object({
      q: z.string(),
      engine: z.enum(["google", "bing", "duckduckgo"]).optional(),
      num: z.number().int().min(1).max(100).optional(),
    }),
    execute: async ({ q, engine, num }) => {
      const result = await c.search(q, { engine, num });
      return result.data ?? result;
    },
  });
}
