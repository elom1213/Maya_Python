# Changelog

## V01.00 (2026-06-24)

### Create
- A00080_KWI_creator_V03 : Maya in-DCC (PySide) version of KWI Creator V02.
- Same generation logic as V02 (base / setting / LD / combined nodes).
- Drag & drop install via `__dragDrop_A00080.py` → shelf button → `tools.A00080_KWI_creator_V03.run(True)`.
- Window is parented to the Maya main window (`Framework.qt.maya_window`).

### Changed (vs V02)
- Target bones are now entered through a TSL (`QListWidget`) in the UI instead of
  reading `A0101_tgtBones.py`.
  - Add by typing a bone name (Enter / Add button).
  - "Add Selected" : add currently selected nodes from the Maya scene.
  - "Remove" / "Clear" / "Load Example" (loads `A0101_tgtBones.py` as an example list).
- `KWI_creator.set_tgt_bones(list)` injects the UI bone list into the core.
