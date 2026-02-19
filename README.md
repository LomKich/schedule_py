# 📅 Расписание колледжа — Android

Android-приложение для просмотра расписания с Яндекс Диска.  
Точная копия веб-версии, собирается автоматически через GitHub Actions.

---

## Как получить APK

1. **Форкни** этот репозиторий на свой GitHub
2. Перейди во вкладку **Actions** → выбери `Build Android APK`
3. Нажми **Run workflow** → **Run workflow**
4. Подожди ~20–40 минут (первый раз дольше из-за скачивания Android SDK)
5. Скачай APK из раздела **Artifacts** в успешном запуске

При каждом пуше в `main`/`master` APK собирается автоматически.

---

## Архитектура

```
┌─────────────────────────────────────┐
│         Android WebView             │
│   (index.html — весь UI/логика)     │
│                                     │
│   fetch → http://127.0.0.1:8765    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Локальный Python-прокси        │
│         (proxy_server.py)           │
│   /proxy/<encoded_url>              │
│                                     │
│   → cloud-api.yandex.net  ✅        │
│   → downloader.disk.yandex.ru  ✅   │
└─────────────────────────────────────┘
```

- **WebView** — отображает оригинальный HTML без изменений дизайна
- **Прокси** — решает проблему CORS: Python делает HTTP-запросы напрямую без ограничений браузера
- **Сборка** — Buildozer + python-for-android, только APK

---

## Структура файлов

```
├── main.py              # Точка входа, запуск прокси + Kivy + WebView
├── proxy_server.py      # HTTP-сервер на 127.0.0.1:8765
├── assets/
│   └── index.html       # Оригинальный UI (прокси → localhost)
├── buildozer.spec       # Конфигурация сборки Android
└── .github/workflows/
    └── build.yml        # GitHub Actions CI
```

---

## Отличия от веб-версии

| Веб | Android |
|-----|---------|
| Cloudflare Worker (`/proxy/`) | Локальный Python-сервер (`127.0.0.1:8765/proxy/`) |
| Браузер | Нативный Android WebView |
| GitHub Pages | APK-файл |

Дизайн, логика, темы, звонки — **без изменений**.

---

## Требования для локальной разработки

```bash
pip install buildozer cython kivy
# Для запуска на десктопе (preview):
python main.py
```

Для сборки APK нужен Linux + Java 17 + Android SDK (Buildozer скачает автоматически).
