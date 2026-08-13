---
name: wip-a00400-curvetool
description: A00400_CurveTool new in-Maya PySide tool — mesh edges to attached curves (one per edge group) + Reverse Direction by axis
metadata: 
  node_type: memory
  type: project
  originSessionId: 74425151-47a7-46c3-a187-1bb4adf16118
  modified: 2026-07-29T00:49:06.633Z
---

A00400_CurveTool — 신규 in-Maya PySide 툴 (v01.00, 코어 mayapy-verified, Maya UI 실기 테스트 대기). A00360_SortTool 구조/축비교 방식 클론.

**기능 1 — Create Curves from Mesh Edges**: 선택한 폴리곤 엣지를 **연결 성분(붙어있는 덩어리)별로 그룹**지어 그룹마다 커브 1개 생성. ref/ref_01.mel(`duplicateCurve`+`attachCurve`로 선택 전체를 커브 1개로만 묶음)의 한계를 해결 — `['e[156:158]','e[196:199]','e[236:239]']` → 커브 3개. 엔진은 ref의 duplicateCurve+attachCurve 대신 **그룹별 `polyToCurve(form=2, degree, ch=1)`** 사용(폴리라인 결과 동일하고 cv 순서를 스스로 정렬해줘 견고 + cv[0]/cv[n] 끝점 명확). degree 1(직선, 기본)/3(스무스) 옵션, Name Prefix. `ch=1`이라 커브가 메시에 부착(따라감).

**기능 2 — Reverse Direction**: TSL(MOD_tsl_qt_v01)에 리스트업된 커브들의 cv[0]/cv[n] 월드 위치를 지정 축(X/Y/Z, 기본 Y)으로 비교, cv[0]을 Max end(기본, 예=위) 또는 Min end에 오도록 `reverseCurve(ch=1, rpo=1)`로 뒤집음. 이미 정렬됐거나 두 끝 축값 동일(판단불가)/커브 아님은 skip. UI는 `tsl.get_all_nodes()`(UUID-safe)로 대상 취득.

핵심 검증 사실: `polyToCurve`는 여러 그룹 선택해도 커브 1개만 만듦 → 그룹핑 필수(BFS로 정점 공유 엣지 묶음, `group_edges`). `reverseCurve`가 cv 순서 실제로 뒤집음(cv0 Y 0→3). 서로 다른 메시 엣지는 정점 공유 안 해 자동으로 다른 그룹.

파일: tools/A00400_CurveTool/{launch.py, __dragDrop_A00400.py, app/core/curve_manager.py, app/ui/main_window.py, app/config/version.py}. 아이콘: icon/A00400_CurveTool.svg(코랄 S-커브+CV사각형+방향화살표, house style) → dev/build_icons.py(mayapy PySide2 QtSvg)로 32x32 png 생성 완료. 관련: [[wip-a00360-sorttool]], [[framework-timerange-widget]], [[prefer-pyside-for-new-tools]]

**Line Width 탭** (v01.01, 2026-08-13): 탭 2개로 나누고(`Create / Direction` = 기존 그대로,
`Line Width` = 신규) 리스트업한 커브의 `nurbsCurve.lineWidth` 를 슬라이더로 조절한다.
목적은 **씬에서 커브가 잘 보이고 잘 집히는 것**(표시 전용, 형상 무관).

- `lineWidth` 실측: float, 기본 **-1 = 마야 전역 설정을 따름**, min/max 없음, **Maya 2019+**,
  mesh/locator 에는 없다.
- 슬라이더 라이브 반영 + **드래그 한 번 = undo 한 스텝** — `sliderPressed` 에서
  `cmds.undoInfo(openChunk=True)`, `sliderReleased` 에서 close(값 변경마다 청크를 열면 undo 도배).
