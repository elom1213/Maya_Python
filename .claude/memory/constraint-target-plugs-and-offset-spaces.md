---
name: constraint-target-plugs-and-offset-spaces
description: "constraint 의 target[i] 연결 열거법 + parentConstraint offset 두 어트리뷰트가 서로 다른 공간에 산다"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ee81a66a-5136-4bb8-b44a-7fa187164cdb
  modified: 2026-08-07T09:06:18.204Z
---

constraint 를 **지웠다 다시 만들지 않고** 타깃만 갈아끼울 때 필요한 사실들 (Maya 2024 실측).

## target[i] 연결 열거

- **`cmds.listConnections("con.target[0]", ...)` 는 None 을 준다** — 컴파운드 배열 원소 플러그는
  안 먹는다. 노드 단위(`listConnections(cn, s=1, d=0, p=1, c=1)`)로 받아 dest 플러그에서
  `.target[<i>].<child>` 를 직접 파싱해야 한다.
- 멀티 인덱스는 **연결에서 역추적**한다. `targetList` 순서에 기대지 말 것.
- 타깃 판정에서 빼야 하는 연결: `targetWeight`(← constraint 자신의 `<타깃>W0` 어트리뷰트),
  그리고 **소스가 constraint 자기 자신**인 것(pointOnPoly 의 `targetU/targetV` ← `geoU0/geoV0`).
- weight 는 별칭(alias)이 아니라 **실제 dynamic attribute** 다. `aliasAttr(q=True)` 는 None,
  이름 변경은 `cmds.renameAttr(cn+".AW0", "BW0")`.
- joint 타깃만 연결되는 자식: `targetJointOrient` / `targetInverseScale` /
  `targetScaleCompensate`. joint↔트랜스폼 교체 시 끊고 기본값으로 되돌리거나 새로 연결해야 한다.
- 셰이프 기반(geometry/normal/tangent) 은 `targetGeometry ← shape.worldMesh|worldSpace`,
  pointOnPoly 는 `targetMesh`.

## offset 재계산 (driven 제자리 유지)

| 타입 | 합성 방식 |
|---|---|
| `parentConstraint` | **타깃별** `targetOffsetTranslate/Rotate`. 아래 참고 |
| `pointConstraint` | 덧셈 — `offset += (t_before − t_after)` |
| `scaleConstraint` | 곱셈 — `offset *= (s_before / s_after)` |
| `orient` · `aim` | 회전 — `O_new = R_before * R_after⁻¹ * O_old` |

**함정**: parentConstraint 의 두 offset 은 **서로 다른 공간에 산다.**
- `targetOffsetTranslate` = `driven_world * inverse(target_world)` 의 **이동** (타깃 스케일 포함)
- `targetOffsetRotate` = **스케일을 뺀 순수 회전** 차이

한 행렬로 같이 옮기면 **스케일 걸린 타깃**에서 driven 이 튄다. 위치는 전체 월드 행렬로,
회전은 `MTransformationMatrix.rotation(asQuaternion=True).asMatrix()` 로 스케일을 벗겨 각각 옮길 것.
타깃별 offset 이라 **weight 가 섞여 있어도 정확**하다(타깃별 기여도만 유지되므로).

**오일러 순서는 전부 driven 의 `rotateOrder`** (= `cn.constraintRotateOrder`). XYZ 로 가정하면
non-XYZ driven 에서 수십 도씩 틀어진다. 보정 뒤에는 driven 월드 행렬을 다시 읽어 검증할 것.

구현: `A00145_RigConnect/app/core/constraint_target_manager.py` ([[wip-a00145-target-replace]]).
관련: [[mayapy-headless-verify]], [[uuid-safe-rename-duplicate-names]]
