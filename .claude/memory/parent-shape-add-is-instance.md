---
name: parent-shape-add-is-instance
description: "`parent -s -add` instances the shape (one node, two parents) — deleting the source hierarchy deletes the added shape too; copy via duplicate + parent -r -s instead"
metadata:
  type: reference
---

`parent -s -add shape target` 은 쉐입을 **인스턴스**로 매단다 — 노드 하나, 부모 둘
(`listRelatives(shape, allParents=True)` → `['A', 'B']`, mayapy 2024 실측).

- `select -hi A; delete`(아웃라이너 계층째) · `delete |A|AShape` → **B 쪽 쉐입도 삭제**
- `delete A` / `doDelete`(트랜스폼만) → B 에 남음
- A 의 CV 편집이 B 에도 보인다

**독립 사본으로 붙이는 법**: `duplicate(src, rr=True, un=False)` → 새 쉐입을 `parent(shape, tgt, r=True, s=True)`
로 이동 → 임시 트랜스폼 삭제. `-r -s` 는 **로컬 CV 값**을 가져가므로 두 트랜스폼이 다르면 모양이 튄다 →
CV 월드 위치를 미리 받아 `xform(cv, ws=True, t=...)` 로 되돌린다. intermediate(Orig) 쉐입은
`listRelatives(noIntermediate=True)` 로 제외.

A00400 `Edit > Combine`(v01.11)이 이 방식. [[wip-a00400-curvetool]]
