defmodule Crawlfox do
  @moduledoc """
  Thin official CrawlFox client for scrape, batch, and search.
  """

  @default_url "https://api.crawlfox.io"
  @version "0.1.0"

  defstruct [:api_key, api_url: @default_url]

  defmodule Error do
    defexception [:message, :status, :code, :body]

    @impl true
    def exception(opts) when is_list(opts) do
      %__MODULE__{
        message: Keyword.get(opts, :message, "CrawlFox request failed"),
        status: Keyword.get(opts, :status),
        code: Keyword.get(opts, :code),
        body: Keyword.get(opts, :body)
      }
    end
  end

  def new(opts \\ []) do
    key = Keyword.get(opts, :api_key) || System.get_env("CRAWLFOX_API_KEY")

    if is_nil(key) or key == "" do
      raise ArgumentError, "CrawlFox API key required. Pass api_key or set CRAWLFOX_API_KEY."
    end

    %__MODULE__{
      api_key: key,
      api_url: String.trim_trailing(Keyword.get(opts, :api_url, @default_url), "/")
    }
  end

  def scrape(%__MODULE__{} = client, url, opts \\ %{}) when is_binary(url) do
    body = Map.merge(%{"url" => url}, stringify_keys(opts))
    document(post(client, "/v1/scrape", body))
  end

  def batch(%__MODULE__{} = client, urls, opts \\ %{}) when is_list(urls) do
    body = Map.merge(%{"urls" => urls}, stringify_keys(opts))
    env = post(client, "/v1/batch", body)

    data =
      env
      |> Map.get("results", [])
      |> Enum.map(&document/1)

    %{
      "success" => Map.get(env, "success", true),
      "count" => Map.get(env, "count"),
      "data" => data
    }
  end

  def search(%__MODULE__{} = client, q, opts \\ %{}) when is_binary(q) do
    body = Map.merge(%{"q" => q}, stringify_keys(opts))
    env = post(client, "/v1/search", body)

    %{
      "success" => Map.get(env, "success", true),
      "web" => get_in(env, ["data", "web"]) || [],
      "creditsUsed" => Map.get(env, "creditsUsed"),
      "id" => Map.get(env, "id")
    }
  end

  defp document(envelope) when is_map(envelope) do
    data = Map.get(envelope, "data")
    base = if is_map(data), do: data, else: envelope
    Map.put(base, "success", Map.get(envelope, "success", true))
  end

  defp post(%__MODULE__{} = client, path, body) do
    url = String.to_charlist(client.api_url <> path)
    payload = Jason.encode!(body)
    headers = [
      {~c"Authorization", String.to_charlist("Bearer " <> client.api_key)},
      {~c"Content-Type", ~c"application/json"},
      {~c"User-Agent", String.to_charlist("crawlfox-elixir/" <> @version)}
    ]

    case :httpc.request(:post, {url, headers, ~c"application/json", payload}, [timeout: 120_000], []) do
      {:ok, {{_, status, _}, _headers, resp_body}} ->
        json = decode_body(resp_body)

        if status >= 200 and status < 300 do
          json
        else
          raise Error,
            message: Map.get(json, "message") || Map.get(json, "title") || "CrawlFox request failed (#{status})",
            status: status,
            code: Map.get(json, "code"),
            body: json
        end

      {:error, reason} ->
        raise Error, message: "request failed: #{inspect(reason)}", status: 0
    end
  end

  defp decode_body(body) when is_list(body), do: decode_body(List.to_string(body))
  defp decode_body(body) when is_binary(body) do
    case Jason.decode(body) do
      {:ok, map} -> map
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
