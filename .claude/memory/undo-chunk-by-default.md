---
name: undo-chunk-by-default
description: Maya 씬을 여러 번 변경하는 코드는 요청 없이도 Framework.core.maya_undo.undo_chunk() 로 묶는다
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fe972a59-a60c-487d-9f5c-3798f34599a5
---

Maya 씬을 **여러 번 변경**하는 코드(루프 안의 `cmds` 호출, 생성+연결+삭제 조합 등)는 사용자가
따로 요청하지 않아도 **항상** `Framework/core/maya_undo.py` 의 `undo_chunk()` 컨텍스트 매니저로
묶어서 **Ctrl+Z 한 번**에 되돌아가게 만든다.

```python
from Framework.core.maya_undo import undo_chunk

with undo_chunk():
    for obj in objs:
        cmds.select(obj, replace=True)
        cmds.cluster(relative=True)
```

기준:
- 여러 `cmds` 씬 변경이 논리적으로 한 동작 → `undo_chunk()`
- 단일 `cmds` 호출 → 불필요 (Maya 가 이미 한 undo 스텝)
- 읽기 전용 코드 → 불필요

**Why:** 사용자가 A00030_quickTool 에 "선택한 오브젝트마다 클러스터 생성" 버튼을 요청했을 때,
undo 를 묶지 않으면 오브젝트 N 개에 Ctrl+Z 를 N 번 눌러야 한다. 사용자가 "다음부터 어떻게 요청하면
되냐"고 물었고 — 매번 요청할 일이 아니라 기본값이어야 하는 규칙이라 저장한다.

**How to apply:** `cmds.undoInfo(openChunk=True)` / `closeChunk` + `try/finally` 를 직접 복붙하지 말 것.
그 패턴은 이미 `undo_chunk()` 로 통일돼 있고(20+ 툴이 사용), 헬퍼가 예외 시 chunk 누수까지 막는다.
arch A(maya.cmds) 툴에서도 `from Framework.core.maya_undo import undo_chunk` 로 그대로 쓸 수 있다.

관련: [[prefer-pyside-for-new-tools]], [[ui-text-english-only]]
