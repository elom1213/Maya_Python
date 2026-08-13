---
name: blendshape-target-name-vs-alias
description: blendShape 타겟 메시의 노드 이름과 웨이트 alias 는 다른 것 — 포즈 이름을 노드 이름으로 쓰면 메시가 둘 이상일 때 깨진다
metadata: 
  node_type: memory
  type: reference
  originSessionId: cbf34923-4abc-4c62-9078-e552b18afd5c
  modified: 2026-08-13T02:31:37.218Z
---

**타겟 메시의 노드 이름 ≠ blendShape 웨이트 별칭(alias).** 노드 이름은 씬 전체에서 유일해야 하지만,
alias 는 **blendShape 노드 단위**라 서로 다른 blendShape 가 같은 alias(`calf_l_default`)를 가질 수 있다.

**How to apply**: 포즈/규칙 이름처럼 **여러 메시가 공유하는 이름**으로 타겟을 만들 때는
① 타겟 메시를 `<메시>_<이름>` 으로 유일하게 만들고 ② 붙인 뒤
`cmds.aliasAttr("<이름>", bs + ".weight[i]")` 로 alias 를 원래 이름으로 되돌린다.
그러면 `<blendShape>.<이름>` 주소가 유지되어 하위 연결 코드가 그대로 동작한다.

**Why**: A00090 에서 이 구분을 안 해 타겟 이름을 포즈 이름 그대로 썼더니, 옷 A 에 타겟을 만든 뒤
옷 B 에 같은 규칙을 돌리면 `objExists` 가 True 라 **A 의 타겟을 B 것으로 재사용** →
`Target ...Shape does not match with base ...Shape.` + `No deformable objects selected.` 로
`cmds.blendShape` 호출이 통째로 실패했다. 이름이 조인트 등에 이미 쓰였으면
`More than one object matches name`. 어느 쪽이든 타겟이 아예 안 생기거나 일부만 생겼다. (2026-08-13 수정, v01.06)

곁들여 알아 둘 것:
- **다음 웨이트 인덱스는 `getAttr(".weight", size=True)` 가 아니다.** 중간 타겟을 지우면 인덱스가
  듬성해져(예: `[0, 2]`, size=2) size 를 쓰면 **기존 타겟 자리를 덮어쓴다**
  (`Error: Target at given index already exists.` 로 조용히 실패). `max(multiIndices)+1` 을 쓸 것.
- `cmds.blendShape(mesh, name=..., frontOfChain=True)` 는 **타겟 없이도** 만들어진다 → 인덱스와 alias 를
  직접 통제하며 하나씩 붙일 수 있고, 타겟 하나가 실패해도 나머지가 산다.
- `cmds.listAttr(bs + ".w", multi=True)` 는 **alias 이름 목록**을 준다(중복 추가 판정에 쓸 수 있다).
- 타겟 트랜스폼을 옮겨도 델타는 안 생긴다 — [[blendshape-live-target-inputpointstarget]] 참고.

관련: [[wip-a00090-rule-versions]], [[extendtoshape-picks-wrong-shape]]
