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

- 키는 1/4 주기마다 계산하되(격자 간격 `quarter = period/4`), 기본적으로 **구간 내부의 0 교차 키는
  빼고 극값(±amplitude)만** 남긴다(v01.01~). 극값 사이 0값 키가 있으면 spline 커브가 그 지점에서
  평평/각지게 되기 때문. 대신 구간 **양끝(Start/End)** 에는 그 지점의 실제 싸인 값으로 **앵커 키**를 둬
  커브가 구간 밖으로 흘러가지 않게 한다. (`Keep zero-crossing keys` 를 켜면 0 교차 키까지 모두 찍는다.)
- 키 사이는 **spline 탄젠트**로 보간되어 깔끔한 싸인 파형이 된다.
- `quarter` 가 소수면(예: `period=10 → 2.5`) **소수 프레임에 키**가 찍힌다.
- 조인트 순번 `i` 는 위상을 `i*offset` 프레임만큼 미룬다 → 체인이 계단식으로 흔들린다.
  A00110 의 Stagger offset 과 달리 **offset 은 실수 프레임**을 쓸 수 있다.

### 모드 (v01.02~)

| 모드 | 순번(i)의 의미 | 대상 |
|------|----------------|------|
| **Bone Chain**(기본) | 리스트 순서 | 리스트업한 조인트들 **자체** (하나의 체인) |
| **Bone Root** | root 로부터의 **깊이(depth)** | 리스트업한 각 조인트를 **루트로 보고 그 자손 조인트 전부** |

- **Bone Root**: `jnt_01, jnt_02, jnt_03` 을 리스트업하면 각각을 체인 루트로 가정하고, 그 조인트 +
  모든 자손 조인트에 Bone Chain 과 같은 파형을 반복 적용한다. offset 순번은 **루트마다 리셋**(root=0,
  자식=1, …)되고, 분기 체인에서 **같은 깊이의 형제는 같은 offset** 을 갖는다. 같은 조인트가 여러
  루트에서 겹쳐 잡히면 처음 것만 쓴다(중복 키 방지).

### 예시

`rotateX`, Start=0, End=100, Period=12, Amplitude=40, Offset=10:

| 조인트 | 위상 지연 | 키(값) |
|--------|-----------|--------|
| `jnt_01` (i=0) | 0f | 3→40, 9→-40, 15→40 … (극값만, 매 12프레임 반복) + 양끝 앵커(0, 100) |
| `jnt_02` (i=1) | 10f | 같은 파형이 +10f 밀림 (13→40 …) + 양끝 앵커 |
| `jnt_03` (i=2) | 20f | 같은 파형이 +20f 밀림 (23→40 …) + 양끝 앵커 |

내부 0 교차 키(6·12·18…f)는 제거되고 극값 사이는 spline 으로 보간된다.
`period=10` 이면 2.5f(최대), 7.5f(최소)에 키가 찍힌다(소수 프레임).

### 출력 (Curve / Node, v01.03~)

| 출력 | 방식 | 특징 |
|------|------|------|
| **Curve**(기본) | 조인트에 **키를 굽는다** | 씬 재생으로 재생. 기존 동작. |
| **Node** | **드라이버 null + 노드망** | 파형을 **실시간** 재현. 어트리뷰트로 편집. |

- **Node** 는 `windPeriod / windAmplitude / windOffset / windSpeed` 어트리뷰트를 가진 **null(로케이터)
  드라이버**를 만들고, 노드망으로 각 조인트를 구동한다:
  `value = windAmplitude · sineLUT( (windPhaseTime − i·windOffset) / windPeriod )`.
  드라이버 파라미터를 바꾸면 애니메이션이 **즉시 갱신**된다.
- **재생 속도 = `windSpeed`(값 = 속도)**. 1=보통, 2=2배, 0=정지. **상수로 둬도 계속 재생**된다.
  - **값이든 키든 자동·실시간**(v01.07~): `windPhaseTime` 을 **`∫windSpeed dt` 적분 표현식**(MEL
    expression)으로 라이브 계산한다. windSpeed 를 **값으로 바꾸든 키로 애니메이션하든 버튼 없이 즉시
    반영**되고, 속도가 변해도 **위상이 단조 전진해 역행(찰랑임 뒤집힘)이 없다**. windSpeed=1 상수면
    windPhaseTime=frame(curve 모드와 같은 위상).
  - ⚠️ 왜 적분인가: 속도는 시간의 적분(`phase=∫speed dt`)이다. 단순 곱셈 `time×speed` 는 가변 속도에서
    위상이 역행하고(v01.03/06), `windTime` 시간값(v01.04)은 상수로 두면 멈춘다. 적분 표현식이 둘 다 해결.
  - Speed 입력은 windSpeed 의 **초기값**을 정한다.
  - 성능: 표현식이 매 프레임 startFrame~현재프레임을 훑어 적분한다(구간이 매우 길고 드라이버가 많으면
    다소 무거울 수 있음).
- 드라이버 개수: **Bone Chain → 1개**, **Bone Root → 루트 수만큼**.
- sin 은 정규화 싸인 `animCurveUU` LUT(한 주기, 무한 반복 cycle)로 만들어 Maya 2023 의 네이티브 sin 노드
  부재를 피한다(A00170 Remap Value 아이디어 응용). 다시 Build 하면 새 드라이버가 생기고 이전 연결은
  끊긴다(이전 드라이버는 수동 삭제 또는 undo).

---

## 사용법

1. 씬에서 조인트를 선택하고 **Select Joints** → TSL 에 리스트업(Chain 모드는 순서 = offset 순번, Up/Down 재정렬).
2. **Mode** 선택 — **Bone Chain**(리스트 = 한 체인) 또는 **Bone Root**(각 항목 = 체인 루트, 자손까지).
3. **Output** 선택 — **Curve**(키 굽기) 또는 **Node**(드라이버 노드망 실시간).
4. **Axis** 로 축 선택(rotateX/Y/Z · translateX/Y/Z).
5. **Start / End** (Curve 전용) 로 키를 만들 구간 지정(Get Current / Get Sel Range 지원).
6. **Period / Amplitude / Offset** 입력(모두 소수 허용). **Speed** 는 Node 전용(windSpeed 초기값).
7. (Curve) **Clear existing keys in range**(기본 on) — 재적용 시 구간의 해당 축 키를 먼저 지운다.
8. **Apply Wind Keys**(Curve) / **Build Wind Node**(Node) — 전체가 한 번의 undo 로 묶인다.
9. (Node) 드라이버의 **windSpeed** 를 값으로 바꾸거나 키로 애니메이션하면 재생 속도가 **자동 반영**된다.

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
