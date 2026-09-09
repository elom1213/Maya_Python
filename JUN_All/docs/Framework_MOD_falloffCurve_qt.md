---
title: Framework 공용 위젯 — MOD_falloffCurve_qt (Falloff 커브 편집기)
aliases: [JUN_mod_falloffCurve_qt, falloff curve, 커브 편집기, Curve presets]
tags: [framework, qt, widget, maya-python]
updated: 2026-09-09
---

# `JUN_mod_falloffCurve_qt_v01` — falloff 커브 편집기

`JUN_All/Framework/qt/MOD_falloffCurve_qt_v01.py` (모델: `JUN_All/Framework/core/falloff_curve.py`)

마야 Soft Select / Paint 툴의 **Falloff curve** 를 PySide 로 재현한 위젯.
`gradientControlNoAttr` 은 cmds 전용 컨트롤이라 PySide 창에 그대로 못 쓴다.

`A00275_skinTool_V01` 의 Expand 탭에서 쓰던 것을 2026-09-09 에 승격했다
(`A00410_SecondaryMotion` 이 파라미터 커브로 같은 UI 를 필요로 했다).

---

## 1. 클래스 셋

| 클래스 | 무엇 | 언제 |
|--------|------|------|
| `JUN_mod_falloffCurve_qt_v01` | 커브 캔버스(그리기 + 편집) | 커브만 필요할 때 |
| `JUN_mod_falloffCurvePanel_qt_v01` | 캔버스 + **Interpolation** 콤보 + **Curve presets** 버튼 | 탭 안에 박아 쓸 때 |
| `JUN_mod_falloffCurveDialog_qt_v01` | 패널을 담은 **비모달 팝업**(+ Reset / Close) | 버튼으로 띄울 때 |

세 클래스 모두 `points()` / `interpolation()` / `set_curve()` / `evaluate(t)` / `is_flat()` 과
`changed` 시그널을 같은 이름으로 낸다 — 호출부는 어느 것을 쓰든 코드가 같다.

---

## 2. 쓰는 법

```python
from Framework.qt import JUN_mod_falloffCurve_qt as JUN_falloff_qt
from Framework.core import falloff_curve

# (a) 탭 안에 박기 — A00275 Expand Bind
self.eb_curve = JUN_falloff_qt.JUN_mod_falloffCurvePanel_qt_v01(title="Falloff curve")
self.eb_curve.changed.connect(self._preview)
layout.addWidget(self.eb_curve)
pts, interp = self.eb_curve.points(), self.eb_curve.interpolation()

# (b) 버튼으로 띄우는 팝업 — A00410 파라미터 커브(값에 **곱해지는** 배수)
dlg = JUN_falloff_qt.JUN_mod_falloffCurveDialog_qt_v01(
    self, title="Stiffness curve",
    points=falloff_curve.FLAT_POINTS, interp=falloff_curve.FLAT_INTERP,
    reset_points=falloff_curve.FLAT_POINTS,
    info="X = chain root -> tip.   Y multiplies Stiffness.")
dlg.changed.connect(self._schedule)
dlg.popup()          # 비모달 — 띄워 둔 채로 슬라이더를 만질 수 있다
```

편집 조작은 마야와 같다 — **드래그**로 모양 조절, **빈 곳 더블클릭**으로 포인트 추가,
**우클릭**으로 삭제. 양 끝 포인트는 x 가 고정(0 / 1)이고 세로로만 움직인다.

---

## 3. 모델은 따로 산다 — `Framework.core.falloff_curve`

커브 값 계산은 **Qt 도 maya 도 모르는 순수 파이썬 모듈**이 한다.
위젯(그리기)과 툴의 계산 로직이 **같은 함수**를 써야 화면 모양과 결과가 어긋나지 않는다.

```python
from Framework.core import falloff_curve

falloff_curve.evaluate(points, interp, t)     # t(0~1) 에서의 값(0~1)
falloff_curve.sample(points, interp, 64)      # [(t, value), ...] 그리기용
falloff_curve.normalize_points(points)        # x 오름차순 + 0~1 로 정리
falloff_curve.preset_points("Ease In")        # (포인트, 보간)
falloff_curve.is_flat(points)                 # 처음부터 끝까지 1.0 인가
```

| 상수 | 값 |
|------|-----|
| `INTERPOLATIONS` | `none` / `linear` / `smooth` / `spline` (마야 gradient control 과 같은 의미) |
| `PRESETS` | Linear · Smooth · Ease In · Ease Out · Spike · **Solid**(= 평평한 1.0) |
| `DEFAULT_POINTS` | `[(0,1), (1,0)]` — 오른쪽으로 갈수록 0 (감쇠용 기본) |
| `FLAT_POINTS` | `[(0,1), (1,1)]` — **곱해도 아무것도 안 바뀌는** 커브 |

> 커브가 **배수**인 툴(A00410)은 `FLAT_POINTS` 로 시작하고, `is_flat()` 이면 계산에 아예
> 넘기지 않는다 — 그래야 "커브를 안 건드린 상태 = 예전과 같은 계산" 이 보장된다.

---

## 4. 축의 뜻은 툴이 정한다

가로축은 **0~1 로 정규화된 무엇**이고, 그 뜻은 툴마다 다르다. 위젯은 모른다.

| 툴 | 가로축 | 세로축 |
|----|--------|--------|
| `A00275_skinTool_V01` Expand Bind | 거리 / 반경 | 웨이트 비중 |
| `A00410_SecondaryMotion` | 체인 루트 → 팁 | Stiffness / Damping / World Damp 에 곱할 배수 |

그래서 `tooltip=` 으로 축의 뜻을 설명하는 문장을 넘길 수 있다(팝업은 `info=` 로 창 안에 한 줄).

---

## 5. 패널이 대신해 주는 것 — 콤보 동기화

**프리셋은 보간 방식까지 바꾼다.** 그래서 커브가 어느 경로로 바뀌든 `Interpolation` 콤보를
맞춰 두지 않으면 **화면 표기와 실제 계산이 어긋난다**. 승격 전 A00275 는 이 동기화를
`_sync_eb_interp_combo()` 로 손수 했는데, 이제 패널이 맡는다(`set_curve()` 로 포인트와 보간을
한 번에 바꿔 `changed` 도 한 번만 나간다).

---

## 6. 쓰고 있는 툴

| 툴 | 어디에 |
|----|--------|
| `A00275_skinTool_V01` | Bind > Expand Bind — Falloff curve (패널) |
| `A00410_SecondaryMotion` | Physics — Stiffness / Damping / World Damp 의 `Graph` 팝업 |
