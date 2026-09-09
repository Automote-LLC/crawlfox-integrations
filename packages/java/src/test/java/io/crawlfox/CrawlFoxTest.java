package io.crawlfox;

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class CrawlFoxTest {
    private HttpServer server;

    @AfterEach
    void stop() {
        if (server != null) {
            server.stop(0);
        }
    }

    @Test
    void requiresApiKey() {
        assertThrows(IllegalArgumentException.class, () -> new CrawlFox(""));
        assertThrows(IllegalArgumentException.class, () -> new CrawlFox("   "));
    }

    @Test
    void scrapeSearchBatchLogsAndRetry() throws Exception {
        AtomicInteger scrapes = new AtomicInteger();
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/v1/scrape", ex -> {
            int n = scrapes.incrementAndGet();
            if (n == 1) {
                write(ex, 503, "{\"message\":\"busy\",\"retryable\":true}");
                return;
            }
            assertEquals("POST", ex.getRequestMethod());
            assertEquals("Bearer cfx_test", ex.getRequestHeaders().getFirst("Authorization"));
            assertTrue(ex.getRequestHeaders().getFirst("User-Agent").startsWith("crawlfox-java/"));
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            assertTrue(body.contains("example.com"));
            write(ex, 200, "{\"success\":true,\"data\":{\"markdown\":\"# Hello\"}}");
        });
        server.createContext("/v1/search", ex ->
                write(ex, 200, "{\"success\":true,\"data\":{\"web\":[{\"url\":\"https://example.com\"}]}}"));
        server.createContext("/v1/batch", ex ->
                write(ex, 200, "{\"success\":true,\"count\":1,\"results\":[{\"success\":true,\"data\":{\"markdown\":\"# A\"}}]}"));
        server.createContext("/v1/logs/log1/result", ex -> write(ex, 200, "{\"ok\":true}"));
        server.createContext("/v1/logs/log1", ex -> {
            assertEquals("GET", ex.getRequestMethod());
            write(ex, 200, "{\"id\":\"log1\",\"status\":\"ok\"}");
        });
        server.start();
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        CrawlFox app = new CrawlFox("cfx_test", base, Duration.ofSeconds(5), 2, 1, null);

        Map<String, Object> doc = app.scrape("https://example.com", Map.of("formats", List.of("markdown")));
        assertEquals("# Hello", doc.get("markdown"));
        assertEquals(2, scrapes.get());

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> web = (List<Map<String, Object>>) app.search("crawlfox", Map.of("engine", "google")).get("web");
        assertEquals("https://example.com", web.get(0).get("url"));

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> batch = (List<Map<String, Object>>) app.batch(List.of("https://example.org"), Map.of()).get("data");
        assertEquals("# A", batch.get(0).get("markdown"));

        assertEquals("ok", app.getLog("log1").get("status"));
        assertEquals(true, app.getLogResult("log1").get("ok"));
    }

    @Test
    void doesNotRetryQuota() throws Exception {
        AtomicInteger n = new AtomicInteger();
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/v1/scrape", ex -> {
            n.incrementAndGet();
            write(ex, 429, "{\"message\":\"quota\",\"retryable\":false,\"code\":\"quota\"}");
        });
        server.start();
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        CrawlFox app = new CrawlFox("cfx_test", base, Duration.ofSeconds(5), 2, 1, null);
        CrawlFox.CrawlFoxException err = assertThrows(CrawlFox.CrawlFoxException.class,
                () -> app.scrape("https://example.com"));
        assertEquals(429, err.status);
        assertEquals(1, n.get());
    }

    private static void write(com.sun.net.httpserver.HttpExchange ex, int status, String body) throws java.io.IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json");
        ex.sendResponseHeaders(status, bytes.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(bytes);
        }
    }
}
