const scrape = async (z, bundle) => {
  const response = await z.request({
    url: "https://api.crawlfox.io/v1/scrape",
    method: "POST",
    body: {
      url: bundle.inputData.url,
      formats: bundle.inputData.formats
        ? bundle.inputData.formats.split(",").map((s) => s.trim())
        : ["markdown"],
      extractMainContent: bundle.inputData.extractMainContent,
      skipCache: bundle.inputData.skipCache,
    },
  });
  return response.data;
};

module.exports = {
  key: "scrape_url",
  noun: "Page",
  display: {
    label: "Scrape URL",
    description: "Scrape a single URL and return clean markdown or HTML via CrawlFox.",
  },
  operation: {
    inputFields: [
      { key: "url", label: "URL", type: "string", required: true },
      {
        key: "formats",
        label: "Formats",
        type: "string",
        default: "markdown",
        helpText: "Comma-separated: markdown, html, text, links",
      },
      { key: "extractMainContent", label: "Extract Main Content", type: "boolean" },
      { key: "skipCache", label: "Skip Cache", type: "boolean" },
    ],
    perform: scrape,
    sample: {
      success: true,
      data: {
        markdown: "# Example Domain\n\nThis domain is for use in documentation examples.",
        metadata: { statusCode: 200, sourceURL: "https://example.com" },
      },
    },
  },
};
