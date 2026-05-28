<?php
declare(strict_types=1);

const DOMAIN = 'https://verbovivo.blog';
const DRAFT_DIR = __DIR__ . '/_editorial_drafts';
const ARTICLE_DIR = __DIR__ . '/artigos';

function esc(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function social_label(string $name): string {
    return [
        'instagram' => 'Instagram',
        'facebook' => 'Facebook',
        'youtube' => 'YouTube',
        'x' => 'X',
        'twitter' => 'X',
        'linkedin' => 'LinkedIn',
        'site' => 'Site',
        'website' => 'Site',
    ][$name] ?? ucfirst($name);
}

function social_icon(string $name): string {
    $icons = [
        'instagram' => '<svg class="social-icon social-icon--instagram" aria-hidden="true" viewBox="0 0 24 24"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4c0 3.2-2.6 5.8-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8C2 4.6 4.6 2 7.8 2Zm-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8c1.99 0 3.6-1.61 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6Zm9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"/></svg>',
        'facebook' => '<svg class="social-icon social-icon--facebook" aria-hidden="true" viewBox="0 0 24 24"><path d="M13.45 23.69v-7.98h3.25l.67-3.67h-3.92v-1.3c0-1.94.76-2.68 2.73-2.68.61 0 1.1.02 1.39.05V4.79c-.54-.15-1.85-.3-2.61-.3-4.01 0-5.86 1.89-5.86 5.98v1.58H6.63v3.67H9.1v7.98h4.35Z"/></svg>',
        'youtube' => '<svg class="social-icon social-icon--youtube" aria-hidden="true" viewBox="0 0 24 24"><path d="M23.5 6.19a3.02 3.02 0 0 0-2.12-2.14C19.5 3.55 12 3.55 12 3.55s-7.5 0-9.38.5A3.02 3.02 0 0 0 .5 6.19C0 8.08 0 12 0 12s0 3.92.5 5.81a3.02 3.02 0 0 0 2.12 2.14c1.88.5 9.38.5 9.38.5s7.5 0 9.38-.5a3.02 3.02 0 0 0 2.12-2.14C24 15.92 24 12 24 12s0-3.92-.5-5.81ZM9.55 15.57V8.43L15.82 12l-6.27 3.57Z"/></svg>',
        'x' => '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        'twitter' => '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        'linkedin' => '<svg class="social-icon social-icon--linkedin" aria-hidden="true" viewBox="0 0 24 24"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13Zm1.78 13.02H3.56V9h3.56v11.45ZM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0Z"/></svg>',
        'site' => '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
        'website' => '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
    ];
    return $icons[$name] ?? $icons['site'];
}

function author_socials_html(array $socials): string {
    $links = [];
    foreach ($socials as $name => $url) {
        $href = (string) $url;
        $display = (string) $url;
        if (str_starts_with($href, '@')) {
            $handle = ltrim($href, '@');
            if ($name === 'instagram') {
                $href = 'https://instagram.com/' . $handle;
            } elseif ($name === 'x' || $name === 'twitter') {
                $href = 'https://x.com/' . $handle;
            }
        }
        $label = trim(social_label((string) $name) . ' ' . $display);
        $links[] = '<a href="' . esc($href) . '" target="_blank" rel="noopener" aria-label="' . esc($label) . '" title="' . esc($label) . '">' . social_icon((string) $name) . '</a>';
    }
    return $links ? '<div class="author-socials" aria-label="Redes sociais do autor">' . implode('', $links) . '</div>' : '';
}

function listen_controls(): string {
    return '
            <div class="listen-tools" aria-label="Narração do artigo">
              <button class="listen-button" type="button" data-listen-toggle aria-label="Ouvir artigo" title="Ouvir artigo">
                <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22">
                  <path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"></path>
                  <path d="M16 9.5c1.1 1.4 1.1 3.6 0 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                  <path d="M18.8 7c2.3 2.8 2.3 7.2 0 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                </svg>
              </button>
              <span data-listen-status>Clique para ouvir o artigo.</span>
            </div>';
}

function listen_script(): string {
    return '
    <script>
      (() => {
        const controls = document.querySelector(".listen-tools");
        const article = document.querySelector(".article-content");
        if (!controls || !article) return;
        const status = controls.querySelector("[data-listen-status]");
        const button = controls.querySelector("[data-listen-toggle]");
        const synthesis = window.speechSynthesis;
        let utterance = null;
        const setStatus = (message) => { if (status) status.textContent = message; };
        const setButton = (speaking) => {
          if (!button) return;
          button.classList.toggle("is-speaking", speaking);
          button.setAttribute("aria-label", speaking ? "Pausar narração" : "Ouvir artigo");
          button.setAttribute("title", speaking ? "Pausar narração" : "Ouvir artigo");
        };
        if (!("speechSynthesis" in window)) {
          if (button) button.disabled = true;
          setStatus("Narração indisponível neste navegador.");
          return;
        }
        const expandBibleReferences = (text) => text.replace(
          /\b([1-3]?\s?[A-Z???????????][A-Za-z??????????????????????]+)\s+(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?/g,
          (_, book, chapter, verse, endVerse) => {
            const cleanBook = book.replace(/\s+/g, " ").trim();
            return endVerse
              ? `${cleanBook}, capítulo ${chapter}, versículos ${verse} a ${endVerse}`
              : `${cleanBook}, capítulo ${chapter}, versículo ${verse}`;
          }
        );
        const articleText = () => expandBibleReferences(article.innerText).replace(/\s+/g, " ").trim();
        const stop = () => {
          synthesis.cancel();
          utterance = null;
          setButton(false);
          setStatus("Narração parada.");
        };
        controls.addEventListener("click", (event) => {
          if (!event.target.closest("[data-listen-toggle]")) return;
          if (synthesis.speaking && !synthesis.paused) {
            synthesis.pause();
            setButton(false);
            setStatus("Narração pausada.");
            return;
          }
          if (synthesis.paused) {
            synthesis.resume();
            setButton(true);
            setStatus("Narrando artigo.");
            return;
          }
          stop();
          utterance = new SpeechSynthesisUtterance(articleText());
          utterance.lang = "pt-BR";
          utterance.rate = 0.95;
          utterance.onend = () => { setButton(false); setStatus("Narração concluída."); };
          utterance.onerror = () => { setButton(false); setStatus("Não foi possível narrar este artigo."); };
          synthesis.speak(utterance);
          setButton(true);
          setStatus("Narrando artigo.");
        });
        window.addEventListener("beforeunload", () => synthesis.cancel());
      })();
    </script>';
}

function token_from_request(): string {
    $token = $_POST['token'] ?? $_GET['token'] ?? '';
    if (!is_string($token) || !preg_match('/^[A-Za-z0-9_-]{20,}$/', $token)) {
        http_response_code(400);
        exit('Token invalido.');
    }
    return $token;
}

function draft_path(string $token): string {
    return DRAFT_DIR . '/' . $token . '.json';
}

function load_draft(string $token): array {
    $path = draft_path($token);
    if (!is_file($path)) {
        http_response_code(404);
        exit('Rascunho nao encontrado.');
    }
    $data = json_decode((string) file_get_contents($path), true);
    if (!is_array($data)) {
        http_response_code(500);
        exit('Rascunho invalido.');
    }
    return $data;
}

function save_draft(string $token, array $draft): void {
    if (!is_dir(DRAFT_DIR)) {
        mkdir(DRAFT_DIR, 0755, true);
    }
    file_put_contents(
        draft_path($token),
        json_encode($draft, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
    );
}

function page(string $title, string $body): void {
    echo '<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>' . esc($title) . ' | Verbo Vivo</title>
    <link rel="stylesheet" href="styles.css" />
    <style>
      .review-shell { padding: clamp(28px, 5vw, 70px) clamp(18px, 4vw, 64px) clamp(48px, 7vw, 96px); }
      .review-wrap { margin: 0 auto; max-width: 980px; }
      .review-actions { display: flex; flex-wrap: wrap; gap: 12px; margin: 24px 0 34px; }
      .review-actions button { border: 0; color: var(--white); cursor: pointer; font-weight: 800; padding: 13px 18px; }
      .approve { background: var(--sage); }
      .correct { background: var(--gold); }
      .review-preview, .review-form { background: var(--white); border: 1px solid var(--line); box-shadow: var(--shadow); padding: clamp(18px, 3vw, 30px); }
      .review-form { margin-top: 24px; }
      .review-form label { display: grid; font-weight: 800; gap: 7px; margin-top: 15px; }
      .review-form input, .review-form textarea { border: 1px solid var(--line); color: var(--ink); font: inherit; padding: 12px 13px; width: 100%; }
      .review-form textarea { min-height: 420px; resize: vertical; font-family: Georgia, "Times New Roman", serif; line-height: 1.65; }
      .review-meta { color: var(--muted); line-height: 1.6; }
    </style>
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="index.html"><span class="brand-mark">VV</span><span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span></a>
      <nav aria-label="Navegação principal"><a href="index.html#artigos">Artigos</a><a href="sobre.html">Sobre</a><a href="contato.html">Contato</a><a href="faq.html">FAQ</a></nav>
    </header>
    <main class="review-shell"><div class="review-wrap">' . $body . '</div></main>
  </body>
</html>';
}

function render_article_page(array $draft): string {
    $title = (string) ($draft['title'] ?? 'Nova reflexão');
    $excerpt = (string) ($draft['excerpt'] ?? 'Uma reflexão cristã para fortalecer a fé na vida cotidiana.');
    $category = (string) ($draft['category'] ?? 'Reflexão');
    $author = (string) ($draft['author'] ?? 'Pastor Antonio Lemos Filho');
    $slug = (string) ($draft['slug'] ?? 'nova-reflexao');
    $image = (string) ($draft['image_filename'] ?? '');
    $imageHtml = $image !== '' ? '<img src="../images/articles/' . esc($image) . '" alt="' . esc($title) . '" />' : '';
    $bodyHtml = (string) ($draft['body_html'] ?? '');

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
      <nav aria-label="Navegação principal"><a href="../index.html#artigos">Artigos</a><a href="../autor.html">Autor</a><a href="../sobre.html">Sobre</a><a href="../contato.html">Contato</a><a href="../faq.html">FAQ</a></nav>
    </header>
    <main>
      <article class="article-page">
        <header class="article-hero">
          <div>
            <p class="category">' . esc($category) . '</p>
            <h1>' . esc($title) . '</h1>
            <p class="article-excerpt">' . esc($excerpt) . '</p>
            <p class="article-meta">Por ' . esc($author) . '</p>
            ' . author_socials_html($draft['author_socials'] ?? []) . '
            ' . listen_controls() . '
          </div>
          ' . $imageHtml . '
        </header>
        <div class="article-content">' . $bodyHtml . '</div>
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

function article_card(array $draft): string {
    $title = (string) ($draft['title'] ?? 'Nova reflexão');
    $slug = (string) ($draft['slug'] ?? 'nova-reflexao');
    $excerpt = (string) ($draft['excerpt'] ?? 'Uma reflexão cristã para fortalecer a fé na vida cotidiana.');
    $category = (string) ($draft['category'] ?? 'Reflexão');
    $image = (string) ($draft['image_filename'] ?? 'o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png');

    return '
      <article class="article-card">
        <a href="artigos/' . esc($slug) . '.html">
          <img src="images/articles/' . esc($image) . '" alt="' . esc($title) . '" />
        </a>
        <div class="article-body">
          <p class="category">' . esc($category) . '</p>
          <h3><a href="artigos/' . esc($slug) . '.html">' . esc($title) . '</a></h3>
          <p>' . esc($excerpt) . '</p>
        </div>
      </article>
';
}

function featured_article(array $draft): string {
    $title = (string) ($draft['title'] ?? 'Nova reflexão');
    $slug = (string) ($draft['slug'] ?? 'nova-reflexao');
    $excerpt = (string) ($draft['excerpt'] ?? 'Uma reflexão cristã para fortalecer a fé na vida cotidiana.');
    $category = (string) ($draft['category'] ?? 'Reflexão');
    $image = (string) ($draft['image_filename'] ?? 'o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png');

    return '
      <article class="featured">
        <a href="artigos/' . esc($slug) . '.html">
          <img src="images/articles/' . esc($image) . '" alt="' . esc($title) . '" />
        </a>
        <div class="article-body">
          <p class="category">' . esc($category) . '</p>
          <h3><a href="artigos/' . esc($slug) . '.html">' . esc($title) . '</a></h3>
          <p>' . esc($excerpt) . '</p>
        </div>
      </article>
';
}

function update_index(array $draft): void {
    $path = __DIR__ . '/index.html';
    $html = (string) file_get_contents($path);
    $needle = 'artigos/' . (string) $draft['slug'] . '.html';
    $wasListed = str_contains($html, $needle);
    $html = (string) preg_replace('/\s*<article class="featured">.*?<\/article>/s', "\n" . featured_article($draft), $html, 1);
    if (!$wasListed) {
    $marker = '<section class="article-grid" aria-label="Lista de artigos">';
    $html = str_replace($marker, $marker . "\n        " . article_card($draft), $html);
    }
    file_put_contents($path, $html);
}

function update_feed(array $draft): void {
    $path = __DIR__ . '/feed.xml';
    $xml = (string) file_get_contents($path);
    $url = DOMAIN . '/artigos/' . (string) $draft['slug'] . '.html';
    if (str_contains($xml, $url)) {
        return;
    }
    $item = '
    <item>
      <title>' . esc((string) $draft['title']) . '</title>
      <link>' . $url . '</link>
      <guid>' . $url . '</guid>
      <description>' . esc((string) $draft['excerpt']) . '</description>
      <pubDate>' . gmdate(DATE_RSS) . '</pubDate>
    </item>';
    $xml = str_replace('    <item>', $item . "\n    <item>", $xml);
    file_put_contents($path, $xml);
}

function update_sitemap(array $draft): void {
    $path = __DIR__ . '/sitemap.xml';
    $xml = (string) file_get_contents($path);
    $url = DOMAIN . '/artigos/' . (string) $draft['slug'] . '.html';
    if (str_contains($xml, $url)) {
        return;
    }
    $xml = str_replace('</urlset>', '  <url><loc>' . $url . '</loc></url>' . "\n</urlset>", $xml);
    file_put_contents($path, $xml);
}

function publish_draft(array $draft): void {
    if (!is_dir(ARTICLE_DIR)) {
        mkdir(ARTICLE_DIR, 0755, true);
    }
    file_put_contents(ARTICLE_DIR . '/' . (string) $draft['slug'] . '.html', render_article_page($draft));
    update_index($draft);
    update_feed($draft);
    update_sitemap($draft);
}

$token = token_from_request();
$draft = load_draft($token);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $draft['title'] = trim((string) ($_POST['title'] ?? $draft['title']));
    $draft['excerpt'] = trim((string) ($_POST['excerpt'] ?? $draft['excerpt']));
    $draft['category'] = trim((string) ($_POST['category'] ?? $draft['category']));
    $draft['body_html'] = (string) ($_POST['body_html'] ?? $draft['body_html']);
    $draft['status'] = (string) ($_POST['action'] ?? 'approved');
    $draft['published_at'] = gmdate(DATE_ATOM);
    save_draft($token, $draft);
    publish_draft($draft);
    page('Artigo publicado', '<p class="eyebrow">Publicado</p><h1>Artigo publicado com sucesso.</h1><p class="article-excerpt">A publicação já foi enviada para o site e incluída na página inicial, no RSS e no sitemap.</p><p><a href="artigos/' . esc((string) $draft['slug']) . '.html">Abrir artigo publicado</a></p>');
    exit;
}

$image = (string) ($draft['image_filename'] ?? '');
$imageHtml = $image !== '' ? '<img src="images/articles/' . esc($image) . '" alt="' . esc((string) $draft['title']) . '" style="margin:20px 0;border:1px solid var(--line);" />' : '';

page(
    'Revisão editorial',
    '<p class="eyebrow">Revisão editorial</p>
    <h1>' . esc((string) $draft['title']) . '</h1>
    <p class="review-meta"><strong>Autor:</strong> ' . esc((string) $draft['author']) . '<br><strong>Categoria:</strong> ' . esc((string) $draft['category']) . '<br><strong>Resumo:</strong> ' . esc((string) $draft['excerpt']) . '</p>
    ' . author_socials_html($draft['author_socials'] ?? []) . '
    ' . $imageHtml . '
    <div class="review-preview article-content">' . (string) $draft['body_html'] . '</div>
    <form class="review-actions" id="aprovar" method="post">
      <input type="hidden" name="token" value="' . esc($token) . '" />
      <input type="hidden" name="action" value="approved" />
      <button class="approve" type="submit">Aprovar e publicar</button>
    </form>
    <form class="review-form" id="corrigir" method="post">
      <input type="hidden" name="token" value="' . esc($token) . '" />
      <input type="hidden" name="action" value="corrected_approved" />
      <h2>Corrigir e publicar</h2>
      <label>Título<input name="title" value="' . esc((string) $draft['title']) . '" required /></label>
      <label>Categoria<input name="category" value="' . esc((string) $draft['category']) . '" required /></label>
      <label>Resumo<input name="excerpt" value="' . esc((string) $draft['excerpt']) . '" required /></label>
      <label>Artigo em HTML<textarea name="body_html" required>' . esc((string) $draft['body_html']) . '</textarea></label>
      <button class="correct" type="submit">Enviar correção e publicar</button>
    </form>'
);
