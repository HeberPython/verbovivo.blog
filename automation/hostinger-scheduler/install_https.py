"""Install a private CLI dispatcher via HTTPS; FTP carries only public bootstrap code."""
from ftplib import FTP
from io import BytesIO
from pathlib import Path
import base64
import hashlib
import json
import os
import secrets
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

BASE = 'https://verbovivo.blog/'
HERE = Path('automation/hostinger-scheduler')
BACKUP = Path('automation/_backups/scheduler-install')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('Credential-bearing installation request cannot redirect')


def remote(ftp, path):
    buffer = BytesIO()
    ftp.retrbinary('RETR ' + path, buffer.write)
    return buffer.getvalue()


def inventory(ftp):
    return {directory: sorted(ftp.nlst(directory)) for directory in ['artigos', 'licoes', '_editorial_drafts']}


def connect():
    ftp = FTP()
    ftp.connect(os.environ['HOSTINGER_FTP_HOST'], int(os.getenv('HOSTINGER_FTP_PORT') or 21), timeout=60)
    ftp.login(os.environ['HOSTINGER_FTP_USER'], os.environ['HOSTINGER_FTP_PASSWORD'])
    ftp.cwd(os.getenv('HOSTINGER_FTP_DIR') or '/')
    return ftp


def prepare():
    BACKUP.mkdir(parents=True, exist_ok=True)
    with connect() as ftp:
        for name in ['index.html', 'artigos.html', 'feed.xml', 'sitemap.xml', 'licoes-escola-dominical.html']:
            data = remote(ftp, name)
            (BACKUP / name).write_bytes(data)
            if remote(ftp, name) != data:
                raise RuntimeError('File changed during backup')
        (BACKUP / 'inventory.json').write_text(json.dumps(inventory(ftp)))
    print('Public index backup and read-only inventory verified. No remote writes.', flush=True)


def install():
    script = (HERE / 'dispatch-editorial.php').read_bytes()
    bootstrap = (HERE / 'install-once.php').read_bytes()
    target = 'scheduler-install-' + secrets.token_hex(12) + '.php'
    token = os.environ['EDITORIAL_DISPATCH_TOKEN'].strip()
    if not token.startswith('github_pat_'):
        raise RuntimeError('Expected dedicated fine-grained token')
    with connect() as ftp:
        before = json.loads((BACKUP / 'inventory.json').read_text())
        if inventory(ftp) != before:
            raise RuntimeError('Catalog changed since backup; stop')
        for path in BACKUP.glob('*'):
            if path.suffix in ['.html', '.xml'] and remote(ftp, path.name) != path.read_bytes():
                raise RuntimeError('Public index changed since backup; stop')
        if target in ftp.nlst():
            raise RuntimeError('Unexpected bootstrap name collision')
        try:
            ftp.storbinary('STOR ' + target, BytesIO(bootstrap))
            if remote(ftp, target) != bootstrap:
                raise RuntimeError('Bootstrap verification failed')
            request = Request(BASE + target, method='POST', data=json.dumps({
                'script': base64.b64encode(script).decode('ascii'), 'github_token': token,
            }).encode(), headers={
                'Content-Type': 'application/json',
                'X-Editorial-Token': os.environ['EDITORIAL_ADMIN_TOKEN'],
            })
            try:
                with build_opener(NoRedirect()).open(request, timeout=60) as response:
                    result = json.load(response)
            except HTTPError as error:
                raise RuntimeError('HTTPS install failed; HTTP ' + str(error.code)) from None
            if not result.get('outside_public_html') or result.get('config_permissions') != '600':
                raise RuntimeError('Private installation protection check failed')
            if result.get('script_sha256') != hashlib.sha256(script).hexdigest():
                raise RuntimeError('Installed script hash mismatch')
            (BACKUP / 'result.json').write_text(json.dumps(result, indent=2))
            print('Private installation verified; mode=email-audit (no publication).', flush=True)
            print('Verified absolute script path:', result['script_path'], flush=True)
        finally:
            # This random temporary file was created by this run, never a user file.
            ftp.delete(target)
        if inventory(ftp) != before:
            raise RuntimeError('Catalog changed during installation; inspect before activation')
        for path in BACKUP.glob('*'):
            if path.suffix in ['.html', '.xml'] and remote(ftp, path.name) != path.read_bytes():
                raise RuntimeError('Public index changed during installation')
    print('Public indexes and catalog inventories unchanged. Temporary installer removed.', flush=True)


if __name__ == '__main__':
    import sys
    try:
        {'prepare': prepare, 'install': install}[sys.argv[1]]()
    except Exception as error:
        # Do not dump response bodies or request data containing credentials.
        print('Installation stopped:', type(error).__name__, flush=True)
        raise SystemExit(1)
