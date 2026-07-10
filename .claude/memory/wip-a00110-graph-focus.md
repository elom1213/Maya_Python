---
name: wip-a00110-graph-focus
description: A00110 Graph Focus tab — frame Graph Editor to current±margin frames on selection instead of whole keyed range
metadata: 
  node_type: memory
  type: project
  originSessionId: ba4273fe-f76d-4e80-a559-f9d7a6aeeb4c
---

DONE (Maya-verified + pushed Dnable/dev, latest commit 835ce8f, v01.30): A00110_animTool **Graph Focus** tab (7th tab).

v01.30: Auto-Focus now fires ONLY on a real scene-object selection change. Maya's `SelectionChanged` also fires on Graph Editor key select/deselect and undo(z), so auto-frame triggered spuriously; v01.27's "skip if keys selected" guard missed the moment keys are *deselected* (0 keys selected). Fix (`graph_focus_manager.py` only): cache the last framed object selection (`_last_selection`); `_apply_silent` only frames when `cmds.ls(sl=True, long=True)` actually differs (skips empty selection too, keeps the key-selected guard). `apply_now` also syncs the cache to avoid re-trigger.

v01.28/01.29: Fit value vertical fit — dropped the fixed 10% pad so min/max hit the view edges, then re-exposed padding as a UI "Value margin (%)" spinbox (default 10, 0–100, threaded as frame_around_current value_pad_pct; flat curves keep a proportional/1.0 min pad).

v01.26/01.27 follow-up fixes (pushed): (1) Fit value vertical axis was computed only from key values inside the window, so it failed when no keys fell in the current±margin window — now samples anim curve `.output` across the window (incl. tangent overshoot) so it always fits; per-curve sample count scaled to a 4000-eval cap. (2) With Auto-Focus on, selecting a key and pressing `f` (Frame Selection) got clobbered back to the current frame by the SelectionChanged deferred callback — now the auto-framing callback skips when any keys are selected in the Graph Editor (`cmds.keyframe(q, selected, name)`); explicit Focus Now / toggle-ON are unaffected.

**What:** Selecting a controller normally shows its whole keyed range (e.g. 0–6000f) in the Graph Editor. This tab instead frames the Graph Editor to `[currentFrame - margin, currentFrame + margin]` (e.g. current 500f, margin 80 → 420f–580f).

**UI:** checkable "Auto-Focus on Selection" toggle button + "Frame margin (±)" QSpinBox (default 80, user-set) + "Fit value (vertical) axis too" checkbox (default on) + "Focus Now" one-shot button.

**How:** toggle ON installs a `SelectionChanged` scriptJob; callback uses `cmds.evalDeferred(..., lowestPriority=True)` so our `animView` framing runs AFTER Maya's own Auto-Frame. Framing = `cmds.animView(<panel>GraphEd, startTime, endTime, minValue, maxValue)` over `cmds.getPanel(scriptType="graphEditor")`. Value axis fit from `cmds.keyframe(sel, time=(s,e), valueChange=True)` min/max. closeEvent kills the scriptJob.

**Files:** new `app/core/graph_view_manager.py` (GraphViewManager, framing logic) + `app/core/graph_focus_manager.py` (GraphFocusManager, scriptJob lifecycle); wired into `app/core/__init__.py`, `app/ui/main_window.py` (`_build_graph_focus_tab`, handlers, teardown), version 01.25, docs `JUN_All/docs/A00110_animTool.md` (§5.7). See [[push-includes-tool-guide-docs]].
