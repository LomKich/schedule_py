"""
Главный модуль приложения «Расписание колледжа» для Android.

Архитектура:
  1. Запускаем локальный прокси-сервер (proxy_server.py) на 127.0.0.1:8765
  2. Открываем нативный Android WebView с index.html из assets/
  3. HTML уже настроен использовать http://127.0.0.1:8765/proxy/ — нет CORS
"""

import os
import sys

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.utils import platform

import proxy_server


# ── Путь к assets ────────────────────────────────────────────────
def get_assets_path():
    if platform == 'android':
        # На Android assets копируются рядом с main.py
        return os.path.join(os.path.dirname(__file__), 'assets')
    # Десктоп / разработка
    return os.path.join(os.path.dirname(__file__), 'assets')


HTML_PATH = os.path.join(get_assets_path(), 'index.html')


# ── Android WebView через pyjnius ─────────────────────────────────
if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass, cast

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    WebView        = autoclass('android.webkit.WebView')
    WebViewClient  = autoclass('android.webkit.WebViewClient')
    WebChromeClient= autoclass('android.webkit.WebChromeClient')
    LinearLayout   = autoclass('android.widget.LinearLayout')
    LayoutParams   = autoclass('android.view.ViewGroup$LayoutParams')
    View           = autoclass('android.view.View')
    Color          = autoclass('android.graphics.Color')

    class AndroidWebView(Widget):
        def __init__(self, url, **kwargs):
            super().__init__(**kwargs)
            self.url = url
            self._wv = None
            Clock.schedule_once(lambda dt: self._create(), 0)

        @run_on_ui_thread
        def _create(self):
            activity = PythonActivity.mActivity
            wv = WebView(activity)
            self._wv = wv

            # Настройки
            settings = wv.getSettings()
            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setAllowFileAccessFromFileURLs(True)
            settings.setAllowUniversalAccessFromFileURLs(True)
            settings.setAllowFileAccess(True)
            settings.setLoadsImagesAutomatically(True)
            settings.setSupportZoom(False)
            settings.setBuiltInZoomControls(False)
            settings.setDisplayZoomControls(False)

            wv.setWebViewClient(WebViewClient())
            wv.setWebChromeClient(WebChromeClient())
            wv.setBackgroundColor(Color.parseColor('#0d0d0d'))

            # Встраиваем WebView как оверлей поверх Kivy surface
            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            params = LayoutParams(
                LayoutParams.MATCH_PARENT,
                LayoutParams.MATCH_PARENT
            )
            layout.setLayoutParams(params)
            layout.addView(wv, params)

            activity.addContentView(layout, params)
            wv.loadUrl(self.url)

        @run_on_ui_thread
        def on_back(self):
            if self._wv and self._wv.canGoBack():
                self._wv.goBack()
                return True
            return False

else:
    # ── Десктоп-заглушка (для разработки) ───────────────────────
    from kivy.uix.label import Label

    class AndroidWebView(Widget):
        def __init__(self, url, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(
                text=f'[b]Desktop mode[/b]\nOpen in browser:\n{url}',
                markup=True,
                halign='center'
            ))


# ── Kivy App ─────────────────────────────────────────────────────
class ScheduleApp(App):

    def build(self):
        # Запускаем локальный прокси до создания WebView
        proxy_server.start_proxy()

        url = f'file://{HTML_PATH}'
        self.webview = AndroidWebView(url=url)
        return self.webview

    def on_back_button(self):
        """Перехватываем кнопку «Назад» — передаём WebView."""
        if platform == 'android':
            if self.webview.on_back():
                return True
        return False


if __name__ == '__main__':
    ScheduleApp().run()
