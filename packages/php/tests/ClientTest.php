<?php

declare(strict_types=1);

namespace Crawlfox\Tests;

use Crawlfox\Client;
use Crawlfox\CrawlfoxError;
use PHPUnit\Framework\TestCase;

final class ClientTest extends TestCase
{
    public function testRequiresApiKey(): void
    {
        $prev = getenv('CRAWLFOX_API_KEY');
        putenv('CRAWLFOX_API_KEY');
        $this->expectException(\InvalidArgumentException::class);
        try {
            new Client();
        } finally {
            if ($prev !== false) {
                putenv('CRAWLFOX_API_KEY=' . $prev);
            }
        }
    }

    public function testScrapeSendsDocument(): void
    {
        $calls = [];
        $client = $this->client(function (string $method, string $url, array $headers, ?string $body) use (&$calls) {
            $calls[] = compact('method', 'url', 'headers', 'body');
            return [200, json_encode([
                'success' => true,
                'data' => ['markdown' => '# Hello', 'metadata' => ['statusCode' => 200]],
            ])];
        });
        $doc = $client->scrape('https://example.com', [
            'formats' => ['markdown'],
            'country' => 'de',
            'redactPII' => true,
        ]);
        $this->assertTrue($doc['success']);
        $this->assertSame('# Hello', $doc['markdown']);
        $this->assertCount(1, $calls);
        $this->assertSame('POST', $calls[0]['method']);
        $this->assertStringEndsWith('/v1/scrape', $calls[0]['url']);
        $this->assertSame('Bearer cfx_test', $calls[0]['headers']['Authorization']);
        $this->assertStringStartsWith('crawlfox-php/', $calls[0]['headers']['User-Agent']);
        $payload = json_decode($calls[0]['body'], true);
        $this->assertSame('https://example.com', $payload['url']);
        $this->assertSame('de', $payload['country']);
        $this->assertTrue($payload['redactPII']);
    }

    public function testSearchAndBatchAndLogs(): void
    {
        $client = $this->client(function (string $method, string $url, array $headers, ?string $body) {
            if (str_contains($url, '/v1/search')) {
                return [200, json_encode([
                    'success' => true,
                    'data' => ['web' => [['url' => 'https://example.com', 'title' => 'Ex']]],
                    'id' => 'abc',
                ])];
            }
            if (str_contains($url, '/v1/batch')) {
                return [200, json_encode([
                    'success' => true,
                    'count' => 1,
                    'results' => [['success' => true, 'data' => ['markdown' => '# A']]],
                ])];
            }
            if (str_contains($url, '/result')) {
                return [200, json_encode(['ok' => true])];
            }
            if (str_contains($url, '/v1/logs/')) {
                $this->assertSame('GET', $method);
                return [200, json_encode(['id' => 'log1', 'status' => 'ok'])];
            }
            return [404, '{}'];
        });
        $search = $client->search('crawlfox', ['engine' => 'google', 'num' => 5]);
        $this->assertSame('https://example.com', $search['web'][0]['url']);
        $batch = $client->batch(['https://example.org']);
        $this->assertSame('# A', $batch['data'][0]['markdown']);
        $log = $client->getLog('log1');
        $this->assertSame('ok', $log['status']);
        $this->assertSame(['ok' => true], $client->getLogResult('log1'));
    }

    public function testRetriesRetryableThenSucceeds(): void
    {
        $n = 0;
        $client = $this->client(function () use (&$n) {
            $n++;
            if ($n === 1) {
                return [503, json_encode(['message' => 'busy', 'retryable' => true])];
            }
            return [200, json_encode(['success' => true, 'data' => ['markdown' => '# ok']])];
        });
        $doc = $client->scrape('https://example.com');
        $this->assertSame('# ok', $doc['markdown']);
        $this->assertSame(2, $n);
    }

    public function testDoesNotRetryQuota(): void
    {
        $n = 0;
        $client = $this->client(function () use (&$n) {
            $n++;
            return [429, json_encode(['message' => 'quota', 'retryable' => false, 'code' => 'quota'])];
        });
        try {
            $client->scrape('https://example.com');
            $this->fail('expected error');
        } catch (CrawlfoxError $e) {
            $this->assertSame(429, $e->status);
            $this->assertFalse($e->retryable);
            $this->assertSame(1, $n);
        }
    }

    /** @param callable(string, string, array<string, string>, ?string): array{0: int, 1: string} $transport */
    private function client(callable $transport): Client
    {
        return new Client('cfx_test', 'https://api.test', 5, 2, 1, $transport);
    }
}
