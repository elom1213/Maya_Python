---
name: wip-a00145-skin-constraint-types
description: A00145 Skin Weight to Constraint gains Parent/Scale/Point/Orient type radio (was parent-only) - Maya test + push pending
metadata: 
  node_type: memory
  type: project
  originSessionId: 91ab0dea-4b6f-4134-a5cd-3d3ccc44c43a
---

A00145_RigConnect v01.16 — Constraint 탭의 "Skin Weight to Constraint" 가 parentConstraint 만
만들던 것을 **Parent / Scale / Point / Orient 라디오 선택**으로 확장. DONE (Maya 검증 + 푸시 완료).

**Why:** 스킨 웨이트 비율로 joint 를 가중 구속하는 기능인데 parent 만 지원해서, 회전만/스케일만
따라가게 하려면 만든 뒤 손으로 갈아끼워야 했다.

**How to apply:**
- `constrain_manager.get_constraint_func(con_type)` — 새 public 헬퍼. key → `cmds.*Constraint` 함수.
  `constrain()` 도 이걸 쓰도록 바꿈.
- `skin_constraint_manager.SKIN_CONSTRAIN_TYPES` = `con_mgr.CONSTRAIN_TYPES` 에서 `pointOnPoly`
  제외(메시 타겟이라 joint 가중 방식 불가). `con_type="parent"` 기본값으로 하위호환 유지.
- **`interpType` 은 parentConstraint / orientConstraint 에만 존재** (point/scale 엔 없음) — mayapy 로
  검증함. 그래서 `cmds.attributeQuery("interpType", node=con, exists=True)` 로 가드하고 Shortest(2) 설정.
- `weightAliasList` 쿼리는 네 타입 모두 각자의 `cmds.*Constraint` 함수로 해야 한다(생성에 쓴 함수 재사용).

관련: [[undo-chunk-by-default]], [[push-includes-tool-guide-docs]], [[mayapy-headless-verify]]
