from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
ADMIN_TOKEN_FILE = ROOT / "automation" / "_admin_token.txt"

load_dotenv(ROOT / ".env", encoding="utf-8-sig")
load_dotenv(ROOT / "automation" / ".env", override=True, encoding="utf-8-sig")


def default_admin_token() -> str:
    if ADMIN_TOKEN_FILE.exists():
        return ADMIN_TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ""


@dataclass(frozen=True)
class Settings:
    imap_host: str = os.getenv("EDITORIAL_IMAP_HOST", "")
    imap_port: int = int(os.getenv("EDITORIAL_IMAP_PORT", "993"))
    imap_user: str = os.getenv("EDITORIAL_IMAP_USER", "artigo@verbovivo.blog")
    imap_password: str = os.getenv("EDITORIAL_IMAP_PASSWORD", "")

    smtp_host: str = os.getenv("EDITORIAL_SMTP_HOST", "")
    smtp_port: int = int(os.getenv("EDITORIAL_SMTP_PORT", "465"))
    smtp_user: str = os.getenv("EDITORIAL_SMTP_USER", "artigo@verbovivo.blog")
    smtp_password: str = os.getenv("EDITORIAL_SMTP_PASSWORD", "")

    publish_imap_host: str = os.getenv("PUBLISH_IMAP_HOST", "imap.hostinger.com")
    publish_imap_port: int = int(os.getenv("PUBLISH_IMAP_PORT", "993"))
    publish_imap_user: str = os.getenv("PUBLISH_IMAP_USER", "publicar@verbovivo.blog")
    publish_imap_password: str = os.getenv("PUBLISH_IMAP_PASSWORD", "")

    approval_base_url: str = os.getenv("EDITORIAL_APPROVAL_BASE_URL", "http://127.0.0.1:8787")
    approver_email: str = os.getenv("EDITORIAL_APPROVER_EMAIL", "hebergravano@gmail.com")
    allowed_senders: str = os.getenv("EDITORIAL_ALLOWED_SENDERS", "hebergravano@gmail.com")
    admin_token: str = os.getenv("EDITORIAL_ADMIN_TOKEN", default_admin_token())

    ftp_host: str = os.getenv("HOSTINGER_FTP_HOST", "ftp.verbovivo.blog")
    ftp_port: int = int(os.getenv("HOSTINGER_FTP_PORT", "21"))
    ftp_user: str = os.getenv("HOSTINGER_FTP_USER", "u454442761.codex")
    ftp_password: str = os.getenv("HOSTINGER_FTP_PASSWORD", "")
    ftp_dir: str = os.getenv("HOSTINGER_FTP_DIR", "/")
    editorial_upload_url: str = os.getenv("EDITORIAL_UPLOAD_URL", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    image_provider: str = os.getenv("EDITORIAL_IMAGE_PROVIDER", "gemini").lower()
    gemini_image_model: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")


settings = Settings()
