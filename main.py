"""
Расписание колледжа — Android

Архитектура:
  WebView загружает index.html через loadDataWithBaseURL.
  Все запросы к /proxy/https://... перехватываются через shouldInterceptRequest —
  Python сам делает HTTPS запрос к Яндексу и возвращает данные в WebView.
  Никакого отдельного сервера, никакого CORS, никакого cleartext HTTP.
"""

import os
import threading

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.utils import platform

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
HTML_FILE   = os.path.join(ASSETS_DIR, 'index.html')

ALLOWED_PREFIXES = (
    'https://cloud-api.yandex.net',
    'https://downloader.disk.yandex.ru',
    'https://getfile.disk.yandex.net',
    'https://disk.yandex.ru',
)


def _do_request(url):
    """HTTPS запрос через requests+certifi — SSL работает на Android."""
    import requests, certifi
    r = requests.get(
        url, timeout=60, allow_redirects=True,
        verify=certifi.where(),
        headers={'User-Agent': 'Mozilla/5.0 (Linux; Android 10)', 'Accept': '*/*'}
    )
    return r.status_code, r.headers.get('Content-Type', 'application/octet-stream'), r.content


if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass, PythonJavaClass, java_method

    PythonActivity   = autoclass('org.kivy.android.PythonActivity')
    WebView          = autoclass('android.webkit.WebView')
    WebChromeClient  = autoclass('android.webkit.WebChromeClient')
    LinearLayout     = autoclass('android.widget.LinearLayout')
    LayoutParams     = autoclass('android.view.ViewGroup$LayoutParams')
    Color            = autoclass('android.graphics.Color')
    WebResourceResponse = autoclass('android.webkit.WebResourceResponse')
    ByteArrayInputStream = autoclass('java.io.ByteArrayInputStream')

    class InterceptingClient(PythonJavaClass):
        """
        WebViewClient который перехватывает /proxy/... запросы
        и выполняет их через Python requests — без CORS, без ограничений.
        """
        __javainterfaces__ = ['android/webkit/WebViewClient']
        __javacontext__ = 'app'

        @java_method('(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Landroid/webkit/WebResourceResponse;')
        def shouldInterceptRequest(self, view, request):
            try:
                url = str(request.getUrl().toString())

                if '/proxy/' not in url:
                    return None  # Обычный запрос — WebView обрабатывает сам

                # Извлекаем целевой URL из /proxy/<encoded>
                from urllib.parse import unquote
                idx = url.find('/proxy/')
                target = unquote(url[idx + len('/proxy/'):])

                if not any(target.startswith(p) for p in ALLOWED_PREFIXES):
                    return None

                # Запрос в отдельном потоке не нужен — shouldInterceptRequest
                # уже вызывается не на UI-потоке
                status, ct, data = _do_request(target)

                stream = ByteArrayInputStream(data)
                charset = 'utf-8' if 'json' in ct or 'text' in ct else None
                return WebResourceResponse(ct, charset, status, 'OK', None, stream)

            except Exception as e:
                return None  # При ошибке — WebView попробует сам

        @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)V')
        def onPageFinished(self, view, url):
            pass

    class AndroidWebView(Widget):
        def __init__(self, html, **kwargs):
            super().__init__(**kwargs)
            self.html = html
            self._wv  = None
            Clock.schedule_once(lambda dt: self._create(), 0)

        @run_on_ui_thread
        def _create(self):
            activity = PythonActivity.mActivity
            wv = WebView(activity)
            self._wv = wv

            s = wv.getSettings()
            s.setJavaScriptEnabled(True)
            s.setDomStorageEnabled(True)
            s.setLoadsImagesAutomatically(True)
            s.setSupportZoom(False)
            s.setBuiltInZoomControls(False)
            s.setDisplayZoomControls(False)

            # Наш перехватчик вместо стандартного WebViewClient
            wv.setWebViewClient(InterceptingClient())
            wv.setWebChromeClient(WebChromeClient())
            wv.setBackgroundColor(Color.parseColor('#0d0d0d'))

            # Загружаем HTML как строку — base URL любой, fetch идёт через перехватчик
            wv.loadDataWithBaseURL(
                'https://app.local/',
                self.html,
                'text/html',
                'UTF-8',
                None
            )

            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            params = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT)
            layout.setLayoutParams(params)
            layout.addView(wv, params)
            activity.addContentView(layout, params)

        @run_on_ui_thread
        def on_back(self):
            if self._wv and self._wv.canGoBack():
                self._wv.goBack()
                return True
            return False

else:
    # ── ПК: запускаем простой сервер, открываем браузер ──────────
    from kivy.uix.label import Label
    import server  # server.py — для ПК тестирования

    class AndroidWebView(Widget):
        def __init__(self, html, **kwargs):
            super().__init__(**kwargs)
            url = server.start_server()
            self.add_widget(Label(
                text=f'[b]Desktop mode[/b]\nОткрой в браузере:\n{url}',
                markup=True, halign='center'
            ))


class ScheduleApp(App):

    def build(self):
        with open(HTML_FILE, encoding='utf-8') as f:
            html = f.read()
        self.webview = AndroidWebView(html=html)
        return self.webview

    def on_back_button(self):
        if platform == 'android':
            return self.webview.on_back()
        return False


if __name__ == '__main__':
    ScheduleApp().run()
