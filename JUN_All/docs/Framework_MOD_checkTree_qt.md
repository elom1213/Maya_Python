---
title: Framework 공용 — MOD_checkTree_qt (트리 다중 선택 + 다중 체크 동작)
aliases: [JUN_mod_checkTree_qt, 트리 체크박스 다중 체크, checkTree]
tags: [framework, qt, behavior, tree, checkbox, maya-python]
updated: 2026-10-12
---

# `JUN_mod_checkTree_qt_v01` — QTreeWidget 다중 선택 + 다중 체크 동작

`JUN_All/Framework/qt/MOD_checkTree_qt_v01.py` · 별칭 `from Framework.qt import JUN_mod_checkTree_qt`

[`JUN_mod_checkList_qt_v01`](Framework_MOD_checkList_qt.md)(QListWidget 판) 과 **같은 규칙의 QTreeWidget 판**이다.
위젯이 아니라 **붙이는 동작(behavior)** 이라 트리 · 열 · 아이콘 · 툴팁은 그대로 둔다.

```python
self.chk_tree = JUN_mod_checkTree_qt.JUN_mod_checkTree_qt_v01(self.tree)      # column=0 기본
self.chk_tree.checksChanged.connect(lambda items: ...)                         # 바뀐 QTreeWidgetItem 들
```

| 조작 | 결과 |
|------|------|
| Shift / Ctrl 클릭 | 여러 행 선택 (`ExtendedSelection` 으로 바꾼다) |
| **고른 행**의 체크박스 클릭 | 보이는 고른 행 **전부**가 같은 상태. 선택은 그대로 |
| 고르지 않은 행의 체크박스 클릭 | 그 행 하나만 |
| `Space` | 보이는 고른 행 전부를 첫 행 기준으로 뒤집는다 |
| 체크박스 **없는** 행(폴더 · `...` · 정보 행) | 누르기도 전파도 건너뛴다 |

## 리스트 판과 다른 점 — 함정 하나

**`QTreeWidgetItem` 은 기본 플래그에 `ItemIsUserCheckable` 이 이미 들어 있다**(리스트 항목과 다르다).
플래그만 보고 "체크 가능" 으로 판정하면 폴더 · 정보 행까지 전파돼 거기에 체크박스가 **생겨 버린다**
(오프스크린 QTest 로 실측). 그래서 체크박스가 있는 행은 **`item.data(col, Qt.CheckStateRole) is not None`**
— `setCheckState` 를 한 적이 있는 행 — 으로 가른다. 체크박스를 두지 않을 행은 `setCheckState` 를 부르지 않으면 된다
(플래그를 벗기면 더 분명하다).

"보이는 것이 작업 대상" 도 같다 — 숨긴 행(`isHidden`)과 **접힌 부모 아래** 행은 전파하지 않는다.
신호는 `checksChanged(바뀐 전부)` 한 번 → `itemChanged(누른 행, col)` 한 번.

## 쓰는 곳

- [`JUN_mod_fileTree_qt_v01`](Framework_MOD_fileTree_qt.md) (`checkable_files=True`) — 파일 행
- `A00210_FileManager` Maya > Reference 트리 — 최상위 레퍼런스 행 (중첩 행은 체크 없음)
