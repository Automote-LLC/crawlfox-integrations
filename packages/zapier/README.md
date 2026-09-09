# CrawlFox Zapier app

Private Zapier Platform integration for scrape and search.

## Setup

```bash
cd packages/zapier
npm install
npx zapier login
npx zapier register "CrawlFox"
npx zapier push
```

## Actions

- **Scrape URL**: `POST /v1/scrape` (markdown and other formats)
- **Search Web**: `POST /v1/search` (Google or DuckDuckGo)

Users paste a CrawlFox API key (`cfx_...`) from the [dashboard](https://crawlfox.io).

After `zapier push`, share invite-only Zaps with your team. Public directory listing follows Zapier app review.

Docs: https://docs.crawlfox.io
