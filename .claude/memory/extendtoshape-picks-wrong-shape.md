---
name: extendtoshape-picks-wrong-shape
description: extendToShape() 는 첫 non-intermediate 셰이프를 집어 스킨 안 걸린 셰이프를 줄 수 있다 (kInvalidParameter 원인), polyEvaluate 는 문자열 반환
metadata:
  node_type: memory
  type: reference
---

`(kInvalidParameter): Object is incompatible with this method` 의 가장 흔한 원인.

**`MDagPath.extendToShape()` 는 "첫 번째 non-intermediate 셰이프"를 고를 뿐이다.** 한 트랜스폼
아래 메시 셰이프가 여럿이면(blendShape 타겟 셰이프를 같은 트랜스폼에 정리해 둔 리그, 머지/임포트
잔재) **스킨이 안 걸린 셰이프**가 나온다. 그 dagPath 로 `MFnSkinCluster.getWeights/setWeights` 를
부르면 저 에러로 죽는다. (Orig=intermediate 는 알아서 건너뛴다 — 실측)

→ 셰이프는 **디포머가 실제로 변형하는 것**으로 확정한다. 공용 헬퍼가 있다:
**`Framework.core.maya_shape`** (`shape_path / shape_dag / vertex_count / deformed_shapes /
drives_shape`). `cmds.deformer -q -g` 는 skinCluster/blendShape/lattice 모두에서 동작한다.
웨이트를 읽고 쓰는 코드는 `deformer=` 를 넘길 것. 새 코드에서 `extendToShape()` 를 쓰지 말 것 —
2026-08-12 에 리포 전체(9곳/툴 6종)를 이 헬퍼로 정리했다.

**같은 계열 함정**: `cmds.copySkinWeights` 는 선택 기반이라 셰이프가 여럿인 **트랜스폼을 선택**하면
`A skinCluster node should be specified with the -destinationSkin/-ds flag.` 로 실패한다.
→ **셰이프를 선택**해 넘기면 된다(`ds=` 만 줘서는 안 풀린다 — 실측).

**두 번째 함정**: 셰이프가 여럿인 트랜스폼에 `cmds.polyEvaluate(transform, v=True)` 는
정수가 아니라 **요약 문자열**을 돌려준다 → 뒤에서 `TypeError`. 항상 **셰이프**에 걸 것.
`transform.vtx[i]` 도 모호해져 `skinPercent` 가 조용히 `None` 을 준다.

Maya 2024 실측 — 정확히 이 문구를 내는 경우:
1. skinCluster 가 변형하지 않는 지오의 dagPath 로 get/setWeights
2. 같은 호출에 intermediate(Orig) 셰이프 경로
3. 컴포넌트 이터레이터 타입 불일치(`MItMeshVertex` 에 face comp 등)

**조용히 통과하는**(더 위험한) 것들: dag/comp 가 서로 다른 메시, 범위 밖 버텍스 인덱스,
`setWeights` 배열 길이 불일치, 잘못된 타입으로 함수 세트 **생성**(에러는 나중 메서드에서).

관련: [[skincluster-hold-mesh-while-moving-joints]], [[wip-a00275-expand-bind]]
