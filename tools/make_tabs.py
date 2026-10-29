# Writes the side-menu tabs of the home page and the row under each one (skin.fentastic/netotv/ and xml/).
# FENtastic has five tab slots; each Idan+ category takes one. Change TABS and run:
#     python -I tools/make_tabs.py
# then rebuild. The order in the menu is set in xml/Home.xml (the <content> of list 9000).
import hashlib
import json
from pathlib import Path
from urllib.parse import quote_plus

WORK = Path(__file__).resolve().parent.parent / 'work/assets/addons'
SKIN = WORK / 'skin.fentastic'
ICON = quote_plus('special://home/addons/plugin.video.idanplus/icon.png')


def idanplus(name, mode):
    return ('plugin://plugin.video.idanplus/?name=%s&amp;url=&amp;mode=%d&amp;iconimage=%s&amp;module=&amp;moredata='
            % (quote_plus('[B]%s[/B]' % name), mode, ICON))


# (skin slot, menu include, row include, menu id, tab name, icon, content path, row template, text when empty)
TABS = [
    ('custom1', 'Custom1MainMenu', 'Custom1Widgets', 23000, 'מועדפים', 'favourites.png',
     idanplus('מועדפי עידן פלוס', 10), 'WidgetListBigLandscapeGrid', None),
    ('custom2', 'Custom2MainMenu', 'Custom2Widgets', 24000, 'ערוצים חיים', 'livetv.png',
     'plugin://plugin.video.netotv/?row=live', 'WidgetListBigLandscapeGrid', None),
    ('custom3', 'Custom3MainMenu', 'Custom3Widgets', 25000, 'המשך צפייה', 'videos.png',
     idanplus('המשך צפייה', 27), 'WidgetListLandscapeAlways', 'עוד לא התחלת לצפות בתוכניות מ-VOD'),
    ('movies', 'MoviesMainMenu', 'MovieWidgets', 19000, 'VOD', 'movies.png',
     idanplus('VOD', 2), 'WidgetListBigLandscapeGrid', None),
    ('tvshows', 'TVShowsMainMenu', 'TVShowWidgets', 22000, 'ערוצי גיבוי', 'tv.png',
     'plugin://plugin.video.netotv/?row=backup', 'WidgetListBigLandscapeGrid', None),
]
FILES = {'custom1': 'custom1', 'custom2': 'custom2', 'custom3': 'custom3', 'movies': 'movies', 'tvshows': 'tvshows'}
# The helper names the movie and tv slots without the s; its labels end in the display type's name.
HELPER_SLOT = {'movies': 'movie', 'tvshows': 'tvshow'}
TYPE_NAME = {'WidgetListLandscape': 'Landscape', 'WidgetListBigLandscape': 'BigLandscape',
             'WidgetListLandscapeGrid': 'Grid',
             'WidgetListBigLandscapeGrid': 'BigLandscape Grid', 'WidgetListLandscapeAlways': 'BigLandscape Grid'}
HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Neto-IL-TV: made by tools/make_tabs.py -->\n<includes>\n'


def menu(slot, include, menu_id, name, icon, path):
    return HEAD + ('    <include name="%s">\n        <item>\n'
                   '            <label>[B]%s[/B]</label>\n'
                   '            <onclick>ActivateWindow(Videos,%s,return)</onclick>\n'
                   '            <property name="menu_id">$NUMBER[%d]</property>\n'
                   '            <thumb>icons/sidemenu/%s</thumb>\n'
                   '            <property name="id">%s</property>\n'
                   '        </item>\n    </include>\n</includes>\n' % (include, name, path, menu_id, icon, slot))


def row(include, menu_id, name, path, template, empty):
    extra = '            <param name="empty_label" value="%s"/>\n' % empty if empty else ''
    return HEAD + ('    <include name="%s">\n        <include content="%s">\n'
                   '            <param name="content_path" value="%s"/>\n'
                   '            <param name="widget_header" value="[B][COLOR yellow]%s[/COLOR][/B]"/>\n'
                   '            <param name="widget_target" value="videos"/>\n'
                   '            <param name="list_id" value="%d"/>\n%s'
                   '        </include>\n    </include>\n</includes>\n' % (include, template, path, name, menu_id + 11, extra))


helper = []  # rows of the skin helper's list (cpath_cache.db), so Settings > Skin can change a row's display type
for slot, menu_inc, row_inc, menu_id, name, icon, path, template, empty in TABS:
    key, raw = HELPER_SLOT.get(slot, slot), path.replace('&amp;', '&')
    header = '[B][COLOR yellow]%s[/COLOR][/B]' % name
    helper += [[key + '.main_menu', raw, '[B]%s[/B]' % name, '', ''],
               [key + '.widget.1', raw, header, template, '%s | %s' % (header, TYPE_NAME[template])]]
    files = {'main_menu_' + FILES[slot]: menu(slot, menu_inc, menu_id, name, icon, path),
             'widget_' + FILES[slot]: row(row_inc, menu_id, name, path, template, empty)}
    for folder in ('netotv', 'xml'):
        for f, text in files.items():
            (SKIN / folder / ('script-fentastic-%s.xml' % f)).write_text(text, encoding='utf-8')
# version: the service registers the tabs again when they change in a new APK
version = hashlib.sha1(json.dumps(helper, ensure_ascii=False).encode('utf-8')).hexdigest()[:12]
(WORK / 'service.netotv/tabs.json').write_text(json.dumps({'version': version, 'rows': helper}, ensure_ascii=False, indent=1),
                                               encoding='utf-8')
print('%d tabs written' % len(TABS))
