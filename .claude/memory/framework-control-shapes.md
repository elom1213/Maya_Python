---
name: framework-control-shapes
description: "컨트롤러 커브 셰이프 34종 공용 라이브러리 — Framework/rules/control_shapes.json + Framework.core.control_shapes (bs_controls 이식). 좌표는 반올림하지 말 것"
metadata:
  node_type: memory
  type: reference
---

`Framework/rules/control_shapes.json` + `Framework/core/control_shapes.py` (2026-09-18 신설,
첫 사용처 [[wip-a00400-controls-tab]]). 문서 `JUN_All/docs/Framework_control_shapes.md`.
`mirror_tokens` 와 **같은 자리·같은 규칙** — 데이터는 `Framework/rules/`, 읽는 코드는 `Framework/core/`.

원본은 Brandon Schaal 의 `bs_controls.py`(마야 `prefs/scripts`) 클래스 변수 `controlNames` + `cvTuples`.

**Why:** 컨트롤러 셰이프는 A00400 만의 것이 아니다(A00460 · A00130 · A00145 도 컨트롤러를 만든다).
`dev/build_release.py` 는 **툴 하나 + Framework** 만 복사하므로 Framework 에 둬야 어느 릴리스에도 따라간다.
사용자가 "특정 툴만 쓰지 않도록" 명시 요청(2026-09-18).

**How to apply:**
- API: `names()`(34, 순서 = 메뉴) · `points(name)` · `has(name)` · `build(name, thickness, curve_name)` · `load(reload_data=)`.
- **`build()` 안에서만 maya.cmds 를 import** 한다 — 데이터 검사는 마야 없이도 된다.
- `Circle` 만 CV 가 없다(`cmds.circle` 3차 커브), `Gear` 만 셰이프 2개(톱니 + 원). 나머지 32종은 degree 1 하나.
- **좌표를 반올림하지 말 것** — 6자리로 줄였더니 8개 셰이프가 원본과 `1e-5` 어긋났다(검증에서 잡음).
- 파일 없음/파싱 실패는 예외가 아니라 **빈 목록 + 경고 문자열**.
