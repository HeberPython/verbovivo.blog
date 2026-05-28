<?php
declare(strict_types=1);

const DOMAIN = 'https://verbovivo.blog';
const ARTICLE_DIR = __DIR__ . '/artigos';
const CONFIG_FILE = __DIR__ . '/_private/editorial-config.php';

if (!function_exists('str_contains')) {
    function str_contains(string $haystack, string $needle): bool {
        return $needle === '' || strpos($haystack, $needle) !== false;
    }
}

if (!is_file(CONFIG_FILE)) {
    http_response_code(500);
    exit('Configuracao privada ausente.');
}

$config = require CONFIG_FILE;

function esc(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function admin_token(): string {
    global $config;
    return (string) ($config['admin_token'] ?? '');
}

function require_admin(): string {
    $token = $_POST['token'] ?? $_GET['token'] ?? '';
    $expected = admin_token();
    if (!is_string($token) || $expected === '' || !hash_equals($expected, $token)) {
        http_response_code(404);
        exit('Pagina nao encontrada.');
    }
    return $token;
}

function slugify(string $value): string {
    $value = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value) ?: $value;
    $value = strtolower((string) preg_replace('/[^a-zA-Z0-9]+/', '-', $value));
    $value = trim($value, '-');
    return $value !== '' ? $value : bin2hex(random_bytes(4));
}

function match_one(string $pattern, string $html, string $default = ''): string {
    return preg_match($pattern, $html, $m) ? html_entity_decode(trim((string) $m[1]), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') : $default;
}

function text_contains(string $haystack, string $needle): bool {
    return $needle === '' || strpos($haystack, $needle) !== false;
}

function article_path(string $slug): string {
    if (!preg_match('/^[a-z0-9-]+$/', $slug)) {
        http_response_code(400);
        exit('Slug invalido.');
    }
    return ARTICLE_DIR . '/' . $slug . '.html';
}

function list_articles(): array {
    $items = [];
    foreach (glob(ARTICLE_DIR . '/*.html') ?: [] as $path) {
        $html = (string) file_get_contents($path);
        $slug = basename($path, '.html');
        $items[] = [
            'slug' => $slug,
            'title' => match_one('/<h1>(.*?)<\/h1>/s', $html, $slug),
            'excerpt' => match_one('/<p class="article-excerpt">(.*?)<\/p>/s', $html),
            'author' => preg_replace('/^Por\s+/u', '', match_one('/<p class="article-meta">(.*?)<\/p>/s', $html)),
        ];
    }
    usort($items, function (array $a, array $b): int {
        return strcmp((string) $a['title'], (string) $b['title']);
    });
    return $items;
}

function load_article(string $slug): array {
    $path = article_path($slug);
    if (!is_file($path)) {
        http_response_code(404);
        exit('Artigo nao encontrado.');
    }
    $html = (string) file_get_contents($path);
    $body = '';
    if (preg_match('/<div class="article-content">(.*?)<\/div>\s*<\/article>/s', $html, $m)) {
        $body = trim((string) $m[1]);
    }
    return [
        'slug' => $slug,
        'title' => match_one('/<h1>(.*?)<\/h1>/s', $html, $slug),
        'category' => match_one('/<p class="category">(.*?)<\/p>/s', $html, 'Reflexao'),
        'excerpt' => match_one('/<p class="article-excerpt">(.*?)<\/p>/s', $html),
        'author' => preg_replace('/^Por\s+/u', '', match_one('/<p class="article-meta">(.*?)<\/p>/s', $html, '')),
        'image_filename' => match_one('/<img src="\.\.\/images\/articles\/([^"]+)"/s', $html),
        'body_html' => $body,
    ];
}

function listen_controls(): string {
    return '<div class="listen-tools" aria-label="Narracao do artigo"><button class="listen-button" type="button" data-listen-toggle aria-label="Ouvir artigo" title="Ouvir artigo"><svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"></path><path d="M16 9.5c1.1 1.4 1.1 3.6 0 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path><path d="M18.8 7c2.3 2.8 2.3 7.2 0 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg></button><span data-listen-status>Clique para ouvir o artigo.</span></div>';
}

function listen_script(): string {
    return '<script>(()=>{const c=document.querySelector(".listen-tools"),a=document.querySelector(".article-content");if(!c||!a)return;const s=c.querySelector("[data-listen-status]"),b=c.querySelector("[data-listen-toggle]"),y=window.speechSynthesis;if(!("speechSynthesis" in window)){if(b)b.disabled=true;if(s)s.textContent="Narracao indisponivel neste navegador.";return}const set=t=>{if(s)s.textContent=t};const btn=t=>{if(!b)return;b.classList.toggle("is-speaking",t);b.setAttribute("aria-label",t?"Pausar narracao":"Ouvir artigo")};c.addEventListener("click",e=>{if(!e.target.closest("[data-listen-toggle]"))return;if(y.speaking&&!y.paused){y.pause();btn(false);set("Narracao pausada.");return}if(y.paused){y.resume();btn(true);set("Narrando artigo.");return}y.cancel();const u=new SpeechSynthesisUtterance(a.innerText.replace(/\s+/g," ").trim());u.lang="pt-BR";u.rate=.95;u.onend=()=>{btn(false);set("Narracao concluida.")};y.speak(u);btn(true);set("Narrando artigo.")});window.addEventListener("beforeunload",()=>y.cancel())})();</script>';
}

function render_article_page(array $article): string {
    $slug = (string) $article['slug'];
    $title = (string) $article['title'];
    $excerpt = (string) $article['excerpt'];
    $category = (string) $article['category'];
    $author = (string) $article['author'];
    $image = trim((string) $article['image_filename']);
    $imageHtml = $image !== '' ? '<img src="../images/articles/' . esc($image) . '" alt="' . esc($title) . '" />' : '';
    return '<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>' . esc($title) . ' | Verbo Vivo</title>
    <meta name="description" content="' . esc($excerpt) . '" />
    <link rel="canonical" href="' . DOMAIN . '/artigos/' . esc($slug) . '.html" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="' . esc($title) . '" />
    <meta property="og:description" content="' . esc($excerpt) . '" />
    <meta property="og:url" content="' . DOMAIN . '/artigos/' . esc($slug) . '.html" />
    <link rel="stylesheet" href="../styles.css" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="../index.html"><span class="brand-mark">VV</span><span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span></a>
      <nav aria-label="Navegacao principal"><a href="../index.html#artigos">Artigos</a><a href="../autor.html">Autor</a><a href="../sobre.html">Sobre</a><a href="../contato.html">Contato</a><a href="../faq.html">FAQ</a></nav>
    </header>
    <main>
      <article class="article-page">
        <header class="article-hero">
          <div>
            <p class="category">' . esc($category) . '</p>
            <h1>' . esc($title) . '</h1>
            <p class="article-excerpt">' . esc($excerpt) . '</p>
            <p class="article-meta">Por ' . esc($author) . '</p>
            ' . listen_controls() . '
          </div>
          ' . $imageHtml . '
        </header>
        <div class="article-content">' . (string) $article['body_html'] . '</div>
      </article>
    </main>
    <footer class="site-footer">
      <p><strong>Verbo Vivo</strong> publica reflexoes cristas para fortalecer a fe na vida cotidiana.</p>
      <div><a href="../autor.html">Autor</a><a href="../sobre.html">Sobre</a><a href="../contato.html">Contato</a><a href="../faq.html">FAQ</a><a href="https://instagram.com/tec.agora" target="_blank" rel="noopener">By @tec.agora</a></div>
    </footer>
    ' . listen_script() . '
  </body>
</html>';
}

function article_card(array $article): string {
    $image = trim((string) $article['image_filename']) ?: 'o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png';
    return '
      <article class="article-card">
        <a href="artigos/' . esc((string) $article['slug']) . '.html">
          <img src="images/articles/' . esc($image) . '" alt="' . esc((string) $article['title']) . '" />
        </a>
        <div class="article-body">
          <p class="category">' . esc((string) $article['category']) . '</p>
          <h3><a href="artigos/' . esc((string) $article['slug']) . '.html">' . esc((string) $article['title']) . '</a></h3>
          <p>' . esc((string) $article['excerpt']) . '</p>
        </div>
      </article>
';
}

function featured_article(array $article): string {
    return str_replace('article-card', 'featured', article_card($article));
}

function remove_article_from_indexes(string $slug): void {
    $urlPart = 'artigos/' . $slug . '.html';
    $index = __DIR__ . '/index.html';
    if (is_file($index)) {
        $html = (string) file_get_contents($index);
        $html = (string) preg_replace('/\s*<article class="(?:featured|article-card)">(?:(?!<article class=).)*?' . preg_quote($urlPart, '/') . '.*?<\/article>/s', '', $html);
        file_put_contents($index, $html);
    }
    foreach (['feed.xml', 'sitemap.xml'] as $file) {
        $path = __DIR__ . '/' . $file;
        if (!is_file($path)) {
            continue;
        }
        $content = (string) file_get_contents($path);
        $content = (string) preg_replace('/\s*<item>.*?' . preg_quote(DOMAIN . '/' . $urlPart, '/') . '.*?<\/item>/s', '', $content);
        $content = (string) preg_replace('/\s*<url><loc>' . preg_quote(DOMAIN . '/' . $urlPart, '/') . '<\/loc><\/url>/s', '', $content);
        file_put_contents($path, $content);
    }
}

function update_indexes(array $article, ?string $oldSlug = null): void {
    if ($oldSlug && $oldSlug !== $article['slug']) {
        remove_article_from_indexes($oldSlug);
    }
    $index = __DIR__ . '/index.html';
    if (is_file($index)) {
        $html = (string) file_get_contents($index);
        $urlPart = 'artigos/' . (string) $article['slug'] . '.html';
        $replacement = text_contains($html, '<article class="featured">') && text_contains((string) preg_replace('/^.*(<article class="featured">.*?<\/article>).*/s', '$1', $html), $urlPart)
            ? featured_article($article)
            : article_card($article);
        if (text_contains($html, $urlPart)) {
            $html = (string) preg_replace('/\s*<article class="(?:featured|article-card)">(?:(?!<article class=).)*?' . preg_quote($urlPart, '/') . '.*?<\/article>/s', "\n" . $replacement, $html, 1);
        } else {
            $marker = '<section class="article-grid" aria-label="Lista de artigos">';
            $html = str_replace($marker, $marker . "\n        " . article_card($article), $html);
        }
        file_put_contents($index, $html);
    }
    update_feed($article);
    update_sitemap($article);
}

function update_feed(array $article): void {
    $path = __DIR__ . '/feed.xml';
    if (!is_file($path)) {
        return;
    }
    $xml = (string) file_get_contents($path);
    $url = DOMAIN . '/artigos/' . (string) $article['slug'] . '.html';
    $item = '<item><title>' . esc((string) $article['title']) . '</title><link>' . $url . '</link><guid>' . $url . '</guid><description>' . esc((string) $article['excerpt']) . '</description><pubDate>' . gmdate(DATE_RSS) . '</pubDate></item>';
    if (text_contains($xml, $url)) {
        $xml = (string) preg_replace('/<item>.*?' . preg_quote($url, '/') . '.*?<\/item>/s', $item, $xml, 1);
    } else {
        $xml = str_replace('    <item>', "    $item\n    <item>", $xml);
    }
    file_put_contents($path, $xml);
}

function update_sitemap(array $article): void {
    $path = __DIR__ . '/sitemap.xml';
    if (!is_file($path)) {
        return;
    }
    $xml = (string) file_get_contents($path);
    $url = DOMAIN . '/artigos/' . (string) $article['slug'] . '.html';
    if (!text_contains($xml, $url)) {
        $xml = str_replace('</urlset>', '  <url><loc>' . $url . '</loc></url>' . "\n</urlset>", $xml);
        file_put_contents($path, $xml);
    }
}

function page(string $title, string $body): void {
    echo '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>' . esc($title) . ' | Verbo Vivo</title><link rel="stylesheet" href="styles.css" /><style>.manager{padding:clamp(28px,5vw,70px) clamp(18px,4vw,64px)}.manager-wrap{margin:0 auto;max-width:1100px}.manager-panel{background:var(--white);border:1px solid var(--line);box-shadow:var(--shadow);padding:clamp(18px,3vw,30px);margin-top:22px}.manager-list{display:grid;gap:12px}.manager-item{border-bottom:1px solid var(--line);display:flex;gap:14px;justify-content:space-between;padding:14px 0}.manager-actions{display:flex;flex-wrap:wrap;gap:10px}.manager-form label{display:grid;font-weight:800;gap:7px;margin-top:15px}.manager-form input,.manager-form textarea{border:1px solid var(--line);color:var(--ink);font:inherit;padding:12px 13px;width:100%}.manager-form textarea{font-family:Georgia,serif;line-height:1.65;min-height:460px}.danger{background:#8f2d2d}.primary{background:var(--sage)}.secondary{background:var(--gold)}.manager button,.button-link{border:0;color:var(--white);cursor:pointer;display:inline-block;font-weight:800;padding:11px 15px;text-decoration:none}</style></head><body><header class="site-header"><a class="brand" href="index.html"><span class="brand-mark">VV</span><span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span></a><nav aria-label="Navegacao principal"><a href="index.html#artigos">Artigos</a><a href="autor.html">Autor</a><a href="sobre.html">Sobre</a><a href="contato.html">Contato</a></nav></header><main class="manager"><div class="manager-wrap">' . $body . '</div></main></body></html>';
}

$token = require_admin();
$action = $_POST['action'] ?? $_GET['action'] ?? 'list';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'save') {
    $oldSlug = (string) ($_POST['old_slug'] ?? '');
    $title = trim((string) ($_POST['title'] ?? ''));
    $slug = slugify((string) ($_POST['slug'] ?? $title));
    $article = [
        'slug' => $slug,
        'title' => $title ?: 'Nova reflexao',
        'category' => trim((string) ($_POST['category'] ?? 'Reflexao')),
        'excerpt' => trim((string) ($_POST['excerpt'] ?? '')),
        'author' => trim((string) ($_POST['author'] ?? '')),
        'image_filename' => trim((string) ($_POST['image_filename'] ?? '')),
        'body_html' => (string) ($_POST['body_html'] ?? ''),
    ];
    if (!is_dir(ARTICLE_DIR)) {
        mkdir(ARTICLE_DIR, 0755, true);
    }
    if ($oldSlug !== '' && $oldSlug !== $slug && is_file(article_path($oldSlug))) {
        @unlink(article_path($oldSlug));
    }
    file_put_contents(article_path($slug), render_article_page($article));
    update_indexes($article, $oldSlug ?: null);
    header('Location: gestor-artigos.php?token=' . rawurlencode($token) . '&saved=' . rawurlencode($slug));
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'delete') {
    $slug = (string) ($_POST['slug'] ?? '');
    @unlink(article_path($slug));
    remove_article_from_indexes($slug);
    header('Location: gestor-artigos.php?token=' . rawurlencode($token) . '&deleted=1');
    exit;
}

if ($action === 'edit') {
    $slug = (string) ($_GET['slug'] ?? '');
    $article = load_article($slug);
    page('Editar artigo', '<p class="eyebrow">Editor escondido</p><h1>Editar artigo</h1><form class="manager-panel manager-form" method="post"><input type="hidden" name="token" value="' . esc($token) . '" /><input type="hidden" name="action" value="save" /><input type="hidden" name="old_slug" value="' . esc($slug) . '" /><label>Titulo<input name="title" value="' . esc((string) $article['title']) . '" required /></label><label>Slug<input name="slug" value="' . esc((string) $article['slug']) . '" required /></label><label>Categoria<input name="category" value="' . esc((string) $article['category']) . '" /></label><label>Resumo<input name="excerpt" value="' . esc((string) $article['excerpt']) . '" /></label><label>Autor<input name="author" value="' . esc((string) $article['author']) . '" /></label><label>Arquivo da imagem<input name="image_filename" value="' . esc((string) $article['image_filename']) . '" /></label><label>Corpo do artigo em HTML<textarea name="body_html" required>' . esc((string) $article['body_html']) . '</textarea></label><div class="manager-actions" style="margin-top:18px"><button class="primary" type="submit">Salvar alteracoes</button><a class="button-link secondary" href="gestor-artigos.php?token=' . esc(rawurlencode($token)) . '">Voltar</a></div></form>');
    exit;
}

$items = list_articles();
$rows = '';
foreach ($items as $item) {
    $rows .= '<div class="manager-item"><div><strong>' . esc((string) $item['title']) . '</strong><p class="review-meta">Por ' . esc((string) $item['author']) . '</p></div><div class="manager-actions"><a class="button-link secondary" href="gestor-artigos.php?token=' . esc(rawurlencode($token)) . '&action=edit&slug=' . esc(rawurlencode((string) $item['slug'])) . '">Editar</a><form method="post" onsubmit="return confirm(\'Excluir este artigo publicado?\')"><input type="hidden" name="token" value="' . esc($token) . '" /><input type="hidden" name="action" value="delete" /><input type="hidden" name="slug" value="' . esc((string) $item['slug']) . '" /><button class="danger" type="submit">Excluir</button></form></div></div>';
}
page('Gestor de artigos', '<p class="eyebrow">Editor escondido</p><h1>Gestor de artigos publicados</h1><p class="article-excerpt">Use esta pagina apenas pelo link secreto. Ela permite editar ou excluir artigos publicados.</p><section class="manager-panel manager-list">' . ($rows ?: '<p>Nenhum artigo encontrado.</p>') . '</section>');
