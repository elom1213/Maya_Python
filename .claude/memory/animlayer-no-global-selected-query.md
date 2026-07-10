---
name: animlayer-no-global-selected-query
description: "Maya animLayer has no global \"selected layers\" query; -selected is per-layer and needs a layer arg"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 03f4c1fe-28fa-44d8-8877-eaf3283167bf
---

`cmds.animLayer(q=True, selected=True)` (레이어 인자 없이) 는 `RuntimeError: No valid query flags
were specified.` 로 죽는다. `-selected` 는 **레이어 이름을 인자로 줘야** 그 레이어의 선택 여부(bool)를
돌려주는 per-layer 쿼리다. Maya 에는 "선택된 레이어 목록"을 주는 전역 쿼리 플래그가 없다.

선택된 레이어를 얻는 올바른 방법:
```python
layers = cmds.ls(type="animLayer") or []           # BaseAnimation 포함
root = cmds.animLayer(q=True, root=True)            # 전역 쿼리는 OK
selected = [l for l in layers if cmds.animLayer(l, q=True, selected=True)]
```
`override`(`animLayer(layer, q=True, override=True)`), `mute` 도 마찬가지로 레이어 인자 필요.

A00110_animTool 의 Follow 탭(`follow_match_manager._resolve_layer`)에서 이 패턴을 쓴다. 이 repo 의
다른 애니 레이어 작업에도 동일하게 적용할 것.
