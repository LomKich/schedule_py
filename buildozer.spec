[app]
title = Расписание колледжа
package.name = schedule
package.domain = org.college

source.dir = .
source.include_exts = py,html,js,css,png,jpg,ttf,woff2,json
source.include_patterns = assets/*

version = 1.0
requirements = python3,kivy==2.3.0,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 26
android.ndk = 25b
android.ndk_api = 26
android.build_tools_version = 33.0.2
android.archs = arm64-v8a
android.allow_backup = True

# Разрешаем HTTP на localhost (нужно для прокси 127.0.0.1:8765)
android.manifest.application_attrs = android:usesCleartextTraffic="true"

# Иконка и сплэш (раскомментируй и положи файлы рядом с main.py)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png
android.presplash_color = #0d0d0d

log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
