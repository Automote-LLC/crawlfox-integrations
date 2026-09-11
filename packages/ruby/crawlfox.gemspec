# frozen_string_literal: true

Gem::Specification.new do |s|
  s.name = "crawlfox"
  s.version = "0.1.0"
  s.summary = "Official Ruby SDK for the CrawlFox scrape and search API"
  s.authors = ["Automote LLC"]
  s.email = ["pratik@automote.io"]
  s.homepage = "https://crawlfox.io"
  s.license = "MIT"
  s.files = ["lib/crawlfox.rb", "README.md", "LICENSE"]
  s.require_paths = ["lib"]
  s.required_ruby_version = ">= 3.1"
  s.metadata = {
    "homepage_uri" => "https://crawlfox.io",
    "source_code_uri" => "https://github.com/Automote-LLC/crawlfox-integrations",
    "documentation_uri" => "https://docs.crawlfox.io"
  }
end
