# CHANGELOG - A00390_WindTool_V02

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
