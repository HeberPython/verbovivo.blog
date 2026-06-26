from __future__ import annotations

from dataclasses import fields
from ftplib import FTP
from io import BytesIO
import json
from pathlib import Path

from .config import settings
from .content import render_article_page
from .models import ArticleDraft
from .publisher import ensure_dir, update_local_indexes


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
        update_local_indexes(draft)


def deploy_site() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        sync_approved_remote_articles(ftp)

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
