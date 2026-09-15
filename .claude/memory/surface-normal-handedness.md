---
name: surface-normal-handedness
description: "pointOnSurfaceInfo 의 normal 은 tangentU x tangentV — [tanU, normal, tanV] 행렬(Chris Lesage pin_to_surface)은 왼손계라 회전이 뒤집힌다"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 123b12b1-9c5d-4090-a848-07c2f0433e5b
  modified: 2026-09-15T00:46:10.432Z
---

Maya 2024 실측: `pointOnSurfaceInfo.normalizedNormal · (tangentU × tangentV) = +1`. 즉 **normal = tangentU × tangentV**.

그래서 널리 퍼진 matrix pinning 구성(Chris Lesage `pin_to_surface`,
`_archive/legacy_tools/01_Modules/JUN_PY_matrixPinning_V01_01.py`)의 fourByFourMatrix 행
`X=tangentU, Y=normal, Z=tangentV` 는 **det < 0 인 왼손 좌표계**다. decomposeMatrix 는 이것을
음수 스케일로 풀기 때문에 `outputRotate` 만 연결하면 **한 축이 뒤집힌 회전**이 들어간다
(tangentU·tangentV 가 직교가 아니면 shear 도 섞인다).

**Why:** A00170 AttachCrv 에 서피스 지원을 넣으며(2026-09-15, v01.23) ref 를 그대로 옮기려다 진단 출력으로 확인했다.

**How to apply:**
- 서피스 프레임은 **X = tangentU, 업 시드 = normal** 로 직교 정규화한다: `Z = X × N`(= −tangentV 방향), `Y = Z × X`.
  A00170 `attach_curve._orient_frame_outputs(poci, aim, up_plug=<posi>.normalizedNormal, tangent_plug=<posi>.normalizedTangentU)`.
- ref 와 결과를 비교할 때 Z 축 방향이 반대인 게 정상이다.
- `closestPointOnSurface.parameterU/V` 는 **실제 파라미터 값**(0~1 아님) — `pointOnSurfaceInfo` 도 `turnOnPercentage=0`.
  "가운데" 는 `0.5` 가 아니라 `minMaxRangeU/V` 의 중간.

관련: [[parentmatrix-includes-offsetparentmatrix]], [[wip-a00170-attachcrv-tab]], [[mayapy-headless-verify]]
