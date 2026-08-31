---
name: animlayer-copy-cut-traps
description: "애님 레이어 사이 키 이동 - copyKey/pasteKey 는 animLayer 를 받지만 cutKey 는 안 받고, 비멤버 plug 는 paste 실패 + findCurveForPlug 가 None"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c9193b2f-22fa-4f73-9fcb-d5a3af9da721
  modified: 2026-08-31T01:24:47.537Z
---

애니메이션 **레이어 사이로 키를 옮길 때** mayapy(Maya 2024)로 확인한 네 가지. 넷 다 조용히
어긋나는 쪽이라 미리 알고 짜야 한다.

1. **`copyKey(plug, animLayer=L)` / `pasteKey(plug, animLayer=L, option=...)` 는 된다.**
   붙여넣기는 클립보드의 **원래 시간**에 들어가고(현재 프레임 아님), **대상 레이어에 그 채널
   커브가 없으면 만들어 준다.** `copyKey` 는 시간 플래그가 없으면 **그 커브의 모든 키**를 담고,
   커브가 없으면 **0 을 돌려준다**(예외 아님) — 그 반환값으로 "이 레이어엔 키가 없다"를 가른다.
2. **`pasteKey` 는 대상이 `BaseAnimation` 이 아닌데 그 plug 가 레이어 멤버가 아니면 실패한다**
   (`RuntimeError: Nothing to paste to`). 먼저 `animLayer(L, e=True, attribute=plug)` 로 넣어야
   한다. **`BaseAnimation` 은 멤버가 아니어도 그냥 붙는다**(커브까지 만들어 준다).
3. **`cutKey` 에는 `animLayer` 플래그가 **없다**(`TypeError: Invalid flag 'animLayer'`).
   잘라내기는 소스 **커브 노드**를 찾아 `cutKey(curve, time=..., clear=True)` 로 해야 한다.
   `clear=True` 는 클립보드를 건드리지 않는다. 커브의 키를 **다 지우면 커브 노드도 사라진다**.
4. **`animLayer(root, q=True, findCurveForPlug=plug)` 는 어느 레이어에도 안 든 오브젝트에
   `None` 을 준다** — 평범한 애님 커브가 멀쩡히 있어도 그렇다. 그때는 plug 에 **직접 연결된**
   `animCurve`(`listConnections(type="animCurve", skipConversionNodes=True)`)가 base 커브다.
   레이어에 든 plug 는 앞단이 `animBlendNode*` 라 이 조회에 안 걸리므로 두 판정이 겹치지 않는다.

**값 의미**: `copyKey`/`pasteKey` 는 **커브 값을 그대로** 옮긴다 — 레이어 기여분을 다시
계산하지 않는다. `setKeyframe(animLayer=L, value=V)` 가 **최종 평가값이 V 가 되도록 역산**하는
것과 **다르다**([[wip-a00110-fill-keys]]). Base(절대값) → additive 로 옮기면 최종 결과가 달라진다.

쓰는 곳: [[wip-a00110-layer-key-copy]]. 레이어 목록 조회 함정은 [[animlayer-no-global-selected-query]].
