# Builds Neto-IL-TV for LG webOS: the official Kodi 21.0 webOS package, renamed to org.xbmc.neto and carrying the same
# add-ons, tabs and settings as the Android build (work/assets). Edits the archive in place with tarfile, because the
# package holds Linux symlinks that a Windows checkout cannot extract.
#     python -I webos/build_ipk.py   ->   webos/dist/org.xbmc.neto_<version>_arm.ipk
import gzip
import io
import json
import re
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADDONS = ROOT.parent / 'work/assets/addons'          # shared with the Android build
SOURCE = ROOT / 'downloads/kodi-webos-21.0.ipk'      # https://mirrors.kodi.tv/releases/webos/
OLD, NEW = 'org.xbmc.kodi', 'org.xbmc.neto'          # same length: the id is patched inside the binary too
# Follows service.netotv's version, so both builds move together: 1.0.16 -> 21.0.16
_service = re.search(r'<addon\b[^>]*\sversion="([^"]+)"', ADDONS.joinpath('service.netotv/addon.xml').read_text(encoding='utf-8'))
VERSION = '21.0.%s' % _service.group(1).split('.')[-1]
APP = 'usr/palm/applications/%s/' % NEW
PACKAGEINFO = 'usr/palm/packages/%s/packageinfo.json' % NEW

# Not needed for Idan+ on a TV remote (as in the Android build), plus the recording-server clients webOS ships.
DROP = ('audioencoder.', 'game.controller.mouse', 'game.controller.snes', 'peripheral.joystick',
        'service.xbmc.versioncheck', 'screensaver.xbmc.builtin.dim', 'pvr.')
# Our add-ons, from the Android build. inputstream.adaptive stays webOS's own: the Android one is an Android library.
ADD = ('skin.fentastic', 'script.fentastic.helper', 'script.module.requests', 'script.module.urllib3',
       'script.module.certifi', 'script.module.chardet', 'script.module.idna', 'resource.language.he_il',
       'service.netotv', 'plugin.video.netotv')
SKIP_IN_ADD = ('service.netotv/payload/inputstream.adaptive/',)
SYSTEM_ADDONS = ('resource.language.he_il', 'service.netotv', 'plugin.video.netotv', 'skin.fentastic',
                 'script.fentastic.helper', 'script.module.requests', 'script.module.urllib3',
                 'script.module.certifi', 'script.module.chardet', 'script.module.idna')

DEFAULTS = {  # same as the Android build's settings.xml
    'locale.language': 'resource.language.he_il', 'locale.country': 'Israel',
    'locale.keyboardlayouts': 'English QWERTY|Hebrew QWERTY', 'screensaver.mode': '',
    'addons.unknownsources': 'true', 'addons.updatemode': '1', 'subtitles.charset': 'CP1255',
    'filelists.showparentdiritems': 'false', 'lookandfeel.skin': 'skin.fentastic',
}


def dropped(addon_path):
    name = addon_path.split('/')[0]
    return any(name.startswith(d) for d in DROP)


def settings(xml):
    for key, value in DEFAULTS.items():
        m = re.search(r'(<setting id="%s"[^>]*>.*?<default>)(.*?)(</default>)' % re.escape(key), xml, re.S)
        assert m, key
        xml = xml[:m.start(2)] + value + xml[m.end(2):]
    return xml


def manifest(xml):
    for name in re.findall(r'<addon[^>]*>([^<]+)</addon>', xml):
        if dropped(name):
            xml = re.sub(r'\s*<addon[^>]*>%s</addon>' % re.escape(name), '', xml)
    return xml.replace('</addons>', ''.join('  <addon>%s</addon>\n' % a for a in SYSTEM_ADDONS) + '</addons>')


def appinfo(text):
    info = json.loads(text)
    info.update(id=NEW, title='Neto-IL-TV', version=VERSION, vendor='local')
    return json.dumps(info, ensure_ascii=False, indent=2)


def binary(data):
    old, new = (OLD + '\0').encode(), (NEW + '\0').encode()
    assert data.count(old) == 1, 'expected the app id once in kodi-webos'
    return data.replace(old, new)


REPLACE = {  # path inside the app -> function(old bytes) -> new bytes
    'appinfo.json': lambda b: appinfo(b.decode('utf-8')).encode('utf-8'),
    'system/settings/settings.xml': lambda b: settings(b.decode('utf-8')).encode('utf-8'),
    'system/addon-manifest.xml': lambda b: manifest(b.decode('utf-8')).encode('utf-8'),
    'kodi-webos': binary,
    'icon.png': lambda b: (ROOT / 'assets/icon.png').read_bytes(),
    'largeIcon.png': lambda b: (ROOT / 'assets/largeIcon.png').read_bytes(),
    'media/applaunch_screen.png': lambda b: (ROOT.parent / 'work/assets/media/applaunch_screen.png').read_bytes(),
    'media/splash.jpg': lambda b: (ROOT.parent / 'work/assets/media/splash.jpg').read_bytes(),
}
EXTRA = {'system/keymaps/zz-netotv.xml': ROOT.parent / 'work/assets/system/keymaps/zz-netotv.xml'}


def add_file(out, name, data, mode=0o644, like=None):
    info = tarfile.TarInfo(name)
    info.size, info.mode, info.mtime = len(data), mode, int(time.time())
    if like is not None:
        info.uid, info.gid, info.mode = like.uid, like.gid, like.mode
    out.addfile(info, io.BytesIO(data))


def add_dir(out, name, seen):
    if name in seen:
        return
    seen.add(name)
    info = tarfile.TarInfo(name)
    info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, int(time.time())
    out.addfile(info)


def data_tar():
    src_ipk = SOURCE.read_bytes()
    members = ar_read(src_ipk)
    src = tarfile.open(fileobj=io.BytesIO(members['data.tar.gz']))
    buf = io.BytesIO()
    seen = set()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0) as gz, tarfile.open(fileobj=gz, mode='w', format=tarfile.GNU_FORMAT) as out:
        for m in src.getmembers():
            name = m.name.replace('/%s' % OLD, '/%s' % NEW, 1)
            rel = name[len(APP):] if name.startswith(APP) else None
            if rel and rel.startswith('addons/') and dropped(rel[len('addons/'):]):
                continue
            m.name = name
            if m.isdir():
                seen.add(name)
            if rel in REPLACE:
                add_file(out, name, REPLACE[rel](src.extractfile(m).read()), like=m)
            elif name == PACKAGEINFO:
                info = json.loads(src.extractfile(m).read().decode('utf-8'))
                info.update(id=NEW, app=NEW, version=VERSION)
                add_file(out, name, json.dumps(info, indent=2).encode('utf-8'), like=m)
            elif m.isfile():
                out.addfile(m, src.extractfile(m))
            else:
                out.addfile(m)
        for rel, path in EXTRA.items():
            add_file(out, APP + rel, path.read_bytes())
        for addon in ADD:
            base = ADDONS / addon
            for p in sorted(base.rglob('*')):
                rel = p.relative_to(ADDONS).as_posix()
                if '__pycache__' in rel or any((rel + '/').startswith(s) for s in SKIP_IN_ADD):
                    continue
                if p.is_dir():
                    add_dir(out, APP + 'addons/' + rel, seen)
                else:
                    add_dir(out, APP + 'addons/' + p.parent.relative_to(ADDONS).as_posix(), seen)
                    add_file(out, APP + 'addons/' + rel, p.read_bytes())
    return members, buf.getvalue()


def control_tar(old):
    src = tarfile.open(fileobj=io.BytesIO(old))
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0) as gz, tarfile.open(fileobj=gz, mode='w', format=tarfile.GNU_FORMAT) as out:
        for m in src.getmembers():
            if m.isfile():
                text = src.extractfile(m).read().decode('utf-8')
                text = re.sub(r'^Package: .*$', 'Package: %s' % NEW, text, flags=re.M)
                text = re.sub(r'^Version: .*$', 'Version: %s' % VERSION, text, flags=re.M)
                text = re.sub(r'^Description: .*$', 'Description: Neto-IL-TV (Kodi with Idan+ only)', text, flags=re.M)
                add_file(out, m.name, text.encode('utf-8'), like=m)
            else:
                out.addfile(m)
    return buf.getvalue()


def ar_read(data):
    assert data[:8] == b'!<arch>\n'
    pos, files = 8, {}
    while pos < len(data):
        header = data[pos:pos + 60]
        name, size = header[:16].decode().strip().rstrip('/'), int(header[48:58])
        files[name] = data[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)
    return files


def ar_write(entries):
    out = [b'!<arch>\n']
    now = int(time.time())
    for name, data in entries:
        out.append(('%-16s%-12d%-6d%-6d%-8s%-10d`\n' % (name, now, 0, 0, '100644', len(data))).encode())
        out.append(data + (b'\n' if len(data) & 1 else b''))
    return b''.join(out)


def main():
    members, data = data_tar()
    ipk = ar_write([('debian-binary', members['debian-binary']),
                    ('control.tar.gz', control_tar(members['control.tar.gz'])),
                    ('data.tar.gz', data)])
    out = ROOT / 'dist' / ('%s_%s_arm.ipk' % (NEW, VERSION))
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(ipk)
    print('%s  %.1f MB' % (out, len(ipk) / 2 ** 20))


if __name__ == '__main__':
    sys.exit(main())
