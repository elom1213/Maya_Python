---
name: wip-ik-edit-keep-pv-offset
description: "A00060/A00130 IK Edit 새 모드(폴 벡터 offset 유지 + 중간 조인트를 폴 평면에 투영) — 2026-09-28 계획서만, 사용자 답 대기. Rest Translate 는 weight 1 이면 IK 에 영향 없음(실측)"
metadata:
  node_type: memory
  type: project
  originSessionId: e2f32ad0-e44a-4434-8bf3-44b0353ea50f
  modified: 2026-09-28T00:07:09.356Z
---

2026-09-28 사용자 요청: IK Edit 이 poleVectorConstraint **offset 을 바꾸지 않고** 체인을 고치게.
계획서 `JUN_All/docs/plans/A00060_A00130_ik_edit_keep_pv_offset_plan.md` — **구현 전, 질문 Q1~Q7 답 대기.**

**실측 (mayapy 2024)**
- ★ `restTranslate` 는 타깃 weight 가 1(또는 0.5, 정규화)이면 `constraintTranslate` 에 **영향 없음**.
  weight 합 0 일 때만 쓰인다. 사용자는 "Rest Translate 만 조절해서" 라고 생각했지만, IK 를 맞추는 건
  **joint2 를 폴 평면(체인 축 + poleVector, twist 만큼 회전)에 투영**하는 것. rest=ct 동기화는 정리용.
- offset 고정 + 평면 투영 → 위치·회전 편차 0 (twist 30 · 기존 offset · 레퍼런스 · 재오픈).
- v 가 폴 **반대편**이면 솔버가 뒤집는다(편차 6.39) → 정책 필요(Q3).
- joint2 translate 만 바꾸면 joint1 X 축이 뼈에서 18.6° 어긋남. `joint -e -oj xyz` 로 다시 맞춰도 편차 0 (Q2).

**구현 때 부딪칠 것**: A00130 IK 축 맞추기가 세션 **뒤**에 twist 를 바꿔 평면이 돈다 · A00130 Orient & Place 의
폴 타깃이 체인에 살아 있게 물린 A' 면 "고정 평면" 이 없다(Q4).

**How to apply:** 답이 오면 Phase 0(실제 케이지 실측)부터. 공유 코어 `ik_edit_manager` 에 셋째 모드
`PV_MODE_KEEP` 로 더하고 기존 두 모드는 건드리지 않는다. A00060 먼저, A00130 은 그다음.
관련 [[wip-a00060-ik-edit]] · [[wip-a00130-ik-session]] · [[wip-a00130-ik-axis]] · [[wip-a00060-pole-target]]
