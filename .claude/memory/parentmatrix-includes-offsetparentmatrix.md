---
name: parentmatrix-includes-offsetparentmatrix
description: offsetParentMatrix 를 노드망으로 구동할 때 obj.parentInverseMatrix 를 쓰면 안 된다 — parentMatrix 가 자기 OPM 을 포함해 되먹는다
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 123b12b1-9c5d-4090-a848-07c2f0433e5b
  modified: 2026-09-15T00:31:07.881Z
---

Maya 2024 실측: 오브젝트의 `parentMatrix[0]` 은 **부모 worldMatrix 가 아니라 `OPM × parent.worldMatrix`** 다.
`worldMatrix == matrix × parentMatrix`, `parentInverseMatrix == inverse(parentMatrix)`.

**Why:** A00170 AttachCrv `Maintain offset`(2026-09-15)에서 `OPM = 오프셋 × 프레임 × obj.parentInverseMatrix`
로 짰더니 **자기 출력을 되먹어**, 부모와 OPM 값이 **둘 다** 있는 오브젝트만 월드가 어긋났다
(OPM 이 단위행렬이거나 월드 직속이면 통과해서 놓치기 쉽다).

**How to apply:**
- OPM 을 구동하는 네트워크는 **부모 transform 의 `worldInverseMatrix[0]`** 을 직접 물린다(월드 직속이면 생략).
- 오프셋 상수도 `OPM0 × parent.worldMatrix0 × inverse(frame0)` — `parentMatrix` 를 쓰면 OPM0 이 두 번 들어간다.
- 반대로 `translate/rotate` 를 decompose 로 구동하는 기존 경로에선 `parentInverseMatrix` 가 맞다(OPM 안쪽 공간).
- 테스트 씬엔 **부모 + 0 이 아닌 OPM** 조합을 꼭 넣는다.
- OPM 으로 오프셋을 들고 갈 프레임은 **직교 정규**여야 한다 — 아니면 shear 가 자식까지 샌다
  (직선 커브의 `pointOnCurveInfo.normal` 은 평행 이동만으로 부호가 뒤집힘, [[wip-a00170-attachcrv-tab]]).

관련: [[mayapy-headless-verify]], [[skincluster-hold-mesh-while-moving-joints]]
