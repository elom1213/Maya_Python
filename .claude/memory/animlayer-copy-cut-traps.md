---
name: animlayer-copy-cut-traps
description: "애님 레이어 사이 키 이동 - copyKey/pasteKey 는 animLayer 를 받지만 cutKey 는 안 받고, 비멤버 plug 는 paste 실패 + findCurveForPlug 가 None · 커브를 다 지우면 blend 입력에 마지막 값이 정적으로 남는다(월드가 틀어지는 원인)"
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

5. **커브를 다 지우면 blend 노드 입력에 지우던 순간의 값이 정적으로 남는다**(2026-10-29 실측). Base 커브
   → 맨 아래 `animBlendNode*.inputA`, 레이어 커브 → 그 레이어 노드의 `inputB`. 그래서 커브를 다른 레이어로
   옮기고 잘라내면 **남은 정적값 + 옮긴 커브**가 돼 월드가 틀어진다(Base → a 6.0, a → b 8.0, a → Base 14.1).
   마야 자체 `animLayer -e -extractAnimation` 도 같은 상태를 만든다. **`setAttr` 로 plug 에 쓰면 활성
   레이어의 `inputB` 로 가서 소용없다** — 그 입력 plug 에 직접 identity(0 · Multiply 스케일은 1)를 써야
   정확히 돌아온다(0.0). override 레이어는 identity 가 없으니 `animLayer -e -removeAttribute` 로 뺀다
   (additive 도 removeAttribute 면 0.0 이지만 멤버십이 사라진다). 사슬은 `plug <- bn.output[X] <- bn.inputA[X]
   <- ...` 로 내려가고 어느 레이어 노드인지는 `animLayer -q -blendNodes` 로 가른다.
6. **대상이 커브 없이 들고 있던 정적값은 붙여넣기가 덮는다.** Base 정적값 c, additive 멤버 정적값 d 는
   `pasteKey` 뒤에 `inputB` 가 커브에 연결돼 읽을 수 없다 — **붙여넣기 전에 읽어** 붙여넣은 키에 합성한다
   (`keyframe -e -r -vc c`, Multiply 스케일은 `scaleKey -vs c -vp 0`). by-component 는 8.9e-16 으로 정확,
   **by-layer 회전에 0 아닌 회전을 합성하면 0.30 근사**(회전 합성은 축별 덧셈이 아니다). 기본 레이어
   `rotationAccumulationMode` 는 standalone 에서 0(by-component).

**값 의미**: `copyKey`/`pasteKey` 는 **커브 값을 그대로** 옮긴다 — 레이어 기여분을 다시
계산하지 않는다. `setKeyframe(animLayer=L, value=V)` 가 **최종 평가값이 V 가 되도록 역산**하는
것과 **다르다**([[wip-a00110-fill-keys]]). Base(절대값) → additive 로 옮기면 최종 결과가 달라진다.

쓰는 곳: [[wip-a00110-layer-key-copy]](v02.28 `Keep Result` 가 §5·§6 처방을 구현). 레이어 목록 조회 함정은 [[animlayer-no-global-selected-query]].
