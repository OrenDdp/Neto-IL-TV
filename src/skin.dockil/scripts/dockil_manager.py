# -*- coding: utf-8 -*-
"""RunScript(special://skin/scripts/dockil_manager.py,section=<id>) opens Set widgets for that Dock;
RunScript(special://skin/scripts/dockil_manager.py,remake) brings back the default widgets of every Dock."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dockil import manager  # noqa: E402

args = dict(a.split("=", 1) if "=" in a else (a, "") for a in sys.argv[1:])
if "remake" in args:
    manager.remake_all()
elif args.get("section"):
    manager.manage(args["section"])
