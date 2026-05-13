from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


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

    approval_base_url: str = os.getenv("EDITORIAL_APPROVAL_BASE_URL", "http://127.0.0.1:8787")
    approver_email: str = os.getenv("EDITORIAL_APPROVER_EMAIL", "")

    ftp_host: str = os.getenv("HOSTINGER_FTP_HOST", "ftp.verbovivo.blog")
    ftp_port: int = int(os.getenv("HOSTINGER_FTP_PORT", "21"))
    ftp_user: str = os.getenv("HOSTINGER_FTP_USER", "u454442761.codex")
    ftp_password: str = os.getenv("HOSTINGER_FTP_PASSWORD", "")
    ftp_dir: str = os.getenv("HOSTINGER_FTP_DIR", "/")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()

