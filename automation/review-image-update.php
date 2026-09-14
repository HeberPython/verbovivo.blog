<?php
declare(strict_types=1);

// Temporary admin-only endpoint: replace one pending draft image, never publish.
function reject_image(int $status): void {
    http_response_code($status);
    exit('Review image update unavailable');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    reject_image(404);
}
$config = require __DIR__ . '/_private/editorial-config.php';
$expected = (string) ($config['admin_token'] ?? '');
if ($expected === '' || !hash_equals($expected, (string) ($_SERVER['HTTP_X_EDITORIAL_TOKEN'] ?? ''))) {
    reject_image(404);
}
try {
    $input = json_decode((string) file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
    $token = (string) ($input['token'] ?? '');
    $filename = (string) ($input['filename'] ?? '');
    if (!preg_match('/^[A-Za-z0-9_-]{20,}$/', $token)
        || !preg_match('/^review-[a-f0-9]{32}\.png$/', $filename)) {
        reject_image(400);
    }
    $path = __DIR__ . '/_editorial_drafts/' . $token . '.json';
    if (!is_file($path) || is_link($path)) {
        reject_image(404);
    }
    $raw = (string) file_get_contents($path);
    if (!hash_equals(hash('sha256', $raw), (string) ($input['expected_sha256'] ?? ''))) {
        reject_image(409);
    }
    $draft = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
    if (($draft['status'] ?? '') !== 'pending_review' || ($draft['token'] ?? '') !== $token
        || !preg_match('/^[a-z0-9-]+$/', (string) ($draft['slug'] ?? ''))
        || is_file(__DIR__ . '/artigos/' . $draft['slug'] . '.html')) {
        reject_image(409);
    }
    $oldName = (string) ($draft['image_filename'] ?? '');
    if (!preg_match('/^[A-Za-z0-9._-]+\.(png|jpg|jpeg|webp)$/', $oldName)) {
        reject_image(409);
    }
    $oldImage = __DIR__ . '/images/articles/' . $oldName;
    $newImage = __DIR__ . '/images/articles/' . $filename;
    if (!is_file($oldImage) || is_link($oldImage) || file_exists($newImage) || is_link($newImage)) {
        reject_image(409);
    }
    $bytes = base64_decode((string) ($input['image_base64'] ?? ''), true);
    $info = $bytes === false ? false : getimagesizefromstring($bytes);
    if (!$info || $info[2] !== IMAGETYPE_PNG) {
        reject_image(400);
    }
    $parent = realpath(dirname(__DIR__));
    $backupName = '_review_image_backup_' . gmdate('Ymd_His') . '_' . bin2hex(random_bytes(8));
    $backup = $parent . '/' . $backupName;
    $oldMask = umask(0077);
    try {
        if (!$parent || $parent === realpath(__DIR__) || !mkdir($backup, 0700)
            || file_put_contents($backup . '/draft.json', $raw, LOCK_EX) !== strlen($raw)
            || !copy($oldImage, $backup . '/' . $oldName)
            || file_get_contents($backup . '/draft.json') !== $raw
            || hash_file('sha256', $oldImage) !== hash_file('sha256', $backup . '/' . $oldName)) {
            throw new RuntimeException('Backup failed');
        }
    } finally {
        umask($oldMask);
    }
    $handle = fopen($newImage, 'xb');
    if (!$handle || fwrite($handle, $bytes) !== strlen($bytes)) {
        throw new RuntimeException('Image upload failed');
    }
    fclose($handle);
    chmod($newImage, 0644);
    if (hash_file('sha256', $newImage) !== hash('sha256', $bytes)) {
        throw new RuntimeException('Image verification failed');
    }
    $draft['image_filename'] = $filename;
    $newRaw = json_encode($draft, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    $temporary = tempnam(dirname($path), '.image-');
    try {
        if (!$temporary || file_put_contents($temporary, $newRaw, LOCK_EX) !== strlen($newRaw)
            || !chmod($temporary, fileperms($path) & 0777)
            || file_get_contents($path) !== $raw
            || is_file(__DIR__ . '/artigos/' . $draft['slug'] . '.html')
            || !rename($temporary, $path)) {
            throw new RuntimeException('Draft changed or atomic replacement failed');
        }
    } finally {
        if ($temporary && is_file($temporary)) {
            unlink($temporary);
        }
    }
    header('Content-Type: application/json');
    header('Cache-Control: no-store');
    echo json_encode(['backup' => $backupName, 'status' => 'pending_review', 'published' => false]);
} catch (Throwable $error) {
    reject_image(500);
}
