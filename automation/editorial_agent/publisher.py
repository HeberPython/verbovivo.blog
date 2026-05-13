from __future__ import annotations

from ftplib import FTP, error_perm
from io import BytesIO

from .config import settings
from .content import render_article_page
from .models import ArticleDraft


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


def publish_article(draft: ArticleDraft) -> None:
    html = render_article_page(draft).encode("utf-8")
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        ensure_dir(ftp, "artigos")
        ftp.storbinary(f"STOR artigos/{draft.slug}.html", BytesIO(html))

