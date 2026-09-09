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
| `JUN_mod_falloffCurvePanel_qt_v01` | 캔버스 + **Point(X/Y 숫자 입력)** + **Interpolation** 콤보 + **Curve presets** 버튼 | 탭 안에 박아 쓸 때 |
| `JUN_mod_falloffCurveDialog_qt_v01` | 패널을 담은 **비모달 팝업**(+ Reset / Close) | 버튼으로 띄울 때 |

세 클래스 모두 `points()` / `tangents()` / `interpolation()` / `set_curve()` / `evaluate(t)` /
`is_flat()` / `selected_index()` / `set_selected_index()` / `set_point()` 과
`changed` · `selectionChanged` 시그널을 같은 이름으로 낸다 — 호출부는 어느 것을 쓰든 코드가 같다.

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

## 2.1 `Point` — 고른 포인트를 **숫자로** 정하기

포인트를 클릭해 고르면(고른 포인트는 채워져서 크게 그려진다) 아래 `Point` 줄에서
**가로축(X) · 세로축(Y) 값을 실수로 직접 입력**할 수 있다. 입력칸은 축마다 하나씩 **두 개**다.

```
Point  [2 / 4]   X [0.250]   Y [0.900]
```

- 드래그로는 "정확히 0.1" 을 맞출 수 없다. 값이 결과에 그대로 곱해지는 툴
  (`A00410` 의 파라미터 배수)에서는 숫자 입력이 사실상 본길이다.
- **범위 규칙은 드래그와 완전히 같다** — 양 끝 포인트는 x 가 0 / 1 로 고정이라 **X 칸이
  꺼지고**(세로로만 움직인다), 가운데 포인트는 이웃을 넘지 못하게 X 범위가 이웃 사이로 좁혀진다.
  클램프된 값은 **칸에 되돌아온다**(왜 안 들어가는지 화면에서 보인다).
- 아무것도 안 골랐으면 두 칸 다 회색으로 꺼진다 — "비활성인데 값은 쓰인다" 는 상태를 만들지 않는다.
- 드래그·프리셋·더블클릭 추가 등 **어느 경로로 커브가 바뀌든 칸이 따라온다.** 빈 곳에
  더블클릭해 만든 포인트는 바로 고른 상태가 되어 곧장 숫자로 다듬을 수 있다.
- `show_point_fields=False` 로 줄을 뺄 수 있고, `decimals=` 로 소수 자릿수를 정한다.

> 스핀박스는 `setKeyboardTracking(False)` 다 — 값을 되쓰는 칸이라 타이핑 중간값을 받으면
> `0.1` 을 치는 도중 `0.100` 으로 잘린다([[qdoublespinbox-keyboard-tracking]] 과 같은 이유).

코드로도 같은 일을 한다.

```python
panel.set_selected_index(1)               # 두 번째 포인트를 고르고
panel.set_point(1, x=1.0, y=0.1)          # 정확한 값으로 (범위는 알아서 클램프)
panel.selected_point()                    # -> (x, y) 또는 None
```

---

## 2.2 `Bezier` — 포인트 사이를 곡선으로 (탄젠트)

`Interpolation` 을 **Bezier** 로 두면 포인트마다 **탄젠트 핸들**이 붙고 구간이 3차 베지어가 된다.
나머지 보간(None/Linear/Smooth/Spline)은 탄젠트를 아예 보지 않으므로 **예전 커브는 그대로**다.

```
Tangent  [ ] Break   [Auto]
In    Angle [  -30.0 deg ]   Length [ 0.167 ]
Out   Angle [  -30.0 deg ]   Length [ 0.200 ]
```

- **드래그**: 고른 포인트의 핸들을 끌면 각도와 길이가 함께 바뀐다(핸들은 포인트보다 **먼저**
  잡힌다 — 겹쳤을 때 핸들을 집으려는 의도가 더 흔하다).
- **각도**는 양쪽 다 **자기 핸들이 뻗는 방향**으로 잰다(in 은 -x 쪽). 그래서 **끊지 않은 탄젠트는
  두 각도가 같다** — 화면의 "한 직선" 과 숫자가 어긋나지 않는다.
- **Break**: 좌우 핸들이 따로 논다. 끄면 out 각도를 기준으로 다시 한 직선에 맞춘다.
  화면에서도 **끊긴 핸들은 빈 원, 이어진 핸들은 채운 원**이다.
- **Length**: 핸들이 뻗는 거리(0~`MAX_TANGENT_LENGTH`=2.0). 길수록 커브를 세게 끈다.
  끊지 않아도 **길이는 좌우가 따로** 논다(마야의 weighted tangent 와 같은 감각).
- **Auto**: 그 포인트를 자동 탄젠트(이웃을 보고 매끄럽게)로 되돌린다. 새로 찍은 포인트와
  프리셋을 누른 뒤에는 전부 자동 탄젠트로 시작한다.

> **커브는 언제나 함수로 남는다.** 핸들을 아무리 길게 빼도 x 가 되돌아가지 않도록, 평가할 때
> 제어점 x 를 `x0 <= cx0 <= cx1 <= x1` 로 가둔다. 그래서 "한 x 에 값이 둘" 인 상태가 생기지 않는다.

```python
panel.set_selected_index(1)
panel.curve.set_tangent(1, falloff_curve.SIDE_OUT, angle=-30.0, length=0.2)
panel.curve.break_tangent(1, True)      # 좌우 독립
panel.curve.reset_tangent(1)            # 자동으로
pts, tans = panel.points(), panel.tangents()
falloff_curve.evaluate(pts, "bezier", 0.4, tans)
```

**비용**: 베지어는 x 로 t 를 되찾느라 이분법(24회)을 돈다 — 25,000회 평가에 **0.29s**
(linear 0.05s). Expand Bind 처럼 정점마다 부르는 곳에서도 체감되지 않지만, 다른 보간보다
6배쯤 비싸다는 것은 알고 쓰는 편이 좋다.

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

# 탄젠트(bezier 에서만 쓰인다)
falloff_curve.evaluate(points, "bezier", t, tangents)
falloff_curve.resolve_tangents(points, tangents)   # 자동 탄젠트까지 풀어 준 (in, out, broken)
falloff_curve.set_tangent(points, tangents, i, side, angle=, length=)
falloff_curve.break_tangent(points, tangents, i, True)
falloff_curve.reset_tangent(tangents, i)
falloff_curve.normalize_curve(points, tangents)    # **둘을 같이** 정렬(짝이 어긋나지 않게)
```

> `normalize_points` 는 x 로 정렬한다. 탄젠트를 따로 정렬하면 **짝이 어긋나므로**, 둘을 같이
> 다루는 곳은 반드시 `normalize_curve` 를 쓴다.

| 상수 | 값 |
|------|-----|
| `INTERPOLATIONS` | `none` / `linear` / `smooth` / `spline` (마야 gradient control 과 같은 의미) + **`bezier`**(탄젠트) |
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

두 툴 모두 커브를 저장/전달할 때 **탄젠트를 함께** 나른다
(`expand_bind(curve_tangents=...)`, A00410 의 `(points, interp, tangents)` spec).
