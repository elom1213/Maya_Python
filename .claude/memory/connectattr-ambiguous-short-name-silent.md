---
name: connectattr-ambiguous-short-name-silent
description: "cmds.connectAttr 에 짧은 이름이 겹치는 DAG 노드(grp1|A:dup, grp2|A:dup)를 'A:dup' 로 주면 에러 없이 첫 노드에 붙는다 - 네임스페이스는 몇 중이든 문제없음"
metadata:
  type: project
---

**실측 (Maya 2024 mayapy, 2026-10-22)**: `cmds.connectAttr("A:dup.Jaw", ...)` 에서 `A:dup` 이 `|grp1|A:dup` · `|grp2|A:dup`
둘에 해당하면 **"More than one object matches" 에러가 나지 않고 조용히 첫 번째(`grp1|A:dup`)에 연결**된다.
(`cmds.ls("A:dup")` 는 둘 다 돌려주고 `getAttr`/`setAttr` 는 애매하다고 에러를 내는 것과 다르다.)

네임스페이스 자체는 문제가 아니다 — `A:src` · `A:B:src` · `A:B:C:src` · 레퍼런스 `REF:A:B:src`(소스 · 데스티네이션 양쪽) 전부
`"{node}.{attr}"` 문자열로 그대로 연결된다(A00145 `connect_by_rule` 7항목 실측).

**Why:** 이름 문자열로 연결하는 툴(A00145 Connect by Rule 등)에서 리스트의 이름이 짧은 이름이고 씬에 같은 잎 이름이 둘이면
**잘못된 노드에 붙고도 성공으로 센다.**

**How to apply:** 오브젝트 목록은 `cmds.ls(sl=True)` 가 주는 **최단 유일 이름**(`grp2|A:dup`)을 그대로 보관한다 — TSL 이 그렇게 한다.
목록을 담은 뒤 리네임 · 복제로 이름이 겹치면 텍스트가 애매해질 수 있으니, 이름 문자열 대신 `tsl.get_all_nodes()`(UUID 해석)를
쓰거나 연결 전에 `cmds.ls(name)` 가 1개인지 검사해 애매하면 스킵 + 로그가 안전하다([[wip-tsl-uuid-selection]], [[uuid-safe-rename-duplicate-names]]).
A00145 Connect by Rule 은 v01.64 에서 `resolve_node` 로 이렇게 막았다. 관련: [[wip-a00145-connect-rules]]
