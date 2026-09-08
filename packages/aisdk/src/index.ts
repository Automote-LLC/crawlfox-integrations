import { tool } from "ai";
import { z } from "zod";
import { CrawlFox, type CrawlFoxClientOptions } from "crawlfox";

export interface CrawlFoxToolsOptions extends CrawlFoxClientOptions {
  /** Include batch scrape tool. Default true. */
  batch?: boolean;
}

const FORMATS = ["markdown", "html", "rawHtml", "json", "links", "images", "emails"] as const;

/**
 * Vercel AI SDK tools for CrawlFox scrape and search.
 */
export function CrawlFoxTools(options: CrawlFoxToolsOptions = {}) {
  const client = new CrawlFox(options);
  const includeBatch = options.batch !== false;

  const scrape = tool({
    description:
      "Scrape a URL and return clean markdown or other formats from the CrawlFox API.",
    parameters: z.object({
      url: z.string().url().describe("Fully-qualified URL to scrape"),
      formats: z
        .array(z.enum(FORMATS))
        .optional()
        .describe("Output formats; defaults to markdown"),
      skipCache: z.boolean().optional(),
      country: z.string().optional(),
      language: z.string().optional(),
    }),
    execute: async ({ url, formats, skipCache, country, language }) => {
      return client.scrape(url, {
        formats: formats ?? ["markdown"],
        skipCache,
        country,
        language,
      });
    },
  });

  const search = tool({
    description: "Search the web with Google or DuckDuckGo via CrawlFox.",
    parameters: z.object({
      q: z.string().describe("Search query"),
      engine: z.enum(["google", "duckduckgo"]).optional(),
      num: z.number().int().min(1).max(100).optional(),
    }),
    execute: async ({ q, engine, num }) => {
      return client.search(q, { engine, num });
    },
  });

  const tools: Record<string, ReturnType<typeof tool>> = { scrape, search };

  if (includeBatch) {
    tools.batch = tool({
      description: "Scrape up to 100 URLs in one CrawlFox batch call.",
      parameters: z.object({
        urls: z.array(z.string().url()).min(1).max(100),
        formats: z.array(z.enum(FORMATS)).optional(),
      }),
      execute: async ({ urls, formats }) => {
        return client.batch(urls, { formats: formats ?? ["markdown"] });
      },
    });
  }

  return tools;
}

export { scrape, search, batch } from "./tools.js";
