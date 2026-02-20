"""
Локальный прокси-сервер для Яндекс Диска.
Запускается в фоновом потоке, доступен на http://127.0.0.1:8765
"""

import threading
import socket
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

PORT = 8765

ALLOWED_PREFIXES = (
    'https://cloud-api.yandex.net',
    'https://downloader.disk.yandex.ru',
    'https://getfile.disk.yandex.net',
    'https://disk.yandex.ru',
)

# Ленивый импорт — на Android requests может грузиться дольше
_session = None

def _get_session():
    global _session
    if _session is None:
        import requests
        s = requests.Session()
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',
            'Accept': '*/*',
        })
        _session = s
    return _session


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # Пинг — для проверки что прокси запущен
        if self.path == '/ping':
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ok')
            return

        if not self.path.startswith('/proxy/'):
            self.send_error(404)
            return

        target = unquote(self.path[len('/proxy/'):])

        if not any(target.startswith(p) for p in ALLOWED_PREFIXES):
            self.send_error(403, 'Forbidden domain')
            return

        try:
            session = _get_session()
            resp = session.get(target, timeout=60, allow_redirects=True)

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

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')


def _is_port_free():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', PORT)) != 0


def wait_until_ready(timeout=10.0):
    """Блокируется пока прокси не начнёт отвечать. Возвращает True если успел."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def start_proxy():
    """Запустить сервер в фоновом потоке и дождаться готовности."""
    if not _is_port_free():
        # Уже запущен (например, при hot-reload)
        return None

    server = HTTPServer(('127.0.0.1', PORT), ProxyHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    # Ждём пока порт откроется (макс 5 сек)
    wait_until_ready(5.0)
    return server


if __name__ == '__main__':
    print(f'Proxy on http://127.0.0.1:{PORT}/proxy/')
    start_proxy()
    import time
    while True:
        time.sleep(1)
