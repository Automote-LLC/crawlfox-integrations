<?php

declare(strict_types=1);

namespace Crawlfox;

final class CrawlfoxError extends \RuntimeException
{
    public function __construct(
        string $message,
        public readonly int $status,
        public readonly ?string $errorCode = null,
        public readonly ?bool $retryable = null,
        public readonly array $body = [],
    ) {
        parent::__construct($message, $status);
    }
}

final class Client
{
    public const VERSION = '0.1.0';

    private string $apiKey;
    private string $apiUrl;
    private int $timeoutSeconds;
    private int $maxRetries;
    private int $retryBackoffMs;
    /** @var callable(string, string, array<string, string>, ?string): array{0: int, 1: string} */
    private $transport;

    /**
     * @param callable(string, string, array<string, string>, ?string): array{0: int, 1: string}|null $transport
     */
    public function __construct(
        ?string $apiKey = null,
        ?string $apiUrl = null,
        int $timeoutSeconds = 120,
        int $maxRetries = 2,
        int $retryBackoffMs = 200,
        ?callable $transport = null,
    ) {
        $key = $apiKey ?? (getenv('CRAWLFOX_API_KEY') ?: '');
        if ($key === '') {
            throw new \InvalidArgumentException('CrawlFox API key required. Pass apiKey or set CRAWLFOX_API_KEY.');
        }
        $this->apiKey = $key;
        $this->apiUrl = rtrim($apiUrl ?? (getenv('CRAWLFOX_API_URL') ?: 'https://api.crawlfox.io'), '/');
        $this->timeoutSeconds = $timeoutSeconds;
        $this->maxRetries = $maxRetries;
        $this->retryBackoffMs = $retryBackoffMs;
        $this->transport = $transport ?? [$this, 'curlTransport'];
    }

    public function scrape(string $url, array $options = []): array
    {
        return $this->document($this->request('POST', '/v1/scrape', ['url' => $url] + $options));
    }

    public function scrapeGet(string $url): array
    {
        return $this->document($this->request('GET', '/v1/scrape/' . rawurlencode($url)));
    }

    public function batch(array $urls, array $options = []): array
    {
        $env = $this->request('POST', '/v1/batch', ['urls' => $urls] + $options);
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
        $env = $this->request('POST', '/v1/search', ['q' => $q] + $options);
        return [
            'success' => $env['success'] ?? true,
            'web' => $env['data']['web'] ?? [],
            'creditsUsed' => $env['creditsUsed'] ?? null,
            'id' => $env['id'] ?? null,
        ];
    }

    public function getLog(string $id): array
    {
        return $this->request('GET', '/v1/logs/' . rawurlencode($id));
    }

    public function getLogResult(string $id): array
    {
        return $this->request('GET', '/v1/logs/' . rawurlencode($id) . '/result');
    }

    private function document(array $envelope): array
    {
        $data = is_array($envelope['data'] ?? null) ? $envelope['data'] : $envelope;
        $data['success'] = $envelope['success'] ?? true;
        return $data;
    }

    private static function isRetryable(CrawlfoxError $err): bool
    {
        if ($err->retryable === false) {
            return false;
        }
        if ($err->retryable === true) {
            return true;
        }
        return in_array($err->status, [502, 503, 504], true);
    }

    private function request(string $method, string $path, ?array $body = null): array
    {
        $payload = $body === null ? null : json_encode($body, JSON_THROW_ON_ERROR);
        $headers = [
            'Authorization' => 'Bearer ' . $this->apiKey,
            'Content-Type' => 'application/json',
            'User-Agent' => 'crawlfox-php/' . self::VERSION,
        ];
        $url = $this->apiUrl . $path;
        $attempts = $this->maxRetries + 1;
        $last = null;
        for ($i = 0; $i < $attempts; $i++) {
            [$status, $raw] = ($this->transport)($method, $url, $headers, $payload);
            $json = json_decode((string) $raw, true);
            if (!is_array($json)) {
                $json = [];
            }
            if ($status >= 200 && $status < 300) {
                return $json;
            }
            $err = new CrawlfoxError(
                (string) ($json['message'] ?? $json['title'] ?? "CrawlFox request failed ($status)"),
                $status,
                isset($json['code']) ? (string) $json['code'] : null,
                array_key_exists('retryable', $json) ? (bool) $json['retryable'] : null,
                $json,
            );
            if ($i < $attempts - 1 && self::isRetryable($err)) {
                $last = $err;
                usleep($this->retryBackoffMs * 1000 * (2 ** $i));
                continue;
            }
            throw $err;
        }
        throw $last ?? new CrawlfoxError('Request failed', 0);
    }

    /**
     * @param array<string, string> $headers
     * @return array{0: int, 1: string}
     */
    private function curlTransport(string $method, string $url, array $headers, ?string $body): array
    {
        $ch = curl_init($url);
        $headerLines = [];
        foreach ($headers as $k => $v) {
            $headerLines[] = $k . ': ' . $v;
        }
        $opts = [
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => $headerLines,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $this->timeoutSeconds,
        ];
        if ($body !== null) {
            $opts[CURLOPT_POSTFIELDS] = $body;
        }
        curl_setopt_array($ch, $opts);
        $raw = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $cerr = curl_error($ch);
        curl_close($ch);
        if ($raw === false) {
            throw new CrawlfoxError($cerr !== '' ? $cerr : 'request failed', 0, null, true);
        }
        return [$status, (string) $raw];
    }
}
