---
name: wip-a00310-searchtool-merge
description: "A00310_SearchTool IMPLEMENTED (Maya test + push pending) — merged legacy JUN_PY_SelectionTool_V02_01 + JUN_PY_SearchTool_V01_02 into one PySide tabbed tool"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8546124f-32a8-4de0-8ce6-b4460f257dcf
---

WIP (started 2026-06-26): 레거시 maya.cmds 툴 2개를 **A00310_SearchTool** 한 PySide 툴로 통합.
탭으로 구분. 소스(읽기전용 참고):
`C:\Users\USER\Documents\maya\2024\prefs\scripts\JUN_PY_SelectionTool_V02_01.py`,
`...\JUN_PY_SearchTool_V01_02.py`.

**소스 기능 요약**:
- SelectionTool: TSL 2개(Types / Objects). "Select Type" 버튼=선택(또는 Hierarchy)에서 각 obj 의
  shape 타입(shape 없으면 transform 타입) 모아 정렬 → Types TSL. "Select Objects"=선택/Hierarchy →
  Objects TSL. 옵션: radio Hierarchy/Selected, checkbox Invert. Select By Shape 프레임: Mesh/
  nurbsCurve/joint/constraint 버튼 = Objects TSL 중 그 타입인 것 선택(constraint 는 5종 set).
  "Select By Type" = Types TSL 에서 *선택된* 타입들에 매칭되는 Objects 선택. Invert 면 여집합.
  (constraint set = {aim,orient,point,scale,parent}Constraint)
- SearchTool: Objects TSL 1개 + "Search Token" 텍스트필드 + radio + Invert checkbox. "Select Objects"
  로 채우고, "Search By Token" = Objects 이름에 토큰 포함된 것 선택(Invert 면 여집합).

**설계 (arch B, A00170_driverTool 골격 복제)**:
```
JUN_All/tools/A00310_SearchTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(reload): MainWindow → ThemeManager coral_dark → show (A00170 복제, 문자열만 교체)
├── __dragDrop_A00310.py   # 셸프설치(A00170 복제); TOOL_LABEL="SearchTool"; run(True)
├── icon/A00310_SearchTool.svg + .png
└── app/{__init__,config/{__init__,version.py},core/{__init__,maya_scene.py,search_select.py},ui/{__init__,main_window.py}}
```
- 공용 위젯 `Framework.qt.JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01` 사용 — Select/Add/Del/Up/Down/**Sort**
  버튼 내장(사용자 요청: Sort 버튼 포함 = show_sort 기본 True 유지). get_all_items/set_items/
  selected_items/select_by_texts 제공. BUT "Select Objects"는 Hierarchy/Selected 옵션을 따라야 하므로
  위젯 기본 select 대신 **커스텀 'Get' 버튼**(add_button)으로 채운다(또는 show_select=False + 자체 버튼).
- core/maya_scene.py: selection(), expand_hierarchy(objs) (소스 BF_SELECTION_makeList_hierarchy 이식,
  reverse+dedup), node_type(obj) (shape 우선, 소스 V02 로직), exists().
- core/search_select.py (maya.cmds, UI 비의존):
  collect_from_selection(hierarchy:bool) -> objs;  collect_types(objs) -> sorted unique types;
  select_by_types(objs, types_set, invert) -> selected list;  select_by_token(objs, token, invert).
  CONSTRAINT_TYPES set 상수.
- ui/main_window.py: QTabWidget 2탭. 접두사 sel_* / sch_*. 공유 로그창 + Help>About + 저작권 푸터
  (A00170 main_window 패턴). 모든 UI 문자열 영어([[ui-text-english-only]]).
  - Selection 탭: 옵션행(radio Hierarchy/Selected, Invert checkbox) + Types TSL | Objects TSL(좌우),
    각 'Get' 버튼, Select By Shape 버튼들(Mesh/nurbsCurve/Joint/Constraint), "Select By Type" 버튼.
  - Search 탭: Search Token 필드 + 옵션행 + Objects TSL('Get') + "Search By Token" 버튼.
- undo: 선택만 바꾸므로 undo_chunk 불필요(선택은 undo 큐 영향 적음) — 단순 try/except + self._log.
- version.py VERSION="01.00", LAST_UPDATE 2026-06-26.

**마무리 작업**: 가이드 `JUN_All/docs/A00310_SearchTool.md` 작성, `JUN_All/docs/WORKLOG.md`
2026-06-26 항목, **아이콘 생성**(svg + png, A00310 번호). py_compile 검증. 끝나면 푸시 여부 질문
(기본 [[push-target-dnable-dev]]). 규약: [[prefer-pyside-for-new-tools]],
[[standalone-app-package-collision]](단 이건 in-Maya 라 tools.* 절대 import 사용),
[[push-includes-tool-guide-docs]], [[worklog-maintenance]].

**진행 상태**: 구현 완료. 전체 패키지 생성됨(__init__/launch/__dragDrop_A00310/app{config/version 01.00,
core{maya_scene,search_select,__init__},ui/main_window}), 아이콘 svg+png(리스트+돋보기) 생성,
가이드 docs/A00310_SearchTool.md + WORKLOG 항목 작성. 전 .py `py_compile` 통과.
TSL Sort 버튼 포함(show_sort 기본 유지). **남은 일**: Maya 실기 검증 + 푸시([[push-target-dnable-dev]]).
검증/푸시 끝나면 이 메모 삭제.
