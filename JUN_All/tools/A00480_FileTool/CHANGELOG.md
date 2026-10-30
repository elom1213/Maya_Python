# Changelog — A00480_FileTool

## v01.19 (2026-10-30)

- **[Feature] Reference > Lineage — 러버밴드 다중 선택 + 선택 노드의 전체 경로 표시.** 빈 곳을 드래그하면 사각형에 **일부라도 걸친**
  노드 · 화살표가 모두 선택된다(A00210 Lineage 탭과 같은 `RubberBandDrag` / `IntersectsItemShape`, Shift / Ctrl 클릭도 그대로).
  캔버스 아래 **`Selected`** 칸(읽기 전용, 글자를 긁어 복사 가능)에 고른 노드의 **전체 경로**가 보인다 — 노드 글자가 파일 이름만일 때
  전체 경로를 보는 자리. 여럿이면 `N nodes selected : a.ma, b.ma` 와 함께 툴팁에 경로 전부, 저장 전 씬은 `(untitled scene - not saved yet)`.
- 검증 `tests/test_reference_lineage.py` **44 항목**(S1~S6: 드래그 모드 · 빈 선택 · 하나 = 전체 경로 · 둘 = 수 + 이름 + 툴팁 ·
  러버밴드 영역으로 한 줄 전부 선택 · 해제). **마야 GUI 확인 아직.**

## v01.18 (2026-10-30)

- **[Feature] Reference > Lineage 에도 `Show` 콤보 — 노드 글자를 `File Name` / `Full Path` 로.** Default 탭과 **같은 optionVar**
  를 써서 한쪽에서 바꾸면 다른 쪽도 다음에 열 때 따라간다. **기본이 `File Name`** 이 됐다(Default 탭도 — 사용자 요청).
  Full Path 는 노드 폭에 맞게 가운데를 줄여 보이고, Reveal / Copy Path / Export 는 늘 전체 경로 · 파일 이름 규약을 쓴다
  (Export 로 쓰는 A00210 그래프의 노드 글자는 모드와 무관하게 파일 이름).
- **[Change] Lineage 배치 — 깊은 노드가 위, 씬(depth 0)이 맨 아래.** 예전엔 씬이 위라 "참조 대상 → 참조하는 파일" 화살표가
  거꾸로 올라갔다(사용자: "지금은 반대로 보여"). A00211_RefLineage v01.03 의 `_layout` 에서 고쳐 A00210 으로 Export 한 그래프도 같다.
- 검증 `tests/test_reference_lineage.py` **38 항목**(N1~N6 보기 모드 · 공유 · Refresh 유지 · Export 는 파일 이름, L7/L7b 배치 방향),
  `tests/test_reference.py` **47 항목**(기본 File Name · Full Path 전환 · 공유 optionVar 따라가기). **마야 GUI 확인 아직.**

## v01.17 (2026-10-30)

- **[Feature] Reference > `Lineage` 하위 탭 — 현재 씬의 레퍼런스 관계를 노드 그래프로.** 노드 1개 = 파일 1개(씬 자신이 루트,
  같은 파일을 여러 번 레퍼런스해도 노드 하나), 화살표 = **참조 대상 → 참조하는 파일**(회색 점선 + 채운 삼각 화살촉), 깊이별 자동 배치.
  데이터는 **A00211_RefLineage** 의 `ref_scanner`(씬 스캔 → A00210 `LineageGraph`)가 만들고, 그림은 **A00210_FileManager Lineage 탭의
  `NodeItem` / `EdgeItem` / `LineageView` 를 그대로** 쓴다 — A00210 에서 보는 노드와 같은 모양(레인 자동색, 파일명 + `current scene` /
  `unloaded` 보조 라벨, 휠 줌 · 중간 버튼 팬 · 드래그 이동 · 러버밴드 선택). 탭을 열 때마다 씬을 다시 읽는다(`Refresh` · `Fit View`).
- **노드 우클릭** `Reveal in File Explorer` / `Copy Path` — 이 페이지는 절대 경로를 알고 있어 A00210 과 달리 project root 없이도 된다
  (Default 탭과 같은 `reference_ops` 경로: 없는 파일은 폴더를 연다).
- **`Export to Lineage`** — 지금 그래프(끌어 놓은 위치 포함)를 A00211 과 똑같은 lineage JSON 으로 **A00210 Store Repo**
  (`<store_dir>/lineage/<name>.json`)에 쓴다. 이름 칸이 비면 씬 파일 이름. 같은 이름이 있으면 덮어쓸지 묻는다. Store Repo 미설정 ·
  저장 전 씬이면 경고. A00210 Lineage 탭에서 Refresh 로 열린다(Push 로 동기화).
- **★ 툴 간 import 예외.** 이 저장소는 릴리즈본(툴 하나 + Framework)을 위해 툴 간 import 를 피하지만, 이 탭은 사용자 지시
  (2026-10-30: "A00211 로 데이터, A00210 과 같은 노드")로 두 툴을 import 한다. 둘이 없으면 페이지는 안내문만 보이고 나머지 탭은 그대로.
  A00211 자체도 같은 식으로 A00210 을 쓴다.
- 검증 `tests/test_reference_lineage.py` mayapy 2024 **31 항목**(노드 4 · 엣지 방향 4 · A00210 NodeItem / 점선 회색 · 라벨 · 키 · 깊이 배치 ·
  레인색 · 드래그 → 모델 + 재배선 · Reveal / Copy · Fit · Export 쓰기 · A00210 으로 다시 로드 · 덮어쓰기 확인 · 이름 지정 · Store 미설정 ·
  저장 전 씬 · 하위 탭 2개 · 백엔드 없을 때 안내문). `test_reference.py` 46/46 그대로. **마야 GUI 확인 아직.**

## v01.16 (2026-10-30)

- **[Feature] Reference > Default — `Show` 콤보 : File 열을 `Full Path` / `File Name` 으로.** 지금까지는 레퍼런스마다
  전체 경로만 보였다(사용자: "파일 이름만 보이는 모드가 필요하다"). `File Name` 을 고르면 모든 행(중첩 · Missing 포함)이
  파일 이름만 보이고 헤더가 `File Name` 으로 바뀐다. **글자만 바뀐다** — Open in Explorer · 더블클릭 · Copy Path 는 그대로
  전체 경로를 쓰고, 툴팁에도 전체 경로가 남는다. 고른 모드는 마야 optionVar(`JUN_A00480_FileTool_reference_file_view`)에
  기억돼 다음에 열 때도 같다. 바꿀 때 씬을 다시 읽지 않는다(글자만 갱신).
- 검증 `tests/test_reference.py` **46 항목**(V1~V11 추가: 글자 변환 · 기본 Full Path · 이름 모드 전 행 · 헤더 · 저장된 경로와
  선택 경로 불변 · 이름 모드에서 Copy Path 는 전체 경로 · Refresh 뒤 유지 · optionVar 기억 + 새 페이지 · 되돌리기 · 모르는 값 무시).
  **마야 GUI 확인 아직.**

## v01.15 (2026-10-29)

- **[UI] 탭마다 창 높이가 자동으로 맞춰진다.** 탭(중첩 포함)을 바꾸면 창 높이가 지금 보이는 페이지에 맞게 늘거나 줄어
  스크롤 없이 다 보인다. 페이지가 모니터 작업 영역보다 길면 화면 높이에서 멈춘다. 폭은 그대로(처음 여는 크기는 예전 `fit_to_content` 그대로, 그 뒤 높이만 따라간다).
  공용 `JUN_mod_tabFit_qt_v01` — A00275 v01.38 과 같은 방식 (`docs/Framework_MOD_tabFit_qt.md`). **마야 GUI 확인 아직.**

## v01.13 (2026-10-27)
- **Import > FBX : new `Mocap FBX Import (Exact Rotation)` section.** The Maya FBX importer flips the
  rotation keys of joints whose rotate order is not XYZ when the values cross +-180 deg (e.g. Vicon
  mocap `Hips` / `RightArm`), so the pose is wrong - in every Quaternion Interpolation mode. This section
  imports the FBX with the Maya importer and then rebuilds the joint rotation (and translation) curves
  from the keys stored in the file.
  - `Browse` reads the file at once (no scene change) : `Info` line and one checkbox per skeleton.
  - Options : `Skeletons only` (delete markers, cameras and other top nodes), `Normalize joints`
    (jointOrient 0 / rotateOrder xyz - the layout of a Blender round trip; on by default),
    `Unwrap rotations` (360 deg jumps removed with the rotate order's own equivalent solutions; when
    Normalize is off), `Verify against file`.
  - `Import FBX (Exact)` logs which joints Maya had wrong and the largest error after the rebuild.
    It stops if the scene already has a node named like a checked skeleton root. Undo is not recorded.
    The timeline is the file's own range.
  - `Fix Scene From FBX` does the same for a scene that was already imported straight from the FBX
    (selected roots, or every top node named like a skeleton in the file).
  - Logic lives in `Framework.core.maya_fbx_exact` with the pure Python `fbx_binary` reader and
    `euler_math`.

## v01.12 (2026-10-26)
- **New `Reference` tab with a `Default` sub tab.** Every reference of the current scene is listed as a
  tree - a reference inside a reference (nested, any depth) sits under its parent. Columns `Reference`
  (namespace, plus `{n}` when the same file is referenced more than once), `File`, `Status`
  (`Loaded` / `Unloaded` in grey / `Missing` in red).
  - `Open in Explorer` (also double-click and the right-click menu) opens the selected files in File
    Explorer, one window per file with the file selected; a missing file opens its folder instead.
  - `Copy Path` puts the selected paths on the clipboard, one per line, in Windows form.
  - Several rows can be selected (Shift / Ctrl); the same file is opened or copied once.
  - The list is read again every time the tab is shown, and with `Refresh`. An unloaded reference hides
    its nested references until it is loaded (Maya does not create their nodes).

## v01.11 (2026-10-16)
- **Import > CSV : new `Value Scale` row** - every CSV value is multiplied by it before it is keyed
  (default 1, quick buttons `x1` / `x10`). The CSV holds 0 ~ 1, while AdvancedSkeleton facial controls
  expect 0 ~ 10 - use `x10` for them. A scale other than 1 is written to the log.

## v01.10 (2026-10-13)
- **Import tab is now two sub tabs : `CSV` and `FBX`.** FBX holds the old Import tab as it was
  (`Import FBX normal`).
- **Import > CSV - ARKit facial CSV import, ported from `A00200_CSV_tool`** (the original tool stays).
  A CSV exported by Live Link Face becomes keyframes : columns are matched to the node's attributes by
  name (case-insensitive), `Recorded` / `Output` FPS set the downsample step and the scene FPS, the
  timeline is extended to the imported range, and the WAV next to the CSV (`_raw` ignored) - or one
  extracted from a video next to it with ffmpeg - is imported as the scene sound.
  - **Different from the original :** every UI string and log line is English; and the keys can go to
    **any node whose attributes are named like the CSV columns**, not only a blendShape - e.g. a facial
    control carrying the 52 ARKit attributes. `Detect` lists every blendShape and every node with ARKit
    attributes (`(n ARKit)` = how many of the 52 names it has) and picks the best; `Selected` adds the node
    selected in the scene.
  - Keys, timeline and sound node are **one undo step** (the original only undid the keys together).

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
