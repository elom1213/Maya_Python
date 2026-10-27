---
title: Framework.core.maya_fbx — FBX 플러그인 · "선택한 것만" FBX 내보내기 헬퍼
aliases: [maya_fbx, fbx_options, collect_export_nodes, FBXExportIncludeChildren]
tags: [maya-python, framework, fbx, export]
updated: 2026-10-27
---

# `Framework.core.maya_fbx`

A00480_FileTool 의 `app/core/fbx_plugin.py` + `export_ops.py` 에 있던 FBX 부분을 2026-10-26 에 공용으로 올렸다.
**A00480 Export 탭(마야 안)** 과 **A00210_FileManager Maya > Export(mayapy 워커)** 가 같은 코드로 FBX 를 쓴다 —
릴리즈본은 툴 간 import 금지([Release_Layout](Release_Layout.md))라 Framework 에 두어야 두 툴의 릴리즈에 다 실린다.
A00480 의 두 모듈은 얇은 재노출이다(동작 동일, mayapy 11 항목 확인).

```python
from Framework.core import maya_fbx

maya_fbx.ensure_fbx_plugin()                                    # (ok, logs) - fbxmaya 로드
maya_fbx.collect_export_nodes(root, excluded_keys, joints_only=True, prune_constraints=False)   # (kept, pruned) fullPath
with maya_fbx.fbx_options(include_children=False, input_connections=False, bake_complex_animation=False):
    cmds.file(path, force=True, options="v=0;", typ="FBX export", pr=True, es=True)
maya_fbx.export_selected(nodes, path, include_children=False, input_connections=False, bake_complex_animation=False)
maya_fbx.filter_members(members, excluded_keys)                 # 타입 필터(FILTER_TYPES: mesh · joint)
maya_fbx.get_unique_filepath(path)  ·  maya_fbx.short_name(name)  ·  maya_fbx.is_joint(n)  ·  maya_fbx.is_constraint(n)
with maya_fbx.import_options(quaternion="euler", mode="add", fill_timeline=None):   # 2026-10-27
    mel.eval('FBXImport -f "..."')
```

| 이름 | 하는 일 |
|------|---------|
| `ensure_fbx_plugin()` | `fbxmaya` 가 없으면 올린다. `(성공, 로그)` — 플러그인이 없으면 `cmds.file(typ="FBX export")` 가 `Invalid file type` 으로 죽으므로 먼저 부른다 |
| `collect_export_nodes(root, excluded_keys, joints_only, prune_constraints)` | root 계층을 펼쳐 **내보낼 노드 / 뺄 노드**를 가른다. 씬은 건드리지 않는다. `joints_only` = joint 아래 non-joint 를 자손까지 뺀다(joint 밑 그룹 안의 joint 도 그룹과 함께 빠진다). `prune_constraints` = 컨스트레인트 노드(조인트의 자식으로 생긴다)를 어디서든 뺀다 — A00210 이 켠다, A00480 은 옛 동작(False) |
| `fbx_options(...)` | `with` 블록 안에서만 MEL `FBXExport*` 전역 옵션을 바꾸고 나갈 때 되돌린다. `include_children` · `input_connections` · `bake_complex_animation` · `in_ascii`. **`-q` 결과가 옵션마다 다르다** — IncludeChildren 은 int, BakeComplexAnimation 은 문자열 `'true'/'false'`(실측) → `_to_bool` 로 읽는다 |
| `export_selected(nodes, path, ...)` | 폴더를 만들고 nodes 를 선택해 export selected. 옵션은 위 셋 |
| `FILTER_TYPES` · `member_matches_type` · `filter_members` | A00480 Export 탭 드롭다운의 타입 필터(제외만 한다). 새 타입 = 두 곳에 한 줄 |
| `get_unique_filepath` · `short_name` · `is_type` · `is_joint` · `is_constraint` | 보조 |
| `import_options(quaternion, mode, fill_timeline)` (2026-10-27) | `with` 블록 안에서만 `FBXImportQuaternion` · `FBXImportMode` · `FBXImportFillTimeline` 을 바꾸고 `-q` 로 읽어 둔 값으로 되돌린다. [maya_fbx_exact](Framework_fbx_binary.md) 가 `euler` 모드로 임포트할 때 |

## 실측으로 정한 것 (mayapy 2024)

- `cmds.file(..., typ="FBX export", es=True)` 가 무엇을 담을지는 **`FBXExport*` 전역 옵션**이 정한다 — 노드를 옮기거나 숨기지 않아도 된다
  (메모리 [fbx-export-selected-scope](../.claude/memory/fbx-export-selected-scope.md)).
  - `FBXExportIncludeChildren false` → 선택한 노드만(선택 안 한 조상은 계층 유지용으로 따라 나오고 자손은 빠진다).
  - `FBXExportInputConnections false` → 컨스트레인트 드라이버 같은 입력 연결 노드가 FBX 루트에 섞이지 않는다.
  - `FBXExportBakeComplexAnimation false`(플러그인 기본값도 false) → 익스포터가 다시 샘플하지 않는다.
- FBX 의 **타임스팬(언리얼 "Exported Time")은 내보낼 때의 `playbackOptions min/max`** 다(ascii FBX `Takes/LocalTime`, 2026-10-26). 커브 키는 범위 밖도 전부 나간다.
- **레퍼런스 노드를 그대로 내보내면 노드 이름에 네임스페이스가 남는다**(`CHN:root`) — 임포트 + 네임스페이스 제거 뒤 내보내면 `root`. A00210 Export 가 기본으로 그렇게 한다.
- `.fbx` 가 아닌 이름(`x.fbx.part`)으로 내보내면 익스포터가 `.fbx` 를 덧붙인다 → 임시 이름도 `.fbx` 로(`<stem>__part.fbx`).

쓰는 곳: [A00480_FileTool](A00480_FileTool.md) Export · [A00210_FileManager](A00210_FileManager.md) §4-E Maya > Export.
