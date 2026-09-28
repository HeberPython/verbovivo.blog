import base64
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from automation.editorial_agent import publisher, lessons, worker


PAYLOAD = b'<html>lesson</html>'
PATH = 'licoes/licao-13-teste.html'


def receipt(path=PATH, payload=PAYLOAD):
    return dict(ok=True, version=1, path=path, size=len(payload),
                sha256=hashlib.sha256(payload).hexdigest())


class UploadReceiptTests(unittest.TestCase):
    def upload_response(self, body, path=PATH, status=200):
        response = MagicMock()
        response.status = status
        response.read.return_value = body
        response.__enter__.return_value = response
        opener = MagicMock()
        opener.open.return_value = response
        with patch.object(publisher, 'settings', SimpleNamespace(editorial_upload_url='https://example.test/upload', admin_token='test')), \
                patch.object(publisher, 'build_opener', return_value=opener), \
                patch.object(publisher.time, 'sleep'):
            publisher.http_upload(path, PAYLOAD)

    def test_incident_regression_http_200_empty_is_failure(self):
        with self.assertRaises(RuntimeError):
            self.upload_response(b'')

    def test_html_invalid_json_and_non_object_are_failures(self):
        for body in [b'<html>OK</html>', b'{broken', b'null', b'[]']:
            with self.subTest(body=body), self.assertRaises(RuntimeError):
                self.upload_response(body)

    def test_wrong_receipt_fields_are_failures(self):
        for field, value in [('ok', False), ('ok', 1), ('path', 'artigos/other.html'),
                             ('size', 1), ('size', True), ('sha256', '0' * 64),
                             ('version', 2)]:
            item = receipt()
            item[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                self.upload_response(json.dumps(item).encode())

    def test_correct_receipt_succeeds(self):
        self.upload_response(json.dumps(receipt()).encode())

    def test_redirect_status_is_not_success(self):
        with self.assertRaises(RuntimeError):
            self.upload_response(json.dumps(receipt()).encode(), status=302)
        with self.assertRaises(RuntimeError):
            publisher.UploadNoRedirect().redirect_request(None, None, 307, '', {}, 'https://other.test')

    def test_home_requires_rebuild_receipt_and_exact_readback(self):
        home = b'rebuilt home from server catalog'
        item = receipt('index.html', home)
        item.update(operation='rebuild_home', request_size=len(PAYLOAD),
                    request_sha256=hashlib.sha256(PAYLOAD).hexdigest())
        response = MagicMock(status=200)
        response.read.return_value = home
        response.__enter__.return_value = response
        with patch.object(publisher, 'build_opener') as opener:
            opener.return_value.open.return_value = response
            publisher.validate_upload_receipt(item, 'index.html', PAYLOAD)
            response.read.return_value = b'wrong home'
            with self.assertRaises(RuntimeError):
                publisher.validate_upload_receipt(item, 'index.html', PAYLOAD)
        with self.assertRaises(RuntimeError):
            publisher.validate_upload_receipt(receipt('index.html'), 'index.html', PAYLOAD)

    def test_http_failure_uses_existing_lesson_ftp_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / 'licoes' / 'test.html'
            page.parent.mkdir()
            page.write_bytes(PAYLOAD)
            config = SimpleNamespace(editorial_upload_url='https://example.test/upload',
                                     ftp_host='test', ftp_port=21, ftp_user='test',
                                     ftp_password='test', ftp_dir='/')
            with patch.object(lessons, 'SITE_DIR', root), patch.object(lessons, 'settings', config), \
                    patch.object(lessons, 'http_upload', side_effect=RuntimeError('empty receipt')), \
                    patch.object(lessons, 'FTP') as ftp:
                lessons.upload_lesson_files([page])
                ftp.return_value.__enter__.return_value.storbinary.assert_called_once()

    def test_fallback_and_verification_failures_leave_email_unread(self):
        message = SimpleNamespace(subject='Lição 13', from_='author@example.test', uid='89')
        for failure in ['FTP fallback failed', 'Publication verification failed']:
            with self.subTest(failure=failure), \
                    patch.object(worker, 'request_authorization_if_needed', return_value=True), \
                    patch.object(worker, 'publish_lesson_from_message', side_effect=RuntimeError(failure)), \
                    patch.object(worker, 'mark_seen') as seen:
                with self.assertRaises(RuntimeError):
                    worker.process_article_message(message)
                seen.assert_not_called()


@unittest.skipUnless(shutil.which('php'), 'PHP runtime required for receiver integration')
class ReceiverIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        for name in ['receber-arquivo-editorial.php', 'home-catalog.php']:
            shutil.copyfile(Path('site') / name, cls.root / name)
        (cls.root / '_private').mkdir()
        (cls.root / '_private/editorial-config.php').write_text("<?php return ['admin_token'=>'test'];")
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.url = f'http://127.0.0.1:{port}/receber-arquivo-editorial.php'
        cls.process = subprocess.Popen(['php', '-S', f'127.0.0.1:{port}', '-t', str(cls.root)],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=.1):
                    break
            except OSError:
                time.sleep(.05)
        else:
            cls.process.terminate()
            cls.process.wait()
            raise RuntimeError('PHP test server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=10)
        cls.temp.cleanup()

    def send(self, path, payload=PAYLOAD, token='test'):
        data = urlencode(dict(token=token, path=path,
                              content_base64=base64.b64encode(payload).decode())).encode()
        try:
            with urlopen(Request(self.url, data=data), timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_traversal_absolute_paths_extensions_and_unknown_targets_rejected(self):
        for path in ['../index.html', '/index.html', 'C:/index.html', 'artigos/../index.html',
                     'artigos\\test.html', 'artigos/test.php', 'licoes/test.html\n',
                     '_private/test.json', 'images/test.png', 'unknown.html']:
            with self.subTest(path=path):
                status, body = self.send(path)
                self.assertGreaterEqual(status, 400)
                self.assertIs(body['ok'], False)

    def test_authentication_and_empty_payload_rejected(self):
        self.assertEqual(self.send(PATH, token='wrong')[0], 404)
        self.assertEqual(self.send(PATH, payload=b'')[0], 400)

    def test_explicit_targets_persist_with_matching_receipts(self):
        for path in [PATH, 'artigos/test.html', 'licoes-escola-dominical.html', 'artigos.html',
                     'feed.xml', 'sitemap.xml', 'images/articles/test.png',
                     '_editorial_drafts/test.json']:
            with self.subTest(path=path):
                status, body = self.send(path)
                self.assertEqual(status, 200)
                self.assertEqual(body, receipt(path))
                self.assertEqual((self.root / path).read_bytes(), PAYLOAD)
        self.assertEqual(list(self.root.rglob('.editorial-upload-*')), [])

    def test_home_still_uses_physical_catalog(self):
        articles = self.root / 'artigos'
        articles.mkdir(exist_ok=True)
        for p in articles.glob('*.html'):
            p.unlink()
        for n in range(1, 6):
            data = dict(headline=f'Title {n}', datePublished=f'2026-09-{n:02}T12:00:00Z')
            (articles / f'post-{n}.html').write_text('<script type="application/ld+json">' + json.dumps(data) + '</script>')
        before = {p.name: p.read_bytes() for p in articles.glob('*.html')}
        (self.root / 'index.html').write_text('<header>KEEP</header><article class="featured">old</article><section class="article-grid">old</section>')
        status, body = self.send('index.html', b'stale checkout - do not publish')
        self.assertEqual(status, 200)
        self.assertEqual(body['operation'], 'rebuild_home')
        stored = (self.root / 'index.html').read_bytes()
        self.assertEqual(body['sha256'], hashlib.sha256(stored).hexdigest())
        self.assertEqual(body['size'], len(stored))
        self.assertIn(b'<header>KEEP</header>', stored)
        self.assertNotIn(b'stale checkout', stored)
        self.assertNotIn(b'post-1.html', stored)
        self.assertEqual(before, {p.name: p.read_bytes() for p in articles.glob('*.html')})
