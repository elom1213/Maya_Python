---
name: addattr-min-max-raises-not-clamps
description: "addAttr minValue/maxValue makes out-of-range setAttr raise RuntimeError, it does NOT clamp — clamp in Python before writing"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5daa567a-aa4a-4115-99c6-ec8bdb8c00eb
  modified: 2026-08-18T08:48:42.826Z
---

`cmds.addAttr(..., minValue=0.0, maxValue=1.0)` 로 만든 어트리뷰트는 범위 밖 값을 **잘라내지
않는다** — `cmds.setAttr(plug, 1.5)` 가 그대로 예외를 던진다:

```
RuntimeError: setAttr: Cannot set the attribute 'node.attr' past its maximum value of 1.
```

(UI 슬라이더/채널박스는 범위 안에서만 움직이므로 사용자 손으로는 이 에러를 볼 일이 없고,
**스크립트로 초기값을 써 넣을 때만** 터진다.)

**How to apply:** 툴이 계산하거나 UI 에서 받아온 초기값을 `setAttr` 하기 전에 파이썬에서 먼저
클램프한다 — `max(lo, min(hi, value))`. 코드가 값을 "알아서 잘리겠지" 하고 넘기면 조용한 무동작이
아니라 **빌드 전체가 예외로 죽는다**.

**Why:** 마야는 min/max 를 표시 범위가 아니라 **하드 제약**으로 본다.

관련: [[wip-a00390-v02-envelope]], [[mayapy-headless-verify]].
