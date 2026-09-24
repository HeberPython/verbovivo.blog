"""User-authorized recovery of four known articles; preserve images and await approval."""
from dataclasses import fields
from ftplib import FTP
from io import BytesIO
import json
from pathlib import Path
import secrets
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .ai import refine_with_openai
from .config import settings
from .mail import send_review_email
from .models import ArticleDraft
from .publisher import prefer_ipv4, upload_review_draft
from .text_quality import EditorialTextError, validate_reflection


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('Authenticated recovery cannot redirect')


def connect():
    ftp = FTP()
    ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
    ftp.login(settings.ftp_user, settings.ftp_password)
    ftp.cwd(settings.ftp_dir)
    return ftp


def main():
    name = 'recover-text-' + secrets.token_hex(16) + '.php'
    payload = Path('automation/recover-four-texts.php').read_bytes()
    with connect() as ftp:
        ftp.storbinary('STOR ' + name, BytesIO(payload))
        check = BytesIO()
        ftp.retrbinary('RETR ' + name, check.write)
        if check.getvalue() != payload:
            raise RuntimeError('Recovery helper verification failed')

    def call(action, **data):
        request = Request('https://verbovivo.blog/' + name, method='POST',
                          data=json.dumps(dict(action=action, **data)).encode(),
                          headers={'Content-Type': 'application/json', 'X-Editorial-Token': settings.admin_token})
        with prefer_ipv4(), build_opener(NoRedirect()).open(request, timeout=180) as response:
            return json.load(response)

    try:
        state = call('withdraw')
        if state['before_count'] - state['after_count'] != 4 or len(state['originals']) != 4:
            raise RuntimeError('Unexpected withdrawal count')
        print(f"Verified private backup: {state['backup']}; articles {state['before_count']} -> {state['after_count']}; other files and four images unchanged.", flush=True)
        errors = []
        for old_id, original in state['originals'].items():
            if state['notified'].get(old_id):
                print('Already sent for new approval: ' + original['slug'], flush=True)
                continue
            cached = state['replacements'].get(old_id)
            try:
                if cached:
                    draft = ArticleDraft(**{f.name: cached[f.name] for f in fields(ArticleDraft) if f.name in cached})
                else:
                    draft = refine_with_openai(original['source_text'], original['source_subject'], original['sender'])
                    # Preserve identity, authorship and image; only editorial text is regenerated.
                    draft.slug = original['slug']
                    draft.source_text = original['source_text']
                    draft.author = original['author']
                    draft.author_socials = original.get('author_socials', {})
                    draft.image_filename = original['image_filename']
                    draft.image_prompt = original.get('image_prompt', '')
                    draft.local_image_path = ''
                    state = call('remember', id=old_id, draft=draft.__dict__)
                validate_reflection(draft.source_text, draft.body_html)
                upload_review_draft(draft)
                recipient = settings.approver_email or original['sender']
                send_review_email(recipient, draft, f'{settings.approval_base_url}/revisao.php?token={draft.token}')
                state = call('remember', id=old_id, notified=True)
                print(f'Reprepared for approval, original image retained: {draft.slug}', flush=True)
            except EditorialTextError as exc:
                errors.append(original['slug'])
                print(f'Recovery pending: {original["slug"]}: {exc}', flush=True)
        if errors:
            raise EditorialTextError(f'{len(errors)} original(s) safely retained in private recovery queue; generation blocked.')
        print('Four new approval emails accepted by SMTP. Nothing republished.', flush=True)
    finally:
        with connect() as ftp:
            ftp.delete(name)


if __name__ == '__main__':
    main()
