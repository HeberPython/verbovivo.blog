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
from .models import ArticleDraft
from .publisher import DOMAIN, article_card, draft_pub_date, ensure_dir, featured_article, sitemap_entry


SITE_DIR = Path("site")
ARTICLE_DIR = SITE_DIR / "artigos"
IMAGE_DIR = SITE_DIR / "images" / "articles"
PUBLISHED_STATUSES = {"approved", "corrected_approved", "published_direct"}


def remote_file_exists(ftp: FTP, remote_path: str) -> bool:
    try:
        ftp.size(remote_path)
        return True
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
        if draft.image_filename:
            download_remote_file(
                ftp,
                f"images/articles/{draft.image_filename}",
                IMAGE_DIR / draft.image_filename,
            )


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
        if draft.image_filename:
            download_remote_file(
                ftp,
                f"images/articles/{draft.image_filename}",
                IMAGE_DIR / draft.image_filename,
            )
    return sorted(catalog, key=article_sort_key, reverse=True)


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
    cards = "".join(article_card(draft) for draft in catalog[1:])
    index, replacements = re.subn(
        r'(<section\b[^>]*class="[^"]*\barticle-grid\b[^"]*"[^>]*>).*?(</section>)',
        lambda match: match.group(1) + "\n" + cards + match.group(2),
        index,
        count=1,
        flags=re.DOTALL,
    )
    if replacements != 1:
        raise RuntimeError("Article grid was not found; deployment aborted.")
    index_path.write_text(index, encoding="utf-8")

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
    entries = "".join(sitemap_entry(f"{DOMAIN}/artigos/{draft.slug}.html") for draft in catalog)
    sitemap = sitemap.replace("</urlset>", entries + "</urlset>", 1)
    sitemap_path.write_text(sitemap, encoding="utf-8")

    validate_catalog_indexes(catalog)


def validate_catalog_indexes(catalog: list[ArticleDraft]) -> None:
    index = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    feed = (SITE_DIR / "feed.xml").read_text(encoding="utf-8")
    sitemap = (SITE_DIR / "sitemap.xml").read_text(encoding="utf-8")
    missing: list[str] = []
    for draft in catalog:
        relative = f"artigos/{draft.slug}.html"
        absolute = f"{DOMAIN}/{relative}"
        if relative not in index or absolute not in feed or absolute not in sitemap:
            missing.append(draft.slug)
    if missing:
        raise RuntimeError("Catalog validation failed; missing from indexes: " + ", ".join(missing))
    print(f"Catalog validated: {len(catalog)} articles in home, feed and sitemap.")


def deploy_site() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        sync_approved_remote_articles(ftp)
        catalog = sync_remote_article_catalog(ftp)
        rebuild_catalog_indexes(catalog)

        for path in SITE_DIR.rglob("*"):
            if not path.is_file():
                continue
            remote_path = path.relative_to(SITE_DIR).as_posix()
            if "/" in remote_path:
                ensure_dir(ftp, remote_path.rsplit("/", 1)[0])
            with path.open("rb") as file:
                ftp.storbinary(f"STOR {remote_path}", file)
            print(f"Uploaded {remote_path}")


if __name__ == "__main__":
    deploy_site()
