<?php
declare(strict_types=1);

const CONFIG_FILE = __DIR__ . '/_private/editorial-config.php';

function fail(int $status, string $message): void {
    http_response_code($status);
    header('Content-Type: text/plain; charset=UTF-8');
    exit($message);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    fail(404, 'Not found');
}

if (!is_file(CONFIG_FILE)) {
    fail(500, 'Missing private config.');
}

$config = require CONFIG_FILE;
$providedToken = $_POST['token'] ?? ($_SERVER['HTTP_X_EDITORIAL_TOKEN'] ?? '');
$expectedToken = (string) ($config['admin_token'] ?? '');
if (!is_string($providedToken) || $expectedToken === '' || !hash_equals($expectedToken, $providedToken)) {
    fail(404, 'Not found');
}

$path = $_POST['path'] ?? '';
$content = $_POST['content_base64'] ?? '';
if (!is_string($path) || !is_string($content) || $path === '' || $content === '') {
    fail(400, 'Missing path or content.');
}

$path = str_replace('\\', '/', ltrim($path, '/'));
if (str_contains($path, '..') || str_starts_with($path, './')) {
    fail(400, 'Invalid path.');
}

$allowed = false;
if (preg_match('#^artigos/[a-z0-9-]+\.html$#', $path)) {
    $allowed = true;
} elseif (preg_match('#^images/articles/[A-Za-z0-9._-]+\.(?:png|jpg|jpeg|webp)$#', $path)) {
    $allowed = true;
} elseif (preg_match('#^_editorial_drafts/[A-Za-z0-9_-]+\.json$#', $path)) {
    $allowed = true;
} elseif (in_array($path, ['index.html', 'feed.xml', 'sitemap.xml'], true)) {
    $allowed = true;
}

if (!$allowed) {
    fail(403, 'Path is not allowed.');
}

$bytes = base64_decode($content, true);
if ($bytes === false) {
    fail(400, 'Invalid base64 content.');
}

$target = __DIR__ . '/' . $path;
$directory = dirname($target);
if (!is_dir($directory) && !mkdir($directory, 0755, true)) {
    fail(500, 'Could not create directory.');
}

if (file_put_contents($target, $bytes, LOCK_EX) === false) {
    fail(500, 'Could not write file.');
}

header('Content-Type: text/plain; charset=UTF-8');
echo 'OK ' . $path;
