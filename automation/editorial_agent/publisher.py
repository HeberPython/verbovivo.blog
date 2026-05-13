from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from ftplib import FTP, error_perm
from html import escape
from io import BytesIO
import json
from pathlib import Path

from .config import settings
from .content import render_article_page
from .models import ArticleDraft


DOMAIN = "https://verbovivo.blog"
SITE_DIR = Path("site")


def ensure_dir(ftp: FTP, path: str) -> None:
    current = ftp.pwd()
    ftp.cwd(settings.ftp_dir)
    for part in [p for p in path.strip("/").split("/") if p]:
        try:
            ftp.mkd(part)
        except error_perm:
            pass
        ftp.cwd(part)
    ftp.cwd(current)


def article_card(draft: ArticleDraft) -> str:
    image = draft.image_filename or "depois-da-festa.png"
    return f"""
      <article class="article-card">
        <a href="artigos/{escape(draft.slug)}.html">
          <img src="images/articles/{escape(image)}" alt="{escape(draft.title)}" />
        </a>
        <div class="article-body">
          <p class="category">{escape(draft.category)}</p>
          <h3><a href="artigos/{escape(draft.slug)}.html">{escape(draft.title)}</a></h3>
          <p>{escape(draft.excerpt)}</p>
        </div>
      </article>
"""


def draft_pub_date(draft: ArticleDraft) -> str:
    try:
        parsed = datetime.fromisoformat(draft.created_at)
    except ValueError:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return format_datetime(parsed.astimezone(timezone.utc))


def update_local_indexes(draft: ArticleDraft) -> list[Path]:
    changed: list[Path] = []

    index_path = SITE_DIR / "index.html"
    if index_path.exists():
        index_html = index_path.read_text(encoding="utf-8")
        article_url = f"artigos/{draft.slug}.html"
        if article_url not in index_html:
            marker = '<section class="article-grid" aria-label="Lista de artigos">'
            replacement = marker + "\n        " + article_card(draft)
            index_html = index_html.replace(marker, replacement, 1)
            index_path.write_text(index_html, encoding="utf-8")
            changed.append(index_path)

    feed_path = SITE_DIR / "feed.xml"
    if feed_path.exists():
        feed_xml = feed_path.read_text(encoding="utf-8")
        url = f"{DOMAIN}/artigos/{draft.slug}.html"
        if url not in feed_xml:
            item = f"""
    <item>
      <title>{escape(draft.title)}</title>
      <link>{url}</link>
      <guid>{url}</guid>
      <description>{escape(draft.excerpt)}</description>
      <pubDate>{draft_pub_date(draft)}</pubDate>
    </item>"""
            marker = "    <item>"
            feed_xml = feed_xml.replace(marker, item + "\n" + marker, 1)
            feed_path.write_text(feed_xml, encoding="utf-8")
            changed.append(feed_path)

    sitemap_path = SITE_DIR / "sitemap.xml"
    if sitemap_path.exists():
        sitemap_xml = sitemap_path.read_text(encoding="utf-8")
        url = f"{DOMAIN}/artigos/{draft.slug}.html"
        if url not in sitemap_xml:
            sitemap_xml = sitemap_xml.replace("</urlset>", f"  <url><loc>{url}</loc></url>\n</urlset>", 1)
            sitemap_path.write_text(sitemap_xml, encoding="utf-8")
            changed.append(sitemap_path)

    return changed


def write_local_article(draft: ArticleDraft, html: bytes) -> list[Path]:
    changed: list[Path] = []
    article_dir = SITE_DIR / "artigos"
    article_dir.mkdir(parents=True, exist_ok=True)
    article_path = article_dir / f"{draft.slug}.html"
    article_path.write_bytes(html)
    changed.append(article_path)

    if draft.local_image_path and draft.image_filename:
        source = Path(draft.local_image_path)
        if source.exists():
            image_dir = SITE_DIR / "images" / "articles"
            image_dir.mkdir(parents=True, exist_ok=True)
            image_path = image_dir / draft.image_filename
            image_path.write_bytes(source.read_bytes())
            changed.append(image_path)
    return changed


def publish_article(draft: ArticleDraft) -> None:
    html = render_article_page(draft).encode("utf-8")
    changed_paths = write_local_article(draft, html)
    changed_paths.extend(update_local_indexes(draft))

    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        ensure_dir(ftp, "artigos")
        ftp.storbinary(f"STOR artigos/{draft.slug}.html", BytesIO(html))
        if draft.local_image_path:
            image_path = Path(draft.local_image_path)
            if image_path.exists():
                ensure_dir(ftp, "images/articles")
                with image_path.open("rb") as image_file:
                    ftp.storbinary(f"STOR images/articles/{draft.image_filename}", image_file)
        for path in changed_paths:
            if path.name == f"{draft.slug}.html" or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            with path.open("rb") as file:
                ftp.storbinary(f"STOR {path.relative_to(SITE_DIR).as_posix()}", file)


def upload_review_draft(draft: ArticleDraft) -> None:
    payload = json.dumps(draft.__dict__, ensure_ascii=False, indent=2).encode("utf-8")
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        ensure_dir(ftp, "_editorial_drafts")
        ftp.storbinary(f"STOR _editorial_drafts/{draft.token}.json", BytesIO(payload))
        if draft.local_image_path and draft.image_filename:
            image_path = Path(draft.local_image_path)
            if image_path.exists():
                ensure_dir(ftp, "images/articles")
                with image_path.open("rb") as image_file:
                    ftp.storbinary(f"STOR images/articles/{draft.image_filename}", image_file)
