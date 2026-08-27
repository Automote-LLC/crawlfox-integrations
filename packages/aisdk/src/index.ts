import { tool } from "ai";
import { z } from "zod";
import { CrawlFox, type CrawlFoxClientOptions } from "crawlfox";

export interface CrawlFoxToolsOptions extends CrawlFoxClientOptions {
  /** Include batch scrape tool. Default true. */
  batch?: boolean;
}

/**
 * Vercel AI SDK tools for CrawlFox scrape and search.
 *
 * @example
 * ```ts
 * import { generateText, stepCountIs } from "ai";
 * import { CrawlFoxTools } from "crawlfox-aisdk";
 *
 * const { text } = await generateText({
 *   model: "anthropic/claude-sonnet-4-5",
 *   tools: CrawlFoxTools(),
 *   stopWhen: stepCountIs(10),
 *   prompt: "Search for CrawlFox and summarize the homepage.",
 * });
 * ```
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
        .array(z.enum(["markdown", "html", "text", "links"]))
        .optional()
        .describe("Output formats; defaults to markdown"),
      extractMainContent: z.boolean().optional(),
      skipCache: z.boolean().optional(),
    }),
    execute: async ({ url, formats, extractMainContent, skipCache }) => {
      const result = await client.scrape(url, {
        formats: formats ?? ["markdown"],
        extractMainContent,
        skipCache,
      });
      return result.data ?? result;
    },
  });

  const search = tool({
    description: "Search the web with Google, Bing, or DuckDuckGo via CrawlFox.",
    parameters: z.object({
      q: z.string().describe("Search query"),
      engine: z.enum(["google", "bing", "duckduckgo"]).optional(),
      num: z.number().int().min(1).max(100).optional(),
    }),
    execute: async ({ q, engine, num }) => {
      const result = await client.search(q, { engine, num });
      return result.data ?? result;
    },
  });

  const tools: Record<string, ReturnType<typeof tool>> = { scrape, search };

  if (includeBatch) {
    tools.batch = tool({
      description: "Scrape up to 100 URLs in one CrawlFox batch call.",
      parameters: z.object({
        urls: z.array(z.string().url()).min(1).max(100),
        formats: z.array(z.enum(["markdown", "html", "text", "links"])).optional(),
      }),
      execute: async ({ urls, formats }) => {
        const result = await client.batch(urls, { formats: formats ?? ["markdown"] });
        return result;
      },
    });
  }

  return tools;
}

export { scrape, search } from "./tools.js";
