<?php
declare(strict_types=1);

// Temporary authenticated bootstrap. Only the scheduler command can change.
function reject_mode(int $status): void {
    http_response_code($status);
    exit('Scheduler update unavailable');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    reject_mode(404);
}
$existing = require __DIR__ . '/_private/editorial-config.php';
$expected = (string) ($existing['admin_token'] ?? '');
if ($expected === '' || !hash_equals($expected, (string) ($_SERVER['HTTP_X_EDITORIAL_TOKEN'] ?? ''))) {
    reject_mode(404);
}
try {
    $payload = json_decode((string) file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
    $mode = $payload['command'] ?? '';
    if (!in_array($mode, ['all', 'email-audit'], true)) {
        reject_mode(400);
    }
    $site = realpath(__DIR__);
    $directory = dirname(__DIR__) . '/_verbovivo_scheduler';
    if (is_link($directory) || realpath($directory) !== $directory
        || str_starts_with($directory . '/', $site . '/')) {
        reject_mode(409);
    }
    $path = $directory . '/scheduler-config.json';
    $script = $directory . '/dispatch-editorial.php';
    if (is_link($path) || is_link($script) || !is_file($path) || !is_file($script)
        || (fileperms($path) & 0777) !== 0600
        || hash_file('sha256', $script) !== '949e1119643dd10d9e35d99e5378c4448cd0a86301e6e8de40385be47490f699') {
        reject_mode(409);
    }
    $lock = fopen($directory . '/scheduler.lock', 'c+');
    if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) {
        reject_mode(409);
    }
    $before = (string) file_get_contents($path);
    $config = json_decode($before, true, 512, JSON_THROW_ON_ERROR);
    if (($config['enabled'] ?? false) !== true || empty($config['github_token'])
        || !in_array($config['command'] ?? '', ['all', 'email-audit'], true)) {
        reject_mode(409);
    }
    $previous = $config['command'];
    $backupName = null;
    if ($previous !== $mode) {
        $oldMask = umask(0077);
        try {
            $backupName = 'before-mode-' . gmdate('Ymd-His') . '-' . bin2hex(random_bytes(6));
            $backup = $directory . '/' . $backupName;
            if (!mkdir($backup, 0700)
                || file_put_contents($backup . '/scheduler-config.json', $before, LOCK_EX) !== strlen($before)
                || !copy($script, $backup . '/dispatch-editorial.php')
                || file_get_contents($backup . '/scheduler-config.json') !== $before
                || hash_file('sha256', $backup . '/dispatch-editorial.php') !== hash_file('sha256', $script)) {
                throw new RuntimeException('Private backup failed');
            }
            $config['command'] = $mode;
            $updated = json_encode($config, JSON_THROW_ON_ERROR);
            $temporary = tempnam($directory, '.mode-');
            try {
                if (!$temporary || file_put_contents($temporary, $updated, LOCK_EX) !== strlen($updated)
                    || !chmod($temporary, 0600) || file_get_contents($temporary) !== $updated
                    || file_get_contents($path) !== $before || !rename($temporary, $path)) {
                    throw new RuntimeException('Atomic update failed');
                }
            } finally {
                if ($temporary && is_file($temporary)) {
                    unlink($temporary);
                }
            }
        } finally {
            umask($oldMask);
        }
    }
    clearstatcache(true, $path);
    $verified = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
    if ($verified !== $config || (fileperms($path) & 0777) !== 0600) {
        throw new RuntimeException('Configuration verification failed');
    }
    header('Content-Type: application/json');
    header('Cache-Control: no-store');
    echo json_encode([
        'mode' => $verified['command'], 'previous_mode' => $previous,
        'backup_name' => $backupName, 'config_permissions' => '600',
        'script_sha256' => hash_file('sha256', $script), 'outside_public_html' => true,
    ], JSON_THROW_ON_ERROR);
} catch (Throwable $error) {
    reject_mode(500);
}
