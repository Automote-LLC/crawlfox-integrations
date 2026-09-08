<?php

declare(strict_types=1);

namespace Crawlfox;

final class CrawlfoxError extends \RuntimeException
{
    public function __construct(
        string $message,
        public readonly int $status,
        public readonly ?string $code = null,
        public readonly ?bool $retryable = null,
        public readonly array $body = [],
    ) {
        parent::__construct($message, $status);
    }
}

final class Client
{
    private string $apiKey;
    private string $apiUrl;
    private int $timeoutSeconds;

    public function __construct(?string $apiKey = null, string $apiUrl = 'https://api.crawlfox.io', int $timeoutSeconds = 120)
    {
        $key = $apiKey ?? getenv('CRAWLFOX_API_KEY') ?: '';
        if ($key === '') {
            throw new \InvalidArgumentException('CrawlFox API key required. Pass apiKey or set CRAWLFOX_API_KEY.');
        }
        $this->apiKey = $key;
        $this->apiUrl = rtrim($apiUrl, '/');
        $this->timeoutSeconds = $timeoutSeconds;
    }

    public function scrape(string $url, array $options = []): array
    {
        return $this->document($this->post('/v1/scrape', ['url' => $url] + $options));
    }

    public function batch(array $urls, array $options = []): array
    {
        $env = $this->post('/v1/batch', ['urls' => $urls] + $options);
        $data = [];
        foreach ($env['results'] ?? [] as $item) {
            $data[] = $this->document($item);
        }
        return [
            'success' => $env['success'] ?? true,
            'count' => $env['count'] ?? count($data),
            'data' => $data,
        ];
    }

    public function search(string $q, array $options = []): array
    {
        $env = $this->post('/v1/search', ['q' => $q] + $options);
        return [
            'success' => $env['success'] ?? true,
            'web' => $env['data']['web'] ?? [],
            'creditsUsed' => $env['creditsUsed'] ?? null,
            'id' => $env['id'] ?? null,
        ];
    }

    private function document(array $envelope): array
    {
        $data = is_array($envelope['data'] ?? null) ? $envelope['data'] : $envelope;
        $data['success'] = $envelope['success'] ?? true;
        return $data;
    }

    private function post(string $path, array $body): array
    {
        $ch = curl_init($this->apiUrl . $path);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $this->apiKey,
                'Content-Type: application/json',
                'User-Agent: crawlfox-php/0.1.0',
            ],
            CURLOPT_POSTFIELDS => json_encode($body),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $this->timeoutSeconds,
        ]);
        $raw = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($raw === false) {
            throw new CrawlfoxError('request failed', 0);
        }
        $json = json_decode((string) $raw, true) ?? [];
        if ($status < 200 || $status >= 300) {
            throw new CrawlfoxError(
                (string) ($json['message'] ?? $json['title'] ?? "CrawlFox request failed ($status)"),
                $status,
                $json['code'] ?? null,
                $json['retryable'] ?? null,
                $json,
            );
        }
        return $json;
    }
}
