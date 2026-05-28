<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'method_not_allowed']);
    exit;
}

$raw = file_get_contents('php://input');
if ($raw === false || strlen($raw) > 8192) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'invalid_payload']);
    exit;
}

$data = json_decode($raw, true);
if (!is_array($data)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'invalid_json']);
    exit;
}

$allowedEvents = ['pageview', 'heartbeat', 'pagehide'];
$event = isset($data['event']) ? (string) $data['event'] : '';
if (!in_array($event, $allowedEvents, true)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'invalid_event']);
    exit;
}

function clean_string(array $data, string $key, int $maxLength): string
{
    $value = isset($data[$key]) ? (string) $data[$key] : '';
    $value = preg_replace('/[\x00-\x1F\x7F]/u', '', $value) ?? '';
    return substr($value, 0, $maxLength);
}

$privateDir = __DIR__ . '/_private';
if (!is_dir($privateDir)) {
    mkdir($privateDir, 0755, true);
}

$saltFile = $privateDir . '/analytics-salt.txt';
if (!is_file($saltFile)) {
    file_put_contents($saltFile, bin2hex(random_bytes(16)), LOCK_EX);
}
$salt = trim((string) file_get_contents($saltFile));
$ip = $_SERVER['REMOTE_ADDR'] ?? '';
$userAgent = $_SERVER['HTTP_USER_AGENT'] ?? '';

$entry = [
    'ts' => gmdate('c'),
    'event' => $event,
    'session_id' => clean_string($data, 'session_id', 80),
    'page_id' => clean_string($data, 'page_id', 80),
    'path' => clean_string($data, 'path', 300),
    'title' => clean_string($data, 'title', 200),
    'referrer' => clean_string($data, 'referrer', 500),
    'elapsed_seconds' => max(0, min(86400, (int) ($data['elapsed_seconds'] ?? 0))),
    'language' => clean_string($data, 'language', 40),
    'timezone' => clean_string($data, 'timezone', 80),
    'screen' => clean_string($data, 'screen', 40),
    'viewport' => clean_string($data, 'viewport', 40),
    'ip_hash' => hash('sha256', $salt . '|' . $ip),
    'user_agent' => substr((string) $userAgent, 0, 300),
];

$line = json_encode($entry, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . PHP_EOL;
file_put_contents($privateDir . '/analytics-events.jsonl', $line, FILE_APPEND | LOCK_EX);

echo json_encode(['ok' => true]);
