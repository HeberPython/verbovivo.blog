<?php
declare(strict_types=1);
// Temporary authenticated repair. Originals stay outside public_html for rollback.
function stop_recovery(int $code): void { http_response_code($code); exit('Recovery unavailable'); }
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { stop_recovery(404); }
$config = require __DIR__ . '/_private/editorial-config.php';
if (empty($config['admin_token']) || !hash_equals((string)$config['admin_token'], (string)($_SERVER['HTTP_X_EDITORIAL_TOKEN'] ?? ''))) { stop_recovery(404); }
$targets = [
    'a4bf10017c3d3fd5' => 'a-boa-obra',
    '3f1963bd6735c1d6' => 'deus-da-presenca',
    '1d0c5a02f63a04fb' => 'construtores-de-altares',
    'd004cd9587f2998f' => 'o-coracao-que-confessa',
];
function write_checked(string $path, string $bytes): void {
    $temp = tempnam(dirname($path), '.recovery-');
    if (!$temp || file_put_contents($temp, $bytes) !== strlen($bytes) || !rename($temp, $path)) {
        throw new RuntimeException('Write failed');
    }
}
function inventory(): array {
    $paths = array_merge(glob(__DIR__ . '/*.*') ?: [], glob(__DIR__ . '/artigos/*.html') ?: [], glob(__DIR__ . '/licoes/*.html') ?: [], glob(__DIR__ . '/_editorial_drafts/*.json') ?: []);
    $result = [];
    foreach ($paths as $path) {
        if (is_file($path) && !is_link($path)) { $result[substr($path, strlen(__DIR__) + 1)] = hash_file('sha256', $path); }
    }
    ksort($result);
    return $result;
}
function verify_catalog(array $slugs): void {
    foreach (['artigos.html', 'feed.xml', 'sitemap.xml'] as $name) {
        $text = (string)file_get_contents(__DIR__ . '/' . $name);
        preg_match_all('~artigos/([a-z0-9-]+)\.html~', $text, $matches);
        $found = array_values(array_unique($matches[1])); sort($found);
        $expected = $slugs; sort($expected);
        if ($found !== $expected) { throw new RuntimeException('Catalog coverage mismatch: ' . $name); }
    }
}
$backup = dirname(__DIR__) . '/_text_recovery_20260924';
$statePath = $backup . '/state.json';
$lock = fopen(__DIR__ . '/.home-catalog.lock', 'c');
if (!$lock || !flock($lock, LOCK_EX)) { stop_recovery(503); }
try {
    $input = json_decode((string)file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
    $action = $input['action'] ?? '';
    if (is_file($statePath)) {
        $state = json_decode((string)file_get_contents($statePath), true, 512, JSON_THROW_ON_ERROR);
    } else { $state = null; }
    if ($action === 'remember') {
        $id = (string)($input['id'] ?? '');
        if (!$state || !isset($targets[$id])) { stop_recovery(409); }
        if (isset($input['draft'])) {
            $draft = $input['draft'];
            $original = $state['originals'][$id];
            if (($draft['slug'] ?? '') !== $targets[$id] || ($draft['status'] ?? '') !== 'pending_review'
                || ($draft['source_text'] ?? '') !== $original['source_text']
                || ($draft['image_filename'] ?? '') !== $original['image_filename']) { stop_recovery(409); }
            if (!isset($state['replacements'][$id])) { $state['replacements'][$id] = $draft; }
        }
        if (!empty($input['notified']) && isset($state['replacements'][$id])) { $state['notified'][$id] = true; }
        write_checked($statePath, json_encode($state, JSON_THROW_ON_ERROR));
    } elseif ($action === 'withdraw' && !$state) {
        $before = inventory();
        $slugs = array_map(static fn($p) => basename($p, '.html'), glob(__DIR__ . '/artigos/*.html') ?: []);
        verify_catalog($slugs);
        $originals = []; $remove = []; $images = [];
        foreach (glob(__DIR__ . '/_editorial_drafts/*.json') ?: [] as $path) {
            $draft = json_decode((string)file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
            $id = $draft['id'] ?? '';
            if (!isset($targets[$id])) { continue; }
            if (isset($originals[$id]) || ($draft['slug'] ?? '') !== $targets[$id] || !in_array($draft['status'] ?? '', ['approved', 'corrected_approved'], true)) { stop_recovery(409); }
            $originals[$id] = $draft;
            $remove[] = substr($path, strlen(__DIR__) + 1);
            $remove[] = 'artigos/' . $targets[$id] . '.html';
            $image = (string)($draft['image_filename'] ?? '');
            if (!preg_match('/^[a-zA-Z0-9._-]+$/', $image) || !is_file(__DIR__ . '/images/articles/' . $image)) { stop_recovery(409); }
            $images['images/articles/' . $image] = hash_file('sha256', __DIR__ . '/images/articles/' . $image);
        }
        if (count($originals) !== 4 || count(array_intersect($slugs, array_values($targets))) !== 4) { stop_recovery(409); }
        // Back up every current article, lesson, draft and root file before any withdrawal.
        $mask = umask(0077);
        if (file_exists($backup) || !mkdir($backup, 0700)) { throw new RuntimeException('Backup already exists or cannot be created'); }
        foreach ($before + $images as $path => $hash) {
            $to = $backup . '/files/' . $path;
            if (!is_dir(dirname($to))) { mkdir(dirname($to), 0700, true); }
            if (!copy(__DIR__ . '/' . $path, $to) || hash_file('sha256', $to) !== $hash) { throw new RuntimeException('Backup verification failed'); }
        }
        umask($mask);
        if (inventory() !== $before) { throw new RuntimeException('Site changed during backup'); }
        $indexes = ['index.html', 'artigos.html', 'feed.xml', 'sitemap.xml'];
        try {
            foreach ($remove as $path) {
                if (!isset($before[$path]) || !unlink(__DIR__ . '/' . $path)) { throw new RuntimeException('Withdrawal failed'); }
            }
            $archive = (string)file_get_contents(__DIR__ . '/artigos.html');
            $archive = preg_replace_callback('~<article\b[^>]*>.*?</article>~s', static function($match) use ($targets) {
                foreach ($targets as $slug) { if (str_contains($match[0], 'artigos/' . $slug . '.html')) { return ''; } }
                return $match[0];
            }, $archive);
            write_checked(__DIR__ . '/artigos.html', $archive);
            foreach (['feed.xml' => ['item', 'link'], 'sitemap.xml' => ['url', 'loc']] as $name => [$element, $link]) {
                $doc = new DOMDocument();
                if (!$doc->load(__DIR__ . '/' . $name, LIBXML_NONET)) { throw new RuntimeException('Invalid XML'); }
                $drop = [];
                foreach ($doc->getElementsByTagName($element) as $node) {
                    $url = $node->getElementsByTagName($link)->item(0)?->textContent ?? '';
                    foreach ($targets as $slug) { if ($url === 'https://verbovivo.blog/artigos/' . $slug . '.html') { $drop[] = $node; } }
                }
                if (count($drop) !== 4) { throw new RuntimeException('Expected exactly four XML entries'); }
                foreach ($drop as $node) { $node->parentNode->removeChild($node); }
                write_checked(__DIR__ . '/' . $name, $doc->saveXML());
            }
            require_once __DIR__ . '/home-catalog.php';
            write_checked(__DIR__ . '/index.html', render_current_home((string)file_get_contents(__DIR__ . '/index.html'), __DIR__));
            $remaining = array_values(array_diff($slugs, array_values($targets)));
            verify_catalog($remaining);
            $after = inventory();
            foreach ($before as $path => $hash) {
                if (in_array($path, $remove, true) || in_array($path, $indexes, true)) { continue; }
                if (($after[$path] ?? '') !== $hash) { throw new RuntimeException('Unrelated file changed'); }
            }
            foreach ($images as $path => $hash) { if (hash_file('sha256', __DIR__ . '/' . $path) !== $hash) { throw new RuntimeException('Image changed'); } }
            $state = ['backup' => basename($backup), 'before_count' => count($slugs), 'after_count' => count($remaining), 'originals' => $originals, 'replacements' => [], 'notified' => []];
            write_checked($statePath, json_encode($state, JSON_THROW_ON_ERROR));
        } catch (Throwable $error) {
            foreach (array_merge($remove, $indexes) as $path) { copy($backup . '/files/' . $path, __DIR__ . '/' . $path); }
            throw $error;
        }
    } elseif ($action !== 'inspect' && $action !== 'withdraw') { stop_recovery(400); }
    header('Content-Type: application/json'); header('Cache-Control: no-store');
    echo json_encode($state ?? ['not_started' => true], JSON_THROW_ON_ERROR);
} catch (Throwable $error) {
    error_log('Four article recovery failed: ' . $error->getMessage());
    stop_recovery(500);
} finally { flock($lock, LOCK_UN); fclose($lock); }
