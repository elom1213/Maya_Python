# A00145_RigConnect — MEL ConnectionTool V04.02 + A00140 ConnectClosest 병합 계획서 (PySide 포팅)

## Context (배경 / 목적)

두 개의 연결(connection/constraint) 툴을 하나의 PySide 툴로 병합한다.

| 소스 | 위치 | 형태 |
|------|------|------|
| **MEL `ConnectionTool V04.02`** | `~/Documents/maya/2024/scripts/JUN_MEL_ConnectionTool_V04_02.mel` | `tabLayout` 3탭(`Constrain` / `Connect` / `List Connected`), 모든 로직이 `global proc` (23개) |
| **Python `A00140_ConnectClosest`** | `JUN_All/tools/A00140_ConnectClosest` (v01.02) | arch (B) PySide, Driven/Driver 2-list + constraint 체크박스, 최근접 1:1 constraint |

**목표**: 새 경로 **`JUN_All/tools/A00145_RigConnect`** 에 병합 툴을 만든다.

요구 사항(확정):
1. MEL 의 **3탭 UI(`Constrain` / `Connect` / `List Connected`)를 그대로 보존**한다(레이아웃·기능 동일).
2. `A00140_ConnectClosest` 의 UI/기능을 **새 탭 `Connect Closest`** 로 추가한다(총 4탭).
3. **MEL 로직은 전체 Python 포팅**한다 — `global proc` → `maya.cmds` Python 함수.
4. **UI 는 PySide(Qt)로 구성**한다 — `maya.cmds` UI 가 아니라 `QTabWidget` 기반.
5. **`Connect Closest` 탭은 나머지 탭과 동일한 Qt 스타일**로 통일한다.
6. **툴 이름은 `RigConnect`** (창 제목 `RigConnect v01.00`, 셸프 라벨 `RigConnect`).
   기존 `A00090_ConnectionBuilder`(MetaHuman 페이셜) / `A00140_ConnectClosest`(원본)와 구분.

> 결과물은 `CLAUDE.md` 의 **아키텍처 (B) — Maya 내 PySide 툴** 형태가 된다.
> 원본 `A00140_ConnectClosest` 와 MEL 파일은 **무수정 보존**한다(레퍼런스 유지).

---

## 1. 기준 레퍼런스 — `A00060_jointTool_V02`

`A00060_jointTool_V02` 가 **정확히 같은 부류**(MEL 다탭 → PySide `QTabWidget` + `maya.cmds` 로직 + dragDrop 설치)이므로
이 툴을 구조 템플릿으로 그대로 삼는다. 차용 패턴:

- `launch.py` `run(reload_module=True)` — `DEV_MODE` 면 `dev.reloader_v02.reload_for_tool("tools.A00145_RigConnect")` 후
  `WINDOW_OBJECT_NAME` 으로 기존 창 정리 → `MainWindow` → `ThemeManager` → `show()`.
- `main_window.py` — `from Framework.qt.qt import *`, `QWidget` + `QTabWidget`, 탭별 `_build_*_tab()` 메서드,
  **공유 로그창**(`self.te_log`, 탭 생성보다 먼저), `Help > About` 메뉴바, 고유 `WINDOW_OBJECT_NAME`, copyright 푸터.
- `app/core/*` — UI 비의존 `maya.cmds` 로직(매니저). `app/core/__init__.py` 에서 export.
- `app/ui/collapsible.py` — `CollapsibleBox`(MEL `frameLayout -collapsable` 대응, A00060 것 복사).
- `__dragDrop_A00145.py` — 셸프 버튼 설치(고유 파일명 + `sys.modules.pop(__name__, None)`).

### 재사용 위젯 — `JUN_mod_tsl_qt_v01` (핵심)

`Framework/qt/MOD_tsl_qt_v01.py` 의 `JUN_mod_tsl_qt_v01`(별칭 `Framework.qt.JUN_mod_tsl_qt`)이
MEL 모든 탭이 반복하는 **textScrollList + Select/Add/Del/Up/Down/(Sort)** 패턴을 그대로 대체한다.
A00140 도 이미 이 위젯의 `driven_tsl`/`driver_tsl` 로 구성돼 있어 **이식이 자연스럽다.**

| MEL proc | `JUN_mod_tsl_qt_v01` 대응 |
|----------|---------------------------|
| `JUN_cmd_upd_tex_numTsl`(Select 버튼·Number 갱신) | `show_select` 버튼 + 내장 `Number: N` 라벨 |
| `JUN_cmd_append_selected` (Add) | `_on_add` (`append_unique`) |
| `JUN_cmd_delete_selected` (Delete) | `_on_del` |
| `JUN_cmd_selMov` up/down | `_on_up` / `_on_down` |
| `JUN_cmd_tsl_select` (항목 클릭 → 씬 선택) | `itemSelectionChanged` 내장 |
| `textScrollList -q -allItems` | `get_all_items()` |
| `textScrollList -q -selectItem` | `selected_items()` |

생성자: `JUN_mod_tsl_qt_v01(title=..., select_label=..., show_sort=..., multi_select=..., list_min_height=..., log_callback=self.log)`.
→ **MEL 의 TSL 인프라 proc 군(11~15)은 새로 만들 필요가 없다.** 위젯 인스턴스만 배치하고 값만 읽는다.

---

## 2. 디렉터리 / 파일 구조 (신규)

```
JUN_All/tools/A00145_RigConnect/
├── __init__.py                         # from .launch import run  (run 만 노출)
├── launch.py                           # run(reload_module=True): reload → MainWindow → "coral_dark" → show
├── __dragDrop_A00145.py                # 셸프 버튼 설치 (고유 파일명, A00060_V02 패턴)
├── requirements.txt                    # (Maya 내장 PySide; 참고용)
└── app/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── version.py                  # VERSION = "01.00", LAST_UPDATE
    ├── core/                           # ── UI 비의존 maya.cmds 로직 ──
    │   ├── __init__.py                 # 매니저/함수 export
    │   ├── constrain_manager.py        # [Constrain 탭] MEL 포팅
    │   ├── connect_manager.py          # [Connect 탭]   MEL 포팅 (attr 연결 + 52 facial + attr 나열/검색)
    │   ├── stream_manager.py           # [List Connected 탭] MEL 포팅 (hyperShade up/down stream)
    │   ├── maya_scene.py               # [Connect Closest 탭] A00140 maya_scene.py 복사 (무수정)
    │   └── closest_connector.py        # [Connect Closest 탭] A00140 closest_connector.py 복사 (무수정)
    └── ui/
        ├── __init__.py
        ├── collapsible.py              # A00060_V02 CollapsibleBox 복사
        └── main_window.py              # QTabWidget(Constrain/Connect/List Connected/Connect Closest) + 공유 로그 + Help>About
```

> **A00140 core 는 복사 이식**한다(import 의존 대신). 이유: 병합 툴을 self-contained 로 두고 원본 A00140 을
> 무수정 보존하기 위함. `closest_connector.py`/`maya_scene.py` 는 이미 UI 비의존이라 **그대로 복사**하면 된다.

---

## 3. MEL → Python 포팅 매핑 (core)

각 `global proc` 를 어느 매니저 함수로 옮기는지의 1:1 표. **순수 로직만** 옮기고
(textScrollList 질의·체크박스·라디오 읽기 같은) UI 접근은 `main_window.py` 에서 값으로 전달한다.
UI 인프라 proc(`JUN_cmd_tsl_select`/`append`/`delete`/`selMov`/`upd_tex_numTsl`)은 **위젯이 흡수**하므로 포팅 제외.

### 3.1 `constrain_manager.py` (Constrain 탭)

| MEL proc | Python 함수 | 비고 |
|----------|-------------|------|
| `JUN_get_vct_from_rb` / `JUN_get_conType_from_vct` | UI 가 enum 문자열 전달 | 5종: `parent`/`scale`/`point`/`orient`/`pointOnPoly` |
| `JUN_cmd_constrain_tgt_to_flw` | `constrain(targets, followers, con_type, maintain_offset)` | followers>targets 면 단일 target 브로드캐스트, 아니면 1:1 (아래 주의) |

`con_type` → `cmds.parentConstraint/scaleConstraint/pointConstraint/orientConstraint/pointOnPolyConstraint`,
`maintain_offset` → `mo=` 플래그. (MEL 의 `eval("<type> <flag>")` 패턴을 함수 디스패치로 대체)

### 3.2 `connect_manager.py` (Connect 탭)

| MEL proc | Python 함수 | 비고 |
|----------|-------------|------|
| `JUN_cmd_upd_tsl_attr` / `JUN_cmd_upd_tsl_obj_n_attr` | `list_attrs(obj, search="")` | `listAttr` + compound 펼치기(`listAttr -multi`) + `.` 중첩 제거 |
| `JUN_cmd_upd_tsl_search` | `filter_attrs(attrs, search)` | textField 검색 → 매칭 항목 (UI 가 선택 갱신) |
| `get_childAttr_indexed` | `next_free_multi_index(obj_attr)` | `getNextFreeMultiIndex` / `connectionInfo -isDestination` 다중 인덱스 처리 |
| `JUN_cmd_connect_attr` | `connect_attrs(src_objs, dst_objs, src_attrs, dst_attrs)` | **3가지 브로드캐스트 패턴**(아래 주의) → `connectAttr -force` |
| `JUN_cmd_connect_52Facial` | `connect_52_facial(src_objs, dst_objs)` | 하드코딩 52 ARKit attr 리스트 상수화, `catch` → `try/except` 로 누락 스킵 |
| `JUN_is_exist` / `is_memoized` | `_match(base, token)` / `_seen(memo, txt)` | 순수 헬퍼 (또는 파이썬 `in`/`set` 으로 대체) |

### 3.3 `stream_manager.py` (List Connected 탭)

| MEL proc | Python 함수 | 비고 |
|----------|-------------|------|
| `JUN_cmd_listStream` | `list_stream_types(objs, upstream: bool)` | `hyperShade -listUpstreamNodes/-listDownstreamNodes` → `nodeType` 중복 제거 |
| `JUN_cmd_update_streamNods` | `nodes_by_types(objs, types, upstream: bool)` | 선택 타입으로 필터된 노드 리스트 반환 |

> MEL 은 up/down 방향을 전역 `$GLB_JUN_str_flag_streamTyp` 로 보관한다. **Python 에서는 전역 금지** —
> 방향(`upstream` bool)을 `main_window` 가 보관(예: `self._stream_upstream`)해 `nodes_by_types` 에 인자로 넘긴다.

### 3.4 `closest_connector.py` + `maya_scene.py` (Connect Closest 탭 — A00140 복사)

A00140 의 두 파일을 **무수정 복사**. 공개 API 그대로 사용:

- `connect_closest(drivers, drivens, constraint_keys, maintain_offset=True) -> (results, errors)`
- `find_closest(driver, driven_pool) -> (closest, dist)`
- `CONSTRAINT_TYPES = [("parent","Parent",...), ("point",...), ("orient",...), ("scale",...)]`
- `MayaScene` (world_position / distance(Euclidean) / *_constraint / selection / exists)

---

## 4. UI 구성 (`app/ui/main_window.py`)

`A00060_jointTool_V02/main_window.py` 골격을 그대로 따른다.

```
MainWindow(QWidget)  objectName = "JUN_A00145_RigConnect_window"  (제목 "RigConnect v01.00")
├─ QMenuBar : Help > About
├─ QTabWidget
│   ├─ Constrain       탭 : _build_constrain_tab()
│   ├─ Connect         탭 : _build_connect_tab()
│   ├─ List Connected  탭 : _build_list_connected_tab()
│   └─ Connect Closest 탭 : _build_connect_closest_tab()
├─ QTextEdit(read-only) : 공유 로그창 (탭 생성보다 먼저 만든다 — log_callback 으로 위젯에 주입)
└─ QLabel : copyright 푸터
```

### 4.1 위젯 매핑 (maya.cmds → Qt)

| MEL UI | Qt 위젯 |
|--------|---------|
| `textScrollList` + Add/Del/Up/Down/Select | `JUN_mod_tsl_qt_v01` |
| `radioCollection`+`radioButton` (constraint type 5종) | `QButtonGroup` + `QRadioButton` |
| `checkBox` (maintain offset) | `QCheckBox` |
| `textField` (attr 검색) | `QLineEdit` (+ `returnPressed` → Search) |
| `frameLayout -collapsable` (Connect 탭 Source/Dest) | `CollapsibleBox` (collapsible.py) |
| `frameLayout`(일반) / `paneLayout vertical2/top3` | `QGroupBox` / `QHBoxLayout`·`QVBoxLayout`·`QSplitter` |
| `button -bgc 0 0.6 0`(초록 액션 버튼) | `QPushButton` (인라인 색 제거, qss 테마로) |

### 4.2 탭별 구성 요약

- **Constrain 탭**: `tsl_targets` + `tsl_followers`(좌우) + Options(`QGroupBox`: Maintain Offset 체크박스 +
  constraint type 5 라디오) + `Constrain` 버튼. → `constrain(...)`.
- **Connect 탭**: Source 섹션(`CollapsibleBox`: `tsl_src_objs` + `tsl_src_attrs` + 검색 `QLineEdit`+Search,
  `Select Source Objects` 버튼이 attr 채움) / Destination 섹션(동일 구성) +
  `Connect Source to Destination` 버튼 + `Connect 52 facial target` 버튼. → `connect_attrs(...)` / `connect_52_facial(...)`.
- **List Connected 탭**: `tsl_objs` + `tsl_types` + `tsl_nodes`(3분할) +
  `List UpStream`/`List DownStream` 버튼(→ `list_stream_types`, 방향 저장) + `Search` 버튼(→ `nodes_by_types`).
- **Connect Closest 탭**: A00140 `MainWindow._build_*` 레이아웃을 **탭용 QWidget 으로 이식**(메뉴바·푸터 제거).
  `tsl_driven` + `tsl_driver` + constraint type 체크박스(`CONSTRAINT_TYPES`) + Maintain Offset + `Connect` 버튼.
  → `connect_closest(drivers, drivens, keys, mo)`.

### 4.3 테마 / 색상

- `launch.py` 에서 `ThemeManager.load_theme_to_widget(window, "coral_dark")` (A00060_V02 와 동일 계열로 통일).
  - 참고: A00140 원본은 `"red"`. 병합본은 in-Maya 다탭 패밀리와 맞춰 `coral_dark` 권장(원하면 `red` 로 변경 가능).
- MEL 초록 `Select`/액션 버튼·회색 frame `bgc` 인라인 색은 **qss 테마로 대체**(개별 위젯 인라인 색 지양).
- 모든 `JUN_mod_tsl_qt_v01(log_callback=self.log)` 로 위젯 메시지를 공유 로그창에 연결.

---

## 5. 진입점 / 설치 (launch · dragDrop · init)

- `__init__.py` : `from .launch import run` / `__all__ = ["run"]`.
- `launch.py` : A00060_V02 `run()` 복제 — 패키지명만 `tools.A00145_RigConnect`, `WINDOW_OBJECT_NAME` 으로 기존 창 정리.
- `__dragDrop_A00145.py` : A00060_V02 dragDrop 복제 —
  - `TOOL_LABEL = "RigConnect"`, `SHELF_COMMAND` 가 `tools.A00145_RigConnect.run(True)` 호출.
  - **고유 파일명 + 끝에서 `sys.modules.pop(__name__, None)`**(드롭 캐시 충돌 방지, `CLAUDE.md` 3장 규칙).
  - A00140 의 `__dragDrop_A00140.py` 에서 식별자/라벨/`TOOL_PATH` 문자열을 **A00145 로 전부 교체**(카피 잔재 주의).
- DEV reload : `dev/reload_path_list.py` 는 `RELOAD_PACKAGES = ["Framework","tools"]` 로 `tools.*` 전체 커버 → **수정 불필요**.

---

## 6. 포팅 시 정밀 주의 포인트 (버그 유발 구간)

1. **`connect_attrs` 3가지 패턴** (`JUN_cmd_connect_attr`): MEL 의 분기 그대로 이식 —
   ① `1 src obj & len(srcAttr)==len(dstAttr)` → 한 src 를 각 dst 에 attr 인덱스별 연결,
   ② `len(srcAttr)==1 & len(dstAttr)==1` → obj 쌍 1:1 (min 길이),
   ③ `len(srcAttr)==len(dstAttr)` → obj 쌍 × attr 인덱스 모두. 그 외 "Connection fail" 경고.
   `connectAttr -force` 유지. **selectItem(선택된 attr) vs allItems(obj 전체)** 구분 정확히.
2. **`constrain` 브로드캐스트**: `len(followers) > len(targets)` 면 단일 target → 모든 follower,
   아니면 인덱스 1:1(min 길이). MEL `eval` 디스패치 → 함수 매핑으로.
3. **compound/multi attr 처리** (`get_childAttr_indexed`/`listAttr -multi`): `getNextFreeMultiIndex` 를
   `try/except` 로 감싸 compound 여부 판정, child 펼치기. `.` 중첩 attr 필터링 로직 보존.
4. **52 facial 리스트**: MEL 하드코딩 순서/철자 그대로 상수(`FACIAL_52`)로 옮기고, 누락 attr 은 `try/except` 로 스킵.
5. **stream 방향 전역 제거**: MEL `$GLB_..._streamTyp` 대신 `upstream: bool` 인자 + UI 상태 보관.
6. **PySide2/PySide6 양립**: 반드시 `from Framework.qt.qt import *` 만 사용(직접 PySideN import 금지).
7. **Maya 2023 호환**(메모리): constraint/connectAttr/hyperShade 기반이라 영향 없음. 확인만.
8. **UI 텍스트 영어 고정**(메모리): 버튼/라벨/로그 문자열 전부 영어. MEL 의 오타(`Matinatin Offset`,
   `Distination`)는 **올바른 영어로 교정**(`Maintain Offset`, `Destination`). 한국어는 주석/독스트링만.

---

## 7. 작업 순서 (제안)

1. `A00060_jointTool_V02` 복제 → `A00145_RigConnect` 골격(`__init__`/`launch`/`config/version.py`=`01.00`/`collapsible.py`).
2. **A00140 core 복사**(`maya_scene.py`+`closest_connector.py`) → `Connect Closest` 탭 먼저 이식·검증(가장 쉬움, 이미 동작 코드).
3. `constrain_manager.py` 포팅 → `Constrain` 탭.
4. `connect_manager.py` 포팅(attr 나열/검색 → 연결 3패턴 → 52 facial) → `Connect` 탭.
5. `stream_manager.py` 포팅 → `List Connected` 탭.
6. 공유 로그/테마(`coral_dark`)/`Help>About`/copyright 푸터 마무리.
7. `__dragDrop_A00145.py` + 진입점 정리.
8. Maya 에서 드롭 설치 → 4탭 각 기능 수동 검증(constrain 5종, attr connect 3패턴+52facial, up/down stream, closest).
9. `docs/A00145_RigConnect.md`(사용법) 작성, `version.py` 갱신.

---

## 8. 산출물

- `JUN_All/tools/A00145_RigConnect/` (위 2장 트리 전체)
- `JUN_All/docs/A00145_RigConnect.md` (탭별 사용법 — 후속)
- 원본 `A00140_ConnectClosest` / MEL 파일 / 빈 `A00145_ConnecttionTool` 폴더 처리:
  **빈 오타 폴더 `A00145_ConnecttionTool` 는 제거**하고 `A00145_RigConnect` 로 신규 생성.

---

## 9. 미해결 / 확인 필요

- 테마: `coral_dark`(권장, 다탭 패밀리 통일) vs `red`(A00140 원본 계승) — 기본 `coral_dark`.
- `Connect` 탭 Source/Dest frame 을 접이식(`CollapsibleBox`)으로 둘지 단순 `QGroupBox` 로 둘지 — MEL 이 collapsable 이므로 `CollapsibleBox` 권장.
- 창 기본 크기: MEL 480×890 → 4탭 Qt 기준 재산정(A00060_V02 의 540×820 정도 시작).
- `Connect 52 facial target`: 하드코딩 52 attr 목록을 MEL 원본에서 정확히 추출해 상수로 옮길 것(철자/순서 보존).
- 셸프 아이콘 명칭(`pythonFamily.png` 기본, 별도 아이콘 시 교체).
