# -*- coding: utf-8 -*-
# A00500_reloader - version info

# 01.00  First packaged version. dev/reloader_v02.py + reload_path_list.py +
#        reloader_mayaScript_v02.py (the snippet pasted into Maya by hand) become a dev tool
#        with a shelf installer (__dragDrop_A00500.py). The shelf button reloads config,
#        the reloader itself, then every Framework / tools module in sys.modules, and
#        reports the counts in the viewport. dev/reloader_v02.py stays as a thin re-export
#        so every tool's launch.py (reload_for_tool) keeps working unchanged.

VERSION = "01.00"
LAST_UPDATE = "2026-10-12"
