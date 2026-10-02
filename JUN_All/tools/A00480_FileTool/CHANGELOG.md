# Changelog — A00480_FileTool

## v01.09 (2026-10-02)
- **Export > Naming: new token rule `Enum`** - pick one of a fixed list of values instead of typing
  (`Values...` edits the token name and the list). It is the same rule as A00330 Token's Enum.
  - The shared token rules are now one set, `COMMON_RULES` (Custom / Enum / Numbering) in
    `Framework/core/token_naming.py`; this tool adds Set's Name on top. New token tools get Enum by default.
  - Enum values are checked like the rest of a file name (no `\ / : * ? " < > |`).

## v01.08 (2026-10-01)
- **Export > Naming: editing a token no longer saves it to the profile.** A new **Save** button on the
  Profile row saves the tokens shown now as that profile's default; nothing else does.
  - Before, every edit was written to the profile right away, so after closing and reopening the tool
    the last edit came back as the profile's default, with no notice.
  - Save is enabled only while there are unsaved edits (edit a token back and it turns off again).
  - Unsaved edits are dropped when you switch profile (`[WARN]` in the log) or close the tool.
  - `New` still copies the tokens shown now into the new profile; the profile you came from is not touched.
  - The change is in the shared widget `Framework/qt/MOD_tokenName_qt_v01.py`, so A00330 Token gets it too.

## v01.07 (2026-09-29)
- **Fixed a second, broken log box under the window** (a ghost of the log on Windows 10 / Maya 2023,
  a white strip on Windows 11 / Maya 2024).
  - Cause: the window opened at its full content height (about 1070px + title bar), taller than a
    1080 screen's work area. Windows cut the window at the screen edge and Qt never painted the part
    below, so the log was drawn a second time (or left white) there.
  - The tabs now sit in a scroll area. `fit_to_content()` still opens the window at the old size when it fits,
    otherwise at the monitor's work-area height (taskbar excluded) and moves it up if its bottom is off screen.
    The lists shrink first; a vertical scrollbar appears only below the tabs' minimum height
    (the window is widened by the bar then, so nothing is cut sideways).
  - The log and the footer always stay on screen.

## v01.06 (2026-09-28)
- **Naming works like A00330_NamingTool Rename > Token.** The six fixed boxes are replaced by the
  shared token widget (`Framework/qt/MOD_tokenName_qt_v01`):
  - each token picks a rule - `Custom` (the text), `Numbering` (the set's place in the list, Start +
    Pad 0, one per name) or `Set's Name` (the set's name, no namespace);
  - `Add Token` inserts to the right of the picked token, `Delete Token` removes it;
  - **Profiles** - `New` / `Rename` / `Delete`, saved as JSON in the tool's `data/` folder (not in git).
    Editing a token saves it to the current profile.
- The default profile `Default` keeps the old six texts: `SK_MANU_CH_Name_Basic_Version`.
- `Set Name` checks the tokens first (no file-name characters like `: * ?`, at most one Numbering)
  and sits at the right of the preview line.
- The window is taller (offscreen slate_dark 960 x 853 -> 868 x 970): a Numbering token needs four rows.

## v01.05 (2026-09-18)
- **The hidden meshes are selected in the scene.** After `Check` - and after an `Export` that
  a rule stopped - the meshes Check Hide Mesh found are selected (their transforms, hidden
  or not), and the log says what was selected. If every rule passes, the selection is left
  alone.
- Rules can hand back the nodes to select (`RuleResult.nodes`), so future rules get the
  same behaviour without UI changes.

## v01.04 (2026-09-18)
- **Check Hide Mesh looks at the meshes only.** A mesh fails when the mesh itself is hidden -
  its transform or shape `visibility` / `lodVisibility` is off, or a display layer / drawing
  override on the mesh hides it. Hidden groups, joints, locators and other non-mesh objects
  are fine, so a mesh that is switched on but sits under a hidden group no longer fails
  (v01.03 looked at every parent).

## v01.03 (2026-09-18)
- **Export rules** - checks that run before anything is exported. Pick them in the new
  `Rules (n/m)` drop-down next to Type Filter; `Check` runs them without exporting.
  - Every checked rule runs on **every listed set first**. If any rule fails, **no file is
    exported at all** - not even the sets that passed. All problems are logged in one go.
  - First rule: **Check Hide Mesh** (off by default). Looks at every mesh in the listed
    sets (members and everything under them, nested sets and component members too) and
    fails if any of them is hidden in the scene: its own, its shape's or any parent's
    `visibility` / `lodVisibility` is off, or a display layer / drawing override hides it.
    The log lists each set and hidden mesh with the reason. Intermediate (orig) shapes are
    ignored.
  - New rules are one entry in `app/core/export_rules.py` (`EXPORT_RULES`); the drop-down
    and Export / Check pick them up without UI changes.

## v01.02 (2026-09-17)
- Fix: the Pin button label was clipped. The button keeps its 72 x 22 size; its
  vertical padding is now 0 (the theme's 8px padding left only 4px for the text).

## v01.01 (2026-09-17)
- The window now opens at the same size as `A00040_file_exporter_V02`
  (960 x 853 with slate_dark). v01.00 measured its size before the theme reached
  the child widgets and opened at about 1290 x 890.
  - The size is fitted to the layout minimum on the event loop right after show().
  - Export tab page margins removed, window side margins reduced by the tab
    frame, Pin button height 22 so the header row matches the menu bar.

## v01.00 (2026-09-17)
- New tool: file import / export / path helpers in one window, three tabs.
  - **Export** — the whole `A00040_file_exporter_V02` (v02.09) window: Export Path
    (Browse / Paste), Set Up, Naming tokens, Move to scene root, Joints only under
    joints, Type Filter. Same results as the original (same files, same FBX
    contents, same log lines).
  - **Import** — `Import FBX normal` from `A00030_quickTool_V02`.
  - **Path** — `Copy Scene Folder` / `Open Scene Folder` from `A00030_quickTool_V02`.
- NEW **Scene** button next to the export path: fills it with the current scene's
  folder (an unsaved scene leaves the path unchanged and logs a warning).
- Export now loads the FBX plugin up front; without it the export logs
  `[FAIL] Cannot export FBX without the plugin.` instead of raising.
- One shared log for all tabs, Pin (always on top), common menu bar.
- Internal: the pasted-path cleanup moved from the UI into
  `core.normalize_pasted_path`; the exporter's private `undo_chunk` copy was
  replaced by `Framework.core.maya_undo.undo_chunk`.
- The two source tools are untouched and can run side by side with this one.
