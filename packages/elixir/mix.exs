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
      source_url: "https://github.com/Automote-LLC/crawlfox-integrations",
      homepage_url: "https://crawlfox.io",
      docs: [
        main: "Crawlfox",
        extras: ["README.md"]
      ],
      package: [
        licenses: ["MIT"],
        links: %{
          "GitHub" => "https://github.com/Automote-LLC/crawlfox-integrations",
          "Docs" => "https://docs.crawlfox.io",
          "Homepage" => "https://crawlfox.io"
        },
        files: ~w(lib mix.exs README.md LICENSE)
      ]
    ]
  end

  def application do
    [extra_applications: [:logger, :inets, :ssl, :public_key]]
  end

  defp deps do
    [
      {:jason, "~> 1.4"},
      {:ex_doc, "~> 0.34", only: :dev, runtime: false}
    ]
  end
end
