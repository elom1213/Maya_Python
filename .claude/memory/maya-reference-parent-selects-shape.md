---
name: maya-reference-parent-selects-shape
description: A control transform under a Reference-display parent inherits 'unselectable'; if only its shape overrides to normal, viewport clicks select the SHAPE - set overrideDisplayType 0 on the transform too
metadata:
  type: project
---

컨트롤 트랜스폼을 **Reference 표시(`overrideDisplayType 2`)인 부모** 아래 두고 **셰이프에만** `overrideEnabled` + normal 을 주면,
트랜스폼은 부모의 Reference 를 물려받아 선택 불가가 되고 Maya 는 뷰포트 클릭에서 선택 가능한 첫 노드인 **셰이프**를 고른다
(A00580 보드에서 사용자 확인 2026-10-26: "커브를 선택하면 쉐입이 선택돼"). 트랜스폼에도 `overrideEnabled 1` + `overrideDisplayType 0`
을 명시하면 트랜스폼이 선택된다.

**Why:** 틀(트랙 · 라벨)을 Reference 로 두고 컨트롤만 선택되게 하려는 구조에서 흔히 생긴다. mayapy 검증으로는 못 잡는다(뷰포트 픽).

**How to apply:** 컨트롤을 만들 때 셰이프 색과 함께 **트랜스폼의 표시도 normal 로 명시**한다. 검증엔 "컨트롤 트랜스폼 overrideDisplayType == 0,
부모 == 2" 를 넣는다. 관련: [[wip-facial-arkit52-ctl-v05]]
