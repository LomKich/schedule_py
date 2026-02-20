"""
Расписание колледжа — Android

Архитектура:
  1. server.py запускает HTTP-сервер на 127.0.0.1:8766
  2. Сервер отдаёт index.html И проксирует Яндекс Диск
  3. WebView открывает http://127.0.0.1:8766/ — всё same-origin, нет CORS
"""

import os

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.utils import platform

import server   # <- единый сервер вместо отдельного proxy_server


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

            s = wv.getSettings()
            s.setJavaScriptEnabled(True)
            s.setDomStorageEnabled(True)
            s.setLoadsImagesAutomatically(True)
            # Зум отключён
            s.setSupportZoom(False)
            s.setBuiltInZoomControls(False)
            s.setDisplayZoomControls(False)

            wv.setWebViewClient(WebViewClient())
            wv.setWebChromeClient(WebChromeClient())
            wv.setBackgroundColor(Color.parseColor('#0d0d0d'))

            # Загружаем по HTTP — никаких file://, никаких CORS
            wv.loadUrl(self.url)

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
    from kivy.uix.label import Label

    class AndroidWebView(Widget):
        def __init__(self, url, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(
                text='[b]Desktop mode[/b]\nОткрой в браузере:\n' + url,
                markup=True, halign='center'
            ))


class ScheduleApp(App):

    def build(self):
        # Стартуем сервер и ждём пока он не ответит
        url = server.start_server()
        self.webview = AndroidWebView(url=url)
        return self.webview

    def on_back_button(self):
        if platform == 'android':
            return self.webview.on_back()
        return False


if __name__ == '__main__':
    ScheduleApp().run()
