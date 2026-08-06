---
name: wip-a00290-mix-targets-tab
description: A00290 Mix Targets 탭 — 소스 타겟 가중합을 다른 타겟과 최종(리깅) 메시에 일괄 반영
metadata: 
  node_type: memory
  type: project
  originSessionId: 4f6580d4-4bc6-4134-a627-7dc361a23170
  modified: 2026-08-06T08:38:10.865Z
---

A00290_BSTool **Mix Targets 탭**(v01.17, 2026-08-06 추가). 소스 `[a x1.0, b x0.5, c x0.8]` 를
섞은 만큼 체크한 다른 타겟들을 변형한다: `new_delta = old_delta + Σ(amount × delta(source))`.
근거는 blendShape 평가식 `base + Σ(w × delta)` — **같은 지오메트리의 델타는 같은 공간이라 그냥
더할 수 있다.**

**Base mesh 3모드** — 타겟이 베이스로부터의 오프셋이라 **베이스를 옮기면 델타를 그대로 둔 타겟이
따라 움직인다.** 그래서 규칙을 하나로 못박았다: *체크한 것은 변형, 체크 안 한 것은 모양 그대로.*
- `Leave it alone` : 델타에 믹스를 더한다
- `Deform it too` : 중립(`<base>ShapeOrig` = 바인드 셰이프)을 옮긴다. 체크한 타겟은 델타 유지
  (live 는 메시도 함께 이동), 체크 안 한 baked 타겟은 델타에서 믹스를 빼 **제자리 보정**
- `New mesh` : `<base>_mixed` 생성, 리그 무손상 (blendShape 이 다른 디포머 뒤일 때의 탈출구)

**스킨 리깅 메시**: blendShape 이 체인 앞이면 입력이 언제나 바인드 셰이프라 그걸 옮기면 되고
skinCluster 는 살아 있다. 베이스 포인트에는 **공간 변환 없이** 더한다(정의상 같은 공간).

UI 관례 하나가 다르다 — **이 탭만 "체크된 것이 작업 대상"**(다른 탭은 "보이는 것이 작업 대상").
목록이 둘이라 필터로 쉽게 가려지므로 가려져도 적용하고 `Checked: 3 (1 hidden)` 로 표시한다.

**Why:** 여러 셰이프에 공통 보정을 한 번에 넣거나 기준 셰이프 변경분을 나머지에 이식하는 작업.
**How to apply:** 저수준 처리는 `app/core/delta_utils.py` 에 모아 Base Shape 탭과 공유한다 —
델타 읽기/쓰기, 델타 공간 되돌리기, live 타겟 이동 + 검증/자가 보정/원상복구.
관련: [[blendshape-delta-space-origin]], [[wip-a00290-shape-editor-tab]], [[qapplication-before-maya-standalone]]
