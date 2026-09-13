"""Linux/PHP integration tests. Credentials and site are temporary fixtures only."""
import fcntl
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class ModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.site = self.parent / 'public_html'
        (self.site / '_private').mkdir(parents=True)
        (self.site / '_private/editorial-config.php').write_text("<?php return ['admin_token'=>'test-only'];")
        (self.site / 'index.html').write_text('unchanged publication')
        self.directory = self.parent / '_verbovivo_scheduler'
        self.directory.mkdir(mode=0o700)
        self.config = self.directory / 'scheduler-config.json'
        self.original = {'github_token': 'github_pat_fixture_only', 'enabled': True,
                         'command': 'email-audit', 'preserve_other_fields': 42}
        self.config.write_text(json.dumps(self.original))
        self.config.chmod(0o600)
        self.before = self.config.read_bytes()
        here = Path(__file__).parent
        shutil.copyfile(here / 'dispatch-editorial.php', self.directory / 'dispatch-editorial.php')
        shutil.copyfile(here / 'set-mode-once.php', self.site / 'mode.php')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        self.server = subprocess.Popen(['php', '-S', f'127.0.0.1:{port}', '-t', str(self.site)],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop_server)
        self.url = f'http://127.0.0.1:{port}/mode.php'
        for _ in range(40):
            try:
                urlopen(self.url, timeout=1)
            except HTTPError as error:
                self.assertEqual(error.code, 404)
                break
            except URLError:
                time.sleep(.1)
        else:
            self.fail('PHP test server did not start')

    def stop_server(self):
        self.server.terminate()
        self.server.wait(timeout=5)

    def send(self, mode='all', token='test-only'):
        request = Request(self.url, method='POST', data=json.dumps({'command': mode}).encode(),
                          headers={'X-Editorial-Token': token, 'Content-Type': 'application/json'})
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def rejected(self, status, **kwargs):
        with self.assertRaises(HTTPError) as error:
            self.send(**kwargs)
        self.assertEqual(error.exception.code, status)
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_backup_switch_idempotence_and_rollback(self):
        result = self.send()
        self.assertEqual(result['mode'], 'all')
        self.assertEqual(result['previous_mode'], 'email-audit')
        self.assertTrue(result['outside_public_html'])
        self.assertEqual(result['config_permissions'], '600')
        self.assertNotIn('github_pat_', json.dumps(result))
        self.assertEqual(json.loads(self.config.read_text()), dict(self.original, command='all'))
        backup = self.directory / result['backup_name']
        self.assertEqual((backup / 'scheduler-config.json').read_bytes(), self.before)
        self.assertEqual((backup / 'scheduler-config.json').stat().st_mode & 0o777, 0o600)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        self.assertEqual((backup / 'dispatch-editorial.php').read_bytes(),
                         (self.directory / 'dispatch-editorial.php').read_bytes())
        self.assertIsNone(self.send()['backup_name'])
        self.assertEqual(len(list(self.directory.glob('before-mode-*'))), 1)
        self.assertEqual(self.send('email-audit')['mode'], 'email-audit')
        self.assertEqual(json.loads(self.config.read_text()), self.original)
        self.assertEqual((self.site / 'index.html').read_text(), 'unchanged publication')

    def test_reject_wrong_auth(self):
        self.rejected(404, token='wrong')

    def test_reject_invalid_command(self):
        self.rejected(400, mode='repair-content')

    def test_reject_modified_dispatcher(self):
        (self.directory / 'dispatch-editorial.php').write_text('<?php echo "changed";')
        self.rejected(409)

    def test_reject_insecure_config(self):
        self.config.chmod(0o644)
        self.rejected(409)

    def test_reject_symlink_config(self):
        target = self.directory / 'real-config.json'
        self.config.rename(target)
        self.config.symlink_to(target)
        self.rejected(409)

    def test_reject_active_dispatcher(self):
        with (self.directory / 'scheduler.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.rejected(409)

    def test_workflow_uses_one_scheduler_and_shared_concurrency(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / '.github/workflows/editorial-agent.yml').read_text()
        self.assertNotIn('  schedule:', workflow)
        self.assertNotIn("github.event_name == 'schedule'", workflow)
        self.assertIn('  workflow_dispatch:', workflow)
        self.assertIn('  cancel-in-progress: false', workflow)
        self.assertIn('group: verbo-vivo-editorial-agent', workflow)


if __name__ == '__main__':
    unittest.main()
