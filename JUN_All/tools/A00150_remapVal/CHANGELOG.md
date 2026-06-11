# Changelog

## v01.00 (2026-06-11)
- Initial release. PySide UI for `sample_01.py`'s `build_slerp_ramp` (remapValue-based interpolation).
- Inputs: Main Controller (QLineEdit + Get), Prefix (QLineEdit), Joints list and Attributes list (reusable `JUN_mod_tsl_qt_v01`).
- "List Attributes" fills the attribute list from the first joint's keyable attributes; Attribute Search filter.
- Build wraps the whole node creation in a single undo chunk; input validation + read-only log; Help > About menu.
