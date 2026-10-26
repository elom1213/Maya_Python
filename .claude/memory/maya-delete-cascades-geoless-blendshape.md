---
name: maya-delete-cascades-geoless-blendshape
description: A blendShape with no geometry is deleted by Maya whenever a connected node is deleted (animCurve delete, cutKey -clear, deleting a downstream pma) - attach dummy blendShapes to a hidden plane
metadata:
  type: project
---

지오메트리 없는 `blendShape`(createNode 로 만든 더미, weight 별칭만 쓰는 것)는 **연결된 노드를 지우는 순간 Maya 가 "쓰이지 않는
디포머" 로 보고 노드째 지운다** (mayapy 2024 실측 2026-10-26): weight 에 걸린 animCurve 를 `delete` · `cutKey -clear` · 그 weight 를
입력으로 받는 `plusMinusAverage` 를 `delete`(입력이 걸린 채) — 전부 blendShape 가 사라지고, 그 노드에 연결돼 있던 다른 노드까지 함께 간다.
값 0 · 미연결 weight 원소는 저장 때 빠져 별칭이 허공을 가리키기도 한다. **숨긴 4점 `polyPlane` 에 붙이면 전부 살아남고** 미연결 원소도
저장 왕복에서 남는다. 별칭 자체는 지오메트리 없이도 `.ma`/`.mb` 왕복에서 살고 A00480 FileTool 도 찾지만, 위 삭제 함정 때문에 쓸 수 없다.

**Why:** A00580 FacialBoardBuilder 에서 `BS_Face_CSV` 를 메시 없이 만들었다가 verify T6(베이크 뒤 커브 정리)에서 노드가 통째로 사라졌다.
V04 의 "Faical" 글자 메시는 그 역할(디포머를 살려 두기)을 하고 있었다.

**How to apply:** CSV · 키 입력용 더미 blendShape 는 **숨긴 평면에 걸어** 만든다. 더미에 연결된 유틸리티 노드를 지울 땐 **입력을 먼저
떼고** 지운다. `aliasAttr -q` 순서는 저장 뒤 plug 문자열 순으로 바뀌므로 순서가 아니라 별칭↔인덱스 대응을 비교한다.
`transformLimits` 는 연결된 입력값도 자른다(2 → 1) — 리밋이 있으면 뒤로 경로에 clamp 가 필요 없다.
관련: [[wip-facial-arkit52-ctl-v05]], [[blendshape-target-name-vs-alias]]
