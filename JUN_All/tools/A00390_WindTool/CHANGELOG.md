# Changelog — A00390_WindTool

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
