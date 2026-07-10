---
name: wip-a00340-split-layout
description: A00340_SelectionTool v01.04 — window split into control pane (collapsible Profile/Create/Color/Log) over the button pane via a vertical QSplitter
metadata: 
  node_type: memory
  type: project
  originSessionId: d954ecb7-1273-466e-ac1f-8dfffdb0392a
---

A00340_SelectionTool v01.04 DONE (Maya-verified + pushed 2026-07-06,
Dnable/dev commit e08e7bb): window layout split so the control panel and the created
button collection are separated.

**Why:** user wanted {Profile, Create, Color, Log} (controls) visually separated from
the created-button collection. Chosen approach (from a proposal menu): vertical
splitter + collapsible controls. Refined afterward: collapse ALL controls with ONE
toggle (not each section individually).

**How to apply:**
- `selection_tab._build_ui` builds a `QSplitter(Qt.Vertical)` (stored as `self._splitter`,
  `setSizes([230,430])`): top = `_build_controls_pane()`, bottom = `_build_buttons_pane()`
  (category/button QScrollArea, `self._cat_layout` as before).
- `CollapsibleBox(title, content_layout, expanded=True)` widget (top of file): a
  QToolButton header (arrow ▾/▸ via setArrowType, checkable=expanded) toggling a content
  QWidget's visibility; exposes `self.toggled = self._header.toggled`.
- **Single collapse:** `_build_controls_pane` puts the four **titled QGroupBox** sections
  (Profile/Create/Color/Log — the group builders return plain QGroupBox again) into one
  `CollapsibleBox("Controls")`. `self._controls_box.toggled` → `_on_controls_toggled`,
  which resizes the splitter: on collapse remember top size + shrink top pane to header
  height (button pane grows); on expand restore. So one header folds all 4 at once and
  reclaims the space.
- Log moved into the control box: `main_window` creates `self.log_view` and passes it as
  `SelectionTab(log_callback=..., log_widget=self.log_view)`; the tab wraps it in a
  `_build_log_group()` QGroupBox("Log"). Removed the old bottom Log group (and unused
  QGroupBox import in main_window). log_callback unchanged.
- Verified offscreen (PySide6): 1 CollapsibleBox("Controls") + 4 titled groups, splitter
  2 panes, collapse shrinks top 230→70 and grows buttons 378→538 with all groups hidden,
  expand restores 230; color-select regression passes. Rendered PNGs confirm visuals.
- Builds on [[wip-a00340-button-colors]] / [[wip-a00340-selectiontool]]. Follows
  [[ui-text-english-only]], [[push-includes-tool-guide-docs]].
