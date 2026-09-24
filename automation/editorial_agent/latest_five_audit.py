"""One-off read-only audit; no generation, publication or mailbox changes."""
from ftplib import FTP
from io import BytesIO
from html import unescape
from pathlib import PurePosixPath
import json
import re

from .config import settings
from .content import paragraphs_from_text

IDS = ['a4bf10017c3d3fd5', '3f1963bd6735c1d6', '1d0c5a02f63a04fb',
       'd004cd9587f2998f', '59b1a380d02e3b7c']


def read(ftp, path):
    output = BytesIO()
    ftp.retrbinary('RETR ' + path, output.write)
    return output.getvalue()


def plain(value):
    return unescape(re.sub(r'<[^>]+>', ' ', value))


def main():
    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.cwd(settings.ftp_dir)
        found = set()
        for entry in ftp.nlst('_editorial_drafts'):
            name = PurePosixPath(entry).name
            if not name.endswith('.json'):
                continue
            data = json.loads(read(ftp, '_editorial_drafts/' + name))
            draft_id = data.get('id')
            if draft_id not in IDS:
                continue
            found.add(draft_id)
            source = data.get('source_text', '')
            body = data.get('body_html', '')
            blocks = paragraphs_from_text(source)
            result = {key: data.get(key) for key in
                      ['id', 'title', 'slug', 'source_subject', 'status', 'created_at']}
            result.update(source_words=len(source.split()),
                          body_words=len(plain(body).split()),
                          source_blocks=len(blocks),
                          fallback_heading='<h2>Para meditar</h2>' in body,
                          first_eight_words=len(' '.join(blocks[:8]).split()),
                          source_end=source[-700:])
            print('AUDIT_RESULT ' + json.dumps(result, ensure_ascii=False), flush=True)
            if draft_id == '59b1a380d02e3b7c':
                print('AUDIT_FIFTH_SOURCE ' + json.dumps(source, ensure_ascii=False), flush=True)
        print('AUDIT_FOUND ' + str(len(found)), flush=True)


if __name__ == '__main__':
    main()
