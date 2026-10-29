# Writes publish/kodi-changes/: what Neto-IL-TV changes in Kodi itself, as diffs against the official Kodi 21.3
# Android package (unpacked with apktool into ORIG). Kodi is GPL-2.0; these, the add-ons under src/ and the webOS
# build script are the whole of our changes to it.
#     java -jar tools/apktool.jar d -f -s -o <ORIG> downloads/kodi-21.3-Omega-armeabi-v7a.apk
#     python -I tools/make_kodi_changes.py <ORIG>
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work'
OUT = ROOT / 'publish/kodi-changes'
FILES = ('AndroidManifest.xml', 'apktool.yml', 'res/values/strings.xml', 'res/xml/searchable.xml',
         'assets/system/settings/settings.xml', 'assets/system/addon-manifest.xml')

NOTES = '''# Changes to Kodi in Neto-IL-TV

Neto-IL-TV is built from the official Kodi releases (GPL-2.0), unmodified in code except as listed here.
Kodi source: https://github.com/xbmc/xbmc (tag 21.3-Omega for Android, 21.0-Omega for webOS).

## Android (Kodi 21.3, armeabi-v7a)
- Package renamed from `org.xbmc.kodi` to `org.xbmc.neto`, so it installs next to Kodi: the Java classes moved from
  `org/xbmc/kodi` to `org/xbmc/neto`, every `org.xbmc.kodi` string in them and in the files below replaced, and the one
  `org.xbmc.kodi` string in `lib/armeabi-v7a/libkodi.so` replaced by `org.xbmc.neto` (same length, nothing else changed).
- `RECORD_AUDIO` permission removed (no voice search).
- Default settings changed: Hebrew, Israel, Hebrew keyboard, no screensaver, add-on updates from any repository,
  Hebrew subtitle encoding, no ".." row, FENtastic skin. See `settings.xml.diff`.
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
'''


def main(orig):
    OUT.mkdir(parents=True, exist_ok=True)
    listed = []
    for rel in FILES:
        a = (Path(orig) / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        b = (WORK / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        diff = ''.join(difflib.unified_diff(a, b, 'kodi-21.3/' + rel, 'neto-il-tv/' + rel))
        if diff:
            name = rel.split('/')[-1] + '.diff'
            (OUT / name).write_bytes(diff.encode('utf-8'))
            listed.append('- `%s`: `%s`' % (name, rel))
    (OUT / 'keymaps').mkdir(exist_ok=True)
    (OUT / 'keymaps/zz-netotv.xml').write_bytes((WORK / 'assets/system/keymaps/zz-netotv.xml').read_bytes())
    (OUT / 'README.md').write_bytes((NOTES + '\n'.join(listed) + '\n').encode('utf-8'))
    print('\n'.join(listed))


if __name__ == '__main__':
    main(sys.argv[1])
