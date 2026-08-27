# Naming Tool (Qt port)
# Qt(PySide) rewrite of legacy JUN_PY_NamingTool_V03_04.py (maya.cmds UI).
# Tabs:
#   - Naming Dyn  : hierarchy token naming (from legacy Naming Dynamics tab)
#   - Copy Name   : copy base names onto targets with prefix (from legacy Copy name tab)
#   - Quick Rename: Front Insert / Change New / Last Add / -1 trim (ported from ref/ref_01.mel)
#   - Set Rename  : search / replace inside SET names (Maya's own tool cannot reach sets)
#                   Add / Del to edit the listed sets (v01.03)
#   - Copy Name   : also works on SETS - a set cannot reuse a name, so "_copy" is added (v01.03)

VERSION = "01.03"
LAST_UPDATE = "2026-08-27"
