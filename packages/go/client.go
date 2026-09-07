package crawlfox

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// Client is the official CrawlFox Go client for scrape, batch, and search.
type Client struct {
	apiKey  string
	apiURL  string
	timeout time.Duration
	http    HTTPDoer
}

// New constructs a Client. apiKey may be empty if CRAWLFOX_API_KEY is set.
func New(opts ClientOptions) (*Client, error) {
	key := opts.APIKey
	if key == "" {
		key = os.Getenv("CRAWLFOX_API_KEY")
	}
	if key == "" {
		return nil, fmt.Errorf("CrawlFox API key required. Pass APIKey or set CRAWLFOX_API_KEY")
	}
	apiURL := opts.APIURL
	if apiURL == "" {
		apiURL = DefaultAPIURL
	}
	apiURL = strings.TrimRight(apiURL, "/")
	ms := opts.TimeoutMs
	if ms <= 0 {
		ms = 120_000
	}
	httpClient := opts.HTTPClient
	if httpClient == nil {
		httpClient = &http.Client{Timeout: time.Duration(ms) * time.Millisecond}
	}
	return &Client{
		apiKey:  key,
		apiURL:  apiURL,
		timeout: time.Duration(ms) * time.Millisecond,
		http:    httpClient,
	}, nil
}

// Scrape fetches one URL.
func (c *Client) Scrape(ctx context.Context, url string, opts *ScrapeOptions) (*ScrapeResponse, error) {
	body := map[string]any{"url": url}
	mergeScrape(body, opts)
	var out ScrapeResponse
	if err := c.post(ctx, "/v1/scrape", body, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Batch scrapes up to 100 URLs with the same options. jsonOptions is not sent.
func (c *Client) Batch(ctx context.Context, urls []string, opts *ScrapeOptions) (*BatchScrapeResponse, error) {
	body := map[string]any{"urls": urls}
	if opts != nil {
		cp := *opts
		cp.JSONOptions = nil
		mergeScrape(body, &cp)
	}
	var out BatchScrapeResponse
	if err := c.post(ctx, "/v1/batch", body, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// Search runs a web search (Google, Bing, or DuckDuckGo).
func (c *Client) Search(ctx context.Context, q string, opts *SearchOptions) (*SearchResponse, error) {
	body := map[string]any{"q": q}
	if opts != nil {
		if opts.Engine != "" {
			body["engine"] = opts.Engine
		}
		if opts.Num != nil {
			body["num"] = *opts.Num
		}
		if opts.Start != nil {
			body["start"] = *opts.Start
		}
		if opts.Country != "" {
			body["country"] = opts.Country
		}
		if opts.Language != "" {
			body["language"] = opts.Language
		}
	}
	var out SearchResponse
	if err := c.post(ctx, "/v1/search", body, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func mergeScrape(body map[string]any, opts *ScrapeOptions) {
	if opts == nil {
		return
	}
	if len(opts.Formats) > 0 {
		body["formats"] = opts.Formats
	}
	if opts.ExtractMainContent != nil {
		body["extractMainContent"] = *opts.ExtractMainContent
	}
	if opts.SkipCache != nil {
		body["skipCache"] = *opts.SkipCache
	}
	if opts.ZDR != nil {
		body["zdr"] = *opts.ZDR
	}
	if opts.Timeout != nil {
		body["timeout"] = *opts.Timeout
	}
	if opts.JSONOptions != nil {
		body["jsonOptions"] = opts.JSONOptions
	}
}

func (c *Client) post(ctx context.Context, path string, payload any, dest any) error {
	raw, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.apiURL+path, bytes.NewReader(raw))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")
	res, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	body, err := io.ReadAll(res.Body)
	if err != nil {
		return err
	}
	if res.StatusCode < 200 || res.StatusCode >= 300 {
		return parseError(res.StatusCode, body)
	}
	if dest == nil {
		return nil
	}
	return json.Unmarshal(body, dest)
}

func parseError(status int, body []byte) error {
	var eb ErrorBody
	_ = json.Unmarshal(body, &eb)
	msg := eb.Message
	if msg == "" {
		msg = eb.Title
	}
	if msg == "" {
		msg = fmt.Sprintf("CrawlFox request failed (%d)", status)
	}
	return &Error{
		Status:    status,
		Code:      eb.Code,
		Retryable: eb.Retryable,
		Body:      eb,
		message:   msg,
	}
}
