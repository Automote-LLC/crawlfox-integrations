# crawlfox (Elixir)

```elixir
{:crawlfox, "~> 0.1.0"}
```

Not published yet.

```elixir
client = Crawlfox.new()
page = Crawlfox.scrape(client, "https://example.com", %{"formats" => ["markdown"]})
hits = Crawlfox.search(client, "crawlfox", %{"engine" => "google", "num" => 5})
```
