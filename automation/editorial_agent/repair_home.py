"""Targeted home repair: prepare backup, save artifact, then apply verified files."""
from ftplib import FTP
from io import BytesIO
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

from .config import settings

ROOT = Path('automation/_backups/home-repair')
BACKUP = ROOT / 'before'
STAGE = ROOT / 'staged'
ENDPOINTS = ['revisao.php', 'gestor-artigos.php', 'receber-arquivo-editorial.php']
TARGETS = ['home-catalog.php', *ENDPOINTS, 'index.html']


def read(ftp, name):
    out = BytesIO()
    ftp.retrbinary('RETR ' + name, out.write)
    return out.getvalue()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def names(ftp, directory):
    return sorted(directory + '/' + name.rsplit('/', 1)[-1]
                  for name in ftp.nlst(directory)
                  if name.endswith(('.html', '.json')))


def snapshot(ftp):
    root = [name.rsplit('/', 1)[-1] for name in ftp.nlst()
            if name.endswith(('.html', '.php', '.xml')) and '/' not in name.strip('/')]
    result = {name: read(ftp, name) for name in root}
    for directory in ['artigos', 'licoes', '_editorial_drafts']:
        for name in names(ftp, directory):
            result[name] = read(ftp, name)
    return result


def patch_endpoint(name, source):
    if name == 'revisao.php':
        pattern = r'function update_index\(array \$draft\): void \{.*?\n\}\s*(?=function update_articles_archive)'
        replacement = "function update_index(array $draft): void {\n    require_once __DIR__ . '/home-catalog.php';\n    refresh_current_home(__DIR__);\n}\n\n"
    elif name == 'gestor-artigos.php':
        pattern = r"(function update_indexes\(.*?\n)(.*?)(    \$index = __DIR__ .*?)(?=    \$articles = __DIR__)"
        match = re.search(pattern, source, re.S)
        if not match:
            raise RuntimeError('Manager markers missing')
        return source[:match.start(3)] + "    require_once __DIR__ . '/home-catalog.php';\n    refresh_current_home(__DIR__);\n" + source[match.end(3):]
    else:
        pattern = r"\$target = __DIR__ \. '/' \. \$path;"
        replacement = "$target = __DIR__ . '/' . $path;\nif ($path === 'index.html') {\n    require_once __DIR__ . '/home-catalog.php';\n    refresh_current_home(__DIR__);\n    header('Content-Type: text/plain; charset=UTF-8');\n    exit('OK ' . $path);\n}"
    updated, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError('Endpoint markers missing: ' + name)
    return updated


def home_links(html):
    cards = re.findall(r'<article class="(?:featured|article-card)">.*?</article>', html, re.S)
    return [re.search(r'href="([^"]+)"', card)[1] for card in cards]


def validate_catalog(files):
    articles = {name for name in files if name.startswith('artigos/')}
    archive = files['artigos.html'].decode('utf-8')
    feed = ET.fromstring(files['feed.xml'])
    sitemap = ET.fromstring(files['sitemap.xml'])
    feed_urls = [n.text for n in feed.findall('.//item/link')]
    map_urls = {n.text for n in sitemap.iter() if n.tag.endswith('}loc') or n.tag == 'loc'}
    if len(feed_urls) != len(set(feed_urls)):
        raise RuntimeError('Duplicate feed entries; stop before deployment')
    missing = [name for name in articles if name not in archive
               or 'https://verbovivo.blog/' + name not in feed_urls
               or 'https://verbovivo.blog/' + name not in map_urls]
    if missing:
        raise RuntimeError('Existing catalog gaps; no deployment: ' + ', '.join(missing))
    print('Protected catalog:', len(articles), 'articles;', len(feed_urls), 'feed entries')


def prepare(ftp):
    files = snapshot(ftp)
    validate_catalog(files)
    for name, data in files.items():
        # Drafts contain private review links; retain only their hashes for comparison.
        if name.startswith('_editorial_drafts/'):
            continue
        path = BACKUP / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (ROOT / 'manifest.json').write_text(json.dumps({n: digest(d) for n, d in files.items()}, indent=2))
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / 'home-catalog.php').write_bytes(Path('site/home-catalog.php').read_bytes())
    for name in ENDPOINTS:
        (STAGE / name).write_text(patch_endpoint(name, files[name].decode('utf-8')), encoding='utf-8')
    for name in TARGETS[:-1]:
        subprocess.run(['php', '-l', str(STAGE / name)], check=True)
    runner = "require $argv[1]; echo render_current_home(file_get_contents($argv[2].'/index.html'), $argv[2]);"
    result = subprocess.run(['php', '-r', runner, str(STAGE / 'home-catalog.php'), str(BACKUP)], check=True, capture_output=True)
    (STAGE / 'index.html').write_bytes(result.stdout)
    links = home_links(result.stdout.decode('utf-8'))
    if len(links) != 4 or len(set(links)) != 4:
        raise RuntimeError('Expected four distinct articles')
    print('Before:', home_links(files['index.html'].decode('utf-8')))
    print('After:', links)
    print('Backup verified; no server files changed.')


def apply(ftp):
    expected = json.loads((ROOT / 'manifest.json').read_text())
    before = snapshot(ftp)
    if {n: digest(d) for n, d in before.items()} != expected:
        raise RuntimeError('Server changed after backup; no deployment')
    written = []
    try:
        for name in TARGETS:
            payload = (STAGE / name).read_bytes()
            ftp.storbinary('STOR ' + name + '.home-repair-tmp', BytesIO(payload))
            if read(ftp, name + '.home-repair-tmp') != payload:
                raise RuntimeError('Staging verification failed: ' + name)
            ftp.rename(name + '.home-repair-tmp', name)
            written.append(name)
        after = snapshot(ftp)
        for name, data in before.items():
            if name not in TARGETS and after.get(name) != data:
                raise RuntimeError('Protected file changed: ' + name)
        for name in TARGETS:
            if after.get(name) != (STAGE / name).read_bytes():
                raise RuntimeError('Target verification failed: ' + name)
        validate_catalog(after)
        print('Verified: only five home-related files deployed; articles, lessons, drafts and other indexes unchanged.')
    except Exception:
        for name in reversed(written):
            if name in before:
                ftp.storbinary('STOR ' + name, BytesIO(before[name]))
        raise


if __name__ == '__main__':
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.cwd(settings.ftp_dir)
        {'prepare': prepare, 'apply': apply}[sys.argv[1]](ftp)
