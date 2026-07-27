# Changelog — A00390_WindTool

## v01.08 (2026-07-27)
- **[Add] Node 드라이버마다 전체 위상 offset `windPhaseOffset` 어트리뷰트** — 노드(드라이버) 하나의
  **전체 타이밍**(그 드라이버가 구동하는 본들이 싸인의 어느 지점 값을 갖는지)을 미는 어트리뷰트.
  `base = windPhaseTime − windPhaseOffset` 로 그룹의 모든 조인트에 공용 적용된다. 드라이버마다 다른
  값을 주면 서로 다른 타이밍으로 찰랑인다(특히 **Bone Root** 모드에서 루트별로 다르게).
- **[Add] `Node Offset` 입력**(Node 전용) — 드라이버 순번 k 마다 `windPhaseOffset = k*값` 으로 초기화해,
  Root 모드에서 루트들이 **자동으로 서로 다른 타이밍**이 되게 한다(0 이면 기존처럼 동일). 이후 각
  드라이버의 windPhaseOffset 을 직접 조절해 개별 리타임 가능.

## v01.07 (2026-07-27)
- **[Fix] windSpeed 를 '키로 애니메이션'해도 버튼 없이 자동 반영 + 위상 역행 제거** — v01.06 의
  `time*windSpeed` 라이브 연결은 windSpeed 를 키로 애니(예: 0.25→0.05)하면 다시 위상이 역행해
  찰랑임이 뒤집혔다(속도는 시간의 적분인데 곱셈이라서). 이제 `windPhaseTime` 을 **`∫windSpeed dt`
  적분 표현식**(MEL expression, 프레임 사다리꼴 + 소수 프레임 잔여 구간)으로 라이브 계산한다.
  - windSpeed 를 **값으로 바꾸든 키로 애니메이션하든 버튼 없이 즉시 반영**되고, 속도가 변해도
    **위상이 단조 전진**해 역행이 없다. windSpeed=1 상수면 windPhaseTime=frame(curve 모드와 동일 위상).
- **[Remove] `Apply Speed` 버튼** — 표현식이 자동 처리하므로 더 이상 필요 없다(core `bake_speed` 제거).

## v01.06 (2026-07-27)
- **[Change] windSpeed 값 조절이 Apply Speed 버튼 없이 실시간 반영되도록** — `windPhaseTime` 을
  기본적으로 **`time * windSpeed` 라이브 연결**로 둔다. 상수 속도는 곱셈이 정확하므로, **windSpeed
  값만 바꿔도 재생 속도가 즉시 갱신**된다(1=보통, 2=2배, 0=정지).
- **Apply Speed 는 이제 '키로 조절한' 가변 속도 전용** — windSpeed 를 키로 주면 곱셈은 위상이
  역행하므로, Apply Speed 로 windSpeed 를 **적분**해 windPhaseTime 애님커브로 구우면(라이브 연결은
  끊김) 역행이 사라진다.

## v01.05 (2026-07-27)
- **[Change] Node 속도 제어를 '값=속도'인 `windSpeed` 로 되돌리되, 위상은 적분으로 굽는다** — v01.04 의
  `windTime`(시간값)은 상수로 두면 애니가 멈춰(값=시간이라) 기대와 달랐다. 이제 드라이버에 **`windSpeed`
  (값 = 재생 속도, 1=보통)** knob 을 두고, 내부 `windPhaseTime` = **windSpeed 의 시간 적분**으로 굽는다.
  - windSpeed 를 **상수로 둬도 계속 재생**(1=보통, 2=2배, 0=정지)되고, 값을 바꾸면 속도가 바뀐다.
  - windSpeed 를 **키로 조절**(예: 1→0.2→1)한 뒤 **Apply Speed** 버튼을 누르면 적분을 다시 구워
    반영한다 — 적분이라 **위상 역행(찰랑임 뒤집힘)이 없다**. (곱셈 time*speed 는 가변 속도에서 역행,
    windTime 시간값은 상수 정지 — 둘 다 해결.)
- **[Add] `Apply Speed` 버튼**(Node 전용) — 선택한(없으면 전체) 드라이버의 windSpeed 를 적분해 반영.

## v01.04 (2026-07-27)
- **[Fix] Node 모드 재생 속도 제어를 `windSpeed` 곱셈 → `windTime` 리타임으로 교체** — 예전엔
  위상 시계가 `time * windSpeed` 라, windSpeed 에 키를 줘 속도를 바꾸면(예: 1→0.2→1) 순간 주파수가
  `speed + time*(dspeed/dt)` 가 되어 **속도가 내려가는 구간에서 위상이 역행(찰랑임이 뒤집힘)**하고
  다시 1이 돼도 위상이 어긋났다. 이제 드라이버에 **`windTime`(위상 시계)** 어트리뷰트를 두고 씬 시간에
  따라 기울기=speed 로 키를 찍는다. **이 커브를 리타임하면 기울기 = 재생 속도**가 되어(시간 자체를
  워프 = 위상 적분) 느리게/빠르게가 **위상 역행 없이** 올바르게 재현된다. Speed 입력은 이제 windTime 의
  초기 기울기를 정한다. (mayapy: 곱셈 방식 19프레임 역행 → 리타임 0 역행 확인.)

## v01.03 (2026-07-27)
- **[Add] Curve / Node 출력 선택** —
  - **Curve**(기본, 기존 동작): 조인트에 키를 굽는다.
  - **Node**: `windPeriod / windAmplitude / windOffset / windSpeed` 어트리뷰트를 가진 **null(로케이터)
    드라이버** + 노드망으로 같은 파형을 **실시간** 재현한다. 어트리뷰트를 바꾸면 애니메이션이 즉시
    갱신되고, **windSpeed** 로 재생 속도를 (키로) 프레임마다 조절할 수 있다.
    - Bone Chain → 드라이버 **1개**, Bone Root → 루트 수만큼 드라이버.
    - sin 은 정규화 싸인 `animCurveUU` LUT(주기 1, `preInfinity/postInfinity=3` 무한 반복)로 구현 —
      Maya 2023 의 네이티브 sin 노드 부재 문제를 피한다(A00170 Remap 아이디어 응용).
  - Node 출력용 **Speed** 입력 추가(드라이버 windSpeed 초기값).

## v01.02 (2026-07-27)
- **[Add] Bone Chain / Bone Root 모드 선택** —
  - **Bone Chain**(기본, 기존 동작): 리스트업한 조인트들을 **하나의 체인**으로 보고 리스트 순서를
    offset 순번으로 쓴다.
  - **Bone Root**: 리스트업한 **각 조인트를 체인 루트**로 보고, 그 조인트 + **모든 자손 조인트**에
    대해 **root 로부터의 깊이(depth)를 offset 순번**으로 삼아 같은 파형을 반복 적용한다. 루트마다
    offset 순번이 리셋되고, 분기 체인에서 같은 깊이의 형제는 같은 offset 을 갖는다.

## v01.01 (2026-07-27)
- **[Change] 구간 내부의 0 교차 키 제거(커브 부드럽게)** — 극값 사이 0값 키(주기의 절반마다,
  예: period 12 → 6·12·18…f)가 있으면 spline 커브가 그 지점에서 평평/각지게 됐다. 이제 기본으로
  **내부 0 교차 키를 빼고 극값(±진폭)만** 남겨 깔끔한 싸인으로 보간되게 한다. 대신 구간 **양끝
  (Start/End)** 에는 그 지점의 실제 싸인 값으로 **앵커 키**를 둬 커브가 구간 밖으로 흘러가지 않게 한다.
- **[Add] `Keep zero-crossing keys` 체크박스**(기본 off) — 켜면 예전처럼 0 교차 키까지 모두 찍는다.

## v01.00 (2026-07-27)
첫 릴리스. 본 체인에 싸인 주기함수 키프레임을 찍어 '바람에 일렁이는' 애니메이션을 만드는
in-Maya PySide 툴.

- **본 체인 TSL**(`JUN_mod_tsl_qt`) — 리스트 순서가 조인트별 offset 순번을 정한다.
- **구간 입력**(`JUN_mod_timeRange_qt`) — 키를 만들 Start/End 프레임(실수 허용).
- **축 선택** — rotateX/Y/Z · translateX/Y/Z.
- **파라미터** — Period(주기), Amplitude(진폭), Offset/joint(조인트별 위상 지연, **실수 프레임**).
- **동작** — 각 조인트에 `value(t) = amplitude * sin(2π(t - i*offset)/period)` 파형.
  키는 **1/4 주기마다**(0, +A, 0, -A ...) 찍고 spline 탄젠트로 보간해 싸인 유사 파형을 만든다.
  1/4 주기가 소수(예: period 10 → 2.5, 7.5)면 **소수 프레임에 키**가 찍힌다.
- **Clear existing keys in range** 옵션(기본 on) — 재적용 시 구간 키를 먼저 지운다. 전체는 한 undo.
