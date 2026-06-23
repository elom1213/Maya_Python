---
title: 카테고리별 테마(qss) 통일 작업 계획서
aliases: [theme-unification, qss-category, 테마통일]
tags: [plan, framework, theme, qss]
updated: 2026-06-23
---

# 카테고리별 테마(qss) 통일 작업 계획서

## 1. 목적 / 배경

현재 각 Qt 툴은 `Framework/themes/theme_manager.py` 를 통해 `Framework/styles/<color>.qss` 를
개별적으로 지정한다. 같은 도메인(리깅·애니메이션 등)의 툴들이 서로 다른 색을 써서 **창 색만 보고
툴 카테고리를 구분하기 어렵다**.

이 작업의 목표는 **"비슷한 카테고리의 툴은 같은 qss 색을 쓰도록"** 각 툴 진입점(`launch.py`)의
테마 색상 인자(`theme_name`)를 카테고리 기준으로 통일하는 것이다.

> 한 줄 요약: **각 `launch.py` 의 `ThemeManager.load_theme_*(..., "<color>")` 의 색 문자열을
> 카테고리 표준 색으로 맞춘다.** 코드 로직 변경 없음, 문자열 한 개씩 교체.

---

## 2. 현황 분석

### 2-1. 테마 적용 메커니즘

`ThemeManager` 에는 색 인자(`theme_name`)를 받아 `Framework/styles/{theme_name}.qss` 를
적용하는 메서드가 3종 있고, **세 메서드 모두 색 인자는 `theme_name` 하나뿐**이라 편집 방식이 동일하다.

| 메서드 | 적용 대상 | 사용처 |
|--------|-----------|--------|
| `load_theme_dev(app, theme_name)` | `QApplication` 전체 | standalone(exe) 툴 |
| `load_theme_to_widget(widget, theme_name)` | 특정 위젯(창) | Maya 내 PySide 툴 |
| `load_theme(app, theme_name)` | `QApplication` 전체 | 템플릿(A00004) |

> 사용자가 말한 "`load_theme_dev` 의 색 인자"는 실제로는 위 3종 호출 전부의 `theme_name` 을 가리킨다.
> 편집은 전부 **`launch.py` 한 줄의 색 문자열 교체**로 동일하다.

### 2-2. 사용 가능한 qss (`Framework/styles/`)

```
dark, red,
blue_dark / blue_light, brown_dark / brown_light, coral_dark / coral_light,
green_dark / green_light, purple_dark / purple_light, yellow_dark / yellow_light
```
- 대부분 `*_dark` / `*_light` 쌍. 예외: `dark`(중립), `red`(단일, dark 계열만 존재).

### 2-3. 작업 대상 / 비대상

**대상 = ThemeManager qss 를 쓰는 Qt 툴 21개.** 비대상은 아래와 같이 분리한다.

| 구분 | 툴 | 이유 |
|------|----|------|
| **비대상 (arch A, maya.cmds)** | A00000_base, A00010_humanIKTool, A00020_move_skineWeightTool, A00030_quickTool, A00040_file_exporter, A00050_uvTool, A00060_jointTool, A00070_KWI_creator | qss 가 아니라 `MOD_colorThem.ColorThemeRegistry`(버튼색) 시스템 사용. **별도 작업**(아래 9장) |
| **비대상 (테마 호출 없음)** | A00100_jsonEditor_MH(미완), A00200_CSV_tool(단일파일·무테마), A00230_StartupTool(설치 스크립트, UI 아님) | 적용할 `ThemeManager` 호출 자체가 없음 |

### 2-4. 현재 테마 인벤토리 (대상 21개)

| 툴 | 현재 색 | 호출 메서드 | launch.py 위치 |
|----|---------|-------------|----------------|
| A00004_base_QT | dark | load_theme | :25 |
| A00008_base_QT_maya | red | load_theme_to_widget | :44 |
| A00010_humanIKTool_V02 | blue_dark | load_theme_to_widget | :57 |
| A00060_jointTool_V02 | coral_dark | load_theme_to_widget | :59 |
| A00080_KWI_creator_V02 | dark | load_theme_dev | :27 |
| A00090_ConnectionBuilder | red | load_theme_to_widget | :48 |
| A00110_animTool | coral_dark | load_theme_to_widget | :62 |
| A00120_FKIK | red | load_theme_to_widget | :53 |
| A00130_ControlRig | red | load_theme_to_widget | :52 |
| A00140_ConnectClosest | red | load_theme_to_widget | :52 |
| A00145_RigConnect | coral_dark | load_theme_to_widget | :60 |
| A00150_remapVal | yellow_dark | load_theme_to_widget | :52 |
| A00160_sphericalEye | green_dark | load_theme_to_widget | :52 |
| A00170_driverTool | yellow_dark | load_theme_to_widget | :61 |
| A00180_abSymMesh | yellow_dark | load_theme_to_widget | :62 |
| A00190_FKIK_General_Tool | blue_dark | load_theme_to_widget | :55 |
| A00210_FileManager | blue_dark | load_theme_dev | :35 |
| A00211_RefLineage | blue_dark | load_theme_to_widget | :55 |
| A00220_BackupTool | green_dark | load_theme_dev | :35 |
| A00240_PathTool | purple_dark | load_theme_dev | :35 |
| A00250_SceneMemo | coral_dark | load_theme_to_widget | :56 |

---

## 3. 카테고리 정의 (도메인 기준)

`CLAUDE.md` 도메인 + 각 툴 docs 개요로 확정한 분류.

| 카테고리 | 툴 |
|----------|----|
| **Rigging (리깅)** | A00060_jointTool_V02, A00120_FKIK, A00130_ControlRig, A00140_ConnectClosest, A00145_RigConnect, A00150_remapVal, A00160_sphericalEye, A00170_driverTool, A00190_FKIK_General_Tool |
| **Animation (애니메이션)** | A00010_humanIKTool_V02, A00110_animTool |
| **Modeling (모델링)** | A00180_abSymMesh |
| **Facial (페이셜)** | A00090_ConnectionBuilder |
| **UE / Physics (언리얼·물리)** | A00080_KWI_creator_V02 |
| **Pipeline / Utility (파이프라인·유틸)** | A00210_FileManager, A00211_RefLineage, A00220_BackupTool, A00240_PathTool, A00250_SceneMemo |
| **Template (템플릿)** | A00004_base_QT, A00008_base_QT_maya |

---

## 4. 카테고리 → qss 매핑 (★ 확정 필요 — 결정 포인트)

각 카테고리에 **시각적으로 구분되는 단일 색**을 배정한다. 아래는 *권장안*(변경 최소화 + 색 충돌 없음 기준).
**색 ↔ 카테고리 배정은 취향 결정 사항**이므로, 확정/수정 후 5장 변경 목록을 그대로 적용하면 된다.

| 카테고리 | 권장 qss | 근거 |
|----------|----------|------|
| Rigging | **coral_dark** | 최대 그룹(9개), 이미 jointTool/RigConnect 가 사용 중 |
| Animation | **blue_dark** | humanIK 가 이미 사용 |
| Modeling | **yellow_dark** | abSymMesh 가 이미 사용 |
| Facial | **red** | 단일·주목색, ConnectionBuilder 가 이미 사용 |
| UE / Physics | **purple_dark** | 다른 카테고리와 미충돌 |
| Pipeline / Utility | **green_dark** | BackupTool 가 이미 사용 |
| Template | **dark** | 중립 baseline(템플릿임을 표시) |

> 7색 모두 `Framework/styles/` 에 존재. 충돌 없음(coral/blue/yellow/red/purple/green/dark).

---

## 5. 툴별 변경 목록 (권장안 적용 시)

`launch.py` 의 색 문자열만 교체. **변경 14건 / 유지 7건.**

### Rigging → `coral_dark`
| 툴 | 변경 |
|----|------|
| A00120_FKIK | `red` → `coral_dark` |
| A00130_ControlRig | `red` → `coral_dark` |
| A00140_ConnectClosest | `red` → `coral_dark` |
| A00150_remapVal | `yellow_dark` → `coral_dark` |
| A00160_sphericalEye | `green_dark` → `coral_dark` |
| A00170_driverTool | `yellow_dark` → `coral_dark` |
| A00190_FKIK_General_Tool | `blue_dark` → `coral_dark` |
| A00060_jointTool_V02 | (유지) coral_dark |
| A00145_RigConnect | (유지) coral_dark |

### Animation → `blue_dark`
| A00110_animTool | `coral_dark` → `blue_dark` |
| A00010_humanIKTool_V02 | (유지) blue_dark |

### Modeling → `yellow_dark`
| A00180_abSymMesh | (유지) yellow_dark |

### Facial → `red`
| A00090_ConnectionBuilder | (유지) red |

### UE / Physics → `purple_dark`
| A00080_KWI_creator_V02 | `dark` → `purple_dark` |

### Pipeline / Utility → `green_dark`
| A00210_FileManager | `blue_dark` → `green_dark` |
| A00211_RefLineage | `blue_dark` → `green_dark` |
| A00240_PathTool | `purple_dark` → `green_dark` |
| A00250_SceneMemo | `coral_dark` → `green_dark` |
| A00220_BackupTool | (유지) green_dark |

### Template → `dark`
| A00008_base_QT_maya | `red` → `dark` (선택적, 후순위) |
| A00004_base_QT | (유지) dark |

---

## 6. 작업 절차

1. **(결정)** 4장 카테고리→색 매핑 확정(또는 수정).
2. **편집**: 각 대상 `launch.py` 에서 `ThemeManager.load_theme_*(..., "<old>")` 의 색 문자열만 교체.
   로직/임포트/시그니처 변경 없음.
3. **검증**(7장).
4. **문서/버전**: 색이 바뀐 각 툴의 `app/config/version.py` 패치 버전 올림(+ 해당 툴 docs 의
   "테마" 언급이 있으면 갱신). `JUN_All/docs/WORKLOG.md` 에 통일 작업 1건 요약.
5. **커밋/푸시**: `Dnable_repo/dev`. (변경 툴이 많으므로 카테고리 단위 커밋 또는 단일 커밋)

---

## 7. 검증 방법

- **정적**: 변경한 모든 `launch.py` `py_compile` 통과. 지정한 `<color>.qss` 가
  `Framework/styles/` 에 실제 존재하는지 확인(오타 시 `FileNotFoundError`).
- **동적(권장)**: 카테고리별 대표 툴 1개씩 Maya/standalone 에서 실행해 창 색 확인
  (예: 리깅=coral, 애니=blue, 유틸=green). 같은 카테고리 두 툴을 나란히 띄워 색 일치 육안 확인.

---

## 8. 리스크 / 주의

- **`red` 는 dark 변형이 없다**(단일 `red.qss`). Facial 에 `red` 유지는 문제없으나, 만약 Facial 을
  다른 색으로 바꾸려면 `*_dark` 중 미사용 색을 골라야 한다.
- 호출 메서드가 3종(`load_theme_dev`/`load_theme_to_widget`/`load_theme`)이지만 **색 인자는 모두
  동일**하므로 메서드는 그대로 두고 문자열만 바꾼다(메서드 교체 금지).
- standalone 툴(A00080/A00210/A00220/A00240)은 `load_theme_dev` 라 **앱 전체** qss. exe 빌드 시에도
  `Framework/styles` 가 동봉되는지(spec) 확인 — 본 작업은 색만 바꾸므로 빌드 구성에는 영향 없음.
- **색 = 카테고리 약속**이므로, 신규 툴 추가 시 이 표를 따르도록 `CLAUDE.md`/템플릿에 메모를 남기는 것을
  후속으로 고려(11장).

---

## 9. 범위 외 (arch A / maya.cmds 툴)

A00000/10/20/30/40/50/60/70 은 qss 가 아니라 `ColorThemeRegistry.get("coral_01")` 식 **버튼 색**을
쓴다. 카테고리 색 통일을 여기까지 확장하려면 **별도 작업**이 필요하다(버튼 스펙의 색 키를 카테고리
표준으로 교체). 본 계획서 범위에 포함하지 않으며, 필요 시 후속 계획서로 분리한다.

---

## 10. 영향 요약

- **수정 파일**: 대상 `launch.py` 14개(+ 각 `version.py`), `WORKLOG.md`, (해당 시) 각 툴 docs.
- **코드 동작 변경 없음**: UI 색만 변경. 기능/로직/단축키/Undo 등 무관.
- **롤백 용이**: 각 줄 문자열 1개 되돌리면 원복.

---

## 11. 후속 제안 (선택)

- `CLAUDE.md` "컨벤션" 절에 **카테고리↔테마색 표준**을 명문화해, 신규 Qt 툴(A00004 복제 시)이 자동으로
  올바른 색을 쓰도록 안내.
- arch A(maya.cmds) 툴의 버튼색도 같은 카테고리 색으로 맞추는 후속 계획서.
