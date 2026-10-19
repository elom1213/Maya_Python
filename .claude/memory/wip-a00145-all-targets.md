---
name: wip-a00145-all-targets
description: "A00145 Constrain > Constraint v01.62 — `All Targets -> Each Follower` 체크박스(기본 OFF): follower 마다 Targets 전부를 타깃으로 갖는 constraint 하나. 짝짓기는 constrain_manager.resolve_pairs() 하나"
metadata:
  type: project
---

`A00145_RigConnect` **v01.62** (2026-10-19) — 요청: Targets 여러 개 + Follower 하나면 타깃이 하나만 걸린다
(예전 짝짓기 = 인덱스 1:1 / 타깃 1개 브로드캐스트) → 모든 타깃을 가진 constraint 를 만드는 옵션.

- `resolve_pairs(targets, followers, all_targets)` → `[(follower, [targets...])]`, `constrain_types(..., all_targets)` 가
  `func(*tgts, follower, mo=)` 로 건다. 기본 OFF(예전 동작 유지), Matrix 모드에선 비활성.
- 검증: mayapy 2024 12항목(코어 + offscreen UI `on_constrain()` · Undo). 마야 GUI 확인 전.
  Point On Poly 에 버텍스 타깃 여러 개는 따로 실측 안 함(실패하면 `[WARN]` 로 남음).

관련: [[wip-a00145-multi-constraint-types]], [[wip-a00145-match-one-to-many]]
