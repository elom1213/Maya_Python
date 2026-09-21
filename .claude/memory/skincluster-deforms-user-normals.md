---
name: skincluster-deforms-user-normals
description: skinCluster 는 deformUserNormals 로 잠긴(user) 노멀도 회전시킨다 — 바인드를 현재 포즈로 갱신하면 노멀만 rest 로 되돌아간다
metadata:
  type: reference
---

`skinCluster.deformUserNormals` 는 기본 ON 이고, **잠긴(locked / user) 버텍스 노멀을 스킨 행렬로
같이 회전**시킨다. 그래서 `bindPreMatrix` 를 현재 포즈로 바꿔 스킨 변형이 항등이 되면
그 회전이 사라져 **노멀만 Orig 셰이프의 rest 값으로 되돌아간다.** 위치는 `pnts` 에 구워서
유지되므로 "위치는 그대로인데 셰이딩만 달라지는" 증상으로 나타난다 (mayapy 2024 확인).

- **잠기지 않은 노멀은 위치에서 계산**되므로 위치가 같으면 노멀도 같다 — 손댈 필요 없다.
- 고치려면 갱신 전 **스킨 출력의 face-vertex 노멀**을 잡아 두었다가, 달라진 **잠긴 노멀만**
  체인 헤드(Orig) 셰이프에 다시 쓴다. 중간(intermediate) 셰이프에 써도 하류로 전달된다.
- 쓰기는 `cmds.polyNormalPerVertex` 에 컴포넌트를 몰아 한 번에 — **undo 되고** 히스토리 노드도
  안 생기며 face-vertex 6,400개에 0.05초. `MFnMesh.setFaceVertexNormals` 는 빠르지만 undo 가
  안 된다([[undo-chunk-by-default]] 와 같은 이유로 금지).
- **안 잠긴 노멀까지 쓰면 그 자리에서 잠긴다** → 이후 디폼에 노멀이 따라 돌지 않는 메시가 된다.
  `MFnMesh.isNormalLocked(normalId)` 로 골라 쓴다.
- `mesh.n[...]` 에 setAttr 하는 길은 **평가 결과에 반영되지 않는다**(확인). 쓰지 말 것.

A00275 Bind Pose v01.29 에서 이 버그를 고쳤다 — [[wip-a00275-skintool-bindpose]].
