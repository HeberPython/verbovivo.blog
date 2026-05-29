from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automation.editorial_agent.content import render_article_page
from automation.editorial_agent.models import ArticleDraft


SITE = ROOT / "site"
DRAFTS = ROOT / "_drafts"
DOMAIN = "https://verbovivo.blog"
DEFAULT_IMAGE = "o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png"
ARTICLE_WIDTH = 1536
ARTICLE_HEIGHT = 1024

CURRENT_HOME_DRAFTS = [
    "dcf1e0e616343e53",
    "3e90550016267f2e",
    "0488ba0c44598305",
]

STATIC_PAGES = [
    "autor.html",
    "sobre.html",
    "contato.html",
    "faq.html",
    "politica-de-privacidade.html",
]


def load_draft(draft_id: str) -> ArticleDraft:
    data = json.loads((DRAFTS / f"{draft_id}.json").read_text(encoding="utf-8"))
    return ArticleDraft(**data)


def article_image(draft: ArticleDraft) -> str:
    return draft.image_filename or DEFAULT_IMAGE


def webp_name(filename: str) -> str:
    return re.sub(r"\.[^.]+$", ".webp", filename)


def article_picture(prefix: str, filename: str, alt: str, *, eager: bool) -> str:
    loading = 'fetchpriority="high" decoding="async"' if eager else 'loading="lazy" decoding="async"'
    return (
        "<picture>"
        f'<source srcset="{prefix}{escape(webp_name(filename))}" type="image/webp" />'
        f'<img src="{prefix}{escape(filename)}" alt="{escape(alt)}" '
        f'width="{ARTICLE_WIDTH}" height="{ARTICLE_HEIGHT}" {loading} />'
        "</picture>"
    )


def article_card(draft: ArticleDraft, featured: bool = False) -> str:
    css_class = "featured" if featured else "article-card"
    image = article_image(draft)
    return f"""      <article class="{css_class}">
        <a href="artigos/{escape(draft.slug)}.html">
          {article_picture("images/articles/", image, draft.title, eager=featured)}
        </a>
        <div class="article-body">
          <p class="category">{escape(draft.category)}</p>
          <h3><a href="artigos/{escape(draft.slug)}.html">{escape(draft.title)}</a></h3>
          <p>{escape(draft.excerpt)}</p>
        </div>
      </article>"""


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


def update_home(drafts: list[ArticleDraft]) -> None:
    index_path = SITE / "index.html"
    html = index_path.read_text(encoding="utf-8")
    featured = drafts[0]
    hero = f"""      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Palavra, fé e vida cristã</p>
          <h1>Reflexões cristãs para aquietar a alma e fortalecer a caminhada.</h1>
          <p>
            O Verbo Vivo reúne textos de fé, consolo e formação interior para quem
            procura uma leitura bíblica sensível, profunda e próxima da vida real.
          </p>
        </div>

{article_card(featured, featured=True)}

      </section>

"""
    html = replace_between(html, '      <section class="hero">', '      <section class="section-intro"', hero)

    cards = "\n\n".join(article_card(draft) for draft in drafts)
    grid = f"""      <section class="article-grid" aria-label="Lista de artigos">
{cards}
      </section>

"""
    html = replace_between(html, '      <section class="article-grid"', '      <section class="editorial"', grid)
    html = re.sub(
        r'<meta property="og:image" content="[^"]*" />',
        f'<meta property="og:image" content="{DOMAIN}/images/articles/{escape(article_image(featured))}" />',
        html,
        count=1,
    )
    index_path.write_text(html, encoding="utf-8")


def write_articles(drafts: list[ArticleDraft]) -> None:
    article_dir = SITE / "artigos"
    image_dir = SITE / "images" / "articles"
    article_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    for draft in drafts:
        (article_dir / f"{draft.slug}.html").write_text(render_article_page(draft), encoding="utf-8")
        if draft.local_image_path and draft.image_filename:
            source = ROOT / draft.local_image_path
            if source.exists():
                shutil.copy2(source, image_dir / draft.image_filename)


def write_sitemap(drafts: list[ArticleDraft]) -> None:
    urls = [f"{DOMAIN}/"]
    urls.extend(f"{DOMAIN}/artigos/{draft.slug}.html" for draft in drafts)
    urls.extend(f"{DOMAIN}/{page}" for page in STATIC_PAGES)
    body = "\n".join(f"  <url><loc>{url}</loc></url>" for url in urls)
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n',
        encoding="utf-8",
    )


def write_feed(drafts: list[ArticleDraft]) -> None:
    items = []
    for draft in drafts:
        created_at = datetime.fromisoformat(draft.created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        url = f"{DOMAIN}/artigos/{draft.slug}.html"
        items.append(
            f"""
    <item>
      <title>{escape(draft.title)}</title>
      <link>{url}</link>
      <guid>{url}</guid>
      <description>{escape(draft.excerpt)}</description>
      <pubDate>{format_datetime(created_at.astimezone(timezone.utc))}</pubDate>
    </item>"""
        )
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Verbo Vivo</title>
    <link>{DOMAIN}/</link>
    <description>Reflexões cristãs para fortalecer a fé e iluminar a caminhada.</description>
{''.join(items)}
  </channel>
</rss>
"""
    (SITE / "feed.xml").write_text(feed, encoding="utf-8")


def main() -> None:
    drafts = [load_draft(draft_id) for draft_id in CURRENT_HOME_DRAFTS]
    write_articles(drafts)
    update_home(drafts)
    write_sitemap(drafts)
    write_feed(drafts)
    print(f"Site atualizado em {SITE}")


if __name__ == "__main__":
    main()
