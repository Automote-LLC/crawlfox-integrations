package crawlfox

import (
	"fmt"
	"net/http"
)

const (
	DefaultAPIURL = "https://api.crawlfox.io"
	SDKVersion    = "0.1.0"
)

type ClientOptions struct {
	APIKey     string
	APIURL     string
	TimeoutMs  int
	MaxRetries int
	HTTPClient HTTPDoer
}

type HTTPDoer interface {
	Do(req *http.Request) (*http.Response, error)
}

type SelectorRule struct {
	Selector string `json:"selector"`
	Attr     string `json:"attr,omitempty"`
	Multiple *bool  `json:"multiple,omitempty"`
}

type JsonOptions struct {
	Selectors map[string]any `json:"selectors"`
}

type Location struct {
	Country   string   `json:"country,omitempty"`
	Languages []string `json:"languages,omitempty"`
}

type ScrapeOptions struct {
	Formats     []string     `json:"formats,omitempty"`
	SkipCache   *bool        `json:"skipCache,omitempty"`
	ZDR         *bool        `json:"zdr,omitempty"`
	Timeout     *int         `json:"timeout,omitempty"`
	JSONOptions *JsonOptions `json:"jsonOptions,omitempty"`
	Country     string       `json:"country,omitempty"`
	Language    string       `json:"language,omitempty"`
	Location    *Location    `json:"location,omitempty"`
	RedactPII   any          `json:"redactPII,omitempty"`
}

type SearchOptions struct {
	Engine   string `json:"engine,omitempty"`
	Num      *int   `json:"num,omitempty"`
	Start    *int   `json:"start,omitempty"`
	Country  string `json:"country,omitempty"`
	Language string `json:"language,omitempty"`
}

type ScrapeMetadata struct {
	Title       string   `json:"title,omitempty"`
	Description string   `json:"description,omitempty"`
	Language    string   `json:"language,omitempty"`
	SourceURL   string   `json:"sourceURL,omitempty"`
	URL         string   `json:"url,omitempty"`
	StatusCode  *int     `json:"statusCode,omitempty"`
	ScrapeID    string   `json:"scrapeId,omitempty"`
	CreditsUsed *float64 `json:"creditsUsed,omitempty"`
	CacheState  string   `json:"cacheState,omitempty"`
}

type Document struct {
	Success  bool            `json:"success,omitempty"`
	Markdown string          `json:"markdown,omitempty"`
	HTML     string          `json:"html,omitempty"`
	RawHTML  string          `json:"rawHtml,omitempty"`
	Links    []string        `json:"links,omitempty"`
	Images   []string        `json:"images,omitempty"`
	Emails   []string        `json:"emails,omitempty"`
	JSON     any             `json:"json,omitempty"`
	Metadata *ScrapeMetadata `json:"metadata,omitempty"`
	Error    string          `json:"error,omitempty"`
}

type scrapeEnvelope struct {
	Success bool      `json:"success"`
	Data    *Document `json:"data"`
	Error   string    `json:"error,omitempty"`
}

type BatchScrapeResult struct {
	Success bool       `json:"success"`
	Count   *int       `json:"count,omitempty"`
	Data    []Document `json:"data"`
}

type batchEnvelope struct {
	Success bool             `json:"success"`
	Count   *int             `json:"count,omitempty"`
	Results []scrapeEnvelope `json:"results"`
}

type SearchResult struct {
	URL         string `json:"url"`
	Title       string `json:"title,omitempty"`
	Description string `json:"description,omitempty"`
	Position    *int   `json:"position,omitempty"`
}

type SearchData struct {
	Success     bool           `json:"success,omitempty"`
	Web         []SearchResult `json:"web,omitempty"`
	CreditsUsed *float64       `json:"creditsUsed,omitempty"`
	ID          string         `json:"id,omitempty"`
}

type searchEnvelope struct {
	Success     bool     `json:"success"`
	CreditsUsed *float64 `json:"creditsUsed,omitempty"`
	ID          string   `json:"id,omitempty"`
	Data        *struct {
		Web []SearchResult `json:"web,omitempty"`
	} `json:"data,omitempty"`
}

type SearchStreamEvent struct {
	Type string `json:"type"`
	Data *struct {
		Web []SearchResult `json:"web,omitempty"`
	} `json:"data,omitempty"`
	Partial     *bool    `json:"partial,omitempty"`
	CreditsUsed *float64 `json:"creditsUsed,omitempty"`
	ID          string   `json:"id,omitempty"`
	Code        string   `json:"code,omitempty"`
	Message     string   `json:"message,omitempty"`
}

type LogRow struct {
	ID           string  `json:"id"`
	StartedAtMs  int64   `json:"started_at_ms"`
	DurationMs   int     `json:"duration_ms"`
	URL          any     `json:"url"`
	Status       int     `json:"status"`
	FinalOutcome *string `json:"final_outcome"`
}

type ErrorBody struct {
	Code        string `json:"code,omitempty"`
	Status      int    `json:"status,omitempty"`
	Retryable   *bool  `json:"retryable,omitempty"`
	Title       string `json:"title,omitempty"`
	Message     string `json:"message,omitempty"`
	Remediation string `json:"remediation,omitempty"`
}

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

func (e *Error) retryable() bool {
	if e == nil {
		return false
	}
	if e.Retryable != nil {
		return *e.Retryable
	}
	return e.Status == 502 || e.Status == 503 || e.Status == 504
}

func Bool(v bool) *bool { return &v }

func Int(v int) *int { return &v }
