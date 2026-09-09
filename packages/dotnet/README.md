# Crawlfox (.NET)

Official .NET SDK for the [CrawlFox](https://crawlfox.io) scrape and search API.

```xml
<PackageReference Include="Crawlfox" Version="0.1.0" />
```

```csharp
using Crawlfox;

using var app = new Client(Environment.GetEnvironmentVariable("CRAWLFOX_API_KEY"));
var page = await app.Scrape("https://example.com", new { formats = new[] { "markdown" } });
Console.WriteLine(page.GetProperty("markdown"));
var hits = await app.Search("crawlfox", new { engine = "google", num = 5 });
```

```bash
dotnet test Crawlfox.Tests/Crawlfox.Tests.csproj
```
