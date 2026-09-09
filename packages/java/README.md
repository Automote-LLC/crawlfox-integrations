# crawlfox (Java)

Official Java 17+ SDK for the [CrawlFox](https://crawlfox.io) API: scrape, search (Google, Bing, or DuckDuckGo), batch scrape, and logs.

Get a key from the [dashboard](https://crawlfox.io). Set `CRAWLFOX_API_KEY`.

Maven: `io.crawlfox:crawlfox:0.1.0`

```java
import io.crawlfox.CrawlFox;
import java.util.List;
import java.util.Map;

CrawlFox app = new CrawlFox(System.getenv("CRAWLFOX_API_KEY"));

Map<String, Object> page = app.scrape("https://example.com", Map.of(
    "formats", List.of("markdown", "links")
));

Map<String, Object> hits = app.search("rust async tutorial", Map.of(
    "engine", "google",
    "num", 10
));

Map<String, Object> batch = app.batch(
    List.of("https://example.com/", "https://example.org/"),
    Map.of("formats", List.of("markdown"))
);
```

Formats: `markdown`, `html`, `rawHtml`, `json`, `links`, `images`, `emails`. CSS selectors go in `jsonOptions` when you ask for `json`. Credits: 1 per page, 1 per 10 requested search results.

`mvn test`. Set `CRAWLFOX_API_KEY` for live scrape/search/batch.

Docs: https://docs.crawlfox.io
