from __future__ import annotations

from ftplib import FTP
from io import BytesIO
import re

from .config import settings
from .content import DOMAIN


def _featured_image_url(index_html: str) -> str:
    featured = re.search(
        r'<article\s+class=["\']featured["\'][^>]*>(.*?)</article>',
        index_html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not featured:
        raise RuntimeError("Featured article not found in homepage.")
    image = re.search(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        featured.group(1),
        flags=re.IGNORECASE,
    )
    if not image:
        raise RuntimeError("Featured article image not found in homepage.")
    src = image.group(1).strip()
    if src.startswith("http://") or src.startswith("https://"):
        return src
    return f"{DOMAIN}/{src.lstrip('/')}"


def _replace_meta(html: str, key: str, value: str, attribute: str = "property") -> str:
    pattern = (
        r'(<meta[^>]+\b' + re.escape(attribute) + r'=["\']'
        + re.escape(key)
        + r'["\'][^>]+\bcontent=["\'])([^"\']*)(["\'][^>]*>)'
    )
    updated, count = re.subn(pattern, rf"\g<1>{value}\g<3>", html, count=1, flags=re.IGNORECASE)
    if count:
        return updated
    marker = "</head>"
    tag = f'<meta {attribute}="{key}" content="{value}" />\n'
    if marker not in html:
        raise RuntimeError("Homepage </head> marker not found.")
    return html.replace(marker, tag + marker, 1)


def sync_home_social_preview_html(index_html: str) -> tuple[str, str]:
    image_url = _featured_image_url(index_html)
    updated = _replace_meta(index_html, "og:image", image_url)
    updated = _replace_meta(updated, "twitter:image", image_url, attribute="name")
    return updated, image_url


def sync_remote_home_social_preview() -> str:
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=30)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.cwd(settings.ftp_dir)
        payload = BytesIO()
        ftp.retrbinary("RETR index.html", payload.write)
        current = payload.getvalue().decode("utf-8")
        updated, image_url = sync_home_social_preview_html(current)
        if updated != current:
            ftp.storbinary("STOR index.html", BytesIO(updated.encode("utf-8")))
            print(f"Homepage social preview updated: {image_url}")
        else:
            print(f"Homepage social preview already current: {image_url}")
        return image_url


def main() -> None:
    sync_remote_home_social_preview()


if __name__ == "__main__":
    main()
