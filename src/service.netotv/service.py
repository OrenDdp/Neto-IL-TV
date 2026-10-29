# Neto-IL-TV: makes this Kodi behave like a single app.
# First run: copies the bundled add-ons (payload/: Fishenzon's repository and Idan+'s helpers) into the user add-on
# folder, downloads Idan+ itself from Fishenzon's repository (it is not shipped here), and enables them all.
# Installed into a regular Kodi from our repository, it also sets that Kodi up as the APK does (see setup_kodi).
# The page itself is the FENtastic home screen with the Idan+ tab (skin.fentastic/netotv/), as in Kodi POV IL;
# Back from its side menu hides the app (skin Home.xml), Back while playing stops (keymaps/zz-netotv.xml).
import json
import os
import re
import shutil
import sqlite3
import zipfile
from io import BytesIO

import xbmc
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
PAYLOAD = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('path')), 'payload')
HOME_ADDONS = xbmcvfs.translatePath('special://home/addons')
IDANPLUS = 'plugin.video.idanplus'


def log(msg):
    xbmc.log('[service.netotv] ' + msg, xbmc.LOGINFO)


def version(addon_dir):
    try:
        with open(os.path.join(addon_dir, 'addon.xml'), encoding='utf-8-sig') as f:
            m = re.search(r'<addon\b[^>]*?\sversion="([^"]+)"', f.read())
    except OSError:
        return []
    return [int(n) for n in re.findall(r'\d+', m.group(1))] if m else []


def rpc(method, **params):
    req = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}
    return json.loads(xbmc.executeJSONRPC(json.dumps(req)))


def enabled(addon_id):
    r = rpc('Addons.GetAddonDetails', addonid=addon_id, properties=['enabled'])
    return r.get('result', {}).get('addon', {}).get('enabled', False)


def files(addon_dir):
    """Every file of an add-on with its size, to tell a same-version copy that differs (say POV's patched one)."""
    found = set()
    for root, dirs, names in os.walk(addon_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for n in names:
            p = os.path.join(root, n)
            found.add((os.path.relpath(p, addon_dir), os.path.getsize(p)))
    return found


def fetch_idanplus():
    """Download Idan+ from Fishenzon's repository into the user add-on folder; True when it was added."""
    if os.path.isdir(os.path.join(HOME_ADDONS, IDANPLUS)):
        return False
    import requests  # script.module.requests, a dependency of this add-on
    with open(os.path.join(PAYLOAD, 'repository.Fishenzon', 'addon.xml'), encoding='utf-8') as f:
        repo = f.read()
    info = re.search(r'<info[^>]*>([^<]+)</info>', repo).group(1).strip()
    datadir = re.search(r'<datadir[^>]*>([^<]+)</datadir>', repo).group(1).strip().rstrip('/')
    try:
        listing = requests.get(info, timeout=30).text
        ver = re.search(r'<addon\s+id="%s"[^>]*?\sversion="([^"]+)"' % re.escape(IDANPLUS), listing).group(1)
        url = '%s/%s/%s-%s.zip' % (datadir, IDANPLUS, IDANPLUS, ver)
        data = requests.get(url, timeout=120).content
        with zipfile.ZipFile(BytesIO(data)) as z:
            z.extractall(HOME_ADDONS)
    except Exception as e:  # no network yet: try again next start
        log('could not download Idan+: %s' % e)
        return False
    log('downloaded Idan+ %s from Fishenzon' % ver)
    return True


def install(monitor):
    ids = sorted(os.listdir(PAYLOAD))
    copied = []
    for a in ids:
        src, dst = os.path.join(PAYLOAD, a), os.path.join(HOME_ADDONS, a)
        have, ship = version(dst), version(src)
        # Never downgrade, and leave an identical copy alone: replacing an add-on while the home page
        # is already calling it makes it fail for a moment.
        if have > ship or (have == ship and files(dst) == files(src)):
            continue
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
        copied.append(a)
    if copied:
        log('copied ' + ', '.join(copied))
    if fetch_idanplus():
        copied.append(IDANPLUS)
    if copied:
        xbmc.executebuiltin('UpdateLocalAddons', True)
    if os.path.isdir(os.path.join(HOME_ADDONS, IDANPLUS)):
        ids.append(IDANPLUS)
    # New add-ons are registered a moment after the scan; keep enabling until all are on.
    for _ in range(40):
        missing = [a for a in ids if not enabled(a)]
        if not missing:
            return bool(copied)
        for a in missing:
            rpc('Addons.SetAddonEnabled', addonid=a, enabled=True)
        if monitor.waitForAbort(0.5):
            return False
    log('could not enable: ' + ', '.join(missing))
    return False


def register_tabs():
    """Put the tabs (tabs.json, from tools/make_tabs.py) in the skin helper's list, so that Settings > Skin settings
    shows them by name and can change each row's display type, as in Kodi POV IL. Done again only when an APK brings
    different tabs; changes made in the skin settings stay until then."""
    with open(os.path.join(os.path.dirname(PAYLOAD), 'tabs.json'), encoding='utf-8') as f:
        tabs = json.load(f)
    done_file = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')), 'tabs-version')
    try:
        with open(done_file) as f:
            if f.read().strip() == tabs['version']:
                return
    except OSError:
        pass
    rows = tabs['rows']
    folder = xbmcvfs.translatePath('special://profile/addon_data/script.fentastic.helper/')
    os.makedirs(folder, exist_ok=True)
    db = sqlite3.connect(os.path.join(folder, 'cpath_cache.db'), timeout=20)
    try:
        db.execute('CREATE TABLE IF NOT EXISTS custom_paths (cpath_setting text unique, cpath_path text, '
                   'cpath_header text, cpath_type text, cpath_label text)')
        db.executemany('INSERT OR REPLACE INTO custom_paths VALUES (?, ?, ?, ?, ?)', rows)
        db.commit()
    finally:
        db.close()
    os.makedirs(os.path.dirname(done_file), exist_ok=True)
    with open(done_file, 'w') as f:
        f.write(tabs['version'])
    labels = {'movie': 'MenuMovieLabel', 'tvshow': 'MenuTVShowLabel', 'custom1': 'MenuCustom1Label',
              'custom2': 'MenuCustom2Label', 'custom3': 'MenuCustom3Label'}
    for setting, _, header, _, _ in rows:
        slot, kind = setting.split('.')[:2]
        if kind == 'main_menu':
            xbmc.executebuiltin('Skin.SetString(%s,%s)' % (labels[slot], header))
    log('registered the tabs with the skin helper')


def setup_kodi():
    """In a regular Kodi (installed from our repository, not our APK/IPK, whose own defaults already do this), set it
    up once like the APK: Hebrew, the Neto-IL-TV skin, updates for Idan+, and our remote keys."""
    if xbmcvfs.exists('special://xbmc/system/keymaps/zz-netotv.xml'):
        return  # our APK/IPK
    done_file = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')), 'kodi-setup')
    if os.path.exists(done_file):
        return
    keymaps = xbmcvfs.translatePath('special://profile/keymaps/')
    os.makedirs(keymaps, exist_ok=True)
    shutil.copy(os.path.join(os.path.dirname(PAYLOAD), 'resources', 'zz-netotv.xml'), keymaps)
    for setting, value in (('locale.language', 'resource.language.he_il'), ('locale.country', 'Israel'),
                           ('locale.keyboardlayouts', ['English QWERTY', 'Hebrew QWERTY']),
                           ('subtitles.charset', 'CP1255'), ('addons.unknownsources', True),
                           ('addons.updatemode', 1), ('filelists.showparentdiritems', False),
                           ('lookandfeel.skin', 'skin.fentastic')):
        rpc('Settings.SetSettingValue', setting=setting, value=value)
    xbmc.executebuiltin('Action(reloadkeymaps)')
    os.makedirs(os.path.dirname(done_file), exist_ok=True)
    open(done_file, 'w').close()
    log('set up this Kodi for Neto-IL-TV')


def main():
    monitor = xbmc.Monitor()
    setup_kodi()
    register_tabs()
    copied = install(monitor)
    if copied:
        # The home rows were drawn before Idan+ was installed; draw them again now that it is.
        xbmc.executebuiltin('ReloadSkin()')


main()
