using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace Crawlfox;

public sealed class CrawlfoxException : Exception
{
    public int Status { get; }
    public string? Code { get; }
    public bool? Retryable { get; }
    public JsonElement Body { get; }

    public CrawlfoxException(string message, int status, string? code = null, bool? retryable = null, JsonElement body = default)
        : base(message)
    {
        Status = status;
        Code = code;
        Retryable = retryable;
        Body = body;
    }

    internal bool RetryableEffective()
    {
        if (Retryable == false) return false;
        if (Retryable == true) return true;
        return Status is 502 or 503 or 504;
    }
}

public sealed class Client : IDisposable
{
    public const string Version = "0.1.0";
    private readonly HttpClient _http;
    private readonly bool _ownsHttp;
    private readonly int _maxRetries;
    private readonly int _retryBackoffMs;

    public Client(
        string? apiKey = null,
        string? apiUrl = null,
        HttpClient? http = null,
        int maxRetries = 2,
        int retryBackoffMs = 200)
    {
        var key = apiKey ?? Environment.GetEnvironmentVariable("CRAWLFOX_API_KEY");
        if (string.IsNullOrWhiteSpace(key))
        {
            throw new ArgumentException("CrawlFox API key required. Pass apiKey or set CRAWLFOX_API_KEY.");
        }
        var baseUrl = apiUrl
            ?? Environment.GetEnvironmentVariable("CRAWLFOX_API_URL")
            ?? "https://api.crawlfox.io";
        _ownsHttp = http is null;
        _http = http ?? new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
        _http.BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/");
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
        _http.DefaultRequestHeaders.UserAgent.Clear();
        _http.DefaultRequestHeaders.UserAgent.ParseAdd($"crawlfox-dotnet/{Version}");
        _maxRetries = Math.Max(0, maxRetries);
        _retryBackoffMs = retryBackoffMs;
    }

    public async Task<JsonElement> Scrape(string url, object? options = null, CancellationToken ct = default)
    {
        var body = Merge(new Dictionary<string, object?> { ["url"] = url }, options);
        return Document(await Request("POST", "v1/scrape", body, ct));
    }

    public async Task<JsonElement> ScrapeGet(string url, CancellationToken ct = default)
    {
        return Document(await Request("GET", "v1/scrape/" + Uri.EscapeDataString(url), null, ct));
    }

    public async Task<JsonElement> Batch(IEnumerable<string> urls, object? options = null, CancellationToken ct = default)
    {
        var body = Merge(new Dictionary<string, object?> { ["urls"] = urls.ToArray() }, options);
        var env = await Request("POST", "v1/batch", body, ct);
        var data = new List<JsonElement>();
        if (env.TryGetProperty("results", out var results) && results.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in results.EnumerateArray())
            {
                data.Add(Document(item));
            }
        }
        using var doc = JsonDocument.Parse(JsonSerializer.Serialize(new
        {
            success = env.TryGetProperty("success", out var s) && s.ValueKind == JsonValueKind.True,
            count = env.TryGetProperty("count", out var c) && c.ValueKind == JsonValueKind.Number ? c.GetInt32() : data.Count,
            data,
        }));
        return doc.RootElement.Clone();
    }

    public async Task<JsonElement> Search(string q, object? options = null, CancellationToken ct = default)
    {
        var body = Merge(new Dictionary<string, object?> { ["q"] = q }, options);
        var env = await Request("POST", "v1/search", body, ct);
        JsonElement web = default;
        if (env.TryGetProperty("data", out var data) && data.TryGetProperty("web", out var w))
        {
            web = w;
        }
        using var doc = JsonDocument.Parse(JsonSerializer.Serialize(new Dictionary<string, object?>
        {
            ["success"] = !env.TryGetProperty("success", out var s) || s.GetBoolean(),
            ["web"] = web.ValueKind == JsonValueKind.Undefined ? Array.Empty<object>() : JsonSerializer.Deserialize<object>(web.GetRawText()),
            ["creditsUsed"] = env.TryGetProperty("creditsUsed", out var cu) ? JsonSerializer.Deserialize<object>(cu.GetRawText()) : null,
            ["id"] = env.TryGetProperty("id", out var id) ? id.GetString() : null,
        }));
        return doc.RootElement.Clone();
    }

    public Task<JsonElement> GetLog(string id, CancellationToken ct = default) =>
        Request("GET", "v1/logs/" + Uri.EscapeDataString(id), null, ct);

    public Task<JsonElement> GetLogResult(string id, CancellationToken ct = default) =>
        Request("GET", "v1/logs/" + Uri.EscapeDataString(id) + "/result", null, ct);

    private static Dictionary<string, object?> Merge(Dictionary<string, object?> baseBody, object? options)
    {
        if (options is null) return baseBody;
        var extra = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(JsonSerializer.Serialize(options));
        if (extra is null) return baseBody;
        foreach (var kv in extra) baseBody[kv.Key] = kv.Value;
        return baseBody;
    }

    private static JsonElement Document(JsonElement env)
    {
        var src = env.TryGetProperty("data", out var data) && data.ValueKind == JsonValueKind.Object
            ? data
            : env;
        var map = JsonSerializer.Deserialize<Dictionary<string, object?>>(src.GetRawText()) ?? new();
        map["success"] = !env.TryGetProperty("success", out var s) || s.ValueKind != JsonValueKind.False;
        using var doc = JsonDocument.Parse(JsonSerializer.Serialize(map));
        return doc.RootElement.Clone();
    }

    private async Task<JsonElement> Request(string method, string path, object? body, CancellationToken ct)
    {
        CrawlfoxException? last = null;
        var attempts = _maxRetries + 1;
        for (var i = 0; i < attempts; i++)
        {
            using var req = new HttpRequestMessage(new HttpMethod(method), path);
            if (body is not null)
            {
                req.Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
            }
            using var res = await _http.SendAsync(req, ct);
            var raw = await res.Content.ReadAsStringAsync(ct);
            using var parsed = JsonDocument.Parse(string.IsNullOrWhiteSpace(raw) ? "{}" : raw);
            var root = parsed.RootElement.Clone();
            if (res.IsSuccessStatusCode)
            {
                return root;
            }
            var msg = root.TryGetProperty("message", out var m) ? m.GetString() : $"CrawlFox request failed ({(int)res.StatusCode})";
            var code = root.TryGetProperty("code", out var c) ? c.GetString() : null;
            bool? retryable = root.TryGetProperty("retryable", out var r) && r.ValueKind is JsonValueKind.True or JsonValueKind.False
                ? r.GetBoolean()
                : null;
            var err = new CrawlfoxException(msg ?? "request failed", (int)res.StatusCode, code, retryable, root);
            if (i < attempts - 1 && err.RetryableEffective())
            {
                last = err;
                await Task.Delay(_retryBackoffMs * (1 << i), ct);
                continue;
            }
            throw err;
        }
        throw last ?? new CrawlfoxException("Request failed", 0);
    }

    public void Dispose()
    {
        if (_ownsHttp) _http.Dispose();
    }
}
