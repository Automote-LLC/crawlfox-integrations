<?php

declare(strict_types=1);

namespace Crawlfox\Tests;

use Crawlfox\Client;
use PHPUnit\Framework\TestCase;

final class LiveTest extends TestCase
{
    public function testLiveScrapeSearchBatch(): void
    {
        $key = getenv('CRAWLFOX_API_KEY');
        if ($key === false || $key === '') {
            $this->markTestSkipped('CRAWLFOX_API_KEY not set');
        }
        $client = new Client($key, getenv('CRAWLFOX_API_URL') ?: 'https://api.crawlfox.io', 90, 1, 200);
        $doc = $client->scrape('https://example.com', ['formats' => ['markdown']]);
        $this->assertNotEmpty($doc['markdown'] ?? null);
        $this->assertGreaterThan(10, strlen((string) $doc['markdown']));
        $search = $client->search('crawlfox', ['engine' => 'google', 'num' => 3]);
        $this->assertNotEmpty($search['web']);
        $batch = $client->batch(['https://example.com'], ['formats' => ['markdown']]);
        $this->assertNotEmpty($batch['data'][0]['markdown'] ?? null);
    }
}
