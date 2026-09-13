"""Switch the existing private scheduler; never deploy site content or new secrets."""
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import sys
from urllib.request import Request, build_opener
from urllib.error import HTTPError

from install_https import BASE, HERE, NoRedirect, connect, inventory, remote

BACKUP = Path('automation/_backups/scheduler-activation')
ROOTS = ['index.html', 'artigos.html', 'feed.xml', 'sitemap.xml', 'licoes-escola-dominical.html']


def snapshot(ftp):
    catalog = inventory(ftp)
    files = {name: remote(ftp, name) for name in ROOTS}
    for directory in ['artigos', 'licoes']:
        for entry in catalog[directory]:
            name = PurePosixPath(entry).name
            if name.endswith('.html'):
                path = directory + '/' + name
                files[path] = remote(ftp, path)
    if not any(name.startswith('artigos/') for name in files) or not any(name.startswith('licoes/') for name in files):
        raise RuntimeError('Empty publication inventory')
    return catalog, files


def manifest(catalog, files):
    return {'catalog': catalog, 'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}


def prepare():
    with connect() as ftp:
        catalog, files = snapshot(ftp)
        for name, data in files.items():
            path = BACKUP / 'before' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (BACKUP / 'manifest.json').write_text(json.dumps(manifest(catalog, files), indent=2))
    print(f'Backed up {len(files)} public files and catalog inventory. No remote writes.', flush=True)


def activate(mode):
    if mode not in ['all', 'email-audit']:
        raise ValueError('Invalid scheduler mode')
    before = json.loads((BACKUP / 'manifest.json').read_text())
    bootstrap = (HERE / 'set-mode-once.php').read_bytes()
    target = 'scheduler-mode-' + secrets.token_hex(12) + '.php'
    with connect() as ftp:
        catalog, files = snapshot(ftp)
        if manifest(catalog, files) != before:
            raise RuntimeError('Public content changed since backup; stop')
        if target in ftp.nlst():
            raise RuntimeError('Unexpected bootstrap collision')
        try:
            ftp.storbinary('STOR ' + target, BytesIO(bootstrap))
            if remote(ftp, target) != bootstrap:
                raise RuntimeError('Bootstrap verification failed')
            request = Request(BASE + target, method='POST', data=json.dumps({'command': mode}).encode(), headers={
                'Content-Type': 'application/json', 'X-Editorial-Token': os.environ['EDITORIAL_ADMIN_TOKEN'],
            })
            try:
                with build_opener(NoRedirect()).open(request, timeout=60) as response:
                    result = json.load(response)
            except HTTPError as error:
                raise RuntimeError('HTTPS mode update failed; HTTP ' + str(error.code)) from None
            (BACKUP / 'result.json').write_text(json.dumps(result, indent=2))
            if result.get('mode') != mode or result.get('config_permissions') != '600' or not result.get('outside_public_html'):
                raise RuntimeError('Private configuration verification failed')
            if result.get('script_sha256') != hashlib.sha256((HERE / 'dispatch-editorial.php').read_bytes()).hexdigest():
                raise RuntimeError('Dispatcher changed unexpectedly')
            print('Private scheduler command verified:', mode, flush=True)
            print('Private rollback backup:', result.get('backup_name'), flush=True)
        finally:
            ftp.delete(target)
        catalog, files = snapshot(ftp)
        after = manifest(catalog, files)
        (BACKUP / 'after.json').write_text(json.dumps(after, indent=2))
        if after != before:
            raise RuntimeError('Public content comparison failed')
    print(f'All {len(files)} public files byte-identical; catalog unchanged; temporary updater removed.', flush=True)


if __name__ == '__main__':
    try:
        if sys.argv[1] == 'prepare':
            prepare()
        elif sys.argv[1] == 'activate':
            activate(sys.argv[2])
        else:
            raise ValueError('Invalid operation')
    except Exception as error:
        print('Scheduler activation stopped:', type(error).__name__, flush=True)
        raise SystemExit(1)
