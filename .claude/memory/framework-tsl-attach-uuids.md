---
name: framework-tsl-attach-uuids
description: 공용 TSL 위젯의 attach_uuids 옵션 — 항목이 씬 노드가 아닌 것이 확실한 리스트(어트리뷰트 별칭·파일명 등)는 꺼서 항목마다 나가는 cmds.ls 를 없앤다
metadata:
  type: reference
---

`Framework/qt/MOD_tsl_qt_v01.py` 의 `JUN_mod_tsl_qt_v01(attach_uuids=True)` (2026-09-07 추가).
항목이 **씬 노드가 아닌 것이 확실한** 리스트는 `attach_uuids=False` 로 만든다.

```python
JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
    title="Targets (top = first)",
    show_select=False, show_add=False, show_del=False,   # 씬 선택으로 담을 것이 없다
    show_up=True, show_down=True, show_sort=True, show_reverse=True,
    show_order=False, attach_uuids=False)
```

**Why:** UUID 부착은 항목마다 `cmds.ls(name, uuid=True)` 를 부른다. MetaHuman blendShape
타겟처럼 수백 개면 그대로 비용이고([[framework-tsl-list-limit]] 이 요약 모드를 두는 이유가
바로 이것), 노드가 아닌 항목에는 **어차피 아무것도 붙지 않는다.** 게다가 이름이 우연히 씬
노드와 겹치면(타겟 별칭은 보통 타겟 메시 이름 그대로다) 항목을 눌렀을 때 엉뚱한 노드가
선택된다.

**How to apply:** 어트리뷰트 별칭 · 파일명 · 노드 타입 이름처럼 노드가 아닌 목록을 담는
TSL 은 끄고, 씬 오브젝트를 담는 TSL 은 기본값(켬)을 그대로 둔다 — 리네임/리페어런트
안전성이 거기서 온다. 첫 사용처는 [[wip-a00290-target-order-tab]].
