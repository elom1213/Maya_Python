---
name: wip-a00340-selectiontool
description: "A00340_SelectionTool v01.00 — new in-Maya PySide tool, quick re-select saved object sets via buttons (profile/category/button pattern)"
metadata: 
  node_type: memory
  type: project
  originSessionId: b7ee37ed-bdf5-4d70-a327-9952147532c6
---

A00340_SelectionTool v01.00 DONE (Maya-verified + pushed 2026-07-02, Dnable/dev commit 2c7d04f). 사용자 data/ 는 .gitignore 처리(A00240 선례), README 목록 등록.

**v01.11 (2026-10-26) `Rules` 탭** — 최상위 탭 `Buttons`(기존 전부) / `Rules`. 규칙 = 이름 목록 하나, **json 파일 하나 =
규칙 하나**(`data/rules/<name>.json`, `name/description/objects`) 라 다른 PC 공유는 파일 복사. 사용자가 "어느 툴에 이식할지"
를 먼저 물었고 A00340 을 권장했다(버튼이 이미 같은 일, 저장 단위만 프로파일 json). A00310 Rules 탭은 **조건 함수**(다른 물건),
A00440 은 씬 안 objectSet 이라 "어느 씬에서든" 을 못 채움. 코어 `select_rules.py`(DCC 비의존, A00145 connect_rules 패턴),
UI `rules_tab.py`. 결정: 이름 ↔ 파일 이름 동행(Rename 이 파일도 바꿈, 금지 문자만 `_`), **짧은 이름 저장 + 동명은 전부 선택
하고 경고**(`maya_select.select_names` — `objExists` 는 동명에 True 인데 `cmds.select(짧은이름)` 은 실패하므로 `cmds.ls(long=True)`
로 펼친다). 여러 규칙 고르면 합집합. GUI 확인 아직.

New in-Maya PySide tool: click a button to re-select a saved set of Maya objects.
Buttons are freely add/remove/reorder-able and grouped into Categories; Profiles
keep separate button sets per character/asset (JSON per profile in the tool's
`data/` folder, like A00240).

**Why:** user wanted an A00240_PathTool-style customizable-button tool, but the
buttons select Maya objects instead of opening paths.

**How to apply:**
- Structure/edit flow ported from [[wip-a00170-attachcrv-tab]]'s sibling A00240_PathTool
  (profile → category → button, right-click Move Up/Down/Rename/Delete/Change Category).
- Maya integration (launch.py run(), __dragDrop_A00340.py shelf install, Maya-parented
  window via Framework.qt.maya_window, blue_dark theme) ported from A00310_SearchTool
  (see [[wip-a00310-searchtool-merge]]).
- Button stores `{"name", "objects":[...]}`; core split: prefs.py (pure JSON, DCC-free)
  + maya_select.py (capture_selection / select_objects, skips missing objects, `Add`
  toggle accumulates). Right-click also has Update/Add Objects (recapture selection).
- Docs: JUN_All/docs/A00340_SelectionTool.md + CHANGELOG.md. Icon made
  (icon/A00340_SelectionTool.png + .svg — blue dashed selection marquee + cursor,
  A00310-style tile; PNG rendered via PIL supersample since no SVG rasterizer avail).
- Follows [[prefer-pyside-for-new-tools]], [[ui-text-english-only]],
  [[standalone-app-package-collision]] (imports via tools.A00340_SelectionTool.app.*).
