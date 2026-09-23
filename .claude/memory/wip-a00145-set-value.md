---
name: wip-a00145-set-value
description: "A00145 Attribute > Set Value (v01.51) — Number Tool 이식, enum 은 이름으로 넣고 오브젝트마다 값을 다시 찾는다"
metadata: 
  node_type: memory
  type: project
  originSessionId: 960691e9-db72-413c-90a3-01b48c764a99
  modified: 2026-09-18T01:09:21.239Z
---

A00145 Attribute > Set Value 하위 탭(v01.51, 2026-09-18)은 `_archive/.../JUN_PY_numberTool_V01_01.py` 의 이식이다.
로직은 `app/core/attr_value_manager.py`. 원본도 같은 기능으로 `JUN_PY_numberTool_V01_02.py` 를 새로 뒀다(V01_01 은 그대로, 현행은 A00145).

- 목록 = 기본 **교집합**(모든 오브젝트가 가진 것), float/int/bool/enum 만. **v01.56 `Include Non-Common`** 이면 합집합,
  행마다 `[k/n]`(Target Edit 표기). 행 글자에 표식이 붙으므로 **이름은 UserRole** 에서 읽는다. 종류·범위·Get 은
  `objects[0]` 이 아니라 **그 어트리뷰트를 가진 첫 오브젝트**(`_aval_owner`) — [0] 에 없을 수 있다. `Channel Box Only` 는 `connect_manager.channel_box_attrs` 를 같이 쓴다.
- Step 은 오브젝트 **리스트 순서**대로 누적, `Repeat every N` 으로 되돌아감. enum 은 항목 **인덱스**를 Step 만큼 옮기고, 적용할 땐 **이름**으로 오브젝트마다 값을 다시 찾는다(`Off:Low=5:High` 처럼 값이 건너뛰는 enum 대응).
- 각도(doubleAngle)의 `attributeQuery(min/max)` 는 UI 단위(deg)로 돌아와 setAttr 와 같다 — 변환 불필요(mayapy 실측).

**Why:** 사용자가 원래 원한 것 = 여러 오브젝트의 같은 어트리뷰트를 한 번에, enum 은 텍스트로 골라서.
**How to apply:** 이 탭을 고칠 때 enum 을 정수 값으로 넣도록 되돌리지 말 것. 관련 [[addattr-min-max-raises-not-clamps]] · [[animated-attr-setkeyframe-plus-setattr]]
