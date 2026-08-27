const search = async (z, bundle) => {
  const response = await z.request({
    url: "https://api.crawlfox.io/v1/search",
    method: "POST",
    body: {
      q: bundle.inputData.q,
      engine: bundle.inputData.engine || "google",
      num: bundle.inputData.num || 10,
    },
  });
  return response.data;
};

module.exports = {
  key: "search_web",
  noun: "Search",
  display: {
    label: "Search Web",
    description: "Search Google, Bing, or DuckDuckGo and return organic results via CrawlFox.",
  },
  operation: {
    inputFields: [
      { key: "q", label: "Query", type: "string", required: true },
      {
        key: "engine",
        label: "Engine",
        type: "string",
        choices: ["google", "bing", "duckduckgo"],
        default: "google",
      },
      { key: "num", label: "Result Count", type: "integer", default: "10" },
    ],
    perform: search,
    sample: {
      success: true,
      data: {
        web: [
          {
            url: "https://example.com",
            title: "Example",
            description: "Example domain",
            position: 1,
          },
        ],
      },
    },
  },
};
