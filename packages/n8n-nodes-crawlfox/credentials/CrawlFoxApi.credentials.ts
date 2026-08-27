{
  "name": "CrawlFox API",
  "displayName": "CrawlFox API",
  "properties": [
    {
      "displayName": "API Key",
      "name": "apiKey",
      "type": "string",
      "typeOptions": { "password": true },
      "default": "",
      "required": true
    }
  ],
  "authenticate": {
    "type": "generic",
    "properties": {
      "headers": { "Authorization": "Bearer {{bundle.authData.apiKey}}" }
    }
  },
  "test": {
    "url": "https://api.crawlfox.io/v1/scrape",
    "method": "POST",
    "body": { "url": "https://example.com", "formats": ["markdown"] }
  }
}
