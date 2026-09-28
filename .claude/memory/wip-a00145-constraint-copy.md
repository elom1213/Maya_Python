---
name: wip-a00145-constraint-copy
description: "A00145 v01.57 (2026-09-28) — Constrain 하위 탭 Constraint·Skin Weight 를 모드(Default / Skin Weight)로 합침, Transfer 에 모드 Copy(constraint 성질을 읽어 다른 오브젝트에 똑같이, 원본 유지)"
metadata:
  node_type: memory
  type: project
  originSessionId: 64d856a3-210c-4001-9bbc-757c4ec50a03
  modified: 2026-09-28T02:26:08.097Z
---

**하위 탭 안의 "모드"** = `_build_mode_page(modes)` (Mode 라디오 줄 + QStackedWidget). 모드 화면은 예전 하위 탭
빌더를 그대로 쓴다 — 사용자 요구가 "기존 Options UI 그대로". 하위 탭은 `Constraint / Group Create / Transfer /
Target Edit / Update`(6 → 5). 기능이 한 하위 탭에 둘 이상이면 이 골격을 쓴다.

**Copy 모드** (`core/constraint_copy_manager.py`, 읽기 헬퍼는 `constraint_transfer_manager` 와 공유):
- 복사 = 종류 · 타깃 순서 · **구동 축**(원본 출력이 driven 의 어느 채널에 꽂혔는지 읽어 skip 플래그로) ·
  동적 어트리뷰트(weight `<t>W0`, pointOnPoly U/V — `listAttr(ud=True)` 한 번으로 둘 다) · aim/normal/tangent 벡터 ·
  worldUpObject · interpType · rest 값.
- 설계 결정(요청에 없던 것): **Maintain Offset 기본 ON = 지금 자리로 오프셋 재계산**(튀지 않음), 끄면 원본 offset
  **값** 복사(원본 driven 자리로 감). Mapping `All -> Each Object`(기본) / `Row to Row`. 사용자에게 보고함.
- **같은 종류 constraint 가 이미 있는 오브젝트는 건너뛴다** — 마야는 새 노드를 안 만들고 기존 것에 타깃을 더한다.
  driven 자신 · 원본 타깃도 건너뜀.
- geometryConstraint 는 maintainOffset 플래그를 받지 않는다 → TypeError 잡고 플래그 없이 재시도.

검증 mayapy 38항목(standalone 은 `undoInfo(state=True)` 켜야 undo 확인 가능). 마야 GUI 확인 전.
관련: [[wip-a00145-constraint-transfer]], [[wip-a00145-skin-constraint-types]], [[prefer-subtabs-over-stacked-collapsibles]]
