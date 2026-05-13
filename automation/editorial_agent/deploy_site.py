from __future__ import annotations

from ftplib import FTP
from pathlib import Path

from .config import settings
from .publisher import ensure_dir


SITE_DIR = Path("site")


def deploy_site() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)

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
