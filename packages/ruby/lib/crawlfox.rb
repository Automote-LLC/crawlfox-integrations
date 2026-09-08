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
  end

  class Client
    def initialize(api_key: nil, api_url: DEFAULT_API_URL, timeout: 120)
      @api_key = api_key || ENV["CRAWLFOX_API_KEY"]
      raise ArgumentError, "CrawlFox API key required. Pass api_key or set CRAWLFOX_API_KEY." if @api_key.to_s.empty?

      @api_url = api_url.to_s.sub(%r{/$}, "")
      @timeout = timeout
    end

    def scrape(url, **options)
      document(post("/v1/scrape", { url: url }.merge(options)))
    end

    def batch(urls, **options)
      env = post("/v1/batch", { urls: urls }.merge(options))
      {
        "success" => env["success"],
        "count" => env["count"],
        "data" => Array(env["results"]).map { |item| document(item) }
      }
    end

    def search(q, **options)
      env = post("/v1/search", { q: q }.merge(options))
      {
        "success" => env["success"],
        "web" => env.dig("data", "web") || [],
        "creditsUsed" => env["creditsUsed"],
        "id" => env["id"]
      }
    end

    private

    def document(envelope)
      data = envelope["data"].is_a?(Hash) ? envelope["data"].dup : envelope.dup
      data["success"] = envelope.fetch("success", true)
      data
    end

    def post(path, body)
      uri = URI.parse(@api_url + path)
      req = Net::HTTP::Post.new(uri)
      req["Authorization"] = "Bearer #{@api_key}"
      req["Content-Type"] = "application/json"
      req["User-Agent"] = "crawlfox-ruby/#{VERSION}"
      req.body = JSON.generate(body)
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == "https"
      http.read_timeout = @timeout
      res = http.request(req)
      json = JSON.parse(res.body.empty? ? "{}" : res.body)
      unless res.is_a?(Net::HTTPSuccess)
        raise Error.new(json["message"] || json["title"] || "CrawlFox request failed (#{res.code})",
                        status: res.code.to_i, code: json["code"], retryable: json["retryable"], body: json)
      end
      json
    end
  end
end
