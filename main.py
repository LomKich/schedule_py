"""
Расписание колледжа — Android

Архитектура:
  1. Запускаем локальный прокси-сервер на 127.0.0.1:8765
  2. Читаем index.html как строку
  3. Загружаем через loadDataWithBaseURL с base = http://localhost/
     → JS внутри может делать fetch() к http://127.0.0.1:8765 без ограничений
"""

import os

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.utils import platform

import proxy_server

# ── Путь к index.html ────────────────────────────────────────────
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
HTML_FILE   = os.path.join(ASSETS_DIR, 'index.html')


# ── Android WebView ───────────────────────────────────────────────
if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    PythonActivity  = autoclass('org.kivy.android.PythonActivity')
    WebView         = autoclass('android.webkit.WebView')
    WebViewClient   = autoclass('android.webkit.WebViewClient')
    WebChromeClient = autoclass('android.webkit.WebChromeClient')
    LinearLayout    = autoclass('android.widget.LinearLayout')
    LayoutParams    = autoclass('android.view.ViewGroup$LayoutParams')
    Color           = autoclass('android.graphics.Color')

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
            # Разрешаем fetch() из file/data URL к http://
            s.setAllowFileAccessFromFileURLs(True)
            s.setAllowUniversalAccessFromFileURLs(True)
            s.setAllowFileAccess(True)
            s.setMixedContentMode(0)   # MIXED_CONTENT_ALWAYS_ALLOW
            s.setLoadsImagesAutomatically(True)
            s.setSupportZoom(False)
            s.setBuiltInZoomControls(False)
            s.setDisplayZoomControls(False)

            wv.setWebViewClient(WebViewClient())
            wv.setWebChromeClient(WebChromeClient())
            wv.setBackgroundColor(Color.parseColor('#0d0d0d'))

            # Загружаем HTML как строку с base http://localhost/
            # → fetch('http://127.0.0.1:8765/...') работает без блокировок
            wv.loadDataWithBaseURL(
                'http://localhost/',   # baseUrl
                self.html,            # data
                'text/html',          # mimeType
                'UTF-8',              # encoding
                None                  # historyUrl
            )

            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            params = LayoutParams(
                LayoutParams.MATCH_PARENT,
                LayoutParams.MATCH_PARENT
            )
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
    # ── Десктоп-заглушка ─────────────────────────────────────────
    from kivy.uix.label import Label

    class AndroidWebView(Widget):
        def __init__(self, html, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(
                text='[b]Desktop mode[/b]\nОткрой assets/index.html в браузере',
                markup=True,
                halign='center'
            ))


# ── App ───────────────────────────────────────────────────────────
class ScheduleApp(App):

    def build(self):
        proxy_server.start_proxy()

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
