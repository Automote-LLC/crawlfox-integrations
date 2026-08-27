# CrawlFox Zapier app

Private Zapier Platform integration for scrape and search actions.

## Setup

```bash
cd packages/zapier
npm install
npx zapier login
npx zapier register "CrawlFox"
npx zapier push
```

## Actions

- **Scrape URL** — `POST /v1/scrape`
- **Search Web** — `POST /v1/search`

Public Zapier directory listing requires Zapier app review after `zapier push`.
Test with invite-only Zaps until approved.

## Auth

Users paste a CrawlFox API key (`cfx_…`) from the dashboard.
