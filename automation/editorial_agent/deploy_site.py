from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from ftplib import FTP
from html import escape, unescape
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from .config import settings
from .content import article_navigation_html, render_article_page
from .lessons import rebuild_lesson_catalog
from .models import ArticleDraft
from .publisher import (
    DOMAIN,
    HOME_ARTICLE_LIMIT,
    article_card,
    article_grid_html,
    draft_pub_date,
    ensure_dir,
    featured_article,
    replace_article_grid,
    sitemap_entry,
)


SITE_DIR = Path("site")
ARTICLE_DIR = SITE_DIR / "artigos"
IMAGE_DIR = SITE_DIR / "images" / "articles"
PUBLISHED_STATUSES = {"approved", "corrected_approved", "published_direct"}


def remote_file_exists(ftp: FTP, remote_path: str) -> bool:
    try:
        ftp.voidcmd("TYPE I")
        ftp.size(remote_path)
        return True
    except Exception:
        try:
            return bool(ftp.nlst(remote_path))
        except Exception:
            return False


def download_remote_file(ftp: FTP, remote_path: str, local_path: Path, overwrite: bool = False) -> bool:
    if local_path.exists() and not overwrite:
        return False
    if not remote_file_exists(ftp, remote_path):
        return False
    local_path.parent.mkdir(parents=True, exist_ok=True)
    with local_path.open("wb") as file:
        ftp.retrbinary(f"RETR {remote_path}", file.write)
    print(f"Synced {remote_path}")
    return True


def approved_remote_drafts(ftp: FTP) -> list[ArticleDraft]:
    allowed = {field.name for field in fields(ArticleDraft)}
    drafts: list[ArticleDraft] = []
    current = ftp.pwd()
    try:
        ftp.cwd("_editorial_drafts")
        names = [name for name in ftp.nlst() if name.endswith(".json")]
    except Exception:
        ftp.cwd(current)
        return drafts
    for name in names:
        payload = BytesIO()
        try:
            ftp.retrbinary(f"RETR {name}", payload.write)
            data = json.loads(payload.getvalue().decode("utf-8"))
        except Exception as exc:
            print(f"Skipped remote draft {name}: {exc}")
            continue
        if data.get("status") not in PUBLISHED_STATUSES:
            continue
        draft = ArticleDraft(**{key: value for key, value in data.items() if key in allowed})
        drafts.append(draft)
    ftp.cwd(current)
    return sorted(drafts, key=lambda draft: draft.created_at)


def sync_approved_remote_articles(ftp: FTP) -> None:
    ftp.cwd(settings.ftp_dir)
    for draft in approved_remote_drafts(ftp):
        local_article = ARTICLE_DIR / f"{draft.slug}.html"
        download_remote_file(
            ftp,
            f"artigos/{draft.slug}.html",
            local_article,
        )
        if not local_article.exists():
            local_article.parent.mkdir(parents=True, exist_ok=True)
            local_article.write_text(render_article_page(draft), encoding="utf-8")
            print(f"Rebuilt missing approved article {draft.slug}.html")


def article_draft_from_html(slug: str, html: str) -> ArticleDraft:
    data: dict = {}
    match = re.search(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if match:
        try:
            parsed = json.loads(unescape(match.group(1)))
            if isinstance(parsed, dict):
                data = parsed
        except json.JSONDecodeError:
            pass

    def meta(property_name: str) -> str:
        pattern = (
            r'<meta[^>]+(?:property|name)=["\']'
            + re.escape(property_name)
            + r'["\'][^>]+content=["\']([^"\']+)["\']'
        )
        found = re.search(pattern, html, flags=re.IGNORECASE)
        return unescape(found.group(1)).strip() if found else ""

    image = data.get("image") or meta("og:image")
    if isinstance(image, list):
        image = image[0] if image else ""
    image_filename = Path(urlparse(str(image)).path).name
    title = str(data.get("headline") or meta("og:title") or slug).strip()
    description = str(data.get("description") or meta("description") or "").strip()
    category = str(data.get("articleSection") or "Reflexão Cristã").strip()
    author_data = data.get("author") or {}
    author = str(author_data.get("name") if isinstance(author_data, dict) else author_data).strip()
    published = str(data.get("datePublished") or "").strip()
    if not published:
        published = datetime.now(timezone.utc).isoformat()

    return ArticleDraft(
        id=f"catalog-{slug}",
        token="catalog",
        sender="",
        source_subject=title,
        source_text="",
        title=title,
        slug=slug,
        excerpt=description,
        category=category,
        author=author or "Pastor Antônio Lemos",
        body_html="",
        image_prompt="",
        image_filename=image_filename,
        seo_description=description,
        created_at=published,
        status="published",
    )


def article_sort_key(draft: ArticleDraft) -> datetime:
    try:
        parsed = datetime.fromisoformat(draft.created_at)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sync_remote_article_catalog(ftp: FTP) -> list[ArticleDraft]:
    ftp.cwd(settings.ftp_dir)
    try:
        names = sorted(
            name.rsplit("/", 1)[-1]
            for name in ftp.nlst("artigos")
            if name.lower().endswith(".html")
        )
    except Exception:
        names = []

    catalog: list[ArticleDraft] = []
    for name in names:
        slug = name[:-5]
        local_article = ARTICLE_DIR / name
        download_remote_file(ftp, f"artigos/{name}", local_article, overwrite=True)
        html = local_article.read_text(encoding="utf-8", errors="replace")
        draft = article_draft_from_html(slug, html)
        catalog.append(draft)
        local_article.write_text(with_article_navigation(html), encoding="utf-8")
    return sorted(catalog, key=article_sort_key, reverse=True)


def should_upload_repair_file(remote_path: str) -> bool:
    if remote_path.startswith("images/"):
        return False
    if remote_path.startswith("_editorial_drafts/"):
        return False
    allowed_suffixes = (".html", ".php", ".css", ".js", ".xml", ".txt", ".json", ".ico")
    return remote_path.endswith(allowed_suffixes)


def with_article_navigation(html: str) -> str:
    navigation = article_navigation_html().strip()
    if "<!-- ARTICLE_NAV_START -->" in html:
        html = re.sub(
            r"<!-- ARTICLE_NAV_START -->.*?<!-- ARTICLE_NAV_END -->",
            navigation,
            html,
            count=1,
            flags=re.DOTALL,
        )
    else:
        html, replacements = re.subn(
            r'(<p class="publication-date">.*?</p>)',
            lambda match: match.group(1) + "\n" + navigation,
            html,
            count=1,
            flags=re.DOTALL,
        )
        if replacements != 1:
            raise RuntimeError("Publication date marker not found while adding article navigation.")

    html = re.sub(
        r"\.\./styles\.css(?:\?v=[^\"']+)?",
        "../styles.css?v=20260627-article-navigation",
        html,
        count=1,
    )
    script = '<script src="../article-navigation.js?v=20260627-article-navigation" defer></script>'
    if "article-navigation.js" not in html:
        html = html.replace("</body>", f"  {script}\n  </body>", 1)
    return html


def rebuild_catalog_indexes(catalog: list[ArticleDraft]) -> None:
    if not catalog:
        raise RuntimeError("Remote article catalog is empty; deployment aborted.")

    index_path = SITE_DIR / "index.html"
    index = index_path.read_text(encoding="utf-8")
    index = re.sub(
        r'\s*<article class="featured">.*?</article>',
        "\n" + featured_article(catalog[0]),
        index,
        count=1,
        flags=re.DOTALL,
    )
    home_cards = article_grid_html(catalog[1:HOME_ARTICLE_LIMIT])
    index = replace_article_grid(index, home_cards)
    index_path.write_text(index, encoding="utf-8")

    articles_path = SITE_DIR / "artigos.html"
    articles_html = render_articles_page(catalog)
    articles_path.write_text(articles_html, encoding="utf-8")

    feed_path = SITE_DIR / "feed.xml"
    feed = feed_path.read_text(encoding="utf-8")
    feed = re.sub(r"\s*<item>.*?</item>", "", feed, flags=re.DOTALL)
    items = []
    for draft in catalog:
        url = f"{DOMAIN}/artigos/{draft.slug}.html"
        items.append(
            "\n    <item>\n"
            f"      <title>{escape(draft.title)}</title>\n"
            f"      <link>{url}</link>\n"
            f"      <guid>{url}</guid>\n"
            f"      <description>{escape(draft.excerpt)}</description>\n"
            f"      <pubDate>{draft_pub_date(draft)}</pubDate>\n"
            "    </item>"
        )
    feed = feed.replace("</channel>", "".join(items) + "\n  </channel>", 1)
    feed_path.write_text(feed, encoding="utf-8")

    sitemap_path = SITE_DIR / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8")
    sitemap = re.sub(
        r"\s*<url>\s*<loc>https://verbovivo\.blog/artigos/.*?</url>",
        "",
        sitemap,
        flags=re.DOTALL,
    )
    sitemap = ensure_sitemap_url(sitemap, f"{DOMAIN}/artigos.html")
    entries = "".join(sitemap_entry(f"{DOMAIN}/artigos/{draft.slug}.html") for draft in catalog)
    sitemap = sitemap.replace("</urlset>", entries + "</urlset>", 1)
    sitemap_path.write_text(sitemap, encoding="utf-8")

    validate_catalog_indexes(catalog)


def ensure_sitemap_url(sitemap_xml: str, url: str) -> str:
    if url in sitemap_xml:
        return sitemap_xml
    return sitemap_xml.replace("</urlset>", sitemap_entry(url) + "</urlset>", 1)


def render_articles_page(catalog: list[ArticleDraft]) -> str:
    cards = article_grid_html(catalog)
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Artigos | Verbo Vivo</title>
    <meta name="description" content="Arquivo completo de reflexões bíblicas publicadas no Verbo Vivo, com textos para leitura, oração e amadurecimento cristão." />
    <link rel="canonical" href="{DOMAIN}/artigos.html" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="Artigos | Verbo Vivo" />
    <meta property="og:description" content="Arquivo completo de reflexões bíblicas publicadas no Verbo Vivo." />
    <meta property="og:url" content="{DOMAIN}/artigos.html" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="alternate" type="application/rss+xml" title="Verbo Vivo" href="feed.xml" />
    <link rel="stylesheet" href="styles.css?v=20260625-adsense-quality" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="index.html"><span class="brand-mark">VV</span><span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span></a>
      <nav aria-label="Navegação principal">
        <a href="artigos.html">Artigos</a>
        <a href="comece-aqui.html">Comece aqui</a>
        <a href="licoes-escola-dominical.html">Lições</a>
        <a href="autor.html">Autor</a>
        <a href="sobre.html">Sobre</a>
        <a href="contato.html">Contato</a>
        <a href="faq.html">FAQ</a>
        <a href="politica-de-privacidade.html">Privacidade</a>
      </nav>
    </header>
    <section aria-label="Livro em destaque" class="top-book-strip">
      <span>Livro gratuito do autor</span>
      <strong>Servir através da Intercessão</strong>
      <a href="https://www.editorakaleo.com/product-page/servir-atrav%C3%A9s-da-intercess%C3%A3o" rel="noopener" target="_blank">Acessar e-book</a>
    </section>
    <main>
      <article class="article-page static-page">
        <header class="plain-hero">
          <p class="eyebrow">Arquivo de reflexões</p>
          <h1>Artigos publicados no Verbo Vivo</h1>
          <p class="article-excerpt">Todas as reflexões bíblicas publicadas no blog, reunidas em ordem de publicação para leitura, oração e estudo.</p>
        </header>
      </article>
      <section aria-label="Lista de artigos" class="article-grid">
{cards}
      </section>
    </main>
    <footer class="site-footer">
      <p><strong>Verbo Vivo</strong> publica reflexões cristãs para fortalecer a fé na vida cotidiana.</p>
      <div>
        <a href="artigos.html">Artigos</a>
        <a href="licoes-escola-dominical.html">Lições</a>
        <a href="comece-aqui.html">Comece aqui</a>
        <a href="autor.html">Autor</a>
        <a href="sobre.html">Sobre</a>
        <a href="contato.html">Contato</a>
        <a href="faq.html">FAQ</a>
        <a href="politica-de-privacidade.html">Privacidade</a>
        <a href="feed.xml">RSS</a>
        <a href="https://instagram.com/tec.agora" rel="noopener" target="_blank">By @tec.agora</a>
      </div>
    </footer>
  </body>
</html>
"""


def validate_catalog_indexes(catalog: list[ArticleDraft]) -> None:
    index = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    articles = (SITE_DIR / "artigos.html").read_text(encoding="utf-8")
    feed = (SITE_DIR / "feed.xml").read_text(encoding="utf-8")
    sitemap = (SITE_DIR / "sitemap.xml").read_text(encoding="utf-8")
    missing: list[str] = []
    if f"{DOMAIN}/artigos.html" not in sitemap:
        missing.append("artigos.html")
    for draft in catalog:
        relative = f"artigos/{draft.slug}.html"
        absolute = f"{DOMAIN}/{relative}"
        if relative not in articles or absolute not in feed or absolute not in sitemap:
            missing.append(draft.slug)
    if missing:
        raise RuntimeError("Catalog validation failed; missing from indexes: " + ", ".join(missing))
    home_article_count = index.count('class="featured"') + index.count('class="article-card"')
    if home_article_count > HOME_ARTICLE_LIMIT:
        raise RuntimeError(f"Home has {home_article_count} articles; expected at most {HOME_ARTICLE_LIMIT}.")
    print(f"Catalog validated: {len(catalog)} articles in artigos.html, feed and sitemap.")


def deploy_site() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        sync_approved_remote_articles(ftp)
        catalog = sync_remote_article_catalog(ftp)
        rebuild_catalog_indexes(catalog)
        lesson_slugs = rebuild_lesson_catalog()
        if lesson_slugs:
            print(f"Lesson catalog validated: {len(lesson_slugs)} lessons in lesson index and sitemap.")
        sitemap_path = SITE_DIR / "sitemap.xml"
        sitemap = sitemap_path.read_text(encoding="utf-8")
        sitemap_path.write_text(ensure_sitemap_url(sitemap, f"{DOMAIN}/artigos.html"), encoding="utf-8")
        validate_catalog_indexes(catalog)

        for path in SITE_DIR.rglob("*"):
            if not path.is_file():
                continue
            remote_path = path.relative_to(SITE_DIR).as_posix()
            if not should_upload_repair_file(remote_path):
                continue
            if "/" in remote_path:
                ensure_dir(ftp, remote_path.rsplit("/", 1)[0])
            with path.open("rb") as file:
                ftp.storbinary(f"STOR {remote_path}", file)
            print(f"Uploaded {remote_path}")


if __name__ == "__main__":
    deploy_site()
