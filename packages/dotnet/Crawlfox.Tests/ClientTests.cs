using System.Net;
using System.Text;
using Xunit;

namespace Crawlfox.Tests;

public class ClientTests
{
    [Fact]
    public void RequiresApiKey()
    {
        Assert.Throws<ArgumentException>(() => new Client(""));
        Assert.Throws<ArgumentException>(() => new Client("   "));
    }

    [Fact]
    public async Task ScrapeSearchBatchLogsAndRetry()
    {
        var scrapes = 0;
        var handler = new StubHandler(req =>
        {
            var path = req.RequestUri!.AbsolutePath;
            if (path == "/v1/scrape")
            {
                scrapes++;
                if (scrapes == 1)
                {
                    return Json(503, """{"message":"busy","retryable":true}""");
                }
                Assert.Equal("Bearer cfx_test", req.Headers.Authorization?.ToString());
                Assert.StartsWith("crawlfox-dotnet/", req.Headers.UserAgent.ToString());
                return Json(200, """{"success":true,"data":{"markdown":"# Hello"}}""");
            }
            if (path == "/v1/search")
            {
                return Json(200, """{"success":true,"data":{"web":[{"url":"https://example.com"}]}}""");
            }
            if (path == "/v1/batch")
            {
                return Json(200, """{"success":true,"count":1,"results":[{"success":true,"data":{"markdown":"# A"}}]}""");
            }
            if (path == "/v1/logs/log1/result")
            {
                return Json(200, """{"ok":true}""");
            }
            if (path == "/v1/logs/log1")
            {
                Assert.Equal(HttpMethod.Get, req.Method);
                return Json(200, """{"id":"log1","status":"ok"}""");
            }
            return Json(404, "{}");
        });
        using var http = new HttpClient(handler);
        using var app = new Client("cfx_test", "https://api.test", http, maxRetries: 2, retryBackoffMs: 1);

        var doc = await app.Scrape("https://example.com", new { formats = new[] { "markdown" } });
        Assert.Equal("# Hello", doc.GetProperty("markdown").GetString());
        Assert.Equal(2, scrapes);

        var search = await app.Search("crawlfox", new { engine = "google", num = 5 });
        Assert.Equal("https://example.com", search.GetProperty("web")[0].GetProperty("url").GetString());

        var batch = await app.Batch(new[] { "https://example.org" });
        Assert.Equal("# A", batch.GetProperty("data")[0].GetProperty("markdown").GetString());

        var log = await app.GetLog("log1");
        Assert.Equal("ok", log.GetProperty("status").GetString());
        Assert.True((await app.GetLogResult("log1")).GetProperty("ok").GetBoolean());
    }

    [Fact]
    public async Task DoesNotRetryQuota()
    {
        var n = 0;
        var handler = new StubHandler(_ =>
        {
            n++;
            return Json(429, """{"message":"quota","retryable":false,"code":"quota"}""");
        });
        using var http = new HttpClient(handler);
        using var app = new Client("cfx_test", "https://api.test", http, maxRetries: 2, retryBackoffMs: 1);
        var err = await Assert.ThrowsAsync<CrawlfoxException>(() => app.Scrape("https://example.com"));
        Assert.Equal(429, err.Status);
        Assert.Equal(1, n);
    }

    private static HttpResponseMessage Json(int status, string body) =>
        new((HttpStatusCode)status)
        {
            Content = new StringContent(body, Encoding.UTF8, "application/json"),
        };

    private sealed class StubHandler : HttpMessageHandler
    {
        private readonly Func<HttpRequestMessage, HttpResponseMessage> _impl;
        public StubHandler(Func<HttpRequestMessage, HttpResponseMessage> impl) => _impl = impl;
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) =>
            Task.FromResult(_impl(request));
    }
}

public class LiveTests
{
    [Fact]
    public async Task LiveScrapeSearchBatch()
    {
        var key = ResolveLiveKey();
        if (string.IsNullOrWhiteSpace(key))
        {
            return; // skipped when CRAWLFOX_API_KEY is unset
        }
        var apiUrl = Environment.GetEnvironmentVariable("CRAWLFOX_API_URL") ?? "https://api.crawlfox.io";
        using var app = new Client(key, apiUrl, maxRetries: 1);
        var doc = await app.Scrape("https://example.com", new { formats = new[] { "markdown" } });
        Assert.True(doc.GetProperty("markdown").GetString()!.Length > 10);
        var search = await app.Search("crawlfox", new { engine = "google", num = 3 });
        Assert.True(search.GetProperty("web").GetArrayLength() > 0);
        var batch = await app.Batch(new[] { "https://example.com" }, new { formats = new[] { "markdown" } });
        Assert.True(batch.GetProperty("data")[0].GetProperty("markdown").GetString()!.Length > 5);
    }

    private static string? ResolveLiveKey()
    {
        var key = Environment.GetEnvironmentVariable("CRAWLFOX_API_KEY");
        if (!string.IsNullOrWhiteSpace(key)) return key;
        var file = Environment.GetEnvironmentVariable("CRAWLFOX_API_KEY_FILE");
        if (!string.IsNullOrWhiteSpace(file) && File.Exists(file))
        {
            return File.ReadAllText(file).Trim();
        }
        return null;
    }
}
