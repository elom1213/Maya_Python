---
name: attr-channelbox-and-references
description: 어트리뷰트가 채널박스에 보이는 상태는 셋(keyable / cb / 둘 다 아님)이고, 레퍼런스로 들어온 어트리뷰트는 표시 상태를 바꿀 수 없다 — 만들 때 정해야 한다
metadata:
  node_type: memory
  type: reference
---

유저 어트리뷰트가 **채널박스에 나오는 길은 둘뿐**이다 (Maya 2024 실측).

| 상태 | 채널박스 | 키 |
|---|---|---|
| `keyable = on` | 보인다 | 걸 수 있다 |
| `keyable = off` + `channelBox = on` | 보인다 (non-keyable displayed) | 못 건다 |
| **둘 다 아님** | **안 보인다** (Attribute Editor 에만) | 못 건다 |

**`addAttr` 은 `keyable` 을 주지 않으면 세 번째 상태로 만든다.** 그래서 "만들었는데 안 보인다"
가 생긴다. `keyable = on` 이면 `getAttr -cb` 는 False — 둘은 배타적이다.

**★ 레퍼런스에서 온 어트리뷰트는 표시 상태를 바꿀 수 없다.**

```
setAttr: The attribute 'RIG:ctl.plain' is from a referenced file,
         thus the channelBox state cannot be changed.
```

`keyable` 도 같은 문구로 거부된다. **애니메이션 씬 쪽에서는 손쓸 방법이 없다** →
어트리뷰트를 **만드는 순간에** 보이게 해 둘 것. 한 번 제대로 만들면 파일에 저장되어
(`setAttr -k on` / `-cb on`) **`.ma` · `.mb` 어느 쪽이든 레퍼런스로 불러와도 그대로 보인다.**
레퍼런스된 노드에 **이 씬에서 새로 더한** 어트리뷰트는 고칠 수 있고, 레퍼런스 에디트로 남아
씬을 다시 열어도 유지된다.

**그 밖에**
- `addAttr -h true` 로 숨겨 만든 것도 `setAttr -k/-cb` 로 **되살아난다**.
  `attributeQuery -hidden` 은 계속 True 라고 답한다 — 표시 여부와 별개다.
- **컴파운드는 부모만 켜도 자식이 안 나온다** → 자식(`listChildren`)까지 켤 것.
- 잠긴(locked) 어트리뷰트도 표시 상태는 바뀐다. 잠금은 그대로 둔다.
- `string` 은 `keyable` 을 켜도 채널박스에 안 나온다 → **`channelBox` 로** 켠다.
  `message` 는 채널박스에 값이 없다.
- `attributeQuery(attr, node=n, channelBox=True)` 는 **cb 로 표시 중인 것에도 False** 를 준다
  (믿지 말 것) → `getAttr(plug, channelBox=True)` 로 본다.
- `keyable` 을 끄면 마야가 표시도 같이 끄므로 **끈 다음에 `channelBox` 를 켠다**(순서 중요).
- 어트리뷰트 재정렬(deleteAttr + undo, [[maya-attr-reorder-deleteattr-undo]])은 표시 상태를
  보존한다 — 숨는 원인이 아니다.

적용: `A00145_RigConnect` v01.52 — `app/core/attr_display.py` 가 `Attribute > Create` ·
`Edit > Copy` 가 만든 것을 채널박스로 올리고, `Edit` 의 `Show in Channel Box` 버튼이 이미
숨은 채로 만들어진 것을 되살린다([[a00145-attribute-tab-blendshape-alias]]).
검증은 [[mayapy-headless-verify]].
