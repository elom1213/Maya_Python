---
name: wip-a00370-toollauncher
description: A00370_ToolLauncher (new) — shortcut launcher UI that pops up JUN tools by folder path; clone of A00340 with launch instead of select
metadata: 
  node_type: memory
  type: project
  originSessionId: 88f40166-6415-4ea3-8f3b-99edf30cfede
---

A00370_ToolLauncher v01.02 — DONE (Maya-confirmed by user + pushed, commit
65cc69e on Dnable_repo/dev). User set UI theme to yellow_light. Ships Default +
user's UE profile.

New in-Maya PySide tool. A shortcut/launcher UI: user creates buttons that each
hold a **tool folder path**; clicking a button launches that tool (pops it up).
Built to unify tools like A00080_KWI_creator_V03 + A00260_ConstraintConverter
(Maya-setup → Unreal-code generators) into one window instead of one shelf icon
each. Fully extensible: any JUN tool folder exposing `run()` works by pasting its
path.

**Ported from [[wip-a00340-selectiontool]]** (A00340_SelectionTool): same
Profile / Category / per-button color / Color Select / collapsible-Controls
splitter layout. Only difference: button click LAUNCHES a tool instead of
selecting objects. Button data = `{name, path, color}` (path replaces A00340's
`objects` list).

Launch mechanism (`app/core/tool_launcher.py`): `resolve_module(path)` →
`(JUN_All_root, "<parentdir>.<toolfolder>")` e.g. `tools.A00080_KWI_creator_V03`;
`validate()` checks folder + `__init__.py`; `launch()` adds root to sys.path,
`importlib.import_module`, calls `run(reload_module)`. Exactly generalizes what
each tool's shelf command does. "Reload on launch" checkbox (default ON) →
run(True) vs run(False).

Verified headlessly (no Maya): all files compile; path resolve/validate correct
against real folders; both target tools import + expose callable run; seeded
Default profile loads. Theme coral_dark. Ships Default profile w/ "Maya to
Unreal" category wired to the two example tools. Icon = rocket + coral play btn.
Doc: JUN_All/docs/A00370_ToolLauncher.md. Drop file __dragDrop_A00370.py.

v01.01–02: each button shows the target tool's own icon —
`tool_launcher.find_icon()` returns `icon/<foldername>.png` (fallback: any png/svg
in icon/). v01.02 moved it OUT of the button into a square QLabel tile to the
LEFT, sized to the button height (BUTTON_HEIGHT=34, btn setFixedHeight; row =
QHBoxLayout[icon_label, btn]) so it reads bigger; icon-less tools return the bare
button. Resolved at render time (updates on path change).

Next tool number after A00360_SortTool. Follows [[ui-text-english-only]],
[[prefer-pyside-for-new-tools]], [[docs-go-in-jun-all-docs]].
