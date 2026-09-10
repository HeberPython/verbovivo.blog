<?php
declare(strict_types=1);

// All publishing paths select the home from published files, never from a truncated home.
function render_current_home(string $html, string $root): string {
    $catalog = [];
    foreach (glob($root . '/artigos/*.html') ?: [] as $path) {
        $source = (string) file_get_contents($path);
        preg_match_all('~<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>~si', $source, $scripts);
        $data = null;
        foreach ($scripts[1] as $script) {
            $candidate = json_decode(html_entity_decode($script, ENT_QUOTES | ENT_HTML5, 'UTF-8'), true);
            if (is_array($candidate) && isset($candidate['headline'], $candidate['datePublished'])) {
                $data = $candidate;
                break;
            }
        }
        if (!$data || strtotime((string) $data['datePublished']) === false) {
            throw new RuntimeException('Missing publication metadata: ' . basename($path));
        }
        $data['slug'] = basename($path, '.html');
        $catalog[] = $data;
    }
    if (!$catalog) {
        throw new RuntimeException('Empty published catalog; home preserved.');
    }
    usort($catalog, static function ($a, $b) {
        return (strtotime($b['datePublished']) <=> strtotime($a['datePublished']))
            ?: strcmp($a['slug'], $b['slug']);
    });
    $escape = static fn($value) => htmlspecialchars((string) $value, ENT_QUOTES, 'UTF-8');
    $cards = [];
    foreach (array_slice($catalog, 0, 4) as $i => $article) {
        $url = 'artigos/' . $article['slug'] . '.html';
        $image = $article['image'] ?? '';
        if (is_array($image)) {
            $image = $image['url'] ?? $image[0] ?? '';
        }
        $class = $i === 0 ? 'featured' : 'article-card';
        $cards[] = '<article class="' . $class . '"><a href="' . $escape($url) . '">'
            . '<img src="' . $escape($image) . '" alt="' . $escape($article['headline']) . '" /></a>'
            . '<div class="article-body"><p class="category">' . $escape($article['articleSection'] ?? 'Reflexão Cristã') . '</p>'
            . '<h3><a href="' . $escape($url) . '">' . $escape($article['headline']) . '</a></h3>'
            . '<p>' . $escape($article['description'] ?? '') . '</p></div></article>';
    }
    $featured = array_shift($cards);
    $html = preg_replace_callback('~<article class="featured">.*?</article>~s', static fn() => $featured, $html, 1, $count);
    if ($count !== 1) {
        throw new RuntimeException('Featured marker missing; home preserved.');
    }
    $html = preg_replace_callback('~(<section\b[^>]*class="[^"]*\barticle-grid\b[^"]*"[^>]*>).*?(</section>)~s',
        static fn($m) => $m[1] . "\n" . implode("\n", $cards) . "\n" . $m[2], $html, 1, $count);
    if ($count !== 1) {
        throw new RuntimeException('Article grid missing; home preserved.');
    }
    return $html;
}

function refresh_current_home(string $root): void {
    $path = $root . '/index.html';
    $lock = fopen($root . '/.home-catalog.lock', 'c');
    if (!$lock || !flock($lock, LOCK_EX)) {
        throw new RuntimeException('Could not lock home.');
    }
    try {
        $html = render_current_home((string) file_get_contents($path), $root);
        $temp = tempnam($root, '.home-');
        if ($temp === false || file_put_contents($temp, $html) === false) {
            throw new RuntimeException('Could not stage home.');
        }
        chmod($temp, 0644);
        if (!rename($temp, $path)) {
            throw new RuntimeException('Could not replace home.');
        }
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}
