"""Manual image-only operation; never publishes or reads/marks inbox messages."""
from dataclasses import fields
from ftplib import FTP
from io import BytesIO
from pathlib import Path, PurePosixPath
import base64
import hashlib
import json
import os
import secrets
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

from PIL import Image
from .ai import generate_cover_image_with_gemini
from .config import settings
from .mail import send_review_email
from .models import ArticleDraft

OUT = Path('automation/_diagnostics/pending-review-image')


def read(ftp, path):
    buffer = BytesIO()
    ftp.retrbinary('RETR ' + path, buffer.write)
    return buffer.getvalue()


def connect():
    ftp = FTP()
    ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
    ftp.login(settings.ftp_user, settings.ftp_password)
    ftp.cwd(settings.ftp_dir)
    return ftp


def choose(records, subject):
    matches = [(path, raw, data) for path, raw, data in records
               if str(data.get('source_subject', '')).strip().casefold() == subject.strip().casefold()
               and data.get('status') == 'pending_review']
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one pending draft; found ' + str(len(matches)))
    return matches[0]


def load_target(ftp, subject):
    records = []
    for entry in ftp.nlst('_editorial_drafts'):
        name = PurePosixPath(entry).name
        if name.endswith('.json'):
            path = '_editorial_drafts/' + name
            raw = read(ftp, path)
            data = json.loads(raw)
            records.append((path, raw, data))
    return choose(records, subject)


def model(data):
    return ArticleDraft(**{field.name: data[field.name] for field in fields(ArticleDraft) if field.name in data})


def png_bytes(payload):
    # Gemini can return JPEG bytes even when the requested local filename is PNG.
    with Image.open(BytesIO(payload)) as image:
        image.load()
        if image.format == 'PNG':
            return payload
        output = BytesIO()
        image.convert('RGB').save(output, format='PNG')
        return output.getvalue()


def fingerprints(ftp):
    result = {}
    for path in ['index.html', 'artigos.html', 'feed.xml', 'sitemap.xml', 'licoes-escola-dominical.html']:
        result[path] = hashlib.sha256(read(ftp, path)).hexdigest()
    for directory in ['artigos', 'licoes', '_editorial_drafts']:
        for entry in ftp.nlst(directory):
            name = PurePosixPath(entry).name
            if name.endswith(('.html', '.json')):
                path = directory + '/' + name
                result[path] = hashlib.sha256(read(ftp, path)).hexdigest()
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('Authenticated update cannot redirect')


def main():
    subject = os.environ['REVIEW_SUBJECT']
    action = os.environ['REVIEW_ACTION']
    with connect() as ftp:
        path, raw, data = load_target(ftp, subject)
        print(json.dumps({key: data.get(key) for key in ['id', 'source_subject', 'title', 'created_at', 'status', 'excerpt', 'image_prompt']}, ensure_ascii=False), flush=True)
        if action == 'inspect':
            print('ARTICLE_CONTEXT:', data.get('body_html', ''), flush=True)
            return
        if action == 'generate':
            OUT.mkdir(parents=True, exist_ok=True)
            old_name = data['image_filename']
            if PurePosixPath(old_name).name != old_name:
                raise RuntimeError('Invalid old image name')
            old_image = read(ftp, 'images/articles/' + old_name)
            (OUT / ('previous' + Path(old_name).suffix)).write_bytes(old_image)
        elif action == 'apply':
            plan = json.loads((OUT / 'plan.json').read_text())
            if plan['subject'] != subject or plan['id'] != data['id'] or plan['draft_sha256'] != hashlib.sha256(raw).hexdigest():
                raise RuntimeError('Draft changed after generation; stop')
            before = fingerprints(ftp)
        else:
            raise ValueError('Invalid action')
    if action == 'generate':
        draft = model(data)
        if os.getenv('REVIEW_DIRECTION', '').strip():
            draft.image_prompt = os.environ['REVIEW_DIRECTION'].strip()
        draft.image_filename = 'review-' + secrets.token_hex(16) + '.png'
        generated = generate_cover_image_with_gemini(draft, OUT)
        if generated is None:
            raise RuntimeError('Gemini did not generate an image; original draft unchanged')
        with Image.open(generated) as image:
            image.verify()
        (OUT / 'plan.json').write_text(json.dumps({
            'id': data['id'], 'subject': subject, 'draft_sha256': hashlib.sha256(raw).hexdigest(),
            'filename': draft.image_filename, 'image_sha256': hashlib.sha256(generated.read_bytes()).hexdigest(),
            'title': data['title'], 'direction': draft.image_prompt,
        }, ensure_ascii=False, indent=2))
        print('Generated preview only. Draft, approval status and public site unchanged.', flush=True)
        return
    image_path = OUT / plan['filename']
    image_bytes = image_path.read_bytes()
    if hashlib.sha256(image_bytes).hexdigest() != plan['image_sha256']:
        raise RuntimeError('Image artifact changed')
    image_bytes = png_bytes(image_bytes)
    bootstrap = Path('automation/review-image-update.php').read_bytes()
    target = 'review-image-' + secrets.token_hex(12) + '.php'
    with connect() as ftp:
        if target in ftp.nlst():
            raise RuntimeError('Temporary filename collision')
        try:
            ftp.storbinary('STOR ' + target, BytesIO(bootstrap))
            if read(ftp, target) != bootstrap:
                raise RuntimeError('Temporary updater verification failed')
            payload = {'token': data['token'], 'expected_sha256': plan['draft_sha256'],
                       'filename': plan['filename'], 'image_base64': base64.b64encode(image_bytes).decode()}
            request = Request('https://verbovivo.blog/' + target, method='POST', data=json.dumps(payload).encode(),
                              headers={'Content-Type': 'application/json', 'X-Editorial-Token': settings.admin_token})
            with build_opener(NoRedirect()).open(request, timeout=60) as response:
                result = json.load(response)
            print('Private backup:', result['backup'], flush=True)
        finally:
            ftp.delete(target)
        updated = json.loads(read(ftp, path))
        expected = dict(data, image_filename=plan['filename'])
        if updated != expected:
            raise RuntimeError('Unexpected draft change')
        if read(ftp, 'images/articles/' + plan['filename']) != image_bytes:
            raise RuntimeError('Uploaded image differs')
        after = fingerprints(ftp)
        before.pop(path)
        after.pop(path)
        if before != after:
            raise RuntimeError('Other draft or publication changed; inspect before notifying')
    review_url = settings.approval_base_url.rstrip('/') + '/revisao.php?token=' + data['token']
    with build_opener(NoRedirect()).open(review_url, timeout=40) as response:
        page = response.read().decode('utf-8')
    if plan['filename'] not in page:
        raise RuntimeError('Review page does not show the updated image')
    send_review_email(settings.approver_email or data['sender'], model(updated), review_url)
    print('One image replaced; text, token and pending_review unchanged. Other drafts and public pages unchanged. Review email accepted by SMTP.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Image operation stopped:', type(error).__name__, flush=True)
        if isinstance(error, HTTPError):
            print('HTTP status:', error.code, flush=True)
        raise SystemExit(1)
