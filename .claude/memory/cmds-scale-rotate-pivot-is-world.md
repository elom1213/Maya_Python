---
name: cmds-scale-rotate-pivot-is-world
description: cmds.scale/rotate 의 -pivot 은 -objectSpace 를 줘도 월드 좌표로 읽힌다
metadata: 
  node_type: memory
  type: reference
  originSessionId: bcfa3c1b-bf62-47f4-b38b-70e50bb266e8
  modified: 2026-09-21T02:39:09.274Z
---

`cmds.scale(..., objectSpace=True, pivot=(x,y,z))` / `cmds.rotate(...)` 에서 **`-pivot` 은 월드 좌표**다.
`-objectSpace` 는 **축 방향**만 오브젝트 공간으로 바꾸고 피벗의 해석은 바꾸지 않는다 (mayapy 2024 로 확인:
`translate=(5,0,0)` 인 원의 CV 를 `pivot=(0,0,0)` 으로 2배 하면 로컬 원점이 아니라 **월드 원점** 기준으로 커진다).

**Why:** 오브젝트 공간 값(예: `getAttr .rotatePivot`)을 그대로 넘기면 조용히 엉뚱한 결과가 나온다.
에러가 없어서 "내 구현이 틀렸나" 로 오해하기 쉽다.

**How to apply:**
- 커브·메시의 CV/버텍스를 그 오브젝트의 피벗 기준으로 다루려면 `cmds.xform(node, q=True, ws=True, rp=True)`
  로 **월드 피벗**을 읽어 넘긴다.
- 내 구현을 마야 명령과 대조해 검증할 때 특히 주의할 것 — [[wip-a00400-shape-transform]] 에서
  이 때문에 처음에 다섯 항목이 실패했다(구현은 맞았고 대조 코드가 틀렸다).
- 오브젝트 공간에서 직접 계산하는 쪽이 헷갈리지 않는다: `new = pivot + S * (cv - pivot)` (둘 다 로컬 값).
