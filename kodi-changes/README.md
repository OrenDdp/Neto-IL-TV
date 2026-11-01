# Changes to Kodi in Neto-IL-TV

Neto-IL-TV is built from the official Kodi releases (GPL-2.0), unmodified in code except as listed here.
Kodi source: https://github.com/xbmc/xbmc (tag 21.3-Omega for Android, 21.0-Omega for webOS).

## Android (Kodi 21.3, armeabi-v7a)
- Package renamed from `org.xbmc.kodi` to `org.xbmc.neto`, so it installs next to Kodi: the Java classes moved from
  `org/xbmc/kodi` to `org/xbmc/neto`, every `org.xbmc.kodi` string in them and in the files below replaced, and the one
  `org.xbmc.kodi` string in `lib/armeabi-v7a/libkodi.so` replaced by `org.xbmc.neto` (same length, nothing else changed).
- `RECORD_AUDIO` permission removed (no voice search).
- Default settings changed: Hebrew, Israel, Hebrew keyboard, no screensaver, add-on updates from any repository,
  Hebrew subtitle encoding, no ".." row, DockIL skin. See `settings.xml.diff`.
- System add-ons removed: audio encoders, mouse and SNES controllers, joystick support, version check, dim
  screensaver. Added: Hebrew language, FENtastic and its helper, the request modules, and our two add-ons (`src/`).
  See `addon-manifest.xml.diff`.
- Added keymap `system/keymaps/zz-netotv.xml` (Back stops playback, red button opens the item menu).
- App name, icons, banner and opening screens replaced (`tools/make_branding.ps1`).

## webOS (Kodi 21.0)
Made by `webos/build_ipk.py` from the official `org.xbmc.kodi-webos_21.0.ipk`: the same renaming (to
`org.xbmc.neto`, including the one id string in `kodi-webos`), the same settings, add-ons and keymap, and the
recording-server (`pvr.*`) add-ons removed.

## Diffs
- `AndroidManifest.xml.diff`: `AndroidManifest.xml`
- `apktool.yml.diff`: `apktool.yml`
- `strings.xml.diff`: `res/values/strings.xml`
- `searchable.xml.diff`: `res/xml/searchable.xml`
- `settings.xml.diff`: `assets/system/settings/settings.xml`
- `addon-manifest.xml.diff`: `assets/system/addon-manifest.xml`
