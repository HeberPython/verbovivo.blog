import base64
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


class InstallTests(unittest.TestCase):
    def test_auth_private_location_permissions_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            site = parent / 'public_html'
            (site / '_private').mkdir(parents=True)
            (site / '_private/editorial-config.php').write_text("<?php return ['admin_token'=>'test-only'];")
            shutil.copyfile(Path(__file__).with_name('install-once.php'), site / 'install.php')
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            server = subprocess.Popen(['php', '-S', f'127.0.0.1:{port}', '-t', str(site)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = f'http://127.0.0.1:{port}/install.php'
            try:
                for _ in range(40):
                    try:
                        urlopen(url, timeout=1)
                    except HTTPError as error:
                        self.assertEqual(error.code, 404)
                        break
                    except URLError:
                        time.sleep(.1)
                else:
                    self.fail('PHP test server did not start')
                data = json.dumps({'script': base64.b64encode(b'<?php echo "test";').decode(),
                                   'github_token': 'github_pat_test_only'}).encode()
                def send(token):
                    return urlopen(Request(url, method='POST', data=data, headers={'X-Editorial-Token': token}), timeout=5)
                with self.assertRaises(HTTPError) as error:
                    send('wrong')
                self.assertEqual(error.exception.code, 404)
                with send('test-only') as response:
                    result = json.load(response)
                self.assertTrue(result['outside_public_html'])
                self.assertEqual(result['config_permissions'], '600')
                self.assertEqual(result['mode'], 'email-audit')
                config = parent / '_verbovivo_scheduler/scheduler-config.json'
                before = config.read_bytes()
                with self.assertRaises(HTTPError) as error:
                    send('test-only')
                self.assertEqual(error.exception.code, 409)
                self.assertEqual(before, config.read_bytes())
                self.assertNotIn('github_pat_', json.dumps(result))
            finally:
                server.terminate()
                server.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
