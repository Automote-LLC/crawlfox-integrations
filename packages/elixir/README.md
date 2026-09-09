# crawlfox (Elixir)

Official Elixir SDK for the [CrawlFox](https://crawlfox.io) scrape and search API.

```elixir
{:crawlfox, "~> 0.1.0"}
```

```elixir
client = Crawlfox.new()
page = Crawlfox.scrape(client, "https://example.com", %{"formats" => ["markdown"]})
hits = Crawlfox.search(client, "crawlfox", %{"engine" => "google", "num" => 5})
```

```bash
mix deps.get && mix test
```
