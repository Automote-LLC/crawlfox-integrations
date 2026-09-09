defmodule CrawlfoxTest do
  use ExUnit.Case

  test "requires api key" do
    prev = System.get_env("CRAWLFOX_API_KEY")
    System.delete_env("CRAWLFOX_API_KEY")

    try do
      assert_raise ArgumentError, fn -> Crawlfox.new() end
    after
      if prev, do: System.put_env("CRAWLFOX_API_KEY", prev)
    end
  end

  test "scrape search batch logs and retry" do
    scrapes = :counters.new(1, [])

    http = fn method, url, headers, body ->
      cond do
        String.ends_with?(url, "/v1/scrape") ->
          n = :counters.get(scrapes, 1) + 1
          :counters.add(scrapes, 1, 1)

          if n == 1 do
            {503, Jason.encode!(%{message: "busy", retryable: true})}
          else
            assert method == "POST"
            assert headers["Authorization"] == "Bearer cfx_test"
            assert String.starts_with?(headers["User-Agent"], "crawlfox-elixir/")
            payload = Jason.decode!(body)
            assert payload["url"] == "https://example.com"
            {200, Jason.encode!(%{success: true, data: %{markdown: "# Hello"}})}
          end

        String.ends_with?(url, "/v1/search") ->
          {200, Jason.encode!(%{success: true, data: %{web: [%{url: "https://example.com"}]}})}

        String.ends_with?(url, "/v1/batch") ->
          {200,
           Jason.encode!(%{
             success: true,
             count: 1,
             results: [%{success: true, data: %{markdown: "# A"}}]
           })}

        String.ends_with?(url, "/v1/logs/log1/result") ->
          {200, Jason.encode!(%{ok: true})}

        String.ends_with?(url, "/v1/logs/log1") ->
          assert method == "GET"
          {200, Jason.encode!(%{id: "log1", status: "ok"})}

        true ->
          {404, "{}"}
      end
    end

    client =
      Crawlfox.new(
        api_key: "cfx_test",
        api_url: "https://api.test",
        retry_backoff_ms: 1,
        http: http
      )

    doc = Crawlfox.scrape(client, "https://example.com", %{"formats" => ["markdown"]})
    assert doc["markdown"] == "# Hello"
    assert :counters.get(scrapes, 1) == 2

    search = Crawlfox.search(client, "crawlfox", %{"engine" => "google"})
    assert hd(search["web"])["url"] == "https://example.com"

    batch = Crawlfox.batch(client, ["https://example.org"])
    assert hd(batch["data"])["markdown"] == "# A"

    assert Crawlfox.get_log(client, "log1")["status"] == "ok"
    assert Crawlfox.get_log_result(client, "log1")["ok"] == true
  end

  test "does not retry quota" do
    n = :counters.new(1, [])

    http = fn _m, _u, _h, _b ->
      :counters.add(n, 1, 1)
      {429, Jason.encode!(%{message: "quota", retryable: false, code: "quota"})}
    end

    client = Crawlfox.new(api_key: "cfx_test", api_url: "https://api.test", retry_backoff_ms: 1, http: http)

    err =
      assert_raise Crawlfox.Error, fn ->
        Crawlfox.scrape(client, "https://example.com")
      end

    assert err.status == 429
    assert :counters.get(n, 1) == 1
  end
end

defmodule CrawlfoxLiveTest do
  use ExUnit.Case

  @moduletag :live

  test "live scrape search batch" do
    :inets.start()
    :ssl.start()
    client = Crawlfox.new(max_retries: 1)
    doc = Crawlfox.scrape(client, "https://example.com", %{"formats" => ["markdown"]})
    assert String.length(doc["markdown"] || "") > 10
    search = Crawlfox.search(client, "crawlfox", %{"engine" => "google", "num" => 3})
    assert length(search["web"]) > 0
    batch = Crawlfox.batch(client, ["https://example.com"], %{"formats" => ["markdown"]})
    assert String.length(get_in(batch, ["data", Access.at(0), "markdown"]) || "") > 5
  end
end
