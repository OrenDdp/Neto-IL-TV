#!/usr/bin/env bash
# Rebuild and sign Neto-IL-TV from work/ (the unpacked, already-renamed Kodi 21.3).
# Output: dist/Neto-IL-TV-21.3-armeabi-v7a.apk. Keep keystore/ safe: updates must be signed with the same key.
set -euo pipefail
cd "$(dirname "$0")"
BT="$LOCALAPPDATA/Android/Sdk/build-tools/34.0.0"
OUT=dist/Neto-IL-TV-21.3-armeabi-v7a.apk
mkdir -p dist
python -I -m py_compile work/assets/addons/service.netotv/service.py
find work -name __pycache__ -type d -prune -exec rm -rf {} +
java -jar tools/apktool.jar b work -o dist/unsigned.apk
"$BT/zipalign.exe" -f -p 4 dist/unsigned.apk dist/aligned.apk
"$BT/apksigner.bat" sign --ks keystore/idantv.jks --ks-pass "pass:$(cat keystore/password.txt)" --out "$OUT" dist/aligned.apk
rm -f dist/unsigned.apk dist/aligned.apk dist/*.idsig
"$BT/aapt.exe" dump badging "$OUT" | grep -E "^package|application-label:"
