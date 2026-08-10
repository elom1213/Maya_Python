---
name: skincluster-hold-mesh-while-moving-joints
description: 조인트를 움직여도 스킨 메시를 고정하려면 bindPreMatrix 직결이 아니라 multMatrix 로 스킨 행렬을 상수 유지
metadata: 
  node_type: memory
  type: reference
  originSessionId: ee81a66a-5136-4bb8-b44a-7fa187164cdb
  modified: 2026-08-10T01:38:17.660Z
---

skinCluster 의 인플루언스별 스킨 행렬은 **`bindPreMatrix[i] * matrix[i]`**
(`matrix[i]` = 조인트의 `worldMatrix`). 조인트를 옮겨도 메시가 안 변하게 하려면 이 곱을 상수로 둔다.

```
C_i                = bindPreMatrix_i(0) * worldMatrix_i(0)     # 편집 시작 시점 상수
bindPreMatrix_i(t) = C_i * worldInverseMatrix_i(t)             # multMatrix 1개로 라이브 연결
```
multMatrix `matrixIn[0]` = `C_i`, `matrixIn[1]` ← 조인트 `worldInverseMatrix[0]`, `matrixSum` → `bindPreMatrix[i]`.

**함정: `worldInverseMatrix` 를 `bindPreMatrix` 에 그냥 직결하면 안 된다.**
스킨 행렬이 항등이 되어 메시가 **rest 셰이프로 튄다**. 리그가 바인드 포즈에 있을 때만 우연히
결과가 같고, **포즈된 리그에서는 눈에 띄게 점프**한다(실측 3.6 유닛). 위 `C_i` 보정은 포즈와
무관하게 항상 무변화(실측 오차 1e-16, `skinMethod` linear/DQ/blended 모두).

확정(굽기)은 **노드를 지우기 전에** `matrixSum` 을 읽어 두었다가 `setAttr ... type="matrix"` 로 쓴다 —
연결이 끊기면 attr 은 연결 전 값으로 돌아가지, 마지막 평가값을 유지하지 않는다.

- `weightList` 를 읽지도 쓰지도 않으므로 **버텍스별 웨이트 동일성은 정의상 보장**된다.
- `bindPreMatrix` 가 잠겨 있으면 `connectAttr` 자체가 거부된다 → 미리 `getAttr(lock=True)` 로 걸러
  경고. 그 조인트(및 그 부모)를 움직이면 메시가 변형된다.
- 인덱스는 [[list-attrs-multi-detection]] 이 아니라 `matrix[]` 연결에서 얻는다(성긴 인덱스 주의 —
  A00275 `bind_pose_manager._influence_index_map`).

구현: `A00275_skinTool_V01/app/core/joint_edit_manager.py` ([[wip-a00275-move-joints]]).
관련: [[wip-a00275-skintool-bindpose]], [[mayapy-headless-verify]]
