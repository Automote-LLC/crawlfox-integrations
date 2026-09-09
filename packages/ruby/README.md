# crawlfox (Ruby)

Official Ruby SDK for the [CrawlFox](https://crawlfox.io) scrape and search API.

```bash
gem install crawlfox
```

```ruby
require "crawlfox"

app = Crawlfox::Client.new
doc = app.scrape("https://example.com", formats: ["markdown"])
puts doc["markdown"]
hits = app.search("crawlfox", engine: "google", num: 5)
```

```bash
ruby -Ilib:test test/client_test.rb
```
