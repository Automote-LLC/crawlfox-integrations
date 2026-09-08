# crawlfox (Ruby)

```bash
gem install crawlfox
```

Not published yet.

```ruby
require "crawlfox"

app = Crawlfox::Client.new
doc = app.scrape("https://example.com", formats: ["markdown"])
puts doc["markdown"]
hits = app.search("crawlfox", engine: "google", num: 5)
```
