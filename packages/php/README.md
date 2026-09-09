# crawlfox (PHP)

Official PHP SDK for the [CrawlFox](https://crawlfox.io) API: scrape, search (Google or DuckDuckGo), batch (up to 100 URLs), and logs.

Get a key from the [dashboard](https://crawlfox.io). Set `CRAWLFOX_API_KEY`.

```bash
composer require crawlfox/crawlfox
```

```php
use Crawlfox\Client;

$app = new Client(getenv('CRAWLFOX_API_KEY'));

$doc = $app->scrape('https://example.com', [
    'formats' => ['markdown', 'links'],
    'skipCache' => false,
]);
echo $doc['markdown'];

$hits = $app->search('rust async tutorial', [
    'engine' => 'google',
    'num' => 10,
    'country' => 'us',
]);

$batch = $app->batch(
    ['https://example.com/', 'https://example.org/'],
    ['formats' => ['markdown']],
);
```

Formats: `markdown`, `html`, `rawHtml`, `json`, `links`, `images`, `emails`. For `json`, pass `jsonOptions.selectors` (CSS). Credits: 1 per page scrape, 1 per 10 requested search results.

```bash
composer install
vendor/bin/phpunit
# live: CRAWLFOX_API_KEY=... vendor/bin/phpunit
```

Docs: https://docs.crawlfox.io
