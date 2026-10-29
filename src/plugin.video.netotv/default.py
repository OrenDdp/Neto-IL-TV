# Neto-IL-TV home rows: Idan+'s live channel list split in two, so each half can be its own row on the home page.
#   ?row=live    the main stream of every channel
#   ?row=backup  the backup and hearing-impaired streams
# Items keep Idan+'s own play links, so playing one is exactly the same as playing it from Idan+.
import json
import sys
from urllib.parse import parse_qsl

import xbmc
import xbmcgui
import xbmcplugin

LIVE = 'plugin://plugin.video.idanplus/?mode=1'
SECONDARY = ('גיבוי', 'לקויי שמיעה')


def live_channels():
    req = {'jsonrpc': '2.0', 'id': 1, 'method': 'Files.GetDirectory',
           'params': {'directory': LIVE, 'media': 'video', 'properties': ['title', 'plot', 'art', 'thumbnail']}}
    files = json.loads(xbmc.executeJSONRPC(json.dumps(req))).get('result', {}).get('files') or []
    return [f for f in files if f.get('filetype') == 'file']  # leaves out shortcuts such as "all channels"


def main():
    handle = int(sys.argv[1])
    backup = dict(parse_qsl(sys.argv[2].lstrip('?'))).get('row') == 'backup'
    items = []
    for f in live_channels():
        if any(word in f['label'] for word in SECONDARY) != backup:
            continue
        li = xbmcgui.ListItem(f['label'], offscreen=True)
        li.setArt(f.get('art') or {'thumb': f.get('thumbnail', '')})
        tag = li.getVideoInfoTag()
        tag.setTitle(f.get('title') or f['label'])
        tag.setPlot(f.get('plot', ''))
        li.setProperty('IsPlayable', 'true')
        items.append((f['file'], li, False))
    xbmcplugin.addDirectoryItems(handle, items, len(items))
    xbmcplugin.endOfDirectory(handle)


main()
