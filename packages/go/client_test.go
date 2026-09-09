package crawlfox

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func TestRequiresAPIKey(t *testing.T) {
	t.Setenv("CRAWLFOX_API_KEY", "")
	os.Unsetenv("CRAWLFOX_API_KEY")
	_, err := New(ClientOptions{})
	if err == nil || !strings.Contains(err.Error(), "API key required") {
		t.Fatalf("expected API key error, got %v", err)
	}
}

func TestScrapeSendsCorrectRequest(t *testing.T) {
	var gotURL, gotAuth, gotBody, gotUA string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotURL = r.URL.Path
		gotAuth = r.Header.Get("Authorization")
		gotUA = r.Header.Get("User-Agent")
		b, _ := io.ReadAll(r.Body)
		gotBody = string(b)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"success":true,"data":{"markdown":"# Hello","metadata":{"statusCode":200}}}`))
	}))
	defer srv.Close()

	client, err := New(ClientOptions{APIKey: "cfx_test", APIURL: srv.URL})
	if err != nil {
		t.Fatal(err)
	}
	res, err := client.Scrape(context.Background(), "https://example.com", &ScrapeOptions{
		Formats:   []string{"markdown"},
		SkipCache: Bool(true),
		Country:   "de",
		RedactPII: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.Markdown != "# Hello" {
		t.Fatalf("unexpected scrape response: %+v", res)
	}
	if gotURL != "/v1/scrape" {
		t.Fatalf("path = %s", gotURL)
	}
	if gotAuth != "Bearer cfx_test" {
		t.Fatalf("auth = %s", gotAuth)
	}
	if !strings.HasPrefix(gotUA, "crawlfox-go/") {
		t.Fatalf("ua = %s", gotUA)
	}
	var body map[string]any
	if err := json.Unmarshal([]byte(gotBody), &body); err != nil {
		t.Fatal(err)
	}
	if body["country"] != "de" || body["redactPII"] != true {
		t.Fatalf("body = %#v", body)
	}
}

func TestSearchSendsQueryBody(t *testing.T) {
	var body map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewDecoder(r.Body).Decode(&body)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"success":true,"data":{"web":[{"url":"https://example.com","title":"Ex"}]}}`))
	}))
	defer srv.Close()

	client, err := New(ClientOptions{APIKey: "cfx_test", APIURL: srv.URL})
	if err != nil {
		t.Fatal(err)
	}
	res, err := client.Search(context.Background(), "crawlfox", &SearchOptions{
		Engine: "google",
		Num:    Int(5),
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Web) == 0 || res.Web[0].URL != "https://example.com" {
		t.Fatalf("unexpected search: %+v", res)
	}
	if body["q"] != "crawlfox" || body["engine"] != "google" {
		t.Fatalf("body = %#v", body)
	}
}

func TestBatch(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"success":true,"count":1,"results":[{"success":true,"data":{"markdown":"# A"}}]}`))
	}))
	defer srv.Close()

	client, err := New(ClientOptions{APIKey: "cfx_test", APIURL: srv.URL})
	if err != nil {
		t.Fatal(err)
	}
	res, err := client.Batch(context.Background(), []string{"https://example.org"}, &ScrapeOptions{
		Formats: []string{"markdown"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Success || len(res.Data) != 1 || res.Data[0].Markdown != "# A" {
		t.Fatalf("unexpected batch: %+v", res)
	}
}

func TestErrorResponse(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(429)
		_, _ = w.Write([]byte(`{"code":"MONTHLY_QUOTA_EXCEEDED","message":"Quota exceeded","retryable":false}`))
	}))
	defer srv.Close()

	client, err := New(ClientOptions{APIKey: "cfx_test", APIURL: srv.URL})
	if err != nil {
		t.Fatal(err)
	}
	_, err = client.Scrape(context.Background(), "https://example.com", nil)
	cfErr, ok := err.(*Error)
	if !ok {
		t.Fatalf("expected *Error, got %T %v", err, err)
	}
	if cfErr.Status != 429 || cfErr.Code != "MONTHLY_QUOTA_EXCEEDED" {
		t.Fatalf("unexpected error: %+v", cfErr)
	}
}

func TestRejectsEmptyURL(t *testing.T) {
	client, err := New(ClientOptions{APIKey: "cfx_test", APIURL: "http://127.0.0.1:1"})
	if err != nil {
		t.Fatal(err)
	}
	_, err = client.Scrape(context.Background(), "  ", nil)
	if err == nil || !strings.Contains(err.Error(), "url is required") {
		t.Fatalf("got %v", err)
	}
}
