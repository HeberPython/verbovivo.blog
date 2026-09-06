from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from ftplib import FTP
from html import unescape
from io import BytesIO
import hashlib
import json
import re

from imap_tools import AND, MailBox

from .config import settings
from .content import slugify
from .content_audit import download, title_from_html
from .security import is_sender_allowed


RECENT_LIMIT = 15


def mask_email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value:
        return value[:2] + "***" if value else ""
    name, domain = value.split("@", 1)
    prefix = name[:2] if len(name) > 2 else name[:1]
    return f"{prefix}***@{domain}"


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]


def safe_subject(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value[:120]


def message_line(
    message,
    inbox: str,
    published_slugs: set[str] | None = None,
    *,
    include_seen_flag: bool = True,
) -> str:
    subject = safe_subject(message.subject or "")
    slug = slugify(subject) if subject else ""
    state = []
    if include_seen_flag:
        if getattr(message, "seen", False):
            state.append("read")
        else:
            state.append("unread")
    else:
        state.append("recent")
    if is_sender_allowed(message.from_ or ""):
        state.append("allowed")
    else:
        state.append("unauthorized")
    if published_slugs is not None and slug:
        state.append("published" if slug in published_slugs else "not-published")
    date = getattr(message, "date", None)
    if isinstance(date, datetime):
        date_text = date.astimezone(timezone.utc).isoformat()
    else:
        date_text = ""
    return (
        f"EMAIL\t{inbox}\tuid={message.uid}\tdate={date_text}\t"
        f"from={mask_email(message.from_ or '')}\tfrom_hash={short_hash(message.from_ or '')}\t"
        f"state={','.join(state)}\tsubject={subject}"
    )


def fetch_messages(host: str, port: int, user: str, password: str, *, unread_only: bool, limit: int):
    with MailBox(host, port).login(user, password) as mailbox:
        if unread_only:
            return list(mailbox.fetch(AND(seen=False), limit=limit, mark_seen=False, headers_only=True))
        return list(mailbox.fetch(limit=limit, reverse=True, mark_seen=False, headers_only=True))


def remote_published_slugs() -> set[str]:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        names = ftp.nlst("artigos")
    return {
        name.rsplit("/", 1)[-1][:-5]
        for name in names
        if name.lower().endswith(".html")
    }


def audit_remote_content() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)

        index = download(ftp, "index.html").decode("utf-8", errors="replace")
        articles_index = download(ftp, "artigos.html").decode("utf-8", errors="replace")
        feed = download(ftp, "feed.xml").decode("utf-8", errors="replace")
        sitemap = download(ftp, "sitemap.xml").decode("utf-8", errors="replace")
        article_names = sorted(
            name.rsplit("/", 1)[-1]
            for name in ftp.nlst("artigos")
            if name.lower().endswith(".html")
        )

        home_count = index.count('class="featured"') + index.count('class="article-card"')
        archive_count = articles_index.count('class="article-card"')
        feed_count = feed.count("<item>")
        sitemap_count = len(re.findall(r"https://verbovivo\.blog/artigos/[^<]+\.html", sitemap))
        print(f"SITE_SUMMARY\thome={home_count}\tarchive={archive_count}\tfeed={feed_count}\tsitemap_articles={sitemap_count}\tphysical_articles={len(article_names)}")

        orphaned: list[str] = []
        for name in article_names:
            locations = [
                label
                for label, content in (
                    ("artigos", articles_index),
                    ("feed", feed),
                    ("sitemap", sitemap),
                )
                if f"artigos/{name}" in content
            ]
            if len(locations) < 3:
                html = download(ftp, f"artigos/{name}").decode("utf-8", errors="replace")
                orphaned.append(f"{name[:-5]}:{','.join(locations) or 'orphan'}:{title_from_html(html, name[:-5])}")
        if orphaned:
            print("SITE_ORPHANS\t" + " | ".join(orphaned))
        else:
            print("SITE_ORPHANS\tnone")

        draft_statuses: Counter[str] = Counter()
        try:
            draft_names = [
                name.rsplit("/", 1)[-1]
                for name in ftp.nlst("_editorial_drafts")
                if name.lower().endswith(".json")
            ]
        except Exception:
            draft_names = []
        for name in draft_names:
            try:
                data = json.loads(download(ftp, f"_editorial_drafts/{name}").decode("utf-8"))
            except Exception:
                draft_statuses["unreadable"] += 1
                continue
            draft_statuses[str(data.get("status") or "unknown")] += 1
        print("DRAFT_SUMMARY\t" + (", ".join(f"{key}={value}" for key, value in sorted(draft_statuses.items())) or "none"))


def audit_inbox(name: str, host: str, port: int, user: str, password: str, published_slugs: set[str] | None = None) -> None:
    unread = fetch_messages(host, port, user, password, unread_only=True, limit=RECENT_LIMIT)
    recent = fetch_messages(host, port, user, password, unread_only=False, limit=RECENT_LIMIT)
    print(f"INBOX_SUMMARY\t{name}\tunread_sample={len(unread)}\trecent_sample={len(recent)}")
    for message in unread:
        print(message_line(message, name, published_slugs))
    if not unread:
        print(f"EMAIL\t{name}\tunread=none")
    print(f"RECENT_HEADER_SAMPLE\t{name}")
    for message in recent[:5]:
        print(message_line(message, name, published_slugs, include_seen_flag=False))


def main() -> None:
    try:
        published_slugs = remote_published_slugs()
        print(f"PUBLISHED_SLUGS\tstatus=ok\tcount={len(published_slugs)}")
    except Exception as exc:
        published_slugs = None
        print(f"PUBLISHED_SLUGS\tstatus=error\terror={exc.__class__.__name__}")
    audit_inbox(
        "publicar@verbovivo.blog",
        settings.publish_imap_host,
        settings.publish_imap_port,
        settings.publish_imap_user,
        settings.publish_imap_password,
        published_slugs,
    )
    audit_inbox(
        "artigo@verbovivo.blog",
        settings.imap_host,
        settings.imap_port,
        settings.imap_user,
        settings.imap_password,
    )
    try:
        audit_remote_content()
    except Exception as exc:
        print(f"SITE_AUDIT\tstatus=error\terror={exc.__class__.__name__}")


if __name__ == "__main__":
    main()
