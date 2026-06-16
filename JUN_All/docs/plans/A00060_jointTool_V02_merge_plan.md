# A00060_jointTool_V02 — MEL JointTool V05.03 + A00060 병합 계획서 (PySide 포팅)

## Context (배경 / 목적)

두 개의 조인트 툴을 하나로 병합한다.

| 소스 | 위치 | 형태 |
|------|------|------|
| **MEL `JointTool V05.03`** | `~/Documents/maya/2024/scripts/JUN_MEL_JointTool_V05_03.mel` | `tabLayout` 3탭(`Curve` / `Divide` / `Aim`), 모든 로직이 `global proc` |
| **Python `A00060_jointTool`** | `JUN_All/tools/A00060_jointTool` (V02.05) | 탭 없는 단일 윈도우, Framework 위젯, 헤어 커브용 조인트 유틸 |

**목표**: 새 경로 **`JUN_All/tools/A00060_jointTool_V02`** 에 병합 툴을 만든다.

요구 사항(확정):
1. MEL 의 **3탭 UI(`Curve` / `Divide` / `Aim`)를 그대로 보존**한다(레이아웃·기능 동일).
2. 기존 `A00060_jointTool` 의 기능을 **새 탭 `Hair`** 로 추가한다(총 4탭).
3. **MEL 로직은 전체 Python 포팅**한다 — `global proc` → `maya.cmds` Python 함수.
4. **UI 는 PySide(Qt)로 구성**한다 — `maya.cmds` UI 가 아니라 `QTabWidget` 기반.
5. **`Hair` 탭은 나머지 탭과 동일한 Qt 스타일**로 통일한다(MEL 탭 스타일에 맞춤).

> 즉 결과물은 `CLAUDE.md` 의 **아키텍처 (B) — Maya 내 PySide 툴**(템플릿 `A00008_base_QT_maya`)
> 형태가 된다. 기존 `A00060_jointTool`(아키텍처 (A) maya.cmds)은 **건드리지 않고 그대로 둔다**(레퍼런스 보존).

---

## 1. 기준 레퍼런스 — `A00110_animTool`

`A00110_animTool` 이 **정확히 같은 부류**(Maya 내 PySide + `maya.cmds` 로직 + `QTabWidget` + dragDrop 설치)이므로
이 툴을 구조 템플릿으로 삼는다. 핵심 차용 패턴:

- `launch.py` `run(reload_module=True)` — `DEV_MODE` 면 `dev.reloader_v02.reload_for_tool("tools.A00060_jointTool_V02")` 후 실행.
- `main_window.py` — `from Framework.qt.qt import *`, `QTabWidget`, 탭별 `_build_*_tab()` 메서드, **공유 로그창**, `Help > About` 메뉴바, 재실행 정리용 고유 `WINDOW_OBJECT_NAME`.
- `app/core/*` — UI 비의존 `maya.cmds` 로직(매니저).
- `app/config/version.py` — `VERSION` / `LAST_UPDATE`.
- `__dragDrop_A00060_V02.py` — 셸프 버튼 설치(고유 파일명 + `sys.modules.pop(__name__)`).

### 재사용 위젯 — `JUN_mod_tsl_qt_v01` (핵심)

`Framework/qt/MOD_tsl_qt_v01.py` 의 `JUN_mod_tsl_qt_v01`(별칭 `Framework.qt.JUN_mod_tsl_qt`)이
MEL 탭이 반복 사용하는 **textScrollList + Select/Add/Del/Up/Down** 패턴을 **그대로 대체**한다.

| MEL proc | `JUN_mod_tsl_qt_v01` 대응 |
|----------|---------------------------|
| `JUN_cmd_Clear_And_Select` (Select 버튼) | `show_select` 버튼 → `_on_select` (현재 선택으로 교체) |
| `JUN_cmd_append_selected` (Add) | `_on_add` (`append_unique`) |
| `JUN_cmd_delete_selected` (Delete) | `_on_del` |
| `JUN_cmd_selMov` up/down | `_on_up` / `_on_down` |
| `JUN_cmd_tsl_select` (항목 클릭 → 씬 선택) | `_on_selection_changed` 내장 |
| `textScrollList -q -allItems` | `get_all_items()` |
| `JUN_cmd_select_updateTex` (Number 라벨 갱신) | 내장 `Number: N` 라벨 자동 갱신 |

→ 즉 **MEL 의 TSL/리스트 인프라 proc 군은 새로 만들 필요가 거의 없다.** 위젯 인스턴스만 배치.
다만 MEL 의 **`Select Start End` / `Add Start End`**(선택 순서로 시작/끝 리스트를 쌍 구성)는
위젯 표준 버튼이 아니므로 **탭 단위 커스텀 버튼**으로 추가한다(`add_button()` 또는 탭 하단 별도 버튼).

---

## 2. 디렉터리 / 파일 구조 (신규)

```
JUN_All/tools/A00060_jointTool_V02/
├── __init__.py                         # from .launch import run  (run 만 노출)
├── launch.py                           # run(reload_module=True): reload_for_tool → MainWindow → 테마 → show
├── __dragDrop_A00060_V02.py            # 셸프 버튼 설치 (고유 파일명, A00110 패턴)
├── requirements.txt                    # (Maya 내장 PySide; 참고용)
└── app/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── version.py                  # VERSION = "01.00", LAST_UPDATE
    ├── core/                           # ── UI 비의존 maya.cmds 로직 (MEL 포팅 + A00060 이식) ──
    │   ├── __init__.py                 # 매니저 export
    │   ├── tsl_ops.py                  # (선택) 공통 헬퍼 — reversed array 등, 대부분 위젯이 흡수
    │   ├── curve_joint_manager.py      # [Curve 탭] joints_to_curve / clusters_to_curve / point-type
    │   ├── obj_joint_manager.py        # [Curve 탭] joints_to_obj(축 옵션) / set_orient / swap_orient_rotate
    │   ├── divide_manager.py           # [Divide 탭] make_joints_divided (curve rebuild → ep joints)
    │   ├── aim_manager.py              # [Aim 탭]    make_joint_aim (ikHandle + poleVectorConstraint)
    │   └── hair_manager.py             # [Hair 탭]   A00060 utility.py 이식 (separate/remove/rebuild/reverse/unused)
    └── ui/
        ├── __init__.py
        └── main_window.py             # QTabWidget(Curve/Divide/Aim/Hair) + 공유 로그 + Help>About
```

`A00060_jointTool`(원본)은 **수정/삭제하지 않는다.**

---

## 3. MEL → Python 포팅 매핑 (core)

각 `global proc` 를 어느 매니저 함수로 옮기는지의 1:1 표. **순수 로직만** 옮기고
(textScrollList 질의·라디오·옵션메뉴 읽기 같은) UI 접근은 `main_window.py` 에서 값으로 전달한다.

### 3.1 `curve_joint_manager.py` (Curve 탭 — Joint to Crv)

| MEL proc | Python 함수 | 비고 |
|----------|-------------|------|
| `get_list_numCVPoints_fromCurve` | `cv_indices_of_curve(curve)` | `.spans + 3` |
| `JUN_get_pointType_from_vct` / `JUN_get_vct_from_rb` | UI 가 enum 문자열로 전달 | 라디오 3종: `controlPointsOmit` / `controlPoints` / `ep` |
| `JUN_make_jnt_toCurvePoint` | `_joint_at_curve_point(curve, idx, pointType)` | `pointPosition` + `xform` 보정 |
| `make_jnts_toCurvePoint` | `joints_along_curve(curve, pointType, indices)` | 끝에서 `oj none` 로 월드 정렬 |
| `JUN_cmd_create_joints_toCrv` | `joints_to_curves(curves, pointType)` | nurbsCurve 검증 + omit/ep 인덱스 처리 |
| `JUN_cmd_create_clusters_toCrv` | `clusters_to_curves(curves)` | CV별 cluster |

### 3.2 `obj_joint_manager.py` (Curve 탭 — Joint to Obj / Orient)

| MEL proc | Python 함수 | 비고 |
|----------|-------------|------|
| `JUN_make_jnt_toObj` | `_joint_at_obj(obj)` | translate 위치에 joint |
| `JUN_cmd_create_joints_toObj` | `joints_to_objs(objs, separate, fwd_axis, secd_axis, secd_ori)` | **축 인덱스 계산 로직 정밀 이식**(아래 주의) |
| `JUN_cmd_joint_swap_rotate` | `swap_rotate_orient(joints, src_attr, dst_attr)` | `jointOrient`↔`rotate` 합산 스왑 |
| `JUN_cmd_set_jntOri` | `set_joint_orient(joints, axis, degree)` | **체인 unparent→setAttr→reparent** 순서 이식(아래 주의) |

### 3.3 `divide_manager.py` (Divide 탭)

| MEL proc | Python 함수 | 비고 |
|----------|-------------|------|
| `JUN_get_curve` / `JUN_get_curves_strEnd` | `_curve_between(posA, posB)` / `curves_from_pairs(starts, ends)` | degree1 2점 커브 |
| `JUN_rebuild_crv` / `JUN_rebuildCurves_spans` | `rebuild_span(curve, n)` | degree 3, span = numDiv-1 |
| `JUN_cmd_makeJnt_divide` | `make_joints_divided(starts, ends, num_div)` | size 검증 + `ep` joints |
| `JUN_cmd_selStrEnd` / `JUN_cmd_addStrEnd` | (UI 헬퍼) `pairs_from_selection(sel)` / 2개 검증 | 시작/끝 리스트 쌍 구성 |

### 3.4 `aim_manager.py` (Aim 탭)

| MEL proc | Python 함수 | 비고 |
|----------|-------------|------|
| `JUN_cmd_make_jntAim` | `make_joint_aim(starts, ends, pole_tgts)` | `ikHandle(sj,ee)` + `poleVectorConstraint` 쌍 루프 |

### 3.5 `hair_manager.py` (Hair 탭 — A00060 이식)

`A00060_jointTool/utility.py` 는 **이미 Python**이다. 함수 본체는 그대로 가져오되,
`kwargs` 로 받던 `tsl`/`tfg`/`cbg` **위젯 의존을 제거**하고 **평범한 인자(list/float/bool)** 로 바꾼다.

| A00060 utility | Python 함수(이식) | 시그니처 변경 |
|----------------|-------------------|----------------|
| `JUN_separate_crv` | `separate_curves(curves)` | tsl → `curves: list` |
| `JUN_remove_crv_by_len` / `rebuild_curves_by_length` | `remove_curves_by_length(curves, max_len)` | tsl/tfg → 값 |
| `JUN_rebuild_crv` | `rebuild_curves_by_interval(curves, interval, max_jnts)` | tsl/tfg → 값 |
| `JUN_reverse_joint` / `reverse_joint_chain` / `search_replace_names` | `reverse_joints(roots, remove_origin)` 등 | tsl/cbg → 값 |
| `select_unused_joints` / `get_unused_joints` | `unused_joints(joints)` (리스트 반환) | 선택은 UI 가 수행 |

> UI(`main_window.py`)가 위젯에서 값을 읽어 매니저에 넘기고, 반환된 결과로 리스트 선택/로그를 갱신한다.
> → `app/core` 와 `app/ui` 분리 원칙 유지(`CLAUDE.md` 9장).

---

## 4. UI 구성 (`app/ui/main_window.py`)

`A00110_animTool/main_window.py` 골격을 그대로 따른다.

```
MainWindow(QWidget)  objectName = "JUN_A00060_jointTool_V02_window"
├─ QMenuBar : Help > About
├─ QTabWidget
│   ├─ Curve  탭  : _build_curve_tab()
│   ├─ Divide 탭  : _build_divide_tab()
│   ├─ Aim    탭  : _build_aim_tab()
│   └─ Hair   탭  : _build_hair_tab()
└─ QTextEdit(read-only) : 공유 로그창 (탭 생성보다 먼저 만든다 — A00110 패턴)
```

### 4.1 위젯 매핑 (maya.cmds → Qt)

| MEL UI | Qt 위젯 |
|--------|---------|
| `textScrollList` + Add/Del/Up/Down/Select | `JUN_mod_tsl_qt_v01` |
| `radioCollection` + `radioButton` (point type, match type) | `QButtonGroup` + `QRadioButton` |
| `optionMenuGrp` (foward/secondary/orient axis) | `QComboBox` |
| `floatFieldGrp` (orient degree) | `QDoubleSpinBox` |
| `intFieldGrp` (joints number) | `QSpinBox` |
| `paneLayout vertical2/3` (Divide/Aim 좌우 분할) | `QHBoxLayout` (tsl 위젯 N개 나란히) |
| `frameLayout -collapsable` | `QGroupBox` (또는 접이식이 필요하면 collapsible 박스) |
| `button -bgc` | `QPushButton` (색은 테마 qss 로) |

### 4.2 탭별 구성 요약

- **Curve 탭**: `tsl_curve`(Select/Add/Del/Up/Down) + 그룹3:
  ① Joint to Crv(라디오 3 + `Joints to Crv`/`Clusters` 버튼)
  ② Joint to Obj(Connect/Separate 라디오 + Foward/Secondary/SecondaryOrient 콤보 + `Match to Obj`)
  ③ Orient/Rotate(`joint orient→rotate` / `rotate→joint orient` 스왑 + Set Orient 콤보·스핀 + 버튼)
- **Divide 탭**: `tsl_start` + `tsl_end`(좌우) + `Select Start End`/`Add Start End`(커스텀) + `Joints Number` 스핀 + `Make Joint Divided`.
- **Aim 탭**: `tsl_aimStart` + `tsl_aimEnd` + `tsl_poleTgt`(3분할) + `Select/Add Start End` + `Make Joint Aim`.
- **Hair 탭**: `tsl_hair` + Sub:Curve(Separate / Max Length+Remove / Interval+Max joints+Rebuild) + Edit(Remove origin 체크 + Reverse joint chain / Select Unused Joints).

### 4.3 테마 / 색상

- `launch.py` 에서 `ThemeManager.load_theme_to_widget(window, "coral_dark")`(A00110 과 동일 계열) 적용.
- MEL 의 초록 `Select` 버튼/회색 frame `bgc` 같은 인라인 색은 **qss 테마로 대체**(개별 위젯 인라인 색 지양).
- `JUN_mod_tsl_qt_v01(log_callback=self.log)` 로 위젯 메시지를 공유 로그창에 연결.

---

## 5. 진입점 / 설치 (launch · dragDrop · init)

- `__init__.py` : `from .launch import run` / `__all__ = ["run"]`.
- `launch.py` : A00110 `run()` 복제 — 패키지명만 `tools.A00060_jointTool_V02` 로, `objectName` 으로 기존 창 정리.
- `__dragDrop_A00060_V02.py` : A00110 dragDrop 복제 —
  - `TOOL_LABEL = "JointTool2"`, `SHELF_COMMAND` 가 `tools.A00060_jointTool_V02.run(True)` 호출.
  - **고유 파일명 + 끝에서 `sys.modules.pop(__name__, None)`**(드롭 캐시 충돌 방지, `CLAUDE.md` 3장 규칙).
- DEV reload : `dev/reload_path_list.py` 의 `RELOAD_PACKAGES` 에 신규 패키지 등록 여부 확인.

> **주의 — 원본 A00060 의 카피 버그**: 기존 `A00060_jointTool/config.py`·`__dragDrop_A00060.py` 는
> `TOOL_PATH`/중복검사 문자열이 `A00040_file_exporter` 로 남아 있다(카피 흔적). **V02 에는 그대로 옮기지 말 것** —
> 모든 식별자를 `A00060_jointTool_V02` 로 일관되게 작성한다.

---

## 6. 포팅 시 정밀 주의 포인트 (버그 유발 구간)

1. **`joints_to_objs` 축 인덱스 계산** (`JUN_cmd_create_joints_toObj`):
   `lastAxis = 3 - (fwd + secd - 2)`, `flag_oriJnt = axis[fwd-1]+axis[secd-1]+axis[last]`,
   `flag_secdAxisOri = axis[ceil(secdOri/2)-1] + ["down","up"][secdOri%2]`.
   콤보 인덱스(0-base)와 MEL 1-base 차이를 **테이블로 명시 이식**하고 케이스 검증.
2. **`set_joint_orient`** (`JUN_cmd_set_jntOri`): 체인을 **역순 unparent → `jointOrient<Axis>` set → 다시 정순 reparent**.
   순서가 틀리면 트랜스폼이 깨진다. `catch(eval(...))` 는 `try/except` 로.
3. **`joints_along_curve`** 끝의 `joint -e -oj none -ch -zso` (월드 정렬) 누락 금지.
4. **`controlPointsOmit`** 처리: pointType 을 `controlPoints` 로 바꾸고 인덱스 `[1, last-1]` 제거 — 인덱스 산술 그대로.
5. **PySide2/PySide6 양립**: 반드시 `from Framework.qt.qt import *` 만 사용(직접 PySideN import 금지).
   `QAbstractItemView`·enum 접근이 버전마다 다를 수 있어 위젯 재사용으로 회피.
6. **Maya 2023 호환**(메모리): native sin/cos 노드 미사용 로직이므로 영향 없음. 확인만.
7. **UI 텍스트 영어 고정**(메모리): 버튼/라벨/로그 문자열 전부 영어, 한국어는 주석/독스트링만.

---

## 7. 작업 순서 (제안)

1. `A00008_base_QT_maya`(또는 `A00110_animTool`) 복제 → `A00060_jointTool_V02` 골격 + `version.py` `01.00`.
2. `core/hair_manager.py` 먼저 이식(이미 Python이라 가장 쉬움) → Hair 탭 + 위젯으로 **동작 1탭 검증**.
3. `core/curve_joint_manager.py` + `obj_joint_manager.py` 포팅 → Curve 탭.
4. `core/divide_manager.py` → Divide 탭, `core/aim_manager.py` → Aim 탭.
5. 공유 로그/테마/About/`Select Start End` 커스텀 버튼 마무리.
6. `__dragDrop_A00060_V02.py` + `__init__`/`launch` 진입점, reload 목록 등록.
7. Maya 에서 드롭 설치 → 4탭 각 기능 수동 검증(곡선→조인트, divide, aim, hair).
8. `docs/A00060_jointTool_V02.md`(사용법) 작성, `CHANGELOG`/version 갱신.

---

## 8. 산출물

- `JUN_All/tools/A00060_jointTool_V02/` (위 2장 트리 전체)
- `JUN_All/docs/A00060_jointTool_V02.md` (탭별 사용법 — 후속)
- 원본 `A00060_jointTool` / MEL 파일은 **무수정 보존**

## 9. 미해결 / 확인 필요

- `frameLayout -collapsable` 접이식을 Qt 에서 그대로 재현할지(접이식 `QGroupBox`) vs 단순 `QGroupBox` 로 둘지 — 기본은 단순 `QGroupBox`, 필요 시 접이 위젯 추가.
- 셸프 라벨/아이콘 명칭(`JointTool2` 잠정).
- 창 기본 크기(MEL 480×900 → Qt 에서 탭 4개 기준 재산정).
