---
name: wip-a00275-edit-mesh
description: A00275 Edit Mesh 탭 — 웨이트 불변으로 바인드된 메시 수정 (envelope 0 + pnts 를 rest 로 이동 + geomMatrix) (v01.14)
metadata: 
  node_type: memory
  type: project
  originSessionId: cce9837c-ee83-4545-8532-e6317949f1f2
  modified: 2026-08-24T08:16:57.717Z
---

A00275_skinTool_V01 **6번째 탭 `Edit Mesh`** (v01.13→**01.14**, 2026-08-24). 코어는
`app/core/mesh_edit_manager.py`. Move Joints 와 **정반대 방향** — 조인트는 그대로 두고 메시를 고친다.

`EDIT MESH` 토글을 켜면 skinCluster **envelope 0** 으로 rest 셰이프를 보여 주고 스킨이 잠가 둔
메시 트랜스폼 t/r/s 를 풀어 준다. 버텍스/엣지/페이스도, **메시 자체도** 옮길 수 있고, 다시 누르면
그 형상이 새 rest 가 된다. `weightList` 를 읽지도 쓰지도 않아 **웨이트 동일성은 정의상 보장**.
UI 조작감·빨간 EDIT_ON_STYLE·씬에 상태 저장은 [[wip-a00275-move-joints]] 와 같은 규칙.

**핵심은 확정 단계다 — 셋 다 mayapy 실측으로 잡았다:**

1. **뷰포트 버텍스 편집은 `<shape>.pnts` 로 들어가고 그건 스킨 *뒤*에 더해진다.** 두 포즈에서
   재면 월드 오프셋이 **똑같다**(포즈 무관 상수). 같은 편집이 체인 헤드(Orig)에 있으면 조인트를
   따라 회전한다. → 확정 시 그 델타를 **헤드로 옮기고**(`bp._bake_delta`) 셰이프 tweak 은 시작
   시점 값으로 되돌린다. 안 옮기면 "고친 메시" 가 아니라 **"화면에만 맞는 메시"**.
   체인 앞쪽 `tweak` 노드에 떨어진 편집은 이미 스킨 입력이라 손댈 것이 없다 — 둘 다 처리.
2. **skinCluster 는 바인드할 때 메시 트랜스폼 t/r/s 9개를 잠근다.** 안 풀면 "메시 자체의 이동" 이
   `The attribute '...translateX' is locked` 로 막힌다. 잠금 상태를 기억했다 확정 때 되돌린다.
3. **메시를 옮기면 `skinCluster.geomMatrix`(멀티 아님, 단일 matrix)를 따라 갱신**해야 한다:
   `geomMatrix' = geomMatrix * G0^-1 * G1`. 갱신하면 **처음부터 그 자리에서 바인드한 리그와
   결과가 완전히 같다**(실측 오차 0). 안 하면 옛 자리 기준 변형이 새 자리에 얹혀 어긋난다.

기타 구현 메모:
- 편집 상태는 셰이프의 `JUN_meshEdit`(bool) / `JUN_meshEditData`(JSON) 에 둔다. 노드는 UUID 로
  보관([[uuid-safe-rename-duplicate-names]]). Cancel 은 tweak 스냅샷(sparse)·트랜스폼·envelope·잠금 복원.
- 편집 중에 새로 생긴 `pnts` element 는 0 으로 덮지 말고 `removeMultiInstance` 로 지운다
  (0 만 써 두면 셰이프가 계속 "tweak 을 가진" 상태로 남는다).
- 리그가 포즈 중이면 켜는 순간 rest 로 점프한다 — 버그가 아니라 고쳐야 할 대상이 rest 이기
  때문. 그 사실을 로그로 알린다.
- 헤드~스킨 사이 디포머가 델타를 그대로 통과시키지 않을 수 있어 **확정 후 형상을 다시 재
  비교**하고 어긋난 크기를 로그에 적는다.

검증: mayapy 헤드리스 코어 51항목(바인드/포즈, 메시 이동 골든 비교, blendShape 체인, 앞쪽 tweak
노드, Cancel, undo, 다중 메시, 가드) + UI 스모크 25항목 통과
([[mayapy-headless-verify]], [[qapplication-before-maya-standalone]]).
관련: [[wip-a00275-skintool-bindpose]], [[skincluster-hold-mesh-while-moving-joints]],
[[undo-chunk-by-default]], [[extendtoshape-picks-wrong-shape]]
