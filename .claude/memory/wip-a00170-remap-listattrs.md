---
name: wip-a00170-remap-listattrs
description: "IMPLEMENTED (Maya test + push pending) — A00170_driverTool Remap Value tab List Attributes expanded to all attrs + search-to-discover (ported A00145 Connect tab behavior)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8546124f-32a8-4de0-8ce6-b4460f257dcf
---

WIP (started 2026-06-26): A00170_driverTool **Remap Value 탭**의 List Attributes/Attr Search 를
A00145_RigConnect **Connect 탭** 방식으로 개선.

**요구사항**: (1) List Attributes 가 보여주는 어트리뷰트를 늘린다(현재 keyable 만). (2) 검색으로
어트리뷰트를 발견하거나, 리스트업 안 된 어트리뷰트도 보이게 한다. A00145 Connect 탭 List Attributes 참고.

**A00145 참고 로직** (`app/core/connect_manager.py::list_attrs`, `on_search_attrs`):
- `list_attrs(obj, search="")`: search 없으면 `cmds.listAttr(obj)`(전체), 있으면
  `cmds.listAttr(obj + "." + search)`. 이름에 "." 든 중첩 항목 skip. multi/compound 는
  `mel.eval(getNextFreeMultiIndex(full,0))` 성공 시 `listAttr(obj.attr[idx], multi=True)` 로 자식 펼침.
- search 핸들러: 현재 목록에 substring 매칭 있으면 그것들을 선택. 없으면 `list_attrs(obj, token)` 로
  재질의해 목록 교체(리스트 안 됐던 attr 발견). try/except 로 listAttr 실패 방어.

**구현 계획 (A00170)**:
- `app/core/maya_scene.py`: `import maya.mel as mel` 추가. `MayaScene.list_attrs(obj, search="")`
  staticmethod 추가(위 A00145 로직 복제). 기존 `list_keyable_attrs` 는 사용처가 on_rmp_list_attributes
  하나뿐 → 제거(또는 유지). list_attrs 로 대체.
- `app/ui/main_window.py`:
  - `on_rmp_list_attributes`: `attrs = MayaScene.list_attrs(first)` 로 변경(전체 attr). 로그 문구 유지.
  - `on_rmp_search_attrs`: token 없으면 warn. all = rmp_attr_tsl.get_all_items();
    matches = [a for a in all if token in a]. matches 있으면 select_by_texts(matches) + 로그.
    없으면 joints[0] 로 `MayaScene.list_attrs(first, token)` 재질의(try/except), set_items, "re-listed" 로그.
    (joints 비었거나 first 미존재 시 warn)
  - 툴팁/주석 갱신(keyable→all). Attr Search placeholder 도 갱신 가능.
- version.py 01.04→01.05, LAST_UPDATE 2026-06-26. 헤더 날짜.
- docs `JUN_All/docs/A00170_driverTool.md` §4.1(3번 항목 List Attributes/Attr Search) 갱신 + WORKLOG 항목.
- 검증 py_compile (Maya 실기 대기).

**진행 상태**: 구현 완료. maya_scene.list_attrs 추가(list_keyable_attrs 제거), 핸들러 2개 수정,
Attr Search 툴팁 보강, version 01.05, docs §4.1 + WORKLOG 갱신. py_compile 통과.
**남은 일**: Maya 실기 검증 + 푸시([[push-target-dnable-dev]]). 끝나면 이 메모 삭제.
규약 [[ui-text-english-only]], [[maya-2023-compat]], [[push-includes-tool-guide-docs]], [[worklog-maintenance]].
참고: A00170 에는 직전 작업 AttachCrv 탭(v01.04)이 이미 커밋/푸시됨(f343286).
