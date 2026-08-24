---
name: shape-pnts-is-post-deformation
description: 히스토리 있는 셰이프의 pnts(tweak) 는 디포머 *뒤*에 더해진다 — 포즈를 따라가지 않는 상수 오프셋
metadata: 
  node_type: memory
  type: reference
  originSessionId: cce9837c-ee83-4545-8532-e6317949f1f2
  modified: 2026-08-24T08:17:16.065Z
---

**뷰포트에서 버텍스를 옮기면 `<shape>.pnts` 에 들어가고, 그 값은 디포머 체인 *뒤*에 더해진다.**
(체인 앞쪽에 `tweak` 노드가 있는 씬이면 거기로 들어간다 — 그건 디포머 입력이다.)

Maya 2024 mayapy 실측 — 조인트에 바인드된 큐브에서 같은 편집을 두 포즈에서 재 봤다.

| 편집을 넣은 곳 | 포즈 A 오프셋 | 포즈 B 오프셋 |
|---|---|---|
| `<shape>.pnts` | `(1.000, 0, 0)` | `(1.000, 0, 0)` — **포즈 무관 상수** |
| 체인 헤드 `...Orig` | `(0.866, 0.500, 0)` | `(0.500, -0.866, 0)` — 조인트를 따라 회전 |

`skinCluster` 의 **입력 지오는 `pnts` 편집에 전혀 변하지 않는다**(실측 차이 0.000000) — 셰이프가
체인의 끝이니 당연하다. 마야가 띄우는 `Tweaks can be undesirable on shapes with history` 경고가
이 이야기다.

**그래서 "스킨된 메시를 고친다" 는 작업은 `pnts` 를 체인 헤드로 옮기지 않으면 완성되지 않는다.**
안 옮기면 바인드 포즈에서만 맞고 조인트를 돌리면 어긋나는 — "고친 메시" 가 아니라 **"화면에만
맞는 메시"** 가 된다. 구현: `A00275_skinTool_V01/app/core/mesh_edit_manager.py`
([[wip-a00275-edit-mesh]]).

덤: `skinCluster` 는 바인드할 때 **메시 트랜스폼의 t/r/s 9개를 잠근다**(실측). 메시 자체를
옮기려면 먼저 풀어야 하고, `skinCluster.geomMatrix`(멀티 아닌 단일 matrix = 바인드 시점 메시
월드 행렬)를 `geomMatrix * G0^-1 * G1` 로 따라 갱신해야 한다.

관련: [[wip-a00275-skintool-bindpose]](같은 이유로 델타를 체인 헤드에 굽는다),
[[blendshape-live-target-inputpointstarget]], [[mayapy-headless-verify]]
