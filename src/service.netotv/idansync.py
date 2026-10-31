# Idan+'s watch records shared between Kodi installs through one network folder (for example smb://server/kodi-sync/).
# Every install writes only its own file there (<id>.json) and reads everyone's, so two writers never touch the same file.
# Merging keeps the newest of each record:
#   progress.json  where each episode stopped        newest 't' wins
#   hidden.json    series removed from Continue      newest time wins
#   seasons.json   the saved seasons (series, order) newest 'fetched' wins
#   episodes.json  plot, aired date, duration        facts are added, never removed
# Idan+'s service keeps progress.json in memory and writes it all back after each viewing, which drops what was merged in
# from the others; the next round puts it back (the folder still has it), so records are never lost, only late by a round.
# The same file is used by service.netotv (Neto-IL-TV) and plugin.video.dockil.idanrows (David-DockIL).
import json
import os
import uuid

import xbmc
import xbmcvfs

IDANPLUS = 'plugin.video.idanplus'
FILES = ('progress', 'hidden', 'seasons', 'episodes')


def log(msg):
    xbmc.log('[idansync] %s' % msg, xbmc.LOGINFO)


def _read_local(folder, name):
    try:
        with open(os.path.join(folder, name + '.json'), encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_local(folder, name, data):
    path = os.path.join(folder, name + '.json')
    tmp = path + '.idansync'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, path)


def _read_remote(path):
    f = xbmcvfs.File(path)
    try:
        data = json.loads(f.read() or '{}')
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}
    finally:
        f.close()


def _newest(mine, theirs, stamp):
    """Records of both, keeping the one with the larger stamp(record) for keys both have."""
    out = dict(mine)
    for key, rec in theirs.items():
        if key not in out or stamp(rec) > stamp(out[key]):
            out[key] = rec
    return out


def _num(value):
    return value if isinstance(value, (int, float)) else 0


def merge(name, mine, theirs):
    if name == 'progress':
        return _newest(mine, theirs, lambda r: _num(r.get('t')) if isinstance(r, dict) else 0)
    if name == 'hidden':
        return _newest(mine, theirs, _num)
    if name == 'seasons':
        seasons = _newest(mine.get('seasons', {}), theirs.get('seasons', {}),
                          lambda r: _num(r.get('fetched')) if isinstance(r, dict) else 0)
        return dict(mine, seasons=seasons) if seasons or 'seasons' in mine else {}
    # episodes: per episode, add the facts this install does not know yet
    out = dict(mine)
    for key, facts in theirs.items():
        if isinstance(facts, dict):
            known = out.get(key) if isinstance(out.get(key), dict) else {}
            out[key] = dict(facts, **known)
    return out


class Sync(object):
    def __init__(self, own_profile, folder, fix_local=None):
        """`own_profile` is the calling add-on's addon_data (it keeps this install's id), `folder` the shared folder,
        `fix_local(watch_folder)` runs after records were merged in (Neto/DockIL use it to put seasons in order)."""
        self.folder = folder.rstrip('/') + '/'
        self.watch = xbmcvfs.translatePath('special://profile/addon_data/%s/watch' % IDANPLUS)
        self.fix_local = fix_local
        self.id = self._own_id(own_profile)
        self.pushed = None

    def _own_id(self, profile):
        path = os.path.join(xbmcvfs.translatePath(profile), 'idansync_id')
        try:
            with open(path) as f:
                own = f.read().strip()
            if own:
                return own
        except OSError:
            pass
        own = uuid.uuid4().hex[:12]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(own)
        return own

    def run(self, pull=True):
        """One round: read the others' files, merge them into Idan+'s, then publish ours. Returns True when Idan+'s
        files changed. `pull=False` only publishes (used while something plays, when Idan+ holds progress in memory)."""
        if not os.path.isdir(self.watch):
            return False
        if not xbmcvfs.exists(self.folder):
            if not xbmcvfs.mkdirs(self.folder):
                return False   # server off or folder unreachable: try again next round
        local = {name: _read_local(self.watch, name) for name in FILES}
        changed = False
        if pull:
            _, files = xbmcvfs.listdir(self.folder)
            merged = dict(local)
            for fname in files:
                if not fname.endswith('.json') or fname == self.id + '.json':
                    continue
                theirs = _read_remote(self.folder + fname)
                for name in FILES:
                    if isinstance(theirs.get(name), dict):
                        merged[name] = merge(name, merged[name], theirs[name])
            for name in FILES:
                if merged[name] != local[name]:
                    _write_local(self.watch, name, merged[name])
                    changed = True
            if changed:
                if self.fix_local:
                    self.fix_local(self.watch)
                local = {name: _read_local(self.watch, name) for name in FILES}
                log('merged records from the other installs')
        text = json.dumps(local, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
        if text != self.pushed:
            f = xbmcvfs.File(self.folder + self.id + '.json', 'w')
            try:
                if f.write(text):
                    self.pushed = text
            finally:
                f.close()
        return changed
