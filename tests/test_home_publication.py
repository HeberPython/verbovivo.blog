import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automation.editorial_agent.publisher import trim_home_articles
from automation.editorial_agent.repair_home import home_links


class HomePublicationTests(unittest.TestCase):
    def test_python_does_not_count_featured_duplicate_as_fourth_article(self):
        html = '<article class="featured"><a href="a">A</a></article><section class="article-grid">'
        html += ''.join('<article class="article-card"><a href="' + s + '">X</a></article>' for s in 'abbcde')
        html += '</section>'
        self.assertEqual(home_links(trim_home_articles(html)), list('abcd'))

    def test_all_live_writers_use_server_catalog(self):
        for name in ['revisao.php', 'gestor-artigos.php', 'receber-arquivo-editorial.php']:
            text = (Path('site') / name).read_text(encoding='utf-8')
            self.assertIn('refresh_current_home(__DIR__)', text)
            self.assertNotIn('array_slice($cards[0], 0, 2)', text)

    @unittest.skipUnless(shutil.which('php'), 'PHP is executed in the deployment workflow')
    def test_php_selects_newest_four_idempotently_without_modifying_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'artigos').mkdir()
            helper = Path('site/home-catalog.php').resolve()
            template = '<header>KEEP</header><article class="featured">old</article><section class="article-grid">old</section><footer>KEEP</footer>'
            (root / 'index.html').write_text(template)
            for number in range(1, 7):
                # Filename order is deliberately the opposite of date order.
                data = {'headline': str(number), 'datePublished': f'2026-09-{number:02}T12:00:00-03:00', 'image': '/images/test.jpg'}
                (root / 'artigos' / f'post-{7-number}.html').write_text('<script type="application/ld+json">' + json.dumps(data) + '</script>')
            before = {p.name: p.read_bytes() for p in (root / 'artigos').iterdir()}
            command = ['php', '-r', 'require $argv[1]; refresh_current_home($argv[2]);', str(helper), tmp]
            subprocess.run(command, check=True, capture_output=True)
            first = (root / 'index.html').read_text()
            self.assertEqual(home_links(first), [f'artigos/post-{n}.html' for n in range(1, 5)])
            self.assertIn('<header>KEEP</header>', first)
            self.assertIn('<footer>KEEP</footer>', first)
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(first, (root / 'index.html').read_text())
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / 'artigos').iterdir()})
            (root / 'artigos/broken.html').write_text('<html>missing date</html>')
            result = subprocess.run(command, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(first, (root / 'index.html').read_text())
