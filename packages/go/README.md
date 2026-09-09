# crawlfox (Go)

Official Go SDK for the [CrawlFox](https://crawlfox.io) API.

Scrape a URL, search Google, Bing, or DuckDuckGo, batch scrape URLs, stream search, and read logs.

Get a key from the [dashboard](https://crawlfox.io). Set `CRAWLFOX_API_KEY` or pass `APIKey`.

```bash
go get github.com/Automote-LLC/crawlfox-integrations/packages/go@main
```

## Quickstart

```go
package main

import (
	"context"
	"fmt"
	"os"

	crawlfox "github.com/Automote-LLC/crawlfox-integrations/packages/go"
)

func main() {
	client, err := crawlfox.New(crawlfox.ClientOptions{
		APIKey: os.Getenv("CRAWLFOX_API_KEY"),
	})
	if err != nil {
		panic(err)
	}
	ctx := context.Background()

	page, err := client.Scrape(ctx, "https://example.com", &crawlfox.ScrapeOptions{
		Formats: []string{"markdown", "links"},
	})
	if err != nil {
		panic(err)
	}
	fmt.Println(page.Markdown)

	results, err := client.Search(ctx, "rust async tutorial", &crawlfox.SearchOptions{
		Engine: "google",
		Num:    crawlfox.Int(10),
	})
	if err != nil {
		panic(err)
	}
	for _, hit := range results.Web {
		fmt.Println(hit.Position, hit.Title, hit.URL)
	}

	batch, err := client.Batch(ctx, []string{"https://example.com/", "https://example.org/"}, &crawlfox.ScrapeOptions{
		Formats: []string{"markdown"},
	})
	if err != nil {
		panic(err)
	}
	for _, doc := range batch.Data {
		fmt.Println(doc.Markdown)
	}
}
```

`Scrape` returns a `Document` (markdown and metadata on the struct, not under `.Data`). `Search` returns `SearchData` with `Web`. `Batch` returns `BatchScrapeResult` with `Data []Document`.

## Scrape options

Formats: `markdown`, `html`, `rawHtml`, `json`, `links`, `images`, `emails`. Default markdown.

`JSONOptions.Selectors` maps field names to CSS selectors when `"json"` is in `Formats`. No separate extract API.

Also: `SkipCache`, `Timeout` (ms, cap 90000), `Country`, `Language`, `Location`, `RedactPII`, `ZDR`.

```go
page, err := client.ScrapeGet(ctx, "https://example.com")
```

## Search

`Engine`: `google`, `bing`, or `duckduckgo`. `Num` is how many results to request. `Start` is the pagination offset. `Country` / `Language` are two-letter codes.

`SearchStream` reads NDJSON (`page` / `done` / `error`).

Credits: scrape 1 per page, search 1 per 10 requested results.

## Logs

```go
row, err := client.GetLog(ctx, id)
body, err := client.GetLogResult(ctx, id)
```

## Errors

```go
page, err := client.Scrape(ctx, "https://example.com", nil)
if err != nil {
	if e, ok := err.(*crawlfox.Error); ok {
		fmt.Println(e.Status, e.Code, e.Retryable, e.Error())
	}
}
```

Retries on 502/503/504 and `retryable: true`.

## Docs

https://docs.crawlfox.io
