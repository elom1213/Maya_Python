---
name: setattr-int32array-no-count
description: cmds.setAttr 은 배열 타입마다 인자 모양이 다르다 — Int32Array 는 개수를 붙이면 안 되고(값이 하나면 에러 없이 개수가 저장된다), pointArray 는 튜플 그대로 넘겨야 한다
metadata:
  type: reference
---

`cmds.setAttr` 로 배열을 쓸 때 **타입마다 인자 모양이 다르다**. 하나로 통일해 쓰면
조용히 틀린 값이 들어간다 (Maya 2024 mayapy 실측).

```python
# pointArray — 개수 + (x, y, z, w) 튜플 **그대로**
cmds.setAttr(plug, len(pts), *pts, type="pointArray")     # pts = [(x,y,z,w), ...]
# 풀어서 float 로 넘기면: "Error reading data element number 2: 0.1"

# componentList — 개수 + 문자열
cmds.setAttr(plug, len(comps), *comps, type="componentList")   # ["vtx[0]", "vtx[3:5]"]

# Int32Array — **개수를 붙이지 않는다.** 리스트를 통째로 넘긴다
cmds.setAttr(plug, [0, -1, 3], type="Int32Array")
```

**Why:** `Int32Array` 에 개수를 붙이면 마야가 **개수를 첫 값으로 읽고 나머지를 버린다.**
값이 여럿이면 `Too much data was provided` 로 죽지만, **값이 하나뿐이면 에러 없이
개수(=1)가 값으로 저장된다** — 조용한 오작동이다.

```
setAttr(p, 2, 0, 3,  type="Int32Array")  ->  [2]      # 값이 아니라 개수가 들어갔다
setAttr(p, 1, -1,    type="Int32Array")  ->  [1]      # 〃
setAttr(p, [0,-1,3], type="Int32Array")  ->  [0,-1,3] # 이게 맞다
```

**How to apply:** 배열 setAttr 을 감싸는 헬퍼를 쓸 때 `Int32Array` 를 따로 갈라 둔다
(`A00290_BSTool/app/core/target_order_manager.py` 의 `_set_array` 가 그렇게 돼 있다).
`blendShape.targetDirectory[d].childIndices` 를 쓰다 걸렸다 —
[[wip-a00290-target-order-tab]] 참고.
