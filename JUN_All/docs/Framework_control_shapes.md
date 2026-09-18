---
title: Framework 공용 데이터 — control_shapes (컨트롤러 셰이프 라이브러리)
aliases: [control_shapes, 컨트롤러 셰이프, 컨트롤 커브 라이브러리, bs_controls]
tags: [framework, maya-python, control, curve, rig]
updated: 2026-09-18
---

# `Framework.core.control_shapes` — 컨트롤러 커브 셰이프 34종

- 데이터: `JUN_All/Framework/rules/control_shapes.json` (**모든 툴이 이 파일 하나를 공유**)
- 코드: `JUN_All/Framework/core/control_shapes.py`
- 첫 사용처: [`A00400_CurveTool`](A00400_CurveTool.md) `Create > Controls` (v01.15)

`mirror_tokens` 와 같은 규칙이다 — **데이터는 `Framework/rules/`, 읽는 코드는 `Framework/core/`.**

---

## 1. 왜 툴 밖에 두나

셰이프 원본은 Brandon Schaal 의 **`bs_controls.py`**(Control Curves Tool)가 클래스 변수로 들고 있던
`controlNames` + `cvTuples` 다. 그대로 `A00400_CurveTool` 안에 넣을 수도 있었지만, **컨트롤러 셰이프는
한 툴의 것이 아니다** — `A00460_ControllerTool` 의 FK 컨트롤, `A00130_ControlRig_V02` 의 케이지,
`A00145_RigConnect` 어디서든 같은 라이브러리를 쓰는 편이 맞다.

`dev/build_release.py` 는 **툴 하나 + Framework** 를 릴리스로 복사하므로, Framework 에 두면 어느 툴을
릴리스해도 따라간다. (반대로 다른 툴의 `app/core` 를 참조하면 릴리스에서 곧바로 깨진다.)

---

## 2. 데이터 (`control_shapes.json`)

```json
{
 "names": ["Circle", "Half Circle", "Square", ... ],       // 메뉴 순서 그대로 34개
 "shapes": { "Square": [[x, y, z], ...], ... }             // degree 1 커브의 CV 좌표
}
```

- **`names` 34개, `shapes` 33개** — `Circle` 만 좌표가 없다. 그것은 CV 를 찍는 대신
  `cmds.circle(degree=3, radius=2, normal=(0,1,0))` 로 그리는 3차 커브이기 때문이다.
- 나머지 33종은 전부 **degree 1 커브 하나**다. 복잡해 보이는 셰이프(구 · 화살표 · 기어)도
  **한 붓 그리기**로 만들어 셰이프 노드가 하나다 — 컨트롤러는 셰이프가 적을수록 다루기 쉽다.
- **`Gear` 만 예외**로 톱니(degree 1) + 안쪽 원, 셰이프 2개다(원본과 같다).
- 좌표는 **원본 값 그대로** 담았다. 처음에 소수점 6자리로 반올림해 넣었더니 원본과 CV 가
  `1e-5` 수준으로 어긋났다 — 검증에서 8개 셰이프가 걸렸다. 라이브러리는 **원본과 같아야** 한다.

셰이프를 추가하려면 `names` 에 이름을 넣고 `shapes` 에 같은 키로 좌표 목록을 넣는다. 좌표는
degree 1 커브의 CV 를 전부 고르고

```python
sel = cmds.ls(sl=True)
trans = cmds.xform(sel, q=True, t=True)
print([tuple(trans[i:i+3]) for i in range(0, len(trans), 3)])
```

로 뽑는다(원본 문서의 방법 그대로).

---

## 3. API

```python
from Framework.core import control_shapes

control_shapes.names()            # ['Circle', 'Half Circle', ... ]  (34)
control_shapes.points("Square")   # [(x, y, z), ...]  - Circle 은 빈 목록
control_shapes.has("Square")      # 이 이름으로 그릴 수 있나
control_shapes.build("Square", thickness=2.0, curve_name="hand_ctl")   # 씬에 그린다
control_shapes.json_path()        # 데이터 파일 경로
```

- `build()` 는 만든 **트랜스폼 이름**을 돌려준다. 모르는 이름이면 `ValueError`.
- `thickness` 는 `1.0` 을 넘을 때만 셰이프의 `lineWidth` 에 들어간다(뷰포트 표시 굵기 — 형상 불변).
- **`build()` 안에서만 `maya.cmds` 를 import 한다.** 이름·좌표를 읽는 것은 순수 파이썬이라
  **마야 없이도 데이터 검사가 된다.**
- 파일은 66KB 라 한 번 읽고 캐시한다. json 을 고쳤으면 `load(reload_data=True)`.
- 파일이 없거나 깨져도 **예외를 던지지 않는다** — 빈 목록 + 경고 문자열을 돌려준다(`load()` 세 번째 값).

---

## 4. 셰이프 34종

`Circle` · `Half Circle` · `Square` · `Triangle` · `Sphere` · `Half Sphere` · `Box` · `Pyramid` ·
`Diamond` · `Circle Pin` · `Square Pin` · `Sphere Pin` · `Circle Dumbbell` · `Square Dumbbell` ·
`Sphere Dumbbell` · `Cross` · `Cross Thin` · `Locator` · `Four Arrows` · `Four Arrows Thin` ·
`Curved Four Arrows` · `Curved Four Arrows Thin` · `Two Arrows` · `Two Arrows Thin` ·
`Curved Two Arrows` · `Curved Two Arrows Thin` · `One Arrow` · `One Arrow Thin` ·
`Circle One Arrow` · `Circle Two Arrows` · `Circle Three Arrows` · `Circle Four Arrows` ·
`Sphere Four Arrows` · `Gear`

---

## 5. 검증 (mayapy 2024)

**원본 `bs_controls` 와 34종 전부 CV 단위로 일치**(같은 씬에서 둘 다 그려 월드 좌표 비교) ·
이름 순서 동일 · `Circle` 만 좌표 없음 · `Gear` 는 셰이프 2개 · `thickness` → `lineWidth` ·
모르는 이름은 `ValueError`.
