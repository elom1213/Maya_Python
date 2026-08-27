# Framework — `MOD_filter_qt_v01` (공용 검색/필터 위젯)

`QListWidget` 에 붙이는 **재사용 검색 위젯**. 입력하는 즉시 일치하는 항목만 남고 나머지는 숨는다.

- 모듈: `JUN_All/Framework/qt/MOD_filter_qt_v01.py`
- 별칭: `from Framework.qt import JUN_mod_filter_qt`
- 클래스: `JUN_mod_filter_qt_v01`
- 출처: `A00290_BSTool` 의 Base Shape / Shape Editor 탭 Filter 를 공용으로 뽑은 것 (2026-08-03)

> 앞으로 **검색 기능이 있는 툴은 이 위젯으로 통일**한다. 툴마다 "선택만 해 주는 검색",
> "다시 질의하는 검색" 처럼 제각각이던 것을 하나의 감각으로 맞추는 것이 목적이다.

---

## 1. 화면 구성

```
Attributes                              Number: 2 / 47   ← number_label (선택)
┌───────────────────────────────────┐
│ browInnerUp                        │
│ mouthInnerCorner                   │
└───────────────────────────────────┘
Filter [ inner              ] [Clear]
```

`Filter` 라벨 · 입력 칸 · `Clear` 버튼 한 줄짜리 `QWidget` 이다. 라벨/버튼은 끌 수 있다.

---

## 2. 매칭 규칙

- **부분 일치** — `Inner` 로 `browInnerUp` 이 잡힌다.
- **대소문자 무시** — `inner` 도 같다.
- 공백으로 나눈 **여러 단어는 AND** — `brow up` → `browInnerUp`, `browOuterUpLeft` …
  한 단어만 쓰면 단순 부분 일치와 동일하다.
- 항목을 **지우지 않고 `setHidden` 으로 가린다.** 필터를 비우면 그대로 돌아온다.

---

## 3. 사용법

```python
from Framework.qt import JUN_mod_filter_qt

self.lbl_number = QLabel("Number: 0")
self.flt = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
    self.lw_targets,                       # 필터를 걸 QListWidget
    placeholder="Type any part of a name",
    number_label=self.lbl_number)          # 없으면 생략 가능
layout.addWidget(self.flt)
```

**목록을 다시 채운 뒤에는 반드시 `refresh()`** — 새 항목은 숨김 상태가 초기화돼 있어서,
부르지 않으면 필터가 걸린 채로 전부 보이게 된다.

```python
self.lw_targets.clear()
self.lw_targets.addItems(names)
shown, total = self.flt.refresh()
```

`number_label` 을 주면 `Number: N`(필터 없음) / `Number: 보이는수 / 전체수`(필터 중)로 자동 갱신된다.

### 주요 메서드

| 메서드 | 설명 |
|--------|------|
| `attach(list_widget)` | 대상 리스트 지정 + 즉시 1회 적용 |
| `refresh()` | 현재 입력값으로 다시 거른다. `(보이는 수, 전체 수)` 반환 |
| `text()` / `set_text(s)` / `clear()` | 입력값 조회·설정·비우기 |
| `visible_items()` / `visible_texts()` | 지금 보이는 항목 |
| `visible_selected()` | **`(보이면서 선택된 이름들, 가려진 선택 수)`** — 4장 |
| `select_all_visible()` | 보이는 것만 전체 선택 (`QListWidget.selectAll` 대체) |
| `filtered` (Signal) | 필터가 바뀔 때 `(보이는 수, 전체 수)` 로 발생 |

---

## 4. "보이는 것이 작업 대상" — 반드시 지킬 규칙

> [!warning] Qt 는 항목을 **숨겨도 선택 상태를 유지**한다.
> `list_widget.selectedItems()` 를 그냥 쓰면 **필터에 가려 안 보이는 항목까지 작업 대상**이 된다.
> 사용자는 화면에 보이는 것만 처리될 거라고 기대하므로, 이건 조용한 오작동이다.

그래서 작업 대상은 **항상** `visible_selected()` 로 고르고, 가려진 선택이 있으면 **로그로 알린다**.

```python
names, hidden = self.flt.visible_selected()
if not names:
    if hidden:
        self.log("[Warning] The {0} selected item(s) are hidden by the filter "
                 "- clear the filter or select a visible one.".format(hidden))
    else:
        self.log("[Warning] Select item(s) first.")
    return

if hidden:
    self.log("[INFO] {0} selected item(s) hidden by the filter were skipped.".format(hidden))
```

`Select All` 버튼도 `selectAll` 대신 **`select_all_visible`** 에 연결한다.

```python
btn_all.clicked.connect(self.flt.select_all_visible)
```

선택 자체는 지우지 않으므로, 여러 검색어를 오가며 고른 뒤 **필터만 비우면 한 번에** 처리된다.

---

## 5. 컬럼이 있는 목록 — `tree_widget` (v2 추가)

컬럼이 필요한 목록은 `QTreeWidget` 을 쓴다
(예: `A00330_NamingTool` 의 Set Rename 탭 — 세트 이름 / 타입 / 멤버 수 / 새 이름 / 상태 5열).
`tree_widget` 으로 넘기면 **최상위 항목**을 `setHidden` 으로 거른다.
어느 열로 거를지는 `tree_column`(기본 0).

```python
self.flt = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
    tree_widget=self.tree, number_label=self.lbl_number,
    placeholder="Type any part of a set name")
```

`visible_items()` / `visible_texts()` / `visible_selected()` / `select_all_visible()` 은
`QListWidget` 모드와 **똑같이** 동작한다(이름은 `tree_column` 열의 텍스트).
목록을 다시 채운 뒤 `refresh()` 를 부르는 것도 같다.

> **함정 — 두 위젯의 `selectedItems()` 가 다르다** (Maya 2024 / PySide2 실측)
>
> | | 항목을 선택한 뒤 숨기면 |
> |---|---|
> | `QListWidget` | `selectedItems()` 에 **그대로 들어온다** |
> | `QTreeWidget` | `selectedItems()` 에서 **빠진다** (단 `item.isSelected()` 는 여전히 `True`) |
>
> 그래서 트리 모드의 `visible_selected()` 는 `selectedItems()` 를 쓰지 않고 **최상위 항목을
> 직접 훑어 `isSelected()` 로 판정**한다. 그냥 `selectedItems()` 를 썼다면 **"가려진 선택 수"가
> 늘 0 이 되어** 4장의 경고가 조용히 사라졌을 것이다.

---

## 6. `QListWidget` 이 아닌 목록 — `rows_provider`

탭에 따라 목록이 `QListWidget` 이 아니라 **행 위젯을 쌓아 만든 것**일 때가 있다
(예: `A00290_BSTool` Shape Editor 탭 — 행마다 Edit 버튼·슬라이더·스핀박스).
이때는 `rows_provider` 로 **`(이름, 위젯)` 쌍의 목록을 돌려주는 콜러블**을 넘긴다.
숨기기는 `widget.setVisible()` 로 한다.

```python
self.flt_se = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
    rows_provider=lambda: [(r["name"], r["row"]) for r in self._se_rows],
    placeholder="Type any part of a target name")
self.flt_se.filtered.connect(self._on_se_filtered)   # 개수 라벨 등 후처리
```

- 행을 새로 만들 때마다 `refresh()` 를 부르면 필터가 유지된다.
- 이 모드에는 **리스트 항목 선택 개념이 없다**(각 행이 자체 선택 상태를 가진다) →
  `visible_selected()` / `select_all_visible()` 대신 **`visible_rows()`** 를 쓴다.
- 개수 라벨을 **두 곳**(탭 + 확장 창)에 반영해야 하는 등 후처리가 필요하면
  `number_label` 대신 **`filtered(shown, total)` 시그널**을 받아 직접 쓴다.

---

## 7. 적용 현황

| 툴 | 위치 | 모드 | 버전 |
|----|------|------|------|
| `A00145_RigConnect` | Connect 탭 Source/Destination, Attribute 탭 | `QListWidget` | v01.19 (실기 확인 완료) |
| `A00290_BSTool` | Base Shape 탭 | `QListWidget` | v01.13 |
| `A00290_BSTool` | Shape Editor 탭 | `rows_provider` | v01.13 |
| `A00170_driverTool` | Remap Value 탭, Stretch 탭 2개 그룹 | `QListWidget`(TSL 내부) | v01.13 |
| `A00330_NamingTool` | Set Rename 탭 | **`tree_widget`** | v01.02 |

> **TSL(`JUN_mod_tsl_qt_v01`) 안의 리스트에 붙일 때**는 `tsl.list_widget` 을 넘긴다.
> 단, TSL 의 `get_all_items()` / `selected_items()` 는 **숨김을 모른다** — 작업 대상은
> 반드시 위젯의 `visible_selected()` 로 고를 것.

> 검색 기능을 새로 넣거나 기존 검색을 손볼 때는 **자체 구현하지 말고 이 위젯을 쓴다.**
> 규칙(매칭 방식, "보이는 것이 작업 대상")이 바뀌면 여기 한 곳만 고치면 된다.
