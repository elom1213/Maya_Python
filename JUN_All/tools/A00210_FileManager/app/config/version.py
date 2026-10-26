# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager - version info

# 01.41  Maya > Export sub tab: set rule (json) -> Check Sets (set · playback range · fps · version per file) -> Bake & Export / Export Only
#        (mayapy worker: import references + remove namespaces, bakeResults, top bones to scene root, FBX). Naming Find/Replace + Insert,
#        Overwrite/Cancel popup, report json. mayapy box + file picker shared by the sub tabs. FBX helpers -> Framework/core/maya_fbx.
# 01.40  Maya tab: mayapy_runner / mayapy_process promoted to Framework (Framework/core/mayapy_runner.py,
#        Framework/qt/MOD_mayapyProcess_qt_v01.py) so other standalone tools (A00560_JaliBatch) share the mayapy worker
#        protocol. The two modules here re-export them (no behaviour change).

VERSION = "01.41"
LAST_UPDATE = "2026-10-26"
