from __future__ import annotations

from ftplib import FTP, error_perm
from pathlib import Path

from .config import settings


BACKUP_DIR = Path("automation") / "_backups" / "site-current"


def is_directory(ftp: FTP, name: str) -> bool:
    current = ftp.pwd()
    try:
        ftp.cwd(name)
        ftp.cwd(current)
        return True
    except error_perm:
        return False


def download_tree(ftp: FTP, remote_dir: str, local_dir: Path) -> None:
    local_dir.mkdir(parents=True, exist_ok=True)
    current = ftp.pwd()
    ftp.cwd(remote_dir)
    for name in ftp.nlst():
        if name in {".", ".."}:
            continue
        if is_directory(ftp, name):
            download_tree(ftp, name, local_dir / name)
            continue
        with (local_dir / name).open("wb") as file:
            ftp.retrbinary(f"RETR {name}", file.write)
        print(f"Backed up {remote_dir.strip('/')}/{name}".strip("/"))
    ftp.cwd(current)


def main() -> None:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        download_tree(ftp, ".", BACKUP_DIR)
    print(f"Backup saved to {BACKUP_DIR}")


if __name__ == "__main__":
    main()
