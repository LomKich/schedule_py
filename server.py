"""
Локальный HTTP-сервер на 127.0.0.1:8766
Отдаёт index.html и проксирует Яндекс Диск.
Использует requests+certifi — работает на Android (SSL сертификаты из certifi).
"""

import os
import threading
import socket
import time
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


def _make_request(url):
    """
    HTTPS-запрос через requests+certifi.
    На Android certifi даёт правильные корневые сертификаты — без него SSL падает.
    """
    import requests
    import certifi
    return requests.get(
        url,
        timeout=60,
        allow_redirects=True,
        verify=certifi.where(),
        headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10)',
            'Accept': '*/*',
        }
    )


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

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

        # ── Пинг (проверка что сервер живой) ─────────────────────
        if self.path == '/ping':
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ok')
            return

        # ── Прокси Яндекс Диска ───────────────────────────────────
        if self.path.startswith('/proxy/'):
            target = unquote(self.path[len('/proxy/'):])

            if not any(target.startswith(p) for p in ALLOWED_PREFIXES):
                self.send_error(403, 'Forbidden')
                return

            try:
                resp = _make_request(target)
                data = resp.content
                ct   = resp.headers.get('Content-Type', 'application/octet-stream')

                self.send_response(resp.status_code)
                self.send_header('Content-Type', ct)
                self.send_header('Content-Length', str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)

            except Exception as e:
                try:
                    self.send_error(502, f'Proxy error: {e}')
                except Exception:
                    pass
            return

        self.send_error(404)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')


def _port_open():
    try:
        with socket.create_connection(('127.0.0.1', PORT), timeout=0.3):
            return True
    except OSError:
        return False


def wait_until_ready(timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open():
            return True
        time.sleep(0.15)
    return False


def start_server():
    """Запустить сервер в фоне, дождаться готовности, вернуть URL."""
    if _port_open():
        return f'http://127.0.0.1:{PORT}/'

    httpd = HTTPServer(('127.0.0.1', PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    wait_until_ready(8.0)
    return f'http://127.0.0.1:{PORT}/'


if __name__ == '__main__':
    url = start_server()
    print(f'✅ Сервер запущен: {url}')
    print('   Открой эту ссылку в браузере')
    print('   Ctrl+C — остановить')
    while True:
        time.sleep(1)
