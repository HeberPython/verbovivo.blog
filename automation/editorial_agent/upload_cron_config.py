from __future__ import annotations

from ftplib import FTP
from io import BytesIO

from .config import settings
from .publisher import ensure_dir


def php_value(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def build_config() -> bytes:
    values = {
        "editorial_imap_host": settings.imap_host,
        "editorial_imap_port": str(settings.imap_port),
        "editorial_imap_user": settings.imap_user,
        "editorial_imap_password": settings.imap_password,
        "editorial_smtp_host": settings.smtp_host,
        "editorial_smtp_port": str(settings.smtp_port),
        "editorial_smtp_user": settings.smtp_user,
        "editorial_smtp_password": settings.smtp_password,
        "publish_imap_host": settings.publish_imap_host,
        "publish_imap_port": str(settings.publish_imap_port),
        "publish_imap_user": settings.publish_imap_user,
        "publish_imap_password": settings.publish_imap_password,
        "openai_api_key": settings.openai_api_key,
    }
    lines = ["<?php", "return ["]
    for key, value in values.items():
        lines.append(f"    {php_value(key)} => {php_value(value)},")
    lines.append("];")
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        ensure_dir(ftp, "_private")
        ftp.storbinary("STOR _private/editorial-config.php", BytesIO(build_config()))
    print("Uploaded _private/editorial-config.php")


if __name__ == "__main__":
    main()
