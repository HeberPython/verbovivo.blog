"""Authorized Phase 2A extraction only: no publication or mailbox flag writes."""
from email import policy
from email.parser import BytesParser
import hashlib
import imaplib
import json
from pathlib import Path
from types import SimpleNamespace

from automation.editorial_agent.config import settings
from automation.editorial_agent.lessons import gemini_json_from_images, lesson_number_from_subject


RAW_HASH = '744028a426a54c87d6363b975e5c527742e2d02edf59321d8eb739ce9f229eb1'
MESSAGE_ID_HASH = '4d4b127c055264f841ca4c53dfbee1c1ae0020894d0f53f2297150aa31386ab9'
OUTPUT = Path('automation/_backups/phase2a-lesson13-extraction')


def extract():
    if OUTPUT.exists():
        raise RuntimeError('Extraction output already exists; preserve previous evidence')
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port, timeout=30) as mailbox:
        mailbox.login(settings.imap_user, settings.imap_password)
        status, _ = mailbox.select('INBOX', readonly=True)
        if status != 'OK':
            raise RuntimeError('Read-only mailbox unavailable')
        status, pending = mailbox.uid('search', None, 'UNSEEN')
        if status != 'OK' or pending != [b'89']:
            raise RuntimeError('Unexpected pending messages; extraction stopped')
        status, fetched = mailbox.uid('fetch', '89', '(UID FLAGS BODY.PEEK[])')
        parts = [part for part in fetched if isinstance(part, tuple)]
        if status != 'OK' or len(parts) != 1 or b'FLAGS ()' not in parts[0][0]:
            raise RuntimeError('Original unread message not confirmed')
        raw = parts[0][1]
        if hashlib.sha256(raw).hexdigest() != RAW_HASH:
            raise RuntimeError('Original message hash mismatch')
        message = BytesParser(policy=policy.default).parsebytes(raw)
        if hashlib.sha256(str(message['Message-ID']).encode()).hexdigest() != MESSAGE_ID_HASH:
            raise RuntimeError('Message-ID identity mismatch')
        subject = str(message['Subject'])
        if lesson_number_from_subject(subject) != 13:
            raise RuntimeError('Unexpected lesson subject')
        attachments = [SimpleNamespace(filename=part.get_filename() or 'photo.jpg',
                                       content_type=part.get_content_type(),
                                       payload=part.get_payload(decode=True))
                       for part in message.walk() if part.get_content_type().startswith('image/')]
        if len(attachments) != 7 or any(a.content_type != 'image/jpeg' or not a.payload for a in attachments):
            raise RuntimeError('Seven original JPEG images not confirmed')

    result = gemini_json_from_images(SimpleNamespace(subject=subject, attachments=attachments), 13)
    if not isinstance(result, dict) or result.get('number') != 13 or not result.get('title'):
        raise RuntimeError('Extraction did not return Lesson 13')
    encoded = json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8')
    OUTPUT.mkdir(parents=True)
    (OUTPUT / 'lesson13.json').write_bytes(encoded)
    if (OUTPUT / 'lesson13.json').read_bytes() != encoded:
        raise RuntimeError('Extraction artifact readback failed')
    manifest = dict(raw_sha256=RAW_HASH, message_id_sha256=MESSAGE_ID_HASH,
                    image_sha256=[hashlib.sha256(a.payload).hexdigest() for a in attachments],
                    result_sha256=hashlib.sha256(encoded).hexdigest(),
                    result_size=len(encoded), model=settings.gemini_text_model,
                    published=False, marked_read=False)
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Lesson 13 extracted from seven verified images; no publication or mailbox writes.')


if __name__ == '__main__':
    try:
        extract()
    except Exception as error:
        print('Controlled extraction stopped:', type(error).__name__)
        raise SystemExit(1)
