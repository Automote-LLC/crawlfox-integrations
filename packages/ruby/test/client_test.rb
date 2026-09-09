# frozen_string_literal: true

require "minitest/autorun"
require "crawlfox"

class ClientTest < Minitest::Test
  def test_requires_api_key
    prev = ENV.delete("CRAWLFOX_API_KEY")
    assert_raises(ArgumentError) { Crawlfox::Client.new }
  ensure
    ENV["CRAWLFOX_API_KEY"] = prev if prev
  end

  def test_scrape_search_batch_logs_and_retry
    scrapes = 0
    transport = lambda do |method, url, headers, body|
      case url
      when %r{/v1/scrape$}
        scrapes += 1
        return [503, { message: "busy", retryable: true }.to_json] if scrapes == 1

        assert_equal "POST", method
        assert_equal "Bearer cfx_test", headers["Authorization"]
        assert headers["User-Agent"].start_with?("crawlfox-ruby/")
        payload = JSON.parse(body)
        assert_equal "https://example.com", payload["url"]
        [200, { success: true, data: { markdown: "# Hello" } }.to_json]
      when %r{/v1/search$}
        [200, { success: true, data: { web: [{ url: "https://example.com" }] } }.to_json]
      when %r{/v1/batch$}
        [200, { success: true, count: 1, results: [{ success: true, data: { markdown: "# A" } }] }.to_json]
      when %r{/v1/logs/log1/result$}
        [200, { ok: true }.to_json]
      when %r{/v1/logs/log1$}
        assert_equal "GET", method
        [200, { id: "log1", status: "ok" }.to_json]
      else
        [404, "{}"]
      end
    end

    app = Crawlfox::Client.new(api_key: "cfx_test", api_url: "https://api.test", retry_backoff_ms: 1, transport: transport)
    doc = app.scrape("https://example.com", formats: ["markdown"], country: "de")
    assert_equal "# Hello", doc["markdown"]
    assert_equal 2, scrapes

    search = app.search("crawlfox", engine: "google", num: 5)
    assert_equal "https://example.com", search["web"][0]["url"]

    batch = app.batch(["https://example.org"])
    assert_equal "# A", batch["data"][0]["markdown"]

    assert_equal "ok", app.get_log("log1")["status"]
    assert_equal true, app.get_log_result("log1")["ok"]
  end

  def test_does_not_retry_quota
    n = 0
    transport = lambda do |*|
      n += 1
      [429, { message: "quota", retryable: false, code: "quota" }.to_json]
    end
    app = Crawlfox::Client.new(api_key: "cfx_test", api_url: "https://api.test", retry_backoff_ms: 1, transport: transport)
    err = assert_raises(Crawlfox::Error) { app.scrape("https://example.com") }
    assert_equal 429, err.status
    assert_equal 1, n
  end
end

class LiveTest < Minitest::Test
  def test_live_scrape_search_batch
    skip "CRAWLFOX_API_KEY not set" if ENV["CRAWLFOX_API_KEY"].to_s.empty?

    app = Crawlfox::Client.new(max_retries: 1)
    doc = app.scrape("https://example.com", formats: ["markdown"])
    assert doc["markdown"].to_s.length > 10
    search = app.search("crawlfox", engine: "google", num: 3)
    refute_empty search["web"]
    batch = app.batch(["https://example.com"], formats: ["markdown"])
    assert batch.dig("data", 0, "markdown").to_s.length > 5
  end
end
