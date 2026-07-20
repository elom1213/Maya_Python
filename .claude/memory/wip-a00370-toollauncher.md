---
name: wip-a00370-toollauncher
description: A00370_ToolLauncher — shortcut launcher UI that pops up JUN tools by folder path; v01.04 stores button paths RELATIVE to JUN_All root (no cross-PC git churn)
metadata: 
  node_type: memory
  type: project
  originSessionId: 88f40166-6415-4ea3-8f3b-99edf30cfede
---

A00370_ToolLauncher v01.02 — DONE (Maya-confirmed by user + pushed, commit
65cc69e on Dnable_repo/dev). User set UI theme to yellow_light. Ships Default +
user's UE profile.

v01.03 — IMPLEMENTED (headless-verified, Maya test + push pending): **PC
portability**. Buttons store absolute tool paths, so profiles broke on a PC where
JUN_All lives elsewhere (PC1 `G:\...\JUN_All`, PC2 `C:\...\Maya_Python\JUN_All`).
Fix: new `Environment` group at top of controls (launcher_tab `_build_env_group`)
with a **JUN_All Root** field (auto-filled via `tool_launcher.jun_all_root()` —
the launcher lives inside JUN_All so it always knows the current PC's root),
`Browse...`, `Detect`, and **Refresh Paths** button. Refresh calls
`prefs.rebase_all_profiles(root)` which rewrites EVERY button in EVERY profile:
`tool_launcher.rebase_to_root(path,new_root)` anchors on the last `tools` segment
and re-joins `<new_root>/tools/<tail>` (no `tools` anchor → None = skipped, left
untouched). Also `launch()` self-heals: broken stored path → try
rebase_to_root(path, jun_all_root()) and launch if it exists. Profiles shared via
repo → pull + one Refresh Paths restores on any PC. All headless-tested (rebase
correctness, color preserved, skip external, same-root no-op writes 0 files).

v01.04 — IMPLEMENTED (headless-verified, Maya test + push pending): **fixes cross-PC git churn**. v01.03's Refresh Paths rewrote every button's ABSOLUTE path to the current PC's root, so profile JSONs (git-tracked) changed on every PC → merge conflicts. Fix: **buttons now store a path RELATIVE to JUN_All root (`tools/A000XX_name`)** — identical on every PC, so tracked `data/profiles/*.json` never churn. Absolute path is resolved at launch via `tool_launcher.resolve(stored, prefs.effective_root())`. New path fns replace v01.03's rebase_* : `_tools_tail` (tail after last `tools` seg, works on relative OR any PC's absolute), `to_portable(path)` (→ `tools/...` slash form, or keep external absolute), `resolve(stored, root)` (→ this PC abs; foreign-absolute self-heals via its tools anchor). `prefs`: `effective_root()` = override-or-`jun_all_root()`; `get/set/clear_root_override()` in **gitignored** `data/local_env.json`; `make_all_portable()` (migrates any absolute→relative, idempotent → 0 writes on repeat) replaces `rebase_all_profiles`. UI stores via `to_portable`, uses via `resolve` (`_abs_path` helper); Environment box = Detect(clear override→auto) / Browse / **Apply Root**(save override, or clear if ==auto) / **Make Paths Portable**. `.gitignore` adds A00370 `data/local_env.json` + `data/active.json` (active.json `git rm --cached`). Committed 4 profiles migrated to relative. Verified headless: 10 buttons resolve+validate OK, make_all_portable 0-changed, PC2 root resolves, external kept. This is the user's "separate root file + gitignore" idea completed with relative profile paths (root file alone wasn't enough while profiles stayed absolute). See [[list-attrs-multi-detection]] style: same push flow [[push-target-dnable-dev]], [[push-includes-tool-guide-docs]].

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
