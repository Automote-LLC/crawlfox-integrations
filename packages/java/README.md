# crawlfox (Java)

Maven coordinates (not published yet): `io.crawlfox:crawlfox:0.1.0`

```java
import io.crawlfox.CrawlFox;

CrawlFox app = new CrawlFox(System.getenv("CRAWLFOX_API_KEY"));
String page = app.scrapeUrl("https://example.com");
String hits = app.search("crawlfox");
```

Requires Java 17+.
