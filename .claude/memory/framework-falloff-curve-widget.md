---
name: framework-falloff-curve-widget
description: Framework 공용 falloff 커브 편집기(MOD_falloffCurve_qt_v01 + core/falloff_curve) — 커브·Interpolation·Presets UI 는 새로 만들지 말고 이걸 쓴다
metadata: 
  node_type: memory
  type: project
  originSessionId: fb4a8dc4-f323-4f72-8ea8-9bbb59d15251
  modified: 2026-09-09T01:29:49.321Z
---

**`Framework/qt/MOD_falloffCurve_qt_v01.py` → `JUN_mod_falloffCurve_qt`**,
모델 **`Framework/core/falloff_curve.py`** (Qt·maya 비의존). 2026-09-09 에
`A00275_skinTool_V01` 의 Expand Bind Falloff curve 에서 승격
([[wip-a00275-expand-bind]] → [[wip-a00410-secondarymotion]] 이 같은 UI 를 요구).
문서: `docs/Framework_MOD_falloffCurve_qt.md`.

```python
from Framework.qt import JUN_mod_falloffCurve_qt as JUN_falloff_qt
from Framework.core import falloff_curve

panel = JUN_falloff_qt.JUN_mod_falloffCurvePanel_qt_v01(title="Falloff curve")  # 탭 안
dlg = JUN_falloff_qt.JUN_mod_falloffCurveDialog_qt_v01(                        # 팝업(비모달)
    self, title="Stiffness curve",
    points=falloff_curve.FLAT_POINTS, reset_points=falloff_curve.FLAT_POINTS,
    info="X = chain root -> tip.   Y multiplies Stiffness.")
pts, interp = dlg.points(), dlg.interpolation()   # 세 클래스 모두 같은 API + changed 시그널
```

**How to apply:**
- 클래스 셋: **캔버스**(`JUN_mod_falloffCurve_qt_v01`) / **패널**(+Interpolation 콤보 +
  Curve presets 버튼) / **비모달 팝업**(+Reset·Close). 셋 다 `points()/interpolation()/
  set_curve()/evaluate(t)/is_flat()` + `changed` 로 같은 API 다.
- **★ 패널을 쓰면 콤보 동기화를 툴이 안 해도 된다.** 프리셋은 **보간 방식까지** 바꾸므로
  콤보를 맞춰 두지 않으면 화면 표기와 계산이 어긋난다(A00275 가 손으로 하던 일).
  `set_curve(points, interp)` 로 묶어 바꾸면 `changed` 도 **한 번만** 나간다.
- **포인트 값을 숫자로**: 캔버스에서 포인트를 고르면(`selectionChanged`) 패널의
  `Point [2/4] X [] Y []` 칸으로 **가로·세로축을 실수 입력**. API 는 `selected_index()` /
  `set_selected_index()` / `set_point(i, x=, y=)` / `x_bounds(i)` / `is_end_point(i)`.
  **★ 범위 규칙을 드래그와 한 곳에서 공유**해야 한다(양 끝 x 고정 → X 칸 비활성, 가운데는
  이웃 사이). **클램프된 값은 칸에 되돌려 준다** — 안 그러면 "왜 안 들어가지" 가 된다.
  칸↔커브 되먹임은 `_updating` 빗장 + `set_point` 이 같은 값이면 `changed` 를 안 내는 것으로 끊는다.
- **탄젠트(Bezier)**: `INTERP_BEZIER` 에서만 포인트마다 핸들이 붙는다(다른 보간은 안 본다 →
  **옛 커브 무회귀**). 탄젠트는 포인트와 나란한 **별도 인자**라 `evaluate(points, interp, t)`
  옛 호출도 그대로. UI 는 `Tangent` 줄(Break · In/Out 각도 · 길이 · Auto).
  - **★ 각도는 '핸들이 뻗는 방향' 으로** 잰다(in 은 -x 쪽) → **끊지 않으면 두 각도가 같다**
    (화면의 한 직선과 숫자가 어긋나지 않는다). 길이는 끊지 않아도 좌우 따로.
  - **★ 제어점 x 를 `x0<=cx0<=cx1<=x1` 로 가둬** 커브를 함수로 유지(핸들을 최대로 빼도 안 접힘).
  - **★ 포인트와 탄젠트는 `normalize_curve` 로 같이 정렬**한다. `normalize_points` 만 쓰면
    정렬 뒤 **짝이 조용히 어긋난다**.
  - 함정 2개(테스트가 잡음): x→t 이분법이라 y 는 **1e-7 수준**까지만 정확 · **y=1 에서 위로 민
    탄젠트는 clamp01 에 잘려 여전히 평평**하다(`is_flat` 검증은 아래로 밀 것).
  - 비용: 25,000회 평가 0.29s(linear 0.05s) — 6배쯤.
- **가로축의 뜻은 툴이 정한다**(위젯은 모른다) — A00275 는 거리/반경, A00410 은 체인 루트→팁.
  `tooltip=` / 팝업 `info=` 로 축의 뜻을 적어 준다.
- 커브가 **배수**인 툴은 `FLAT_POINTS`(전 구간 1.0)로 시작하고, `is_flat()` 이면 계산에 아예
  안 넘긴다(`None`) → "안 건드린 상태 = 예전과 같은 코드 경로" 가 보장되고, 버튼 표식
  (`Graph *`) 판정도 같은 함수 하나로 끝난다.
- 헤드리스 검증 가능: QApplication 을 `standalone.initialize()` 앞에 두면
  **A00275 MainWindow 까지 생성된다**([[qapplication-before-maya-standalone]] 의 순서만 지키면
  Qt+cmds 조합도 뜬다 — 예전 메모의 "MainWindow 는 헤드리스 생성 불가" 는 순서 문제였다).

관련: [[framework-progress-widget]], [[wip-a00275-expand-bind]], [[wip-a00410-secondarymotion]],
[[prefer-pyside-for-new-tools]], [[mayapy-headless-verify]]
