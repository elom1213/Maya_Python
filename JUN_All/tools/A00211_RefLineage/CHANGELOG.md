# Changelog — A00211_RefLineage

All notable changes to this tool are documented here.

## [01.03] - 2026-10-30
### Changed
- **Layout flipped: deeper references sit higher, the scene (depth 0) is at the bottom.** A00210 draws a
  reference edge from the bottom of the referenced node to the top of the referencing node, so the
  referenced (deeper) files must be above for the arrows to flow down into the scene. Before, the scene
  was on top and the arrows ran upward. Same scanner is used by **A00480_FileTool > Reference > Lineage**
  (which shows the graph in-tool); existing exported graphs keep their saved positions.
- **Depth = longest path, not shortest.** A file referenced both by the scene and inside another
  reference now sits one row above that reference, so every arrow points downward (before, both shared
  a row and the arrow ran sideways).

## [01.00] - 2026-06-22
### Added
- **Initial release.** Scans the current Maya scene's **reference relationships**
  (including nested references) and exports them as an **A00210_FileManager Lineage
  graph** — the same `<store_dir>/lineage/<name>.json` format, so the result opens
  directly in A00210's **Lineage** tab.
  - In-Maya **PySide** window: **Scan Scene References** shows the scene + its
    references as a tree; **Export to Lineage JSON** writes the graph.
  - Each unique file becomes a node (the scene itself is the root node); the
    relationship is written as A00210 **reference edges** (referenced file →
    referencing file), so it lines up with the dashed reference arrows there.
  - Reuses A00210's `lineage` / `store` / `prefs` modules so the JSON format and
    the `store_dir` / `project_root` settings stay a single source of truth. Node
    `key`s are project-root-relative (empty when outside the root / no root set).
  - A headless one-shot is available too:
    `ref_scanner.export_scene_references(name="")`.
