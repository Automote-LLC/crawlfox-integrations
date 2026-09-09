# crawlfox (Go)

Official Go SDK for the [CrawlFox](https://crawlfox.io) scrape + search API.

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
	fmt.Println(page.Data.Markdown)

	results, err := client.Search(ctx, "crawlfox web scraping", &crawlfox.SearchOptions{
		Engine: "google",
		Num:    crawlfox.Int(5),
	})
	if err != nil {
		panic(err)
	}
	for _, hit := range results.Data.Web {
		fmt.Println(hit.Position, hit.Title, hit.URL)
	}

	batch, err := client.Batch(ctx, []string{"https://example.org", "https://example.net"}, &crawlfox.ScrapeOptions{
		Formats: []string{"markdown"},
	})
	if err != nil {
		panic(err)
	}
	for _, item := range batch.Results {
		if item.Data != nil {
			fmt.Println(item.Data.Markdown[:min(80, len(item.Data.Markdown))])
		}
	}
}
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

## Docs

https://docs.crawlfox.io
