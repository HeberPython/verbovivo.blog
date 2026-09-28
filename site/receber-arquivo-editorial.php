<?php
declare(strict_types=1);

const CONFIG_FILE = __DIR__ . '/_private/editorial-config.php';

function fail(int $status, string $message): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=UTF-8');
    header('Cache-Control: no-store');
    exit(json_encode(['ok' => false, 'error' => $message, 'version' => 1]));
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

if (str_contains($path, '..') || str_contains($path, '\\') || str_starts_with($path, '/')) {
    fail(400, 'Invalid path.');
}

$allowed = false;
if (preg_match('#^(?:artigos|licoes)/[a-z0-9-]+\.html$#D', $path)) {
    $allowed = true;
} elseif (preg_match('#^images/articles/[A-Za-z0-9._-]+\.(?:png|jpg|jpeg|webp)$#D', $path)) {
    $allowed = true;
} elseif (preg_match('#^_editorial_drafts/[A-Za-z0-9_-]+\.json$#D', $path)) {
    $allowed = true;
} elseif (in_array($path, ['index.html', 'artigos.html', 'licoes-escola-dominical.html', 'feed.xml', 'sitemap.xml'], true)) {
    $allowed = true;
}

if (!$allowed) {
    fail(403, 'Path is not allowed.');
}

if (strlen($content) > 44739244) {
    fail(413, 'Content too large.');
}
$bytes = base64_decode($content, true);
if ($bytes === false || strlen($bytes) === 0) {
    fail(400, 'Invalid base64 content.');
}

if (strlen($bytes) > 33554432) {
    fail(413, 'Content too large.');
}

$temporary = null;
try {
    $root = realpath(__DIR__);
    $target = $root;
    foreach (explode('/', $path) as $component) {
        $target .= '/' . $component;
        if (is_link($target)) {
            fail(403, 'Linked destination is not allowed.');
        }
    }
    $directory = dirname($target);
    if (!is_dir($directory) && !mkdir($directory, 0755, true)) {
        throw new RuntimeException('Directory creation failed');
    }
    $resolved = realpath($directory);
    if ($resolved === false || ($resolved !== $root
        && !str_starts_with($resolved . DIRECTORY_SEPARATOR, $root . DIRECTORY_SEPARATOR))) {
        fail(403, 'Destination outside root.');
    }
    $size = strlen($bytes);
    $hash = hash('sha256', $bytes);
    $receipt = ['ok' => true, 'path' => $path, 'version' => 1];
    if ($path === 'index.html') {
        // The home is rebuilt from the server catalog, never from a stale upload.
        require_once __DIR__ . '/home-catalog.php';
        refresh_current_home(__DIR__);
        $receipt['operation'] = 'rebuild_home';
        $receipt['request_size'] = $size;
        $receipt['request_sha256'] = $hash;
    } else {
        $temporary = tempnam($directory, '.editorial-upload-');
        if ($temporary === false
            || file_put_contents($temporary, $bytes, LOCK_EX) !== $size
            || filesize($temporary) !== $size
            || hash_file('sha256', $temporary) !== $hash
            || !chmod($temporary, 0644)
            || !rename($temporary, $target)) {
            throw new RuntimeException('Atomic upload failed');
        }
        $temporary = null;
    }
    clearstatcache(true, $target);
    $stored = file_get_contents($target);
    if ($stored === false || strlen($stored) === 0
        || ($path !== 'index.html' && (strlen($stored) !== $size || hash('sha256', $stored) !== $hash))) {
        throw new RuntimeException('Persistence verification failed');
    }
    $receipt['size'] = strlen($stored);
    $receipt['sha256'] = hash('sha256', $stored);
} catch (Throwable $error) {
    if (is_string($temporary) && is_file($temporary)) {
        unlink($temporary);
    }
    fail(500, 'Upload persistence failed.');
}

header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');
echo json_encode($receipt, JSON_THROW_ON_ERROR);
