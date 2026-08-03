---
name: maya-toggle-cmd-not-undoable
description: cmds.toggle(localAxis 등)은 undo 큐에 아무것도 안 남겨 Ctrl+Z 가 이전 작업을 지운다 — setAttr 로 쓸 것
metadata: 
  node_type: memory
  type: reference
  originSessionId: 8159c5e9-39b3-41e1-9acb-4a6386fdfd25
  modified: 2026-08-03T01:07:19.892Z
---

`cmds.toggle(node, localAxis=True)` (MEL `toggle -localAxis`) 는 값은 바꾸지만 **undo 큐에
아무것도 남기지 않는다**. `undoInfo(openChunk/closeChunk)` 로 감싸도 빈 청크라서, 실행 직후
Ctrl+Z 를 누르면 로컬 축이 아니라 **그 이전 작업이 취소된다**(mayapy 2024 실측: toggle 후 undo
하니 joint 생성이 되돌아감).

**Why:** 뷰포트 표시 토글이라 무해해 보이지만, 툴 버튼으로 만들면 사용자의 Ctrl+Z 가
엉뚱한 작업을 날리는 조용한 버그가 된다.

**How to apply:** 표시 어트리뷰트는 `cmds.setAttr(node + ".displayLocalAxis", value)` 로 직접
쓴다(정상 undo). 절대 상태(ON/OFF)라서 "현재 값 진단 → 다를 때만 setAttr" 패턴도 자연스럽다.
덤: shape 에는 `displayLocalAxis` 가 없다 — `ls(sl=True, objectsOnly=True)` 결과가 shape 면
부모 transform 으로 올라가야 하고, shape 에 toggle 을 걸면 에러 없이 무시된다.
적용 예: A00030_quickTool `JUN_cmd_set_local_axis` (v01.15). 관련 [[undo-chunk-by-default]],
[[mayapy-headless-verify]].
