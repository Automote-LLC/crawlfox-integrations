package crawlfox

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

type Client struct {
	apiKey     string
	apiURL     string
	maxRetries int
	http       HTTPDoer
}

func New(opts ClientOptions) (*Client, error) {
	key := opts.APIKey
	if key == "" {
		key = os.Getenv("CRAWLFOX_API_KEY")
	}
	if key == "" {
		return nil, &Error{
			Status:    401,
			Code:      "UNAUTHORIZED",
			Retryable: Bool(false),
			message:   "CrawlFox API key required. Pass APIKey or set CRAWLFOX_API_KEY",
		}
	}
	apiURL := opts.APIURL
	if apiURL == "" {
		apiURL = os.Getenv("CRAWLFOX_API_URL")
	}
	if apiURL == "" {
		apiURL = DefaultAPIURL
	}
	apiURL = strings.TrimRight(apiURL, "/")
	ms := opts.TimeoutMs
	if ms <= 0 {
		ms = 120_000
	}
	retries := 2
	if opts.MaxRetries > 0 {
		retries = opts.MaxRetries
	}
	httpClient := opts.HTTPClient
	if httpClient == nil {
		httpClient = &http.Client{Timeout: time.Duration(ms) * time.Millisecond}
	}
	return &Client{
		apiKey:     key,
		apiURL:     apiURL,
		maxRetries: retries,
		http:       httpClient,
	}, nil
}

func requireURL(pageURL string) error {
	if strings.TrimSpace(pageURL) == "" {
		return &Error{Status: 400, Code: "INVALID_REQUEST", Retryable: Bool(false), message: "url is required"}
	}
	return nil
}

func requireQuery(q string) error {
	if strings.TrimSpace(q) == "" {
		return &Error{Status: 400, Code: "INVALID_REQUEST", Retryable: Bool(false), message: "q is required"}
	}
	return nil
}

func requireBatch(urls []string) error {
	if len(urls) == 0 {
		return &Error{Status: 400, Code: "INVALID_REQUEST", Retryable: Bool(false), message: "urls must be a non-empty array"}
	}
	if len(urls) > 100 {
		return &Error{Status: 400, Code: "INVALID_REQUEST", Retryable: Bool(false), message: "batch supports at most 100 URLs"}
	}
	for _, u := range urls {
		if err := requireURL(u); err != nil {
			return err
		}
	}
	return nil
}

func defaultScrapeOpts(opts *ScrapeOptions) *ScrapeOptions {
	if opts == nil {
		return &ScrapeOptions{Formats: []string{"markdown"}}
	}
	if len(opts.Formats) == 0 {
		cp := *opts
		cp.Formats = []string{"markdown"}
		return &cp
	}
	return opts
}

func (c *Client) Scrape(ctx context.Context, pageURL string, opts *ScrapeOptions) (*Document, error) {
	if err := requireURL(pageURL); err != nil {
		return nil, err
	}
	body := map[string]any{"url": pageURL}
	mergeScrape(body, defaultScrapeOpts(opts))
	var env scrapeEnvelope
	if err := c.doJSON(ctx, http.MethodPost, "/v1/scrape", body, &env); err != nil {
		return nil, err
	}
	return documentFromEnv(env), nil
}

func (c *Client) ScrapeGet(ctx context.Context, pageURL string) (*Document, error) {
	if err := requireURL(pageURL); err != nil {
		return nil, err
	}
	path := "/v1/scrape/" + url.PathEscape(pageURL)
	var env scrapeEnvelope
	if err := c.doJSON(ctx, http.MethodGet, path, nil, &env); err != nil {
		return nil, err
	}
	return documentFromEnv(env), nil
}

func (c *Client) Batch(ctx context.Context, urls []string, opts *ScrapeOptions) (*BatchScrapeResult, error) {
	if err := requireBatch(urls); err != nil {
		return nil, err
	}
	body := map[string]any{"urls": urls}
	if opts != nil {
		cp := *opts
		cp.JSONOptions = nil
		mergeScrape(body, defaultScrapeOpts(&cp))
	} else {
		mergeScrape(body, defaultScrapeOpts(nil))
	}
	var env batchEnvelope
	if err := c.doJSON(ctx, http.MethodPost, "/v1/batch", body, &env); err != nil {
		return nil, err
	}
	out := &BatchScrapeResult{Success: env.Success, Count: env.Count}
	for _, item := range env.Results {
		if d := documentFromEnv(item); d != nil {
			out.Data = append(out.Data, *d)
		}
	}
	return out, nil
}

func (c *Client) Search(ctx context.Context, q string, opts *SearchOptions) (*SearchData, error) {
	if err := requireQuery(q); err != nil {
		return nil, err
	}
	body := map[string]any{"q": q}
	mergeSearch(body, opts)
	var env searchEnvelope
	if err := c.doJSON(ctx, http.MethodPost, "/v1/search", body, &env); err != nil {
		return nil, err
	}
	out := &SearchData{Success: env.Success, CreditsUsed: env.CreditsUsed, ID: env.ID}
	if env.Data != nil {
		out.Web = env.Data.Web
	}
	return out, nil
}

func (c *Client) SearchStream(ctx context.Context, q string, opts *SearchOptions) ([]SearchStreamEvent, error) {
	if err := requireQuery(q); err != nil {
		return nil, err
	}
	body := map[string]any{"q": q}
	mergeSearch(body, opts)
	res, err := c.send(ctx, http.MethodPost, "/v1/search/stream", body)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()
	if res.StatusCode < 200 || res.StatusCode >= 300 {
		b, _ := io.ReadAll(res.Body)
		return nil, parseError(res.StatusCode, b)
	}
	var events []SearchStreamEvent
	sc := bufio.NewScanner(res.Body)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var ev SearchStreamEvent
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			return nil, err
		}
		events = append(events, ev)
	}
	return events, sc.Err()
}

func (c *Client) GetLog(ctx context.Context, id string) (*LogRow, error) {
	var row LogRow
	if err := c.doJSON(ctx, http.MethodGet, "/v1/logs/"+url.PathEscape(id), nil, &row); err != nil {
		return nil, err
	}
	return &row, nil
}

func (c *Client) GetLogResult(ctx context.Context, id string) (json.RawMessage, error) {
	var raw json.RawMessage
	if err := c.doJSON(ctx, http.MethodGet, "/v1/logs/"+url.PathEscape(id)+"/result", nil, &raw); err != nil {
		return nil, err
	}
	return raw, nil
}

func documentFromEnv(env scrapeEnvelope) *Document {
	doc := env.Data
	if doc == nil {
		doc = &Document{}
	}
	doc.Success = env.Success
	if env.Error != "" {
		doc.Error = env.Error
	}
	return doc
}

func mergeSearch(body map[string]any, opts *SearchOptions) {
	if opts == nil {
		return
	}
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

func mergeScrape(body map[string]any, opts *ScrapeOptions) {
	if opts == nil {
		return
	}
	if len(opts.Formats) > 0 {
		body["formats"] = opts.Formats
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
	if opts.Country != "" {
		body["country"] = opts.Country
	}
	if opts.Language != "" {
		body["language"] = opts.Language
	}
	if opts.Location != nil {
		body["location"] = opts.Location
	}
	if opts.RedactPII != nil {
		body["redactPII"] = opts.RedactPII
	}
}

func (c *Client) doJSON(ctx context.Context, method, path string, payload any, dest any) error {
	var last error
	attempts := c.maxRetries + 1
	for i := 0; i < attempts; i++ {
		res, err := c.send(ctx, method, path, payload)
		if err != nil {
			if i < attempts-1 {
				last = err
				time.Sleep(time.Duration(200*(1<<i)) * time.Millisecond)
				continue
			}
			return err
		}
		body, err := io.ReadAll(res.Body)
		res.Body.Close()
		if err != nil {
			return err
		}
		if res.StatusCode < 200 || res.StatusCode >= 300 {
			cfErr := parseError(res.StatusCode, body)
			if i < attempts-1 {
				if e, ok := cfErr.(*Error); ok && e.retryable() {
					last = cfErr
					time.Sleep(time.Duration(200*(1<<i)) * time.Millisecond)
					continue
				}
			}
			return cfErr
		}
		if dest == nil {
			return nil
		}
		return json.Unmarshal(body, dest)
	}
	return last
}

func (c *Client) send(ctx context.Context, method, path string, payload any) (*http.Response, error) {
	var reader io.Reader
	if payload != nil {
		raw, err := json.Marshal(payload)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(raw)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.apiURL+path, reader)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "crawlfox-go/"+SDKVersion)
	return c.http.Do(req)
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
