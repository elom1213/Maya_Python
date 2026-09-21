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
- **쓰기는 `MFnMesh.setVertexNormals` / `setFaceVertexNormals` 로 한두 번에.**
  `cmds.polyNormalPerVertex` 에 face-vertex 를 몰아 주면 **마야가 죽는다** — face-vertex
  359,400 장 메시 하나에 **메모리 +1.2 GB**(undo 레코드가 face-vertex 당 3 KB 넘는다),
  **참조된 리그**는 face-vertex 89,700 개에 **레퍼런스 편집 131,698 개**(노멀을 안 쓰면 145 개).
- ★ API 로 쓴 뒤 **`cmds.dgdirty(shape)`** 를 불러야 한다. 노멀이 쪼개진 사실이 디포머 출력까지
  가지 않아 출력이 옛 공유 구조를 들고 값이 이웃과 뒤섞인다(40 개 중 26 개가 틀렸다).
- ★ **undo 는 스냅샷 명령 하나로 되살린다**: 쓸 버텍스 범위(`vtx[a:b]`)에만
  `polyNormalPerVertex -freezeNormal` 을 **먼저** 한 번 걸면(이미 잠긴 노멀엔 no-op) 그 시점
  노멀이 undo 레코드에 담기고, 뒤이은 API 쓰기까지 Ctrl+Z 로 통째로 복구된다(1,560/1,560).
  `vtx[*]` 로 걸면 안 잠긴 노멀까지 잠기므로 **쓸 버텍스만** 건다.
- ★ **참조(reference)된 셰이프에는 쓰지 말 것** — 마야가 참조 메시의 노멀 변경을 face-vertex
  마다 편집으로 보존하므로 API 로 써도 편집이 폭발한다. 건너뛰고 알린다.
- 한 버텍스의 face-vertex 가 전부 같은 값이면 `setVertexNormals` 로 — `setFaceVertexNormals`
  로 쓰면 공유 노멀이 쪼개져(28 -> 56) 메시가 괜히 무거워진다.
- **안 잠긴 노멀까지 쓰면 그 자리에서 잠긴다** → 이후 디폼에 노멀이 따라 돌지 않는 메시가 된다.
  `MFnMesh.isNormalLocked(normalId)` 로 골라 쓴다.
- `mesh.n[...]` 에 setAttr 하는 길은 **평가 결과에 반영되지 않는다**(확인). 쓰지 말 것.

A00275 Bind Pose v01.29 에서 이 버그를 고쳤고, **v01.30 에서 쓰는 방식을 바꿔 마야가 죽던 것을
고쳤다** — [[wip-a00275-skintool-bindpose]].
