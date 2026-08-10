---
name: wip-a00275-move-joints
description: A00275 Move Joints 탭 — Edit 토글로 메시를 안 건드리고 조인트 이동 후 재바인드 (v01.08)
metadata: 
  node_type: memory
  type: project
  originSessionId: ee81a66a-5136-4bb8-b44a-7fa187164cdb
  modified: 2026-08-10T01:38:40.392Z
---

A00275_skinTool_V01 **5번째 탭 `Move Joints`** (v01.07→**01.08**, 2026-08-10).

`EDIT JOINTS` 를 켜면 조인트를 아무리 옮겨도 **메시가 전혀 변형되지 않고**, 다시 누르면 그 조인트
배치가 새 바인드 상태로 굳는다. **버텍스별 웨이트는 불변.** UI 조작감은 A00290_BSTool 의 Shape
Editor Edit 토글과 같다(같은 주황 `EDIT_ON_STYLE`).

행렬 원리와 함정(직결 금지)은 [[skincluster-hold-mesh-while-moving-joints]] 참고.

**기존 Bind Pose 탭과 순서가 반대**라 문서에 차이를 명시했다.
- Bind Pose : 조인트를 먼저 옮겨 **메시가 변형된 뒤** 그 결과를 굳힌다(형상 델타를 Orig 에 굽는다).
- Move Joints : **변형 없이** 옮기고 확정한다 → Orig 셰이프도 blendShape 도 안 건드린다.

구현 메모:
- `bind_pose_manager` 의 `_influence_index_map` / `_rebuild_bind_pose` / `resolve_targets` /
  `describe` 를 그대로 재사용(규칙이 동일).
- Cancel : 시작 시점 `bindPreMatrix` + 조인트 트랜스폼을 skinCluster 의 `JUN_jointEditBackup`
  문자열 어트리뷰트에 JSON 으로 저장 → 씬을 저장했다 열어도 취소 가능.
  복원 시 `rotateOrder` 를 `rotate` 보다 **먼저** 써야 오일러 해석이 맞는다.
- 편집 상태는 UI 가 아니라 **씬(노드)** 에 있다 — 편집용 multMatrix 에 `JUN_jointEdit` bool 태그를
  달아 두고, 탭을 열 때 `find_editing_in_scene()` 으로 되찾는다(툴 재실행/다른 창에서도 확정 가능).
  편집 중에는 Load/Clear 를 잠근다(대상을 바꾸면 임시 노드가 씬에 남는다).

검증: mayapy 헤드리스 — 바인드/포즈 상태 양쪽, skinMethod 3종, **웨이트 배열 전체 동일**, Cancel 복원,
성긴 인덱스, 다중 skinCluster, 잠긴 bindPreMatrix, 노드 잔류 없음, Go to Bind Pose, UI 스모크 전부 통과
([[mayapy-headless-verify]], [[qapplication-before-maya-standalone]]).
