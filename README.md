# crawlfox-integrations

Official CrawlFox SDKs and framework integrations for the public API (`https://api.crawlfox.io`).

## Packages

| Package | Install | Description |
|---------|---------|-------------|
| **crawlfox** | `npm install crawlfox` | JavaScript / TypeScript SDK |
| **crawlfox-py** | `pip install crawlfox-py` | Python SDK |
| **crawlfox (Go)** | `go get github.com/Automote-LLC/crawlfox-integrations/packages/go` | Go SDK |
| **crawlfox (Rust)** | path/git crate `crawlfox` | Rust SDK |
| **crawlfox (PHP)** | `composer require crawlfox/crawlfox` | PHP SDK |
| **crawlfox (Java)** | `io.crawlfox:crawlfox` | Java 17+ SDK |
| **crawlfox (.NET)** | `Crawlfox` NuGet | .NET SDK |
| **crawlfox (Ruby)** | `gem install crawlfox` | Ruby SDK |
| **crawlfox (Elixir)** | `{:crawlfox, "~> 0.1.0"}` | Elixir SDK |
| **crawlfox-aisdk** | `npm install crawlfox-aisdk` | Vercel AI SDK tools |
| **langchain-crawlfox** | `pip install langchain-crawlfox` | LangChain loaders & tools |
| **crawlfox-llamaindex** | `pip install crawlfox-llamaindex` | LlamaIndex web reader |
| **crawlfox-crewai** | `pip install crawlfox-crewai` | CrewAI agent tools |
| **n8n-nodes-crawlfox** | Community node for n8n | Scrape & search in workflows |
| **zapier** | Zapier Platform CLI app | Scrape & search actions |

## Live API surface

- `POST /v1/scrape` — scrape one URL
- `POST /v1/batch` — scrape up to 100 URLs
- `POST /v1/search` — web search
- `GET /v1/logs/:id` — request logs

SDKs cover scrape, batch, search, streaming search, and logs.

## Auth

Set `CRAWLFOX_API_KEY` or pass `apiKey` to the client constructor. Keys are sent as `Authorization: Bearer <key>`.

## Docs

Integration guides live at [docs.crawlfox.io](https://docs.crawlfox.io).

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
