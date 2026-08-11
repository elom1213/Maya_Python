---
name: setkeyframe-insert-needs-existing-curve
description: "setKeyframe(insert=True) 는 커브가 있어야 동작한다 — 없으면 조용히 no-op. 레이어 채우기의 함정"
metadata:
  node_type: memory
  type: reference
---

구간의 **빈 프레임을 현재 값 그대로 키로 채울 때**(애니메이션 모양은 그대로 두고 키만 촘촘히):

- 대상 커브가 **있으면** `cmds.setKeyframe(plug, time=f, insert=True)` 가 정답이다. 커브 모양을
  그대로 보존한 채 키만 꽂는다. 값을 계산할 필요가 없고 오차도 없다(실측 1.8e-15).
  이미 키가 있는 프레임에 insert 해도 개수가 늘지 않는다(no-op).
- **커브가 없으면 insert 는 조용히 아무것도 하지 않는다** — 예외도 없고 반환 0, 커브도 안 생긴다.
  애니메이션이 아예 없는 채널, 그리고 **"레이어는 있는데 그 채널 커브가 아직 없는"** 흔한 상황이
  여기 걸린다. 이 경우엔 `cmds.getAttr(plug, time=f)` 로 프레임별 평가값을 읽어 값으로 키를 찍는다.

**값은 쓰기 전에 전부 미리 구할 것.** 레이어 커브에 키가 하나라도 생기면 그 레이어의 기여가 달라져
이후 프레임의 평가값이 흔들릴 수 있다. 계산과 쓰기를 번갈아 하면 그 흔들린 값을 그대로 굳힌다.

**레이어**
- `setKeyframe(animLayer=L, value=V)` 는 레이어 커브에 V 를 그대로 쓰는 게 아니라 **최종 평가값이
  V 가 되도록** 기여분을 역산해 넣는다(additive/override 공통) — 그래서 평가값을 그대로 넘기면 된다.
- 그 레이어의 채널 커브는 `animLayer(L, q=True, findCurveForPlug=plug)`. 채널이 아직 레이어에
  없으면 `animLayer(L, e=True, attribute=plug)` 로 먼저 넣는다.
- 선택된 레이어 조회는 [[animlayer-no-global-selected-query]] 참고.

성능: insert 경로는 프레임 단위로 여러 plug 를 한 번에 넘겨 호출 수를 (프레임×채널) → (프레임)으로.

구현: `A00110_animTool/app/core/fill_key_manager.py` ([[wip-a00110-fill-keys]]).
