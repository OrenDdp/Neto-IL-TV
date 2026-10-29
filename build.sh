#!/usr/bin/env bash
# Rebuild and sign Neto-IL-TV from work/ (the unpacked, already-renamed Kodi 21.3), with the Dock home page.
# Output: dist/Neto-IL-TV-21.3-armeabi-v7a.apk. Keep keystore/ safe: updates must be signed with the same key.
set -euo pipefail
cd "$(dirname "$0")"
BT="$LOCALAPPDATA/Android/Sdk/build-tools/34.0.0"
OUT=dist/Neto-IL-TV-21.3-armeabi-v7a.apk
mkdir -p dist
python -I -m py_compile work/assets/addons/service.netotv/service.py
find work -name __pycache__ -type d -prune -exec rm -rf {} +
# Box 2 runs the one-page Dock home (no side menu); the tabs Home.xml stays in work/ for the LG tabs build.
DOCK_HOME=work/assets/addons/skin.fentastic/xml/Home.xml
cp "$DOCK_HOME" dist/Home.tabs.xml
trap 'cp dist/Home.tabs.xml "$DOCK_HOME"; rm -f dist/Home.tabs.xml' EXIT
python -I -c "import sys; sys.path.insert(0, 'webos'); import build_ipk as b; p = '$DOCK_HOME'; s = b.dock_home(open(p, encoding='utf-8').read()); open(p, 'w', encoding='utf-8', newline='').write(s)"
java -jar tools/apktool.jar b work -o dist/unsigned.apk
"$BT/zipalign.exe" -f -p 4 dist/unsigned.apk dist/aligned.apk
"$BT/apksigner.bat" sign --ks keystore/idantv.jks --ks-pass "pass:$(cat keystore/password.txt)" --out "$OUT" dist/aligned.apk
rm -f dist/unsigned.apk dist/aligned.apk dist/*.idsig
"$BT/aapt.exe" dump badging "$OUT" | grep -E "^package|application-label:"
