# -*- coding: utf-8 -*-
# A00500_reloader - version info

# 01.00  First packaged version. dev/reloader_v02.py + reload_path_list.py +
#        reloader_mayaScript_v02.py (the snippet pasted into Maya by hand) become a dev tool
#        with a shelf installer (__dragDrop_A00500.py). The shelf button reloads config,
#        the reloader itself, then every Framework / tools module in sys.modules, and
#        reports the counts in the viewport. dev/reloader_v02.py stays as a thin re-export
#        so every tool's launch.py (reload_for_tool) keeps working unchanged.

# 01.01  Stale class fix. A module that imports a name re-exported by its package
#        (`from tools.X.app.core import Mgr` in app/ui/main_window.py) is deeper than that
#        package, so it was reloaded first and kept the OLD class - new methods raised
#        AttributeError until the shelf button was pressed a second time (A00110 v02.55
#        `copies_rotation`, 2026-11-11). reload_package now re-reloads only the modules
#        whose globals still point at replaced classes/functions (stale_refs), up to 4 passes.
#        Test: tests/test_stale_refs.py 5/5 (fails 2/5 on 01.00).

VERSION = "01.01"
LAST_UPDATE = "2026-11-11"
