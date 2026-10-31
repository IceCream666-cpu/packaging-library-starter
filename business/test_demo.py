import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_demo
from test_server import server


class DemoInitialization(unittest.TestCase):
    def test_fresh_state_restarts_without_resetting_accounts_or_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'runtime'
            self.assertTrue(run_demo.initialize_demo(root))
            credentials = (root / 'accounts.json').read_bytes()
            self.assertFalse(run_demo.initialize_demo(root))
            self.assertEqual((root / 'accounts.json').read_bytes(), credentials)
            accounts = json.loads(credentials)
            self.assertNotEqual(accounts['employee']['password'], accounts['admin']['password'])
            for role, filename in [('employee', 'auth.json'), ('admin', 'admin-bootstrap.json')]:
                auth = json.loads((root / 'state' / filename).read_text())
                digest = hashlib.pbkdf2_hmac('sha256', accounts[role]['password'].encode(), bytes.fromhex(auth['salt']), auth['iterations']).hex()
                self.assertEqual(digest, auth['hash'])
            catalog = json.loads((root / 'private/catalog.json').read_text())
            self.assertEqual(len(catalog['records']), 8)
            for record in catalog['records']:
                self.assertTrue(record['id'].startswith('DEMO-'))
                for image in record['images']:
                    self.assertTrue((root / 'private' / image['path']).is_file())

    def test_refuses_existing_or_incomplete_directory(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'keep.txt';path.write_text('keep')
            with self.assertRaises(ValueError):run_demo.initialize_demo(Path(root))
            self.assertEqual(path.read_text(), 'keep')

    def test_loopback_demo_rejects_foreign_host(self):
        handler = object.__new__(server.Handler)
        with patch.object(server, 'DEMO_HTTP', True):
            for host, allowed in [('localhost:4180', True), ('127.0.0.1:4180', True), ('attacker.test:4180', False)]:
                handler.headers = {'Host': host}
                self.assertEqual(handler.valid_host(), allowed)


class DemoClientDirectory(unittest.TestCase):
    from test_http import HTTP
    setUp = HTTP.setUp
    tearDown = HTTP.tearDown
    req = HTTP.req
    login = HTTP.login

    def test_customer_fallback_keeps_internal_routes_private(self):
        self.login()
        status, _, _ = self.req('/api/admin/users', {'action':'save', 'id':'demo_client_test',
            'version':0, 'name':'虚构客户', 'role':'client', 'active':True, 'password':self.password})
        self.assertEqual(status, 200)
        status, headers, _ = self.req('/api/login', {'username':'demo_client_test','password':self.password})
        self.assertEqual(status, 200)
        self.cookie = headers['Set-Cookie'].split(';')[0]
        status, headers, _ = self.req('/client')
        self.assertEqual(status, 303)
        self.assertEqual(headers['Location'], '/client/products')
        self.assertEqual(self.req('/client/products')[0], 200)
        for path in ['/api/catalog','/api/admin/users','/business/index.html','/media/demo-01.png']:
            self.assertEqual(self.req(path)[0], 403, path)
        self.assertEqual(self.req('/api/client/catalog')[0], 200)


if __name__ == '__main__':unittest.main()
