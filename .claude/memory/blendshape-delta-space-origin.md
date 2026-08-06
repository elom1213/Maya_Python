---
name: blendshape-delta-space-origin
description: "blendShape 델타가 어느 공간인지는 origin 어트리뷰트가 정한다(0=world→베이스 공간, 1=local→타겟 공간)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4f6580d4-4bc6-4134-a627-7dc361a23170
  modified: 2026-08-06T05:41:12.036Z
---

`inputPointsTarget` 델타의 공간은 blendShape 노드의 **`origin`** 어트리뷰트가 정한다
(연결 플러그는 힌트가 안 된다 — origin 과 무관하게 항상 `worldMesh` 에서 온다).

| `origin` | 델타 | 타겟 정점을 옮기려면 |
|---|---|---|
| `1` = local (`cmds.blendShape` **기본**) | `타겟 로컬 − 베이스 로컬` = 타겟 오브젝트 공간 | 그대로 |
| `0` = world | `타겟로컬 × 타겟worldMatrix × 베이스worldInverse − 베이스로컬` = **베이스** 오브젝트 공간 | `delta × (base.worldMatrix × target.worldMatrix⁻¹)` 의 **3×3 부분** (평행이동은 상쇄) |

`om.MVector * om.MMatrix` 는 평행이동을 무시하므로 방향 변환에 그대로 쓰면 된다.

**Why:** A00290 Base Shape 탭이 "값 0.5 인데 일부 정점만 1.5 처럼" 스케일되던 버그의 원인
(v01.16). world origin + 타겟 `scaleX=-1`(미러) 이면 X 로 움직인 정점만 부호가 뒤집혀
**정점마다 되기도 하고 안 되기도** 한 것처럼 보인다. 델타를 노드에서 직접 스케일하는
baked 경로는 벡터 배율이라 공간과 무관.

**How to apply:** 델타를 타겟 메시 이동으로 바꾸는 코드는 반드시 origin 을 보고 공간을 되돌린다.
공간 가정이 맞는지 못 믿겠으면 **적용 후 델타를 다시 읽어 정점 번호로 대조**하고, 어긋나면
정점을 x/y/z 로 한 번씩 밀어 응답 3×3 을 직접 재는 폴백이 확실하다(선형이라 3번이면 끝).
관련: [[blendshape-live-target-inputpointstarget]], [[mayapy-headless-verify]]
