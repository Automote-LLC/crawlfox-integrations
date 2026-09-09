# frozen_string_literal: true

require "json"
require "net/http"
require "uri"

module Crawlfox
  VERSION = "0.1.0"
  DEFAULT_API_URL = "https://api.crawlfox.io"

  class Error < StandardError
    attr_reader :status, :code, :retryable, :body

    def initialize(message, status:, code: nil, retryable: nil, body: {})
      super(message)
      @status = status
      @code = code
      @retryable = retryable
      @body = body
    end

    def retryable_effective?
      return false if retryable == false
      return true if retryable == true

      [502, 503, 504].include?(status)
    end
  end

  class Client
    def initialize(api_key: nil, api_url: nil, timeout: 120, max_retries: 2, retry_backoff_ms: 200, transport: nil)
      @api_key = api_key || ENV["CRAWLFOX_API_KEY"]
      raise ArgumentError, "CrawlFox API key required. Pass api_key or set CRAWLFOX_API_KEY." if @api_key.to_s.empty?

      @api_url = (api_url || ENV["CRAWLFOX_API_URL"] || DEFAULT_API_URL).to_s.sub(%r{/$}, "")
      @timeout = timeout
      @max_retries = max_retries
      @retry_backoff_ms = retry_backoff_ms
      @transport = transport || method(:net_http_transport)
    end

    def scrape(url, **options)
      document(request("POST", "/v1/scrape", { url: url }.merge(options)))
    end

    def scrape_get(url)
      document(request("GET", "/v1/scrape/#{URI.encode_www_form_component(url)}"))
    end

    def batch(urls, **options)
      env = request("POST", "/v1/batch", { urls: urls }.merge(options))
      {
        "success" => env.fetch("success", true),
        "count" => env["count"] || Array(env["results"]).length,
        "data" => Array(env["results"]).map { |item| document(item) }
      }
    end

    def search(q, **options)
      env = request("POST", "/v1/search", { q: q }.merge(options))
      {
        "success" => env.fetch("success", true),
        "web" => env.dig("data", "web") || [],
        "creditsUsed" => env["creditsUsed"],
        "id" => env["id"]
      }
    end

    def get_log(id)
      request("GET", "/v1/logs/#{URI.encode_www_form_component(id)}")
    end

    def get_log_result(id)
      request("GET", "/v1/logs/#{URI.encode_www_form_component(id)}/result")
    end

    private

    def document(envelope)
      data = envelope["data"].is_a?(Hash) ? envelope["data"].dup : envelope.dup
      data["success"] = envelope.fetch("success", true)
      data
    end

    def request(method, path, body = nil)
      payload = body && JSON.generate(body)
      headers = {
        "Authorization" => "Bearer #{@api_key}",
        "Content-Type" => "application/json",
        "User-Agent" => "crawlfox-ruby/#{VERSION}"
      }
      url = @api_url + path
      attempts = @max_retries + 1
      last = nil
      attempts.times do |i|
        status, raw = @transport.call(method, url, headers, payload)
        json = JSON.parse(raw.to_s.empty? ? "{}" : raw)
        return json if status >= 200 && status < 300

        err = Error.new(json["message"] || json["title"] || "CrawlFox request failed (#{status})",
                        status: status, code: json["code"], retryable: json["retryable"], body: json)
        raise err unless i < attempts - 1 && err.retryable_effective?

        last = err
        sleep(@retry_backoff_ms / 1000.0 * (2**i))
      end
      raise last || Error.new("Request failed", status: 0)
    end

    def net_http_transport(method, url, headers, body)
      uri = URI.parse(url)
      req = Net::HTTPGenericRequest.new(method, !body.nil?, true, uri)
      headers.each { |k, v| req[k] = v }
      req.body = body if body
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == "https"
      http.read_timeout = @timeout
      res = http.request(req)
      [res.code.to_i, res.body.to_s]
    end
  end
end
