# crawlfox (PHP)

```bash
composer require crawlfox/crawlfox
```

Not published yet — use a path/git dependency until then.

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
