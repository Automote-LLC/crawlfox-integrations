import type {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
} from "n8n-workflow";

const API_BASE = "https://api.crawlfox.io";

export class CrawlFox implements INodeType {
  description: INodeTypeDescription = {
    displayName: "CrawlFox",
    name: "crawlfox",
    icon: "file:crawlfox.svg",
    group: ["transform"],
    version: 1,
    subtitle: '={{$parameter["operation"]}}',
    description: "Scrape URLs and search the web with CrawlFox",
    defaults: { name: "CrawlFox" },
    inputs: ["main"],
    outputs: ["main"],
    credentials: [{ name: "crawlfoxApi", required: true }],
    properties: [
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        options: [
          { name: "Scrape URL", value: "scrape" },
          { name: "Search Web", value: "search" },
        ],
        default: "scrape",
      },
      {
        displayName: "URL",
        name: "url",
        type: "string",
        default: "",
        required: true,
        displayOptions: { show: { operation: ["scrape"] } },
      },
      {
        displayName: "Query",
        name: "query",
        type: "string",
        default: "",
        required: true,
        displayOptions: { show: { operation: ["search"] } },
      },
      {
        displayName: "Engine",
        name: "engine",
        type: "options",
        options: [
          { name: "Google", value: "google" },
          { name: "Bing", value: "bing" },
          { name: "DuckDuckGo", value: "duckduckgo" },
        ],
        default: "google",
        displayOptions: { show: { operation: ["search"] } },
      },
      {
        displayName: "Result Count",
        name: "num",
        type: "number",
        default: 10,
        displayOptions: { show: { operation: ["search"] } },
      },
      {
        displayName: "Formats",
        name: "formats",
        type: "string",
        default: "markdown",
        displayOptions: { show: { operation: ["scrape"] } },
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];
    const credentials = await this.getCredentials("crawlfoxApi");
    const apiKey = credentials.apiKey as string;

    for (let i = 0; i < items.length; i++) {
      const operation = this.getNodeParameter("operation", i) as string;

      let path = "/v1/scrape";
      let body: Record<string, unknown> = {};

      if (operation === "scrape") {
        const url = this.getNodeParameter("url", i) as string;
        const formatsRaw = this.getNodeParameter("formats", i, "markdown") as string;
        const formats = formatsRaw.split(",").map((s) => s.trim()).filter(Boolean);
        body = { url, formats };
      } else {
        path = "/v1/search";
        body = {
          q: this.getNodeParameter("query", i) as string,
          engine: this.getNodeParameter("engine", i) as string,
          num: this.getNodeParameter("num", i) as number,
        };
      }

      const response = await this.helpers.httpRequest({
        method: "POST",
        url: `${API_BASE}${path}`,
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body,
        json: true,
      });

      returnData.push({ json: response as Record<string, unknown> });
    }

    return [returnData];
  }
}
