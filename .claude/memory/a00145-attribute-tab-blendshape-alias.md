---
name: a00145-attribute-tab-blendshape-alias
description: "A00145 Attribute tab (copy attrs to other objects w/ prefix/suffix) + blendShape targets are weight[] aliases - how to list/copy them"
metadata: 
  node_type: memory
  type: project
  originSessionId: 91ab0dea-4b6f-4134-a5cd-3d3ccc44c43a
---

A00145_RigConnect v01.17 — **Attribute 탭** 신설(어트리뷰트를 골라 다른 오브젝트에 같은 정의로
재생성, Prefix/Suffix) + **blendShape 타겟 이름 나열**(Attribute·Connect 탭). DONE (Maya 검증 + 푸시).

**Why (핵심 함정 — blendShape):** 타겟은 별도 어트리뷰트가 아니라 **`weight[i]` 멀티의 별칭(alias)**.
- `listAttr(bs, userDefined=True)` → `attributeAliasList` 하나뿐. 타겟 안 나옴.
- `getNextFreeMultiIndex` 로 `weight` 멀티를 펼치면 **인덱스 0(첫 타겟) 하나만** 잡힌다.
- **`attributeQuery` 는 별칭을 부모 멀티(`weight`)로 해석한다** → 별칭 스펙을 그대로 addAttr 하면
  타겟 하나를 복사해도 **`weight` 라는 multi 어트리뷰트**가 생긴다.

**How to apply:**
- 타겟은 `cmds.aliasAttr(bs, q=True)`(평면 [alias, attr, ...])에서 직접 읽고 `weight[i]` 인덱스로 정렬.
  → `tools/A00145_RigConnect/app/core/blendshape_utils.py` (A00290_BSTool 에도 같은 유틸 존재;
  툴 간 import 는 하지 않는 게 이 repo 관례).
- 별칭 스펙은 long/short name 을 **타겟 이름**으로, `multi=False` 로 덮어쓸 것. 복사된 attr 은
  float / keyable / soft 0~1 / hard -10~10 (blendShape weight 정의 그대로).
- 어트리뷰트 복제 시 **short name 은 이름을 안 바꾼 경우에만 유지** — prefix/suffix 로 바뀌었는데
  원본 short name 을 그대로 쓰면 다른 어트리뷰트와 충돌한다.
- 컴파운드 자식(`tintR`)은 목록에서 제외 — 부모 복사 시 같이 생기고, 자식만 addAttr 불가.
  `usedAsColor` 는 `float3` 에만 붙일 수 있다(`double3` 이면 Maya 가 거부).

관련: [[wip-a00145-skin-constraint-types]], [[mayapy-headless-verify]], [[undo-chunk-by-default]]
