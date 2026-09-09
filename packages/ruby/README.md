# crawlfox (Ruby)

Official Ruby SDK for the [CrawlFox](https://crawlfox.io) API: scrape, search (Google or DuckDuckGo), batch (up to 100 URLs), and logs.

Get a key from the [dashboard](https://crawlfox.io). Set `CRAWLFOX_API_KEY`.

```bash
gem install crawlfox
```

```ruby
require "crawlfox"

app = Crawlfox::Client.new

doc = app.scrape("https://example.com", formats: ["markdown", "links"])
puts doc["markdown"]

hits = app.search("rust async tutorial", engine: "google", num: 10)

batch = app.batch(
  ["https://example.com/", "https://example.org/"],
  formats: ["markdown"]
)
```

Formats: `markdown`, `html`, `rawHtml`, `json`, `links`, `images`, `emails`. Use `json_options` / CSS selectors for `json`. Credits: 1 per page, 1 per 10 requested search results.

```bash
ruby -Ilib:test test/client_test.rb
```

Docs: https://docs.crawlfox.io
