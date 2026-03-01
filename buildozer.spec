# Buildozer spec file for packaging the Kivy app as an APK
# See https://github.com/kivy/buildozer for options

[app]
title = MTG Random Commander Generator
package.name = mtgcommander
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
icon.filename = %(source.dir)s/icon.png
version = 1.0
requirements = python3,kivy,requests,cython<3,pillow
orientation = portrait
fullscreen = 1
android.permissions = INTERNET
source.main = main.py
ignore_setup_py = 1

# Improve viewport and scaling for mobile
window.softinput_mode = adjustResize
android.window_dpi = 320

[buildozer]
log_level = 2
warn_on_root = 1

[output]
# (apk|aab) Choose the format of the output package
format = apk