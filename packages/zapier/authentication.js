module.exports = {
  type: "custom",
  test: {
    url: "https://api.crawlfox.io/v1/scrape",
    method: "POST",
    body: { url: "https://example.com", formats: ["markdown"] },
  },
  fields: [
    {
      key: "apiKey",
      label: "API Key",
      type: "string",
      required: true,
      helpText: "Your CrawlFox API key from https://crawlfox.io/dashboard/keys",
    },
  ],
  connectionLabel: "{{bundle.authData.apiKey}}",
};
