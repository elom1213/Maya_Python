---
title: Framework 공용 위젯 — MOD_treeExpand_qt (트리 펼치기 = 한 단계, Shift = 아래 전부)
aliases: [JUN_mod_treeExpand_qt, Tree Expand, 트리 펼치기]
tags: [framework, qt, widget, maya-python]
updated: 2026-11-05
---

# `JUN_mod_treeExpand_qt_v01` — 트리 펼치기 · 접기 규칙

`JUN_All/Framework/qt/MOD_treeExpand_qt_v01.py`

**모든 툴의 트리가 같은 규칙으로 펼쳐지고 접히게** 하는 한 줄짜리 공용 동작. QTreeWidget · QTreeView 둘 다.

2026-11-05 사용자 요청: A00210 Sync > Status 트리에서 행을 접었다가 펼치면 그 아래가 전부 다시 열린다
(Qt 는 자식의 펼침 상태를 기억한다) → 화살표로는 한 단계만, Shift 를 누르면 아래 전부.
"이렇게 안 되어 있는 트리는 이렇게 되도록, 앞으로 만들 툴도 따르도록 공용 코드로."

---

## 1. 규칙

| 조작 | 동작 |
|------|------|
| 화살표 클릭 · 행 더블클릭 · `→` 키로 **펼치기** | **한 단계만** — 바로 아래 자식은 접힌 채로 보인다(예전에 열어 둔 아래 단계도) |
| **Shift** + 펼치기 | 그 아래 **전부** 펼친다 |
| **Shift** + 접기 | 그 아래 **전부** 접는다 — 다음에 그냥 펼치면 한 단계부터 |
| `*` 키 (Qt 기본 '아래 전부 펼치기') | Shift + 펼치기와 같다 |
| 코드의 `expandAll()` · `setExpanded()` · `expand()` | **손대지 않는다** — 툴이 처음 전부 펼쳐 보여 주는 동작은 그대로 |

사용자 입력(마우스 누름 · 뗌 · 더블클릭 · 키)을 Qt 가 처리하는 동안 생긴 펼침 · 접힘에만 반응한다.
Shift 는 그 입력 이벤트에 실린 modifier 로 본다(`QApplication.keyboardModifiers()` 도 함께).

## 2. 쓰는 법

```python
from Framework.qt.MOD_treeExpand_qt_v01 import JUN_mod_treeExpand_qt_v01

self.tree = QTreeWidget()
JUN_mod_treeExpand_qt_v01(self.tree)  # 펼치기 = 한 단계, Shift = 아래 전부 (공용)
```

- 부모가 트리라서 반환값을 들고 있을 필요가 없다. 같은 트리에 두 번 붙이면 처음 것을 돌려준다(`attach(view)` 도 같다).
- QTreeWidget 을 상속한 클래스는 `__init__` 의 `super().__init__()` 바로 뒤에 `JUN_mod_treeExpand_qt_v01(self)`.
- 별칭: `from Framework.qt import JUN_mod_treeExpand_qt`.
- 코드에서도 부를 수 있다: `collapse_children(index)` · `collapse_all_below(index)` · `expand_all_below(index)`.

**새 툴의 트리는 만들자마자 이 한 줄을 붙인다.**

## 3. 게으른 트리 · 한도

- 펼칠 때 자식을 채우는 트리(디스크 폴더 등)도 Shift 전부 펼치기가 **새로 생긴 자식까지** 따라간다 — `canFetchMore` / `fetchMore` 도 부른다.
- 얕은 단계부터(너비 우선) 펼치고 **`max_nodes`(기본 2000)** 개에서 멈춘다 — 디스크 전체를 훑지 않게. `JUN_mod_treeExpand_qt_v01(tree, max_nodes=500)`.
- 펼치는 동안 `setUpdatesEnabled(False)`.

## 4. 적용 현황 (2026-11-05)

A00010 V02(결과) · A00050 V02(UV Set) · A00110 V02(View > Layers) · A00130 V02(Plan · Length · Orient · Pair · Constrain) ·
A00145(All Targets 미리보기) · A00210(Sync · 파일 목록 · Path Structure · Maya > Reference) · A00211 · A00275(Layer · Lock) ·
A00290 / V02(Naming 미리보기) · A00330(Insert · Search/Replace · Token) · A00340(Rules) · A00380(Match · By Weight · UV Set) ·
A00420 · A00470(Name Check) · A00480(Reference). 각 툴 버전 +1 · CHANGELOG.

**`MOD_fileTree_qt_v01` 에는 붙이지 않는다** — 같은 규칙(Shift 재귀 · 접을 때 자손까지 접기)을 A00240 v01.x 때부터 자체로 갖고 있고,
루트 아래 `...`(Omit) 줄을 늘 펼쳐 둬야 해서 '한 단계만' 규칙과 겹치면 그 줄이 접힌다. A00240 · A00480 Maya 탭의 폴더 트리는 그쪽 규칙.

## 5. 시험

`Framework/tests/test_tree_expand.py` 19/19 — PySide6(파이썬) · PySide2(mayapy 2024) 둘 다.
화살표 클릭(`QTest` 로 실제 마우스 이벤트) · Shift 클릭 · 더블클릭 · `→` / `*` 키 · 코드 expandAll / setExpanded 무시 · 두 번 붙이기 ·
QTreeView + 모델 · 게으른 트리 + 한도 · 너비 우선.
툴 31개 창 생성은 `test_tab_fit_rollout.py`(mayapy) 로 확인. **마야 · 실제 창에서의 손 확인은 아직.**
