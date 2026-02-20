"""
Расписание колледжа — Android
Загружает index.html напрямую через file:// — как открытие файла в браузере.
"""

import os

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.utils import platform

import proxy_server

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
HTML_FILE   = os.path.join(ASSETS_DIR, 'index.html')


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
        def __init__(self, file_url, **kwargs):
            super().__init__(**kwargs)
            self.file_url = file_url
            self._wv = None
            Clock.schedule_once(lambda dt: self._create(), 0.3)

        @run_on_ui_thread
        def _create(self):
            activity = PythonActivity.mActivity
            wv = WebView(activity)
            self._wv = wv

            s = wv.getSettings()
            s.setJavaScriptEnabled(True)
            s.setDomStorageEnabled(True)
            # Эти три разрешают fetch() из file:// к http://127.0.0.1
            s.setAllowFileAccess(True)
            s.setAllowFileAccessFromFileURLs(True)
            s.setAllowUniversalAccessFromFileURLs(True)
            # Разрешаем HTTP внутри file:// контекста
            s.setMixedContentMode(0)   # MIXED_CONTENT_ALWAYS_ALLOW
            s.setLoadsImagesAutomatically(True)
            # Зум отключён
            s.setSupportZoom(False)
            s.setBuiltInZoomControls(False)
            s.setDisplayZoomControls(False)

            wv.setWebViewClient(WebViewClient())
            wv.setWebChromeClient(WebChromeClient())
            wv.setBackgroundColor(Color.parseColor('#0d0d0d'))

            # Грузим как обычный файл — точно так же как браузер открывает HTML
            wv.loadUrl(self.file_url)

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
        def __init__(self, file_url, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(
                text='[b]Desktop mode[/b]\nОткрой assets/index.html в браузере',
                markup=True, halign='center'
            ))


class ScheduleApp(App):

    def build(self):
        # Запускаем прокси и ждём готовности
        proxy_server.start_proxy()

        # Получаем реальный путь к файлу на устройстве
        file_url = f'file://{HTML_FILE}'

        self.webview = AndroidWebView(file_url=file_url)
        return self.webview

    def on_back_button(self):
        if platform == 'android':
            return self.webview.on_back()
        return False


if __name__ == '__main__':
    ScheduleApp().run()
