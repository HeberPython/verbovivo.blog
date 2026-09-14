import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image
from automation.editorial_agent.review_image import choose


class ReviewImageTests(unittest.TestCase):
    def test_selects_only_exact_pending_subject(self):
        target = ('one', b'one', {'source_subject': 'EXPERIMENTARAM', 'status': 'pending_review'})
        others = [('other', b'other', {'source_subject': 'EXPERIMENTARAM', 'status': 'approved'}),
                  ('two', b'two', {'source_subject': 'OUTRO', 'status': 'pending_review'})]
        self.assertEqual(choose(others + [target], 'experimentaram'), target)
        with self.assertRaises(RuntimeError):
            choose(others, 'EXPERIMENTARAM')
        with self.assertRaises(RuntimeError):
            choose([target, target], 'EXPERIMENTARAM')

    @unittest.skipUnless(shutil.which('php'), 'PHP integration runs in GitHub')
    def test_authenticated_image_only_update_with_private_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            site = parent / 'public_html'
            for directory in ['_private', '_editorial_drafts', 'images/articles', 'artigos']:
                (site / directory).mkdir(parents=True)
            (site / '_private/editorial-config.php').write_text("<?php return ['admin_token'=>'test-only'];")
            shutil.copyfile('automation/review-image-update.php', site / 'update.php')
            token = 'test-only-token-1234567890'
            draft = {'token': token, 'slug': 'test-article', 'status': 'pending_review',
                     'image_filename': 'old.png', 'body_html': '<p>Preserved text</p>', 'extra_field': 3}
            path = site / '_editorial_drafts' / (token + '.json')
            path.write_text(json.dumps(draft))
            raw = path.read_bytes()
            (site / 'images/articles/old.png').write_bytes(b'old image backup fixture')
            buffer = BytesIO()
            Image.new('RGB', (8, 8), 'green').save(buffer, format='PNG')
            payload = {'token': token, 'filename': 'review-' + 'a' * 32 + '.png',
                       'expected_sha256': hashlib.sha256(raw).hexdigest(),
                       'image_base64': base64.b64encode(buffer.getvalue()).decode()}
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            server = subprocess.Popen(['php', '-S', f'127.0.0.1:{port}', '-t', str(site)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = f'http://127.0.0.1:{port}/update.php'
            def send(data=payload, auth='test-only'):
                return urlopen(Request(url, data=json.dumps(data).encode(), headers={'X-Editorial-Token': auth}), timeout=5)
            try:
                for _ in range(40):
                    try:
                        urlopen(url, timeout=1)
                    except HTTPError:
                        break
                    except URLError:
                        time.sleep(.1)
                for data, auth in [(payload, 'wrong'), (dict(payload, expected_sha256='stale'), 'test-only')]:
                    with self.assertRaises(HTTPError):
                        send(data, auth)
                    self.assertEqual(path.read_bytes(), raw)
                (site / 'artigos/test-article.html').write_text('already published')
                with self.assertRaises(HTTPError):
                    send()
                self.assertEqual(path.read_bytes(), raw)
                (site / 'artigos/test-article.html').unlink()
                with send() as response:
                    result = json.load(response)
                self.assertFalse(result['published'])
                self.assertEqual(json.loads(path.read_text()), dict(draft, image_filename=payload['filename']))
                self.assertEqual((parent / result['backup'] / 'draft.json').read_bytes(), raw)
                if __import__('os').name != 'nt':
                    self.assertEqual((parent / result['backup'] / 'draft.json').stat().st_mode & 0o777, 0o600)
                self.assertEqual(list((site / 'artigos').iterdir()), [])
                self.assertEqual((site / 'images/articles/old.png').read_bytes(), b'old image backup fixture')
            finally:
                server.terminate()
                server.wait(timeout=5)
