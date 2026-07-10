---
name: uuid-safe-rename-duplicate-names
description: rename/DAG-edit tools break on duplicate scene names because TSL stores short names; hold nodes by UUID instead
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 92603683-fcd8-4828-9270-90a9f2a9957e
---

Maya 툴에서 오브젝트 이름을 바꾸거나 DAG 경로로 노드를 다루는 코드는, 씬에 **같은 이름의 오브젝트가 여러 개** 있으면 깨질 수 있다. 공용 TSL 위젯(`JUN_mod_tsl_qt_v01`)과 `cmds.ls(sl=True)`는 기본적으로 **short name** 을 저장/반환하는데, 동일 이름이 있으면 short name 이 모호해서 `cmds.rename("joint_02", ...)` 가 `RuntimeError: Invalid path` 로 실패한다. 부모를 rename 하면 자식의 DAG 경로가 바뀌어 미리 잡아둔 경로도 무효가 된다.

**Why:** UUID 는 rename·재부모화 중에도 바뀌지 않는 유일하게 안정적인 노드 핸들이다. short name/경로는 둘 다 모호하거나 휘발된다.

**How to apply:**
- 입력을 `cmds.ls(name, long=True)` 로 정규화하고 자손은 `listRelatives(..., fullPath=True)` 로 수집.
- rename 전에 `(uuid, new_name)` 배정을 **먼저 전부 계산**한 뒤, `cmds.ls(uuid, long=True)[0]` 로 현재 경로를 매번 다시 해석해 rename.
- 헬퍼 참고 구현: `A00330_NamingTool/app/core/naming_ops.py` 의 `_to_uuid()` / `_rename_by_uuid()` (v01.01, 2026-07-03).

사용자가 이 패턴을 적용하라고 할 때 쓰는 말: **"UUID 기반 리네임 패턴 적용해줘"** 또는 **"동일 이름 안전하게(UUID 핸들로) 처리해줘"**. 관련: [[explain-in-korean]] [[ui-text-english-only]]
