# -*- coding: utf-8 -*-
"""Set widgets for a side-menu section, in the same dialogs as FENtastic's widget manager:
Choose widget (Widget 1-10) > Widget options (Move up, Move down, Display type, Rename, Remake, Remove);
an empty slot adds one. When the list closes, the section is saved, Includes_Dock.xml is rewritten and the skin
reloads, as FENtastic does with its widgets.

  Dock     each widget is a tab: all the options, display types as in FENtastic
  stacked  each widget is a "because you watched" row: display type of the recommendations under it
  buttons  no widget list: one display type for all the section's buttons
"""
import copy
import json

import xbmc
import xbmcgui
import xbmcvfs

from dockil import docks

dialog = xbmcgui.Dialog()
CONFIG = "special://profile/addon_data/skin.dockil/dock_tabs.json"
DOCK_XML = "special://skin/xml/Includes_Dock.xml"
DEFAULT_PATH = "addons://sources/video"


def load_config():
    try:
        with xbmcvfs.File(CONFIG) as f:
            return json.loads(f.read() or "{}")
    except ValueError:
        return {}


def save_config(config):
    xbmcvfs.mkdirs("special://profile/addon_data/skin.dockil/")
    with xbmcvfs.File(CONFIG, "w") as f:
        f.write(json.dumps(config, ensure_ascii=False, indent=1))


def default_section(section_id):
    for sec in docks.SECTIONS:
        if sec["id"] == section_id:
            return copy.deepcopy(sec)
    return None


def clean_label(label):
    label = label.replace("[B]", "").replace("[/B]", "").replace("[I]", "").replace("[/I]", "").replace(" >>", "")
    while "[COLOR" in label:
        start = label.find("[COLOR")
        label = label[:start] + label[label.find("]", start) + 1:]
    return label.replace("[/COLOR]", "").strip()


def files_get_directory(directory):
    request = {"jsonrpc": "2.0", "id": 1, "method": "Files.GetDirectory",
               "params": {"directory": directory, "media": "files", "properties": ["title", "file", "thumbnail"]}}
    try:
        files = json.loads(xbmc.executeJSONRPC(json.dumps(request)))["result"]["files"]
    except (KeyError, TypeError, ValueError):
        return []
    return [i for i in files if i["file"].startswith("plugin://") and i["filetype"] == "directory"]


def path_browser(label="", file=DEFAULT_PATH, thumbnail=""):
    """Browse the add-ons' folders; returns {"label", "file", "thumbnail"} of the chosen one, or {}."""
    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
    results = files_get_directory(file)
    xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
    items, choices = [], []
    if file != DEFAULT_PATH:
        li = xbmcgui.ListItem("Use [COLOR dodgerblue]%s[/COLOR] as path" % clean_label(label), "Set as path",
                              offscreen=True)
        li.setArt({"icon": thumbnail})
        items.append(li)
        choices.append({"label": label, "file": file, "thumbnail": thumbnail})
    for i in results:
        li = xbmcgui.ListItem("%s »" % clean_label(i["label"]), "Browse path...", offscreen=True)
        li.setArt({"icon": i["thumbnail"]})
        items.append(li)
        choices.append({"label": i["label"], "file": i["file"], "thumbnail": i["thumbnail"]})
    choice = dialog.select("Choose path", items, useDetails=True)
    if choice == -1:
        return {}
    chosen = choices[choice]
    if chosen["file"] == file:
        return chosen
    return path_browser(**chosen)


def views_for(kind):
    return list(docks.STACKED_VIEWS) if kind == "stacked" else list(docks.VIEWS)


def choose_view(views, current=None):
    preselect = views.index(current) if current in views else -1
    choice = dialog.select("Choose widget display type", views, preselect=preselect)
    return None if choice == -1 else views[choice]


def ask_label(default):
    return dialog.input("Set widget label", defaultt=clean_label(default)) or None


def new_item(kind):
    """A new or remade widget, from a path chosen in the browser; None if cancelled on the way."""
    result = path_browser()
    if not result:
        return None
    label = ask_label(result["label"])
    if not label:
        return None
    view = choose_view(views_for(kind))
    if not view:
        return None
    return docks.tab(label, {"any": result["file"]}, view)


def widget_options(kind, items, n):
    """Returns True when items changed."""
    choices = ["Move up", "Move down", "Display type", "Rename", "Remake", "Remove"]
    choice = dialog.select("Widget options", choices)
    if choice == -1:
        return False
    action, item = choices[choice], items[n]
    if action in ("Move up", "Move down"):
        m = (n - 1) % len(items) if action == "Move up" else (n + 1) % len(items)
        items[n], items[m] = items[m], items[n]
    elif action == "Display type":
        view = choose_view(views_for(kind), item.get("view"))
        if not view:
            return False
        item["view"] = view
    elif action == "Rename":
        label = ask_label(item["label"])
        if not label:
            return False
        item["label"] = label
    elif action == "Remake":
        made = new_item(kind)
        if not made:
            return False
        items[n] = made
    elif action == "Remove":
        if len(items) == 1:
            dialog.ok("DockIL", "A section needs at least one widget")
            return False
        del items[n]
    return True


def manage(section_id):
    sec = default_section(section_id)
    if not sec:
        return
    kind = sec["kind"]
    config = load_config()
    if kind == "buttons":
        return set_buttons_view(config, section_id, config.get(section_id + ".view") or sec.get("view"))
    items = config.get(section_id) or sec["items"]
    changed = False
    while True:
        rows = ["Widget %d : %s" % (n + 1, "%s | %s" % (clean_label(items[n]["label"]), items[n]["view"])
                                     if n < len(items) else "") for n in range(docks.MAX_ITEMS[kind])]
        choice = dialog.select("Choose widget", rows)
        if choice == -1:
            break
        if choice < len(items):
            changed |= widget_options(kind, items, choice)
        else:
            made = new_item(kind)
            if made:
                items.append(made)
                changed = True
    if changed:
        config[section_id] = items
        apply(config)


def set_buttons_view(config, section_id, current):
    """A buttons section has no widget list, only one tile size for all its buttons."""
    view = choose_view(list(docks.BUTTON_VIEWS), current)
    if view and view != current:
        config[section_id + ".view"] = view
        apply(config)


def apply(config):
    save_config(config)
    with xbmcvfs.File(DOCK_XML, "w") as f:
        f.write(docks.build(config))
    xbmc.executebuiltin("ReloadSkin()")


def remake_all():
    """Back to the default widgets in every section."""
    if not dialog.yesno("DockIL", "Remake all menus with their default widgets?"):
        return
    save_config({})
    with xbmcvfs.File(DOCK_XML, "w") as f:
        f.write(docks.build())
    xbmc.executebuiltin("ReloadSkin()")
