# Changelog

## v01.02 (2026-06-11)
- Replaced the hand-built list columns with the reusable PySide widget `Framework/qt/MOD_tsl_qt_v01.py` (`JUN_mod_tsl_qt_v01`).
- Each list now has Select / Add / Del / Up / Down / Sort buttons and updates its own item count.

## v01.01 (2026-06-11)
- Added a "Help > About" menu that opens a popup describing the tool and its usage.

## v01.00 (2026-06-11)
- Initial release.
- Two `QListWidget` panels: left = Driven, right = Driver.
- For each Driver, finds the closest unused Driven (1:1 matching) and connects them with constraints.
- Constraint types selectable via checkboxes (Parent / Point / Orient / Scale, multi-select).
- "Maintain Offset" option.
- Read-only log panel (English messages).
