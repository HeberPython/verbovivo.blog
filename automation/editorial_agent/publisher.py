from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from ftplib import FTP, error_perm
from html import escape
from io import BytesIO
from contextlib import contextmanager
import base64
import json
from pathlib import Path
import re
import socket
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

from .config import settings
from .content import render_article_page
from .models import ArticleDraft


DOMAIN = "https://verbovivo.blog"
SITE_DIR = Path("site")
DEFAULT_IMAGE = "o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png"


@contextmanager
def prefer_ipv4():
    """Avoid broken IPv6 routes observed between GitHub Actions and Hostinger."""
    original = socket.getaddrinfo

    def ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
        results = original(host, port, family, type, proto, flags)
        ipv4 = [item for item in results if item[0] == socket.AF_INET]
        return ipv4 or results

    socket.getaddrinfo = ipv4_only
    try:
        yield
    finally:
        socket.getaddrinfo = original


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
    image = draft.image_filename or DEFAULT_IMAGE
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


def featured_article(draft: ArticleDraft) -> str:
    image = draft.image_filename or DEFAULT_IMAGE
    return f"""
      <article class="featured">
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


def draft_description(draft: ArticleDraft) -> str:
    return (draft.seo_description or draft.excerpt).strip()


def sitemap_entry(url: str) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    return f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""


def update_local_indexes(draft: ArticleDraft) -> list[Path]:
    changed: list[Path] = []

    index_path = SITE_DIR / "index.html"
    if index_path.exists():
        index_html = index_path.read_text(encoding="utf-8")
        original_html = index_html
        article_url = f"artigos/{draft.slug}.html"
        article_was_listed = article_url in index_html
        previous_featured_card = ""
        previous_featured_url = ""
        previous_featured = re.search(r'\s*(<article class="featured">.*?</article>)', index_html, re.DOTALL)
        if previous_featured:
            previous_markup = previous_featured.group(1)
            href_match = re.search(r'href="([^"]+)"', previous_markup)
            previous_featured_url = href_match.group(1) if href_match else ""
            if previous_featured_url and previous_featured_url != article_url:
                previous_featured_card = previous_markup.replace('class="featured"', 'class="article-card"', 1)
        index_html = re.sub(
            r'\s*<article class="featured">.*?</article>',
            "\n" + featured_article(draft),
            index_html,
            count=1,
            flags=re.DOTALL,
        )
        cards_to_insert: list[str] = []
        if previous_featured_card and previous_featured_url not in index_html:
            cards_to_insert.append(previous_featured_card)
        if not article_was_listed:
            cards_to_insert.append(article_card(draft))
        if cards_to_insert:
            index_html = re.sub(
                r'(<section\b[^>]*class="[^"]*\barticle-grid\b[^"]*"[^>]*>)',
                lambda match: match.group(1) + "\n        " + "\n        ".join(cards_to_insert),
                index_html,
                count=1,
            )
        if index_html != original_html:
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
      <description>{escape(draft_description(draft))}</description>
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
            sitemap_xml = sitemap_xml.replace("</urlset>", sitemap_entry(url) + "</urlset>", 1)
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


def http_upload(remote_path: str, payload: bytes) -> None:
    if not settings.editorial_upload_url:
        raise RuntimeError("EDITORIAL_UPLOAD_URL is not configured.")
    body = urlencode(
        {
            "token": settings.admin_token,
            "path": remote_path,
            "content_base64": base64.b64encode(payload).decode("ascii"),
        }
    ).encode("utf-8")
    request = Request(
        settings.editorial_upload_url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "VerboVivoEditorialAgent/1.0",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with prefer_ipv4(), urlopen(request, timeout=45) as response:
                if response.status >= 400:
                    raise RuntimeError(f"HTTP upload failed for {remote_path}: {response.status}")
                return
        except (OSError, URLError, RuntimeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"HTTP upload failed for {remote_path} after 3 attempts: {last_error}")


def remote_text(path: str) -> str:
    url = f"{DOMAIN}/{path.lstrip('/')}"
    request = Request(url, headers={"User-Agent": "VerboVivoEditorialAgent/1.0"})
    last_error: Exception | None = None
    for _ in range(3):
        try:
            with prefer_ipv4(), urlopen(request, timeout=30) as response:
                if response.status >= 400:
                    raise RuntimeError(f"Remote check failed for {path}: {response.status}")
                return response.read().decode("utf-8", errors="replace")
        except (OSError, URLError, RuntimeError) as exc:
            last_error = exc
    raise RuntimeError(f"Remote check failed for {path}: {last_error}")


def article_publication_status(slug: str) -> bool | None:
    article_path = f"artigos/{slug}.html"
    article_url = f"{DOMAIN}/{article_path}"
    try:
        article_html = remote_text(article_path)
        index_html = remote_text("index.html")
        feed_xml = remote_text("feed.xml")
        sitemap_xml = remote_text("sitemap.xml")
    except RuntimeError:
        return None
    return (
        "<article" in article_html
        and article_path in index_html
        and article_url in feed_xml
        and article_url in sitemap_xml
    )


def article_is_fully_published(slug: str) -> bool:
    return article_publication_status(slug) is True


def review_draft_is_available(token: str) -> bool:
    try:
        html = remote_text(f"revisao.php?token={token}")
    except RuntimeError:
        return False
    return "Rascunho nao encontrado" not in html and "Revisão editorial" in html


def verify_review_draft_upload(draft: ArticleDraft) -> None:
    if not review_draft_is_available(draft.token):
        raise RuntimeError(f"Review draft upload verification failed for draft {draft.id}.")


def verify_article_publication(draft: ArticleDraft) -> None:
    if not article_is_fully_published(draft.slug):
        raise RuntimeError(
            "Publication verification failed: "
            f"{draft.slug} is not visible in article page, home, feed and sitemap."
        )


def publish_article_http(draft: ArticleDraft, html: bytes, changed_paths: list[Path]) -> None:
    http_upload(f"artigos/{draft.slug}.html", html)
    if draft.local_image_path and draft.image_filename:
        image_path = Path(draft.local_image_path)
        if image_path.exists():
            http_upload(f"images/articles/{draft.image_filename}", image_path.read_bytes())
    for path in changed_paths:
        if path.name == f"{draft.slug}.html" or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        http_upload(path.relative_to(SITE_DIR).as_posix(), path.read_bytes())


def publish_article(draft: ArticleDraft) -> None:
    html = render_article_page(draft).encode("utf-8")
    changed_paths = write_local_article(draft, html)
    changed_paths.extend(update_local_indexes(draft))

    if settings.editorial_upload_url:
        publish_article_http(draft, html, changed_paths)
        verify_article_publication(draft)
        return

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
    verify_article_publication(draft)


def upload_review_draft(draft: ArticleDraft) -> None:
    payload = json.dumps(draft.__dict__, ensure_ascii=False, indent=2).encode("utf-8")
    if settings.editorial_upload_url:
        http_upload(f"_editorial_drafts/{draft.token}.json", payload)
        if draft.local_image_path and draft.image_filename:
            image_path = Path(draft.local_image_path)
            if image_path.exists():
                http_upload(f"images/articles/{draft.image_filename}", image_path.read_bytes())
        verify_review_draft_upload(draft)
        return

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
    verify_review_draft_upload(draft)
