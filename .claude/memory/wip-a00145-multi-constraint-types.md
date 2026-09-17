---
name: wip-a00145-multi-constraint-types
description: "A00145 Constrain > Constraint v01.47 — 종류를 체크박스로, 구동 채널이 겹치지 않는 조합(Parent+Scale, Point/Orient/Scale)을 한 번에. 마야는 이미 연결된 채널에 parentConstraint 를 걸면 에러 대신 pairBlend 를 끼운다"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5782f0ec-e7f6-4339-aa79-6790d10548f6
  modified: 2026-09-17T08:27:02.668Z
---

`A00145_RigConnect` **v01.47** (2026-09-17) — Constrain > Constraint 의 종류 라디오를 **체크박스**로.
사용자 요청: Parent + Scale 동시, Scale · Point · Orient 중 2~3개 동시.

**규칙 = 구동 채널이 겹치지 않을 것** — `constrain_manager.CONSTRAIN_CHANNELS`
(parent=tr, point=t, orient=r, scale=s, pointOnPoly=trs 로 두어 혼자 쓰게). UI 는 체크하면 겹치는 쪽을 끈다
(먼저 켜진 쪽이 꺼짐). 코어 `constrain_types()` 는 `validate_types` 로 먼저 막고, follower 별로 종류마다 try —
실패는 `errors` 로 돌려주고 계속한다. 기본 체크는 `Parent` 하나(예전 라디오 기본과 같음).
`Skin Weight to Constraint` 페이지의 라디오는 그대로 둠(요청 범위 밖).

**실측 (Maya 2024)**
- `parentConstraint` 뒤 `pointConstraint` / `orientConstraint` → `Object is already connected.`
- parent+scale, point+orient+scale → 함께 걸림.
- `pointOnPolyConstraint` 는 translate + **rotate** 를 구동한다.
- ★ **순서가 반대면 에러가 안 난다**: `pointConstraint` 가 이미 있는데 `parentConstraint` 를 걸면
  **`pairBlend` 가 끼어들어** 두 constraint 가 섞인다(`tx` 소스가 `pairBlend1`). 이미 constraint 가 걸린
  오브젝트는 이 탭의 겹침 검사로 못 잡는다 — 가이드에 주의로 적었다.

검증: mayapy 37항목(조합 5종, 충돌 시 아무것도 안 만듦, 한 follower 실패 후 계속, 1:1/브로드캐스트,
UI 자동 해제·Matrix 모드 비활성·Undo 한 번·빈 선택 ERR). 마야 GUI 확인 전.
관련: [[wip-a00145-skin-constraint-types]], [[constraint-target-plugs-and-offset-spaces]]
