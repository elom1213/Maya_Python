---
title: 공용 TSL 이름 표시 모드 (Outliner Name / Full Path) 계획서
aliases: [TSL name display, Outliner Name mode, tsl 표시 이름, 같은 이름 | 표시]
tags: [plan, maya-python, framework, widget, tsl, A00275]
updated: 2026-11-19
---

# 공용 TSL 이름 표시 모드 (Outliner Name / Full Path) 계획서

> 작성 2026-11-19 · 상태: **1단계 구현 완료 (2026-11-19, A00275 v01.44 · mayapy 오프스크린 시험) · 마야 GUI 확인 전** · 2단계: 모든 툴(나중)
>
> 사용자 결정 (2026-11-19):
> - 같은 이름 줄은 **툴팁만으로** 구별한다(흐린 부모 이름 같은 덧붙임은 없음).
> - 1단계는 **A00275_skinTool_V01 만** 쓸 수 있게 한다.
> - 기본 모드는 **Outliner Name**.
> - 나중에 모든 툴에 넣고, 거기서 Full Path / Outliner Name 을 고를 수 있게 한다.
>
> 이 문서만 보고 구현할 수 있도록 고칠 파일 · 함수 · 줄 위치 · 시험까지 적었다. 줄 번호는 작성 시점(커밋 `5b2c4a0c`) 기준이다.

---

## 0. 요약

- **문제**: TSL 리스트는 마야 `cmds.ls(sl=True)` 가 돌려준 문자열을 그대로 항목 글자로 쓴다. 씬에 같은 이름 노드가 있으면 마야는
  구별되는 최소 경로(`A|dup`, `B|dup`)를 주므로, 리스트에 `|` 가 섞여 보인다. 아웃라이너는 `dup` 만 보여 준다.
- **해법**: 항목 글자(`item.text()`)는 **그대로 두고**, 리스트에 Qt 델리게이트를 달아 **그릴 때만** 마지막 이름(`dup`)을 보여 준다.
  같은 이름 줄은 마우스를 올리면 **툴팁으로 전체 경로**(`|A|dup`)를 보여 준다.
- **왜 글자를 바꾸면 안 되나**: 툴들이 리스트 글자를 그대로 **노드 이름으로** 쓴다(`get_all_items()` 44개 파일, `item.text()` 직접 33곳,
  TSL 내부 10여 곳). 글자를 `dup` 으로 바꾸면 같은 이름이 있을 때 엉뚱한 노드를 잡거나 에러가 난다.
- **1단계 범위**: TSL 생성자에 켜는 옵션(`name_display=True`)을 하나 두고, A00275 의 TSL 11개만 켠다. 다른 툴은 **한 글자도 안 바뀐다**
  (옵션 기본값 False → 델리게이트를 아예 달지 않는다).
- **모드는 전역 설정 하나**: QSettings `JUN/tsl` 의 `name_display` (`outliner` 기본 / `full`). 리스트 **우클릭 메뉴**로 바꾸고,
  바꾸면 열려 있는 모든 옵트인 TSL 이 바로 다시 그려진다.

---

## 1. 현재 구조 (조사 결과)

### 1-1. TSL 위젯 `Framework/qt/MOD_tsl_qt_v01.py` (1172줄)

| 위치 | 내용 | 이 작업과의 관계 |
|------|------|------------------|
| 128 `UUID_ROLE = Qt.UserRole + 1` | 항목에 `(uuid, component)` 보관 | 툴팁의 현재 경로를 여기서 찾는다 |
| 205~218 `_looks_like_node()` · `_split_component()` | 노드 이름 모양 판정 · `노드.컴포넌트` 분리 | 표시 이름 함수가 그대로 쓴다 |
| 232 `_uuid_of(name)` | 이름이 **유일할 때만** UUID 를 붙인다 | `cmds.ls(sl)` 가 `A|dup` 을 주므로 같은 이름도 UUID 가 붙는다 |
| 307~ `JUN_mod_tsl_qt_v01.__init__` | 생성자 옵션들 | 새 옵션 `name_display` 추가 |
| 422~430 `_build_ui` 안 `self.list_widget = _ListWidget(...)` | 리스트 위젯 생성 | 여기 뒤에 델리게이트 · 우클릭 메뉴 연결 |
| 496 `get_all_items()` | **항목 글자** 목록 | 바뀌면 안 된다(시험으로 고정) |
| 506 `get_all_nodes()` | UUID 로 푼 현재 경로 | 변화 없음 |
| 840 `_fill_list` · 922 `_add_item` · 1010 `_set_records` | 항목 만들기 | 변화 없음(글자 그대로 넣는다) |
| 949 `_node_of(item)` | 항목 → 현재 노드 경로(UUID 우선, 중복 UUID 는 글자로 좁힘) | 툴팁이 이걸 부른다 |
| 1117 `_on_sort` | `sorted(records, key=rec[0])` = **글자(경로) 기준** | Outliner Name 모드면 **보이는 이름 기준**으로 |
| 871 `_sync_summary` | 요약 모드 라벨의 `First:` 는 이미 `split("|")[-1]` | 변화 없음 |

- TSL 리스트에는 **지금 델리게이트도 우클릭 메뉴도 없다**(저장소 전체 grep: `tools/` 에서 `list_widget.setItemDelegate` ·
  `list_widget.setContextMenuPolicy` 0건). 공용 `viewZoom` 의 델리게이트는 트리 5곳에만 붙어 있고 TSL 에는 없다 → 1단계 충돌 없음.
- 별칭: `Framework/qt/__init__.py` 6행 `from Framework.qt import MOD_tsl_qt_v01 as JUN_mod_tsl_qt`.

### 1-2. 공용 필터 `Framework/qt/MOD_filter_qt_v01.py`

- `refresh()` (204~) 가 `self._matches(item.text(), tokens)` 로 거른다 = **저장된 글자(경로)** 기준.
- A00275 `Select > By Weight` 의 조인트 리스트(TSL)에 붙어 있다. Outliner Name 모드에서 `A` 를 치면 화면엔 `dup` 인 줄이 걸러지지 않고 남는다
  → **보이는 글자 기준으로 거르게** 바꾼다(§3-4).

### 1-3. A00275 의 TSL 11개

| 파일:줄 | 속성 | 담기는 것 |
|---------|------|-----------|
| `app/ui/main_window.py:358` | `tsl_classic_from` | 조인트 또는 메시 (Transfer > Classic) |
| `app/ui/main_window.py:360` | `tsl_classic_to` | 〃 |
| `app/ui/main_window.py:446` | `tsl_transfer_src` | 소스 메시 |
| `app/ui/main_window.py:451` | `tsl_transfer_tgt` | 타겟 메시 |
| `app/ui/main_window.py:902` | `tsl_joints_a` | Migrate A 조인트 |
| `app/ui/main_window.py:905` | `tsl_joints_b` | Migrate B 조인트 |
| `app/ui/main_window.py:1675` | `tsl_eb_joints` | Expand Bind 조인트 |
| `app/ui/move_tab.py:107` | `tsl_from` | Move From 조인트 |
| `app/ui/move_tab.py:109` | `tsl_to` | Move To 조인트 |
| `app/ui/flood_tab.py:111` | `tsl_joints` | Flood 조인트 |
| `app/ui/weight_select_tab.py:105` | `tsl_joints` | By Weight 조인트(체크박스 + 필터) |

- 이 툴은 모두 `get_all_items()` · `get_all_nodes()` 로 읽는다 → 글자를 안 바꾸므로 **코어 · 핸들러 수정 없음**.
- By Weight 는 `_fill_joints` 가 `cmds.ls(p)` (짧고 유일한 이름)로 채우고 체크박스를 단다. 델리게이트 기본 그리기가 체크박스를 그대로 그린다.

### 1-4. 전역 설정 저장 선례

- 공용 `viewZoom` 이 `QSettings("JUN", "viewZoom")` 에 배율을 기억한다(마야 안팎 모두 동작, optionVar 아님).
  같은 방식으로 `QSettings("JUN", "tsl")` 를 쓴다 → 2단계에서 standalone 툴(마야 밖)에도 그대로 통한다.

---

## 2. 동작 명세

### 2-1. 두 모드

| 모드 | 값 | 보이는 글자 | 툴팁 |
|------|----|-------------|------|
| **Outliner Name** (기본) | `"outliner"` | 노드 부분의 마지막 이름. `A|dup` → `dup`, `|keep` → `keep` | 노드 항목이면 **현재 전체 경로** (`|A|dup`) |
| Full Path | `"full"` | 항목 글자 그대로(지금 동작) | 지금처럼 없음 |

### 2-2. 표시 이름 규칙 `display_name(text)` — 순수 함수

1. `_looks_like_node(text)` 가 False 면 **그대로**: `(Null)`, 공백 들어간 글자, 숫자로 시작하는 글자, 파일 이름 등.
2. `node, comp = _split_component(text)` (첫 `.` 기준).
3. `leaf = node.rsplit("|", 1)[-1]`. 비면(`"|"` 같은 이상한 글자) 원래 `text` 를 돌려준다.
4. `comp` 가 있으면 `leaf + "." + comp`.
5. 네임스페이스는 **남긴다**(아웃라이너도 보여 준다): `grp|ns:dup` → `ns:dup`.

| 입력 | 출력 |
|------|------|
| `A|dup` | `dup` |
| `|A|dup` | `dup` |
| `keep` | `keep` |
| `grp|ns:dup` | `ns:dup` |
| `A|pCube1|pCube1Shape.vtx[3]` | `pCube1Shape.vtx[3]` |
| `A|pCube1.vtx[0:5]` | `pCube1.vtx[0:5]` |
| `nodeA.translateX` | `nodeA.translateX` |
| `(Null)` | `(Null)` |
| `` (빈 글자) | `` |

### 2-3. 툴팁 (같은 이름 구별 수단)

- Outliner Name 모드에서 **노드 항목**(UUID 가 있거나 `_node_of` 가 경로를 찾는 항목)에 마우스를 올리면 **현재 롱네임**을 보여 준다.
  - 같은 이름 줄만이 아니라 **모든 노드 줄**에 띄운다. 어느 줄이 같은 이름인지 미리 셀 필요가 없고(목록 전체 비교 비용 없음),
    사용자 입장에서도 "올리면 경로" 로 규칙이 하나다.
  - 경로는 **그 순간** `_node_of(item)` 으로 구한다 → 담은 뒤 리네임 · 리페어런트해도 맞는 경로가 뜬다.
  - 컴포넌트 항목이면 `_node_of` 가 `노드.컴포넌트` 를 주므로 그대로 쓴다.
- 항목에 이미 `ToolTipRole` 이 있으면(예: `(Null)` 의 안내문) **그것을 우선**한다.
- 씬에서 사라진 노드(UUID 는 있는데 못 찾음)는 `"<item.text()>  (not in the scene)"`.
- Full Path 모드에서는 지금처럼 아무것도 띄우지 않는다(기본 처리로 넘긴다).

### 2-4. 모드 바꾸기 — 리스트 우클릭 메뉴

- 옵트인 TSL 의 리스트에서 우클릭하면 메뉴 하나:
  ```
  Show Names
    (•) Outliner Name
    ( ) Full Path
  ```
  (체크 가능한 액션 두 개, `QActionGroup` 배타.) UI 문자열은 영어.
- 고르면 `set_name_display(mode)` → QSettings 저장 + 살아 있는 **모든 옵트인 TSL** 의 `viewport().update()` + 정렬은 다시 하지 않는다
  (지금 순서를 바꾸지 않는다 — 사용자가 Sort 를 누를 때만).
- 1단계에서는 A00275 의 리스트만 옵트인이므로, 이 메뉴도 A00275 에서만 보인다.

### 2-5. Sort

- `_on_sort` 의 정렬 키:
  - 옵트인이고 Outliner Name 모드면 `key=lambda rec: (display_name(rec[0]), rec[0])` — 보이는 이름 순, 같은 이름은 경로 순(결정적).
  - 그 밖(옵트인 아님 또는 Full Path)은 **지금 그대로** `key=lambda rec: rec[0]`.
- 요약 모드(`_deferred`)의 `.sort()` 도 같은 키를 쓴다.
- 대소문자 처리는 지금과 같다(그냥 문자열 비교).

### 2-6. 필터 (`MOD_filter_qt_v01`)

- `refresh()` 가 `item.text()` 대신 **보이는 글자**로 거른다: 리스트의 델리게이트가 `QStyledItemDelegate` 면
  `delegate.displayText(item.text(), QLocale())` 를 쓰고, 아니면 `item.text()`.
  - 기본 `QStyledItemDelegate.displayText` 는 문자열을 그대로 돌려주므로 **옵트인 아닌 리스트는 결과가 같다**.
  - 트리(`QTreeWidget`) 경로와 `rows_provider` 경로는 건드리지 않는다.

### 2-7. 바뀌지 않는 것 (시험으로 고정)

- `item.text()`, `get_all_items()`, `selected_items()`, `get_all_nodes()`, `selected_nodes()`, UUID, 씬 선택 동기화, 중복 판정(`append_unique`),
  요약 모드, `(Null)` 빨간 글씨, `select_by_texts()`.
- 옵트인 아닌 TSL: 델리게이트를 달지 않고(`list_widget.itemDelegate()` 는 Qt 기본), 우클릭 메뉴도 없다.

---

## 3. 구현 (파일별)

### 3-1. `Framework/qt/MOD_tsl_qt_v01.py`

**(a) 모듈 상수 · 설정 함수** — `UUID_ROLE` 정의(128행) 아래에 둔다.

```python
# 이름 표시 모드 (2026-11-19~). 항목 글자는 그대로 두고 **그릴 때만** 바꾼다 - 툴들이 글자를 노드 이름으로 쓰기 때문.
NAME_OUTLINER = "outliner"      # 마지막 이름만 (아웃라이너처럼). 같은 이름은 툴팁으로 구별
NAME_FULL = "full"              # 항목 글자 그대로 (A|dup)
NAME_MODES = (NAME_OUTLINER, NAME_FULL)
DEFAULT_NAME_DISPLAY = NAME_OUTLINER
NAME_SETTINGS_ORG = "JUN"
NAME_SETTINGS_APP = "tsl"
NAME_SETTINGS_KEY = "name_display"

_NAME_WIDGETS = weakref.WeakSet()   # 옵트인 TSL 들 - 모드가 바뀌면 다시 그린다


def get_name_display():
    """지금 이름 표시 모드. 저장값이 없거나 이상하면 DEFAULT_NAME_DISPLAY."""

def set_name_display(mode):
    """모드를 저장하고 살아 있는 옵트인 TSL 을 모두 다시 그린다. 모르는 값은 ValueError."""

def display_name(text):
    """§2-2 규칙. 순수 함수(마야 호출 없음)."""
```

- `import weakref` 를 모듈 머리 `import re` 옆에 더한다.
- `get_name_display` 는 `QSettings(ORG, APP).value(KEY)` 를 읽고 `NAME_MODES` 에 없으면 기본값. 예외는 삼키고 기본값.
- `set_name_display` 는 저장 뒤 `for w in list(_NAME_WIDGETS): w.refresh_names()` (위젯이 이미 파괴됐으면 `RuntimeError` 무시).

**(b) 델리게이트 클래스** — `_ListWidget` 클래스(102행~) 아래.

```python
class _NameDelegate(QStyledItemDelegate):
    """이름 표시 모드 델리게이트. 글자(DisplayRole)는 그대로, 그리는 글자와 툴팁만 바꾼다."""

    def __init__(self, owner):
        super().__init__(owner.list_widget)
        self._owner = owner          # JUN_mod_tsl_qt_v01 (툴팁에서 _node_of 를 부른다)

    def displayText(self, value, locale):
        text = super().displayText(value, locale)
        if get_name_display() == NAME_OUTLINER:
            return display_name(text)
        return text

    def helpEvent(self, event, view, option, index):
        if event.type() == QEvent.ToolTip and get_name_display() == NAME_OUTLINER \
                and not index.data(Qt.ToolTipRole):
            tip = self._owner.full_path_tooltip(index.row())
            if tip:
                QToolTip.showText(event.globalPos(), tip, view)
                return True
        return super().helpEvent(event, view, option, index)
```

- `get_name_display()` 를 그릴 때마다 QSettings 에서 읽으면 느리다 → **모듈 캐시** `_NAME_STATE = {"mode": None}` 를 두고,
  `get_name_display()` 는 캐시가 비었을 때만 QSettings 를 읽는다. `set_name_display()` 가 캐시를 갱신한다.
- `QEvent` · `QToolTip` · `QStyledItemDelegate` · `QActionGroup` · `QMenu` · `QSettings` · `QLocale` 은 **추가 작업 없이 쓸 수 있다** —
  `Framework/qt/qt.py` 가 PySide6/PySide2 의 `QtWidgets` · `QtCore` · `QtGui` 를 모두 `*` 로 내보낸다(확인함). PySide6 의 `QAction` · `QActionGroup`
  (`QtGui`)도 여기에 들어 있다.

**(c) 생성자 옵션** — `__init__` 시그니처(307행)에 `name_display=False` 를 `select_no_expand=False,` 다음에 더하고,
속성 `self.name_display = bool(name_display)`. 독스트링/주석: "True 면 전역 이름 표시 모드(Outliner Name / Full Path)를 따른다.
2026-11-19 은 A00275 만 켠다(계획서 참고)".

**(d) `_build_ui` 연결** — 리스트 위젯을 만든 직후(430행 `layout.addWidget(self.list_widget)` 다음):

```python
self._name_delegate = None
if self.name_display:
    self._name_delegate = _NameDelegate(self)
    self.list_widget.setItemDelegate(self._name_delegate)
    self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
    self.list_widget.customContextMenuRequested.connect(self._on_name_menu)
    _NAME_WIDGETS.add(self)
```

**(e) 새 메서드** (공개 API 구역, `count()` 근처)

| 메서드 | 내용 |
|--------|------|
| `name_display_mode()` | 옵트인이면 `get_name_display()`, 아니면 `NAME_FULL` (= 지금 보이는 방식) |
| `shown_text(row)` | 그 행의 **보이는 글자**. 옵트인 + Outliner 면 `display_name(text)`, 아니면 `text` |
| `full_path_tooltip(row)` | §2-3. `item = list_widget.item(row)`; `node = self._node_of(item)`; 있으면 `node`; UUID 가 있는데 못 찾으면 `"{text}  (not in the scene)"`; 노드가 아니면 `None` |
| `refresh_names()` | `self.list_widget.viewport().update()` |
| `_on_name_menu(pos)` | §2-4 메뉴. `menu.exec_(self.list_widget.viewport().mapToGlobal(pos))` — PySide6 는 `exec`; `qt.py` 에 호환 처리가 있으면 그것을, 없으면 `getattr(menu, "exec_", None) or menu.exec` |

- `_node_of` 는 컴포넌트면 `노드.컴포넌트` 를 돌려준다(현재 동작) → 툴팁에 그대로 쓴다.
- 우클릭 메뉴의 액션 글자: `"Outliner Name"`, `"Full Path"`, 메뉴 제목 `"Show Names"` (서브메뉴 대신 섹션 머리말로 `menu.addSection("Show Names")`).
  각 액션 툴팁: `"Show only the last name, like the Outliner. Hover a row to see its full path."` / `"Show the name as listed (A|dup when names clash)."`

**(f) `_on_sort` (1117행)** — §2-5 키 함수를 `_sort_key()` 로 빼서 두 경로가 같이 쓴다.

**(g) 모듈 독스트링** — "UUID 보관" 절 다음에 "이름 표시 모드 (2026-11-19~)" 절을 더한다(왜 글자를 안 바꾸는지, 옵트인, 전역 설정, 툴팁, 2단계 예정).

### 3-2. `Framework/qt/MOD_filter_qt_v01.py`

- `refresh()` 의 리스트 경로(216행 근처) 한 줄:
  ```python
  hit = True if not tokens else self._matches(self._shown(item), tokens)
  ```
- 헬퍼:
  ```python
  def _shown(self, item):
      """리스트에 **보이는** 글자. 델리게이트가 그릴 때 바꾸는 글자(TSL 이름 표시 모드)를 따른다."""
      delegate = self.list_widget.itemDelegate()
      if isinstance(delegate, QStyledItemDelegate):
          try:
              return delegate.displayText(item.text(), QLocale())
          except Exception:
              pass
      return item.text()
  ```
- 필터가 TSL 을 import 하지 않게(순환 방지) 델리게이트에만 의존한다.

### 3-3. A00275 — 11개 TSL 에 `name_display=True`

§1-3 표의 11곳 생성자 호출에 `name_display=True` 한 인자씩 더한다. 다른 코드는 바꾸지 않는다.

### 3-4. 버전 · 문서

| 파일 | 내용 |
|------|------|
| `tools/A00275_skinTool_V01/app/config/version.py` | `01.44` + 이력 주석 ("리스트 이름이 아웃라이너처럼 - 같은 이름은 툴팁으로 전체 경로, 우클릭 Show Names 로 Full Path") |
| `tools/A00275_skinTool_V01/CHANGELOG.md` | v01.44 항목 |
| `docs/A00275_skinTool_V01.md` | 머리 버전 줄 + 짧은 절 "리스트 이름 표시 (v01.44~)" |
| `docs/Framework_MOD_tsl_qt.md` | 새 절 "이름 표시 모드 — `name_display` (2026-11-19~)" (§2 요약 + 옵트인 방법 + 2단계 예정) · 생성 옵션 표에 `name_display` |
| `docs/Framework_MOD_filter_qt.md` | 리스트 모드는 **보이는 글자**로 거른다는 한 줄 |
| `docs/WORKLOG.md` | 2026-11-19(또는 작업일) 항목 |
| `.claude/memory/` | 새 메모 `framework-tsl-name-display.md` + `MEMORY.md` 공용 위젯 구역 한 줄 |

---

## 4. 시험

### 4-1. 새 공용 시험 `Framework/tests/test_tsl_name_display.py` (mayapy 2024, 오프스크린)

준비: `QT_QPA_PLATFORM=offscreen`, `QApplication` 을 `maya.standalone.initialize()` **보다 먼저**. 시작할 때 QSettings 키의 원래 값을 기억하고
끝에서 되돌린다(사용자 설정을 시험이 바꿔 놓지 않게).

씬: 그룹 `A`, `B` 아래 같은 이름 조인트 `dup`, 최상위 `keep`, 그룹 `A` 아래 메시 `pCube1`.

| # | 확인 | 기대 |
|---|------|------|
| 1 | `display_name` 표 §2-2 전부 | 표와 같음 |
| 2 | 키 삭제 후 `get_name_display()` | `"outliner"` (기본) |
| 3 | 옵트인 TSL 에 `cmds.ls(sl)` (`A|dup`, `B|dup`, `keep`) 담기 → `get_all_items()` | 담은 글자 그대로 (`A|dup` …) |
| 4 | 델리게이트 `displayText(item.text(), QLocale())` | `dup`, `dup`, `keep` |
| 5 | `shown_text(row)` | 4 와 같음 |
| 6 | `full_path_tooltip(0)` / `(1)` | `|A|dup` / `|B|dup` |
| 7 | `A` 를 `A2` 로 리네임 → `full_path_tooltip(0)` | `|A2|dup` (UUID 로 따라감) |
| 8 | 노드 삭제 → 툴팁 | `... (not in the scene)` |
| 9 | `(Null)` 항목 | 보이는 글자 `(Null)`, 툴팁 = 기존 안내문(`ToolTipRole`) |
| 10 | 컴포넌트 `A|pCube1.vtx[0]` | 보이는 글자 `pCube1.vtx[0]`, 툴팁 `|A|pCube1.vtx[0]` |
| 11 | `set_name_display("full")` → 4 다시 | 글자 그대로 (`A|dup`), 툴팁 `None` 경로로 기본 처리 |
| 12 | 두 번째 옵트인 TSL 도 모드가 함께 바뀌는지 | 같은 모드 |
| 13 | QSettings 에 저장됐는지 | `"full"` |
| 14 | `set_name_display("bad")` | `ValueError` |
| 15 | Outliner 모드 Sort: `B|alpha`, `A|zeta`, `keep` 담고 Sort | `B|alpha`, `keep`, `A|zeta` (보이는 이름 순) |
| 16 | Full Path 모드 Sort | `A|zeta`, `B|alpha`, `keep` (지금과 같음) |
| 17 | 옵트인 **아닌** TSL | `itemDelegate()` 가 `_NameDelegate` 아님, contextMenuPolicy 기본, `get_all_items` 같음 |
| 18 | 우클릭 메뉴 슬롯 직접 호출(액션 트리거) | 모드 바뀜 (오프스크린에서 `QMenu.exec_` 는 멈추므로 메뉴를 띄우지 말고, 메뉴를 만드는 헬퍼 `_build_name_menu()` 를 따로 두어 액션을 `trigger()` 한다) |
| 19 | 행 클릭 → 씬 선택 | `|B|dup` 이 선택됨 (선택 동기화 불변) |
| 20 | 필터: 옵트인 리스트에 `A` 입력 | `A|dup` 줄 숨김(보이는 글자 `dup` 에 `a` 없음), `keep` 숨김; `dup` 입력 → 두 줄 보임 |
| 21 | 필터: 옵트인 아닌 리스트에 `A` 입력 | 지금처럼 `A|dup` 보임 |

> 18 의 이유: 메모 [[wip-a00480-filetool]] — 오프스크린에서 `QMenu.exec_` 는 멈춘다.

### 4-2. A00275 회귀 (mayapy 2024)

- `tests/test_flood_ui.py` (29) · `test_move_ui.py` (15) · `test_transfer_classic_ui.py` (9) · `test_tab_fit_ui.py` (34) · `test_weight_flood.py` (31, Kangaroo 없이) ·
  `test_weight_move.py` (45) · `test_weight_smooth_regression.py` — 전부 그대로 통과.
- 새 확인 하나를 `test_flood_ui.py` 끝에 더한다: `MainWindow` 의 `findChildren(JUN_mod_tsl_qt_v01)` 가 **11개 전부 `name_display=True`**,
  그리고 같은 이름 씬에서 Flood 리스트의 보이는 글자가 `dup` · 툴팁이 `|A|dup` · `joints()` 가 풀패스.

### 4-3. 다른 툴 회귀 (옵트인 아님 = 불변 확인)

- `Framework/tests/test_list_rules.py`, `Framework/tests/test_view_zoom.py`, `Framework/tests/test_tab_fit_rollout.py` 통과.
- 필터를 쓰는 툴 하나: A00110_V02 의 필터가 걸린 리스트가 TSL 이 아니면 영향 없음을 grep 으로 확인(필터는 `QListWidget` 이면 다 받으므로 §2-6 의
  "기본 델리게이트는 같은 글자" 가 보장).

### 4-4. 마야 GUI 확인 (사용자)

- A00275 를 열고 같은 이름 조인트 씬에서 Flood `Get Bound Joints` → `dup` 두 줄, 마우스를 올리면 각자 경로 툴팁.
- 리스트 우클릭 → `Full Path` → A00275 의 모든 리스트가 `A|dup` 으로. 마야를 다시 켜도 기억.

---

## 5. 2단계 — 모든 툴 (나중, 이번 범위 아님)

1. `name_display` 기본값을 `True` 로 바꾼다(한 줄). 그러면 38개 툴의 154개 리스트가 따른다.
2. 그 전에 확인할 것:
   - **노드가 아닌 리스트**(`attach_uuids=False`: blendShape 타겟 별칭, 어트리뷰트 이름, 파일 이름)에서 `display_name` 이 글자를 줄이는 경우가 없는지.
     `|` 가 없는 글자는 안 바뀌므로 대부분 무관하지만, `node|path.attr` 처럼 경로가 든 어트리뷰트 리스트는 짧아진다 → 툴별로 판단해 그 리스트만 `name_display=False`.
   - **툴이 자기 델리게이트나 우클릭 메뉴를 TSL 리스트에 다는지** — 작성 시점 0건이지만 2단계 때 다시 grep.
   - **TSL 에 viewZoom 을 붙이는 경우** 델리게이트가 덮인다 → 그때는 `_ZoomDelegate` 가 `_NameDelegate` 를 상속하거나 `displayText` 를 위임하도록 합친다.
   - `item.text()` 를 직접 **화면 문구**(로그 등)로 쓰는 곳은 그대로 경로가 찍힌다 — 로그는 경로가 더 정확하므로 그대로 둔다.
3. 모드 선택 UI: 우클릭 메뉴는 그대로 전 툴에 생긴다. 필요하면 공용 메뉴(`tool_menu.COMMON_MENUS`)에 `View > List Names` 를 더해 메뉴 바에서도 바꾸게 한다.
4. 문서: `Framework_MOD_tsl_qt.md` 의 "1단계 A00275 만" 문구를 지우고, 툴 가이드들에는 한 줄씩.

---

## 6. 위험과 대응

| 위험 | 대응 |
|------|------|
| 글자를 노드 이름으로 쓰는 툴이 깨짐 | 글자를 안 바꾼다(델리게이트). 시험 #3 · #17 · A00275 회귀로 고정 |
| 같은 이름 두 줄을 화면으로 구별 못 함 | 툴팁(사용자 결정). 우클릭으로 Full Path 전환도 가능 |
| 그릴 때마다 QSettings 읽기 → 느림 | 모듈 캐시(`_NAME_STATE`) |
| 툴팁이 마야를 부름(`_node_of`) | 마우스를 올린 **한 줄**만, 그 순간에만 → 비용 무시 가능 |
| PySide2 / PySide6 차이 (`exec_`/`exec`, `QAction` 위치) | `qt.py` 호환 처리 사용. 시험은 mayapy 2024(PySide2), `display_name` · 필터 부분은 시스템 python(PySide6)으로도 돌린다 |
| 오프스크린에서 메뉴가 멈춤 | 메뉴 만들기와 띄우기를 나눠 액션을 직접 `trigger()` |
| 키보드 검색(리스트에 글자 입력 시 해당 줄로 이동)은 저장 글자 기준 | 1단계는 그대로 둔다(같은 이름 리스트가 짧아 체감 작음). 필요하면 2단계에서 `keyboardSearch` 재정의 |
| 리네임 뒤 보이는 이름이 예전 이름 | 지금도 같은 동작(글자 기준). 툴팁은 현재 경로. 실시간 이름 표시는 범위 밖(필요하면 별도 계획) |

---

## 7. 작업 순서 (체크리스트)

1. [x] `qt.py` 가 필요한 Qt 클래스를 다 내보내는지 확인 — 세 모듈 `*` import 라 추가 없음(작성 시 확인).
2. [x] `MOD_tsl_qt_v01.py` §3-1 (a)~(g).
3. [x] `MOD_filter_qt_v01.py` §3-2.
4. [x] `Framework/tests/test_tsl_name_display.py` §4-1 작성 · 통과.
5. [x] A00275 11곳 `name_display=True` §3-3.
6. [x] A00275 회귀 + 새 확인 §4-2, Framework 회귀 §4-3.
7. [x] 버전 01.44 · CHANGELOG · 문서 · WORKLOG · 메모 §3-4.
8. [x] 로컬 커밋(경로 명시). 푸시는 사용자가 그 턴에 요청할 때만.
