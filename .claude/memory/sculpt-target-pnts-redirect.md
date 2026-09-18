---
name: sculpt-target-pnts-redirect
description: blendShape 타겟 Edit(sculptTarget) 중에는 shape.pnts setAttr 가 타겟으로 새며 에러 — 아이템 inputPointsTarget 에 직접 더한다
metadata: 
  node_type: memory
  type: reference
  originSessionId: f0dafff4-39d2-4341-8b56-4bc9271dd7f4
  modified: 2026-09-18T09:00:07.002Z
---

`cmds.sculptTarget(bs, e=True, target=i)` 로 Edit 를 켜면 셰이프의 **`tweakLocation` → `<bs>.inputTarget[g].vertex[0]`**
연결이 생긴다. 이때 Maya 2024 mayapy 실측:

| 쓰기 | 결과 |
|---|---|
| `setAttr shape.pnts[..]` | 타겟 델타에 **더해지고**(절대값 아님) `RuntimeError: Maya command error`. 구간 쓰기는 원소가 빠지기도 |
| `move -r -os vtx` | 정상 — d 가 아이템 `inputPointsTarget` 에 그대로 더해짐. 1만 버텍스 11초, undo 14초 |
| `xform -os -t vtx` | 타겟에 안 들어감 |

마야 `move` 규칙: 아이템 = `5000 + 1000 × inputTarget[g].sculptInbetweenWeight`, d 는 셰이프 오브젝트 공간
그대로(weight 로 안 나눔, origin world 여도 그대로). 라이브 타겟이면 그 메시도 d 만큼 옮기는데
**origin world + 트랜스폼이 다르면 변환 없이 옮겨서 마야 자체가 어긋난다**.

**Why:** A00380 By Weight 가 Edit 중인 메시에서 에러(2026-09-18). pnts 로 쓰는 툴은 전부 같은 함정.
**How to apply:** pnts 로 버텍스를 쓰는 코드는 먼저 Edit 중인 타겟이 있는지 보고, 있으면 그 아이템의
`inputPointsTarget` / `inputComponentsTarget` 에 더해 쓴다. 구현 `A00380_MeshTool/app/core/sculpt_target.py`.
관련 [[shape-pnts-is-post-deformation]] · [[wip-a00290-shape-editor-tab]] · [[blendshape-delta-space-origin]] · [[wip-a00380-match-by-weight]]
