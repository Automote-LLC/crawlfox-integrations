package io.crawlfox;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

@EnabledIfEnvironmentVariable(named = "CRAWLFOX_API_KEY", matches = ".+")
class CrawlFoxLiveTest {
    @Test
    void liveScrapeSearchBatch() {
        String url = System.getenv().getOrDefault("CRAWLFOX_API_URL", "https://api.crawlfox.io");
        CrawlFox app = new CrawlFox(System.getenv("CRAWLFOX_API_KEY"), url);
        Map<String, Object> doc = app.scrape("https://example.com", Map.of("formats", List.of("markdown")));
        assertTrue(String.valueOf(doc.get("markdown")).length() > 10);
        @SuppressWarnings("unchecked")
        List<?> web = (List<?>) app.search("crawlfox", Map.of("engine", "google", "num", 3)).get("web");
        assertFalse(web.isEmpty());
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> data = (List<Map<String, Object>>) app
                .batch(List.of("https://example.com"), Map.of("formats", List.of("markdown")))
                .get("data");
        assertTrue(String.valueOf(data.get(0).get("markdown")).length() > 5);
    }
}
