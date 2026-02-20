[app]
title = Расписание колледжа
package.name = schedule
package.domain = org.college

source.dir = .
source.include_exts = py,html,js,css,png,jpg,ttf,woff2,json
source.include_patterns = assets/*

version = 1.0
requirements = python3,kivy==2.3.0,pyjnius,requests,certifi

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

android.presplash_color = #0d0d0d
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
