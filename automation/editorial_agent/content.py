from __future__ import annotations

import re
import secrets
import unicodedata
from html import escape

from .models import ArticleDraft


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or secrets.token_hex(4)


def paragraphs_from_text(text: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if len(blocks) == 1:
        blocks = [line.strip() for line in text.splitlines() if line.strip()]
    return blocks


def fallback_refine(source_text: str, subject: str, sender: str) -> ArticleDraft:
    """Deterministic fallback until the LLM/image step is connected."""
    blocks = paragraphs_from_text(source_text)
    title = subject.strip() or "Nova reflexão"
    selected = blocks[:8]
    body = ["<h2>Reflexão</h2>"]
    for paragraph in selected:
        body.append(f"<p>{escape(paragraph)}</p>")
    body.append("<h2>Para meditar</h2>")
    body.append("<p>Que esta palavra seja lida com calma, oração e abertura diante de Deus.</p>")
    slug = slugify(title)
    return ArticleDraft(
        id=secrets.token_hex(8),
        token=secrets.token_urlsafe(24),
        sender=sender,
        source_subject=subject,
        source_text=source_text,
        title=title,
        slug=slug,
        excerpt="Uma reflexão cristã preparada para leitura, meditação e fortalecimento da fé.",
        category="Reflexão",
        author="Pastor Antonio Lemos Filho",
        body_html="\n".join(body),
        image_prompt=f"Imagem editorial cristã, reverente e simbólica para o tema: {title}",
        image_filename=f"{slug}.png",
    )


def render_article_page(draft: ArticleDraft) -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(draft.title)} | Verbo Vivo</title>
    <meta name="description" content="{escape(draft.excerpt)}" />
    <link rel="stylesheet" href="../styles.css" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="../index.html">
        <span class="brand-mark">VV</span>
        <span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span>
      </a>
      <nav aria-label="Navegação principal">
        <a href="../index.html#artigos">Artigos</a>
        <a href="../sobre.html">Sobre</a>
        <a href="../contato.html">Contato</a>
        <a href="../faq.html">FAQ</a>
      </nav>
    </header>
    <main>
      <article class="article-page">
        <header class="plain-hero">
          <p class="category">{escape(draft.category)}</p>
          <h1>{escape(draft.title)}</h1>
          <p class="article-excerpt">{escape(draft.excerpt)}</p>
          <p class="article-meta">Por {escape(draft.author)}</p>
        </header>
        <div class="article-content">
          {draft.body_html}
        </div>
      </article>
    </main>
  </body>
</html>
"""

