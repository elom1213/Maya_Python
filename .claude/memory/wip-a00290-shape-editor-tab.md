---
name: wip-a00290-shape-editor-tab
description: "A00290_BSTool Shape Editor tab — replaces Maya's Shape Editor Edit button via sculptTargetIndex; v01.07 adds target multi-edit + keyed-target editing (IMPLEMENTED, Maya test pending)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2af83ce7-788e-4c2c-83e0-9ebc68b52132
---

A00290_BSTool v01.02 — new "Shape Editor" tab (tab 1). DONE (Maya-verified + pushed, 2026-07-10).

Replaces Maya's built-in Shape Editor: lists every blendShape target from `aliasAttr` (so targets
Maya's tree hides are still editable) with a per-target `Edit` toggle + weight spinbox.

**Why:** Maya's Shape Editor sometimes doesn't expose a target, so there's no Edit button and the
user can't sculpt it.

**How to apply:** Edit ON/OFF = `cmds.sculptTarget(bs, e=True, target=<weightIdx|-1>)`.
WRITING `<bs>.inputTarget[g].sculptTargetIndex` with `setAttr` does NOT work — it only changes the
value; the deformer never intercepts vertex edits, so sculpting lands in the base shape's tweak
(`.pnts`) and the ORIGINAL mesh is modified. Read the attr, write via the command.
(Verified empirically with `Maya2024/bin/mayapy.exe` + maya.standalone — a fast way to test
maya.cmds behavior headlessly from this repo.)
Core logic in `app/core/shape_editor_manager.py` (`ShapeEditorManager`). On enter it forces
weight=1.0 (backs up previous), envelope=1.0, selects base mesh, calls mel `updateBlendShapeEditHUD`;
on exit restores weight. One target per node. Window close exits all edit modes.

**v01.06** (Maya-verified + pushed): gave `WeightSlider` its own `SLIDER_STYLE` — no theme qss
styles QSlider so the groove was invisible on the dark bg (only the handle showed). Bipolar slider,
so the groove is a uniform bar (no directional sub-page fill) + center tick marks 0.

**v01.07** (IMPLEMENTED, Maya test pending): two Shape Editor updates.
- **Target multi-edit** (selection UI, v01.08–09 per user requests): rows are `TargetRow(QFrame)` and you
  **click a row to select it** (accent background highlight). **Shift+click = range select** (anchor row →
  clicked row, all visible rows in between; standard list behavior, anchor = last plain/Ctrl click, works
  both directions). **Ctrl+click = individual toggle** (non-contiguous). Plain click clears others + sets
  anchor. Then dragging/typing any *selected* row's slider/spinbox applies the same value to ALL selected
  targets live; edited row not selected → single-edit. Slider drag does NOT change selection (so "select
  many → drag one" works). QLabel ignores the press so clicking the name cell selects; slider/spin/Edit
  consume their own clicks. Header: Select All / Clear (filtered-visible, resets anchor). row_info dicts are
  unhashable → range membership uses `id(r)`, not sets/`in`. `on_se_weight_changed`→`_co_edit_rows` (selected
  rows); `_se_applying` + blockSignals prevent the setValue→handler recursion. (v01.07 used per-row
  QCheckBox; v01.08 switched to click-select; v01.09 Shift range + Ctrl toggle.)
- **Undo per gesture** (v01.10): a slider drag emits a setAttr per tick per selected target, each its own
  undo entry, so Ctrl+Z only reverted the last tick of ONE target (~0.01). Fix: wrap the gesture in ONE
  undo chunk — slider `sliderPressed`→`sliderReleased` is one chunk (lazy `undoInfo(openChunk)` on the
  first change, close on release; `_se_dragging`/`_se_undo_open` state), spinbox/discrete change wraps that
  single call. One Ctrl+Z now restores ALL selected targets (values and setKeyframe keys). `_clear_se_rows`
  closes any dangling chunk on rebuild.
- **Keyed targets editable**: previously animCurve-driven (keyed) weights were disabled. Now
  `weight_state()` classifies free / keyed / driven / locked; only driven(non-animCurve)/locked stay
  disabled. Editing a keyed weight: Auto Keyframe ON → `cmds.setKeyframe` (value keyed at current
  frame); OFF → `cmds.setAttr` (preview that reverts when you scrub time). Verified with mayapy:
  setAttr on a keyed attr changes the value but reverts on re-eval, so setKeyframe is required to
  commit; `cmds.autoKeyframe(q=1,state=1)` reads the scene toggle. sculpt Edit-enter still only
  sets FREE weights to 1.0 (won't accidentally key/disturb keyed/driven targets).

**Testing note (important):** creating Qt widgets together with `maya.standalone` crashes mayapy
(exit 127) in this repo, so the full MainWindow can't be rendered headless. Test the propagation
logic by binding the real `MainWindow.on_se_weight_changed`/`_co_edit_rows`/`_show_weight` to a
plain object with FAKE widget stand-ins (isChecked/value/setValue/set_weight/weight/blockSignals) —
no Qt, coexists with maya.standalone. Render widget *styling* separately in pure PySide WITHOUT
maya.standalone (that works).

Related: [[ui-text-english-only]], [[push-includes-tool-guide-docs]], [[mayapy-headless-verify]],
[[push-only-when-asked]]
