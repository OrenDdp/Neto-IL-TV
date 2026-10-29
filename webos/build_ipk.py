# Builds Neto-IL-TV for LG webOS: the official Kodi 21.0 webOS package, renamed to org.xbmc.neto and carrying the same
# add-ons, tabs and settings as the Android build (work/assets). Edits the archive in place with tarfile, because the
# package holds Linux symlinks that a Windows checkout cannot extract.
#     python -I webos/build_ipk.py          ->   webos/dist/org.xbmc.neto_<version>_arm.ipk   (side-menu tabs)
#     python -I webos/build_ipk.py dock     ->   webos/dist/org.xbmc.net2_<version>_arm.ipk   (one page: dock + grid)
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
DOCK = 'dock' in sys.argv[1:]                         # the one-page variant, installable next to the tabs one
OLD, NEW = 'org.xbmc.kodi', ('org.xbmc.net2' if DOCK else 'org.xbmc.neto')  # same length: patched in the binary too
TITLE = 'Neto-IL-TV Dock' if DOCK else 'Neto-IL-TV'
# Follows service.netotv's version, so both builds move together: 1.0.16 -> 21.0.16
_service = re.search(r'<addon\b[^>]*\sversion="([^"]+)"', ADDONS.joinpath('service.netotv/addon.xml').read_text(encoding='utf-8'))
VERSION = '21.0.%s' % _service.group(1).split('.')[-1]
APP = 'usr/palm/applications/%s/' % NEW
PACKAGEINFO = 'usr/palm/packages/%s/packageinfo.json' % NEW

# Not needed for Idan+ on a TV remote (as in the Android build), plus the recording-server clients webOS ships.
DROP = ('audioencoder.', 'game.controller.mouse', 'game.controller.snes', 'peripheral.joystick',
        'service.xbmc.versioncheck', 'screensaver.xbmc.builtin.dim', 'pvr.',
        # Only Idan+ and what it needs: no official Kodi repository (its updates of bundled add-ons fail on webOS)
        # and no library scrapers, weather icons or unused Python modules.
        'repository.xbmc.org', 'metadata.album.universal', 'metadata.artists.universal', 'metadata.common.allmusic.com', 'metadata.common.fanart.tv', 'metadata.common.musicbrainz.org', 'metadata.common.theaudiodb.com', 'metadata.generic.albums', 'metadata.generic.artists', 'metadata.themoviedb.org.python', 'metadata.tvshows.themoviedb.org.python', 'resource.images.weathericons.default', 'script.module.pil', 'script.module.pycryptodome')
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
    'musiclibrary.albumsscraper': '', 'musiclibrary.artistsscraper': '', 'scrapers.moviesdefault': 'metadata.local', 'scrapers.tvshowsdefault': 'metadata.local',
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
    info.update(id=NEW, title=TITLE, version=VERSION, vendor='local')
    return json.dumps(info, ensure_ascii=False, indent=2)


def binary(data):
    old, new = (OLD + '\0').encode(), (NEW + '\0').encode()
    assert data.count(old) == 1, 'expected the app id once in kodi-webos'
    return data.replace(old, new)


def idanplus(name, mode):
    from urllib.parse import quote_plus
    return ('plugin://plugin.video.idanplus/?name=%s&amp;url=&amp;mode=%d&amp;iconimage=%s&amp;module=&amp;moredata='
            % (quote_plus('[B]%s[/B]' % name), mode, quote_plus('special://home/addons/plugin.video.idanplus/icon.png')))


# The dock variant's categories, left to right (same lists as the tabs in tools/make_tabs.py).
DOCK_ITEMS = [('ערוצים חיים', 'plugin://plugin.video.netotv/?row=live'), ('VOD', idanplus('VOD', 2)),
              ('המשך צפייה', idanplus('המשך צפייה', 27)), ('מועדפים', idanplus('מועדפי עידן פלוס', 10)),
              ('ערוצי גיבוי', 'plugin://plugin.video.netotv/?row=backup')]


def dock_home(xml):
    """The one-page home: no side menu; a dock of the categories right of the logo and icons, and the chosen one as a
    full-width grid below. Built from the tabs Home.xml so both variants keep every other change."""
    xml = xml.replace('<defaultcontrol>9000</defaultcontrol>', '<defaultcontrol>23040</defaultcontrol>', 1)
    xml = xml.replace('<control type="fixedlist" id="9000">', '<control type="fixedlist" id="9000">\n\t\t\t\t\t\t<visible>false</visible>', 1)
    xml = xml.replace('<ondown>SetFocus(9000,0,absolute)</ondown>', '<ondown>23040</ondown>', 1)
    i = xml.index('<control type="grouplist" id="700">')
    xml = xml[:i] + xml[i:].replace('<onright>2000</onright>', '<onright>23040</onright>', 1)
    items = ''.join('\t\t\t\t\t\t\t<item>\n\t\t\t\t\t\t\t\t<label>%s</label>\n\t\t\t\t\t\t\t\t<property name="path">%s</property>\n'
                    '\t\t\t\t\t\t\t\t<onclick>SetFocus(23050)</onclick>\n\t\t\t\t\t\t\t</item>\n' % it for it in DOCK_ITEMS)
    block = """				<!-- Neto-IL-TV Dock: the categories as a dock (Left/Right), the chosen one as a grid below (Down) -->
				<control type="group" id="23000">
					<visible>String.IsEqual(Container(9000).ListItem.Property(id),custom1)</visible>
					<defaultcontrol always="true">23040</defaultcontrol>
					<control type="list" id="23040">
						<left>0</left>
						<top>90</top>
						<width>1400</width>
						<height>80</height>
						<orientation>horizontal</orientation>
						<scrolltime tween="cubic" easing="out">300</scrolltime>
						<onleft>700</onleft>
						<onup>700</onup>
						<ondown>23050</ondown>
						<onback>Minimize</onback>
						<itemlayout width="275" height="80">
							<control type="label">
								<width>255</width>
								<height>80</height>
								<align>center</align>
								<aligny>center</aligny>
								<font>font32</font>
								<textcolor>unfocused_text</textcolor>
								<label>$INFO[ListItem.Label]</label>
							</control>
						</itemlayout>
						<focusedlayout width="275" height="80">
							<control type="image">
								<width>255</width>
								<height>80</height>
								<texture colordiffuse="button_focus">masks/categorywidget.png</texture>
								<visible>Control.HasFocus(23040)</visible>
							</control>
							<control type="label">
								<width>255</width>
								<height>80</height>
								<align>center</align>
								<aligny>center</aligny>
								<font>font32</font>
								<textcolor>white</textcolor>
								<label>[B]$INFO[ListItem.Label][/B]</label>
							</control>
						</focusedlayout>
						<content>
%s						</content>
					</control>
					<include content="BusyListSpinner">
						<param name="list_id" value="23050"/>
						<param name="posy" value="330"/>
					</include>
					<control type="panel" id="23050">
						<left>-417</left>
						<top>230</top>
						<width>1830</width>
						<height>840</height>
						<orientation>vertical</orientation>
						<scrolltime tween="cubic" easing="out">500</scrolltime>
						<onup>23040</onup>
						<onleft>23050</onleft>
						<onback>SetFocus(23050,0,absolute)</onback>
						<onback>23040</onback>
						<itemlayout width="448" height="290">
							<control type="group">
								<left>68</left>
								<top>15</top>
								<include content="BigWideInfoWallMovieLayout">
									<param name="focused" value="false" />
									<param name="list_id" value="23050" />
								</include>
							</control>
						</itemlayout>
						<focusedlayout width="448" height="290">
							<control type="group">
								<depth>DepthContentPopout</depth>
								<left>68</left>
								<top>15</top>
								<include content="BigWideInfoWallMovieLayout">
									<param name="focused" value="true" />
									<param name="list_id" value="23050" />
								</include>
							</control>
						</focusedlayout>
						<content target="videos">$INFO[Container(23040).ListItem.Property(path)]</content>
					</control>
				</control>
""" % items
    s0 = xml.index('\t\t\t\t<!-- CUSTOM 1 -->')
    s1 = xml.index('\t\t\t\t<!-- CUSTOM 2 -->')
    return xml[:s0] + block + xml[s1:]


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
                    data = p.read_bytes()
                    if DOCK and rel == 'skin.fentastic/xml/Home.xml':
                        data = dock_home(data.decode('utf-8')).encode('utf-8')
                    add_file(out, APP + 'addons/' + rel, data)
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
