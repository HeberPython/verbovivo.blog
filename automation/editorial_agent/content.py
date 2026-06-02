from __future__ import annotations

import re
import secrets
import unicodedata
from html import escape
from urllib.parse import urlparse

from .models import ArticleDraft


DEFAULT_AUTHOR = "Pastor Antônio Lemos"
DEFAULT_AUTHOR_SOCIALS = {
    "instagram": "https://www.instagram.com/antoniolemosoficial/",
    "youtube": "https://www.youtube.com/@Lemos3",
    "facebook": "https://www.facebook.com/PastorAntonioLemos",
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or secrets.token_hex(4)


def paragraphs_from_text(text: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if len(blocks) == 1:
        blocks = [line.strip() for line in text.splitlines() if line.strip()]
    return blocks


def normalize_direct_submission_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    kept_lines: list[str] = []
    stop_headings = {
        "fontes",
        "fontes e dicionarios de referencia",
        "referencias",
        "referencias bibliograficas",
        "bibliografia",
    }
    discard_patterns = (
        r"^\[image:\s*.*?\]$",
        r"^!\[.*?\]\(.*?\)$",
        r"^texto(?:\s+mais\s+imagem)?\s+do\s+artigo\s+come[cç]a\s+aqui\.{0,3}$",
        r"^[-_]{3,}$",
        r"^(?:enviado|sent)\s+(?:do|from)\s+meu\b",
        r"^(?:de|from|para|to|assunto|subject|data|date):\s",
    )
    for line in text.splitlines():
        clean = line.strip()
        heading = clean.strip("*# ").rstrip(":")
        heading_norm = unicodedata.normalize("NFKD", heading).encode("ascii", "ignore").decode("ascii").lower()
        if heading_norm in stop_headings:
            break
        if any(re.match(pattern, clean, re.IGNORECASE) for pattern in discard_patterns):
            continue
        kept_lines.append(line.rstrip())
    return "\n".join(kept_lines).strip()


def inline_direct_markup(text: str) -> str:
    text = re.sub(r"\$\\alpha\s+\\gamma\s+\\omega\s+\\nu\$", "agōn", text)
    text = re.sub(
        r"\b([1-3]?\s?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ]+)\s+(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?",
        lambda match: (
            f"{match.group(1)}, capítulo {match.group(2)}, versículos {match.group(3)} a {match.group(4)}"
            if match.group(4)
            else f"{match.group(1)}, capítulo {match.group(2)}, versículo {match.group(3)}"
        ),
        text,
    )
    value = escape(text.strip())
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*(.+?)\*", r"<em>\1</em>", value)
    return value


def direct_article_html(text: str, title: str) -> str:
    blocks = paragraphs_from_text(normalize_direct_submission_text(text))
    body: list[str] = []
    list_items: list[str] = []

    def flush_list() -> None:
        if list_items:
            body.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    normalized_title = slugify(title)
    for block in blocks:
        clean = re.sub(r"\s*\n\s*", " ", block.strip())
        if not clean:
            continue
        if clean.startswith("- "):
            list_items.append(inline_direct_markup(clean[2:]))
            continue
        flush_list()
        heading = clean.strip("*# ").strip()
        if slugify(heading) == normalized_title or slugify(heading).startswith(normalized_title + "-"):
            continue
        if re.match(r"^\*?\d+\.\s+.+?\*?$", clean):
            body.append(f"<h2>{inline_direct_markup(heading)}</h2>")
        elif clean.startswith("#"):
            body.append(f"<h2>{inline_direct_markup(heading)}</h2>")
        elif clean.startswith("*") and clean.endswith("*") and len(clean) < 100:
            body.append(f"<h2>{inline_direct_markup(heading)}</h2>")
        elif clean.startswith(("“", '"')) and ("—" in clean or re.search(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ]+\s+\d+:\d+", clean)):
            body.append(f"<blockquote>{inline_direct_markup(clean)}</blockquote>")
        else:
            body.append(f"<p>{inline_direct_markup(clean)}</p>")
    flush_list()
    return "\n".join(body)


def normalize_social_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("@"):
        return value
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.geturl() if parsed.netloc else value


def extract_submission_metadata(source_text: str) -> tuple[dict, str]:
    metadata = {"author": "", "guest_author": False, "socials": {}}
    body_lines: list[str] = []
    in_header = True
    for line in source_text.splitlines():
        clean = line.strip()
        if in_header and not clean:
            in_header = False
            body_lines.append(line)
            continue
        if in_header and ":" in clean:
            key, value = clean.split(":", 1)
            key_norm = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode("ascii").lower().strip()
            value = value.strip()
            if key_norm in {"autor convidado", "author guest", "guest author"}:
                metadata["author"] = value
                metadata["guest_author"] = bool(value)
                continue
            if key_norm in {"autor", "author", "nome", "nome do autor"}:
                continue
            if key_norm in {"instagram", "facebook", "youtube", "x", "twitter", "linkedin", "site", "website"}:
                if value:
                    metadata["socials"][key_norm] = normalize_social_url(value)
                continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip() or source_text.strip()
    return metadata, body


def submission_author(metadata: dict) -> str:
    return metadata["author"] if metadata.get("guest_author") else DEFAULT_AUTHOR


def submission_socials(metadata: dict) -> dict[str, str]:
    if metadata.get("guest_author"):
        return metadata["socials"]
    return DEFAULT_AUTHOR_SOCIALS.copy()


def social_label(name: str) -> str:
    return {
        "instagram": "Instagram",
        "facebook": "Facebook",
        "youtube": "YouTube",
        "x": "X",
        "twitter": "X",
        "linkedin": "LinkedIn",
        "site": "Site",
        "website": "Site",
    }.get(name.lower(), name.title())


def social_icon(name: str) -> str:
    icons = {
        "instagram": '<svg class="social-icon social-icon--instagram" aria-hidden="true" viewBox="0 0 24 24"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4c0 3.2-2.6 5.8-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8C2 4.6 4.6 2 7.8 2Zm-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8c1.99 0 3.6-1.61 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6Zm9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"/></svg>',
        "facebook": '<svg class="social-icon social-icon--facebook" aria-hidden="true" viewBox="0 0 24 24"><path d="M13.45 23.69v-7.98h3.25l.67-3.67h-3.92v-1.3c0-1.94.76-2.68 2.73-2.68.61 0 1.1.02 1.39.05V4.79c-.54-.15-1.85-.3-2.61-.3-4.01 0-5.86 1.89-5.86 5.98v1.58H6.63v3.67H9.1v7.98h4.35Z"/></svg>',
        "youtube": '<svg class="social-icon social-icon--youtube" aria-hidden="true" viewBox="0 0 24 24"><path d="M23.5 6.19a3.02 3.02 0 0 0-2.12-2.14C19.5 3.55 12 3.55 12 3.55s-7.5 0-9.38.5A3.02 3.02 0 0 0 .5 6.19C0 8.08 0 12 0 12s0 3.92.5 5.81a3.02 3.02 0 0 0 2.12 2.14c1.88.5 9.38.5 9.38.5s7.5 0 9.38-.5a3.02 3.02 0 0 0 2.12-2.14C24 15.92 24 12 24 12s0-3.92-.5-5.81ZM9.55 15.57V8.43L15.82 12l-6.27 3.57Z"/></svg>',
        "x": '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        "twitter": '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        "linkedin": '<svg class="social-icon social-icon--linkedin" aria-hidden="true" viewBox="0 0 24 24"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13Zm1.78 13.02H3.56V9h3.56v11.45ZM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0Z"/></svg>',
        "site": '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
        "website": '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
    }
    return icons.get(name.lower(), icons["site"])


def author_socials_html(socials: dict[str, str]) -> str:
    links = []
    for name, url in socials.items():
        if not url:
            continue
        href = url
        display = url
        if url.startswith("@"):
            handle = url.lstrip("@")
            if name == "instagram":
                href = f"https://instagram.com/{handle}"
            elif name in {"x", "twitter"}:
                href = f"https://x.com/{handle}"
            display = url
        label = f"{social_label(name)} {display}".strip()
        links.append(
            f'<a href="{escape(href)}" target="_blank" rel="noopener" '
            f'aria-label="{escape(label)}" title="{escape(label)}">{social_icon(name)}</a>'
        )
    if not links:
        return ""
    return '<div class="author-socials" aria-label="Redes sociais do autor">' + "".join(links) + "</div>"


def listen_controls() -> str:
    return """
            <div class="listen-tools" aria-label="Narração do artigo">
              <button class="listen-button" type="button" data-listen-toggle aria-label="Ouvir artigo" title="Ouvir artigo">
                <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22">
                  <path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"></path>
                  <path d="M16 9.5c1.1 1.4 1.1 3.6 0 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                  <path d="M18.8 7c2.3 2.8 2.3 7.2 0 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                </svg>
              </button>
              <span data-listen-status>Clique para ouvir o artigo.</span>
            </div>
"""


def listen_script() -> str:
    return """
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
          /\\b([1-3]?\\s?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç]+)\\s+(\\d{1,3}):(\\d{1,3})(?:-(\\d{1,3}))?/g,
          (_, book, chapter, verse, endVerse) => {
            const cleanBook = book.replace(/\\s+/g, " ").trim();
            return endVerse
              ? `${cleanBook}, capítulo ${chapter}, versículos ${verse} a ${endVerse}`
              : `${cleanBook}, capítulo ${chapter}, versículo ${verse}`;
          }
        );
        const articleText = () => expandBibleReferences(article.innerText).replace(/\\s+/g, " ").trim();
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
    </script>
"""


def analytics_head() -> str:
    return """
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KRH6PSKSMV"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-KRH6PSKSMV');
    </script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5233928852442075" crossorigin="anonymous"></script>
"""


def analytics_script(endpoint: str = "analytics.php") -> str:
    return f"""
    <script>
      (() => {{
        const endpoint = "{endpoint}";
        const now = Date.now();
        const sessionKey = "vv_session_id";
        const pageKey = "vv_page_id";
        let sessionId = sessionStorage.getItem(sessionKey);
        if (!sessionId) {{
          sessionId = crypto.randomUUID ? crypto.randomUUID() : `${{now}}-${{Math.random().toString(36).slice(2)}}`;
          sessionStorage.setItem(sessionKey, sessionId);
        }}
        const pageId = crypto.randomUUID ? crypto.randomUUID() : `${{now}}-${{Math.random().toString(36).slice(2)}}`;
        sessionStorage.setItem(pageKey, pageId);
        const payload = (eventName) => ({{
          event: eventName,
          session_id: sessionId,
          page_id: pageId,
          path: location.pathname,
          title: document.title,
          referrer: document.referrer || "",
          elapsed_seconds: Math.max(0, Math.round((Date.now() - now) / 1000)),
          language: navigator.language || "",
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
          screen: `${{screen.width}}x${{screen.height}}`,
          viewport: `${{innerWidth}}x${{innerHeight}}`
        }});
        const send = (eventName) => {{
          const body = JSON.stringify(payload(eventName));
          if (navigator.sendBeacon) {{
            navigator.sendBeacon(endpoint, new Blob([body], {{ type: "application/json" }}));
            return;
          }}
          fetch(endpoint, {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body, keepalive: true }}).catch(() => {{}});
        }};
        send("pageview");
        const timer = setInterval(() => send("heartbeat"), 15000);
        window.addEventListener("pagehide", () => {{
          clearInterval(timer);
          send("pagehide");
        }});
      }})();
    </script>
"""


def fallback_refine(source_text: str, subject: str, sender: str) -> ArticleDraft:
    metadata, article_text = extract_submission_metadata(source_text)
    blocks = paragraphs_from_text(article_text)
    title = subject.strip() or "Nova reflexão"
    selected = blocks[:8]
    body = ["<h2>Reflexão</h2>"]
    for paragraph in selected:
        body.append(f"<p>{escape(paragraph)}</p>")
    body.append("<h2>Para meditar</h2>")
    body.append("<p>Que esta palavra seja lida com calma, oração e abertura diante de Deus.</p>")
    slug = slugify(title)
    draft_id = secrets.token_hex(8)
    return ArticleDraft(
        id=draft_id,
        token=secrets.token_urlsafe(24),
        sender=sender,
        source_subject=subject,
        source_text=article_text,
        title=title,
        slug=slug,
        excerpt="Uma reflexão cristã preparada para leitura, meditação e fortalecimento da fé.",
        category="Reflexão",
        author=submission_author(metadata),
        body_html="\n".join(body),
        image_prompt=f"Imagem editorial cristã, reverente e simbólica para o tema: {title}",
        image_filename=f"{slug}-{draft_id}.png",
        author_socials=submission_socials(metadata),
    )


def render_article_page(draft: ArticleDraft) -> str:
    image_html = ""
    if draft.image_filename:
        image_html = f'<img src="../images/articles/{escape(draft.image_filename)}" alt="{escape(draft.title)}" />'
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(draft.title)} | Verbo Vivo</title>
    <meta name="description" content="{escape(draft.excerpt)}" />
    <link rel="stylesheet" href="../styles.css" />
    {analytics_head()}
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="../index.html">
        <span class="brand-mark">VV</span>
        <span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span>
      </a>
      <nav aria-label="Navegação principal">
        <a href="../index.html#artigos">Artigos</a>
        <a href="../autor.html">Autor</a>
        <a href="../sobre.html">Sobre</a>
        <a href="../contato.html">Contato</a>
        <a href="../faq.html">FAQ</a>
      </nav>
    </header>
    <main>
      <article class="article-page">
        <header class="article-hero">
          <div>
            <p class="category">{escape(draft.category)}</p>
            <h1>{escape(draft.title)}</h1>
            <p class="article-excerpt">{escape(draft.excerpt)}</p>
            <p class="article-meta">Por {escape(draft.author)}</p>
            {author_socials_html(draft.author_socials)}
            {listen_controls()}
          </div>
          {image_html}
        </header>
        <div class="article-content">
          {draft.body_html}
        </div>
      </article>
    </main>
    <footer class="site-footer">
      <p><strong>Verbo Vivo</strong> publica reflexões cristãs para fortalecer a fé na vida cotidiana.</p>
      <div><a href="../autor.html">Autor</a><a href="../sobre.html">Sobre</a><a href="../contato.html">Contato</a><a href="../faq.html">FAQ</a><a href="https://instagram.com/tec.agora" target="_blank" rel="noopener">By @tec.agora</a></div>
    </footer>
    {listen_script()}
    {analytics_script("../analytics.php")}
  </body>
</html>
"""


def ready_article_from_email(subject: str, source_text: str, sender: str, image_filename: str = "", image_path: str = "") -> ArticleDraft:
    metadata, article_text = extract_submission_metadata(source_text)
    article_text = normalize_direct_submission_text(article_text)
    blocks = paragraphs_from_text(article_text)
    title = subject.strip() or (blocks[0][:80] if blocks else "Nova reflexão")
    slug = slugify(title)
    return ArticleDraft(
        id=secrets.token_hex(8),
        token=secrets.token_urlsafe(24),
        sender=sender,
        source_subject=subject,
        source_text=article_text,
        title=title,
        slug=slug,
        excerpt="Uma reflexão cristã para fortalecer a fé na vida cotidiana.",
        category="Reflexão",
        author=submission_author(metadata),
        body_html=direct_article_html(article_text, title),
        image_prompt="",
        image_filename=image_filename,
        author_socials=submission_socials(metadata),
        local_image_path=image_path,
        status="published_direct",
    )
