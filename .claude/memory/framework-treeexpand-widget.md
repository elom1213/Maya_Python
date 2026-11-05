---
name: framework-treeexpand-widget
description: 모든 Qt 트리에 JUN_mod_treeExpand_qt_v01(tree) 한 줄 - 화살표 펼치기 = 한 단계, Shift + 펼치기/접기 = 아래 전부 (사용자 지정 2026-11-05, 새 툴도)
metadata:
  type: feedback
---

트리 UI 규칙(사용자 지정 2026-11-05): 화살표로 펼치면 **한 단계만**, **Shift + 펼치기 = 아래 전부**, **Shift + 접기 = 아래 전부 접기**.
Qt 기본은 자식 펼침 상태를 기억해서 접었다 펼치면 아래가 다 열린다 — 사용자가 이걸 싫어했다(A00210 Sync 트리).

- 공용 `Framework/qt/MOD_treeExpand_qt_v01.py` — `JUN_mod_treeExpand_qt_v01(tree)` 를 트리 만든 직후 한 줄(상속 클래스는 super().__init__ 뒤 `(self)`).
- 사용자 입력 중의 펼침에만 반응(이벤트 필터 플래그 + singleShot(0) 해제), 코드 expandAll/setExpanded 는 그대로. Shift 는 이벤트의 modifiers 로.
- **`MOD_fileTree_qt_v01` 에는 붙이지 말 것** — 같은 규칙을 자체로 갖고 있고 `...`(Omit) 줄을 펼쳐 둬야 해서 충돌.
- 오프스크린 QTest.mouseDClick 단독은 펼치지 않는다 → 먼저 mouseClick 후 DClick. 게으른 트리 Shift 펼치기는 너비 우선 + max_nodes 2000.
- 2026-11-05 툴 16개(트리 26개)에 적용, 버전 +1. 시험 `Framework/tests/test_tree_expand.py` PySide6 · PySide2 19/19.

**Why:** "이렇게 안 되어 있는 트리는 이렇게, 앞으로 만들 툴도 이 UI 를 따르도록 공용 코드로" (사용자).
**How to apply:** 새 QTreeWidget/QTreeView 를 만들 때마다 이 한 줄. 문서 `JUN_All/docs/Framework_MOD_treeExpand_qt.md`. 관련 [[framework-viewzoom-widget]] · [[framework-tabfit-widget]].
