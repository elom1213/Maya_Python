# CHANGELOG - A00390_WindTool_V02

## v02.01 (2026-08-18) - windEnvelope

### Added
- **`windEnvelope` 어트리뷰트 [0, 1]** — Node 출력이 만드는 **모든** 드라이버
  (Sine `*_windDriver`, Chain Wave `*_waveDriver`, Chain Wave Lite `*_liteDriver`)에 붙는다.
  - `0` = 노드가 **아무 영향도 주지 않는다**, `0.5` = **절반**, `1` = **완전 적용**(기본값).
  - `addAttr` 의 `minValue`/`maxValue` 로 구간을 강제한다 — 마야가 범위 밖 `setAttr` 을
    **거부한다**(잘라 내는 게 아니라 `RuntimeError`). 툴에서 넘기는 초기값은 파이썬에서 먼저 클램프.
  - 키를 걸 수 있으므로 바람을 **페이드 인/아웃** 시킬 수 있다 — 진폭을 건드리지 않고.
- 세 탭 모두 UI 에 `Envelope` 스핀박스(0~1, 기본 1.0). Sine 탭은 Node 전용이라
  Curve 출력에서는 `Speed`/`Node Offset` 처럼 **비활성**된다.

### 구현
파형 값이 **진폭에 정비례**하므로 envelope 를 **진폭에 한 번만** 곱하면 아래 전부가 같은
비율로 줄어든다. 그래서 드라이버당 `multDoubleLinear` **1개**면 끝이다(조인트/CV 마다
노드를 더 만들지 않는다).

| 탭 | 실효값 | 노드 | envelope=0 일 때 |
|----|--------|------|------------------|
| Sine | `windAmplitude × windEnvelope` | `*_ampEnvelope` | 값이 전부 0 (진폭 0 과 같음) |
| Chain Wave | `windAmplitude × windEnvelope` | `*_ampEnvelope` | CV 가 rest → 체인이 rest 자세 |
| Chain Wave Lite | `windSwingAngle × windEnvelope` | `*_liteSwingEnv` | theta 전부 0 → rest 자세 |

Chain Wave / Lite 는 이 노드도 제거용 세트에 들어가므로 Remove 로 같이 지워진다.

### 검증
`mayapy` (Maya 2024) 헤드리스 — 코어 21항목 + UI 14항목 **전부 통과**.

- 세 드라이버 모두 `windEnvelope` 존재 · 기본값 1.0 · 빌드 시 초기값 유지
- 범위 밖 `setAttr`(5.0 / −3.0) 이 거부되는지
- Sine: `0.5` 가 `1.0` 결과의 **정확히 절반**(5프레임 표본), `0.0` 이 전부 0
- Chain Wave: `0.5` 가 CV 변위의 **정확히 절반**, `0.0` 이면 CV 변위 0 · 회전 0 ·
  조인트 월드 위치가 rest 와 `0.000000` 차이
- Chain Wave Lite: `0.5` 가 로컬 회전의 **정확히 절반**, `0.0` 이면 rest 와 `1e-8` 미만 차이
- 임의 축(쿼터니언 경로, 대각 체인)에서도 `0.0` = rest · `0.5` 가 rest 와 full 사이
- Remove 후 envelope 노드 잔여 0

> ⚠️ Chain Wave 에서 **CV 변위는 envelope 에 정확히 비례하지만 조인트 회전각은 아니다.**
> ikSpline 이 커브를 푸는 과정이 비선형이라 `0.5` 에서 회전 비율이 0.47~1.08 로 흩어진다
> (변위가 0 근처인 조인트에서 특히). "절반의 영향력" 은 **파동의 세기**가 절반이라는 뜻이고,
> Lite 탭은 각도를 직접 다루므로 회전각까지 정확히 절반이다.

## v02.00 (2026-08-18) - Chain Wave Lite

`A00390_WindTool` v01.11 을 그대로 복제해 시작한다(Sine / Chain Wave 탭은 동일).

### Added
- **Chain Wave Lite 탭** - 커브·ikHandle·프록시 조인트 **없이** 각도만으로 같은 종류의
  파형을 만든다. 루트가 100개를 넘는 상황(털·풀·촉수 다발)을 위한 것.
  - `theta_k = swing * ramp_k * sin(2pi(s_k/lambda - phase))`, 조인트 로컬 회전은
    `theta_k - theta_(k-1)` — FK 누적을 상쇄해 체인이 말리지 않는다.
  - **진폭의 뜻이 바뀌었다**: 거리(월드 단위)가 아니라 **뼈가 흔들리는 각도(도)**.
    기존 탭과 같은 숫자가 같은 그림을 주지 않는다.
  - 회전축은 체인 방향 x 진동축으로 구하고 rotate 채널 공간으로 옮긴다. 기본축과
    맞으면 채널 직결, 아니면 `axisAngleToQuat -> quatProd -> quatToEuler`.
  - 조인트든 FK 컨트롤러든 **같은 경로** — 프록시 체인이 필요 없다.
- `core/wave_lite_manager.py` (신규). 기존 `wave_manager` 는 손대지 않았다.

### 측정
- 같은 체인(조인트 9, 뼈 2.0)에서 **141 -> 95 노드 (33% 감소)**,
  커브 0 · ikHandle 0 · ikEffector 0 · 프록시 조인트 0.
- 뼈 각도가 정의식과 최대 **0.015도** 차이(16샘플 싸인 LUT 보간 오차).
- 뼈 길이 유지 · 루트 고정 · translate 불변.

### 알아둘 것
- 기존 Chain Wave 와 **값이 같지 않다.** 접선각을 그대로 쓰면 ikSpline 대비 과대해지고
  (파장 10에서 -25.5도 vs -39.7도), 그 비율이 파장에 따라 0.41~0.75로 변해 상수 보정이
  불가능하다. 그래서 재현 대신 **정의를 각도로 바꿨다**.
