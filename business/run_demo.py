#!/usr/bin/env python3
"""Initialize fictional state once, then serve authenticated HTTP on loopback only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
MARKER = 'packaging-business-demo-v1'


def initialize_demo(directory):
    directory = Path(directory).resolve()
    if directory.exists():
        marker = directory / 'demo-marker.txt'
        required = ['state/auth.json', 'state/admin-bootstrap.json', 'private/catalog.json', 'accounts.json']
        if not marker.is_file() or marker.read_text().strip() != MARKER or not all((directory / name).is_file() for name in required):
            raise ValueError('目录已存在或不完整，未覆盖任何文件。请选择新的 --data-dir。')
        return False
    directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.demo-init-', dir=directory.parent))
    try:
        (temporary / 'state').mkdir(mode=0o700)
        shutil.copytree(ROOT / 'demo', temporary / 'private')
        accounts = {}
        for role, filename in [('employee', 'auth.json'), ('admin', 'admin-bootstrap.json')]:
            password, salt = secrets.token_urlsafe(20), secrets.token_hex(16)
            username = 'demo_' + role
            accounts[role] = {'username': username, 'password': password}
            auth = {'username': username, 'salt': salt, 'iterations': 600000,
                    'hash': hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000).hex()}
            path = temporary / 'state' / filename
            path.write_text(json.dumps(auth), encoding='utf-8')
            path.chmod(0o600)
        path = temporary / 'accounts.json'
        path.write_text(json.dumps(accounts, indent=2) + '\n', encoding='utf-8')
        path.chmod(0o600)
        (temporary / 'demo-marker.txt').write_text(MARKER + '\n')
        # A competing initialization must never replace a populated directory.
        temporary.rename(directory)
        return True
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / '.runtime')
    parser.add_argument('--port', type=int, default=4180)
    parser.add_argument('--init-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('端口必须在 1–65535 之间')
    try:
        initialize_demo(args.data_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    directory = args.data_dir.resolve()
    print('账号文件（仅本机，勿上传）：' + str(directory / 'accounts.json'), flush=True)
    if args.init_only:
        return
    import server
    server.STATE, server.PRIVATE = directory / 'state', directory / 'private'
    server.LOCAL = False  # Normal authentication and roles also apply to the demo.
    server.DEMO_HTTP = True
    os.environ['YZ_SECURE_COOKIE'] = '0'  # Only this fixed loopback HTTP launcher uses insecure transport.
    server.initialize()
    service = server.ThreadingHTTPServer(('127.0.0.1', args.port), server.Handler)
    print(f'本地演示：http://127.0.0.1:{args.port}/login （Ctrl+C 停止）', flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.server_close()
        server.CATALOG_PAGES.close()


if __name__ == '__main__':
    main()
