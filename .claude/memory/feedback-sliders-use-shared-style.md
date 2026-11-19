---
name: feedback-sliders-use-shared-style
description: Every new QSlider in a PySide tool must be clearly visible in the theme - attach the shared JUN_mod_sliderStyle_qt_v01 (themes have no QSlider rule, so the groove vanishes on dark backgrounds)
metadata:
  type: feedback
---

When building slider UI, make the slider **clearly visible in the tool's theme** — add the shared one-liner
`self.slider_style = JUN_mod_sliderStyle_qt_v01(self)` (`Framework/qt/MOD_sliderStyle_qt_v01.py`) to the widget that holds the
sliders. Use `fill=False` for centre-zero (bipolar) sliders. Check the look by grabbing the widget to a PNG offscreen.

**Why:** the user asked on 2026-11-19 ("앞으로도 이렇게 슬라이더 ui 를 제작할 때 색이 잘 보이도록 해") after A00275 Flood's
Options sliders showed only the handle bar. No theme qss in `Framework/styles/` styles `QSlider`, so on dark themes the native
groove disappears into `#2b2b2b`. Seven older tools copied their own `SLIDER_STYLE` strings for the same reason.

**How to apply:**
- New tab/window with a `QSlider` → attach the widget (it paints on Show, after `launch.py` applied the theme).
- A slider that already has its own stylesheet is skipped by the widget — don't give new sliders ad-hoc styles.
- Don't mass-migrate old tools' custom styles unasked; mention it when touching them.

Related: [[framework-tabfit-widget]] · [[offscreen-size-needs-theme]] · [[wip-a00275-flood]]
