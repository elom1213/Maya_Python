# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - version info

# 01.00  Two tabs.
#        Pose Map : pick a node with phoneme attributes (e.g. JALI_IN) and a target node (a
#        blendShape -> its target aliases, or any node with numeric attributes). Per phoneme,
#        set the target values it should give at the reference value (default 10, any real
#        number). Builds one blendWeighted (+ clamp) per target, edits weights live, Solo
#        preview, Capture the current result, save / load the relation as json and Connect
#        it to any other node pair (existing target connections: Skip by default).
#        Blend Weights : list a blendWeighted's inputs / weights, flag inputs without a weight
#        element (computed as 1.0 but hidden in the UI), add an input together with its
#        weight, create the missing weights (1.0 - result unchanged), remove input + weight.

# 01.01  Pose Map > Source list : Shift / Ctrl multi-select (shared checkList behaviour - clicking
#        the check box of a selected row checks / unchecks every selected row), "Check Sel" /
#        "Uncheck Sel" buttons, and a "Check All" <-> "Uncheck All" toggle.

# 01.02  Menu "Library > Show Libraries Folder" : opens app/libraries (the saved pose library
#        json files) in Explorer.

# 01.03  Solo preview stays on until its check box is clicked off (or the window closes). It used
#        to turn itself off when a target value changed (the phoneme label "AHH" -> "AHH (1)" fires
#        QListWidget.itemChanged, read as a check change), on tab change, on focus-out of the node
#        fields, on Capture and on Remove Network. Now those keep it on and re-apply it
#        (new source / new checks / after Capture).

VERSION = "01.03"
LAST_UPDATE = "2026-10-19"
