# A00190_FKIK_General_Tool — 제작 계획서

## 1. 목적 / 배경

레거시 단일 파일 `01_Modules/JUN_PY_FKIK_General_Tool_V01_02.py`(2481줄, maya.cmds UI)를
현행 프레임워크의 **(B) Standalone/Qt 앱 아키텍처**로 리팩토링하여
`JUN_All/tools/A00190_FKIK_General_Tool` 에 새 툴로 재구현한다.

- 기능: 캐릭터 리그의 **FK/IK 매칭 & 베이크**. 팔·다리 × 좌·우 컨트롤러 목록을 모아
  FK↔IK 포즈를 스냅 매칭하고, 프레임 구간을 베이크한다. 보조로 매칭용 **드라이버 오브젝트
  (NURBS 삼각형 / locator)** 생성과 **세팅 JSON 저장·로드**를 제공한다.
- UI 는 **PySide(Qt)** 로 재작성하고, 로직은 `app/core` 로 분리한다(UI 비의존).
- 공용 인프라(`JUN_All/Framework`)를 최대한 재사용한다.

### 확정된 방향 (사용자 결정)
1. **범위**: Qt화 + 정리 — 중복 UI를 Framework Qt 위젯으로 통합, core/ui 분리, 구세대 중복 경로 제거, 명백한 버그 수정. 기능 동작은 유지.
2. **pymel**: `pin_to_surface` 등은 **pymel 유지**. 단 **Maya 2023(Python 3.9 / PySide2)에서 동작**하도록 작성.
3. **레거시 경로**: 하드코딩 매처(`JUN_matcher_FKIK`, 특정 리그 이름 목록) **제거**, 제네릭(`_Gen`) 경로만 유지.

---

## 2. 레거시 코드 분석

### 2.1 코드 레이어 (유지/이전 대상)

| 레이어 | 레거시 심볼 | 역할 | 신규 위치 |
|--------|-------------|------|-----------|
| **매칭 코어** | `JUN_MATCH_twoObjects(tgt, flw, rotOrder, rotAxis, trs, rot)` | 각 쌍에 대해 rotateOrder/rotateAxis/world T/world R 복사. 모든 매칭의 원자 연산 | `core/matching.py` |
| **매칭/베이크** | `JUN_cmd_bake_IK_FK_Gen(...)` | 8 FK tsl + 8 IK tsl + 4 체크박스로 tgt/flw 조립 → 프레임 순회하며 매칭+키프레임. `is_bake`(단일/구간), `bake_ik`(방향) 플래그. 베이크 중 `OGSFreeze` 로 뷰포트 정지 | `core/matching.py` |
| **데이터 모델** | `JUN_matcher_FKIK_Gen`, `JUN_cage_FKIK_Gen`, `JUN_checker` | tgt/flw 리스트 컨테이너, 드라이버 묶음(cage), 체크 상태 | `core/matching.py` / `core/driver_setup.py` |
| **컨텍스트** | `OGSFreeze`, `DummyContext` | `ogs -pause` 로 베이크 가속 | `core/matching.py` |
| **드라이버 생성** | `pin_to_surface`(pymel), `JUN_cmd_FKIK_gen_setup_triangle_pos_objs`, `JUN_create_loc_for_given_objs`, `JUN_cmd_FKIK_gen_create_pos_objs_FKIK_Gen` | NURBS 삼각형 드라이버(폴 위치), FK↔IK locator 드라이버 생성 | `core/driver_setup.py` |
| **선택/리스트 유틸** | `BF_SELECTION_makeList_hierarchy*`, `JUN_get_list_ordered_by_token`, `JUN_get_set_by_token`, `JUN_get_list_by_shapes`, `BF_LIST_remove_repetitionArray`, `JUN_cmd_Search_By_Token`, `JUN_get_world_positions`, `JUN_average_position`, `JUN_parent` | 계층/토큰 필터, 위치 계산 | `core/selection_utils.py` |
| **세팅 IO** | `save_multiple_tsl_to_json`, `load_multiple_tsl_from_json`, `JUN_browse_json_save_path`, `JUN_cmd_FKIK_gen_save/load_setting` | tsl 내용을 JSON 으로 저장/복원 | `core/settings_io.py` |

### 2.2 UI 구조 (레거시 `PY_JUN_makeUI_general_FKIKTool`, ~1200줄)

- 윈도우 + menuBar(Help/About) + `tabLayout` 3탭:
  1. **Source**: "Set source: FK"(팔L/R·다리L/R 4 tsl) + "Set source: IK"(4 tsl).
  2. **Match FK**: 4 limb × (pose_obj, ctl) = **8 tsl**.
  3. **Match IK**: 4 limb × (pose_obj, ctl) = **8 tsl**.
- 하단 **Option** 프레임: 체크박스 4(팔/다리 L/R), Start/End Frame `intFieldGrp` 2,
  셋업 버튼 4(Set up triangle drivers / Drivers for FK IK switch / Load setting / Save setting),
  실행 버튼 4(Match IK / Match FK / Bake IK / Bake FK).
- 총 **tsl 위젯 24개** + 각 tsl 마다 Add/Del/Up/Down + Select Objects 버튼이 **수작업으로 ~24회 반복**.

### 2.3 리팩토링 대상 문제점

- **문자열 command 콜백 + 전역 컨트롤 이름 의존** (`command='JUN_cmd_...("name")'`) → 취약·디버깅 곤란.
- **거대한 UI 중복** (동일 tsl 블록 24회) → `Framework.qt.JUN_mod_tsl_qt` 위젯 재사용으로 제거.
- **로직-UI 강결합**: core 함수들이 tsl 이름 문자열을 받아 내부에서 `cmds.textScrollList` 조회.
  → core 는 **순수 `list[str]` 입출력**으로 바꾸고, UI 가 위젯↔리스트 변환을 담당.
- **구세대/신세대 혼재**: 하드코딩 `JUN_matcher_FKIK`·`JUN_cmd_match_IK_and_FK`·`JUN_cmd_bake_IK_to_FK` → 제거.
- **import 시 자동 실행** (`PY_JUN_makeUI_general_FKIKTool()` 모듈 최하단) → 제거, `run()` 진입점으로.
- **버그**: `JUN_get_list_ordered_by_token` 의 `is` 문자열 비교(→ `==`/`in`),
  삼각형 메시 이름 `"CH_r_triLeg_sfc,"` 의 오타 트레일링 콤마,
  베이크 루프 `range(timeStr, timeEnd)` 가 **마지막 프레임 누락**(→ `timeEnd+1` 확인 후 수정).

---

## 3. 목표 아키텍처

`A00180_abSymMesh` 레이아웃을 그대로 미러링한다(가장 최신 Maya-PySide 툴, 검증됨).

```
JUN_All/tools/A00190_FKIK_General_Tool/
├── __init__.py            # from .launch import run  →  run()만 노출
├── launch.py             # run(reload): DEV reload → MainWindow 생성/교체 → ThemeManager → show
├── __dragDrop_A00190.py  # DEV_MODE + 셸프 버튼 설치 / onMayaDroppedPythonFile (드래그&드롭)
└── app/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── version.py     # VERSION="01.00", LAST_UPDATE
    ├── core/              # 로직 (UI 비의존, list[str] 입출력) — Maya 씬 접근만 cmds/pymel
    │   ├── __init__.py
    │   ├── matching.py        # match_two_objects, MatchData, run_match_bake, OGSFreeze
    │   ├── driver_setup.py    # pin_to_surface(pymel), setup_triangle_drivers, create_switch_drivers, Cage
    │   ├── selection_utils.py # 계층/토큰 필터, 위치/평균, parent 헬퍼
    │   └── settings_io.py     # save_settings/load_settings (dict[str, list[str]] ↔ JSON)
    └── ui/
        ├── __init__.py
        ├── main_window.py     # MainWindow(QWidget): QTabWidget 조립 + Option/실행부 + 핸들러
        └── limb_list_group.py # 4-limb(arm L/R, leg L/R) tsl 묶음 컴포지트 위젯
```

### 핵심 설계 원칙
- **core 는 plain `list[str]` in/out**. UI 가 `JUN_mod_tsl_qt.get_all_items()` 로 읽어 core 에 넘기고,
  결과는 `set_items()` 로 위젯에 되돌린다. core 는 위젯/컨트롤 이름을 모른다.
- 매칭 방향/단일·구간 베이크는 **플래그가 아니라 명시적 인자/enum** 으로(`Direction.IK_TO_FK` 등) 가독성 개선.

---

## 4. Framework 재사용 매핑

| 필요 | 재사용 대상 (경로) | 사용법 |
|------|--------------------|--------|
| Qt 바인딩(PySide6→2 폴백) | `Framework/qt/qt.py` | `from Framework.qt.qt import *` (Maya 2023 → PySide2 자동 폴백) |
| **tsl 위젯(중복 제거 핵심)** | `Framework/qt/MOD_tsl_qt_v01.py` → `JUN_mod_tsl_qt` | `JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title=..., log_callback=...)`. Select/Add/Del/Up/Down/Sort + 씬 선택 동기화 + `get_all_items/set_items/append_unique/count` 내장 → 레거시 tsl 블록 + `CMD_ToolSel_b_*` 전부 대체 |
| 테마(qss) | `Framework/themes/theme_manager.py` | `ThemeManager.load_theme_to_widget(window, "blue_dark")` (레거시의 짙은 청색 팔레트와 근접) |
| DEV 리로드 | `JUN_All/dev/reloader_v02.py` | `reload_for_tool("tools.A00190_FKIK_General_Tool")` (자기 자신+Framework만, 타 툴 창 보존) |
| (선택) 저장 경로 | `Framework/core/path_manager.py` | JSON 기본 디렉터리 관리에 사용 가능. 단 파일 다이얼로그는 `cmds.fileDialog2` 유지 |

> 주의: `Framework/ui/MOD_*` 는 **maya.cmds 위젯**이라 Qt 툴에서 재사용 불가. 반드시 `Framework/qt/` 쪽을 쓴다.

---

## 5. 모듈별 설계

### 5.1 `app/core/matching.py`
- `match_two_objects(tgt_list, flw_list, rot_order=True, rot_axis=True, trs=True, rot=True)`
  — `JUN_MATCH_twoObjects` 이식(이름/동작 유지, bool 인자화).
- `class MatchData`: `tgt: list[str]`, `flw: list[str]` (구 `JUN_matcher_FKIK_Gen`). tsl 의존 제거 — 리스트로 직접 채운다.
- `class Checker` 대체 → UI 가 `[bool, bool, bool, bool]` 리스트를 직접 전달(별도 클래스 불필요).
- `run_match_bake(match_fk_pairs, match_ik_pairs, enabled_limbs, direction, frame_range=None)`
  — `JUN_cmd_bake_IK_FK_Gen` 재구현. `direction`(IK_TO_FK/FK_TO_IK), `frame_range=None` 이면 현재 프레임 단일 매칭,
  아니면 `(start, end)` 구간 베이크(+OGSFreeze). **`end+1` 로 마지막 프레임 포함** 버그 수정.
- `OGSFreeze` 컨텍스트 매니저 이식.

### 5.2 `app/core/driver_setup.py`
- `pin_to_surface(...)` — **pymel 유지**. Maya 2023 호환 확인(pointOnSurfaceInfo/fourByFourMatrix/decomposeMatrix/closestPointOnSurface 모두 2023 제공).
- `class Cage`(구 `JUN_cage_FKIK_Gen`): 팔/다리 L/R 드라이버 묶음 보관.
- `setup_triangle_drivers(fk_source_lists, cage)` — 구 `JUN_cmd_FKIK_gen_setup_triangle_pos_objs` (삼각형 메시 이름 오타 수정).
- `create_switch_drivers(fk_src, ik_src, fk_ctl, ik_ctl, ...)` — 구 `JUN_cmd_FKIK_gen_create_pos_objs_FKIK_Gen`.
- `create_loc_for_objs(objs)` — 구 `JUN_create_loc_for_given_objs`.

### 5.3 `app/core/selection_utils.py`
- `make_hierarchy_list`, `order_by_token`(← `is` → `in` 수정), `set_by_token`, `list_by_shapes`,
  `remove_duplicates`, `search_by_token`, `world_position`, `average_position`, `ensure_parent`.

### 5.4 `app/core/settings_io.py`
- `save_settings(data: dict[str, list[str]], path)` / `load_settings(path) -> dict` — JSON. 키는 tsl 이름이 아니라
  **논리 슬롯 id**(예: `"src_fk_arm_l"`). UI 가 슬롯 id ↔ 위젯 매핑 보유.
- 파일 다이얼로그는 `cmds.fileDialog2`(`*.json`) 유지.

### 5.5 `app/ui/limb_list_group.py`
- `class LimbListGroup(QWidget)`: 한 섹션의 4개 limb 리스트(arm L/R, leg L/R)를 `QGridLayout`(2×2) 또는
  가로 배치로 묶고, 각 칸은 `JUN_mod_tsl_qt_v01`. `get_lists() -> dict[str, list[str]]`, `set_lists(dict)` 제공.
- Source 탭은 LimbListGroup 2개(FK/IK), Match 탭은 limb×(pose,ctl) 이므로 limb당 2 리스트 묶음 → 전용 구성.

### 5.6 `app/ui/main_window.py`
- `WINDOW_OBJECT_NAME = "JUN_A00190_FKIK_General_window"`, `class MainWindow(QWidget)`.
- `QTabWidget` 3탭(Source / Match FK / Match IK) + 하단 Option(체크박스 4, Start/End `QSpinBox`,
  셋업 버튼 4, 실행 버튼 4) + 로그(`QPlainTextEdit`) + About 메뉴.
- 모든 버튼은 **시그널-슬롯**(`clicked.connect(self.on_xxx)`)으로 연결. 핸들러가 위젯→list 추출 후 core 호출.
- 메뉴: `Help > About` (`QMessageBox`, VERSION/LAST_UPDATE 표시).

### 5.7 `launch.py` / `config.py` / `__init__.py`
- `A00180_abSymMesh` 의 boilerplate 를 그대로 복제하고 툴 이름만 치환:
  - `__init__.py`: `from .launch import run`.
  - `launch.py`: ROOT sys.path 추가 → DEV시 `reload_for_tool("tools.A00190_FKIK_General_Tool")` →
    `WINDOW_OBJECT_NAME` 으로 기존 창 정리 → `MainWindow()` → `ThemeManager.load_theme_to_widget(win, "blue_dark")` → `show()`.
  - `config.py`: `DEV_MODE`, `install_shelf_button()`, `onMayaDroppedPythonFile()` (셸프 명령 `tools.A00190_FKIK_General_Tool.run(True)`).

---

## 6. 레거시 → 신규 매핑 요약

- tsl 블록 24개 + `CMD_ToolSel_b_add/del/up/down`, `JUN_cmd_FKIK_gen_toolSel_btn`, `JUN_cmd_tsl_select`
  → **`JUN_mod_tsl_qt` 위젯 내장 기능으로 전부 대체**(코드 대량 삭제).
- `JUN_cmd_bake_IK_FK_Gen`(tsl 이름 인자) → `run_match_bake`(list 인자).
- `JUN_matcher_FKIK`, `JUN_cmd_match_IK_and_FK`, `JUN_cmd_bake_IK_FK`, `JUN_cmd_bake_IK_to_FK` → **삭제**.
- `PY_JUN_makeUI_general_FKIKTool()` 자동 실행 → `run()` 진입점.
- 색상 상수(color_mainDark 등) → ThemeManager qss.

---

## 7. 구현 단계

1. **스캐폴딩**: `A00180_abSymMesh` 구조 복제 → 이름 치환(`__init__/launch/config/app/config/version`). 빈 `app/core`, `app/ui` 패키지 생성.
2. **core 이식(UI 무관, 먼저)**: `selection_utils` → `matching` → `driver_setup` → `settings_io` 순. 함수 시그니처를 `list[str]` 입출력으로. 버그 수정 반영.
3. **UI 구축**: `limb_list_group` → `main_window`(탭/옵션/버튼/로그). 핸들러에서 위젯↔list 변환 후 core 호출.
4. **배선**: 셋업·매칭·베이크·저장/로드 버튼 → 핸들러 → core. 체크박스/프레임 입력 반영.
5. **테마/마감**: `blue_dark` 적용, About, 로그 출력, 창 objectName 교체 동작 확인.
6. **문서화**: `JUN_All/docs/A00190_FKIK_General_Tool.md` 사용법 작성(설치/실행/탭별 기능/주의).

---

## 8. Maya 2023 호환 주의

- Qt 는 `Framework.qt.qt` 폴백으로 **PySide2** 사용 → PySide6 전용 API 금지(`exec()` 대신 `exec_()`,
  enum 정수 접근 등 기존 A00180 패턴 준수).
- pymel 은 Maya 2023 동봉 → `import pymel.core as pm` 사용 가능. `pin_to_surface` 의 노드는 2023 제공 확인됨.
- f-string(py3.9) OK. 본 툴은 커맨드 플러그인 미사용이라 `__file__` 이슈 없음.

---

## 9. 검증 방법

1. **설치**: `__dragDrop_A00190.py` 를 Maya 2023 뷰포트로 드래그&드롭 → 셸프 버튼 생성 확인.
2. **실행**: 셸프 버튼 또는 `import tools.A00190_FKIK_General_Tool as t; t.run(True)` → `blue_dark` 창,
   재실행 시 objectName 으로 중복 없이 교체되는지 확인.
3. **기능 E2E** (FK/IK 컨트롤이 있는 테스트 리그에서):
   - Source 탭에서 팔/다리 FK·IK 컨트롤을 각 리스트에 Add.
   - "Set up triangle drivers" / "Drivers for FK IK switch" → 드라이버/포즈 오브젝트 생성, Match 탭 리스트 자동 채움 확인.
   - 체크박스로 대상 limb 선택, Start/End Frame 설정.
   - **Match IK / Match FK**(단일 프레임), **Bake IK / Bake FK**(구간) 실행 → 컨트롤이 반대 솔버 포즈로 스냅/키되는지,
     **마지막 프레임까지** 키가 찍히는지 확인.
   - **Save setting → 새 씬/재실행 → Load setting** 으로 리스트 복원 확인.
4. core 단위 점검: `match_two_objects`, `order_by_token`(중복/토큰 정렬) 을 간단 스크립트로 호출해 회귀 확인.

---

## 10. 리스크 / 메모

- **드라이버 셋업 로직 복잡도**: 삼각형/locator 드라이버 생성부는 씬 상태 의존이 커 리팩토링 시 동작 보존이 까다롭다.
  → 1차로 함수 동작을 그대로 옮기고(이름만 정리), 검증 후 점진적으로 다듬는다.
- **베이크 마지막 프레임 수정**은 동작 변화이므로 사용자 확인 후 적용(원본 의도가 end 제외였는지 점검).
- **세팅 JSON 호환**: 키를 tsl 이름 → 논리 슬롯 id 로 바꾸면 기존 저장 파일과 비호환. 신규 포맷으로 진행(기존 파일 마이그레이션 불필요 가정).
- UI 텍스트/로그는 **영어**, 주석/문서는 한국어(프로젝트 관례).
```
