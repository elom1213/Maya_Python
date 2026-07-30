---
title: 공용 리스트 위젯 (JUN_mod_tsl_qt) 사용법
aliases: [MOD_tsl_qt, JUN_mod_tsl_qt, TSL 위젯, 공용 TSL]
tags: [maya-python, framework, widget, tsl, selection-order]
updated: 2026-07-29
---

# 공용 리스트 위젯 `JUN_mod_tsl_qt_v01`

`JUN_All/Framework/qt/MOD_tsl_qt_v01.py` 에 있는 **모든 PySide 툴이 공유하는 리스트(TSL) 위젯**이다.
maya.cmds 판 `Framework/ui/MOD_tsl_01_01.py` 의 Qt 대응물로, 현재 저장소 안에서 **75곳**이 쓴다
(A00060 / A00090 / A00110 / A00145 / A00170 / A00350 / A00380 / A00390 / A00400 …).

개별 툴 문서는 "리스트는 재사용 위젯 `JUN_mod_tsl_qt_v01`" 이라고만 적고, **위젯 자체의 동작·옵션은
이 문서**를 본다.

- **모듈**: `Framework/qt/MOD_tsl_qt_v01.py`
- **별칭**: `from Framework.qt import JUN_mod_tsl_qt` → `JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(...)`
- **관련**: `Framework/qt/MOD_timeRange_qt_v01.py`(`JUN_mod_timeRange_qt`, Start/End 구간 입력)

---

## 1. 화면 구성

```
[ Select Objects ]                     ← show_select (라벨은 select_label 로 교체 가능)
Title              [x] Order   Number: N   ← 타이틀(bold) + Order 체크박스 + 개수
┌──────────────────────────────────┐
│ pCube1.vtx[5]                    │   QListWidget (기본 다중선택)
│ pCube1.vtx[0]                    │   항목을 고르면 씬에서도 그 오브젝트가 선택된다
└──────────────────────────────────┘
[Add][Del][Up][Down]                   ← show_add / show_del / show_up / show_down
[            Sort            ]         ← show_sort
[           Reverse          ]         ← show_reverse (기본 꺼짐)
```

| 요소 | 동작 |
|------|------|
| **Select Objects** | 현재 Maya 선택으로 리스트를 **교체** |
| **Order** | 체크하면 **고른 순서**대로 담는다 (3장) |
| **Add** | 현재 Maya 선택을 **중복 없이 추가** (중복은 로그로 안내) |
| **Del / Up / Down** | 선택 항목 삭제 / 한 칸 위·아래 이동 |
| **Sort / Reverse** | 이름 오름차순 정렬 / 현재 순서 통째로 뒤집기 |

---

## 2. 생성 옵션

```python
from Framework.qt import JUN_mod_tsl_qt

tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
    title="Objects",
    show_select=True, show_add=True, show_del=True,
    show_up=True, show_down=True, show_sort=True,
    show_reverse=False,          # 순서 뒤집기 버튼 (기본 꺼짐)
    show_order=True,             # Order 체크박스 표시 (기본 켬)
    order_default=False,         # 열자마자 Order ON (기본 꺼짐)
    multi_select=True,
    list_min_height=None,        # 지정 없으면 바닥값 100px
    select_label="Select Objects",
    log_callback=self.log,       # 없으면 print
)
```

주요 메서드

| 메서드 | 설명 |
|--------|------|
| `get_all_items()` | 표시 텍스트(담을 때의 이름) 목록 |
| `get_all_nodes()` | **UUID 로 되찾은 현재 경로** 목록 — 리네임/리페어런트 뒤에도 유효. 실제 씬 작업은 이걸 쓴다 |
| `selected_items()` / `selected_nodes()` / `selected_rows()` | 리스트에서 고른 항목 |
| `set_items(list)` / `append_unique(list)` / `clear()` / `count()` | 채우기·추가·비우기 |
| `add_button(label, cb, index=None)` | 편집 버튼 행에 커스텀 버튼 끼워넣기 |
| `set_order_tracking(bool, quiet=False)` / `is_order_tracking()` | 선택 순서 유지 on/off (3장) |
| `maya_selection()` | **현재 Maya 선택**(flatten). Order 가 켜져 있으면 고른 순서 (3장 "리스트를 거치지 않는 버튼") |

---

## 3. 선택 순서 유지 — `Order` 체크박스

### 왜 필요한가

`cmds.ls(sl=True)` 는 **컴포넌트(vtx/edge/face)를 고른 순서가 아니라 인덱스 순서**로 돌려준다.
버텍스를 `5 → 0 → 3 → 1` 로 찍어도 리스트에는 `0, 1, 3, 5` 로 올라간다.
(**오브젝트/트랜스폼은 pref 와 상관없이 원래부터 선택 순서를 유지**한다 — 순서가 깨지는 건 컴포넌트뿐이다.)

선택 순서를 얻으려면 Maya 프리퍼런스 **Track Selection Order** 가 켜져 있어야 하고
(`cmds.selectPref(trackSelectionOrder=True)`), 그 뒤 `cmds.ls(orderedSelection=True)` 로 읽어야 한다.

> [!warning] pref 가 꺼져 있으면 `ls(orderedSelection=True)` 는 **에러 없이 조용히 인덱스 순서**를 준다.
> "순서가 되는지"는 반환값이 아니라 pref 를 직접 조회해야 알 수 있다.

### 동작

- **체크 ON** — Track Selection Order pref 를 켜고, Select/Add 가 `ls(orderedSelection=True, flatten=True)`
  로 **고른 순서 그대로** 담는다.
- **체크 OFF** — **우리가 켠 경우에만** pref 를 원래 값으로 되돌린다. 사용자가 원래 켜두고 쓰던 설정이면
  건드리지 않는다. 리스트는 다시 기본(인덱스) 순서로 담긴다.
- TSL 위젯이 여러 개 떠 있어도 **전역 refcount** 로 pref 를 관리해서, 하나를 꺼도 다른 위젯의 순서 추적이
  끊기지 않는다. 창이 닫혀 위젯이 파괴되면 pref 를 자동으로 반납한다(전역 설정을 남기지 않는다).

### 사용 순서

1. 리스트 헤더의 **`Order`** 를 체크한다 (로그: `Selection order: ON - pick your objects/components again ...`).
2. Maya 에서 **원하는 순서대로 다시 클릭**한다.
3. **Select Objects**(교체) 또는 **Add**(추가) — 찍은 순서대로 리스트에 올라간다.

> [!important] pref 는 **켠 시점부터** 순서를 기록한다. 체크하기 **전에** 해둔 선택은 순서 정보가 없어서
> 그대로 Select 하면 여전히 인덱스 순서로 담긴다. 반드시 체크한 뒤 다시 고른다.

### 왜 항상 켜두지 않는가

1. `trackSelectionOrder` 는 툴 설정이 아니라 **Maya 전역 프리퍼런스**(userPrefs 에 저장)라, 툴이 말없이
   켜두면 다른 작업·툴에까지 영향이 남는다.
2. 어차피 "켠 뒤 다시 선택" 제약이 있어서, 항상 켜둬도 사용자가 모르면 오해만 커진다. 의식하고 켜는 편이 낫다.
3. 순서가 필요 없는 대부분의 리스트에서는 인덱스 순서가 오히려 읽기 편하다.

순서가 **항상** 중요한 툴이라면 그 툴에서 `order_default=True` 로 열자마자 켜면 되고, 씬 노드가 아닌
리스트(어트리뷰트·파일명 등)라면 `show_order=False` 로 체크박스를 숨긴다.

### 리스트를 거치지 않는 버튼 — `maya_selection()`

"리스트에 올리지 않고 **지금 선택한 것으로 바로 실행**" 하는 버튼을 툴에 둘 때는
`ls(orderedSelection=...)` 를 호출부에서 다시 쓰지 말고 **`maya_selection()`** 을 쓴다.
Order 판정(pref 조회) · `flatten` · pref 가 꺼졌을 때의 폴백이 이미 들어 있어서
**Select / Add 버튼과 정확히 같은 규칙**이 보장된다 — 한 툴 안에서 두 경로의 순서가 어긋나지 않는다.

```python
objs = self.tsl.maya_selection()          # Order ON 이면 고른 순서
if not objs:
    self.log("[ERR] nothing selected in the scene")
    return
if not self.tsl.is_order_tracking() and len(objs) > 1:
    self.log("[INFO] 'Order' is off - components come in index order.")
```

Order 가 꺼진 상태를 **조용히 넘기지 말고 로그로 알리는 것**이 중요하다. 사용자는 자기가 찍은
순서대로 될 거라고 기대하는데, 컴포넌트는 인덱스 순서로 들어와도 에러가 나지 않는다.

첫 적용: `A00060_jointTool_V02` 의 **`Match to Sel`** 버튼 (v01.04) — Curve 탭 `Match to Obj` 는
리스트를, `Match to Sel` 은 현재 선택을 대상으로 같은 축 옵션으로 조인트를 만든다.

### 순서가 의미를 갖는 대표 사용처

| 툴 | 순서가 결정하는 것 |
|----|--------------------|
| `A00350_ArrayCreator` | UE Control Rig Item Array 원소 순서 |
| `A00390_WindTool` | 리스트 순번 = 조인트별 wind offset 인덱스 |
| `A00060_jointTool_V02` (Curve/Divide) | 생성되는 조인트 체인 순서 (`Match to Sel` 은 리스트 없이 선택 순서) |
| `A00400_CurveTool` | 커브 CV·방향 순서 |
| `A00110_animTool` (Stagger Offset) | 리스트 순서 = 스태거 단계 |
| `A00090_ConnectionBuilder` / `A00145_RigConnect` | n→n 페어링에서 Source↔Target 짝 |

---

## 4. UUID 보관 (항목이 가리키는 실제 오브젝트)

항목의 **표시 텍스트는 이름**이지만, 씬 노드인 항목은 **UUID + 컴포넌트 접미사**를 함께 들고 있다
(`Qt.UserRole + 1`). 리스트에서 항목을 고르면 이름이 아니라 UUID 로 현재 경로를 되찾아 씬에서 선택한다.

- 담은 뒤 **리네임/리페어런트** 해도 정확히 그 오브젝트가 잡힌다.
- **같은 이름** 오브젝트가 늘어나도 `More than one object matches name` 로 실패하지 않는다.
- 같은 파일을 **레퍼런스로 여러 번** 걸면 사본들이 **UUID 를 공유**한다(import 는 재할당, reference 는 유지).
  이때는 담을 때의 표시 이름으로 후보를 좁혀 고른다.
- 노드가 아닌 항목(어트리뷰트 이름·파일명·노드 타입 등)은 UUID 가 없어 예전처럼 이름으로 동작한다.

씬을 실제로 조작하는 코드는 `get_all_items()`(표시 이름)가 아니라 **`get_all_nodes()` / `selected_nodes()`**
를 써야 위 이점을 얻는다.

---

## 5. 로그 · 문제 해결

| 로그 / 증상 | 뜻 |
|-------------|-----|
| `... is already in the list.` | Add 로 담으려는 오브젝트가 이미 리스트에 있다(현재 씬 경로 기준 판정) |
| `Not in the scene anymore: ...` | UUID 는 알지만 씬에서 삭제된 항목을 골랐다 |
| `Selection order: ON - pick ... again` | Order 를 켰다. **다시 선택해야** 순서가 기록된다 |
| `Selection order: OFF ...` | Order 를 껐다. pref 도 원래 값으로 돌아갔다 |
| Order 를 켰는데 여전히 인덱스 순서 | 체크하기 **전에** 해둔 선택이다. 다시 고르고 Select/Add |
| 컴포넌트가 아니라 오브젝트인데 순서가 그대로 | 정상. 오브젝트는 Order 없이도 선택 순서가 유지된다 |

---

## 6. 검증 메모 (mayapy)

- `selectPref -q -trackSelectionOrder` 기본값 **False**. 이 상태에서 `ls(orderedSelection=True)` 는
  **에러 없이 인덱스 순서**를 반환한다 → 반환값으로 판별 불가, pref 를 조회할 것.
- pref ON 이면 `ls(orderedSelection=True, flatten=True)` 가 `vtx[5], vtx[0], vtx[3], vtx[1]` 처럼 **찍은
  순서** 그대로 반환. 마퀴로 한 번에 여러 개 추가 / 해제 후 재선택(맨 뒤로 이동) / 오브젝트+컴포넌트 혼합 정상.
- pref 를 켜기 **이전** 선택은 순서가 기록되지 않는다.
- **mayapy 안에서는 위젯 자체를 띄울 수 없다** — `maya.standalone` 이 이미 `QGuiApplication` 을 만들어 둬서
  `QWidget` 생성이 실패한다(`QWidget: Cannot create a QWidget without QApplication`).
  위젯 배선 테스트는 **stub `maya.cmds` + PySide6**(맨 파이썬)로 돌린다.
