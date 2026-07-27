---
title: A00390_WindTool
aliases: [WindTool, 바람툴, wind sway]
tags: [maya-python, tool, animation, keyframe]
updated: 2026-07-27
---

# A00390_WindTool

본 체인에 **싸인 주기함수 키프레임**을 찍어 *바람에 일렁이는* 간단한 애니메이션을 만드는
in-Maya PySide 툴. 조인트마다 위상만 어긋난 같은 파형을 넣어 체인이 순차적으로 흔들리게 한다.

> [!info] 아키텍처
> arch (A) in-Maya PySide. 공용 위젯 `JUN_mod_tsl_qt`(TSL) + `JUN_mod_timeRange_qt`(Start/End) 사용.
> 로직은 `app/core/wind_manager.py`(maya.cmds, UI 비의존), UI 는 `app/ui/main_window.py`.

---

## 파형 정의

각 조인트 `i`(리스트 순번 0,1,2…)의 선택 축 값:

```
value(t) = amplitude * sin( 2π * (t - i*offset) / period )
```

- **키는 1/4 주기마다** 찍는다 → `0, +amplitude, 0, -amplitude, 0 …`(격자 간격 `quarter = period/4`).
- 키 사이는 **spline 탄젠트**로 보간되어 싸인과 유사한 파형이 된다(피크에서 평평, 0 교차에서 급).
- `quarter` 가 소수면(예: `period=10 → 2.5`) **소수 프레임에 키**가 찍힌다.
- 조인트 순번 `i` 는 위상을 `i*offset` 프레임만큼 미룬다 → 체인이 계단식으로 흔들린다.
  A00110 의 Stagger offset 과 달리 **offset 은 실수 프레임**을 쓸 수 있다.

### 예시

`rotateX`, Start=0, End=100, Period=12, Amplitude=40, Offset=10:

| 조인트 | 위상 지연 | 키(값) |
|--------|-----------|--------|
| `jnt_01` (i=0) | 0f | 0→0, 3→40, 6→0, 9→-40, 12→0 … (매 12프레임 반복) |
| `jnt_02` (i=1) | 10f | 같은 파형이 +10f 밀림 (13→40 …) |
| `jnt_03` (i=2) | 20f | 같은 파형이 +20f 밀림 (23→40 …) |

`period=10` 이면 2.5f(최대), 7.5f(최소)에 키가 찍힌다(소수 프레임).

---

## 사용법

1. 씬에서 본 체인을 선택하고 **Select Joints** → TSL 에 리스트업(순서 = offset 순번, Up/Down 재정렬).
2. **Axis** 로 축 선택(rotateX/Y/Z · translateX/Y/Z).
3. **Start / End** 로 키를 만들 구간 지정(Get Current / Get Sel Range 지원).
4. **Period / Amplitude / Offset** 입력(모두 소수 허용).
5. **Clear existing keys in range**(기본 on) — 재적용 시 구간의 해당 축 키를 먼저 지운다.
6. **Apply Wind Keys** — 전체가 한 번의 undo 로 묶인다.

---

## 설치 / 실행

- **설치**: `__dragDrop_A00390.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 생성.
- **실행**: 셸프 버튼 또는 `tools.A00390_WindTool.run(True)`.

---

## 참고 (mayapy 검증)

- Maya 는 **회전(각도) 키를 내부적으로 라디안으로 저장**했다가 도로 변환하므로, 30° 같은 값은
  `29.999999999999996` 처럼 미세 오차로 돌아올 수 있다(도↔라디안 왕복). 표시·동작상 30 과 동일하며
  회전 키를 찍는 모든 툴에 공통이다.
- 키 시간은 `round(shift + n*quarter, 5)` 로 부동소수 잡음을 정리한다.
- `_SIN_QUARTER = (0, 1, 0, -1)` 를 `n % 4` 로 인덱싱 — 파이썬 모듈로가 음의 격자에도 맞으므로
  구간이 0 보다 앞/뒤여도 파형이 이어진다.
