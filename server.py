"""
Локальный HTTP-сервер на 127.0.0.1:8766
Отдаёт index.html И проксирует Яндекс Диск — всё в одном origin.
Используется urllib (встроен в Python, нет внешних зависимостей).
"""

import os
import threading
import socket
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

PORT = 8766

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
HTML_FILE   = os.path.join(ASSETS_DIR, 'index.html')

ALLOWED_PREFIXES = (
    'https://cloud-api.yandex.net',
    'https://downloader.disk.yandex.ru',
    'https://getfile.disk.yandex.net',
    'https://disk.yandex.ru',
)


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        # ── Главная страница ──────────────────────────────────────
        if self.path in ('/', '/index.html'):
            try:
                with open(HTML_FILE, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_error(500, str(e))
            return

        # ── Прокси Яндекс Диска ───────────────────────────────────
        if self.path.startswith('/proxy/'):
            target = unquote(self.path[len('/proxy/'):])

            if not any(target.startswith(p) for p in ALLOWED_PREFIXES):
                self.send_error(403, 'Forbidden domain')
                return

            try:
                req = urllib.request.Request(
                    target,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 10)',
                        'Accept': '*/*',
                    }
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = resp.read()
                    ct   = resp.headers.get('Content-Type', 'application/octet-stream')

                self.send_response(200)
                self.send_header('Content-Type', ct)
                self.send_header('Content-Length', str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)

            except urllib.error.HTTPError as e:
                self.send_error(e.code, str(e.reason))
            except Exception as e:
                self.send_error(502, f'Proxy error: {e}')
            return

        self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')


def wait_until_ready(timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def start_server():
    """Запустить сервер в фоне и дождаться готовности. Вернуть URL."""
    # Проверяем — вдруг уже запущен
    try:
        with socket.create_connection(('127.0.0.1', PORT), timeout=0.3):
            return f'http://127.0.0.1:{PORT}/'
    except OSError:
        pass

    httpd = HTTPServer(('127.0.0.1', PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    wait_until_ready(8.0)
    return f'http://127.0.0.1:{PORT}/'


if __name__ == '__main__':
    url = start_server()
    print(f'Server: {url}')
    print('Ctrl+C to stop')
    import time
    while True:
        time.sleep(1)
