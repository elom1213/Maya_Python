# A00150_remapVal — Sine Wave 모드 추가 계획서

작성일: 2026-06-11 / 대상 툴: `JUN_All/tools/A00150_remapVal`

---

## 0. 한 줄 요약

기존 `build_slerp_ramp`(master remapValue 구동 방식)는 그대로 두고,
**오브젝트마다 `plusMinusAverage → animCurve → remapValue` 체인을 만들어 위상이 어긋난
사인 웨이브를 전파**하는 **새 빌드 모드("Sine Wave")** 를 추가한다.

참고 이미지(툴 폴더의 ref): `tools/A00150_remapVal/ref/ref_01.png`(노드 그래프),
`ref_02.png`(animCurve 세팅), `ref_03.png`(remapValue 세팅).

---

## 1. 만들 노드 구조

오브젝트가 `N`개, 인덱스 `i = 0 .. N-1` 라고 할 때, **오브젝트마다 3개 노드**를 만든다.
컨트롤러에는 **공통 driver attr 1개**를 추가한다.

### (공통) 컨트롤러 custom attr — 1개
- `controlObj`에 keyable `double` attr 추가. 이름은 **UI에서 사용자가 입력**(기본값 예: `wave`).
- 이 attr 값이 "시간/위상" 역할을 하며, 모든 `plusMinusAverage.input1D[0]`에 연결된다.
- 이미 존재하면 재사용(기존 `add_attr` 헬퍼 패턴 그대로).

### (오브젝트별 ①) plusMinusAverage — `{prefix}_wave_{i+1}_ADD`
- `operation = 1` (sum)
- `input1D[0]` ← `controlObj.{driverAttr}` (공통 driver, 위상 시작점)
- `input1D[1]` = **상수 `i`** (0, 1, 2, … N-1) → 오브젝트별 위상 offset
  - 예) `plusMinusAverage1.input1D[1] = 0`, `…5.input1D[1] = 4` (사용자 명시 사항)
- `output1D` → animCurve `.input`

### (오브젝트별 ②) animCurve(UU) — `{prefix}_wave_curve_{i+1}`
- 타입: `animCurveUU` (unitless 입력 → unitless 출력, 어트리뷰트로 구동되는 커브)
- 키: **`(0, 0)` 과 `(N-1, N-1)` 두 개**, In/Out Tangent = **Linear** (= `ref_02` 의 (0,0)(4,4))
- **Pre Infinity / Post Infinity = Constant** ← *사용자 지시* (`ref_02`는 Cycle이지만 Constant로 변경)
  - 동작 차이 메모: Constant는 입력이 `[0, N-1]` 구간을 벗어나면 **끝값에 고정**(반복 안 함).
    Cycle이었다면 구간이 무한 반복되어 웨이브가 계속 순환한다. 의도대로 Constant로 둔다.
- 연결: `plusMinusAverage.output1D` → `animCurve.input`,  `animCurve.output` → `remapValue.inputValue`

### (오브젝트별 ③) remapValue — `{prefix}_wave_{i+1}_MAP`
- `inputMin = 0`, `inputMax = N-1` (= `ref_03` 의 Input Min 0 / Max 4)
- value 커브 = **3키 봉우리(사인 반주기)**, interpolation = **spline(3)**:
  | index | Position | FloatValue | Interp |
  |-------|----------|-----------|--------|
  | 0 | 0.0 | 0.0 | spline |
  | 1 | 0.5 | 1.0 | spline |
  | 2 | 1.0 | 0.0 | spline |
- `outputMin = 0`, `outputMax = 1.0` (기본값. `ref_03`의 9.2는 사용자 수동 조정값 → 추후 UI 노출 검토, 1차는 1.0)
- 연결: `remapValue.outValue` → `object[i].{objAttr}` (선택한 모든 attr에 연결)

### 연결 요약 (1개 체인)
```
controlObj.{driverAttr} ─┐
                         ├─▶ plusMinusAverage(input1D[0,1]=driver, i) ─▶ animCurve(0..N-1, Constant)
i (상수) ────────────────┘                                                      │
                                                                                ▼
                                                   object[i].{objAttr} ◀── remapValue(in 0..N-1, peak curve)
```

---

## 2. 코드 변경 사항

### 2-1. `app/core/slerp_ramp.py` (로직 — pymel)
기존 `build_slerp_ramp` / `run_build`는 **수정하지 않음**. 아래 추가:

- `build_sine_wave(prefix, controlObj, oColl, driverAttr, objAttrs)`
  - 위 1장의 노드/연결을 생성. `add_attr` 헬퍼 재사용해 driver attr 추가.
  - animCurve: `pm.createNode('animCurveUU')` → `pm.setKeyframe(..., float=t, value=v)` →
    `pm.keyTangent(itt='linear', ott='linear')` → `pm.setInfinity(pri='constant', poi='constant')`.
  - remapValue 봉우리 커브는 `value[0/1/2].value_Position / value_FloatValue / value_Interp` 직접 set.
- `run_build_wave(prefix, controller_name, joint_names, driver_attr, obj_attrs)`
  - 문자열 → PyNode 변환 후 `build_sine_wave` 호출 (기존 `run_build`와 동일 패턴).
  - 반환: 생성 요약(예: driver attr 이름 또는 첫 remapValue 이름).

### 2-2. `app/core/__init__.py`
- `run_build_wave` 를 export 목록에 추가.

### 2-3. `app/ui/main_window.py` (UI — PySide)
- **Driver Attr 입력 행 추가**: `QLineEdit`("Driver Attr", 기본 `wave`) — 컨트롤러에 만들 custom attr 이름.
- **모드/실행 추가** (둘 중 택1, 권장: 두 번째 버튼):
  - 권장: 기존 `Build`(slerp) 옆에 **`Build Wave`** 버튼 추가 → `on_build_wave()` 슬롯.
  - 대안: 상단에 라디오("Slerp Ramp" / "Sine Wave")로 모드 선택 후 단일 Build 분기.
- `on_build_wave()`:
  - 입력 검증(prefix, controller 존재, joints 비어있지 않음, attrs 1개 이상, **driver attr 이름 비어있지 않음**).
  - `cmds.undoInfo(openChunk/closeChunk)`로 감싸 한 번에 undo (기존 `on_build` 패턴 동일).
  - `run_build_wave(...)` 호출 후 로그 출력. 모든 UI 문자열/로그는 **영어** (메모리 규칙).
- Help > About 텍스트에 Sine Wave 모드 사용법 한두 줄 추가.

### 2-4. 버전/문서
- `app/config/version.py` → `VERSION = "01.01"`, `LAST_UPDATE = "2026-06-11"`.
- `CHANGELOG.md` → v01.01 항목 추가(Sine Wave 모드 설명).

---

## 3. 작업 순서 (구현 시)

1. `slerp_ramp.py` 에 `build_sine_wave` + `run_build_wave` 추가.
2. `core/__init__.py` export 갱신.
3. `main_window.py` 에 Driver Attr 행 + `Build Wave` 버튼 + `on_build_wave` 슬롯 추가.
4. version / CHANGELOG / About 갱신.
5. Maya에서 검증: 조인트 N개 + 컨트롤러 선택 → 노드 그래프가 `ref_01`과 일치하는지,
   driver attr 슬라이드 시 위상차 웨이브가 전파되는지 확인.

---

## 4. 확인이 필요한(또는 가정으로 둔) 사항

- **remapValue Output Max**: 1차는 `1.0` 고정. `ref_03`의 `9.2`처럼 진폭 조절이 필요하면 UI 필드로 노출(추가 작업).
- **objAttr 다중 선택**: 기존 slerp와 동일하게 선택된 모든 attr에 `remapValue.outValue`를 연결한다고 가정.
- **노드 네이밍**: 위 `{prefix}_wave_*` 규칙은 제안값. `ref_01`의 `curve2_translateX`류 자동 이름 대신
  prefix 기반 고정 네이밍을 쓴다(중복/추적 용이).
- **animCurve 봉우리 vs remapValue 봉우리 역할 분담**: 봉우리(사인 반주기) 형상은 **remapValue** 가 담당,
  animCurve는 0..N-1 선형 + Constant(위상 매핑) 역할만 한다 (이미지 해석 기준).
