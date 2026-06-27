from __future__ import annotations

from ftplib import FTP
from html import unescape
from io import BytesIO
import json
import re

from .config import settings


def download(ftp: FTP, path: str) -> bytes:
    payload = BytesIO()
    ftp.retrbinary(f"RETR {path}", payload.write)
    return payload.getvalue()


def title_from_html(html: str, slug: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return slug
    return unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def main() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)

        index = download(ftp, "index.html").decode("utf-8", errors="replace")
        feed = download(ftp, "feed.xml").decode("utf-8", errors="replace")
        sitemap = download(ftp, "sitemap.xml").decode("utf-8", errors="replace")

        article_names = sorted(
            name.rsplit("/", 1)[-1]
            for name in ftp.nlst("artigos")
            if name.lower().endswith(".html")
        )
        print(f"REMOTE_ARTICLES={len(article_names)}")
        for name in article_names:
            slug = name[:-5]
            html = download(ftp, f"artigos/{name}").decode("utf-8", errors="replace")
            title = title_from_html(html, slug)
            locations = [
                label
                for label, content in (("home", index), ("feed", feed), ("sitemap", sitemap))
                if f"artigos/{name}" in content
            ]
            state = ",".join(locations) if locations else "orphan"
            print(f"ARTICLE\t{slug}\t{state}\t{title}")

        draft_names: list[str] = []
        try:
            draft_names = [
                name.rsplit("/", 1)[-1]
                for name in ftp.nlst("_editorial_drafts")
                if name.lower().endswith(".json")
            ]
        except Exception:
            pass
        print(f"REMOTE_DRAFTS={len(draft_names)}")
        for name in sorted(draft_names):
            try:
                data = json.loads(download(ftp, f"_editorial_drafts/{name}").decode("utf-8"))
            except Exception:
                continue
            print(
                "DRAFT\t"
                f"{data.get('slug', '')}\t{data.get('status', '')}\t"
                f"{data.get('created_at', '')}\t{data.get('title', '')}"
            )


if __name__ == "__main__":
    main()
