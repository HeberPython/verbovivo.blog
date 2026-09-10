"""Read-only diagnostics. Never print or persist credentials."""
from ftplib import FTP_TLS
from io import BytesIO
import os
import ssl
from urllib.request import Request, urlopen
import json


def main():
    token = os.environ['EDITORIAL_DISPATCH_TOKEN'].strip()
    request = Request(
        'https://api.github.com/repos/HeberPython/verbovivo.blog/actions/workflows/editorial-agent.yml',
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'VerboVivo-Scheduler-Setup', 'X-GitHub-Api-Version': '2022-11-28'},
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    assert result['state'] == 'active', 'Editorial workflow is not active'
    print('Dedicated token: workflow read access OK; no dispatch requested.', flush=True)
    ftp = FTP_TLS(context=ssl.create_default_context())
    try:
        ftp.connect(os.environ['HOSTINGER_FTP_HOST'], int(os.getenv('HOSTINGER_FTP_PORT') or 21), timeout=45)
        ftp.login(os.environ['HOSTINGER_FTP_USER'], os.environ['HOSTINGER_FTP_PASSWORD'])
        ftp.prot_p()
        ftp.cwd(os.getenv('HOSTINGER_FTP_DIR') or '/')
        root = ftp.pwd()
        print('Verified encrypted FTPS connection. Site directory:', root, flush=True)
        ftp.cwd('..')
        parent = ftp.pwd()
        print('Parent directory:', parent, 'different from site:', parent != root, flush=True)
        print('Directory names:', ', '.join(sorted(ftp.nlst())[:20]), flush=True)
        ftp.cwd(root)
        data = BytesIO()
        ftp.retrbinary('RETR _private/.htaccess', data.write)
        protected = b'Require all denied' in data.getvalue()
        print('Existing _private HTTP deny directive:', protected, flush=True)
        print('Read-only inspection completed. No server file changed.', flush=True)
    finally:
        ftp.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Exceptions may include URLs or private data; output only their type.
        print('Access check failed:', type(error).__name__, flush=True)
        raise SystemExit(1)
