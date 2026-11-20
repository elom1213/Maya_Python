---
title: A00630_MotionPathEditor — 편집 가능한 모션 경로 (마야) 계획서
aliases: [A00630, MotionPathEditor, Editable Motion Paths 마야판, 모션 경로 편집, motion trail 대체]
tags: [plan, maya-python, animation, motion-path, motion-trail, viewport-draw, A00630]
updated: 2026-11-19
---

# A00630_MotionPathEditor — 편집 가능한 모션 경로 (마야) 계획서

> 작성 2026-11-19 · 상태: **0단계 실측 완료 · 1단계 구현 완료 (v01.00, 2026-11-19, mayapy 시험 106항목) · 마야 GUI 확인 전** · 결정 Q1~Q5 = 전부 추천대로(§9) · 아키텍처 (B) Maya 내 PySide 툴 + 파이썬 플러그인(뷰포트 그리기 노드 · undo 명령)
>
> 참고 원본 (읽기 전용, 저장소 밖): `D:\D__1020_Blender_PlugIn\0010_Editable_Motion_Paths` — 블렌더 애드온
> *Editable Motion Paths* v2.0.7 (블렌더 4.4+, 파이썬 약 31,000줄). 아래 분석은 그 `README.md` · `DEV_GUIDE.md` · `docs/MANUAL.md` ·
> `editable_motion_paths/core.py` · `edit.py` 를 직접 읽고 썼다.
>
> 요청 (2026-11-19):
> - 이 블렌더 툴을 **마야의 새 툴**로 만든다.
> - 마야의 **Create Editable Motion Trail** 같은 기존 기능보다 **훨씬 빨라야** 한다.
> - **우선순위**: 프레임별 오브젝트 위치를 잇는 커브 표시와, 그 커브를 고쳐 애니메이션을 고치는 기능. 나머지 기능은 천천히(최종 목표는 전부).

---

## 0. 요약

- **무엇을 만드나**: 고른 오브젝트 · 조인트의 **프레임별 월드 위치를 잇는 경로**를 뷰포트에 그리고, 경로 위의 **키 점을 드래그하면 그 키 값이 바뀌어**
  애니메이션이 고쳐진다. 그래프 에디터를 열지 않고 궤적 모양으로 애니메이션을 고치는 툴이다.
- **왜 빠른가** — 원본의 핵심 설계를 그대로 따른다(§2):
  - 경로 = `부모 공간(f)` × `자기 채널(f)`. **부모 공간만** 프레임을 돌며 한 번 구워 두고, **자기 채널(translate 커브)은 애님 커브를 직접 평가**한다.
  - 그래서 키를 움직여도 **프레임을 다시 돌지 않는다**: 드래그 한 번 = 파이썬 행렬 계산 몇 번. 마야 Motion Trail 은 바뀔 때마다 씬을 프레임별로 다시 평가한다.
  - 굽는 것도 **부모 행렬 plug 하나만** 시간 문맥으로 평가해, 스킨 메시 같은 무거운 노드는 계산하지 않는다(§4-3, 0단계에서 실측으로 고른다).
- **구성**: PySide 툴 창 + 파이썬 플러그인 하나(① 경로를 그리는 locator 노드 + VP2 draw override, ② 키 편집을 한 번의 undo 로 묶는 명령) +
  드래그를 직접 처리하는 마야 컨텍스트(`draggerContext`).
- **씬에 남기지 않는다**: 그리기 노드는 저장되지 않게(`doNotWrite`) 만들고, 바꾸는 것은 **평범한 애님 커브 키 값뿐**이다 → 이 툴 없이도 파일이 그대로 열린다(원본의 원칙 1).
- **라이선스**: 원본은 **GPL-3.0-or-later**. 코드를 옮기면 이 저장소 결과물도 GPL 이 되어야 한다 → **아이디어와 공개 문서만 참고하는 독자 구현**(코드 복사 없음, §1).
- **단계**: 0단계 실측 → **1단계 위치 경로 표시 + 키 드래그(핵심)** → 1.5단계 프레임 드래그 · 비례 편집 → 2단계 탄젠트 핸들 · 자동 갱신 → 3단계 회전 경로 · 공간 → 4단계 이후 원본의 나머지 기능.

---

## 1. 라이선스와 구현 방침 (먼저 정할 것)

- 원본 `LICENSE` / `blender_manifest.toml`: `license = ["SPDX:GPL-3.0-or-later"]`. README 도 "GPL-3.0-or-later, like Blender" (아이콘만 CC0).
- GPL 코드를 이 저장소에 옮기거나 번역해 넣으면 그 툴은 GPL 파생물이 되어, 배포할 때 GPL 로 소스를 공개해야 한다.
- **방침(추천)**: A00380 Quad Patch 때와 같이 **독자 구현**. 이 계획서와 구현은 원본의 *동작 설명*(README · MANUAL · DEV_GUIDE 의 설계 원칙)과
  *수학적 아이디어*(부모 공간을 굽고 자기 채널은 커브로 평가, 월드 → 채널 값 역산)만 쓴다. 원본 파이썬 코드는 **복사 · 번역하지 않는다**.
  마야 쪽 코드는 마야 API 로 새로 쓴다(어차피 블렌더 API 코드는 그대로 쓸 수 없다).
- 구현 중 원본 코드를 열어 볼 때는 "무엇을 하는지" 를 확인하는 데만 쓰고, 이 저장소 파일에 원본 코드 조각을 붙이지 않는다.
  (메모 [[wip-a00380-quad-patch]] "Don't paste code from reference scripts — check their licence header first and ask")
- **사용자 확인 필요 (Q1)**: 독자 구현으로 간다 — 추천. (GPL 로 공개해도 된다면 다른 길도 있지만, 이 저장소 정책과 맞지 않는다.)

---

## 2. 원본 분석 — 무엇을 어떻게 하나

### 2-1. 기능 (README · MANUAL)

| 영역 | 원본 기능 | 이 계획의 단계 |
|------|-----------|----------------|
| 표시 | 경로 선 + 프레임마다 점(간격 = 속도) + 키 점 + 핸들, 여러 경로 동시 | **1** (핸들은 2) |
| 키 편집 | 키 클릭 · 드래그, G/R/S, 박스 · 원 선택, 축 고정, 스냅 | **1** (드래그 · 선택) / 2 (R/S, 스냅) |
| 비례 편집 | Proportional editing (근처 키가 함께 따라옴) | 1.5 |
| 핸들 | 키의 Bezier 핸들을 월드에서 잡고 돌림 | 2 |
| 모드 | 1 Location / 2 Rotation(뼈 끝) / 3 Scale(리본) / 4 Value(트랙) | 1 = Location, 3 단계 = Rotation, 이후 Scale · Value |
| 토폴로지 | 키 삽입(모양 유지) · 삭제 · Dissolve · Extrude · Knife · Bevel · Loop cut · Merge · 복사/붙여넣기 | 1.5 (삽입) / 4 이후 |
| 타이밍 | 프레임 점 드래그(간격), 속도 그래프, 타이밍 차트, Breakdown · Scale Time · Moving Hold · Offset Cascade · Shift Phase | 2 (프레임 점 드래그) / 4 이후 |
| 모양 도구 | Smooth · Exaggerate · Ease · 이징 프리셋 · Mirror · Spin · LoopTools | 4 이후 |
| 스컬프트 | Grab · Smooth · Pinch · Slow · Fast · Even · Dissolve(모캡 키 줄이기) 브러시 | 5 이후 |
| 보기 | 어니언 스킨 · 속도 색 · 떨림 히트맵 · 무게중심 · 스냅샷 | 5 이후 (속도 색은 3) |
| 공간 | Global / Local / Camera / Relative To | 3 |
| 갱신 | 부모 · 컨스트레인트가 바뀌면 바뀐 프레임만 백그라운드로 다시 굽기, 자식은 즉시 따라옴 | 2 (자동 다시 굽기) / 4 (자식 즉시) |
| API | AI 어시스턴트용 파이썬 API | 범위 밖(필요하면 나중) |

### 2-2. 핵심 설계 (DEV_GUIDE §3, `core.py`)

- **경로 식**: `world(f) = B(f) @ basis(f)`.
  - `B(f)` = 대상이 물려받는 모든 것(부모, 컨스트레인트, 드라이버) = **부모 공간**. 프레임을 돌며 **한 번** 굽는다.
    원본은 숨긴 보조 씬에서 굽는다 — 사용자 씬 · 프레임 · 포즈를 건드리지 않고, **스킨 메시를 평가하지 않는다**.
  - `basis(f)` = 대상 자신의 loc / rot / scale. **F-Curve 를 직접 평가**해 만든다 → 키가 움직이면 프레임을 다시 돌지 않고 경로가 바로 따라온다.
- **편집 = 역산**: 키를 월드 점 W 로 옮기면 `solve(t, W)` 가 그 프레임의 `B(t)` 역행렬로 채널 값을 구해 **키 값에 쓴다**.
  위치는 정확히 풀린다. 회전은 뼈 끝이 W 로 가는 최소 회전(swing)으로 푼다.
- **핸들**: 월드 핸들 끝 = `point(키 값 + 기울기 × dt, t) + vp × dt`. 여기서 `vp` 는 **부모 공간이 움직이는 속도**다(자기 값은 고정하고 B 만 움직였을 때의 점 속도).
  핸들을 월드에서 끌면 이 식을 거꾸로 풀어 채널마다 기울기를 구한다.
- **편집 전 채널 키 맞추기**(`ensure_keys`): X 에만 키가 있는 프레임에서 키를 움직이면 Y · Z 에도 그 프레임 키를 **모양을 바꾸지 않게** 먼저 넣는다.
  키가 아예 없는 채널은 기존 키 프레임마다 현재 값으로 키를 만든다. **실제로 움직일 때만** 넣는다(드래그를 시작만 하고 놓으면 아무것도 바뀌지 않음).
- **드래그 = 스냅샷 + 매번 처음부터**: 누를 때 커브 상태를 저장하고, 마우스가 움직일 때마다 저장본에서 다시 계산한다(오차 누적 없음). Esc 는 저장본으로 되돌린다.
- **한 동작 = undo 한 번**.
- **갱신 추적**: 부모 애니메이션 · 컨스트레인트 · 드라이버가 바뀌면 다시 굽기를 예약하고, 바뀐 프레임 구간만 굽는다. 현재 프레임 근처부터 굽는다.

### 2-3. 마야로 옮길 때 달라지는 것

| 원본(블렌더) | 마야 | 이 계획의 처리 |
|--------------|------|----------------|
| F-Curve (Bezier, 핸들 = 시간 · 값 좌표) | animCurve (Hermite, 탄젠트 = 각도 · 가중치, 가중/비가중) | 1단계는 **키 값만** 바꾼다(탄젠트는 유지). 2단계에서 탄젠트 ↔ 월드 핸들 변환 |
| 숨긴 보조 씬에서 프레임 돌기 | 시간 문맥(DG context) 평가 | 부모 행렬 plug 만 문맥 평가 (§4-3) |
| `gpu` 모듈로 직접 그리기 | VP2 `MPxDrawOverride` + `MUIDrawManager` | 파이썬 플러그인 locator 노드 (§4-5) |
| 모달 오퍼레이터 | `draggerContext` (파이썬) | 컨텍스트에서 누름 · 끌기 · 놓기 처리 (§4-6) |
| 키 선택 = F-Curve 키 선택 | 툴이 자체 선택을 가짐 | 1단계는 툴 안 선택, 2단계에서 그래프 에디터 키 선택과 동기화(선택) |
| 단위: 블렌더 미터 | 마야 내부 단위 cm · 라디안, UI 단위는 설정에 따름 | **API(내부 단위)만** 쓴다. `cmds.keyframe` 는 UI 단위라 섞지 않는다 |

---

## 3. 툴 개요 (1단계 기준 사용 흐름)

1. 툴 창(`A00630_MotionPathEditor`)을 연다. 씬에서 오브젝트 · 조인트(애니메이션된 컨트롤)를 고르고 **`Add Selected`** → 리스트에 경로가 생긴다.
2. 뷰포트에 경로가 그려진다: **선**(프레임마다 이은 궤적), **작은 점**(프레임마다 - 간격이 속도), **큰 점**(키), **현재 프레임 표시**.
3. **`Edit Path`** 를 누르면 편집 컨텍스트로 들어간다:
   - 키 점 클릭 = 선택(Shift = 추가/빼기, Ctrl = 빼기). 빈 곳 드래그 = 박스 선택.
   - 선택한 키를 드래그 = 화면 평면(또는 고른 평면 · 축)에서 이동 → **그 키의 translate 값이 바뀌고** 경로와 오브젝트가 바로 따라온다.
   - 놓으면 **undo 한 번**으로 묶인다. Esc / 오른쪽 클릭 = 취소.
   - Alt + 드래그 = 카메라(마야 그대로). `Q` = 선택 툴로 나가기.
4. 그래프 에디터에서 키를 고치거나 Ctrl+Z 를 하면 경로가 따라 바뀐다.
5. 부모 · 컨스트레인트 애니메이션을 바꾸면 1단계에서는 **`Refresh`** 버튼으로 다시 굽는다(2단계에서 자동).

---

## 4. 설계 (마야)

### 4-1. 폴더 구조

`A00008_base_QT_maya` 를 복제해 시작한다(CLAUDE.md §9). PySide 버전은 템플릿을 따른다(마야 2022~2024 = PySide2, 2025+ = PySide6 — `Framework.qt.qt` 로 가린다).

```
JUN_All/tools/A00630_MotionPathEditor/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(reload_module=False): MainWindow + ThemeManager("blue_dark" 등 애니메이션 계열 색)
├── __dragDrop_A00630.py        # 셸프 설치 (툴마다 고유 이름, CLAUDE.md §3)
├── icon/A00630.png             # 메모 [[new-tool-needs-icon]]
├── CHANGELOG.md
├── app/
│   ├── config/version.py       # VERSION = "01.00", LAST_UPDATE
│   ├── core/                   # 마야 API 로직 (UI 비의존)
│   │   ├── anim_channels.py    # 대상의 translate 채널 ↔ animCurve 찾기 · 평가 · 키 합집합 · 잠금 판정 · 채널 키 맞추기
│   │   ├── parent_space.py     # 부모 공간 굽기 PM(f) · 피벗 보정 c(f) (§4-3)
│   │   ├── path_cache.py       # PathCache: 프레임 · 점(numpy) · 키 목록 · solve · 부분 갱신
│   │   ├── edit_session.py     # 드래그 한 번: 스냅샷 · MAnimCurveChange 누적 · 비례 가중 · commit / cancel
│   │   ├── picking.py          # 뷰 행렬로 점들을 화면에 투영 · 가장 가까운 키 · 박스 안 키
│   │   ├── watcher.py          # 콜백: 애님 커브 변경 · undo/redo · 시간 변경 · 씬 새로/열기 → 지연 갱신
│   │   ├── draw_bridge.py      # 툴 ↔ 플러그인 데이터 전달 (일반 import 경로, 모듈 하나)
│   │   └── plugin_loader.py    # 플러그인 로드 확인 (A00180 mesh_io.ensure_undo_plugin 과 같은 방식)
│   ├── plugin/
│   │   └── jun_motion_path.py  # maya_useNewAPI: locator 노드 + draw override + undo 명령 (§4-5, §4-7)
│   └── ui/
│       ├── main_window.py      # 툴 창
│       └── edit_context.py     # draggerContext 래퍼 (§4-6)
└── tests/                      # mayapy 시험 (§7)
```

- **툴 간 import 금지**(메모 [[release-layout-launch-py]]). 공용이 필요하면 `Framework/` 로.
- 플러그인 `.py` 는 `__file__` 이 없다 → 경로 계산 금지, `tools.A00630_MotionPathEditor.app.core.draw_bridge` 를 정식 경로로 import(메모 [[maya-loadplugin-no-file]]).

### 4-2. 경로 수학 (위치 경로)

마야 행 벡터 규약: `worldMatrix = xformMatrix × parentMatrix`. `parentMatrix` 는 **자기 offsetParentMatrix 를 포함**한다(메모 [[parentmatrix-includes-offsetparentmatrix]] — 0단계에서 다시 확인).

- **그리는 점** = 대상의 **회전 피벗 월드 위치**(조인트는 조인트 위치). 마야 Move 툴 · Motion Trail 이 보여 주는 점과 같다.
- transform 행렬에서 translate `T` 는 **맨 마지막** 항이다:
  - transform: `[-sp][S][Sh][sp][spt][-rp][Ra][R][rp][rpt][T]`
  - joint: `[S][Ra][R][Jo][IS][T]` (IS = segmentScaleCompensate 의 부모 역스케일)
- 그래서 피벗 점의 월드 위치는 **T 에 대해 아핀**이다:

  ```
  P(f) = (c(f) + T(f)) · PM(f)
  ```

  - `PM(f)` = 그 프레임의 `parentMatrix` (굽는다).
  - `c` = **rotatePivot + rotatePivotTranslate — 상수**(구현 때 실측으로 확정, §10). 조인트는 0, 피벗이 원점인 transform 도 0.
    회전 피벗은 회전 · 스케일 뒤에 `rp + rpt + T` 로 남기 때문에 회전 · 스케일과 무관하다 = 마야 `xform -q -ws -rp`.
    (처음 적은 "`c(f)` 를 worldMatrix 로 굽는다" 는 틀렸다 - 스케일이 1 이 아니면 0.43 어긋났다.)
  - `T(f)` = translate 애님 커브 3개를 **직접 평가**한 값(`MFnAnimCurve.evaluate`, 키 없는 채널은 정적 값).
- **solve (월드 W → translate)** — 정확한 역산:

  ```
  T_new = W · PM(f)⁻¹ − c(f)
  ```

  잠긴 축(`translateX` lock 등)은 그 축 값을 원래대로 두고 나머지만 바꾼다(원본의 lock 처리와 같다).
- `c` 는 상수라 rotate · scale 키가 바뀌어도 다시 굽지 않는다(시험 `test_path_math`). 피벗 위치를 옮기면 `refresh()` 가 다시 읽는다.

### 4-3. 부모 공간 굽기 — 속도의 핵심

- 굽는 것: 대상마다 프레임마다 `PM(f)`(4×4) 와, 피벗이 있으면 `P_baked(f)`. 결과는 numpy `(N, 4, 4)` / `(N, 3)`.
- 후보 평가 방법 (0단계에서 **실측으로 고른다**):

  | 방법 | 내용 | 기대 |
  |------|------|------|
  | A | `MPlug.asMObject(MDGContext(MTime(f)))` 로 `parentMatrix` plug 만 평가 (마야 2022+ 는 `MDGContextGuard`) | 그 plug 의 상류만 계산 → 스킨 메시 · 다른 캐릭터는 계산 안 함. 유력 |
  | B | `cmds.getAttr(node + ".parentMatrix", time=f)` | A 와 같은 원리, 호출 비용만 더 큼(비교 기준) |
  | C | `cmds.currentTime(f, update=False)` + plug 읽기 | **값이 틀려 버림**(다시 계산하지 않은 값, 차이 20 — §10) |
  | D | 마야 기본 Editable Motion Trail (`cmds.snapshot(motionTrail=True, ...)`) | **비교 대상(이겨야 할 기준)** |

- 여러 대상을 굽을 때는 **프레임 하나에 대상 전부**를 읽는다(프레임 바깥 루프) — 같은 부모를 공유하면 상류 계산을 덜 반복할 가능성이 있다(0단계에서 A 의 두 루프 순서 비교).
- 굽는 동안 마야 UI 를 막지 않게 **나눠서 굽는다**: 현재 프레임 ±50 프레임 먼저, 나머지는 `MTimerMessage` / `evalDeferred` 로 조금씩(원본의 BakeJob 과 같은 생각).
  1단계는 단순하게 한 번에 굽고 진행 팝업(`JUN_mod_progress_qt_v01`)을 띄운다. 2,000 프레임 · 무거운 리그에서 1초를 넘으면 2단계에서 나눠 굽기.
- **사용자 씬을 바꾸지 않는다**: 현재 시간 · 선택 · 포즈는 굽기 전과 같아야 한다(시험으로 고정).

### 4-4. 애님 커브 읽기 · 쓰기 (`anim_channels.py`)

- **채널 찾기**: `translateX/Y/Z` plug 의 입력이 **animCurveTL 직결**이면 편집 가능. 그 밖은 1단계에서 **잠금 + 이유 표시**:
  - 컨스트레인트 · 표현식 · 드라이버(그 밖의 노드)가 translate 를 구동 → "Translate is driven by <node>"
  - 애니메이션 레이어(`animBlendNodeAdditiveDL` 등) · `pairBlend` → "Animation layers / pairBlend are not supported yet" (3단계 이후)
  - 레퍼런스된 잠긴 커브 · 잠긴 plug → "Locked"
  - 세 축이 모두 lock → "Translate is locked"
- **평가**: `MFnAnimCurve(curve).evaluate(MTime(f, uiUnit))` — DG 평가 없이 커브 수학만. 프레임 N 개 × 커브 3개.
  N 이 크면(> 5,000) 키 구간별로 numpy 로 Hermite 를 직접 계산하는 경로를 2단계에서 검토(0단계에서 1,000 · 10,000 프레임 측정).
- **키 합집합**: 세 커브의 키 시간을 소수 3자리로 합쳐 "경로 키" 목록을 만든다. 키마다 채널별 인덱스(없으면 -1 = 부분 키).
- **채널 키 맞추기(`ensure_keys`)** — 드래그가 실제로 움직일 때 한 번:
  - 부분 키(그 프레임에 X 만 키) → 나머지 채널에 `MFnAnimCurve.addKey` 를 **모양 유지**로 넣는다(그 시간의 현재 값 · 탄젠트는 커브 기울기에 맞춘 고정 탄젠트,
    또는 `cmds.setKeyframe(insert=True)` 와 같은 결과인지 0단계에서 비교 — 같은 undo 묶음에 들어가야 한다).
  - 커브가 없는 축 → 그 축이 잠기지 않았으면 animCurveTL 을 만들어 기존 키 시간마다 정적 값으로 키(원본과 같은 동작). 이것도 같은 undo 묶음.
- **쓰기**: `MFnAnimCurve.setValue(index, value, change)` — 값은 **내부 단위(cm)**. `MAnimCurveChange` 에 기록해 undo 가능하게(§4-7).
- 탄젠트: 1단계는 건드리지 않는다. 마야 auto · spline 탄젠트는 값이 바뀌면 마야가 다시 계산한다 — 원본 MANUAL 의 "Continuous Acceleration" 주의와 같은 현상(이웃 탄젠트가 함께 움직임)이 마야 `auto` 탄젠트에서 있는지 0단계에서 확인.

### 4-5. 뷰포트 그리기 — 플러그인 locator + VP2 draw override

- 플러그인 파일 `app/plugin/jun_motion_path.py` (OpenMaya 2.0, `maya_useNewAPI = True`) 에:
  - **노드 `junMotionPath`** (`MPxLocatorNode`) — 경로 하나에 노드 하나. 속성: `revision`(int, 바뀌면 다시 그림), `pathKey`(string), 색 · 크기 속성 몇 개.
  - **`junMotionPathDrawOverride`** (`MPxDrawOverride`) — `prepareForDraw` 에서 `draw_bridge.DATA[pathKey]` 를 읽고, `addUIDrawables` 에서 `MUIDrawManager` 로:
    - 경로 선: `mesh(kLineStrip, points)` 또는 `lineStrip`
    - 프레임 점: `points(..., pointSize)` (작게), 키 점: 크게 · 선택 키는 다른 색, 현재 프레임 점: 강조
    - (옵션) 키 옆 프레임 번호: `text`
    - **늘 위에 그리기**: `setDepthPriority(kDormantPointDepthPriority 이상)` 또는 깊이 테스트 끄기 — 메시에 가려지지 않게
  - **명령 `junMotionPathSetKeys`** (`MPxCommand`) — §4-7.
- 그리기 데이터는 **바뀔 때만** 만든다: 툴이 `MPointArray` 와 색 배열을 `draw_bridge` 에 넣고 노드의 `revision` 을 올린다 → 마야가 그 노드만 다시 그린다.
  매 그리기마다 numpy → `MPointArray` 변환을 하지 않는다.
- 노드는 **씬에 저장되지 않는다**: 만들 때 `MFnDependencyNode.setDoNotWrite(True)`, 아웃라이너에서 숨김(`hiddenInOutliner`).
  툴을 닫거나 씬을 새로 · 열기(`MSceneMessage`) 하면 지운다.
  **저장 직전(`kBeforeSave`)에 지우고 저장 뒤 다시 만든다** — 노드가 씬에 있으면 doNotWrite 여도(그리고 `pluginInfo -writeRequires off` 여도)
  파일에 `requires jun_motion_path` 줄이 써져, 툴 없는 PC 에서 경고가 난다(구현 때 실측).
- 마야 셀렉션 대상이 아니다(`isTransparent`/선택 불가 설정 또는 `overrideEnabled + displayType=reference`) — 클릭은 우리 컨텍스트가 처리한다.
- 0단계 확인: 파이썬 draw override 로 **경로 10개 × 2,000 점**을 그릴 때 뷰포트가 60fps 근처를 유지하는지. 느리면 점은 `MUIDrawManager.mesh(kPoints)` 한 번에.

### 4-6. 편집 컨텍스트 (`edit_context.py`)

- `cmds.draggerContext("junMotionPathCtx", pressCommand=..., dragCommand=..., releaseCommand=..., space="screen", cursor="hand", undoMode="sequence")`
  — 파이썬만으로 된다. 툴 창의 **`Edit Path`** 버튼이 `cmds.setToolTo(ctx)`, 나갈 때 이전 툴로.
- **누름**: 화면 좌표 → `picking.pick(x, y)`:
  - 뷰 행렬: `M3dView.active3dView()` 의 `modelViewMatrix` · `projectionMatrix` + 뷰포트 크기 → 보이는 경로의 키 점을 **numpy 로 한 번에** 화면에 투영.
  - 반경 `PICK_RADIUS_PX = 10` 안에서 가장 가까운 키. 없으면 박스 선택 시작.
  - Shift / Ctrl 은 `cmds.draggerContext(ctx, q=True, modifier=True)`.
- **끌기**: 드래그 평면 = 기본 **화면 평면**(눌린 키를 지나고 카메라 방향에 수직). 옵션: `View`, `XZ (ground)`, `X`, `Y`, `Z`(축은 그 축 위로만).
  마우스 광선과 평면의 교점 → 이동량 `Δ` → 선택 키마다 `W = 원래 월드 점 + Δ` → `solve` → `setValue`(누적 change) → 바뀐 키 사이 구간만 경로 다시 계산 → `draw_bridge` 갱신 → `M3dView.refresh(False, True)`.
  오브젝트 자체도 커브가 바뀌었으니 현재 프레임에서 따라 움직인다.
- **놓기**: `junMotionPathSetKeys` 명령으로 누적된 change 를 undo 큐에 넣는다(한 번). 아무것도 안 움직였으면 아무것도 안 한다.
- **취소**: draggerContext 는 키 입력을 받지 않아 Esc 대신 **드래그 중 오른쪽 버튼** → change `undoIt()` 로 되돌리고 경로를 원래대로.
  다른 툴로 바꾸면(`finalize`) 끄는 중인 드래그도 취소.
- 마야 내비게이션(Alt + 드래그)은 컨텍스트와 무관하게 동작한다(0단계 확인).

### 4-7. undo — 한 동작 = 한 번

- A00180 의 `abSymSetPoints` 와 같은 구조(메모 [[maya-loadplugin-no-file]]): 툴이 `draw_bridge.PENDING` 에 **드래그 동안 쌓인 `MAnimCurveChange`**
  (와 `ensure_keys` 로 만든 키 · 커브 정보)를 넣고 `cmds.junMotionPathSetKeys()` 를 부른다. 명령의 `doIt` 이 그것을 받아 두고,
  `undoIt` = `change.undoIt()`, `redoIt` = `change.redoIt()`. `isUndoable() = True`.
- 커브를 새로 만든 경우(키 없던 축)는 그 커브 생성도 되돌려야 한다 → 그 부분은 `MDGModifier`(커브 노드 생성 + 연결)로 하고 같은 명령이 함께 undo/redo.
- 드래그 중 `setValue` 는 undo 큐 밖(change 에만 기록)이라, 마야 undo 큐에는 놓을 때 **딱 한 번** 들어간다.
- 메모 [[undo-chunk-by-default]]: 그 밖의 씬 변경(경로 추가 · 삭제 등)은 `undo_chunk` 안에서. 그리기 노드 생성 · 삭제는 **undo 큐에 넣지 않는다**(API 로, A00380 미리보기와 같은 방식 — [[wip-a00380-quad-patch]]).

### 4-8. 갱신 (`watcher.py`)

| 무엇이 바뀌나 | 감지 | 처리 |
|---------------|------|------|
| 대상의 translate 키 (그래프 에디터 · 다른 툴 · undo) | 대상 애님 커브에 `MNodeMessage.addAttributeChangedCallback` (키 배열 변경) | 그 경로 `dirty` → **idle 에 한 번** 다시 계산(`evalDeferred(lowestPriority)`), 굽기 없음 |
| 대상의 rotate · scale 키 (피벗 있는 transform) | 같음 | `c(f)` 다시 계산 |
| 부모 · 컨스트레인트 · 드라이버 애니메이션 | 1단계: 없음(**Refresh** 버튼) · 2단계: 상류 애님 커브 목록에 콜백 + 서명 비교 | 다시 굽기 (2단계: 바뀐 커브의 키 범위만) |
| 현재 시간 | `MEventMessage("timeChanged")` | 현재 프레임 표시만 갱신 |
| undo / redo | `MEventMessage("Undo"/"Redo")` | 모든 경로 `dirty` |
| 씬 새로 · 열기 · 참조 | `MSceneMessage` | 경로 · 노드 · 콜백 모두 정리 |

- 콜백 안에서는 **씬을 바꾸지 않고** 표시만 `dirty` 로 둔다. 실제 계산은 idle 에서 한 번(여러 콜백을 한 번으로 모은다).
- 툴 창이 닫히면 콜백 · 컨텍스트 · 노드를 전부 정리(`closeEvent`).

### 4-9. 툴 창 (1단계)

```
[Paths]                                   (JUN_mod_tsl_qt_v01, 한 줄 = 대상 하나)
  pCube1           [Add Selected] [Remove] [Clear]
  L_hand_ctrl
[Range]   (o) Playback  ( ) Scene  ( ) Custom [  1 ] ~ [ 120 ]
[Display] [x] Frame dots  [x] Key points  [ ] Frame numbers   Line width [--|--]  Point size [--|--]
[Edit]    [ Edit Path ]  (토글, 켜지면 컨텍스트)   Drag plane (o) View ( ) Ground ( ) X ( ) Y ( ) Z
[Refresh]  - 부모 애니메이션이 바뀌었을 때 다시 굽기
[Log]
```

- UI 문자열은 영어. 슬라이더는 공용 `JUN_mod_sliderStyle_qt_v01`(메모 [[feedback-sliders-use-shared-style]]). 로그는 공용 log 위젯. 메뉴 바는 `tool_menu.COMMON_MENUS`.
- 창 높이는 `JUN_mod_tabFit_qt_v01`(탭이 생기면). 경로마다 잠금 이유는 로그와 리스트 툴팁.
- 설정(표시 옵션 · 드래그 평면)은 optionVar `JUN_A00630_*` 로 기억.

---

## 5. 단계별 작업

### 0단계 — 실측과 기술 확인 (먼저, 결과를 이 문서 §10 에 적는다)

`tests/bench_motion_path.py` (mayapy 2024) 와 GUI 마야에서 짧은 확인.

| # | 확인할 것 | 통과 기준 |
|---|-----------|-----------|
| 0-1 | 굽기 방법 A · B · C 와 마야 Motion Trail(D) 의 시간 — 시험 씬 3종(§7-1) × 프레임 120 · 1,000 | A(또는 고른 방법)가 D 보다 **5배 이상 빠름**(무거운 리그) |
| 0-2 | 문맥 평가가 IK · 컨스트레인트 · 드라이버 · OPM 에서 `worldMatrix -time` 과 같은 값 | 차이 < 1e-6 |
| 0-3 | `MFnAnimCurve.evaluate` 1,000 / 10,000 프레임 × 3 커브 시간 | 1,000 프레임 < 10 ms |
| 0-4 | 누적 `MAnimCurveChange` + `MPxCommand` undo/redo 한 번 | Ctrl+Z 한 번에 원래 값, Ctrl+Y 로 다시 |
| 0-5 | `setValue` 뒤 auto/spline 탄젠트 재계산 범위 | 기록만(설계 변경 필요 여부) |
| 0-6 | 파이썬 draw override 성능 (GUI): 경로 10 × 2,000 점 | 뷰포트 회전 시 체감 끊김 없음 |
| 0-7 | `draggerContext` 에서 Alt 내비게이션 · 수식키 · Esc 처리 (GUI) | 동작 |
| 0-8 | `parentMatrix` 가 자기 OPM 을 포함하는지, 조인트 IS 가 T 앞인지 | §4-2 식이 맞음 |

0단계 결과로 §4-3 방법을 확정하고, 0-1 기준을 못 넘으면 계획을 다시 본다(그 경우 사용자에게 보고).

### 1단계 — 위치 경로 표시 + 키 드래그 (핵심, 첫 배포 v01.00)

- **범위**: transform · joint 의 Location 경로. translate 가 animCurveTL 직결인 대상.
- **작업**
  1. 툴 골격(템플릿 복제, launch · dragDrop · icon · version · CHANGELOG).
  2. `anim_channels.py`: 채널 찾기 · 잠금 판정 · 평가 · 키 합집합 · `ensure_keys`.
  3. `parent_space.py`: 0단계에서 고른 방법으로 `PM(f)` · `c(f)` 굽기, 사용자 시간 · 선택 불변.
  4. `path_cache.py`: `refresh()`(점 · 키), `refresh_span(f0, f1)`(드래그 중 부분 갱신), `solve(f, W)`.
  5. 플러그인: 노드 + draw override + `junMotionPathSetKeys` 명령, `plugin_loader`.
  6. `picking.py` · `edit_context.py`: 클릭 선택 · Shift/Ctrl · 박스 선택 · 선택 키 드래그(평면 옵션) · Esc 취소.
  7. `edit_session.py`: 누를 때 스냅샷, 움직일 때 `ensure_keys`(한 번) + `setValue` 누적, 놓을 때 명령, 취소.
  8. `watcher.py`: 애님 커브 변경 · undo/redo · 시간 · 씬 정리.
  9. 툴 창(§4-9).
- **완료 기준**
  - 키를 끌어 놓으면 그 프레임의 **피벗 월드 위치 = 놓은 점**(차이 < 1e-4 cm, mayapy 로 `xform -q -ws -rp` 를 그 시간에 읽어 확인).
  - 드래그 중 놓기 전까지 undo 큐에 아무것도 없고, 놓은 뒤 **Ctrl+Z 한 번**에 원래대로.
  - 그래프 에디터에서 키를 바꾸면 경로가 다음 idle 에 따라온다.
  - 툴을 닫으면 씬에 노드 · 콜백이 하나도 남지 않고, 저장한 파일에 그리기 노드가 없다.
  - 속도: 0-1 기준 + 드래그 한 번 갱신(경로 1,000 프레임, 키 1개) < 16 ms(파이썬 측 시간).

### 1.5단계 — 프레임 단위 편집 · 비례 편집

- **키 아닌 프레임 점 드래그**: 옵션 `Frame drag` = `Insert key` (그 프레임에 **모양 유지 키 삽입** 후 그 키를 끈다) / `Off`.
- **비례 편집**: 선택 키를 끌면 주변 키가 **가중치만큼** 따라온다. 반경 = 프레임 수(기본) 또는 월드 거리, 곡선 = Smooth / Linear / Sharp(공용 falloff 위젯 `JUN_mod_falloffCurve_qt` 재사용 가능).
  모캡처럼 **매 프레임 키**인 커브에서 핵심 기능이다.
- **수치 입력**: 선택 키의 월드 위치를 툴 창에서 X/Y/Z 로 입력(`Edit Value` 와 같은 역할).

### 2단계 — 탄젠트 핸들 · 자동 갱신 · 타이밍

- **핸들 표시 · 편집**: 키의 in/out 탄젠트를 월드 핸들로(§2-2 식, `vp` 포함). 마야 탄젠트 단위(시간 축 초 · 각도 · 가중치, 가중/비가중)를 0단계식 측정으로 확정한 뒤
  핸들 드래그 → 채널마다 기울기 → `setInTangent/OutTangent`(타입은 `fixed` 로, 좌우 `unify` 유지 옵션).
- **자동 다시 굽기**: 상류 애님 커브 · 컨스트레인트 가중치 등의 서명을 두고, 바뀌면 **바뀐 키 구간만** 다시 굽기, 나눠 굽기(현재 프레임 근처 먼저).
- **프레임 점 드래그 = 타이밍**(원본 기본 동작): 경로 모양은 그대로, 그 프레임이 경로 위 어디에 오는지만 바꾼다 — 구간의 호 길이-시간 관계를 다시 맞추는 refit. 1.5단계 `Insert key` 와 모드로 구분.
- 그래프 에디터 키 선택과 동기화(옵션).

### 3단계 — 회전 경로 · 공간 · 표시

- **Rotation 경로**: 조인트 · 컨트롤의 **끝점**(자식 방향 길이 `Rotation Length`)을 그린다. 끝점을 끌면 그 점을 향하는 **최소 회전(swing)** 을 회전 채널(rotate XYZ, 회전 순서 · rotateAxis · jointOrient 반영)에 쓴다.
  오일러 연속성은 원래 값에 가장 가까운 해로(메모 [[euler-closest-solution-not-equivalent]] 주의).
- **공간**: Global / Local(현재 프레임의 부모에 붙여 보기) / Camera(카메라에서 본 궤적) / Relative To(다른 노드 기준).
- 속도 색(점 간격 대신 색으로 빠르기), 떨림 히트맵.
- 애니메이션 레이어 · pairBlend 지원 검토(선택 레이어의 커브에 쓰기).

### 4단계 이후 — 원본의 나머지 (우선순위 순)

1. 키 삽입 · 삭제 · Dissolve(모양을 최대한 유지하며 키 줄이기) · 복사/붙여넣기
2. Smooth · Exaggerate · Ease · 이징 프리셋
3. 타이밍 도구: Breakdown · Scale Time · Moving Hold · Offset Cascade · Shift Phase
4. 스컬프트 브러시(Grab · Smooth · Slow/Fast/Even · Dissolve) — 모캡 정리
5. Scale · Value 경로
6. 어니언 스킨 · 스냅샷 · 무게중심
7. Knife · Bevel · Loop cut · Extrude · Merge · LoopTools 류
8. 자식 즉시 따라오기(굽지 않고 계산), 스크립트 API

각 단계는 시작 전에 이 문서에 짧은 하위 계획을 추가한다.

**하위 계획서**
- 속도 그래프 · Smooth Speed (2단계 타이밍 + 4단계 3번 · 2번 일부) → [`A00630_MotionPathEditor_speed_graph_plan.md`](A00630_MotionPathEditor_speed_graph_plan.md) (2026-11-19 계획, **2026-11-20 v01.04 구현** · GUI 확인 전)

---

## 6. 위험과 대응

| 위험 | 대응 |
|------|------|
| GPL 코드 유입 | 독자 구현, 원본 코드 복사 금지(§1). 리뷰 때 원본과 겹치는 코드가 없는지 확인 |
| 문맥 평가가 기대만큼 빠르지 않음(리그가 상류에서 무거움) | 0단계 실측 후 C(시간 이동) · 나눠 굽기 · 상류가 FK 뿐이면 직접 계산(4단계 항목 8 을 앞당김) |
| 문맥 평가 값이 실제 재생과 다름(시간 노드 · 표현식 · 캐시 · 동역학) | 0-2 로 확인. 다른 노드는 잠금 표시 + `Refresh` 시 C 방식 폴백 |
| `setValue` 뒤 auto 탄젠트가 이웃까지 바뀜 | 0-5 결과를 문서화, 필요하면 편집 키의 탄젠트를 `fixed`/현재 기울기 유지 옵션 |
| 단위 혼동(cm/m, 도/라디안, UI 시간 단위) | API 내부 단위만 사용. `cmds.keyframe` · `keyTangent` 를 섞지 않는다. 시험 씬을 미터 단위로도 한 번 |
| 파이썬 draw override 가 느림 | 바뀔 때만 배열 생성, `mesh(kPoints)` 한 번 그리기, 경로가 많으면 선택된 것만 키 점 |
| 콜백 누수 · 크래시 | 노드 · 콜백 ID 를 한 곳(`watcher`)에서 관리, 창 닫기 · 씬 변경 · 플러그인 언로드 때 정리. 콜백 안에서는 씬 변경 금지 |
| undo 와 그리기 노드가 섞임 | 그리기 노드는 API 로 만들고 undo 큐 밖. 시험으로 "Ctrl+Z 한 번 = 키만 되돌림" 고정 |
| 레퍼런스 리그 · 잠긴 커브 | 잠금 이유 표시, 편집 안 함 |
| 플러그인 로드(`__file__` 없음) | A00180 방식 bridge 모듈, 정식 import 경로 |

---

## 7. 시험

### 7-1. 시험 씬 (코드로 만든다, `tests/scenes.py`)

1. **단순**: transform 하나, translate 키 5개(부분 키 포함), 피벗을 원점 밖으로 옮긴 것 하나, OPM 이 있는 것 하나.
2. **계층**: 애니메이션된 부모 3단 + 컨스트레인트(parent · point) 로 움직이는 그룹 아래 컨트롤, 조인트 체인(jointOrient · segmentScaleCompensate · 비균일 스케일 부모).
3. **무거운 리그**: 조인트 200 + IK 4 + 컨스트레인트 50 + 스킨 메시(10만 버텍스) + 다른 캐릭터 한 벌(상관없는 무거운 노드). 120 · 1,000 프레임.

### 7-2. mayapy 시험 (헤드리스, 메모 [[mayapy-headless-verify]])

| 파일 | 내용 |
|------|------|
| `tests/bench_motion_path.py` | 0단계 표 출력(방법 A~D 시간), 1단계 이후 회귀용 속도 기준 |
| `tests/test_path_math.py` | 굽기 값 = `getAttr worldMatrix -time` (씬 1·2), `c(f)` (피벗 · OPM · 조인트), solve 후 월드 피벗 = W (< 1e-4) |
| `tests/test_anim_channels.py` | 잠금 판정(컨스트레인트 · 레이어 · lock), 키 합집합, `ensure_keys` 가 모양을 바꾸지 않음(삽입 전후 120 프레임 값 같음), 커브 없는 축 생성 |
| `tests/test_edit_session.py` | 드래그 흉내(세션 API 직접 호출): 키 이동 → 값, 여러 키 · 잠긴 축, 비례 가중(1.5단계), **undo 한 번 · redo**, 취소 = 원래대로, 움직이지 않고 놓기 = 변화 없음 |
| `tests/test_watcher.py` | 그래프 에디터식 변경(`MFnAnimCurve` · `cmds.keyframe`) → dirty → 갱신, undo 후 갱신, 씬 새로 → 정리, 사용자 시간 · 선택 불변 |
| `tests/test_ui.py` | 오프스크린 툴 창(QApplication 을 standalone 보다 먼저 — [[qapplication-before-maya-standalone]]): 경로 추가 · 제거 · 범위 · 옵션 기억 · 잠금 이유 표시 |

- draw override · 컨텍스트 · 실제 마우스 드래그는 헤드리스로 확인할 수 없다 → **사용자 GUI 확인 목록**(§7-3).
  대신 그리기 데이터(점 · 색 · 선택 표시 배열)는 `draw_bridge` 에서 숫자로 시험한다.

### 7-3. GUI 확인 (사용자)

1. 툴 열기 → 큐브 · 조인트 경로 추가 → 선 · 점 · 키가 보이고 메시에 가려지지 않음.
2. Edit Path → 키 클릭 · Shift · 박스 선택 → 드래그 → 오브젝트가 따라옴 → 놓고 Ctrl+Z 한 번.
3. Alt 로 카메라 돌리면서 편집, Esc 취소, Q 로 나가기.
4. 그래프 에디터에서 키 이동 → 경로가 따라옴.
5. 무거운 리그에서 마야 Editable Motion Trail 과 체감 비교(만들기 · 드래그).
6. 저장 → 툴 없이 다시 열기: 오류 · 남은 노드 없음.

---

## 8. 문서 · 기록 (각 단계 끝에)

- `JUN_All/docs/A00630_MotionPathEditor.md` (툴 가이드: 사용법 · 옵션 · 잠금 이유 표 · 알아 둘 것 · 검증)
- `CHANGELOG.md` · `app/config/version.py` · `JUN_All/docs/WORKLOG.md` · portfolio EN/KR(메모 [[update-portfolio-on-tool-work]])
- 툴 런처 버튼(A00370, 메모 [[launcher-buttons-follow-current-version]]) · 아이콘
- 메모 `wip-a00630-motion-path.md` (라이선스 결정, 0단계 실측 결과, 마야 함정)
- 이 계획서의 §10 에 단계별 결과

---

## 9. 정할 것 (구현 전 사용자 확인)

| # | 질문 | 추천 |
|---|------|------|
| Q1 | 원본이 GPL-3.0 — 코드 복사 없이 **독자 구현**으로 갈까? | **예** (§1) — **결정 2026-11-19: 독자 구현** |
| Q2 | 툴 이름 `A00630_MotionPathEditor` 괜찮은가? | 예 (A00630 은 비어 있음) — **결정: 그대로** |
| Q3 | 1단계 대상: translate 가 **애님 커브 직결**인 transform · joint 만 (레이어 · 컨스트레인트 구동은 잠금 표시) | 예 — 레이어는 3단계 — **결정: 추천대로** |
| Q4 | 키 아닌 프레임을 끌 때 기본 동작: 1.5단계 `Insert key`(키 넣고 이동) — 원본의 기본(타이밍 이동)은 2단계 | 예 — 요청 우선순위가 "위치로 애니메이션 수정" 이므로 — **결정: 추천대로** |
| Q5 | 지원 마야 버전: 2024 기준 + 2023 확인(메모 [[maya-2023-compat]]), 2025+ PySide6 | 예 — **결정: 추천대로** |

---

## 10. 결과 기록 (단계가 끝날 때마다 채운다)

### 0단계 (2026-11-19, mayapy 2024, `tests/bench_motion_path.py`)

| 씬 · 1,000 프레임 | A 문맥 평가 | B getAttr -time | C 시간 이동 | D Motion Trail 만들기 | 키 하나 바꾼 뒤: D | 키 하나 바꾼 뒤: 이 툴(커브 평가) |
|---|---|---|---|---|---|---|
| 단순 | 0.014 | 0.033 | 0.011 | 0.025 | 0.036 | **0.002** |
| 계층 | 0.174 | 0.198 | (틀림) | 0.182 | 0.175 | **0.002** |
| 무거운 리그 | 0.141 | 0.176 | (틀림) | 0.148 | 0.153 | **0.002** |

- **방법 A 로 확정.** C 는 빠르지만 값이 틀렸다(다시 계산하지 않은 값, 최대 차이 20).
- **0-1 기준(만들기 5배)은 못 넘었다**: 만들기는 A ≈ Motion Trail(둘 다 프레임마다 리그 평가 - 피할 수 없다).
  대신 **편집 때 약 70 ~ 90배**(0.002 대 0.15초), 드래그 한 번 3.4 ms. 요청의 "훨씬 빨라야" 는 편집 쪽에서 충족 — 사용자에게 보고.
  만들기를 더 줄이려면 상류가 FK 뿐일 때 행렬을 직접 계산(4단계 항목 8 을 앞당기기)이 다음 후보.
- 0-2 · 0-8: 문맥 평가 parentMatrix 로 만든 경로 = 마야 `xform -ws -rp` (차이 < 1e-15). OPM 은 parentMatrix 에 들어 있다.
- 0-3: 커브 3개 × 1,000 프레임 평가 2 ms.
- 0-4: 드래그 동안 쌓은 MAnimCurveChange 를 명령이 받아 **undo 한 번 · redo** 정확(차이 0).
- 0-5: `auto` 탄젠트는 키 하나를 바꾸면 이웃 키 탄젠트도 다시 계산 → 앞뒤 키 사이까지 바뀐다(그래프 에디터와 같음, 설계 변경 불필요).
- 0-6 · 0-7 (GUI): 아직. 그리기 · 컨텍스트에 쓴 API 이름이 마야 2024 에 있는 것만 확인.
- 실측으로 찾은 마야 함정: `getAttr -time worldMatrix` 는 시간 문맥 값을 캐시해 두고 **자기 커브가 바뀌어도 옛 값**을 준다(`dgdirty` 로도 안 지워짐).
  이 툴의 굽기(parentMatrix plug + makeCurrent)는 부모를 바꾼 뒤 다시 구우면 새 값이 나왔다. 시험 기준값은 `xform -ws -rp` 실측으로 바꿨다.

### 1단계 (2026-11-19, v01.00)

- 완료: 툴 골격 · 채널 · 굽기 · 경로 캐시 · 플러그인(노드 + draw override + undo 명령) · 고르기 · 편집 컨텍스트 · 편집 세션 · 감시 · 툴 창 · 아이콘 · 런처 버튼.
- 완료 기준: 놓은 위치 = 마야 피벗(차이 1e-16) · undo 한 번 · 그래프 에디터/undo 에 따라옴(감시 flush) · 창 닫으면 노드 · 콜백 없음 · 저장 파일에 노드 · requires 없음 ·
  드래그 갱신 3.4 ms(< 16) — 모두 mayapy 로 확인. 시험 106항목(§7-2 + `test_picking.py`).
- 남은 것: §7-3 GUI 확인. 1.5단계(키 아닌 프레임 끌기 = 키 넣고 이동 · 비례 편집 · 수치 입력)부터 다음 작업.
