---
name: maya-attr-lock-parent-compound
description: setAttr -lock 0 on a child (tx) under a locked parent compound (translate) succeeds silently but the child stays locked — unlock the parent and re-lock the other siblings
metadata:
  node_type: memory
  type: reference
  originSessionId: a77033e9-aeae-47e4-8237-7277835d7edd
  modified: 2026-10-12T08:16:55.396Z
---

`cmds.setAttr("node.translate", lock=True)` 뒤에 `cmds.getAttr("node.tx", lock=True)` 는 **True** 다
(부모 잠금이 자식에 보인다). 그런데 `cmds.setAttr("node.tx", lock=False)` 는 **예외 없이 성공하고
`tx` 는 그대로 잠겨 있다** — 자식 자체 플래그만 꺼지고 부모 잠금이 계속 덮는다 (mayapy 2024 실측).

반대로 `lock=True` 는 부모가 잠겨 있어도 문제 없고, 연결된 어트리뷰트 · 레퍼런스 노드 어트리뷰트도
lock / unlock 모두 된다. lock 변경은 undo 청크로 정상 되돌아간다.

**How to apply:** unlock 을 하고 나서 `getAttr -lock` 으로 **다시 확인**한다. 여전히 잠겨 있으면
`attributeQuery -listParent` 로 부모를 찾아 부모를 풀고, `-listChildren` 의 형제 중 **요청에 없는
것은 다시 잠가** "그 자식만 풀렸다" 가 되게 한다. 부모의 부모가 또 잠겨 있을 수 있으니 풀릴 때까지
위로 반복. 비교는 `attributeQuery -longName` 으로 긴 이름끼리(채널박스는 `tx`, listChildren 은
`translateX` 를 준다). 구현: `A00030_quickTool_V02/app/core/quick_ops.py` 의 `_unlock_plug`.

관련: [[attr-channelbox-and-references]], [[xform-silent-on-locked-channels]]
