# -*- coding: utf-8 -*-
"""Builds xml/Includes_Dock.xml: the side menu and one group per section.

A section is one of:
  dock     a Dock of tabs (left to right) with a grid of the chosen tab under it
  stacked  rows of "because you watched" titles, each with its recommendations under it (FENtastic stacked widgets)
  buttons  one grid of fixed buttons with icons

Every default Dock tab has a path per player add-on (POV, Fen, Umbrella). A tab shows only when the active player
has a path for it; a section shows only when at least one of its tabs does. The player is the first installed of
POV, Fen, Umbrella. Tabs made in the widget manager (manager.py) have one path and always show.

Plain Python with no Kodi imports: tools/make_docks.py runs it on the PC, manager.py runs it on the TV.
"""
import re
from xml.sax.saxutils import escape

POV = "plugin://plugin.video.pov/?"
FEN = "plugin://plugin.video.fen/?"
UMB = "plugin://plugin.video.umbrella/?"
IDAN = "plugin://plugin.video.idanplus/?"
ROWS = "plugin://plugin.video.dockil.idanrows/?"

PLAYERS = {
    "pov": "plugin.video.pov",
    "fen": "plugin.video.fen",
    "umb": "plugin.video.umbrella",
}

# Idan+ tabs do not depend on the player, only on Idan+ being installed.
IDAN_ON = "System.HasAddon(plugin.video.idanplus)"
# In Neto-IL-TV (its service is installed) the home page is only the Idan+ Dock: no side menu, a full-width grid,
# and its own rows add-on for the live and backup channels.
NETO = "$EXP[dockil_neto]"

# Display types, named as in FENtastic's widget manager. Includes_DockLayout.xml has a layout for each.
VIEWS = ("Poster", "BigPoster", "Landscape", "BigLandscape", "LandscapeInfo", "BigLandscapeInfo", "Category", "Icons")
# Display types of the recommendations row under a stacked row, and the FENtastic widget each one uses
STACKED_VIEWS = {"Poster": "WidgetListPosterStacked", "BigPoster": "WidgetListBigPosterStacked",
                 "Landscape": "WidgetListLandscapeStacked", "BigLandscape": "WidgetListBigLandscapeStacked",
                 "LandscapeInfo": "WidgetListEpisodesStacked", "BigLandscapeInfo": "WidgetListBigEpisodesStacked"}
# Look of all the tiles of a buttons section (one choice for the whole section): Includes_DockLayout.xml has
# a layout for each
BUTTON_VIEWS = {"Icons": "DockButtonsIcons", "Poster": "DockButtonsPoster", "PosterInfo": "DockButtonsPosterInfo",
                "Landscape": "DockButtonsLandscape", "LandscapeInfo": "DockButtonsLandscapeInfo"}
MAX_ITEMS = {"dock": 10, "stacked": 10, "buttons": 20}


def idan(query):
    return IDAN + query + "&iconimage=special%3A%2F%2Fhome%2Faddons%2Fplugin.video.idanplus%2Ficon.png&module=&moredata="


def tab(label, paths, view="BigLandscape"):
    """A Dock tab or a stacked row. paths: {player: path}, or {"idan": path}, or {"any": path} when made in the
    widget manager."""
    return {"label": label, "paths": paths, "view": view}


def button(label, icon, action):
    return {"label": label, "icon": icon, "action": action}


POV_ICONS = "special://home/media/povil_icons/"
POV_MEDIA = "special://home/addons/plugin.video.pov/resources/skins/Default/media/"

SECTIONS = [
    {"id": "tvshows", "label": "סדרות", "icon": "icons/sidemenu/dockil_tvshows.png", "kind": "dock", "items": [
        tab("פופולריות", {
            "pov": POV + "mode=build_tvshow_list&action=trakt_tv_trending",
            "fen": FEN + "mode=build_tvshow_list&action=tmdb_tv_popular",
            "umb": UMB + "action=tvshows&url=traktpopular"}),
        tab("חדשות", {
            "pov": POV + "mode=build_tvshow_list&action=tmdb_tv_premieres",
            "fen": FEN + "mode=build_tvshow_list&action=tmdb_tv_premieres",
            "umb": UMB + "action=tvshows&url=tmdb_newshows"}),
        tab("הפרק הבא", {
            "pov": POV + "mode=build_next_episode",
            "fen": FEN + "mode=build_single_episode&list_type=next",
            "umb": UMB + "action=calendar&url=progress"}),
        tab("הסדרות שלי", {
            "pov": POV + "mode=build_tvshow_list&action=trakt_favorites",
            "umb": UMB + "action=tvshows&url=traktwatchlist"}),
        tab("רשתות", {
            "pov": POV + "mode=navigator.networks&menu_type=tvshow",
            "umb": UMB + "action=tvNetworks"}, "Icons"),
        tab("ז'אנרים", {
            "pov": POV + "mode=navigator.genres&menu_type=tvshow",
            "fen": FEN + "mode=navigator.genres&menu_type=tvshow",
            "umb": UMB + "action=tvGenres&url=trakt_tvshow_genre"}, "Icons"),
    ]},
    {"id": "movies", "label": "סרטים", "icon": "icons/sidemenu/dockil_movies.png", "kind": "dock", "items": [
        tab("פופולריים", {
            "pov": POV + "mode=build_movie_list&action=trakt_movies_trending",
            "fen": FEN + "mode=build_movie_list&action=tmdb_movies_popular",
            "umb": UMB + "action=movies&url=traktpopular"}),
        tab("חדשים", {
            "pov": POV + "mode=build_movie_list&action=tmdb_movies_latest_releases",
            "fen": FEN + "mode=build_movie_list&action=tmdb_movies_premieres",
            "umb": UMB + "action=tmdbmovies&url=tmdb_discovery_released"}),
        tab("המשך צפייה", {
            "pov": POV + "mode=build_movie_list&action=in_progress_movies",
            "fen": FEN + "mode=build_movie_list&action=in_progress_movies",
            "umb": UMB + "action=moviesUnfinished&url=traktunfinished"}),
        tab("הסרטים שלי", {
            "pov": POV + "mode=build_movie_list&action=trakt_favorites",
            "umb": UMB + "action=movies&url=traktwatchlist"}),
        tab("ז'אנרים", {
            "pov": POV + "mode=navigator.genres&menu_type=movie",
            "fen": FEN + "mode=navigator.genres&menu_type=movie",
            "umb": UMB + "action=movieGenres&url=trakt_movie_genre"}, "Icons"),
    ]},
    {"id": "idanplus", "label": "עידן פלוס", "icon": "icons/sidemenu/dockil_livetv.png", "kind": "dock", "items": [
        tab("ערוצים חיים", {"idan": ROWS + "row=live", "neto": "plugin://plugin.video.netotv/?row=live"}),
        tab("המשך צפייה", {"idan": idan("name=%5BB%5D%D7%94%D7%9E%D7%A9%D7%9A+%D7%A6%D7%A4%D7%99%D7%99%D7%94%5B%2FB%5D&url=&mode=27")}),
        tab("מועדפים", {"idan": idan("name=%5BB%5D%D7%9E%D7%95%D7%A2%D7%93%D7%A4%D7%99+%D7%A2%D7%99%D7%93%D7%9F+%D7%A4%D7%9C%D7%95%D7%A1%5B%2FB%5D&url=&mode=10")}),
        tab("VOD", {"idan": idan("name=%5BB%5DVOD%5B%2FB%5D&url=&mode=2")}),
        tab("ערוצי גיבוי", {"idan": ROWS + "row=backup", "neto": "plugin://plugin.video.netotv/?row=backup"}),
    ]},
    # Like POV-IL's "כי צפית": a row of watched titles, and under it the recommendations for the focused one.
    # The titles come through our rows add-on, which drops POV's "כי צפית..." prefix.
    {"id": "byw", "label": "בגלל שראית", "icon": "icons/sidemenu/videos.png", "kind": "stacked", "items": [
        tab("סדרות", {"pov": ROWS + "row=byw&menu_type=tvshow"}, "Landscape"),
        tab("סרטים", {"pov": ROWS + "row=byw&menu_type=movie"}, "Landscape"),
    ]},
    # POV-IL's settings shortcuts, with the icons of its favourites. Each shows only when its add-on is installed.
    {"id": "home", "label": "דף הבית", "icon": "icons/sidemenu/dockil_home.png", "kind": "buttons", "view": "Icons", "items": [
        button("POV", POV_ICONS + "Logo_POV_IL.png", 'RunAddon("plugin.video.pov")'),
        button("חיבור שירותים להרחבת POV", POV_ICONS + "Connect_Services.png",
         'RunPlugin("plugin://plugin.video.pov/?mode=myservices")'),
        button("הגדרת התראות מנוי", POV_ICONS + "Connect_Services.png",
         "RunScript(service.subtitles.kodipovilai,action=debrid_notice_settings)"),
        button("סטטוס מנוי Real Debrid", POV_ICONS + "RD_Account_Status.png",
         'PlayMedia("plugin://plugin.video.pov/?mode=real_debrid.show_account_info&name=Account+Info&isFolder=false")'),
        button("סטטוס מנוי TorBox", POV_MEDIA + "torbox.png",
         "RunPlugin(plugin://plugin.video.pov/?mode=torbox.show_account_info)"),
        button("סטטוס מנוי Premiumize", POV_MEDIA + "premiumize.png",
         'PlayMedia("plugin://plugin.video.pov/?mode=premiumize.show_account_info&name=Account+Info&isFolder=false")'),
        button("בדיקת מהירות", POV_ICONS + "speed_test_icon.png",
         'PlayMedia("plugin://plugin.program.kodipovilwizard/?mode=build_speed_test")'),
        button("שליחת לוג", POV_ICONS + "twilight_send_log.png",
         'ActivateWindow(10025,"plugin://plugin.video.pov/?mode=navigator.log_utils&name=Changelog%20%26%20Log%20Utils",return)'),
        button("אשף ההתקנה", POV_ICONS + "wizard_pov_il.png", 'RunAddon("plugin.program.kodipovilwizard")'),
        button("עדכון מהיר", POV_ICONS + "fast_update_pov_il.png",
         'PlayMedia("plugin://plugin.program.kodipovilwizard/?mode=install&action=quick_update&name=Kodi+POV+IL+-+FENtastic&auto_quick_update=false")'),
        button("10 העדכונים האחרונים", "special://home/media/build_icons/Wizard/wizard_pov_il.png",
         'RunPlugin("plugin://plugin.program.kodipovilwizard/?mode=recentupdates")'),
        button("מי צופה?", "special://home/addons/plugin.program.kodipovilwizard/resources/skins/Default/media/DefaultUser.png",
         "RunPlugin(plugin://plugin.program.kodipovilwizard/?mode=profiles)"),
        button("סידור מועדפים", POV_ICONS + "Order_Favorites.png", "RunAddon(plugin.program.orderfavourites-hebrew)"),
        button("הערב שלי", "special://home/addons/service.subtitles.kodipovilai/resources/media/tonight.png",
         "RunScript(service.subtitles.kodipovilai,action=tonight)"),
    ]},
]

MANAGER = "special://skin/scripts/dockil_manager.py"


def shown(key):
    """Not hidden in the skin settings."""
    return "!Skin.HasSetting(dock.hide.%s)" % key


def player_cond(p):
    """True when p is the active player: installed, and no player before it in PLAYERS is."""
    order = list(PLAYERS)
    earlier_missing = "".join(" + !System.HasAddon(%s)" % PLAYERS[q] for q in order[:order.index(p)])
    return "System.HasAddon(%s)%s" % (PLAYERS[p], earlier_missing)


def path_entries(paths):
    """[(condition, path)] for a tab's paths."""
    if "any" in paths:
        return [("true", paths["any"])]
    if "neto" in paths:
        return [(IDAN_ON + " + " + NETO, paths["neto"]), (IDAN_ON + " + !" + NETO, paths["idan"])]
    if "idan" in paths:
        return [(IDAN_ON, paths["idan"])]
    return [("$EXP[dockil_%s]" % p, path) for p, path in paths.items()]


def action_addon(action):
    """The add-on an action runs, for its visibility condition."""
    m = re.search(r"plugin://([\w.\-]+)/|Run(?:Addon|Script)\(\"?([\w.\-]+)", action)
    return m and (m.group(1) or m.group(2))


def sections_with(config):
    """SECTIONS, with what the widget manager saved: a section's own items ("<id>") and, for buttons, the tile
    size ("<id>.view")."""
    out = []
    for sec in SECTIONS:
        if sec["id"] in config:
            sec = dict(sec, items=config[sec["id"]])
        if sec["id"] + ".view" in config:
            sec = dict(sec, view=config[sec["id"] + ".view"])
        out.append(sec)
    return out


def section_conds(sec):
    if sec["kind"] == "buttons":
        conds = ["System.HasAddon(%s)" % action_addon(b["action"]) for b in sec["items"]]
    else:
        conds = [c for t in sec["items"] for c, _ in path_entries(t["paths"])]
    conds = list(dict.fromkeys(conds))
    return ["true"] if "true" in conds else conds


def focus_id(sec, base):
    return {"dock": base + 40, "stacked": base + 1, "buttons": base + 50}[sec["kind"]]


def dock_section(sec, base):
    dock, grid = base + 40, base + 50
    o = ["\t\t\t<defaultcontrol always=\"true\">%d</defaultcontrol>" % dock,
         '\t\t\t<control type="list" id="%d">' % dock,
         '\t\t\t\t<include content="DockListCommon">',
         '\t\t\t\t\t<param name="id" value="%d"/>' % dock,
         '\t\t\t\t\t<param name="grid_id" value="%d"/>' % grid,
         "\t\t\t\t</include>",
         "\t\t\t\t<content>"]
    for t in sec["items"]:
        for cond, path in path_entries(t["paths"]):
            o += ["\t\t\t\t\t<item>",
                  "\t\t\t\t\t\t<label>%s</label>" % escape(t["label"]),
                  "\t\t\t\t\t\t<property name=\"path\">%s</property>" % escape(path),
                  "\t\t\t\t\t\t<property name=\"view\">%s</property>" % t["view"],
                  # OK opens the tab full screen, where every option of its add-on works; Down goes into the grid
                  "\t\t\t\t\t\t<onclick>ActivateWindow(Videos,&quot;%s&quot;,return)</onclick>" % escape(path),
                  "\t\t\t\t\t\t<visible>%s</visible>" % escape(cond),
                  "\t\t\t\t\t</item>"]
    o += ["\t\t\t\t</content>",
          "\t\t\t</control>",
          '\t\t\t<include content="DockGrid">',
          '\t\t\t\t<param name="id" value="%d"/>' % grid,
          '\t\t\t\t<param name="dock_id" value="%d"/>' % dock,
          "\t\t\t</include>"]
    return o


def stacked_section(sec, base):
    # FENtastic's stacked widgets: the title row needs a 5-digit id, its recommendations row is that id + "1".
    o = ["\t\t\t<defaultcontrol always=\"true\">%d</defaultcontrol>" % (base + 1),
         '\t\t\t<control type="grouplist" id="%d">' % (base + 1),
         "\t\t\t\t<include>WidgetGroupListCommon</include>",
         "\t\t\t\t<onleft>9000</onleft>",
         "\t\t\t\t<onback>9000</onback>"]
    for n, row in enumerate(sec["items"]):
        list_id = base + 13 + n * 10
        for cond, path in path_entries(row["paths"]):
            o += ['\t\t\t\t<include content="WidgetListCategoryStacked">',
                  '\t\t\t\t\t<param name="content_path" value="%s"/>' % escape(path, {'"': "&quot;"}),
                  '\t\t\t\t\t<param name="widget_header" value="%s"/>' % escape(row["label"]),
                  '\t\t\t\t\t<param name="widget_target" value="videos"/>',
                  '\t\t\t\t\t<param name="list_id" value="%d"/>' % list_id,
                  '\t\t\t\t\t<param name="visible" value="%s"/>' % escape(cond, {'"': "&quot;"}),
                  "\t\t\t\t</include>",
                  '\t\t\t\t<include content="%s">' % STACKED_VIEWS.get(row["view"], "WidgetListLandscapeStacked"),
                  '\t\t\t\t\t<param name="content_path" value="$INFO[Window(Home).Property(fentastic.%d.path)]"/>' % list_id,
                  '\t\t\t\t\t<param name="widget_header" value="$INFO[Window(Home).Property(fentastic.%d.label)]"/>' % list_id,
                  '\t\t\t\t\t<param name="widget_target" value="videos"/>',
                  '\t\t\t\t\t<param name="list_id" value="%d1"/>' % list_id,
                  "\t\t\t\t</include>"]
    o.append("\t\t\t</control>")
    return o


def buttons_section(sec, base):
    o = ["\t\t\t<defaultcontrol always=\"true\">%d</defaultcontrol>" % (base + 50),
         '\t\t\t<control type="panel" id="%d">' % (base + 50),
         "\t\t\t\t<include>%s</include>" % BUTTON_VIEWS.get(sec.get("view"), BUTTON_VIEWS["Icons"]),
         "\t\t\t\t<content>"]
    for b in sec["items"]:
        o += ["\t\t\t\t\t<item>",
              "\t\t\t\t\t\t<label>%s</label>" % escape(b["label"]),
              "\t\t\t\t\t\t<icon>%s</icon>" % escape(b["icon"]),
              "\t\t\t\t\t\t<onclick>%s</onclick>" % escape(b["action"]),
              "\t\t\t\t\t\t<visible>System.HasAddon(%s)</visible>" % action_addon(b["action"]),
              "\t\t\t\t\t</item>"]
    o += ["\t\t\t\t</content>",
          "\t\t\t</control>"]
    return o


def settings_page(sections):
    """Skin settings > main menu items: as in FENtastic, each section with a toggle and Set widgets."""
    ids = iter(range(62000, 63000))  # grouplist children need ids to take focus
    o = ['\t<include name="DockSettings">',
         '\t\t<control type="button" id="%d">' % next(ids),
         "\t\t\t<label>Remake menus and widgets</label>",
         "\t\t\t<include>DefaultSettingButton</include>",
         "\t\t\t<onclick>RunScript(%s,remake)</onclick>" % MANAGER,
         "\t\t</control>"]
    for sec in sections:
        o += ['\t\t<control type="radiobutton" id="%d">' % next(ids),
              "\t\t\t<label>[B]%s[/B]</label>" % escape(sec["label"]),
              "\t\t\t<include>DefaultSettingButton</include>",
              "\t\t\t<selected>%s</selected>" % shown(sec["id"]),
              "\t\t\t<onclick>Skin.ToggleSetting(dock.hide.%s)</onclick>" % sec["id"],
              "\t\t</control>"]
        o += ['\t\t<control type="button" id="%d">' % next(ids),
              "\t\t\t<label>   - %s</label>" % ("Display type" if sec["kind"] == "buttons" else "Set widgets"),
              "\t\t\t<include>DefaultSettingButton</include>",
              "\t\t\t<onclick>RunScript(%s,section=%s)</onclick>" % (MANAGER, sec["id"]),
              "\t\t\t<visible>%s</visible>" % shown(sec["id"]),
              "\t\t</control>"]
    o.append("\t</include>")
    return o


def build(config=None):
    sections = sections_with(config or {})
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         "<!-- Written by scripts/dockil/docks.py (tools/make_docks.py on the PC, Set widgets on the TV). -->",
         "<includes>"]
    for p in PLAYERS:
        o.append('\t<expression name="dockil_%s">%s</expression>' % (p, escape(player_cond(p))))
    o.append('\t<expression name="dockil_neto">System.HasAddon(service.netotv)</expression>')

    # side menu
    o.append('\t<include name="DockMainMenu">')
    for n, sec in enumerate(sections):
        base = 30000 + n * 100
        o += ["\t\t<item>",
              "\t\t\t<label>%s</label>" % escape(sec["label"]),
              "\t\t\t<onclick>SetFocus(%d)</onclick>" % focus_id(sec, base),
              "\t\t\t<property name=\"menu_id\">$NUMBER[%d]</property>" % focus_id(sec, base),
              "\t\t\t<property name=\"id\">dock_%s</property>" % sec["id"],
              "\t\t\t<thumb>%s</thumb>" % sec["icon"],
              "\t\t\t<visible>%s</visible>" % escape("[%s] + %s%s" % (
                  " | ".join("[%s]" % c for c in section_conds(sec)), shown(sec["id"]),
                  "" if sec["id"] == "idanplus" else " + !" + NETO)),
              "\t\t</item>"]
    o.append("\t</include>")

    o += settings_page(sections)

    # one group per section
    o.append('\t<include name="DockSections">')
    for n, sec in enumerate(sections):
        base = 30000 + n * 100
        o += ['\t\t<control type="group" id="%d">' % base,
              "\t\t\t<visible>String.IsEqual(Container(9000).ListItem.Property(id),dock_%s)</visible>" % sec["id"],
              '\t\t\t<include content="Visible_Right_Delayed"><param name="id" value="dock_%s"/></include>' % sec["id"]]
        o += {"dock": dock_section, "stacked": stacked_section, "buttons": buttons_section}[sec["kind"]](sec, base)
        o.append("\t\t</control>")
    o.append("\t</include>")
    o.append("</includes>\n")
    return "\n".join(o)
