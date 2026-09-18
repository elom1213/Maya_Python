# Framework — `MOD_checkList_qt_v01` (다중 선택 + 다중 체크 동작)

체크박스가 달린 `QListWidget` 에 붙이는 **동작(behavior)**. 위젯이 아니라서 목록 · 필터 · 라벨은 그대로 둔다.

- 모듈: `JUN_All/Framework/qt/MOD_checkList_qt_v01.py`
- 별칭: `from Framework.qt import JUN_mod_checkList_qt`
- 클래스: `JUN_mod_checkList_qt_v01(list_widget)`
- 출처: `A00275_skinTool_V01` Select > By Weight 의 eventFilter 를 공용으로 뽑았다 (2026-09-18, A00145 v01.49 에서 처음 사용)

```python
self.lw_attrs = QListWidget()
# ... 항목에 Qt.ItemIsUserCheckable + setCheckState ...
self.chk_attrs = JUN_mod_checkList_qt.JUN_mod_checkList_qt_v01(self.lw_attrs)
```

## 동작

| 조작 | 결과 |
|------|------|
| Shift / Ctrl 클릭 | 여러 행 선택 (`ExtendedSelection` 으로 바꾼다) |
| **고른 행**의 체크박스 클릭 | 보이는 고른 행 **전부**가 같은 상태. 선택은 그대로 남는다 |
| 고르지 않은 행의 체크박스 클릭 | 그 행 하나만. 선택도 바뀌지 않는다 |
| `Space` | 보이는 고른 행 전부를 첫 행 기준으로 뒤집는다 |
| 글자 클릭 | 평소처럼 선택만 바뀐다 |

## 왜 공용으로 뽑았나

1. **Qt 기본 처리의 함정** — 체크박스 위 누르기가 **선택을 그 한 행으로 풀어 버린다**. 첫 클릭은 여러 행에
   전파돼도 그 뒤로는 한 행씩만 바뀐다(A00275 에서 오프스크린 QTest 로 실측). 그래서 체크박스 위
   누르기 / 놓기 / 더블클릭을 viewport eventFilter 에서 먹고, 놓을 때 한 번만 뒤집는다.
   툴마다 이걸 다시 짜면 같은 함정을 또 밟는다.
2. **체크박스 목록이 여러 툴에 있다** — A00145(Edit / Create) · A00210 · A00275 · A00280 · A00290 V01/V02.
3. **새 리스트 위젯이 아니라 붙이는 방식** — 이미 쓰고 있는 `JUN_mod_filter_qt` · 개수 라벨 · 툴 고유의
   항목 색/툴팁을 그대로 두고 한 줄로 붙인다. TSL(`MOD_tsl_qt`) 에 옵션으로 넣지 않은 것도 같은 이유다 —
   체크 목록 대부분은 TSL 이 아니라 맨 `QListWidget` 이다.

## 규칙

- **보이는 것이 작업 대상** — 필터에 가려진 행은 고른 범위 안에 있어도 체크를 바꾸지 않는다.
- **신호는 한 번** — 여러 행을 바꿀 때 신호를 막고 바꾼 뒤 `itemChanged(누른 행)` 를 한 번만 쏜다.
  바뀐 행 전부가 필요하면 `checksChanged(list)` 를 받는다.
- **코드에서 부르는 `setCheckState` 는 전파하지 않는다** — `Check All` 같은 호출부 로직은 그대로 동작한다.
- 창이 닫히며 리스트가 먼저 지워진 뒤 오는 이벤트는 조용히 넘긴다(mayapy 실측 `already deleted`).

## 검증 (2026-09-18)

- mayapy 2024(PySide2): A00145 Attribute > Edit 에서 실제 클릭 14항목 — Shift/Ctrl 선택, 반복 체크/해제,
  고르지 않은 행, Space, 필터로 가린 행, `itemChanged` 1회, Preview 갱신, Clear Checks.
- PySide6 오프스크린: 같은 조작 + `checksChanged` 개수.

## 적용한 곳 (2026-09-18)

| 툴 | 목록 | 비고 |
|----|------|------|
| A00145 v01.49 · v01.50 | Attribute > Edit · Attribute > Create | |
| A00290_BSTool_V02 v02.02 | Mix Targets Sources · Targets to Modify | Sources 는 `checksChanged` 로 행마다 라벨(`x배율`)을 다시 쓴다. Targets 의 회색(소스) 행은 건너뛴다 |
| A00275 v01.28 | Select > By Weight 의 Bound Joints | 이 탭의 자체 eventFilter(56줄)가 원본 — 공용으로 교체 |
| A00210 v01.31 | Lineage `Add Node from Scan...` · Path Structure `Folders to record` | standalone(PySide6) — `Framework.qt` 는 maya 없이 import 된다 |

**적용하지 않은 것**
- 트리 · 표: A00210 Path Structure 미리보기(`QTreeWidget`, 자체 eventFilter), A00275 Layer(`QTreeWidget`),
  A00420 Wrapper(`QTreeWidget`), A00280(`QTableWidget`). 이 동작은 `QListWidget` 전용이다.
- A00290_BSTool(V01): V02 로 넘어간 옛 버전이라 그대로 둔다(새 버전은 새 폴더 규칙).

## 호출부가 알아야 할 것

- **행마다 할 일이 있으면 `checksChanged` 를 받는다.** `itemChanged` 는 누른 행 하나로만 온다.
  순서는 `checksChanged` → `itemChanged` 라서, 행별 처리가 끝난 뒤 목록 전체 처리(개수 · 동기화)가 한 번 돈다.
- **비활성(`~ItemIsEnabled`) 행은 클릭으로도 전파로도 바꾸지 않는다** — Qt 기본 처리와 같다.
