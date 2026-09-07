package crawlfox

import (
	"fmt"
	"net/http"
)

const DefaultAPIURL = "https://api.crawlfox.io"

// ClientOptions configure a CrawlFox client.
type ClientOptions struct {
	// APIKey (cfx_…). Defaults to CRAWLFOX_API_KEY.
	APIKey string
	// APIURL defaults to https://api.crawlfox.io.
	APIURL string
	// TimeoutMs for the HTTP round-trip. Defaults to 120_000.
	TimeoutMs int
	// HTTPClient overrides the default client (tests, custom transports).
	HTTPClient HTTPDoer
}

// HTTPDoer is the subset of http.Client used by CrawlFox.
type HTTPDoer interface {
	Do(req *http.Request) (*http.Response, error)
}

// ScrapeOptions are optional scrape / batch fields. Zero values are omitted.
type ScrapeOptions struct {
	Formats            []string       `json:"formats,omitempty"`
	ExtractMainContent *bool          `json:"extractMainContent,omitempty"`
	SkipCache          *bool          `json:"skipCache,omitempty"`
	ZDR                *bool          `json:"zdr,omitempty"`
	Timeout            *int           `json:"timeout,omitempty"`
	JSONOptions        map[string]any `json:"jsonOptions,omitempty"`
}

// SearchOptions are optional search fields. Zero values are omitted.
type SearchOptions struct {
	Engine   string `json:"engine,omitempty"`
	Num      *int   `json:"num,omitempty"`
	Start    *int   `json:"start,omitempty"`
	Country  string `json:"country,omitempty"`
	Language string `json:"language,omitempty"`
}

type ScrapeMetadata struct {
	Title       string `json:"title,omitempty"`
	Description string `json:"description,omitempty"`
	Language    string `json:"language,omitempty"`
	SourceURL   string `json:"sourceURL,omitempty"`
	URL         string `json:"url,omitempty"`
	StatusCode  *int   `json:"statusCode,omitempty"`
	ScrapeID    string `json:"scrapeId,omitempty"`
	CreditsUsed *float64 `json:"creditsUsed,omitempty"`
	CacheState  string `json:"cacheState,omitempty"`
}

type ScrapeData struct {
	Markdown string          `json:"markdown,omitempty"`
	HTML     string          `json:"html,omitempty"`
	RawHTML  string          `json:"rawHtml,omitempty"`
	Text     string          `json:"text,omitempty"`
	Links    []string        `json:"links,omitempty"`
	Images   []string        `json:"images,omitempty"`
	Emails   []string        `json:"emails,omitempty"`
	JSON     any             `json:"json,omitempty"`
	Metadata *ScrapeMetadata `json:"metadata,omitempty"`
}

type ScrapeResponse struct {
	Success  bool           `json:"success"`
	Data     *ScrapeData    `json:"data,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

type BatchScrapeResponse struct {
	Success bool             `json:"success"`
	Count   *int             `json:"count,omitempty"`
	Results []ScrapeResponse `json:"results"`
}

type SearchResult struct {
	URL         string `json:"url"`
	Title       string `json:"title,omitempty"`
	Description string `json:"description,omitempty"`
	Position    *int   `json:"position,omitempty"`
}

type SearchData struct {
	Web []SearchResult `json:"web,omitempty"`
}

type SearchResponse struct {
	Success     bool        `json:"success"`
	CreditsUsed *float64    `json:"creditsUsed,omitempty"`
	ID          string      `json:"id,omitempty"`
	Data        *SearchData `json:"data,omitempty"`
}

type ErrorBody struct {
	Code        string `json:"code,omitempty"`
	Status      int    `json:"status,omitempty"`
	Retryable   *bool  `json:"retryable,omitempty"`
	Title       string `json:"title,omitempty"`
	Message     string `json:"message,omitempty"`
	Remediation string `json:"remediation,omitempty"`
}

// Error is returned when the API responds with a non-success status.
type Error struct {
	Status    int
	Code      string
	Retryable *bool
	Body      ErrorBody
	message   string
}

func (e *Error) Error() string {
	if e == nil {
		return ""
	}
	if e.message != "" {
		return e.message
	}
	return fmt.Sprintf("CrawlFox request failed (%d)", e.Status)
}

// Bool is a helper for optional boolean request fields.
func Bool(v bool) *bool { return &v }

// Int is a helper for optional integer request fields.
func Int(v int) *int { return &v }
