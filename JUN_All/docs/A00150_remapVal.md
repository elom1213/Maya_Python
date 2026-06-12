# A00150_remapVal 사용법

## 1. 개요

여러 오브젝트(주로 조인트)의 어트리뷰트를 remapValue 커브로 구동하는 셋업을 만드는 툴이다.
**두 가지 빌드 모드**를 제공한다.

1. **Slerp Ramp** (기존) — 하나의 마스터 remapValue 가 여러 개의 remapValue 를 구동해서
   "multi-out 커브" 효과를 흉내낸다. 원래 트위스트 리본 IK용으로 작성됐지만, 임의의
   어트리뷰트에 적용할 수 있다.
2. **Sine Wave** (v01.01~) — 오브젝트마다 `plusMinusAverage → animCurve → remapValue`
   체인을 만들어 **위상이 어긋난 사인 웨이브를 전파**한다. 컨트롤러에 추가한 driver attr
   하나로 전체 위상을 민다.

> **v01.02 — 마스터 remapValue 일괄 제어**: 두 모드 모두
> **컨트롤러 attr → 마스터 remapValue → 자식 remapValue** 의 fan-out 구조로 통일했다.
> - Slerp Ramp: 마스터의 `outputMin`/`outputMax` 가 모든 자식의 `outputMin`/`outputMax` 를
>   구동하도록 연결을 추가했고, 그 값을 컨트롤러 `{prefix}_output_min`/`_output_max` 로 노출한다.
> - Sine Wave: 없던 **마스터 노드 `{prefix}_wave_master_MAP`** 를 신설해, range 4개와
>   봉우리 커브(`value[0~2]`)를 마스터가 들고 모든 자식 remapValue 를 구동한다.
>
> 즉 노드 하나(마스터)만 조절하면 진폭·커브 모양이 전체에 일괄 반영된다.

- 원본 로직: `sample_01.py` 의 `build_slerp_ramp` (Chris Lesage, 2019). Sine Wave 모드는
  `build_sine_wave` 로 추가됐다.
- DCC: Autodesk Maya (PySide UI). 노드 생성은 **pymel** 사용.
- UI는 `A00090_ConnectionBuilder`(QLineEdit+Get)와 `01_Modules/JUN_PY_numberTool`(소스+어트리뷰트 2-리스트)
  구성을 참고했다.

---

## 2. 폴더 구조

```
A00150_remapVal/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마 적용 → show()
├── config.py              # 셸프 버튼 설치 + 드래그&드롭 진입점
├── CHANGELOG.md
├── requirements.txt
├── sample_01.py           # 원본 참고 코드(보존)
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직
    │   ├── slerp_ramp.py  # add_attr / build_slerp_ramp + run_build (Slerp Ramp 모드)
    │   │                  #  + build_sine_wave + run_build_wave (Sine Wave 모드)
    │   └── maya_scene.py  # cmds 보조 래퍼 (selection / list_keyable_attrs / exists)
    └── ui/main_window.py  # 전체 UI
```

- **노드 생성 본체**(`slerp_ramp.py`)는 pymel을 쓰고, **UI 보조**(선택·어트리뷰트 나열)는 `maya.cmds`
  (`maya_scene.py`)를 쓴다. UI는 pymel을 직접 다루지 않고 `run_build(...)`만 호출한다.

---

## 3. 설치

`A00150_remapVal/config.py` 를 Maya 뷰포트로 **드래그&드롭** → 셸프에 **`RemapVal`** 버튼 생성.

---

## 4. 실행

- 셸프 버튼 **`RemapVal`** 클릭, 또는 Script Editor에서:

```python
import tools.A00150_remapVal as A00150_remapVal
A00150_remapVal.run(True)
```

---

## 5. UI 구성

```
┌ Help ───────────────────────────────────────┐  ← 메뉴 바 (Help > About)
│ Main Controller [ QLineEdit        ] [Get]   │
│ Prefix          [ twist            ]         │
│ Driver Attr [ wave ]                         │  ← Sine Wave 모드 전용
│ Range  In Min[0] In Max[N-1, read-only] Out Min[0] Out Max[1.000] │  ← In: Sine Wave 전용 / Out: 두 모드 공용
├ Set Up ──────────────────────────────────────┤
│ [Joints]                [Attributes]         │
│ Select Objects          List Attributes      │
│ ┌ QListWidget ┐         ┌ QListWidget ┐      │
│ │  joints     │         │ rotateX...  │      │
│ └─────────────┘         └─────────────┘      │
│ Add|Del|Up|Down|Sort    Del|Up|Down|Sort     │
│ Attr Search [ token        ] [Search]        │
├──────────────────────────────────────────────┤
│  [ Build (Slerp Ramp) ] [ Build (Sine Wave) ]│
├ Log ─────────────────────────────────────────┤
│ ┌ read-only 로그창 (영어 출력) ┐             │
│ └────────────────────────────────┘           │
└──────────────────────────────────────────────┘
```

- **Help > About**: 툴 설명·사용법 팝업.
- **Main Controller** = `controlObj`. `Get`을 누르면 현재 Maya 선택의 첫 오브젝트가 채워진다. 제어용 어트리뷰트들이 이 컨트롤러에 추가된다.
- **Prefix** = 첫 인자(기본 `twist`). 생성되는 노드/어트리뷰트 이름의 접두사로 쓰여 이름 충돌을 막는다.
- **Driver Attr** (Sine Wave 모드 전용, 기본 `wave`) = 컨트롤러에 추가되는 keyable double 어트리뷰트 이름. 이 값이 모든 오브젝트의 **위상(phase)** 을 한 번에 민다. Slerp Ramp 모드에서는 사용하지 않는다.
- **Range** = remapValue range의 **기본값**. **In Min / In Max** 는 Sine Wave 모드 전용,
  **Out Min / Out Max** 는 **두 모드 공용**(마스터 remapValue 의 Output Min/Max 기본값).
  - **In Max 는 항상 (Joints 개수 - 1)** 로 자동 세팅되는 **읽기 전용** 값이다. Joints 리스트가
    바뀔 때마다(Select / Add / Del / Sort) **라이브로 자동 갱신**된다. 사용자가 직접 입력할 수 없다.
    이렇게 해야 마스터 remapValue 의 input 범위가 `0 .. (오브젝트 수 - 1)` 로 animCurve 출력과 정렬된다.
  - Sine Wave: 빌드 시 컨트롤러에 `{prefix}_input_min` / `_input_max` / `_output_min` / `_output_max` 4개가 만들어져 **마스터** remapValue 를 connect 하고, 마스터가 다시 모든 자식을 구동한다. `_input_max` 기본값은 위 규칙대로 **오브젝트 개수 - 1** 이다.
  - Slerp Ramp: **Out Min / Out Max** 만 사용. 빌드 시 `{prefix}_output_min` / `_output_max` 가 만들어져 마스터의 Output Min/Max 를 connect 한다(In Min/Max 는 무시 — 마스터의 Input Max 는 조인트 개수 - 1 로 자동 설정).
  - 빌드 후 **컨트롤러에서 이 값들을 조절하면 전체 remapValue 가 동시에 바뀐다**(Out Max = 진폭).
- **Joints** (좌측, 재사용 위젯 `JUN_mod_tsl_qt_v01`) = `oColl`. 대상 오브젝트들. Select/Add/Del/Up/Down/Sort.
- **Attributes** (우측, 재사용 위젯) = 적용할 어트리뷰트. **List Attributes** 버튼이 Joints 리스트 **첫 오브젝트**의 keyable 어트리뷰트(rotateX/Y/Z, scaleX/Y/Z 등)를 채운다. 여기서 **하나 또는 여러 개**를 선택한다.
- **Attr Search**: 토큰(예: `rotate`)을 포함하는 어트리뷰트를 리스트에서 선택해 준다(어트리뷰트가 많을 때 편리).
- **Build (Slerp Ramp)**: 기존 마스터 remapValue 슬러프 램프 셋업 생성.
- **Build (Sine Wave)**: 위상 사인 웨이브 셋업 생성. **Driver Attr 이름**이 필요하다.
- 각 Build는 전체가 **하나의 Undo 청크**로 묶여 Ctrl+Z 한 번에 취소된다.
- **Log**: 결과/경고를 영어로 출력하는 읽기 전용 창.

---

## 6. 사용 순서

1. 컨트롤러로 쓸 오브젝트를 선택 → **Get** (Main Controller 채움).
2. 대상 조인트들을 선택 → Joints 리스트의 **Add**.
3. **List Attributes** 클릭 → 채워진 어트리뷰트에서 적용할 것(예: `rotateY`)을 하나 이상 선택.
   (필요하면 Attr Search로 빠르게 선택)
4. **Prefix** 입력(기본 `twist`). Sine Wave 모드면 **Driver Attr** 이름(기본 `wave`)과 **Range**(In/Out Min·Max) 기본값도 설정.
5. 모드에 맞는 버튼 클릭:
   - **Build (Slerp Ramp)** → 마스터 노드와 적용 결과가 로그에 출력.
   - **Build (Sine Wave)** → 컨트롤러에 추가된 driver attr 경로와 적용 결과가 로그에 출력.
     이후 컨트롤러의 driver attr 값을 조절하면 오브젝트들이 위상차를 두고 사인 형태로 움직인다.

---

## 7. 동작 규칙

### 공통
- Attributes는 **선택된 항목**만 적용된다(리스트에 있어도 선택 안 하면 미적용).
- 각 Build 전체가 **단일 Undo 청크** — Ctrl+Z 한 번으로 생성 노드 전부 취소.

### Slerp Ramp 모드
- 생성되는 마스터 노드: `{prefix}_master_ribbon_lerp_MAP` (remapValue). 조인트 개수만큼
  `{prefix}_lerp_profile_{i}_MAP` 등이 생성되어 마스터 커브에 연결된다.
- 마스터의 **Input Max 는 항상 (조인트 수 - 1)** 로 set 된다 → input 범위 `0 .. N-1`.
- 마스터는 자식들의 `value[0]`/`value[1]`(position·floatValue·interp)에 더해
  **`outputMin`/`outputMax` 도 connect** 한다(v01.02). 따라서 마스터의 Output Min/Max 를
  바꾸면 모든 자식의 진폭이 함께 변한다.
- 컨트롤러에 추가되는 제어 어트리뷰트: `{prefix}_start`, `{prefix}_end`,
  `{prefix}_start_position`, `{prefix}_end_position`, `{prefix}_interpolation`,
  `{prefix}_output_min`, `{prefix}_output_max`. 뒤 2개는 마스터의 Output Min/Max 를 구동한다.

### Sine Wave 모드
- 오브젝트가 `N`개일 때(인덱스 `i = 0 .. N-1`), 오브젝트마다 3개 노드를 생성한다:
  - `{prefix}_wave_{i+1}_ADD` (plusMinusAverage, operation=sum):
    `input1D[0]` ← 컨트롤러 driver attr, `input1D[1]` = **상수 `i`** (위상 offset; `_ADD1`=0 … `_ADD5`=4).
  - `{prefix}_wave_curve_{i+1}` (animCurveUU): 키 `(0,0)`·`(N-1,N-1)` Linear,
    **Pre/Post Infinity = Constant**(구간 밖 입력은 끝값 고정, 반복 안 함).
  - `{prefix}_wave_{i+1}_MAP` (remapValue): Input/Output Min·Max 와 value 커브(`value[0~2]`,
    3키 봉우리 `(0,0)(0.5,1)(1,0)` **spline** → 사인 반주기)를 **마스터에서 connect** 받는다.
    `inputValue` 만 각 노드 고유(앞단 animCurve 출력)이고, `outValue` 를 오브젝트 attr에 연결한다.
- **마스터 노드 `{prefix}_wave_master_MAP`** (remapValue, v01.02 신설): range 4개와 봉우리
  커브를 들고 모든 자식 `*_MAP` 의 Input Min/Max·Output Min/Max·`value[0~2]` 를 구동한다.
  마스터의 커브 키 하나만 옮겨도 전체 자식 커브가 같이 변한다.
- 마스터(→ 자식)의 **Input Max 는 항상 (오브젝트 수 - 1)** 이다. `_input_max` attr 기본값이
  오브젝트 수 - 1 로 고정되며, UI 의 In Max 입력은 무시된다(In Max 는 읽기 전용 자동값).
- 컨트롤러에 추가되는 제어 어트리뷰트(모두 double):
  - **Driver Attr** 이름(기본 `wave`) — 전체 위상을 미는 값.
  - `{prefix}_input_min`, `{prefix}_input_max`, `{prefix}_output_min`, `{prefix}_output_max` —
    **마스터** 노드의 Input Min / Input Max / Output Min / Output Max 에 **connect** 된다.
    즉 컨트롤러 → 마스터 → 자식 체인이라, 빌드 후 컨트롤러 값을 바꾸면 모든 remapValue 가
    동시에 반영된다(Output Max = 진폭). `_input_max` 의 빌드 기본값은 오브젝트 수 - 1 이다.
- 이 4개 attr 의 **기본값**은 UI 의 **Range**(In/Out Min·Max)에서 정한다. `In Max` 가 `0` 이하이면
  `{prefix}_input_max` 기본값은 자동으로 **오브젝트 개수 - 1**(`N-1`)이 된다.
- 메모: Pre/Post Infinity는 remapValue가 아니라 그 앞단 animCurve의 속성이다.

---

## 8. 로그 · 문제 해결

### 정상 로그 예시
```
--- Build Slerp Ramp ---
Listed 18 keyable attribute(s) from joint1.
Built: twist_master_ribbon_lerp_MAP | 5 joint(s) | attrs: rotateY

--- Build Sine Wave ---
Built sine wave: driver ctl.wave | 5 object(s) | range in[0.0,0.0] out[0.0,1.0] | attrs: translateY
```

### 경고/오류 메시지
- `[WARN] Nothing selected. ...` — Get 시 선택이 없음.
- `[WARN] Joints list is empty. ...` — List Attributes/Build 전에 조인트를 추가해야 함.
- `[WARN] Main Controller is empty. ...` — 컨트롤러 미설정.
- `[WARN] Controller not found in scene: <name>` — 입력한 컨트롤러가 씬에 없음.
- `[WARN] No attribute selected. ...` — 어트리뷰트를 선택하지 않음.
- `[WARN] Driver Attr name is empty.` — Sine Wave 빌드 시 Driver Attr 이름이 비어 있음.
- `[ERROR] Build failed: <error>` — pymel 노드 생성 중 오류(이름 오타, 존재하지 않는 어트리뷰트 등).

### 자주 겪는 문제
- **List Attributes에 아무것도 안 뜸** → Joints 리스트가 비었거나 첫 오브젝트가 씬에 없음.
- **Build해도 아무 변화 없음** → 로그의 `[WARN]` 확인(컨트롤러/조인트/어트리뷰트/Prefix 중 빠진 것).
- **어트리뷰트 연결 실패** → 선택한 어트리뷰트가 조인트들에 모두 존재하는지 확인.
