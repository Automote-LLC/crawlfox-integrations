defmodule Crawlfox do
  @moduledoc """
  Official CrawlFox client for scrape, batch, search, and logs.
  """

  @default_url "https://api.crawlfox.io"
  @version "0.1.0"

  defstruct [
    :api_key,
    api_url: @default_url,
    max_retries: 2,
    retry_backoff_ms: 200,
    http: nil
  ]

  defmodule Error do
    defexception [:message, :status, :code, :retryable, :body]

    @impl true
    def exception(opts) when is_list(opts) do
      %__MODULE__{
        message: Keyword.get(opts, :message, "CrawlFox request failed"),
        status: Keyword.get(opts, :status),
        code: Keyword.get(opts, :code),
        retryable: Keyword.get(opts, :retryable),
        body: Keyword.get(opts, :body)
      }
    end

    def retryable_effective?(%__MODULE__{} = err) do
      cond do
        err.retryable == false -> false
        err.retryable == true -> true
        err.status in [502, 503, 504] -> true
        true -> false
      end
    end
  end

  def new(opts \\ []) do
    key = Keyword.get(opts, :api_key) || System.get_env("CRAWLFOX_API_KEY")

    if is_nil(key) or key == "" do
      raise ArgumentError, "CrawlFox API key required. Pass api_key or set CRAWLFOX_API_KEY."
    end

    %__MODULE__{
      api_key: key,
      api_url: String.trim_trailing(Keyword.get(opts, :api_url, System.get_env("CRAWLFOX_API_URL") || @default_url), "/"),
      max_retries: Keyword.get(opts, :max_retries, 2),
      retry_backoff_ms: Keyword.get(opts, :retry_backoff_ms, 200),
      http: Keyword.get(opts, :http)
    }
  end

  def scrape(%__MODULE__{} = client, url, opts \\ %{}) when is_binary(url) do
    body = Map.merge(stringify_keys(opts), %{"url" => url})
    document(request(client, "POST", "/v1/scrape", body))
  end

  def scrape_get(%__MODULE__{} = client, url) when is_binary(url) do
    document(request(client, "GET", "/v1/scrape/" <> URI.encode_www_form(url), nil))
  end

  def batch(%__MODULE__{} = client, urls, opts \\ %{}) when is_list(urls) do
    body = Map.merge(stringify_keys(opts), %{"urls" => urls})
    env = request(client, "POST", "/v1/batch", body)

    data =
      env
      |> Map.get("results", [])
      |> Enum.map(&document/1)

    %{
      "success" => Map.get(env, "success", true),
      "count" => Map.get(env, "count", length(data)),
      "data" => data
    }
  end

  def search(%__MODULE__{} = client, q, opts \\ %{}) when is_binary(q) do
    body = Map.merge(stringify_keys(opts), %{"q" => q})
    env = request(client, "POST", "/v1/search", body)

    %{
      "success" => Map.get(env, "success", true),
      "web" => get_in(env, ["data", "web"]) || [],
      "creditsUsed" => Map.get(env, "creditsUsed"),
      "id" => Map.get(env, "id")
    }
  end

  def get_log(%__MODULE__{} = client, id) when is_binary(id) do
    request(client, "GET", "/v1/logs/" <> URI.encode_www_form(id), nil)
  end

  def get_log_result(%__MODULE__{} = client, id) when is_binary(id) do
    request(client, "GET", "/v1/logs/" <> URI.encode_www_form(id) <> "/result", nil)
  end

  defp document(envelope) when is_map(envelope) do
    data = Map.get(envelope, "data")
    base = if is_map(data), do: data, else: envelope
    Map.put(base, "success", Map.get(envelope, "success", true))
  end

  defp request(%__MODULE__{} = client, method, path, body) do
    url = client.api_url <> path
    payload = if is_nil(body), do: nil, else: Jason.encode!(body)

    headers = %{
      "Authorization" => "Bearer " <> client.api_key,
      "Content-Type" => "application/json",
      "User-Agent" => "crawlfox-elixir/" <> @version
    }

    attempts = client.max_retries + 1
    do_request(client, method, url, headers, payload, attempts, 0, nil)
  end

  defp do_request(_client, _method, _url, _headers, _payload, attempts, i, last_err) when i >= attempts do
    raise last_err || Error.exception(message: "Request failed", status: 0)
  end

  defp do_request(client, method, url, headers, payload, attempts, i, _last) do
    {status, raw} = call_http(client, method, url, headers, payload)
    json = decode_body(raw)

    if status >= 200 and status < 300 do
      json
    else
      err =
        Error.exception(
          message: Map.get(json, "message") || Map.get(json, "title") || "CrawlFox request failed (#{status})",
          status: status,
          code: Map.get(json, "code"),
          retryable: Map.get(json, "retryable"),
          body: json
        )

      if i < attempts - 1 and Error.retryable_effective?(err) do
        Process.sleep(client.retry_backoff_ms * Integer.pow(2, i))
        do_request(client, method, url, headers, payload, attempts, i + 1, err)
      else
        raise err
      end
    end
  end

  defp call_http(%__MODULE__{http: http}, method, url, headers, payload) when is_function(http, 4) do
    http.(method, url, headers, payload)
  end

  defp call_http(%__MODULE__{}, method, url, headers, payload) do
    char_url = String.to_charlist(url)

    header_list =
      Enum.map(headers, fn {k, v} -> {String.to_charlist(k), String.to_charlist(v)} end)

    http_method = String.downcase(method) |> String.to_atom()

    request =
      if payload do
        {char_url, header_list, ~c"application/json", payload}
      else
        {char_url, header_list}
      end

    http_opts = [timeout: 120_000, ssl: ssl_opts(url)]

    case :httpc.request(http_method, request, http_opts, []) do
      {:ok, {{_, status, _}, _headers, resp_body}} ->
        {status, resp_body}

      {:error, reason} ->
        raise Error, message: "request failed: #{inspect(reason)}", status: 0, retryable: true
    end
  end

  defp ssl_opts(url) do
    host =
      case URI.parse(url) do
        %URI{host: host} when is_binary(host) -> String.to_charlist(host)
        _ -> ~c""
      end

    [
      verify: :verify_peer,
      cacerts: :public_key.cacerts_get(),
      server_name_indication: host
    ]
  end

  defp decode_body(body) when is_list(body), do: decode_body(List.to_string(body))

  defp decode_body(body) when is_binary(body) do
    case Jason.decode(body) do
      {:ok, map} when is_map(map) -> map
      _ -> %{}
    end
  end

  defp stringify_keys(map) when is_map(map) do
    Map.new(map, fn
      {k, v} when is_atom(k) -> {Atom.to_string(k), v}
      {k, v} -> {k, v}
    end)
  end
end
