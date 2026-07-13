# Changelog

## V01.03 (2026-07-13)

### Fixed
- **Constraints tab — zero-padding in bracket patterns**: a bracket bound written with a
  leading zero now zero-pads the expanded values to that width. `[01-10]` &rarr;
  `01,02,…,10` (previously `1,2,…,10`), so `dyn_necklace_n_[01-10]_0[1-4]` expands to
  `dyn_necklace_n_01_01 … dyn_necklace_n_10_04`. Bounds without a leading zero keep the
  old behavior (`[1-10]` &rarr; `1..10`), so existing patterns are unaffected.

## V01.02 (2026-06-29)

### Added
- New **Constraints** tab: generates the **Bone Constraints** content for a KawaiiPhysics
  **Data Asset** from bracket patterns. Two patterns (Chain A / Chain B) are paired
  index-by-index (1:1), e.g. `dyn_asset_side_0[1-7]_0[1-5]` ↔ `dyn_asset_side_0[2-8]_0[1-5]`.
  - `[a-b]` expands to integers a..b (leftmost bracket is the outer loop); a leading `0`
    is literal, so values are not zero-padded (single-digit indices).
  - **+ Add pair** adds more pattern rows; all rows are merged into one output wrapped in
    a single outer `( )`.
  - **Generate & Copy** writes `0020_out/A020_LDA_constraint_out.py`, shows a preview and
    copies the text to the clipboard for pasting into the Unreal Data Asset.
- New core `ConstraintCreator` (`app/core/constraint_creator.py`) and entry template
  `app/core/0010_src/A0202_Src_LDA_constraint_entry.py`.

### Changed
- Main window is now **tabbed** (`KWI Nodes` / `Constraints`) with a shared log at the bottom.

## V01.01 (2026-06-25)

### Added
- "Create combined file" now copies the combined code to the clipboard so it can be
  pasted straight into the Unreal AnimGraph (Ctrl+V). Only the combined output is copied.
- Target bones label now shows a live count (e.g. `Target bones (Root bones) : 3`),
  kept in sync via the list model's row signals.

### Changed
- Help moved from a top-right button to a menu bar (`Help > How to use`).
- `KWI_creator.create_combined_file()` now returns `(out_path, combined_text)`.

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
