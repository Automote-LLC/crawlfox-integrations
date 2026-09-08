package io.crawlfox;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Thin official CrawlFox Java client (scrape / batch / search).
 * Robust typing and retries can land later; this ships the HTTP surface.
 */
public final class CrawlFox {
    private final String apiKey;
    private final String apiUrl;
    private final HttpClient http;

    public CrawlFox(String apiKey) {
        this(apiKey, "https://api.crawlfox.io", Duration.ofSeconds(120));
    }

    public CrawlFox(String apiKey, String apiUrl, Duration timeout) {
        String key = apiKey != null && !apiKey.isBlank()
            ? apiKey
            : System.getenv("CRAWLFOX_API_KEY");
        if (key == null || key.isBlank()) {
            throw new IllegalArgumentException(
                "CrawlFox API key required. Pass apiKey or set CRAWLFOX_API_KEY.");
        }
        this.apiKey = key;
        this.apiUrl = apiUrl.replaceAll("/$", "");
        this.http = HttpClient.newBuilder().connectTimeout(timeout).build();
    }

    public String scrape(String url, String jsonOptionsBody) {
        String body = jsonOptionsBody == null || jsonOptionsBody.isBlank()
            ? "{\"url\":\"" + escape(url) + "\",\"formats\":[\"markdown\"]}"
            : jsonOptionsBody;
        return post("/v1/scrape", body);
    }

    public String scrapeUrl(String url) {
        return scrape(url, null);
    }

    public String batch(String jsonBody) {
        return post("/v1/batch", jsonBody);
    }

    public String search(String q) {
        return post("/v1/search", "{\"q\":\"" + escape(q) + "\",\"num\":5}");
    }

    public String search(String jsonBody) {
        return post("/v1/search", jsonBody);
    }

    public String post(String path, String jsonBody) {
        try {
            HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl + path))
                .timeout(Duration.ofSeconds(120))
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .header("User-Agent", "crawlfox-java/0.1.0")
                .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                .build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() < 200 || res.statusCode() >= 300) {
                throw new CrawlFoxException(res.statusCode(), res.body());
            }
            return res.body();
        } catch (CrawlFoxException e) {
            throw e;
        } catch (Exception e) {
            throw new CrawlFoxException(0, e.getMessage());
        }
    }

    private static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    public static final class CrawlFoxException extends RuntimeException {
        public final int status;
        public final String body;

        public CrawlFoxException(int status, String body) {
            super("CrawlFox request failed (" + status + "): " + body);
            this.status = status;
            this.body = body;
        }
    }
}
