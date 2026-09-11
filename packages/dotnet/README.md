# Crawlfox (.NET)

Official .NET SDK for the [CrawlFox](https://crawlfox.io) API: scrape, search (Google, Bing, or DuckDuckGo), batch scrape, and logs.

Get a key from the [dashboard](https://crawlfox.io). Set `CRAWLFOX_API_KEY`.

```xml
<PackageReference Include="Crawlfox" Version="0.1.0" />
```

Until nuget.org lists it, add a project reference to `packages/dotnet/Crawlfox.csproj`.

```csharp
using Crawlfox;

using var app = new Client(Environment.GetEnvironmentVariable("CRAWLFOX_API_KEY"));

var page = await app.Scrape("https://example.com", new { formats = new[] { "markdown", "links" } });
Console.WriteLine(page.GetProperty("markdown"));

var hits = await app.Search("rust async tutorial", new { engine = "google", num = 10 });

var batch = await app.Batch(
    new[] { "https://example.com/", "https://example.org/" },
    new { formats = new[] { "markdown" } }
);
```

Formats: `markdown`, `html`, `rawHtml`, `json`, `links`, `images`, `emails`. Pass `jsonOptions` with CSS selectors for structured fields. Credits: 1 per page, 1 per 10 requested search results.

```bash
dotnet test Crawlfox.Tests/Crawlfox.Tests.csproj
```

Docs: https://docs.crawlfox.io
