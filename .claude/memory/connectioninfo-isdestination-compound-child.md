---
name: connectioninfo-isdestination-compound-child
description: connectionInfo -isDestination is True for a child whose parent compound is connected (source = parent plug); connectAttr -force on that child silently breaks the parent connection
metadata:
  type: project
---

`cmds.connectionInfo("C.tx", isDestination=True)` 는 `C.tx` 자신이 아니라 **부모 `C.t` 가 연결돼 있어도 True** 를
돌려주고, `sourceFromDestination` 은 자식 plug 가 아닌 **부모 plug(`X.translate`)** 를 준다. 정확히 자기 자신인지는
`isExactDestination` 이 따로 있다. 반대로 그 자식에 `connectAttr(..., force=True)` 를 걸면 실패하지 않고 **부모
연결을 끊고 자식에 건다** (mayapy 2024 실측, 2026-10-26).

**Why:** A00145 Connect 탭의 `Force (replace existing connections)` 체크박스(v01.67, 기본 OFF) 를 만들 때 "이미
연결됐는가" 판정에 `isDestination` 을 썼다. 부모가 연결된 자식은 어차피 바로 못 걸므로 "연결됨 = 그대로 둔다" 쪽으로
묶는 것이 맞았고, Force 쪽은 부모 연결까지 끊긴다는 걸 알고 써야 한다. `connect_manager.incoming_plug()` 가 이 질의를
감싼다.

**How to apply:** "연결 유지/교체" 옵션을 만들 땐 대상 plug 의 `isDestination` 만 보면 되고(드라이버 팬아웃은 막지
말 것), 로그엔 `sourceFromDestination` 결과를 그대로 적으면 부모 compound 가 걸린 경우도 자연히 드러난다.
자식만 정확히 봐야 하면 `isExactDestination`. 관련: [[compound-connect-leaves-child-connections]] ·
[[wip-a00145-connect-rules]]
