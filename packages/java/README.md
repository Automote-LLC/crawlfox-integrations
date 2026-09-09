# crawlfox (Java)

Official Java SDK for the [CrawlFox](https://crawlfox.io) scrape and search API.

Maven: `io.crawlfox:crawlfox:0.1.0`

```java
import io.crawlfox.CrawlFox;

CrawlFox app = new CrawlFox(System.getenv("CRAWLFOX_API_KEY"));
Map<String, Object> page = app.scrape("https://example.com");
Map<String, Object> hits = app.search("crawlfox", Map.of("engine", "google", "num", 5));
```

Java 17+. `mvn test` runs the suite; set `CRAWLFOX_API_KEY` for live scrape/search/batch.
