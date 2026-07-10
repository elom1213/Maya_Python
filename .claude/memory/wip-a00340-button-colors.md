---
name: wip-a00340-button-colors
description: A00340_SelectionTool v01.03 — per-button custom colors (palette+eyedropper) + Color Select mode to recolor many buttons across categories
metadata: 
  node_type: memory
  type: project
  originSessionId: d954ecb7-1273-466e-ac1f-8dfffdb0392a
---

A00340_SelectionTool v01.03 DONE (Maya-verified + pushed 2026-07-06,
Dnable/dev commit 2fefeba): selection buttons can have a custom color.

**Why:** user wanted each created button colorable like A00210_FileManager lineage
tab's "Set Color..." (palette popup + eyedropper/spoid), and to recolor multiple
buttons at once — then refined to picking arbitrary buttons ACROSS categories (not
per-category bulk).

**How to apply:**
- Data: each button dict gets optional `"color"` hex (`btn_data["color"]`) in the
  profile JSON; absent = theme default. `selection_tab._build_selection_button`
  applies `_button_stylesheet(hex)` — readable label color (`_contrast_text_hex`,
  luminance>140→black else white) + darker border / lighter hover / darker pressed,
  plus a `:checked` highlight-border rule (CHECK_HILITE_HEX).
- Palette + eyedropper = plain `QColorDialog.getColor()` (same as A00210); its built-in
  "Pick Screen Color" IS the spoid. Added QColorDialog, QColor to the qt import list.
- Per-button (kept): right-click → `Set Color...` / `Reset Color`
  (`_set_button_color` / `_reset_button_color`).
- **Color Select mode (v01.03, replaced v01.02 per-category bulk):** a `Color` bar
  (`_build_color_group`) with a `Color Select` toggle. When on, every button is
  rendered checkable (click = check via `_on_color_check`, not select); check any
  buttons across categories, then `Apply Color...` (`on_apply_color_to_checked`) paints
  all checked with one picked color, or `Clear Color` (`on_clear_color_from_checked`)
  resets them. Checked set = `self._checked` of (cat,name) tuples — survives re-render,
  cleared on mode-off and profile switch. No-color buttons use CHECK_ONLY_QSS for the
  checked border. The v01.02 category right-click Set/Reset Buttons Colors were removed.
- **Bug fixed during v01.03 dev (2026-07-06):** "check 2 buttons → Apply Color →
  'Check one or more buttons first' popup" — `self._checked` wasn't populated.
  Hardened: (a) `clicked`→`toggled` signal for check tracking (toggled reliably
  carries the new state); (b) `_build_selection_button` now appends each color-mode
  button widget to `self._color_buttons` (reset each render), and Apply/Clear call
  `_sync_checked_from_widgets()` first — rebuilding `self._checked` from the widgets'
  real `isChecked()` so a missed/odd signal can't leave the set empty. Widget state
  is the source of truth. Reproduced the empty-set case + verified via offscreen
  PySide6 smoke test (real `btn.click()`).
- Updated version.py (01.03), CHANGELOG, About, JUN_All/docs/A00340_SelectionTool.md.
- Builds on [[wip-a00340-selectiontool]]. Follows [[ui-text-english-only]],
  [[push-includes-tool-guide-docs]].
