# Naming Tool (Qt port)
# Qt(PySide) rewrite of legacy JUN_PY_NamingTool_V03_04.py (maya.cmds UI).
# Tabs:
#   - Naming Dyn  : hierarchy token naming (from legacy Naming Dynamics tab)
#   - Copy Name   : copy base names onto targets with prefix (from legacy Copy name tab)
#   - Quick Rename: Front Insert / Change New / Last Add / -1 trim (ported from ref/ref_01.mel)
#   - Set Rename  : search / replace inside SET names (Maya's own tool cannot reach sets)
#                   Add / Del to edit the listed sets (v01.03)
#   - Copy Name   : also works on SETS - a set cannot reuse a name, so "_copy" is added (v01.03)
#   - Copy Name   : Search / Replace a word inside the Base name before copying (v01.05)

#   - Rename      : new parent tab - Token (was Naming Dyn) and Set Rename are its sub tabs (v01.07)
#   - Token       : any number of tokens, each Custom (text) or Numbering (Start + Pad 0),
#                   Add / Delete Token at the picked place, horizontal scroll, profiles as JSON (v01.07)

#   - Token       : each token column is 2/3 as wide (120 -> 80 px); Start / Pad 0 labels sit
#                   above their spin boxes so everything still fits (v01.08)

#   - Quick Rename: split into sub tabs Selection (the old buttons) and Insert (new).
#                   Insert puts text at the n-th position of every listed name
#                   (0 = front, -1 = end, negative counts from the end); a live preview
#                   table shows the new names, nothing changes until Apply (v01.09)
#                   The inserted text is drawn in green in the New name column.

#   - Token       : the Profile + Tokens screen is now the shared Framework widget
#                   MOD_tokenName_qt_v01 (rules/profiles: Framework.core.token_naming), also used by
#                   A00480_FileTool Export > Naming. Same look and behaviour, same profile files (v01.10)

#   - Token       : editing a token no longer saves it to the profile - the new Save button on the
#                   Profile row does (shared widget change, same as A00480 v01.08) (v01.11)

#   - Token       : new Enum rule - pick one of a fixed list of values instead of typing
#                   (Values... edits the list). Profile Dnable_Set_v001 uses it for character /
#                   side / part / type. Team naming rule doc: docs/A00330_NamingRule_Set.md (v01.12)

#   - Token       : every token's input box (text / Enum value / Start / Pad 0) has the same height
#                   and sits on the same row - each column has a caption row above it (v01.13)

#   - Token       : outside developer mode (the shared release) the fixed rules cannot be changed -
#                   no Values... button, an Enum token's rule is locked and it cannot be deleted (v01.14)

#   - Token       : Preview table next to the Objects list (like Quick Rename > Insert) - every node
#                   that Rename will touch, as a tree, with Current / New name / Status. Rename now
#                   skips locked / referenced nodes instead of stopping, and refreshes the list (v01.15)

#   - Token       : the Preview table's three columns have their own colors (blue / purple / gray),
#                   header included, so Current, New name and Status are easy to tell apart (v01.16)

#   - Release view: no Add Token / Delete Token, and only Rename > Token can be used (the other
#                   tabs are locked). In developer mode a Dev Mode toggle switches between the
#                   developer view and the release view (v01.17)

#   - Token       : Hierarchy check box next to Rename - on: the listed objects and their transform
#                   descendants (as before), off: only the listed objects (v01.18)

#   - Release view: the other tabs are hidden instead of grayed out. Hierarchy is off by default (v01.19)

#   - Release view: no Save / New on the Profile row - edited tokens cannot become a profile (v01.20)

#   - Release view: no Rename / Delete on the Profile row either - only the profile combo (v01.21)

#   - Release view: no Token 1..N header buttons above the token columns (v01.22)

#   - Token       : new profile "Custom" - "free_tokens": true lets anyone (also in the shared tool)
#                   add / delete tokens; save / rename / delete of profiles stay locked (v01.23)

#   - Quick Rename: Insert - Position slider next to the number field (like A00110 Stagger
#                   Offset per Item); its range follows the longest listed name (v01.24)

#   - Quick Rename: Insert - the Position slider uses this tool's brown_dark theme colors (v01.25)

VERSION = "01.25"
LAST_UPDATE = "2026-10-02"
