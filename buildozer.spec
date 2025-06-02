[app]
title = Music Player
package.name = musicplayer
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,mp3,kv  # پسوند فایل‌های شما
version = 1.0.0
requirements = python3,kivy==2.3.0,pygame==2.5.2,mutagen==1.47.0,hostpython3
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 23b
p4a.branch = master
orientation = portrait
fullscreen = 0