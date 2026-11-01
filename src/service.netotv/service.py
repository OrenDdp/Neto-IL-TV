# Neto-IL-TV: makes this Kodi behave like a single app.
# First run: copies the bundled add-ons (payload/: Fishenzon's repository and Idan+'s helpers) into the user add-on
# folder, downloads Idan+ itself from Fishenzon's repository (it is not shipped here), and enables them all.
# Installed into a regular Kodi from our repository, it also sets that Kodi up as the APK does (see setup_kodi).
# The page itself is the Idan+ Dock of the DockIL skin (skin.dockil, which turns to its Neto-IL-TV mode when this
# service is installed); Back from the Dock hides the app, Back while playing stops (keymaps/zz-netotv.xml).
# With the "sync folder" setting set, Idan+'s watch records are shared with the other Kodi installs (idansync.py).
import json
import os
import re
import shutil
import sqlite3
import time
import zipfile
from io import BytesIO

import xbmc
import xbmcaddon
import xbmcvfs

from idansync import Sync

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
                           ('lookandfeel.skin', 'skin.dockil')):
        rpc('Settings.SetSettingValue', setting=setting, value=value)
    xbmc.executebuiltin('Action(reloadkeymaps)')
    os.makedirs(os.path.dirname(done_file), exist_ok=True)
    open(done_file, 'w').close()
    log('set up this Kodi for Neto-IL-TV')


def move_to_dockil():
    """Up to 1.0.30 the skin was our FENtastic (skin.fentastic), which updates no longer bring: switch to DockIL once,
    with the skin settings made so far."""
    skin = rpc('Settings.GetSettingValue', setting='lookandfeel.skin').get('result', {}).get('value')
    if skin != 'skin.fentastic':
        return
    data = xbmcvfs.translatePath('special://profile/addon_data/')
    old, new = os.path.join(data, 'skin.fentastic', 'settings.xml'), os.path.join(data, 'skin.dockil', 'settings.xml')
    if os.path.exists(old) and not os.path.exists(new):
        os.makedirs(os.path.dirname(new), exist_ok=True)
        shutil.copy(old, new)
    rpc('Settings.SetSettingValue', setting='lookandfeel.skin', value='skin.dockil')
    log('moved from skin.fentastic to skin.dockil')


def seed_favourites():
    """Personal builds only: start Idan+'s favourites from resources/favorites.json (not published) once, if empty."""
    src = os.path.join(os.path.dirname(PAYLOAD), 'resources', 'favorites.json')
    dst = xbmcvfs.translatePath('special://profile/addon_data/%s/favorites.json' % IDANPLUS)
    if os.path.exists(src) and not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
        log('added the personal Idan+ favourites')


def fix_episode_order(path):
    """Idan+ saves each season's episodes in the site's order, and mako lists them newest first, so its "next episode"
    points backwards. Put every season whose episodes all carry distinct numbers in episode-number order; seasons
    already in that order (the other channels) are left exactly as they are."""
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return
    changed = False
    for season in data.get('seasons', {}).values():
        order, eps = season.get('order', []), season.get('eps', {})
        numbers = [eps.get(k, {}).get('number') for k in order]
        if len(order) < 2 or not all(isinstance(n, int) for n in numbers) or len(set(numbers)) != len(numbers):
            continue
        fixed = sorted(order, key=lambda k: eps[k]['number'])
        if fixed != order:
            season['order'] = fixed
            changed = True
    if changed:
        tmp = path + '.netotv'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        os.replace(tmp, path)
        log('put episodes in episode-number order')


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def main():
    monitor = xbmc.Monitor()
    seed_favourites()
    setup_kodi()
    move_to_dockil()
    register_tabs()
    copied = install(monitor)
    if copied:
        # The home rows were drawn before Idan+ was installed; draw them again now that it is.
        xbmc.executebuiltin('ReloadSkin()')
    # Idan+ rewrites its saved seasons whenever a season is opened: fix the order again after each change.
    seasons = xbmcvfs.translatePath('special://profile/addon_data/%s/watch/seasons.json' % IDANPLUS)
    progress = os.path.join(os.path.dirname(seasons), 'progress.json')
    player = xbmc.Player()
    folder = ADDON.getSetting('sync_folder').strip()
    sync = Sync('special://profile/addon_data/service.netotv/', folder,
                lambda watch: fix_episode_order(os.path.join(watch, 'seasons.json'))) if folder else None
    seen = progress_seen = None
    last_sync = 0
    while not monitor.waitForAbort(3):
        if mtime(seasons) != seen:
            fix_episode_order(seasons)
            seen = mtime(seasons)
        # Sync every 30 seconds, and as soon as Idan+ wrote new progress (a viewing stopped or reached a minute).
        if sync and (time.time() - last_sync >= 30 or mtime(progress) != progress_seen):
            try:
                sync.run(pull=not player.isPlaying())
            except Exception as e:  # a network error must never stop the service
                log('sync: %s' % e)
            last_sync, progress_seen, seen = time.time(), mtime(progress), mtime(seasons)

main()
