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


TARGETS = {'a4bf10017c3d3fd5': 'a-boa-obra', '3f1963bd6735c1d6': 'deus-da-presenca',
           '1d0c5a02f63a04fb': 'construtores-de-altares', 'd004cd9587f2998f': 'o-coracao-que-confessa'}


class RecoveryTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('php'), 'PHP integration runs in GitHub')
    def test_withdraws_only_four_and_preserves_backup_images_and_other_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'public_html'
            for directory in ['_private', '_editorial_drafts', 'artigos', 'licoes', 'images/articles']:
                (root / directory).mkdir(parents=True)
            (root / '_private/editorial-config.php').write_text("<?php return ['admin_token'=>'test'];")
            shutil.copyfile('automation/recover-four-texts.php', root / 'recover.php')
            shutil.copyfile('site/home-catalog.php', root / 'home-catalog.php')
            slugs = list(TARGETS.values()) + ['kept-one', 'kept-two', 'kept-three', 'kept-four']
            for slug in slugs:
                schema = {'headline': slug, 'datePublished': '2026-09-24T12:00:00Z', 'image': 'image.png'}
                (root / 'artigos' / (slug + '.html')).write_text('<script type="application/ld+json">' + json.dumps(schema) + '</script>')
            for ident, slug in TARGETS.items():
                data = {'id': ident, 'slug': slug, 'status': 'approved', 'source_text': 'complete original', 'image_filename': slug + '.png'}
                (root / '_editorial_drafts' / (ident + '.json')).write_text(json.dumps(data))
                (root / 'images/articles' / (slug + '.png')).write_bytes(b'original image')
            (root / 'licoes/licao-01.html').write_text('lesson unchanged')
            cards = ''.join(f'<article class="article-card"><a href="artigos/{s}.html">{s}</a></article>' for s in slugs)
            (root / 'artigos.html').write_text(cards)
            (root / 'index.html').write_text('<article class="featured">old</article><section class="article-grid">old</section>')
            (root / 'feed.xml').write_text('<rss><channel>' + ''.join(f'<item><link>https://verbovivo.blog/artigos/{s}.html</link></item>' for s in slugs) + '</channel></rss>')
            (root / 'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>https://verbovivo.blog/artigos/{s}.html</loc></url>' for s in slugs) + '</urlset>')
            original = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            server = subprocess.Popen(['php', '-S', f'127.0.0.1:{port}', '-t', str(root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = f'http://127.0.0.1:{port}/recover.php'
            def call(action='withdraw', auth='test'):
                with urlopen(Request(url, data=json.dumps({'action': action}).encode(), headers={'X-Editorial-Token': auth}), timeout=10) as response:
                    return json.load(response)
            try:
                for _ in range(40):
                    try:
                        urlopen(url, timeout=1)
                    except HTTPError:
                        break
                    except URLError:
                        time.sleep(.1)
                with self.assertRaises(HTTPError):
                    call(auth='wrong')
                result = call()
                self.assertEqual((result['before_count'], result['after_count']), (8, 4))
                self.assertEqual(call(), result)
                self.assertEqual(call('inspect'), result)
                backup = Path(temp) / result['backup'] / 'files'
                for name, data in original.items():
                    if name.startswith('_private/'):
                        continue
                    self.assertEqual((backup / name).read_bytes(), data)
                for ident, slug in TARGETS.items():
                    self.assertFalse((root / 'artigos' / (slug + '.html')).exists())
                    self.assertFalse((root / '_editorial_drafts' / (ident + '.json')).exists())
                    self.assertEqual((root / 'images/articles' / (slug + '.png')).read_bytes(), b'original image')
                for slug in slugs[4:]:
                    self.assertEqual((root / 'artigos' / (slug + '.html')).read_bytes(), original['artigos/' + slug + '.html'])
                    self.assertIn(slug, (root / 'index.html').read_text())
                self.assertEqual((root / 'licoes/licao-01.html').read_text(), 'lesson unchanged')
            finally:
                server.terminate()
                server.wait(timeout=5)
