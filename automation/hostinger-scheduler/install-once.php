<?php
declare(strict_types=1);

// Temporary bootstrap, removed immediately by the installer. No embedded secrets.
function reject_install(int $status): void {
    http_response_code($status);
    exit('Installation unavailable');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    reject_install(404);
}
$existing = require __DIR__ . '/_private/editorial-config.php';
$expected = (string) ($existing['admin_token'] ?? '');
$supplied = (string) ($_SERVER['HTTP_X_EDITORIAL_TOKEN'] ?? '');
if ($expected === '' || !hash_equals($expected, $supplied)) {
    reject_install(404);
}
try {
    $payload = json_decode((string) file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
    $script = base64_decode((string) ($payload['script'] ?? ''), true);
    $token = (string) ($payload['github_token'] ?? '');
    if (!$script || !str_starts_with($script, '<?php') || !str_starts_with($token, 'github_pat_')) {
        reject_install(400);
    }
    $site = realpath(__DIR__);
    $parent = realpath(dirname(__DIR__));
    if (!$site || !$parent || $parent === $site || !is_writable($parent)) {
        reject_install(409);
    }
    $directory = $parent . '/_verbovivo_scheduler';
    // First installation only: never overwrite an existing private configuration.
    if (file_exists($directory) || is_link($directory) || !mkdir($directory, 0700)) {
        reject_install(409);
    }
    $config = json_encode(['github_token' => $token, 'enabled' => true, 'command' => 'email-audit'], JSON_THROW_ON_ERROR);
    $oldMask = umask(0077);
    try {
        if (file_put_contents($directory . '/scheduler-config.json', $config, LOCK_EX) === false
            || file_put_contents($directory . '/dispatch-editorial.php', $script, LOCK_EX) === false) {
            reject_install(500);
        }
    } finally {
        umask($oldMask);
    }
    header('Content-Type: application/json');
    header('Cache-Control: no-store');
    echo json_encode([
        'installed' => true,
        'mode' => 'email-audit',
        'script_path' => $directory . '/dispatch-editorial.php',
        'script_sha256' => hash_file('sha256', $directory . '/dispatch-editorial.php'),
        'outside_public_html' => !str_starts_with(realpath($directory) . '/', $site . '/'),
        'config_permissions' => decoct(fileperms($directory . '/scheduler-config.json') & 0777),
    ], JSON_THROW_ON_ERROR);
} catch (Throwable $error) {
    reject_install(500);
}
