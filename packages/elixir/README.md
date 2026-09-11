# crawlfox (Elixir)

Official Elixir SDK for the [CrawlFox](https://crawlfox.io) API: scrape, search (Google, Bing, or DuckDuckGo), batch scrape, and logs.

Get a key from the [dashboard](https://crawlfox.io). Set `CRAWLFOX_API_KEY`.

Hex once published:

```elixir
{:crawlfox, "~> 0.1.0"}
```

Until Hex lists it:

```elixir
{:crawlfox,
 git: "https://github.com/Automote-LLC/crawlfox-integrations.git",
 sparse: "packages/elixir"}
```

```elixir
client = Crawlfox.new()

page = Crawlfox.scrape(client, "https://example.com", %{
  "formats" => ["markdown", "links"]
})

hits = Crawlfox.search(client, "rust async tutorial", %{
  "engine" => "google",
  "num" => 10
})

batch = Crawlfox.batch(client, ["https://example.com/", "https://example.org/"], %{
  "formats" => ["markdown"]
})
```

Formats: `markdown`, `html`, `rawHtml`, `json`, `links`, `images`, `emails`. CSS selectors live under `jsonOptions` when you request `json`. Credits: 1 per page, 1 per 10 requested search results.

```bash
mix deps.get && mix test
```

Docs: https://docs.crawlfox.io
