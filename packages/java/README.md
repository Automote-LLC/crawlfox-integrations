# crawlfox (Java)

Maven coordinates (not published yet): `io.crawlfox:crawlfox:0.1.0`

```java
import io.crawlfox.CrawlFox;

CrawlFox app = new CrawlFox(System.getenv("CRAWLFOX_API_KEY"));
Map<String, Object> page = app.scrape("https://example.com");
Map<String, Object> hits = app.search("crawlfox", Map.of("engine", "google", "num", 5));
```

Requires Java 17+. `mvn test` runs unit tests; set `CRAWLFOX_API_KEY` for live tests.
