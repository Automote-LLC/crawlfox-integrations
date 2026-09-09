# crawlfox (PHP)

Official PHP SDK for the [CrawlFox](https://crawlfox.io) scrape and search API.

```bash
composer require crawlfox/crawlfox
```

```php
use Crawlfox\Client;

$app = new Client(getenv('CRAWLFOX_API_KEY'));
$doc = $app->scrape('https://example.com', ['formats' => ['markdown']]);
echo $doc['markdown'];

$hits = $app->search('crawlfox', ['engine' => 'google', 'num' => 5]);
$batch = $app->batch(['https://example.org'], ['formats' => ['markdown']]);
```

```bash
composer install
vendor/bin/phpunit
# live tests: CRAWLFOX_API_KEY=... vendor/bin/phpunit
```
