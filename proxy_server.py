"""
Локальный прокси-сервер для Яндекс Диска.
Запускается в фоновом потоке на порту 8765.
Заменяет Cloudflare Worker — нет CORS проблем, нет внешних зависимостей.
"""

import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler


ALLOWED_DOMAINS = (
    'https://cloud-api.yandex.net',
    'https://downloader.disk.yandex.ru',
)

PORT = 8765


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Отключаем лишние логи
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # /proxy/<encoded_url>
        if not self.path.startswith('/proxy/'):
            self.send_error(404, 'Not found')
            return

        raw = self.path[len('/proxy/'):]
        # Может быть query string после закодированного URL — берём только path часть
        target = urllib.parse.unquote(raw)

        # Проверяем домен
        if not any(target.startswith(d) for d in ALLOWED_DOMAINS):
            self.send_error(403, 'Forbidden domain')
            return

        try:
            req = urllib.request.Request(
                target,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; ScheduleBot/1.0)',
                    'Accept': '*/*',
                }
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                ct = resp.headers.get('Content-Type', 'application/octet-stream')

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

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')


def start_proxy():
    """Запустить сервер в фоновом потоке. Вызвать один раз при старте приложения."""
    server = HTTPServer(('127.0.0.1', PORT), ProxyHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


if __name__ == '__main__':
    print(f'Proxy listening on http://127.0.0.1:{PORT}/proxy/')
    start_proxy()
    import time
    while True:
        time.sleep(1)
