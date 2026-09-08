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
      formats: z
        .array(z.enum(["markdown", "html", "rawHtml", "json", "links", "images", "emails"]))
        .optional(),
    }),
    execute: async ({ url, formats }) => {
      return c.scrape(url, { formats: formats ?? ["markdown"] });
    },
  });
}

export function search(options?: CrawlFoxClientOptions) {
  const c = client(options);
  return tool({
    description: "Search the web with CrawlFox.",
    parameters: z.object({
      q: z.string(),
      engine: z.enum(["google", "duckduckgo"]).optional(),
      num: z.number().int().min(1).max(100).optional(),
    }),
    execute: async ({ q, engine, num }) => {
      return c.search(q, { engine, num });
    },
  });
}

export function batch(options?: CrawlFoxClientOptions) {
  const c = client(options);
  return tool({
    description: "Scrape multiple URLs with CrawlFox.",
    parameters: z.object({
      urls: z.array(z.string().url()).min(1).max(100),
      formats: z
        .array(z.enum(["markdown", "html", "rawHtml", "json", "links", "images", "emails"]))
        .optional(),
    }),
    execute: async ({ urls, formats }) => {
      return c.batch(urls, { formats: formats ?? ["markdown"] });
    },
  });
}
