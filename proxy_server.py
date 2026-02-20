"""
Локальный прокси-сервер для Яндекс Диска.
Использует requests (как старая версия приложения) — проверено на Android в России.
"""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

import requests

PORT = 8765

# Разрешаем все поддомены Яндекса — Яндекс использует разные домены для редиректов
ALLOWED_PREFIXES = (
    'https://cloud-api.yandex.net',
    'https://downloader.disk.yandex.ru',
    'https://getfile.disk.yandex.net',
    'https://disk.yandex.ru',
    'https://yastatic.net',
)

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (compatible; ScheduleBot/1.0)',
    'Accept': '*/*',
})


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # отключаем лишние логи

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if not self.path.startswith('/proxy/'):
            self.send_error(404)
            return

        target = unquote(self.path[len('/proxy/'):])

        if not any(target.startswith(p) for p in ALLOWED_PREFIXES):
            self.send_error(403, 'Forbidden domain')
            return

        try:
            resp = SESSION.get(target, timeout=60, allow_redirects=True)

            data = resp.content
            ct   = resp.headers.get('Content-Type', 'application/octet-stream')

            self.send_response(resp.status_code)
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)

        except requests.exceptions.ConnectionError as e:
            self.send_error(502, f'Connection error: {e}')
        except requests.exceptions.Timeout:
            self.send_error(504, 'Timeout')
        except Exception as e:
            self.send_error(502, f'Proxy error: {e}')

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')


def start_proxy():
    """Запустить сервер в фоновом потоке."""
    server = HTTPServer(('127.0.0.1', PORT), ProxyHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


if __name__ == '__main__':
    import time
    print(f'Proxy on http://127.0.0.1:{PORT}/proxy/')
    start_proxy()
    while True:
        time.sleep(1)
