# crawlfox-integrations

Official CrawlFox SDKs and adapters for `https://api.crawlfox.io`.

Get a key from the [dashboard](https://crawlfox.io). Every request uses `Authorization: Bearer`. Do not ship keys in browsers.

## Packages

| Package | Install | Description |
|---------|---------|-------------|
| **crawlfox** | `npm install crawlfox` | JavaScript / TypeScript SDK |
| **crawlfox-py** | `pip install crawlfox-py` | Python SDK (sync and async) |
| **crawlfox (Go)** | `go get github.com/Automote-LLC/crawlfox-integrations/packages/go` | Go SDK |
| **crawlfox (Rust)** | git/path crate `crawlfox` | Rust SDK |
| **crawlfox (PHP)** | `composer require crawlfox/crawlfox` | PHP SDK |
| **crawlfox (Java)** | `io.crawlfox:crawlfox` | Java 17+ SDK |
| **crawlfox (.NET)** | `Crawlfox` NuGet | .NET SDK |
| **crawlfox (Ruby)** | `gem install crawlfox` | Ruby SDK |
| **crawlfox (Elixir)** | `{:crawlfox, "~> 0.1.0"}` | Elixir SDK |
| **crawlfox-aisdk** | `npm install crawlfox-aisdk` | Vercel AI SDK tools |
| **langchain-crawlfox** | `pip install langchain-crawlfox` | LangChain loaders and tools |
| **crawlfox-llamaindex** | `pip install crawlfox-llamaindex` | LlamaIndex web reader |
| **crawlfox-crewai** | `pip install crawlfox-crewai` | CrewAI agent tools |
| **n8n-nodes-crawlfox** | Community node for n8n | Scrape and search in workflows |
| **zapier** | Zapier Platform CLI app | Scrape and search actions |

JavaScript on npm: https://www.npmjs.com/package/crawlfox

## API the SDKs cover

| Method | Path | What you get |
| --- | --- | --- |
| scrape | `POST /v1/scrape` | One URL. Formats: markdown, html, rawHtml, json, links, images, emails |
| scrape GET | `GET /v1/scrape/:url` | Lightweight scrape of an encoded URL |
| batch | `POST /v1/batch` | Many URLs, same formats, order preserved |
| search | `POST /v1/search` | Google, Bing, or DuckDuckGo |
| search stream | `POST /v1/search/stream` | NDJSON `page` / `done` / `error` |
| logs | `GET /v1/logs/:id` | Status and timing (`metadata.scrapeId` or search `id`) |
| log result | `GET /v1/logs/:id/result` | Stored scrape body |

Credits: 1 per scraped page, 1 per 10 requested search results.

Auth: `CRAWLFOX_API_KEY` or constructor `apiKey` / `api_key` / `APIKey`.

## MCP

Agents can use the same API through `https://mcp.crawlfox.io/mcp` (OAuth). That is not this repo. See https://docs.crawlfox.io

## Docs

- https://docs.crawlfox.io
- OpenAPI: https://crawlfox.io/openapi.json

## Development

```bash
# JavaScript SDK
cd packages/js && npm install && npm test && npm run build

# Python SDK
cd packages/python && pip install -e ".[dev]" && pytest

# Go SDK
cd packages/go && go test ./...

# Rust SDK
cd packages/rust && cargo test

# PHP
cd packages/php && composer install && vendor/bin/phpunit

# Java
cd packages/java && mvn test

# .NET
cd packages/dotnet && dotnet test Crawlfox.Tests/Crawlfox.Tests.csproj

# Ruby
cd packages/ruby && ruby -Ilib:test test/client_test.rb

# Elixir
cd packages/elixir && mix deps.get && mix test
```

Set `CRAWLFOX_API_KEY` (and optionally `CRAWLFOX_API_URL`) to run live scrape/search/batch tests against production.

GitHub Actions CI runs all nine language SDKs. Add repo secrets `CRAWLFOX_API_KEY` and optional `CRAWLFOX_API_URL` to enable live tests in CI.
