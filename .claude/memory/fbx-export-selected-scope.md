---
name: fbx-export-selected-scope
description: FBX export selected 의 내용은 씬을 안 건드리고 FBXExportIncludeChildren/InputConnections 로 통제한다
metadata: 
  node_type: memory
  type: reference
  originSessionId: 832a604d-822f-406b-a725-dcd47d36b498
  modified: 2026-08-28T08:20:50.381Z
---

`cmds.file(..., typ="FBX export", es=True)` 가 무엇을 담을지는 **MEL `FBXExport*` 옵션**이 정한다
(cmds 호출도 이 옵션을 그대로 따른다). 특정 노드를 FBX 에서 빼려고 **노드를 옮기거나 숨길 필요가 없다.**

- **`FBXExportIncludeChildren -v false`** → *export selected* 가 **선택한 노드만** 내보낸다.
  선택 안 한 **조상(부모 그룹)은 계층 유지용으로 따라 나오고**, 선택 안 한 자손은 빠진다.
  → 내보낼 노드를 전부 명시로 선택하면 FBX 내용을 정확히 통제할 수 있다.
  선택한 트랜스폼의 **shape 은 그대로 나가고**(자식이지만 예외), skinCluster · 애님 커브도 살아 있다.
- **`FBXExportInputConnections -v false`** → 선택 노드에 **입력으로 연결된 노드**를 안 딸려 보낸다.
  기본값이 **on** 이라, 컨스트레인된 조인트를 뽑으면 **드라이버 로케이터/컨트롤러가 FBX 루트에
  섞여 들어온다.** 조인트만 뽑을 때는 꺼야 한다. (끈다고 애님 커브가 사라지지는 않는다.)
- 두 옵션 모두 **전역 상태**다 — `-q` 로 읽어 두고 export 후 되돌린다. `fbxmaya` 로드 확인 필수.

씬을 건드리는 옛 방식(월드로 unparent 후 복원 · shape `intermediateObject` 토글)은
**잠김/연결/컨스트레인/레퍼런스 노드에서 애초에 실패**하고, shape 만 숨기면 **빈 트랜스폼이
FBX 에 null 로 남는다.** 위 옵션 방식은 그 함정이 전부 없다.

[[wip-a00040-joints-only-export]] 에서 이 방식으로 갈아탔다. 확인은 [[mayapy-headless-verify]].
