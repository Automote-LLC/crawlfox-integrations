using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace Crawlfox;

public sealed class CrawlfoxException : Exception
{
    public int Status { get; }
    public string? Code { get; }
    public bool? Retryable { get; }

    public CrawlfoxException(string message, int status, string? code = null, bool? retryable = null)
        : base(message)
    {
        Status = status;
        Code = code;
        Retryable = retryable;
    }
}

public sealed class Client : IDisposable
{
    private readonly HttpClient _http;
    private readonly bool _ownsHttp;

    public Client(string? apiKey = null, string apiUrl = "https://api.crawlfox.io", HttpClient? http = null)
    {
        var key = apiKey ?? Environment.GetEnvironmentVariable("CRAWLFOX_API_KEY");
        if (string.IsNullOrWhiteSpace(key))
        {
            throw new ArgumentException("CrawlFox API key required. Pass apiKey or set CRAWLFOX_API_KEY.");
        }
        _ownsHttp = http is null;
        _http = http ?? new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
        _http.BaseAddress = new Uri(apiUrl.TrimEnd('/') + "/");
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
        _http.DefaultRequestHeaders.UserAgent.ParseAdd("crawlfox-dotnet/0.1.0");
    }

    public async Task<JsonElement> Scrape(string url, object? options = null, CancellationToken ct = default)
    {
        var body = Merge(new Dictionary<string, object?> { ["url"] = url }, options);
        var env = await Post("v1/scrape", body, ct);
        return Document(env);
    }

    public async Task<JsonElement> Batch(IEnumerable<string> urls, object? options = null, CancellationToken ct = default)
    {
        var body = Merge(new Dictionary<string, object?> { ["urls"] = urls.ToArray() }, options);
        return await Post("v1/batch", body, ct);
    }

    public async Task<JsonElement> Search(string q, object? options = null, CancellationToken ct = default)
    {
        var body = Merge(new Dictionary<string, object?> { ["q"] = q }, options);
        return await Post("v1/search", body, ct);
    }

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
        if (env.TryGetProperty("data", out var data) && data.ValueKind == JsonValueKind.Object)
        {
            return data;
        }
        return env;
    }

    private async Task<JsonElement> Post(string path, object body, CancellationToken ct)
    {
        var json = JsonSerializer.Serialize(body);
        using var content = new StringContent(json, Encoding.UTF8, "application/json");
        using var res = await _http.PostAsync(path, content, ct);
        var raw = await res.Content.ReadAsStringAsync(ct);
        using var doc = JsonDocument.Parse(string.IsNullOrWhiteSpace(raw) ? "{}" : raw);
        var root = doc.RootElement.Clone();
        if (!res.IsSuccessStatusCode)
        {
            var msg = root.TryGetProperty("message", out var m) ? m.GetString() : $"CrawlFox request failed ({(int)res.StatusCode})";
            var code = root.TryGetProperty("code", out var c) ? c.GetString() : null;
            throw new CrawlfoxException(msg ?? "request failed", (int)res.StatusCode, code);
        }
        return root;
    }

    public void Dispose()
    {
        if (_ownsHttp) _http.Dispose();
    }
}
