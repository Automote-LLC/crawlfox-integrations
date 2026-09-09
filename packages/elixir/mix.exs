defmodule Crawlfox.MixProject do
  use Mix.Project

  def project do
    [
      app: :crawlfox,
      version: "0.1.0",
      elixir: "~> 1.14",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      description: "Official Elixir SDK for the CrawlFox scrape and search API",
      package: [
        licenses: ["MIT"],
        links: %{"GitHub" => "https://github.com/Automote-LLC/crawlfox-integrations"}
      ]
    ]
  end

  def application do
    [extra_applications: [:logger, :inets, :ssl]]
  end

  defp deps do
    [{:jason, "~> 1.4"}]
  end
end
