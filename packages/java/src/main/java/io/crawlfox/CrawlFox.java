package io.crawlfox;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Official CrawlFox Java client for scrape, batch, search, and logs. */
public final class CrawlFox {
    public static final String VERSION = "0.1.0";
    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final TypeReference<Map<String, Object>> MAP = new TypeReference<>() {};

    private final String apiKey;
    private final String apiUrl;
    private final Duration timeout;
    private final int maxRetries;
    private final long retryBackoffMs;
    private final HttpClient http;

    public CrawlFox() {
        this(null, null, Duration.ofSeconds(120), 2, 200, null);
    }

    public CrawlFox(String apiKey) {
        this(apiKey, null, Duration.ofSeconds(120), 2, 200, null);
    }

    public CrawlFox(String apiKey, String apiUrl) {
        this(apiKey, apiUrl, Duration.ofSeconds(120), 2, 200, null);
    }

    public CrawlFox(
            String apiKey,
            String apiUrl,
            Duration timeout,
            int maxRetries,
            long retryBackoffMs,
            HttpClient http) {
        String key;
        if (apiKey != null) {
            key = apiKey;
        } else {
            key = System.getenv("CRAWLFOX_API_KEY");
        }
        if (key == null || key.isBlank()) {
            throw new IllegalArgumentException(
                    "CrawlFox API key required. Pass apiKey or set CRAWLFOX_API_KEY.");
        }
        String base = apiUrl != null && !apiUrl.isBlank()
                ? apiUrl
                : envOr("CRAWLFOX_API_URL", "https://api.crawlfox.io");
        this.apiKey = key;
        this.apiUrl = base.replaceAll("/$", "");
        this.timeout = timeout == null ? Duration.ofSeconds(120) : timeout;
        this.maxRetries = Math.max(0, maxRetries);
        this.retryBackoffMs = retryBackoffMs;
        this.http = http != null
                ? http
                : HttpClient.newBuilder().connectTimeout(this.timeout).build();
    }

    public Map<String, Object> scrape(String url) {
        return scrape(url, Map.of("formats", List.of("markdown")));
    }

    public Map<String, Object> scrape(String url, Map<String, Object> options) {
        Map<String, Object> body = new HashMap<>();
        if (options != null) {
            body.putAll(options);
        }
        body.put("url", url);
        return document(request("POST", "/v1/scrape", body));
    }

    public Map<String, Object> scrapeGet(String url) {
        return document(request("GET", "/v1/scrape/" + urlEncode(url), null));
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> batch(List<String> urls, Map<String, Object> options) {
        Map<String, Object> body = new HashMap<>();
        if (options != null) {
            body.putAll(options);
        }
        body.put("urls", urls);
        Map<String, Object> env = request("POST", "/v1/batch", body);
        List<Map<String, Object>> data = new ArrayList<>();
        Object results = env.get("results");
        if (results instanceof List<?> list) {
            for (Object item : list) {
                if (item instanceof Map<?, ?> m) {
                    data.add(document((Map<String, Object>) m));
                }
            }
        }
        Map<String, Object> out = new HashMap<>();
        out.put("success", env.getOrDefault("success", true));
        out.put("count", env.getOrDefault("count", data.size()));
        out.put("data", data);
        return out;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> search(String q, Map<String, Object> options) {
        Map<String, Object> body = new HashMap<>();
        if (options != null) {
            body.putAll(options);
        }
        body.put("q", q);
        Map<String, Object> env = request("POST", "/v1/search", body);
        Map<String, Object> data = env.get("data") instanceof Map<?, ?> m
                ? (Map<String, Object>) m
                : Map.of();
        Map<String, Object> out = new HashMap<>();
        out.put("success", env.getOrDefault("success", true));
        out.put("web", data.getOrDefault("web", List.of()));
        out.put("creditsUsed", env.get("creditsUsed"));
        out.put("id", env.get("id"));
        return out;
    }

    public Map<String, Object> getLog(String id) {
        return request("GET", "/v1/logs/" + urlEncode(id), null);
    }

    public Map<String, Object> getLogResult(String id) {
        return request("GET", "/v1/logs/" + urlEncode(id) + "/result", null);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> document(Map<String, Object> envelope) {
        Map<String, Object> data = envelope.get("data") instanceof Map<?, ?> m
                ? new HashMap<>((Map<String, Object>) m)
                : new HashMap<>(envelope);
        data.put("success", envelope.getOrDefault("success", true));
        return data;
    }

    private Map<String, Object> request(String method, String path, Map<String, Object> body) {
        CrawlFoxException last = null;
        int attempts = maxRetries + 1;
        for (int i = 0; i < attempts; i++) {
            try {
                HttpRequest.Builder b = HttpRequest.newBuilder()
                        .uri(URI.create(apiUrl + path))
                        .timeout(timeout)
                        .header("Authorization", "Bearer " + apiKey)
                        .header("User-Agent", "crawlfox-java/" + VERSION);
                if (body != null) {
                    b.header("Content-Type", "application/json");
                    b.method(method, HttpRequest.BodyPublishers.ofString(write(body)));
                } else {
                    b.method(method, HttpRequest.BodyPublishers.noBody());
                }
                HttpResponse<String> res = http.send(b.build(), HttpResponse.BodyHandlers.ofString());
                Map<String, Object> json = parse(res.body());
                if (res.statusCode() >= 200 && res.statusCode() < 300) {
                    return json;
                }
                CrawlFoxException err = errorFrom(res.statusCode(), json);
                if (i < attempts - 1 && err.retryableEffective()) {
                    last = err;
                    sleep(retryBackoffMs * (1L << i));
                    continue;
                }
                throw err;
            } catch (CrawlFoxException e) {
                throw e;
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new CrawlFoxException("interrupted", 0, null, true, Map.of());
            } catch (Exception e) {
                throw new CrawlFoxException(e.getMessage(), 0, null, true, Map.of());
            }
        }
        throw Objects.requireNonNullElse(last, new CrawlFoxException("Request failed", 0, null, null, Map.of()));
    }

    private static CrawlFoxException errorFrom(int status, Map<String, Object> json) {
        Object retry = json.get("retryable");
        Boolean retryable = retry instanceof Boolean b ? b : null;
        String msg = str(json.get("message"));
        if (msg == null) {
            msg = str(json.get("title"));
        }
        if (msg == null) {
            msg = "CrawlFox request failed (" + status + ")";
        }
        return new CrawlFoxException(msg, status, str(json.get("code")), retryable, json);
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v);
    }

    private static Map<String, Object> parse(String raw) {
        if (raw == null || raw.isBlank()) {
            return new HashMap<>();
        }
        try {
            Map<String, Object> m = MAPPER.readValue(raw, MAP);
            return m == null ? new HashMap<>() : m;
        } catch (Exception e) {
            return new HashMap<>();
        }
    }

    private static String write(Map<String, Object> body) {
        try {
            return MAPPER.writeValueAsString(body);
        } catch (Exception e) {
            throw new CrawlFoxException("encode failed", 0, null, null, Map.of());
        }
    }

    private static String urlEncode(String s) {
        return URLEncoder.encode(s, StandardCharsets.UTF_8);
    }

    private static String envOr(String name, String fallback) {
        String v = System.getenv(name);
        return v == null || v.isBlank() ? fallback : v;
    }

    private static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static final class CrawlFoxException extends RuntimeException {
        public final int status;
        public final String code;
        public final Boolean retryable;
        public final Map<String, Object> body;

        public CrawlFoxException(String message, int status, String code, Boolean retryable, Map<String, Object> body) {
            super(message);
            this.status = status;
            this.code = code;
            this.retryable = retryable;
            this.body = body == null ? Map.of() : body;
        }

        boolean retryableEffective() {
            if (Boolean.FALSE.equals(retryable)) {
                return false;
            }
            if (Boolean.TRUE.equals(retryable)) {
                return true;
            }
            return status == 502 || status == 503 || status == 504;
        }
    }
}
