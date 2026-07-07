---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-07-08
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-07-08 (오늘)

> [!summary] `A00060_jointTool_V02` v01.02→01.03 — Curve/Divide 조인트를 월드 절대 좌표로 생성(계층 아래 오브젝트 위치 오차 수정)
- **요청**: Curve/Divide 탭의 **Match to Obj / Make Joint Divided** 로 조인트를 만들면, 오브젝트가 어떤 계층
  아래에 있을 때 **원하는 위치에 안 생긴다**. 월드 기준 절대값으로 받아 어떤 계층이든 정확히 생성하도록 수정.
- **원인/수정(모두 `app/core`)**: ① `divide_manager.curves_from_pairs` — `xform` 이 **object-space** translation
  이라 커브/분할 joint 가 로컬 좌표에 생성 → `ws=True` 추가. ② `curve_joint_manager._joint_at_curve_point` —
  `pointPosition`(이미 월드)에 커브 world translation 을 **한 번 더 가산**(이중 가산) → 커브가 원점 아니면 2배
  오차 → 가산 제거 + `xform(ws)` 확정. ③ `obj_joint_manager._joint_at_obj`(Match to Obj) — `joint -p` 가 부모
  체인 아래로 들어갈 때 대비해 생성 직후 `xform(jnt, ws=True, translation=pos)` 로 월드 위치 확정.
- `aim_manager` 는 원래부터 `ws=True` 라 변경 없음. 원점/무계층 케이스는 동작 불변(하위 호환).
- **검증**: **Maya 실기 확인 완료.** version 01.03 + 신규 가이드 문서 `JUN_All/docs/A00060_jointTool_V02.md`(§6) 갱신.
  #jointTool #worldSpace #xform #pointPosition #rigging

---

## 2026-07-07

> [!summary] `A00300_meshDoctor` v01.01→01.02 — 여러 메시 배치 진단 + 메시별 요약 테이블(클릭 시 상세)
- **요청**: 여러 메시를 TSL 에 리스트업하고 한 번에 진단해, 모든 메시의 결과를 **간단하게** 보고 싶다. UI 방식 제안 요청.
- **결정(옵션 '요약 테이블 + 클릭 상세' 선택)**: 창 상단에 **Target Meshes** TSL(Add Selected/Remove/Clear, **UUID 보관**
  → 중복 이름/리페어런트 안전) 추가. **Diagnose Listed**(기존 Diagnose Selected 대체)가 리스트 전체를 진단하고,
  **리스트가 비면 현재 선택**으로 폴백. 결과는 **Summary 테이블**(`Mesh|Status|Issues`, Status 색상 구분, Issues 는
  WARN/FAIL 을 `이름(개수)` 요약)로 보여주고, **행 클릭 → 그 메시의 기존 전체 상세 리포트를 아래 로그뷰에 출력**.
- **구현**: core `mesh_scan.py` 에 `scan_nodes(nodes)`/`_resolve_meshes()` 추가(`scan_selection` 은 이를 재사용).
  `main_window.py` 에 TSL 그룹·Summary 테이블·핸들러(`on_add_selected`/`_listed_nodes`/`_fill_summary`/`_on_summary_row` 등).
  JSON/TXT 리포트는 배치 전체 저장 유지.
- **검증**: **Maya 실기 확인 완료.** version 01.02 + 신규 문서 반영 `JUN_All/docs/A00300_meshDoctor.md`(§여러 메시 한 번에 진단).
  #meshDoctor #배치진단 #SummaryTable #UUID #weightTransfer

> [!summary] `A00210_FileManager` v01.27→01.28 — Path Structure: Recreate 목적지("Recreate To") 칸 + Rename 버튼
- **요청**: Path Structure 탭에서 (1) 저장된 구조 이름을 바꾸는 **Rename** 버튼, (2) Recreate 가 File Manager 탭의
  `Scan Dir` 인지 이 탭의 `Base Folder` 인지 헷갈려서 **재생성 목적지를 따로 지정**하는 UI. UI 방식은 제안 요청.
- **원인/혼동**: 기존 Recreate 는 `<File Manager 탭 Project Root>/<base_rel>` 에 생성 — 어느 경로인지 화면에 안 보였다.
- **구현(옵션1 '베이스 폴더 직접 지정' 선택)**: Saved Structures 그룹에 **`Recreate To` 칸(+Browse)** 추가 —
  체크된 폴더가 이 폴더 **바로 안**에 생성된다. 구조 선택 시 `<Project Root>/<base_rel>`(기존과 같은 경로)로
  **자동 채움**, 다른 곳으로 자유롭게 변경 가능(생성 경로가 항상 노출). 목적지가 없으면 생성 확인. `Rename` 은
  QInputDialog(파일명+내부 name 동기화, 충돌 거부). **Recreate 버튼은 녹색 액센트 + 우측 정렬**로 Refresh/Rename/
  Delete(관리)와 구분(실제로 폴더를 생성하는 동작). core: `path_structure.rename()` 신규, `recreate(..., base_abs=)` 추가.
- **검증**: **실기 확인 완료.** version 01.28 + 문서 `JUN_All/docs/A00210_FileManager.md`(§4-C) 갱신.
  #FileManager #PathStructure #Recreate #Rename #UX

> [!summary] `A00110_animTool` v01.29→01.30 — Graph Focus 자동 확대를 오브젝트 선택에만 엄격히 한정
- **요청**: Graph Focus 의 Auto-Focus 자동 확대가 **컨트롤러를 선택했을 때만** 동작하게. 지금은 애니 작업 중
  컨트롤+`z`(undo)를 눌러도, 그래프 에디터의 키프레임을 하나 선택했다 풀어도 자동 확대가 걸린다.
- **원인**: 마야 `SelectionChanged` 는 씬 오브젝트 선택뿐 아니라 **키 선택/해제·undo** 로도 발생. v01.27 의
  "선택된 키가 있으면 건너뛰기"는 키를 **해제한** 순간(선택 키 0개)을 막지 못했다.
- **구현(`app/core/graph_focus_manager.py` 만 변경)**: 직전에 프레이밍한 **오브젝트 선택 목록**을 캐시
  (`_last_selection`)해두고, `_apply_silent` 에서 `cmds.ls(sl=True, long=True)` 가 실제로 **달라졌을 때만**
  프레이밍(선택이 비면 무시, 기존 키-선택 방어도 유지). `apply_now`(토글 ON/값 변경/Focus Now)도 캐시를 현재
  선택으로 맞춰 재트리거 방지. 키 선택/해제·undo 는 오브젝트 선택이 그대로라 무시된다.
- **검증**: **Maya 실기 확인 완료.** version 01.30 + 문서 `JUN_All/docs/A00110_animTool.md`(§1 changelog, §5.7) 갱신.
  #animTool #GraphFocus #SelectionChanged #AutoFocus

---

## 2026-07-06

> [!summary] `A00145_RigConnect` v01.10→01.12 — Constrain 탭에 Group Create 접이식 추가(오프셋 그룹 _con_NN 삽입, UUID 기반)
- **요청**: Constraint 탭에 접이식 UI 하나 추가. 리스트업된 각 오브젝트에 **위치·회전이 같은 그룹**을 만들어 **오브젝트의 부모와
  오브젝트 사이 계층**에 삽입(그룹명 `<obj>_con_01`, 몇 개 만들지 사용자 지정).
- **구현(v01.11, 새 매니저 `app/core/group_create_manager.py`)**: `create_groups(objects, count)` — 오브젝트당 `Count` 개의
  중첩 오프셋 그룹을 삽입. 각 그룹은 `matchTransform`(position/rotation, **scale 제외**)로 오브젝트 월드에 맞추고, 원래 부모 아래로
  재부모(월드 보존) 후 대상을 그 그룹 아래로. `_con_01` 이 오브젝트 바로 위, 번호가 커질수록 바깥. 오브젝트 월드/기존 계층 유지.
  `CollapsibleBox("Group Create", 기본 접힘)` + 전용 TSL + Count 스핀박스(1~50) + `Create Groups` 버튼(`_build_group_create_box`/`on_group_create`).
- **UUID 기반(v01.12)**: 중복 이름·재부모로 DAG 경로가 바뀌어도 안전하도록, 대상/부모/생성 그룹을 **UUID 로 잡아두고 매번 UUID→현재 경로로
  해석**(`_to_uuid`/`_path`, A00330_NamingTool 패턴). 중복 이름이면 경고 후 첫 매치 사용, 없거나 실패한 항목은 건너뛰고 로그.
- **검증**: `py_compile` 통과. **Maya 실기 검증 대기.** version 01.12 + 문서 `JUN_All/docs/A00145_RigConnect.md`(Constrain > Group Create) 갱신.
  #RigConnect #GroupCreate #offsetGroup #UUID #matchTransform

> [!summary] `A00220_BackupTool` v01.12→01.13 — Always on Top(Pin) 토글 버튼 추가 (A00110 패턴 이식)
- **요청**: `A00110_animTool` 처럼 Pin 기능을 붙여, 필요할 때 이 창을 다른 창들 위에 고정.
- **구현(`app/ui/main_window.py`)**: 창 **우상단 헤더 행**에 체크형 `Pin` 버튼(좌측 stretch + 고정 크기 72×28) 배치.
  `toggle_always_on_top(enabled)` 이 `Qt.WindowStaysOnTopHint` 를 켜고/끄고 라벨을 `Pinned`/`Pin` 으로 바꾼 뒤
  `show()` 재호출(플래그 변경 시 창이 숨는 Qt 특성 회피). A00220 은 standalone Qt 창이라 A00110 과 동일하게 동작.
  기본 OFF(정상 Z-order, opt-in), prefs 미저장(A00110 과 동일).
- **검증**: `py_compile` 통과 + **실기 확인 완료**. version 01.13 + CHANGELOG + 문서 `JUN_All/docs/A00220_BackupTool.md`(§3) 갱신.
  #BackupTool #Pin #AlwaysOnTop #WindowStaysOnTopHint

> [!summary] `A00340_SelectionTool` v01.03→01.04 — 창을 상하 스플리터로 분리 + 컨트롤 4칸(Profile/Create/Color/Log)을 하나로 접었다 펴기 (Maya 실기 검증 완료)
- **요청**: 컨트롤 칸(Profile/Create/Color/Log)과 생성한 버튼 모음을 분리하고, 컨트롤을 접었다 펼 수 있게. (제안 4가지 중
  '상하 분할 + 접기' 채택 → 이후 '각 칸 개별'이 아니라 '네 칸을 한 번에' 접도록 재조정)
- **구현(`app/ui/selection_tab.py`)**: 창을 `QSplitter(Qt.Vertical)` 로 [컨트롤 pane] / [버튼 pane] 분리(핸들 드래그로 비율 조절).
  컨트롤은 Profile/Create/Color/Log 그룹박스 4개를 **하나의 접이식 `Controls` 박스**(신설 `CollapsibleBox` 위젯,
  QToolButton 헤더 ▾/▸)로 묶어 **한 번에** 접었다 편다. 접으면 `_on_controls_toggled` 가 스플리터 위 pane 을 헤더 높이로
  줄여(230→70) 버튼 영역을 넓히고(378→538), 펴면 원위치. 로그창은 이 박스 안으로 이동(기존 하단 Log 그룹 제거,
  `main_window` 가 `log_view` 를 탭에 전달).
- **검증**: `py_compile` + 오프스크린 PySide6 스모크(접이식 박스 1개+그룹 4개, 접기 시 전 그룹 숨김·pane 축소/확대, 펴기
  복원, 색칠 기능 회귀 없음) 통과 + 렌더 PNG 육안 확인, **Maya 실기 검증 완료**. version 01.04 + CHANGELOG + About +
  문서 `JUN_All/docs/A00340_SelectionTool.md` 갱신.
  #SelectionTool #레이아웃 #QSplitter #CollapsibleBox #접기

> [!summary] `A00110_animTool` v01.27→01.29 — Graph Focus 세로축 Fit value 를 값 범위에 꽉 맞추고, 위/아래 여백(%)을 UI 로 조절
- **v01.28 — 여백 없이 꽉 채우기**: Fit value 세로 값 범위에 주던 위아래 10% 여백을 없애, 구간 내 **최댓값이 뷰 맨 위·
  최솟값이 맨 아래에 닿도록**(`animView` minValue/maxValue = vmin/vmax) 값을 최대한 크게 보이게 함(값이 줄어 잘 안 보이던 문제).
  평평한 구간(min==max)만 예외로 최소 여백 유지.
- **v01.29 — 여백을 UI 로 조절**: 가장자리에 딱 붙는 게 부담스러워 살짝 여백을 두고 싶다는 요청에 따라 **`Value margin (%)`
  스핀박스**(기본 10%, 0~100, 5~10% 권장) 추가. 세로 값 범위에 이 %만큼 위/아래 여백을 두고 프레이밍한다.
  `frame_around_current(..., value_pad_pct)` 로 전달, Auto-Focus·Focus Now 공통, 값 변경 시 즉시 재적용.
- **파일**: `app/core/graph_view_manager.py` · `graph_focus_manager.py`(pad_getter 배선) · `app/ui/main_window.py`(스핀박스+핸들러),
  version 01.29, 문서 `JUN_All/docs/A00110_animTool.md`(§5.7 + 이력) 갱신. `py_compile` 통과, **Maya 실기 검증 완료**.
  #animTool #GraphEditor #FitValue #ValueMargin #animView

> [!summary] `A00340_SelectionTool` v01.02→01.03 — 선택 버튼 색을 카테고리 넘나들며 다중 선택해 일괄 적용(Color Select 모드) + 체크 누락 버그 수정 (Maya 실기 검증 완료)
- **요청 변경**: v01.02 의 "카테고리 단위 일괄 색 변경"을, **카테고리를 넘나들며 임의의 버튼을 골라 칠하는** 방식으로 교체.
- **구현(`app/ui/selection_tab.py`)**: `Color` 바에 **`Color Select`** 토글 추가. 켜면 모든 버튼이 체크형이 되어 클릭이 '선택'
  대신 '체크'로 바뀐다. 카테고리와 무관하게 원하는 버튼을 체크한 뒤 **`Apply Color...`** 로 고른 한 색을 일괄 적용,
  **`Clear Color`** 로 해제. 체크된 버튼은 강조 테두리로 표시되고 재렌더/색적용 후에도 체크 유지, 모드 OFF 시 초기화.
  v01.02 의 카테고리 우클릭 `Set/Reset Buttons Colors` 는 제거(개별 버튼 우클릭 `Set Color...`/`Reset Color` 는 유지).
- **버그 수정**: "버튼 2개를 체크했는데 `Apply Color` 를 누르면 *Check one or more buttons first* 팝업"이 뜨던 문제.
  원인은 체크 상태를 `clicked` 시그널로만 내부 집합(`self._checked`)에 쌓는 구조 — 시그널 인자 신뢰도가 환경(Maya
  PySide2)에 따라 갈려 집합이 비어 있었다. **수정**: ① `clicked`→`toggled` 시그널(새 상태를 확실히 전달),
  ② Apply/Clear 시 렌더된 버튼 위젯의 실제 `isChecked()` 를 다시 읽어(`_sync_checked_from_widgets`) 집합을 맞춤 —
  **화면 버튼 상태를 진실의 원천**으로. 시그널이 누락돼도 빈 집합이 되지 않는다.
- **검증**: `py_compile` + 오프스크린 PySide6 스모크(실제 `btn.click()`·시그널 누락 복구·재렌더 체크 유지) 통과,
  **Maya 실기 검증 완료**. version 01.03 + CHANGELOG + About + 문서 `JUN_All/docs/A00340_SelectionTool.md` 갱신.
  #SelectionTool #버튼색 #ColorSelect #다중선택 #toggled #버그수정

> [!summary] `A00110_animTool` v01.25→01.27 — Graph Focus 세로축 Fit value 보정 + 키 선택 후 `f`(Frame Selection) 존중 (Maya 실기 검증 완료)
- **v01.26 — Fit value 세로축이 항상 맞도록**: 세로 값 범위를 **구간 안 키 값**만으로 구해, 현재 프레임 ±margin
  구간에 키가 없으면(멀리 떨어진 두 키 사이) 세로축을 못 맞추던 문제. 이제 애니메이션 커브 `.output` 을 **구간에 걸쳐
  시간별로 평가**(탄젠트 오버슛 포함)해 min/max 를 구하고 구간 내 키 값도 함께 반영 → 키 유무와 무관하게 세로축이 맞는다.
  커브가 많으면 커브당 샘플 수를 줄여 총 평가 횟수 상한(4000) 유지. `app/core/graph_view_manager.py`.
- **v01.27 — 키 선택 후 `f` 를 존중**: Auto-Focus 켠 상태에서 특정 키를 선택해 `f` 로 그 범위만 보려 하면, 키 선택으로
  발생한 `SelectionChanged` 의 지연 콜백이 뒤늦게 현재 프레임으로 덮어써 원하는 프레임(예: 300f)이 아니라 현재
  프레임(400f)으로 튀던 문제. 자동 프레이밍 콜백이 **선택된 키가 있으면 건너뛰도록**(`cmds.keyframe(q, selected, name)`)
  수정. `Focus Now`·토글 ON 같은 명시적 조작은 영향 없음. `app/core/graph_focus_manager.py`.
- **검증**: `py_compile` 통과 + **Maya 실기 검증 완료**(선택 포커싱·Fit value·`f` 존중 모두 의도대로).
  #animTool #GraphEditor #FitValue #FrameSelection #scriptJob

> [!summary] `A00110_animTool` v01.24→01.25 — Graph Focus 탭 신설(선택 시 그래프 에디터를 현재 프레임 ±margin 으로 프레이밍)
- **요청**: 컨트롤러를 선택하면 전체 키 구간(예: 0~6000f)이 다 보이는 대신, 현재 프레임 기준 앞/뒤 80프레임 정도만
  그래프 에디터에 확대해서 보고 싶다(예: 현재 500f → 420~580f). On/Off 토글 + margin 값(80)을 UI 로 지정.
- **구현**: 7번째 탭 **Graph Focus**. `Auto-Focus on Selection` 체크형 토글 버튼이 켜지면 `SelectionChanged` scriptJob 으로
  선택 변경을 감시하다가, 마야 자체 Auto-Frame 뒤(`evalDeferred(lowestPriority=True)`)에 `animView` 로
  `[현재-margin, 현재+margin]` 을 덮어쓴다. `Frame margin (±)` 스핀박스(기본 80, 사용자 지정), `Fit value` 체크로
  세로(값) 축도 구간 내 키 값 범위에 맞춤(기본 ON), `Focus Now` 로 토글과 무관하게 1회 프레이밍. `closeEvent` 에서 scriptJob 정리.
- **파일**: 새 매니저 `app/core/graph_view_manager.py`(프레이밍 로직) + `graph_focus_manager.py`(scriptJob 라이프사이클),
  `app/core/__init__.py` · `app/ui/main_window.py` 배선, version 01.25, 문서 `JUN_All/docs/A00110_animTool.md`(§5.7) 갱신.
- **검증**: `py_compile` 통과. **Maya 실기 검증 대기.**
  #animTool #GraphEditor #animView #scriptJob #SelectionChanged

> [!summary] `A00340_SelectionTool` v01.01→01.02 — 선택 버튼에 커스텀 색 지정(팔레트+스포이드) + 카테고리 일괄 색 변경
- **요청**: 만든 선택 버튼마다 색을 바꾸고 싶다. A00210 lineage 탭의 `Set Color...`처럼 팔레트를 띄우고, 스포이드로
  다른 색을 집어 적용. 가능하면 여러 버튼 색을 한 번에.
- **구현(`app/ui/selection_tab.py`)**: 버튼 dict 에 선택적 `"color"`(hex) 추가. 색이 있으면 `_button_stylesheet()` 로
  배경/테두리/hover/pressed 스타일 적용, 라벨 글자색은 배경 밝기(`_contrast_text_hex`, 휘도>140→검정)로 자동 결정.
  팔레트+스포이드는 A00210 과 동일하게 `QColorDialog.getColor()` 그대로 사용(내장 **Pick Screen Color** = 스포이드).
- **개별**: 버튼 우클릭 → `Set Color...` / `Reset Color`. **일괄**: 카테고리 우클릭 → `Set Buttons Color...`(그 카테고리
  전체 버튼에 한 색 적용) / `Reset Buttons Colors`. 색은 프로파일 JSON 에 버튼별로 저장돼 세션 유지.
- **검증**: `py_compile` 통과. **Maya 실기 검증 대기.** version 01.02 + CHANGELOG + About + 문서
  `JUN_All/docs/A00340_SelectionTool.md` 갱신.
  #SelectionTool #버튼색 #QColorDialog #스포이드 #일괄변경

---

## 2026-07-03

> [!summary] `A00040_file_exporter_V02` v02.04→02.05 — 메시 제외 실패 재진단(레퍼런스 아님) + shape intermediate 를 1순위로
- **재진단**: 제외 메시가 FBX 에 남던 진짜 원인은 "레퍼런스"가 아니라 **메시 transform 이 잠김/연결/컨스트레인**(리그드
  캐릭터에 흔함)이라 `parent -world` 가 실패한 것. 동일 이름 레퍼런스 그룹이 있는 건 무관. v02.02~04 의 "referenced" 라벨이 오분류였음.
- **수정(`app/core/export_ops.py`)**: shape 기반 제외 타입(mesh 등)은 이제 **shape 의 `intermediateObject` 를 켜는 방식을
  1순위**로 사용 — reparent 를 안 쓰므로 잠금/연결/레퍼런스/네임스페이스와 무관하게 항상 제외됨. shape 없는 타입(joint)만
  unparent. `_safe_parent_to_world` 예외 범위 확대(잠김/연결 포함), WARN 문구에서 "referenced" 제거.
- **한계**: 하위 메시는 shape 만 숨기므로 **빈 transform(null)** 이 FBX 에 남을 수 있음(지오는 빠짐).
- **검증**: `py_compile` + parent 실패 시뮬 단독 테스트(메시가 intermediate 로 제외·원복) 통과. **Maya 실기 재검증 대기.**
  문서 §6.1 + CHANGELOG/version v02.05.
  #FileExporter #메시제외 #intermediateObject #locked #connected #재진단

> [!summary] `A00040_file_exporter_V02` v02.03→02.04 — 레퍼런스 메시가 제외 세팅에도 FBX 에 남던 문제 수정
- **버그**: 이름 같은 레퍼런스가 있는 씬에서 메시 제외로 추출 시, 그룹 하위의 **레퍼런스 메시들**이 그대로 남음
  (`[WARN] could not exclude 51 referenced object(s), still in FBX`).
- **원인**: 레퍼런스 노드는 계층 밖으로 unparent 가 금지되어(v02.02 안전장치가 "제외 불가"로 처리) FBX 에 남음.
- **수정(`app/core/export_ops.py`)**: 제외 노드를 ① 통째로 월드로 빼내기 시도 → ② 실패(레퍼런스)하면 그 타입 **shape 의
  `intermediateObject` 를 켜서** FBX 에서 제외(export 후 원복). FBX 는 intermediate shape 를 안 내보내므로 reparent
  없이 레퍼런스 메시 제외 가능. 헬퍼 `_excluded_shapes_of`/`_set_intermediate` 추가. shape 없는 타입(레퍼런스 joint 등)만
  `could not exclude` 경고로 남음.
- **검증**: `py_compile` + 헬퍼 단독 테스트(shape 선별·setAttr intermediate) 통과. **Maya 실기 재검증 대기.**
  문서 §6.1 + CHANGELOG/version v02.04.
  #FileExporter #레퍼런스 #메시제외 #intermediateObject #FBX #버그수정

> [!summary] `A00040_file_exporter_V02` v02.02→02.03 — 씬 최상위로 빼기 / 계층 유지 선택 체크박스 추가
- **요청**: 세트 오브젝트를 씬 최상위로 빼서 뽑을지, 현재 계층을 유지해 뽑을지 고르는 체크박스. 기본은 최상위로 빼기.
  (`grp>joint_01` 에서 joint_01 이 세트면 → `joint_01` 또는 `grp>joint_01` 로 선택 추출)
- **구현**: Export 섹션에 **Move to scene root** 체크박스(기본 ON). core `export_sets/_export_fbx` 에 `keep_hierarchy`
  인자 추가 — 체크 ON 이면 기존처럼 멤버를 월드로 빼냈다 복원, OFF 면 멤버 이동을 건너뛰고 제자리에서 export.
- **원리**: FBX *export selected* 는 조상(부모) 체인은 포함하되 형제 가지는 제외하므로, 빼내지 않으면 부모 계층만 보존됨.
  타입 필터(그룹 하위 mesh/joint 제외)는 두 모드 모두 그대로 동작.
- **검증**: `py_compile` + 오프스크린 UI 스모크(체크박스 기본값·토글) 통과. **Maya 실기 검증 대기.**
  문서 §5·§7 + CHANGELOG/version v02.03.
  #FileExporter #계층유지 #씬최상위 #FBX #옵션

> [!summary] `A00040_file_exporter_V02` v02.01→02.02 — 레퍼런스 오브젝트(동일 이름 네임스페이스) 추출 시 크래시 수정
- **버그**: 레퍼런스로 같은 이름 오브젝트가 생긴 씬(`Test` + `namespace:Test`)에서 `Test` 를 세트에 넣어 추출하면
  `RuntimeError: Referenced objects parented to referenced objects may not be reparented` 로 크래시.
- **원인**: 깔끔한 계층을 위해 멤버를 월드로 빼내는(`cmds.parent(world=True)`) 단계를 Maya 가 **레퍼런스-밑-레퍼런스**
  노드에는 금지한다.
- **수정(`app/core/export_ops.py`)**: `_safe_parent_to_world` 헬퍼로 빼내기를 try/except 감싸고, 실패한 노드는
  **제자리에서 내보내고 복원도 생략**(성공한 것만 moved 로 추적해 복원). 제외 대상이 레퍼런스라 못 빼면
  `[WARN] could not exclude ... still in FBX` 로그. UUID 식별은 그대로라 동일 이름도 안전.
- **검증**: `py_compile` + 오프스크린 UI 스모크 통과. **Maya 실기 재검증 대기.** 문서 §7 + CHANGELOG/version v02.02.
  #FileExporter #레퍼런스 #네임스페이스 #reparent #버그수정

> [!summary] `A00040_file_exporter_V02` v02.00→02.01 — 타입 필터가 그룹 하위 노드에도 적용되도록 수정
- **버그**: Mesh 체크 해제 시 세트에 **직접 든** 메시는 제외되지만, 세트에 든 **그룹 하위**의 메시는 그대로 추출됨.
- **원인**: 타입 판별이 노드 자신·직속 shape 만 검사 → 그룹(transform, shape 없음)은 mesh 로 안 걸려 통째로 유지되고,
  FBX export 가 그룹을 선택하면 하위 메시까지 자동 포함.
- **수정(`app/core/export_ops.py`)**: `_collect_excluded_in_hierarchy` 추가 — 각 멤버 **계층 전체**를 훑어 제외 타입의
  '최상위' 노드를 찾고, export 직전 월드로 빼냈다가 후 원부모 복원(UUID 기반). 그룹은 유지, 하위 제외 타입만 FBX 에서 빠짐.
  로그의 excluded 목록에 그룹 하위 제외 노드도 합산.
- **검증**: `py_compile` + top-most 수집 로직 단독 테스트 통과. **Maya 실기 재검증 대기.** 문서 §6.1/§7 + CHANGELOG/version v02.01.
  #FileExporter #타입필터 #그룹계층 #FBX #버그수정

> [!summary] `A00040_file_exporter_V02` 신규 — 레거시 파일 익스포터를 PySide 로 재작업 + 타입 필터 추가
- **요청**: A00040_file_exporter 를 PySide 로 재작업해 `A00040_file_exporter_V02` 에 생성(아이콘 재사용).
  내보낼 때 **드롭다운 체크로 노드 타입 포함/제외**를 고르고 싶다(지금은 mesh·joint, 나머지는 항상 포함, 확장 가능).
- **구조**: 아키텍처 (B) 관례대로 `app/core/export_ops.py`(로직) · `app/ui/main_window.py`(화면) 분리,
  A00330 을 템플릿으로. 고유 드롭 파일 `__dragDrop_A00040_V02.py`(셸프 라벨 "FileExporterV2"), 테마 blue_dark.
- **포팅**: Export path · Set's Name/File name TSL · 토큰 네이밍(Custom / Set's Name) · 세트별 FBX
  내보내기(월드로 빼내기→export→원부모 복원). 복원 단계는 **UUID 기반**으로 바꿔 동일 이름 오브젝트도 안전.
- **신규 Type Filter**: `Export` 섹션 "Include Types ▾" 드롭다운에 체크 항목(Mesh/Joint, 기본 전부 체크).
  체크 해제=제외, 목록에 없는 타입(curve/nurbs 등)은 항상 포함. Mesh 해제+Joint 유지 → 메시만 빠지고 나머지 전부 추출.
  타입 추가는 `core.FILTER_TYPES` + `_TYPE_MATCHERS` 두 곳만.
- **검증**: 전체 `py_compile` + 오프스크린 스모크(core 파일명 조립·필터 토글 + UI 생성) 통과. **Maya 실기(FBX
  export/reparent) 검증은 대기.** 문서 [A00040_file_exporter_V02](A00040_file_exporter_V02.md) + CHANGELOG/version v02.00.
  #FileExporter #FBX #타입필터 #PySide #재작업 #UUID

> [!summary] `A00220_BackupTool` v01.11→01.12 · `A00240_PathTool` v01.05→01.06 — 두 툴에 작업표시줄 아이콘 적용
- **요청**: A00210 과 같은 방식으로 이 두 standalone 툴에도 아이콘 생성·적용.
- **아이콘 제작**([taskbar_icon_guide.md](taskbar_icon_guide.md) 방식): 각 테마에 맞춘 SVG →
  QtSvg 사이즈별 렌더 → 멀티사이즈 `.ico`(16~256px)+`.png`.
  A00220 = **green_dark, 초록 문서 스택+백업 순환화살표**; A00240 = **purple_dark, 보라 폴더 계층 트리**.
- **배선(각 툴)**: `app/config/app_meta.py`(고유 `APP_USER_MODEL_ID` + dev/exe 경로 해석) 신설,
  `launch.py` 가 QApplication 전에 AUMID 지정 + `app.setWindowIcon`, `main_window` 창 아이콘,
  `build_exe.bat` 에 `--icon`/`--add-data "icon;icon"`.
- **검증**: `py_compile` + 오프스크린 스모크(두 툴 모두 멀티사이즈 아이콘·고유 AUMID·창 아이콘 non-null)
  통과. 각 CHANGELOG/version.py + docs([A00220_BackupTool](A00220_BackupTool.md)/[A00240_PathTool](A00240_PathTool.md)) §2 갱신.
  #BackupTool #PathTool #아이콘 #작업표시줄 #AppUserModelID #PySide

> [!summary] `A00330_NamingTool` v01.00→01.01 — 씬에 동일 이름 오브젝트가 있어도 리네임이 실패하지 않도록 수정
- **버그**: Naming Dyn 탭에 `joint_01`·`joint_03` 를 리스트업하고, 두 루트 밑에 각각 **같은 이름** `joint_02`
  자식이 있는 상태에서 **Naming Dynamics** 실행 시 `RuntimeError: Invalid path ...` 발생.
- **원인**: TSL 이 **short name** 을 저장 → `listRelatives` 로 받은 자손 이름(`joint_02`)이 씬에서 **모호**해
  `cmds.rename("joint_02", …)` 가 어느 노드인지 특정 못 함. 부모를 rename 하면 자식 경로가 바뀌는 문제도 있음.
- **수정(`app/core/naming_ops.py`)**: rename 을 **UUID 기반**으로 전환(`_to_uuid`/`_rename_by_uuid`). rename 전에
  `(UUID, 새 이름)` 배정을 모두 계산하고, UUID 로 **현재 경로를 매번 다시 해석**해 rename → 동일 이름/계층에도 안전.
  `build_hierarchy_groups` 는 입력을 `ls(long=True)` 정규화 + 자손을 `fullPath` 로 수집. 같은 취약점이 있던
  **Copy Name·Quick Rename**(insert/add/change/trim) 도 동일하게 하드닝.
- **검증**: `py_compile` 통과 + Maya 실기 확인 완료(사용자). 문서 [A00330_NamingTool](A00330_NamingTool.md) §7
  갱신 + CHANGELOG/version.py v01.01.
  #NamingTool #리네임 #UUID #동일이름 #버그수정

> [!summary] Standalone Qt 툴 작업표시줄 아이콘 재사용 가이드 문서 작성 (docs/taskbar_icon_guide.md)
- **배경**: A00210 에서 확립한 "작업표시줄 아이콘 만들기" 방식을 앞으로 다른 standalone 툴에도
  재사용하도록 문서로 남김(사용자 요청).
- **내용**: ① SVG→QtSvg 사이즈별 렌더→멀티사이즈 `.ico`(각 사이즈 SVG 직접 렌더·base=최대 프레임
  주의) ② `setWindowIcon` ③ **AppUserModelID 를 QApplication 생성 전 지정**(터미널 python.exe
  아이콘 대체의 핵심) + `app_meta.py`/`build_exe.bat` 배선·체크리스트. Maya 셸프 아이콘([icon_plan.md])과
  맥락 구분·상호 링크.
- **산출물**: [taskbar_icon_guide.md](taskbar_icon_guide.md). 메모리에도 방법 저장.
  #가이드 #작업표시줄 #AppUserModelID #PySide #ico #docs

> [!summary] `A00210_FileManager` v01.26→01.27 — 앱/작업표시줄 아이콘 추가 (터미널 실행 시 python 아이콘 대체)
- **요청**: 이 툴(터미널에서 `python launch.py` 로 실행)의 작업표시줄 아이콘을 적절히 바꾸고 싶다.
- **아이콘 제작**: blue_dark 테마에 맞춘 **파란 폴더 + 기록 카드 + 동기화 뱃지** SVG 를 그려
  (`icon/A00210_FileManager.svg`) QtSvg 로 사이즈별 렌더 → **멀티 사이즈 `.ico`(16~256px)** + `.png` 생성.
- **연결(`launch.py`)**: `app.setWindowIcon` + 창(`main_window`)에도 아이콘 지정. 터미널 실행 시 프로세스가
  `python.exe` 라 그대로면 python 아이콘이 떠서, Windows **AppUserModelID**
  (`Dnable.JUN.A00210.FileManager`)를 QApplication 생성 전에 지정해 앱 아이콘이 작업표시줄에 뜨게 함.
  경로 해석은 dev·PyInstaller 양쪽 대응(`app/config/app_meta.py`), `build_exe.bat` 에 `--icon`/`--add-data` 추가.
- **검증**: `py_compile` + 오프스크린 스모크(아이콘 경로/멀티사이즈/창 아이콘 non-null) 통과. 문서
  [A00210_FileManager](A00210_FileManager.md) §2 + CHANGELOG/version.py v01.27 갱신.
  #FileManager #아이콘 #작업표시줄 #AppUserModelID #PySide #ico

> [!summary] `A00220_BackupTool` v01.10→01.11 — 저장 톡 점프가 Windows 10 에서도 빨간색으로 표시되도록 수정
- **배경**: 대상 파일 저장 순간 공룡이 빨갛게 짧게 톡 점프하는데, **Win11 에선 빨갛게 되지만 Win10 에선
  점프만 하고 색이 안 변함**.
- **원인**: 저장 강조색을 **OS 팔레트 하이라이트**(`palette().highlight()`)에서 가져와서 — 이 색이
  Windows 버전마다 다르다(Win11=빨강 계열, Win10=시스템 파랑 등). 그래서 Win10 에선 빨강이 안 나왔다.
- **수정(`app/ui/dino_widget.py`)**: 팔레트 의존을 버리고 **고정 빨강 `#E53935`**(`_SAVE_ACCENT_COLOR`)
  으로 직접 그린다 → 모든 OS 에서 동일하게 빨간 톡 점프. 점프 타이밍·높이는 그대로.
- **검증**: `py_compile` 통과(실기 확인은 실행으로). 문서 [A00220_BackupTool](A00220_BackupTool.md)
  §5 + CHANGELOG/version.py v01.11 갱신.
  #BackupTool #저장감지 #Windows10 #팔레트 #강조색 #버그수정

---

## 2026-07-02

> [!summary] Kangaroo 스킨 웨이트 전이 코드 심층 분석 문서 작성 (docs/study)
- **요청**: Kangaroo 플러그인이 스킨 웨이트를 전이하는 방식을 코드 집중 분석하고, Maya 기본
  `Copy Skin Weights` 와 뭐가 다른지 정리한 문서를 `docs/study` 에.
- **분석**(외부/읽기전용 코드, 수정 없음): `kangarooTabTools/weights.py`(`transferSkinCluster`·
  `moveSkinClusterWeights`·`intTransferSkinCluster`), `kangarooTools/barycentric.py`
  (`getVertexCoordinates`·`getBarycentricCoords`), `patch.py`(`setSkinClusterWeights` + enum),
  `kt_findClosestPoints.mll`(C++). 핵심: ① "전이"가 실은 **Transfer(메시→메시)** 와
  **Move(조인트→조인트)** 두 기능 ② Transfer = C++ 최근접점 질의 → **면 무게중심 보간**(쿼드 전용
  넓이기반) → **numpy 벡터화**, 멀티소스 per-vertex 최근접 선택, **이름 기반 인플루언스 union/매핑**,
  경계 스무딩·prune·normalize·skinCluster 자동생성 후처리 통합 ③ Maya `copySkinWeights` 와 대응
  원리는 같으나 쿼드 정확도·멀티소스·이름 통합·후처리 통합·본→본 Move 로 차별화.
- **산출물**: [kangaroo_skinWeight_transfer_analysis.md](study/kangaroo_skinWeight_transfer_analysis.md)
  (파일·라인 참조 포함). 기존 [skinWeight_transfer_workflow.md](study/skinWeight_transfer_workflow.md)
  는 워크플로우 관점, 이번 문서는 코드 레벨 심층 분석으로 상호 링크.
  #Kangaroo #skinWeights #Transfer #barycentric #copySkinWeights #코드분석 #docs

> [!summary] `A00110_animTool` v01.23→01.24 — Always on Top(Pin) 토글 버튼 추가 (A00340 패턴 이식)
- **요청**: A00340_SelectionTool 처럼 창을 다른 마야 창 위에 고정하는 Pin 버튼을 A00110 에도.
- **구현(`app/ui/main_window.py`)**: 기존 `setMenuBar` 방식을 **QHBoxLayout 헤더 행**(메뉴 바 좌 +
  Pin 버튼 우)으로 바꾸고, 체크형 `Pin` 버튼(`setFixedSize(72, 28)`) 추가. `toggle_always_on_top()`
  이 `Qt.WindowStaysOnTopHint` 토글 + `show()` 재호출, ON 이면 라벨 `Pinned`·로그 기록. 이 툴은 기본
  정상 Z-order 라 필요할 때만 켜는 방식. A00340 과 동일 패턴이라 위치·크기 불변.
- **검증**: `py_compile` 통과(실기 확인은 마야 `run(True)` 리로드로 예정). 문서
  [A00110_animTool](A00110_animTool.md) v01.24 노트 + version.py v01.24 갱신.
  #animTool #AlwaysOnTop #Pin #WindowStaysOnTopHint #PySide

> [!summary] `A00210_FileManager` v01.25→01.26 — Store Repo / Shared Folder 입력을 한 칸으로 병합(모드별 경로는 각각 기억)
- **요청**: Source Mode(Remote/Local)마다 따로 있던 **Store Repo**·**Shared Folder** 입력 두 칸을
  하나로 병합해도 정상 동작할지 → 정상 동작하면 그대로 반영.
- **판단**: 단순히 "한 칸=한 경로"로 합치면 한 프로파일 안에서 모드를 오갈 때 상대 모드 경로 기억을
  잃는다. 그래서 **입력 칸은 하나로 보이되(라벨이 모드 따라 Store Repo↔Shared Folder 전환) 모드별
  경로는 각각 기억**하는 방식으로 구현 → UI 병합 + 동작·프로파일 호환성 무손실.
- **구현(`app/ui/main_window.py`)**: 데이터 폴더 입력을 `ipf_store_dir` 한 칸으로 통합(로컬 전용
  `ipf_local_dir`/`lbl_local`/`btn_local` 제거). 모드별 경로를 `self._path_values{git,local}` 에 보관,
  Source Mode 전환 시 떠나는 모드로 칸 값 저장→오는 모드 값 로드(`_on_source_mode_changed`). 라벨/
  플레이스홀더/툴팁은 `_apply_source_mode` 가 모드에 맞춰 전환, 데이터 폴더 칸은 두 모드 모두 항상 활성
  (git 전용 Remote/Branch/URL/Pull/Push 만 토글). `_load_prefs_to_ui`/`_collect_prefs` 는 여전히 프로파일
  `store_dir`/`local_dir` 두 키로 저장/복원 → **마이그레이션 불필요**.
- **검증**: `py_compile` 통과(실기 확인은 실행으로 예정). 문서
  [A00210_FileManager](A00210_FileManager.md) 개념표/화면구성/사용흐름 + CHANGELOG/version.py v01.26 갱신.
  #FileManager #SourceMode #StoreRepo #SharedFolder #UI병합 #프로파일호환

> [!summary] `A00340_SelectionTool` v01.00→01.01 — 창을 다른 마야 창 위에 고정하는 Always on Top(Pin) 토글 추가
- **요청**: 툴 UI 가 다른 마야 창들보다 항상 위에 뜨도록 하는 토글 버튼.
- **구현(`app/ui/main_window.py`)**: 체크형 `Pin` 버튼을 **상단 헤더 행**(QHBoxLayout: 메뉴 바 좌 +
  버튼 우)에 배치. `toggle_always_on_top()` 이 `Qt.WindowStaysOnTopHint` 를 켜고/끄고,
  플래그 변경 시 창이 숨는 Qt 특성을 피하려 **`show()` 재호출**. ON 이면 라벨 `Pinned`, 로그에도 기록.
- **버튼 배치 다듬기**: 처음엔 메뉴 바 코너 위젯(`setCornerWidget`)으로 뒀으나 토글 시 위치/크기가
  튀어(코너 geometry 재계산) **헤더 행 레이아웃 + 고정 크기(`setFixedSize(72, 28)`)** 로 변경 →
  `Pin`↔`Pinned` 토글에도 위치·크기 불변, 글씨 잘림 없음.
- **검증**: `py_compile` 통과, **마야 실기 확인 완료**. 문서
  [A00340_SelectionTool](A00340_SelectionTool.md) §사용법 + CHANGELOG/version.py v01.01 갱신.
  #SelectionTool #AlwaysOnTop #Pin #WindowStaysOnTopHint #PySide

> [!summary] `A00220_BackupTool` v01.09→01.10 — 저장 감지(공룡 톡 점프)가 Windows 10 에서도 동작하도록 mtime 폴링 fallback 추가
- **배경**: 파일 저장 순간 공룡이 빨간색으로 짧게 점프하는 애니(`notify_save`)가 **Windows 11 에서는
  되는데 Windows 10 에서는 안 됨**.
- **원인**: 저장 감지가 `QFileSystemWatcher.fileChanged` 신호에만 의존 — 이 신호는 Win10 이나 임시파일
  교체식(atomic replace) 저장에서 안정적으로 발화하지 않아 저장 순간을 놓쳤다(애니 자체는 순수 Qt 라 무관).
- **수정(`main_window.py`)**: **0.5초 mtime 폴링 fallback**(`_save_poll_timer`, 감시 중일 때만 동작) 추가.
  `_start_watching` 에서 mtime 기준선(`_watch_mtimes`)을 잡고, `_poll_saves` 가 변화한 파일을 저장으로 감지.
  기존 watcher(`_on_fs_changed`)와 폴링을 **공통 핸들러 `_on_save_detected`** 로 합치고 **mtime 으로 중복
  발화 제거** → Win11(watcher 정상)에서도 톡 점프는 한 번만. 백업용 `_last_mtimes` 와 감지용 `_watch_mtimes`
  는 별개라 간섭 없음.
- **검증**: `py_compile` 통과, **Windows 10 실기 확인 완료**. 문서 [A00220_BackupTool](A00220_BackupTool.md)
  §5-1 + CHANGELOG/version.py v01.10 갱신.
  #BackupTool #저장감지 #Windows10 #QFileSystemWatcher #폴링 #버그수정

> [!summary] `A00210_FileManager` v01.24→01.25 — Path Structure 트리 다중 선택 체크박스 토글이 반복 클릭에도 선택 유지
- **배경**: v01.24 의 다중 선택 일괄 토글이 **첫 클릭만** 선택을 유지하고, 두 번째 클릭부터 선택이
  한 행으로 붕괴됐다.
- **원인**: `itemChanged`(체크박스 토글)는 마우스 **릴리스** 시점에 발생하는데, 그때는 이미 Qt 가 선택을
  클릭한 한 행으로 붕괴시킨 뒤라, 그 시점 `selectedItems()` 로는 붕괴 전 다중 선택을 알 수 없었음.
- **수정**: 트리 뷰포트에 **이벤트 필터**를 달아 **마우스 누름(press) 시점**(붕괴 전)에 선택을 `_presel`
  로 캡처. 핸들러는 키보드 토글이면 온전한 `selectedItems()`, 마우스면 `_presel` 을 써서 대상 폴더 전체를
  일괄 토글(`_apply_state_to_rels`) 후 `singleShot(0)` 로 선택 복원. 매 클릭마다 press 시점에 (복원된)
  선택을 다시 캡처하므로 반복 클릭에도 유지됨.
- **검증**: `py_compile` 통과, **PySide 실기 확인 완료**. CHANGELOG/version.py v01.25.
  #FileManager #PathStructure #다중선택 #Qt #버그수정

> [!summary] `A00340_SelectionTool` v01.00 신규 — 마야 선택 오브젝트를 **버튼 하나로 다시 선택**하는 in-Maya PySide 툴
- **배경**: A00240_PathTool 처럼 버튼을 자유롭게 추가·삭제·순서변경 하되, **경로 열기 대신 마야 오브젝트를
  다시 선택**하는 툴이 필요했다.
- **개념**: **Selection 버튼**(현재 선택을 캡처 → 클릭 시 그 오브젝트 재선택, 이름변경/삭제된 것은 건너뛰고
  로그) · **Category**(버튼 그룹) · **Profile**(캐릭터/에셋별 버튼 세트, `data/profiles/<name>.json`).
  `Add` 토글 시 현재 선택에 누적.
- **구조**: 구성/편집 흐름(profile→category→button, 우클릭 Move Up/Down·Rename·Delete·Change Category·
  Update/Add Objects)은 **A00240_PathTool**, 마야 연동(launch `run()`·`__dragDrop_A00340.py` 셸프 설치·
  Maya parent 창·blue_dark 테마)은 **A00310_SearchTool** 에서 이식. core 분리: `prefs.py`(순수 JSON, DCC 비의존)
  + `maya_select.py`(capture/select). 아이콘(파란 선택 마퀴+커서) png/svg 제작.
- **검증**: **Maya 실기 확인 완료**. 문서 [A00340_SelectionTool](A00340_SelectionTool.md) + CHANGELOG +
  README 목록 등록. version.py v01.00.
  #SelectionTool #선택 #리깅 #애니메이션 #Maya #PySide #신규툴

> [!summary] `A00210_FileManager` v01.23→01.24 — Path Structure 탭: Preview 트리뷰(파일 토글·Expand) + 깊이/선택 재생성
- **배경**: Path Structure 탭이 ① Preview 를 ASCII 텍스트로만 보여주고 ② Save/Recreate 가 대상 경로의
  **모든 하위**를 통째로 저장·생성해서, 원하는 깊이·경로만 고르기 어려웠음. A00240 PathTool 의 Tree 탭처럼
  트리로 보고, 깊이(정수)와 경로(체크박스)를 골라 재생성하고 싶다는 요청.
- **Preview 트리뷰(feature 1)**: `QPlainTextEdit` → **`QTreeWidget`** 로 교체. **Show files** 체크박스
  (기본 **OFF**, 켜면 로컬 파일시스템에서 실제 파일도 표시 — 확인용, 재생성 대상 아님) + **Expand** 버튼
  (큰 창, 체크 상태 반영). 폴더/파일 표준 아이콘.
- **깊이·선택 재생성(feature 2)**: Save 그룹의 *Recursive* 체크박스 → **Capture Depth** 스핀박스
  (1=최상위만, 0=All)로 교체. Saved 그룹에 **Depth** 스핀박스(표시 겸 Recreate 깊이 제한, 0=All) +
  트리 **폴더별 체크박스**(해제 시 Recreate 제외; 루트=base 는 항상 생성, 체크된 자식의 상위는 자동 생성).
- **다중 선택 일괄 토글**: 트리를 **ExtendedSelection** 으로 바꿔 Shift/Ctrl 다중 선택 → 선택 항목 중
  하나의 체크박스를 누르면 선택된 폴더 전체가 동시에 체크/해제(`_syncing_checks` 재진입 가드).
  Saved Structures **목록 높이 축소**(maxHeight 120, stretch 0)로 남는 세로 공간을 Preview 트리에 배분.
- **core `path_structure.py`**: `PathStructure.max_depth` 필드 추가(구버전 JSON `recursive`→깊이 매핑으로
  하위호환: True=0/All, False=1/top). `_collect_folders(max_depth)` 로 깊이 캡처, `limit_depth()`,
  `build_structure_tree(structure, base_abs, show_files, max_depth)`(폴더 트리 + 실파일 병합),
  `recreate(..., folders=None)`(선택 목록만 생성, 중복 제거).
- **검증**: 변경 `.py` `py_compile` 통과 + 코어 로직 테스트(깊이 캡처/limit_depth/트리 빌드/파일 병합/
  구버전 from_dict/선택·깊이 recreate) 통과. **PySide 실기 확인 완료**.
- 문서: 가이드 [A00210_FileManager](A00210_FileManager.md) §4-C 갱신 + CHANGELOG/version.py v01.24.
  #FileManager #PathStructure #트리뷰 #깊이 #선택재생성 #Qt

## 2026-07-01

> [!summary] `A00220_BackupTool` v01.09 — 상태 공룡에 **저장 감지 순간(강조색 톡 점프)** 표현 추가: 저장 순간 ↔ 백업 순간(360° 스핀) 시각 구분
- **요청**: 공룡이 지금은 '툴 작동 중'·'백업 실시' 두 상태만 표현. Save Delay(v01.08) 로 *저장 순간* 과
  *백업 순간* 이 벌어졌으니, **사용자가 파일을 저장한 순간**을 눈으로 구분할 표현을 추가. → 스타일은
  사용자 확정 **"강조색 톡 점프"**.
- **dino_widget.py**: 스핀(`_spin_t`) 패턴을 미러링한 저장 펄스 상태 `_save_t` + `notify_save()` 추가.
  상수 `_SAVE_TICKS=12`(~0.4s, 자동 점프 18틱보다 스냅)·`_SAVE_PEAK_CELLS=5`(7칸보다 낮게). `_tick`
  우선순위 사다리 `스핀 > 저장 > 점프 > 자동점프`. paintEvent 비-스핀 경로에서 `_save_t` 활성 시
  스프라이트를 **테마 하이라이트색**(폴백 `#4CAF50`)으로 그리고 `_save_offset_px()` 만큼 톡 띄움.
  다리는 점프 포즈. 죽은 코드 `hop()`(v01.06 이후 미사용) 제거.
- **main_window.py**: 저장 감지 핸들러 `_on_fs_changed` 에서 백업 예약 직후 `self.dino.notify_save()`
  호출(감시 중 = Auto Backup 모드에서만). stale hop 주석/헤더 갱신. 버전 01.08→01.09.
- **검증**: 전 파일 `ast.parse` + 오프스크린 PySide6 실제 인스턴스화 단위검증 6/6 PASS(펄스 시작·종료,
  스핀 우선 양보, 저장 점프 높이<자동 점프, 정지 시 초기화, `_on_fs_changed`→notify_save+예약).
- **문서**: [A00220_BackupTool](A00220_BackupTool.md) 5장 Dino 상태표에 '저장 감지=강조색 톡 점프' 행 +
  저장/백업 순간 구분 설명, CHANGELOG 01.09.
  #백업 #UI #공룡애니메이션 #standalone

> [!summary] `A00145_RigConnect` v01.10 — Match 탭에 레거시 `DOOTOOL_PY_TOOL_Match.py` 의 체크박스 옵션(Translation/Rotation/Scale/Parent) 이식
- **요청**: 사내 레거시 `DOOTOOL_PY_TOOL_Match.py`(Doosup Jung, 2018)의 Match 옵션 체크박스를 A00145 Match 탭에
  이식하되, 동작·기본 체크 상태를 원본과 동일하게. 단 **Rotate Order / Rotate Axis 는 제외**(A00145 는 월드 행렬
  기반 매칭이라 무의미).
- **이식 항목/기본값**(원본 준수): Translation(ON) / Rotation(ON) / Scale — world space(OFF) /
  Parent Followers to Targets(OFF).
- **core(`match_manager.py`)**: `match()` 에 `translate/rotate/scale/parent` 인자 추가. transform 타겟은
  `matchTransform` 의 position/rotation/scale 플래그로 켜진 채널만 월드 매칭(원본 xform 방식 대신 rotateOrder-safe
  통일 유지). 원본 Scale(null+scaleConstraint 로 월드 스케일 읽기)은 `matchTransform scale`(월드 스케일 일치)로 대체.
  Parent 는 매칭 완료 후 별도 패스로 `_parent_one`(컴포넌트면 소유 transform 아래로, 자기자신/이미 자식이면 스킵,
  월드 위치 보존). vertex/mesh/cluster/component 특수 처리는 translate/rotate 로 게이팅(둘 다 꺼지면 vertex 샘플링도 스킵).
- **ui(`main_window.py`)**: Match 탭에 "Match Options" 그룹(4개 체크박스, 툴팁) 추가. `on_match` 가 값을 읽어 전달,
  채널 전무 시 경고 후 no-op, 로그에 적용 채널 `[TRSP]` 표기. About/버전 01.09→01.10 갱신.
- **검증**: 전 파일 `ast.parse` + 페이크 `maya.cmds` 로 core 단위검증 10/10 PASS(플래그별 matchTransform kwargs,
  parent→owner, already-child 스킵, count/skip). Maya 실기 대기.
- **문서**: 가이드 [A00145_RigConnect](A00145_RigConnect.md) Match 절에 옵션 설명 추가.
  #리깅 #매칭 #이식 #DOOTOOL

> [!summary] `A00220_BackupTool` v01.08 — Auto Backup 에 **저장 후 지연(Save Delay)** 도입: 크래시로 손상된 파일이 정상 백업을 덮어쓰는 사고 방지
- **문제/진단**: PC 가 사고로 자주 종료되는데, 종료 시점에 저장 중이던 Maya 파일이 **손상된 채 디스크에
  남는다**. 기존 Auto Backup 은 저장을 감지하자마자(~300ms 디바운스) 백업해, 그 손상 파일이 정상 백업본을
  덮어써 버렸다. → **10초 지연**이 해결책이 되는지 진단: 백업 툴이 크래시하는 PC 와 **운명을 함께하므로**,
  저장 후 지연 백업을 in-process 타이머로 예약해 두면 크래시 시 예약 백업도 함께 사라져 손상 파일이
  백업되지 않는다(직전 정상본 보존). "저장 후 N초 생존 = 정상 저장" settle 휴리스틱 — **타당**하다고 판단, 구현.
- **구현**: 저장 감지(`_on_fs_changed`) 시 즉시 복사 대신 **파일별로 `{path: 지금+Delay}` 예약**. 1초 폴링
  `_process_pending_backups` 가 due 지난 파일만 백업(예약 있을 때만 타이머 동작). 지연 중 재저장되면 그
  파일만 재예약(settle). 기존 300ms 디바운스(`_debounce_timer`/`_pending_changes`/`_flush_pending_changes`)
  제거. 주기 Interval fallback 은 그대로.
- **UI/설정**: Settings 에 **Save Delay(sec)** 스핀박스(기본 10, 0~600, 0=다음 폴링에 백업) 추가.
  prefs `save_delay` 영속화(+ 기존 `auto_backup` 도 DEFAULTS 에 명시). 버전 01.07→01.08.
- **검증**: 전 파일 `ast.parse` 통과(표준 라이브러리 로직, standalone). 실사용 검증 대기.
- **문서**: [A00220_BackupTool](A00220_BackupTool.md) 5-1 절에 지연 원리/보완(Version Up) 추가, CHANGELOG 01.08.
  #백업 #크래시복구 #standalone #PySide

## 2026-06-30

> [!summary] `A00170_driverTool` v01.07 — AttachCrv 탭에 **Distribute(균일 분배)** 모드 추가 (`ref_01.mel` 원래 동작 복원)
- **배경**: AttachCrv 탭은 그동안 TSL 의 *기존* 오브젝트를 커브 최근접 지점에 붙이는 동작만 있었다. 원본
  `ref/ref_01.mel`(attachDriverOnCurve, Doosup Jung)에 있던 **"양의 정수 N 만큼 새 오브젝트를 커브에 균일
  배치"** 기능을 추가해 달라는 요청.
- **core(`app/core/attach_curve.py`)**: `build_attach_uniform(curve, count, driver_type, full_range, ...)`
  신규(= `run_attach_uniform`). 파라미터 분배는 ref `makeParameterValueList` 그대로 — `count==1`→구간 중앙,
  **full_range ON**→`division=count-1`(양 끝 정확히 포함, 열린 커브), **OFF**→`division=count`(마지막이 끝
  직전, 주기/닫힌 커브 seam 중복 방지). Locator/Null 드라이버 생성 → `<curve>_<NN>_drv`(0 패딩) 리네임 →
  기존 `_attach_one()` 을 `param=` 인자로 재사용(=None 이면 closest, 값 주면 그 파라미터). 매트릭스 네트워크
  (pointOnCurveInfo→fourByFourMatrix→multMatrix→decomposeMatrix)·orient·norCrv·set 은 Closest 모드와 공유.
- **UI(`app/ui/main_window.py`)**: AttachCrv 탭에 "Distribute new drivers uniformly" 그룹(Count spin /
  Driver Type 콤보 / full-range 체크 / **Distribute Drivers on Curve** 버튼) + `on_atc_distribute` 핸들러.
  orient/Aim Axis/norCrv/set 옵션은 두 모드 공유. About 갱신, 버전 01.06→01.07.
- **검증**: 전 파일 `ast.parse` 통과. Maya 실기 대기.
- **문서**: 가이드 [A00170_driverTool](A00170_driverTool.md) AttachCrv 절에 Distribute 사용법 추가.
  #리깅 #커브어태치 #이식 #PySide

> [!summary] `A00320_ARKitCurveTool` 신규 — Unreal "Add ARKit Curves to Skeleton" 분석 + 재현 코드/가이드 정리
- **배경**: Unreal Content Browser 에서 Skeleton 우클릭 시 나오는 *"Add ARKit Curves to Skeleton"*(선택
  스켈레톤에 ARKit 52 블렌드셰이프 커브 메타데이터 일괄 등록) 기능이 어떻게 구현됐는지 분석하고, 같은 동작을
  **직접 만드는 방법**을 정리해 달라는 요청. (Maya 셸프 툴이 아니라 Unreal 용 참조/이식 코드 모음)
- **분석**: 기능은 엔진 수정이 아니라 프로젝트 플러그인(MANUEditor=메뉴 익스텐더 / MANUAnimationEd=커브 추가
  로직 / MANUAnimation=52개 이름)에 분업 구현. 핵심 API `USkeleton::AddCurveMetaData()` 는 `UFUNCTION` 이
  아니라 **Python/BP 미노출** → 두 접근 제공.
- **코드(`tools/A00320_ARKitCurveTool/`)**: ① **하이브리드(B-2, 권장)** — 얇은 C++ 래퍼
  `MANUSkeletonCurveLibrary.h/.cpp`(52 이름 자체 포함, 외부 모듈 의존 없음)를 BP/Python 에 노출 +
  `add_arkit_curves.py`(실행) + `init_unreal.py`(ToolMenus 우클릭 메뉴 자동 등록). ② **빌드-프리** —
  `nobuild_arkit_curves.py`(API discover + 커브 포함 애니 임포트 / `unreal.AnimationLibrary` 경로, 컴파일 0).
- **바닐라 호환**: 스톡 `unreal` API 만 사용 — 커스텀 엔진 비의존(바닐라 UE 5.5 동작).
- **문서**: 학습 노트 [분석](study/Add_ARKit_Curves_to_Skeleton_분석.md) ·
  [B안 구현가이드](study/Add_ARKit_Curves_B안_구현가이드.md), 가이드 [A00320_ARKitCurveTool](A00320_ARKitCurveTool.md)
  신규 작성, README 인덱스 등록.
  #ARKit #Unreal #스켈레톤커브 #LiveLink #이식 #참조코드

> [!summary] `A00330_NamingTool` v01.00 신규 — 레거시 `JUN_PY_NamingTool_V03_04`(maya.cmds) PySide 이식 + ref_01.mel 3번째 탭 통합
- **배경**: 레거시 네이밍 툴은 절차형 `cmds` UI 2탭(Naming Dynamics, Copy name)이었다. 이를 다른 툴들과
  동일한 **PySide 창 + QTabWidget** 구조로 이식하고, 현장용 빠른 리네임 MEL(`ref/ref_01.mel`)을 **3번째 탭**으로 합쳤다.
- **구조**: `A00310_SearchTool` 컨벤션 그대로 — `__dragDrop_A00330.py`(셸프 설치) / `launch.py`(green_dark 테마) /
  `app/{config,core,ui}`. 리스트 UI 는 공용 위젯 `JUN_mod_tsl_qt_v01` 재사용, 로직은 `app/core/naming_ops.py`(thin UI).
- **탭**: ① **Naming Dyn** — `T1_T2_T3_Idx1_Idx2` 계층 토큰 리네임(Idx1=루트 그룹별, Idx2=항목별 증가, 0 패딩,
  transform 자손만). ② **Copy Name** — Base leaf 이름(+Prefix)을 Targets 에 순서대로 적용. ③ **Quick Rename**(신규,
  `ref_01.mel` 이식) — Front Insert / Change New(+인덱스, 10 미만 0 패딩) / Last Add / `-1 Front`·`-1 Rear` / All Apply.
  모든 작업은 단일 Undo(`undo_chunk`)로 묶음.
- **정정/개선**: 원본 `is 0`(Py3 경고) → `== 0`; 이름 처리 시 네임스페이스(`:`)까지 제거해 rename 안정성 향상.
- **아이콘**: green 테마 네이밍/태그 아이콘 생성(svg + png 64/32).
- **검증**: 전 파일 `py_compile` 통과. 가짜 `maya.cmds` 주입 단위 테스트 **13/13 PASS**(인덱스 패딩·10 경계·
  네임스페이스 제거·계층 transform 필터링·copy 개수 불일치 경고). Maya 실기 대기.
- **문서**: 가이드 [A00330_NamingTool](A00330_NamingTool.md) 신규 작성, README 인덱스 등록.
  #namingTool #리네임 #PySide #이식 #ref이식 #신규툴

> [!summary] `A00040_file_exporter` v01.01→01.03 — 월드 최상위(부모 없음) 오브젝트 내보내기 에러 수정 + 인덱스 정렬/비교 정리 (Maya 실기 검증 완료)
- **배경**: 세트 내보내기 시 멤버가 **다른 오브젝트의 차일드가 아니면**(월드 최상위)
  `get_parents()` 의 `cmds.listRelatives(sel_obj, parent=True)` 가 `None` 을 반환 →
  `[0]` 인덱싱에서 `'NoneType' object is not subscriptable` 로 내보내기 실패.
- **수정(`utility.py`)**: ① `get_parents()` — 부모가 없으면 `None` 으로 표시(`prnt[0] if prnt else None`).
  ② 복원 단계 — 월드 최상위(`None`)였던 오브젝트는 그대로 두고 reparent 건너뜀.
  ③ **인덱스 정렬**: `cmds.parent(members, world=True)` 가 *이미 월드에 있던* 오브젝트를
  반환에서 제외해 `objs_out`↔`parents_origin` 가 어긋나던 문제를, 멤버를 하나씩 월드로 빼내며
  `(새 이름 ↔ 원래 부모)` 짝을 `zip` 으로 유지하도록 재작성. ④ 재부모 루프의 바깥 루프 변수
  `i` 섀도잉 제거, `len(...) is 0` → `== 0` 비교 정정.
- **결과**: 추출 대상이 다른 오브젝트의 차일드든 월드 최상위든 모두 정상 내보내기.
- **문서**: 가이드 [A00040_file_exporter](A00040_file_exporter.md) 신규 작성.
- **검증**: Maya 실기 확인 완료(월드 최상위 오브젝트 내보내기 정상). 헤더/타이틀 v01.03.
  #fileExporter #FBX #export #objectSet #버그수정

---

## 2026-06-29

> [!summary] `A00170_driverTool` v01.05→01.06 — AttachCrv 탭에 norCrv(노멀 커브) 방향 옵션 추가(ref_01.mel 원본 방식)
- **배경**: 원본 `ref/ref_01.mel`(attachDriverOnCurve, by Doosup Jung)은 별도 **norCrv** 직선 커브를
  만들어 커브에 어태치된 오브젝트들의 **up(위) 방향**을 정했다. 현재 AttachCrv 탭은 norCrv 없이 월드 +Y
  시드의 자족 직교 프레임만 썼음. 원본 방식(norCrv)을 옵션으로 추가하고 **기본값으로** 삼고 싶다는 요청.
- **구현(core `attach_curve.py`)**: `build_attach_to_closest(..., use_normal_curve=True, normal_curve_length=1.0)`
  추가. orient + use_normal_curve 면 `_create_normal_curve()` 로 attachCrv 밑에 직선 norCrv(원점→(0,±len,0),
  +X/-X 부호) 1개를 만들어 `matchTransform`(pos+rot) 후 parent. 오브젝트마다 norCrv 용 `pointOnCurveInfo` 를
  하나 더 만들어 **fourByFourMatrix X=attachCrv 접선 / Y=norCrv 접선 / Z=norCrv 노멀**(-X 면 세 행 반전)로 구성
  — ref 노드 구성 그대로. 반환에 `norcrv` 추가(4-튜플). use_normal_curve=False 면 기존 자족 프레임 유지.
- **UI(main_window)**: AttachCrv 탭에 **Create Normal Curve (norCrv)** 체크박스(기본 ON) + **norCrv Length**
  스핀박스 추가. Orient OFF 면 둘 다 비활성(`_atc_sync_orient_enabled`). 빌드 후 생성된 norCrv 이름을 로그에 표시.
  About/가이드 [A00170_driverTool](A00170_driverTool.md) §4.3 갱신.
- **검증**: 변경 `.py`(attach_curve/main_window) `py_compile` 통과(Maya 실기 대기). version.py v01.06.
  #driverTool #AttachCrv #norCrv #리깅 #커브어태치 #이식

> [!summary] `A00080_KWI_creator_V03` v01.01→01.02 — 언리얼 Kawaii Physics Bone Constraints Data Asset 내용 생성 "Constraints" 탭 추가(두 탭 구조)
- **배경**: 언리얼에서 `dyn_asset_side_0[1-7]_0[1-5]` / `dyn_asset_side_0[2-8]_0[1-5]` 두 줄 브래킷
  패턴으로 KawaiiPhysics 제약(Data Asset) 내용을 자동 생성하지만 **가끔 에러**가 나서, Maya 에서 동일
  텍스트를 직접 만들어 클립보드로 복사하려 함.
- **Tab 2 "Constraints"**(신규): `(Chain A, Chain B)` 브래킷 패턴 쌍 입력 → **인덱스 1:1 zip** → 합본.
  **+ Add pair** 로 여러 쌍을 받아 하나의 출력으로 병합. `[a-b]` 는 정수 a..b 로 확장(왼쪽 브래킷이
  바깥 루프), 리딩 `0` 은 리터럴이라 **제로패딩 없음**(단일자리 가정). 두 체인 개수 불일치 시 에러.
  출력 = `(` + `(BoneReference1=(BoneName="A"),BoneReference2=(BoneName="B"))` 콤마결합 + `)`,
  미리보기 + 클립보드 + `0020_out/A020_LDA_constraint_out.py` 기록.
- **Tab 1 "KWI Nodes"**: 기존 노드 생성 UI 그대로. `main_window` 를 **QTabWidget** 로 재구성, 로그는 하단 공유.
- **core/템플릿**(신규): `constraint_creator.py`(`ConstraintCreator`: expand_pattern/build_pairs/build_text/
  create_file), `0010_src/A0202_Src_LDA_constraint_entry.py`(단일 항목 템플릿). `A0201_*` 은 골든 샘플로 보존 —
  예시 단일 쌍 출력이 `A0201`(3501자)과 **정확히 일치** 검증.
- **검증**: 변경 `.py` `py_compile` 통과 + 코어 기능 테스트(단일/다중/불일치/빈입력) 통과, **Maya 실기 확인 완료**.
  가이드 [A00080_KWI_creator](A00080_KWI_creator.md) 신규 + CHANGELOG/version.py v01.02 갱신.
  #KawaiiPhysics #언리얼 #Constraint #DataAsset #텍스트생성

> [!summary] `A00270_skinMigrate` v01.00→01.01 — 레거시 move_skinWeightTool 원본 2버튼 UI 를 "Classic" 탭으로 이식(두 탭 구조)
- **배경**: A00270 은 레거시 `JUN_PY_move_skinWeightTool_v01_04`(외부 `import kangarooTabTools.weights`
  사용) 에서 "스마트 통합"(Transfer+Move 체이닝)만 추려 단일 화면으로 만든 상태. **원본의 2버튼 UI 는 누락**돼
  있었음. 이를 복원해 두 탭으로 재구성.
- **Tab 1 "Classic"**(원본 충실 이식): `From`/`To` TSL + Transfer Mode 콤보 + 버튼 2개 —
  `Joints to Joints (single mesh)`(현재 선택 메시에서 `From[i]→To[i]` 웨이트 이동, Kangaroo
  `moveSkinClusterWeights`, selection 기반) / `Meshes to Meshes`(`From[i]→To[i]` skinCluster 전이,
  Kangaroo `transferSkinCluster`, 인덱스 쌍 루프).
- **Tab 2 "Migrate A → B"**: 기존 v01.00 통합 마이그레이션 그대로. 로그창은 두 탭 공유로 하단 이동.
- **core**(`SkinMigrateManager`): `move_joints_in_mesh`/`transfer_meshes` 추가. Kangaroo lazy import 를
  `_import_kangaroo()` 헬퍼로 공통화(외부 3rd-party 플러그인 — 미존재 시 안내 메시지, 무수정).
- **검증**: 변경 `.py`(skin_migrate_manager/main_window) `py_compile` 통과(Maya 실기 대기). 가이드
  [A00270_skinMigrate](A00270_skinMigrate.md) + CHANGELOG/version.py v01.01 갱신. #skinMigrate #리깅 #스킨웨이트 #kangaroo #이식

> [!summary] `A00120_FKIK` v01.06→01.07 — Bake IK/FK 가 구간 밖/다른 레이어 포즈를 바꾸던 버그 수정(컨스트레인트 제거)
- **증상**: 컨트롤러가 base + 다른 애니메이션 레이어 2곳에 키가 있을 때, base 레이어에서 특정 구간만
  Bake IK 하면 **구간 밖 포즈가 베이크 전과 달라짐**. 원본 `JUN_PY_FKIK_Tool_V02_01` 에는 없던 현상.
- **원인**: `fkik_matcher.bake()` 가 임시 `parentConstraint` + `bakeResults` 사용. 컨스트레인트가
  pairBlend 를 끼워 기존 animCurve 를 분리·머지 → 레이어가 있으면 구간 밖까지 오염. 스냅샷/복원 우회책도
  머지 커브만 봐서 **레이어를 인식 못함**.
- **해결(사용자 요구: 컨스트레인트 0)**: 레거시처럼 **per-frame** 으로 되돌림 — 프레임마다 `currentTime` →
  각 쌍 `cmds.matchTransform(position+rotation)` → follower translate/rotate 키. `setKeyframe` 이 활성
  레이어에만 써서 구간 밖/타 레이어 안전. `matchTransform` 은 **rotateOrder 가 서로 달라도 정확**
  (A00145 Match 탭 방식). `match_transforms` 도 xform rotateOrder 스왑 → `matchTransform` 으로 교체.
  `_snapshot/_restore` 는 의도적 컨스트레인트 경로인 `bake_constraint()`(Bake (Constraint) 버튼) 전용으로 잔존.
- **기능 추가**: Start/End 스핀박스 옆에 **Get Current** 버튼(A00110 패턴) — 현재 프레임으로 각 칸 갱신.
  창 맨 위에 **Help > About** 메뉴 바 추가(QMenuBar, 버전/날짜 + 버튼 동작 요약).
- **검증**: 변경 `.py`(fkik_matcher/main_window) `py_compile` 통과(Maya 실기 대기). 가이드
  [A00120_FKIK](A00120_FKIK.md) §4·5 + version.py v01.07 갱신. #FKIK #리깅 #베이크 #애니레이어 #버그수정

---

## 2026-06-26

> [!summary] `A00170_driverTool` v01.04→01.05 — Remap Value 탭 List Attributes/Search 강화(A00145 방식)
- **배경**: Remap Value 탭의 List Attributes 가 keyable 어트리뷰트만 보여줘 범위가 좁았고, 검색은 현재
  목록 안에서만 선택했다. A00145_RigConnect Connect 탭처럼 더 많은 attr + 검색으로 미리스트 attr 발견을 원함.
- **구현**: `core/maya_scene.py` 에 `MayaScene.list_attrs(obj, search="")` 추가(A00145 connect_manager
  list_attrs 이식) — `listAttr(obj)` 전체, 중첩("." ) skip, multi/compound 는 getNextFreeMultiIndex 로
  판정해 자식 펼침. search 시 `listAttr(obj.search)` 로 재질의. 기존 `list_keyable_attrs` 제거.
- **핸들러**(main_window): `on_rmp_list_attributes` → `list_attrs(first)`(전체). `on_rmp_search_attrs`
  → 현재 목록에 토큰 매칭 있으면 선택, 없으면 `list_attrs(first, token)` 로 재질의해 미리스트 attr
  채움(try/except). Attr Search 툴팁 보강.
- **검증**: 변경 `.py`(maya_scene/main_window) `py_compile` 통과(Maya 실기 대기). 가이드
  [A00170_driverTool](A00170_driverTool.md) §4.1 + version.py v01.05 갱신. #driverTool #리깅 #어트리뷰트 #UX

> [!summary] `A00310_SearchTool` v01.00 신규 — 레거시 Selection + Search 툴 2개를 PySide 탭으로 통합
- **배경**: `~/Documents/maya/2024/prefs/scripts` 의 단일 파일 maya.cmds 툴 `JUN_PY_SelectionTool_V02_01`
  + `JUN_PY_SearchTool_V01_02` 를 한 PySide 툴로 합치고 탭으로 구분해 달라는 요청.
- **구현(arch B, A00170 골격 복제)**: `JUN_All/tools/A00310_SearchTool/` 신설. core(maya.cmds, UI 비의존):
  `maya_scene.py`(선택/계층 펼치기/노드 타입) + `search_select.py`(collect_from_selection / collect_types /
  select_by_types / select_by_token, CONSTRAINT_TYPES 5종). ui `main_window.py`: QTabWidget 2탭(접두사
  `sel_*`/`sch_*`) + 공유 로그 + Help>About + 푸터.
  - **Selection 탭**: Source(Hierarchy/Selected)·Invert 옵션, Types|Objects TSL(Get/List Types),
    Select By Shape(Mesh/nurbsCurve/Joint/Constraint), Select By Type(선택 타입 매칭).
  - **Search 탭**: Search Token + 옵션 + Objects TSL + Search By Token.
- **공용 TSL**: `JUN_mod_tsl_qt_v01` 사용 — 사용자 요청대로 **Sort 버튼 포함**(show_sort 기본값 유지).
  Hierarchy/Selected 를 따르도록 기본 Select 버튼 대신 커스텀 **Get** 버튼(add_button)으로 채움.
- **마무리**: 셸프 설치 `__dragDrop_A00310.py`(TOOL_LABEL "SearchTool"), **아이콘**(svg+png, 리스트+돋보기),
  가이드 [A00310_SearchTool](A00310_SearchTool.md), version.py v01.00. 전 `.py` `py_compile` 통과(Maya 실기 대기). #SearchTool #SelectionTool #UI #신규툴

> [!summary] `A00170_driverTool` v01.03→01.04 — 새 탭 **AttachCrv**(커브 최근접 지점 어태치) 추가
- **배경**: `ref/ref_01.mel`(attachDriverOnCurve, by Doosup Jung)을 이식하되 **동작을 바꿔** 달라는 요청.
  원본은 커브에 *일정 간격*으로 새 로케이터를 어태치 → 대신 **TSL 의 기존 오브젝트들**을 각자
  커브에서 **가장 가까운 지점**에 라이브로 붙인다.
- **구현**: 새 core `app/core/attach_curve.py`(maya.cmds, 자족). 오브젝트마다 임시 `nearestPointOnCurve`
  로 최근접 파라미터 취득 → `pointOnCurveInfo → fourByFourMatrix → multMatrix(* parentInverseMatrix)
  → decomposeMatrix → translate`(옵션 `rotate`). orient 시 접선을 aim 축(+X/-X)에 맞추고 side=T×up,
  up'=side×T(vectorProduct)로 직교 프레임 구성. 부모 계층 안전 + 커브 변형 추종.
- **UI**: `_build_attach_tab()` + 탭 "AttachCrv"(접두사 `atc_*`). Attachment Curve(Get), Objects TSL,
  Orient 체크박스 + Aim Axis 콤보, Build 버튼. `__init__` 에 `run_attach_to_closest` 재노출, About 갱신.
- **세트 옵션**: 체크박스 "Group pointOnCurveInfo nodes into a set"(기본 ON) → 빌드로 생성된 모든
  `pointOnCurveInfo` 노드를 objectSet 하나(`<curve>_atcPOCI_SET`)로 묶음. core 가 poci 들을 모아
  `cmds.sets(...)` 생성, 반환을 `(attached, failed, set_node)` 로 확장.
- **검증**: 변경 `.py`(attach_curve/main_window/core __init__) `py_compile` 통과(Maya 실기 대기).
  가이드 [A00170_driverTool](A00170_driverTool.md) §1·2·4.3 + version.py v01.04 갱신. #driverTool #리깅 #커브 #UI

> [!summary] `A00145_RigConnect` v01.08→01.09 — 모든 TSL 에 **Sort 버튼** 노출
- **배경**: 4탭의 모든 리스트(TSL)가 정렬 버튼 없이 입력 순서로만 쌓여 항목이 많아지면 찾기 불편했다.
- **핵심 관찰**: 공용 위젯 `JUN_mod_tsl_qt_v01` 이 이미 `show_sort` 플래그(기본 `True`)와 Sort 버튼을
  갖고 있는데, 이 툴만 9개 TSL 전부 `show_sort=False` 로 끄고 있었다 → **인자 제거만으로 활성화**.
- **구현**: main_window.py 의 모든 TSL 생성에서 `show_sort=False` 제거(Match·Constrain·Skin·Connect·
  Stream·Connect Closest 탭의 Targets/Followers/Vertices/Objects/Driven/Driver). 공용 위젯의 기본
  Sort(`sorted(get_all_items())`) 동작을 그대로 사용 — 위젯 변경 없음.
- **후속 수정(같은 버전)**: Sort 버튼이 한 줄씩 더해지면서 **Connect 탭**(Source/Destination 두 섹션 +
  큰 버튼 2개가 한 창에 세로로 쌓임)에서 공간 부족 시 TSL 버튼이 창 경계를 침범. → Connect 탭 내용을
  `QScrollArea(setWidgetResizable=True)` 로 감싸 공간이 모자라면 겹치는 대신 스크롤바가 생기게 함.
- **검증**: `main_window.py` `py_compile` 통과(Maya 실기 대기). version.py v01.09 + 헤더 날짜 갱신. #RigConnect #UI #TSL

> [!summary] `A00240_PathTool` v01.04→01.05 — ShortCut 탭 **Path 버튼 순서 변경**(우클릭 Move Up/Down)
- **배경**: 카테고리는 이미 우클릭 Move Up/Down 으로 재정렬되는데, 그 안의 Path 버튼은 만든 순서에 고정돼 있었다.
- **구현**: `_show_button_menu` 맨 위에 **Move Up / Move Down**(+구분선) 추가, 카테고리 내 인덱스로 끝단 자동 비활성.
  `_move_button(cat_name, btn_name, delta)` 가 `cat["buttons"]` 에서 인접 버튼과 자리를 맞바꿔 저장·재렌더 —
  카테고리 재정렬(`_move_category`)과 동일 패턴이라 화면 순서=리스트 순서가 그대로 프로파일 JSON 에 반영된다.
- **검증**: `shortcut_tab.py` `py_compile` 통과(Qt 실기 대기). 가이드 [A00240_PathTool](A00240_PathTool.md) 5절 표/설명 +
  CHANGELOG + version.py 갱신. #PathTool #UI #UX

> [!summary] `A00210_FileManager` v01.22→01.23 — **Source Mode** 추가(Remote Git ↔ Local 공유/NAS 선택)
- **배경**: 팀 협업 시 매번 git push/pull 하는 대신 **NAS 같은 공유 저장소**에 데이터를 두고
  파일 서버가 동기화하도록 하고 싶다는 요구.
- **핵심 관찰**: 데이터 read/write 는 이미 `store_dir`(일반 폴더) 기반이고 git 에 묶인 건 Pull/Push
  레이어뿐. Lineage·Path Structure 탭도 폴더를 직접 읽는다 → **새 동기화 로직 불필요**.
- **구현**: Settings 에 **Source Mode** 콤보(`Remote (Git)`/`Local (Shared / NAS)`)와 **Shared Folder**
  입력 추가. `_effective_store_dir()` 한 곳이 모드에 따라 Store Repo(git)/Shared Folder(local)를 반환,
  `get_store_dir()`·`_make_store()` 가 이를 사용해 **모든 탭이 활성 모드 폴더를 자동으로 따름**.
  local 모드에선 git 입력·Pull/Push 비활성 + 안내. `source_mode`/`local_dir` 은 **프로파일별 저장**.
- **자동 폴더 생성**: `MetaStore.ensure_store()` 추가 → 빈 공유/NAS 폴더라도 첫 저장 시 `records/`·`thumbs/`
  가 함께 생성(`_stamp_and_save` 에서 호출). (lineage/path_structure 저장도 기존 `_ensure_parent` 로 자동 생성.)
- **검증**: 변경 `.py`(main_window/store/prefs) `py_compile` 통과(Qt 실기 대기). 가이드
  [A00210_FileManager](A00210_FileManager.md) 5-C 절 + CHANGELOG + version.py 갱신. #FileManager #협업 #NAS #UI

---

## 2026-06-25

> [!summary] `A00110_animTool` v01.22→01.23 — 확장된 `Get Current` 버튼이 동작 안 하던 버그 수정
- **배경**: v01.22 에서 Follow 외 탭(Move Keys/Copy/Mirror/Bake)으로 넓힌 `Get Current` 버튼이
  눌러도 Start/End 입력이 갱신되지 않았다. Follow 탭 버튼만 정상.
- **원인**: 공용 헬퍼 `_make_get_current_btn` 의 슬롯이 `lambda le=line_edit:` 로 **위치 인자 1개**를
  받는 형태였다. PySide `clicked` 시그널은 슬롯에 `checked`(bool) 인자를 넘기는데, 그 값이 `le` 기본값을
  덮어써 `_set_current_frame(False)` 로 호출 → `False.setText` 로 실패. Follow 버튼은 무인자 람다라 무사.
- **수정**: `lambda *_a, le=line_edit:` 로 checked 인자를 흡수해 모든 탭 버튼이 현재 프레임으로 갱신.
  `app/ui/main_window.py` 만 변경.
- **검증**: 가이드 [A00110_animTool](A00110_animTool.md) v01.23 노트 + version.py 갱신(마야 실기 대기). #anim #UI

> [!summary] `A00300_meshDoctor` v01.00→01.01 — zero_area 판정을 형상품질(q) 기반으로 + Clear Log 버튼
- **배경**: polyCleanup(zeroGeom 1e-05) 후에도 `zero_area_faces` 가 FAIL 로 남고, 선택하면 육안 보이는
  아주 작은 면이 나오는 사례. 트리거는 Maya `it.zeroArea()`. 진짜 슬라이버(케이스 A, Transfer 깨짐)와
  작지만 멀쩡한 면(케이스 B, 오탐)을 구분 못 하던 문제(사용자 메시는 케이스 A).
- **개선**: 절대 면적/`zeroArea()` 의존을 줄이고 **스케일 무관 형상품질** `q=(4π·area)/perimeter²`(`face_quality`)로
  판정. 후보(`zeroArea()` or `area<AREA_TINY 1e-5`) 중 `area<AREA_DEGEN 1e-10` 또는 `q<QUALITY_EPS 1e-2` →
  `zero_area_faces`(FAIL, 슬라이버), 그 외 → 신규 `tiny_faces`(INFO, 결함 아님)로 강등해 오탐 제거.
- **로깅**: 플래그된 면마다 `f<idx> a=<area> q=<q>` 를 샘플로 남겨 JSON/TXT 에서 A/B 육안 구분.
  `Select Zero-Area Faces` 헬퍼도 동일 기준. zero_area 메시지에 "필요한 면이면 closestVertex 모드로" 안내.
- **UI**: 로그뷰 아래 **`Clear Log`** 버튼 추가.
- **검증**: 변경 `.py`(mesh_scan/mesh_fix/main_window) `py_compile` 통과(마야 실기 대기). 가이드
  [A00300_meshDoctor](A00300_meshDoctor.md) 진단노트 "v01.01 적용" + CHANGELOG + version.py 갱신. #메시진단 #스킨 #kangaroo

> [!summary] `A00290_BSTool` v01.00→01.01 — Edit BS 탭에 `Copy every frame`(구간 프레임별 메시 추출) 추가
- **Feat**: `Start`/`End` 구간을 **1프레임마다** 씬에서 **선택한 메시**를 복제(visibility off)해
  `<mesh>_f<frame>`(0 패딩)으로 추출하고 `<mesh>_frames` 그룹으로 묶는다. **키 없이** 현재 씬 애니메이션
  상태를 그대로 캡처(`suspend_refresh` + 종료 시 현재 프레임 원복, 전체 단일 undo).
- **UI**: 구간 입력(`Start`/`End` + `Get Current`)은 A00110 Follow 탭 패턴. 대상은 blendShape 리스트가
  아니라 씬 선택 메시. 로직 `edit_bs_manager.copy_every_frame(meshes, start, end)`.
- **검증**: `py_compile` 통과(마야 실기 테스트 대기). 가이드 [A00290_BSTool](A00290_BSTool.md) +
  CHANGELOG v01.01 + version.py 갱신. #blendShape #페이셜 #UI

> [!summary] `A00110_animTool` v01.21→01.22 — `Get Current` 버튼을 시간범위 탭 전체로 확장
- **Feat**: Follow 탭에만 있던 `Get Current`(현재 Maya 프레임으로 Start/End 입력 채움) 버튼을
  **Key Edit(Move Keys) · Copy Key · Mirror Key · Bake** 탭의 Start/End 에도 추가.
- **구현**: 공용 헬퍼 `_make_get_current_btn(line_edit)` 로 버튼 생성 일원화, 핸들러
  `_follow_set_current_frame` → `_set_current_frame`(범용)으로 변경. Bake 탭은 Custom range 일 때만
  버튼 활성(입력 필드와 동일 토글 `_bake_update_range_mode`). `app/ui/main_window.py` 만 변경.
- **검증**: `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기). 가이드
  [A00110_animTool](A00110_animTool.md) v01.22 + version.py 갱신. #애님 #UI

> [!summary] `A00110_animTool` v01.20→01.21 — Follow 탭: 비-베이스 레이어 베이크가 베이스와 동일한 월드 결과를 내도록 수정
- **증상**: Follow 를 비-베이스 애님 레이어(특히 **additive**)에 구우면 ① 구간 안 위치가 어긋나고 ② 회전이
  베이스와 다르며 ③ **구간 밖 원본 애니메이션이 상수만큼 평행이동**. 베이스 레이어 베이크는 정상.
- **근본 원인(사용자 제공 좌표로 확정)**: `setKeyframe(animLayer=L, value=V)` 는 레이어 커브에 V 를 그대로
  쓰는 게 아니라 **'평가 결과(아래 레이어+이 레이어) = V' 가 되도록 레이어 기여를 역산**해 기록한다.
  → override 는 절대값 `V=F` 를 넘겨 정상이었으나, additive 는 **델타 `V=F−base`** 를 넘겨 평가값이
  `F−base` 만큼 어긋남. 중립 `value=0` 도 `additive=−base` 로 역산돼 구간 밖 오프셋으로 유지됨.
  (보내준 커브 값이 정확히 `additive=−base`, `base_pin=2×원본` 패턴이라 역산 동작이 증명됨.)
- **수정**: override/additive 구분 없이 **항상 절대 로컬값 F 만 기록** → Maya 가 레이어 종류에 맞는 기여
  (additive 회전 합성 포함)를 자동 계산. **델타 계산·base 읽기·회전 합성 캘리브레이션·base-pin 전부 제거**
  (코드 단순화). 구간 밖은 경계(`start-1`/`end+1`)에 **원본 절대값**을 키 → 레이어 기여 0, 레이어 커브
  **Infinity=constant** 고정으로 구간 밖 0 기여 유지(원본 위치 변화 없이 그대로 재생).
- **범위**: `follow_match_manager.py` 만 변경(`py_compile` 통과, 사용자 Maya 검증 완료 "아주 잘 됨").
  가이드 [A00110_animTool](A00110_animTool.md) v01.21 항목 + 트러블슈팅 갱신, version 01.21. #애니메이션 #리깅 #애님레이어

> [!summary] 신규 툴 `A00300_meshDoctor` v01.00 — 메시 진단(읽기 전용) + 안전 원클릭 수정 + 로그 출력
- **목적**: 문제 메시 두 증상 해결 — ①빈 공간 클릭해도 메시 선택됨(=bbox 팽창) ②kangaroo Transfer 시 일부만
  이동/페이스 일그러짐(=토폴로지 손상). 메시를 **읽기 전용 진단**해 JSON+TXT 로그를 `0020_out/` 에 출력하고,
  그 로그를 Claude 가 분석해 근본 원인을 짚는 워크플로.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00300`/app core·ui 분리,
  blue_dark 테마, 마야 메인윈도우 parent). 진단 로직은 `maya.cmds` + `maya.api.OpenMaya` 2.0(Maya 2023 호환).
- **진단(`mesh_scan.py`)**: NaN/Inf 정점, 떠돌이(stray) 정점, bbox 팽창, intermediate(orig) shape, 잔여 history,
  non-manifold edge/vertex, lamina/holed/concave/zero-area 페이스, zero-length edge, 겹친(미병합) 정점,
  border edge, 음수 스케일, UV 셋/누락 UV, skinCluster — 각 `PASS/INFO/WARN/FAIL` + 의심 근본원인 매핑.
- **수정(`mesh_fix.py`, 전부 Undo 가능)**: Delete History(deformer-safe), Merge Vertices, Conform Normals,
  polyCleanup(non-manifold+lamina+zero-area+zero-edge), Snap NaN/Stray Verts(정점 삭제 없이 좌표만 복구).
  + 문제 컴포넌트 선택 헬퍼(non-manifold/zero-area face/stray·NaN vert).
- **로그(`report.py`)**: `PathManager(write_dir="0020_out")` 로 `meshDoctor_<scene>_<ts>.json` + `_summary.txt` 출력.
- **문서**: kangaroo Transfer 원리(barycentric)와 **메시를 수정하지 않고 Transfer 하는 법**(`closestVertex` 모드 전환,
  근거 `weights.py:2073-2077`) + **NaN(Not a Number) 정의**까지 가이드에 정리. kangaroo 플러그인은 **읽기 전용 참조, 미수정**.
- **아이콘**: 전용 셸프 아이콘 신규(32×32 ARGB svg+png) — 다크 라운드 배경 + 청록 와이어프레임 메시 +
  우하단 빨간 의료 십자 배지(진단/수리 모티프). GDI+ 렌더, `__dragDrop_A00300` 이 이미 경로 참조.
- **문서 보강**: 가이드에 NaN(Not a Number) / manifold·non-manifold / lamina face 용어 정의 추가.
- **검증**: 신규 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기).
  가이드 [A00300_meshDoctor](A00300_meshDoctor.md) + CHANGELOG v01.00. #리깅 #메시진단 #스킨 #kangaroo

> [!summary] `A00080_KWI_creator_V03` v01.00→01.01 — 합본 클립보드 복사 · Help 메뉴바 · 본 개수 표시
- **Feat: 합본 코드 클립보드 복사.** **Create combined file** 실행 시 base+setting+LD 합본 텍스트만
  `QApplication.clipboard().setText(...)` 로 복사 → 언리얼 AnimGraph 에 바로 Ctrl+V. (개별 파일 내용은 복사 안 함.)
  코어 `KWI_creator.create_combined_file()` 반환을 `out_path` → `(out_path, combined)` 튜플로 변경.
- **Change: Help 버튼 → 메뉴바.** 우상단 `QPushButton("Help")` 제거, `QMenuBar` 의 `Help > How to use`
  액션으로 이동(`layout.setMenuBar`). A00260_ConstraintConverter 의 메뉴바 패턴과 동일.
- **Feat: TSL 본 개수 표시.** `Target bones (Root bones)` 라벨에 현재 개수를 붙여 표시(예: `... : 3`).
  `tsl_bones.model()` 의 `rowsInserted`/`rowsRemoved` 시그널에 연결해 추가/삭제/Clear/Load 어떤 경로로 바뀌어도 자동 동기화.
- **검증**: 수정 `.py` `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기).
  가이드 [A00080_KWI_creator_V03](A00080_KWI_creator_V03.md) + CHANGELOG v01.01 갱신. #언리얼 #KawaiiPhysics #리깅

---

## 2026-06-24

> [!summary] 신규 툴 `A00290_BSTool` — 레거시 BS Tool(maya.cmds) 을 PySide 로 재작성 + Base Shape 탭 추가
- **목적**: `~/Documents/maya/2024/prefs/scripts/JUN_PY_BSTool_V01_01`(maya.cmds UI) 을 **PySide(Qt)** 로 재작성.
  기존 툴의 **Connect BS 탭은 제외**하고 **Edit BS 탭만** 이식, **Base Shape 탭**을 신규 추가.
- **아키텍처**: (B) PySide-in-Maya — `A00270_skinMigrate` 클론(launch/`__dragDrop_A00290`/app core·ui 분리,
  green_dark 테마, 마야 메인윈도우 parent, `QTabWidget` 2탭 + 공용 로그).
- **탭1 Edit BS**: blendShape 노드 TSL(`JUN_mod_tsl_qt`) + `Key every target`(프레임 i=1, i±1=0 으로 타겟 순차 키) +
  `Copy every target`(키 후 프레임마다 베이스 메시 복제→타겟 이름 메시 추출, vis off, `<node>_targets` 그룹).
- **탭2 Base Shape (신규)**: blendShape 를 `<- Set`(노드/메시 선택에서 탐색)→`List Targets` 로 타겟 나열, 선택 타겟의
  **weight=Value 모양을 weight=1.0 기본 모양으로 재정의**. 원리: 결과=`base+weight·delta` 이므로 델타를 **Value 배**
  스케일하면 weight 1.0 이 예전 Value 모양이 됨(0.5→절반, 1.3→과장). 구현은
  `inputTargetItem[*].inputPointsTarget`(pointArray) 직접 스케일, in-between·다중 지오 포함, 단일 undo.
  Value 0 금지, 저장 델타 없는(라이브 지오) 타겟은 스킵+로그.
- **코어 분리**: `blendshape_utils`(타겟 조회/인덱스 매핑/베이스 메시/선택→blendShape) ·
  `edit_bs_manager`(Edit BS) · `base_shape_manager`(델타 스케일) — 모두 UI 비의존.
- **검증**: 신규 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기;
  특히 pointArray get/setAttr 라운드트립 권장). 전용 아이콘(System.Drawing 64x64 png + svg, 페이스 모핑 모티프).
  가이드 [A00290_BSTool](A00290_BSTool.md) + CHANGELOG v01.00 + README 등록. #블렌드셰이프 #페이셜 #리깅

> [!summary] 신규 툴 `A00080_KWI_creator_V03` — KWI Creator 를 마야 내부 실행(PySide)으로 버전업 + 본 TSL 입력
- **목적**: 언리얼 KawaiiPhysics 노드 텍스트 생성기(`A00080_KWI_creator_V02`)를 **마야에서 드래그&드롭으로
  설치/실행**하는 (B) PySide-in-Maya 툴로 버전업. **생성 로직은 V02 와 동일**.
- **V02→V03 차이**: ① standalone PySide 앱 → **마야 내부 실행**(`__dragDrop_A00080` → 셸프 `KWI_V03` →
  `tools.A00080_KWI_creator_V03.run(True)`, 마야 메인윈도우 parent). ② 타겟 루트 본을 파일
  (`A0101_tgtBones.py`)이 아니라 **UI 의 TSL(`QListWidget`)** 로 입력 — 입력란/Add·**Add Selected**(씬 선택)·
  Remove·Clear·**Load Example**. 코어에 `KWI_creator.set_tgt_bones(list)`/`get_default_tgt_bones()` 추가.
- **추가 작업**: 상단 **Help 버튼**(`QMessageBox` 사용 안내 팝업, `exec_()` 로 PySide2/6 호환), **전용 아이콘**
  (PIL 렌더 32x32 png + svg, 앵커바+흔들리는 컬러 비드 체인).
- **검증**: 신규/수정 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기).
  가이드 [A00080_KWI_creator_V03](A00080_KWI_creator_V03.md) + CHANGELOG v01.00 + README 등록. #언리얼 #KawaiiPhysics #리깅

> [!summary] A00280_correctiveFromCache — 실사용 피드백 반영 (v01.00→01.01)
- **Fix: PoseWrangler Route "Target mesh is not skinned" 오탐 제거.** PoseWrangler `create_blendshape`(api.py:1165)의
  skin 검사는 skinCluster 가 **노출 셰이프에 직접 연결**돼 있어야만 통과 — skinCluster 가 디포머 체인 마지막이 아닌
  의상 메시(흔함)에선 스킨돼 있어도 에러. 체크 없는 `create_blendshape_safe`(go default→isolate→duplicate→
  `add_existing_blendshape`)로 대체. invertShape 는 히스토리로 skin 을 찾으므로 결과 동일.
- **Feat: `default` 포즈 코렉티브 생성 옵션.** Options 에 `Include 'default' pose` 체크박스 — ON 이면 default 행도
  자동 체크되고 코어가 스킵하지 않음(기존엔 항상 스킵).
- **Fix: 타겟 이름이 A00090 `rules_v01` 약속을 따름.** default 타겟이 `default` 로 나오던 문제 → 솔버 이름에서
  접두사 추출 `<prefix>_default`(예: `WRK_calf_l_UERBFSolver`→`calf_l_default`). 비-default 포즈는 이미 접두사 포함이라 그대로. 양 Route 공통.
- **Feat: Frame Step 입력.** 포즈→프레임 = `start + index x step`(기본 1). abc 캐시가 포즈당 N프레임 간격(예: 60)으로
  정착되도록 시뮬된 경우 step=60 → 0,60,120… 자동 채움(미정착 프레임 샘플링 방지). 행별 수동 편집 유지.
- **검증**: 변경 `.py` 전부 `py_compile` 통과 + 타겟 네이밍 5케이스 단위 검증(PASS). 마야 실기 재확인 대기.
  가이드 [A00280_correctiveFromCache](A00280_correctiveFromCache.md) + CHANGELOG v01.01 반영. #리깅 #페이셜 #RBF #후디니

> [!summary] A00260_ConstraintConverter — 생성 노드 간 ExecutePin 연결(RigVMLink) 추가 (v01.03→01.04)
- **노드 실행 체인 연결**(`ref_/sample_04.py` 기준): 여러 컨스트레인트를 한 번에 변환할 때 생성된 노드들을
  **생성 순서대로 `ExecutePin` → `ExecutePin`** 으로 잇는 `RigVMLink` 블록을 노드 텍스트 뒤에 덧붙인다 —
  붙여넣으면 노드들이 **실행 체인으로 연결된 상태**가 된다(이전엔 노드만 흩어져 나와 수동 연결 필요).
- **구현**: 신규 템플릿 `0010_src/A0004_Src_link.py`(`{{GRAPH}}`/`{{IDX}}`/`{{SOURCE_NODE}}`/`{{TARGET_NODE}}`) +
  `NodeBuilder.build_links(graph, node_names)` — `node_names[i] → [i+1]` 로 N-1 개(`RigVMLink_0 … RigVMLink_{N-2}`) 생성,
  **노드 1개 이하면 링크 없음**. `ConverterPaths.read_link_tmpl` 경로 추가, `build_text` 가 `blocks + links` 를 결합.
- **검증**: 핵심 4파일 `py_compile` 통과 + `build_links` 단독 실행으로 3노드→링크 2개가 `sample_04.py` 와
  동일 포맷, 0·1노드 엣지케이스 빈 결과 확인. 가이드 [A00260_ConstraintConverter](A00260_ConstraintConverter.md) v01.04 반영. #리깅 #언리얼 #ControlRig

> [!summary] 신규 툴 `A00280_correctiveFromCache` — MetaHuman RBF 의상 주름 코렉티브를 후디니 Alembic 캐시에서 배치 추출
- **목적**: RBF(PoseWrangler) 의상 주름 코렉티브 작업에서, 각 포즈 hold 프레임마다 마야 Shape Editor 로 의상을
  abc 캐시에 **수동 매치**하던 (타겟수×관절수 ≈ 32회) 병목을 제거 → 캐시에서 코렉티브를 **버튼 한 번**으로 일괄 추출.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00280`/app core·ui 분리, coral_dark).
- **핵심**: 포즈 프레임에서 캐시 형상 월드 스냅샷 → `go_to_pose` → PoseWrangler `edit_blendshape` 의 EDIT 메시에
  캐시 포인트 복사 → `edit_blendshape(edit=False)` 내부 `cmds.invertShape()` 가 bind(스킨 이전) 델타 생성 + 솔버 자동 와이어.
  토폴로지 동일(캐시==의상) 전제. `UERBFAPI(view=False)` 헤드리스 래핑. 포즈→프레임 = `start + poses().index()`.
- **Route 2종**: `PoseWrangler`(솔버 자동 와이어, 기본) / `Direct invertShape`(타겟 이름만, 와이어는 `A00090_ConnectionBuilder` 위임).
- **UI**: 솔버소스(씬/JSON) + Garment/Alembic + Start Frame + per-pose 테이블(체크/프레임 편집/Status) + 옵션
  (exists Skip/Overwrite, skip-if-delta, **L/R Mirror** 선택) + Generate/Mirror 버튼. 전체 단일 undo + suspend_refresh, 종료 시 default/타임 복원.
- **core**: `pose_wrangler_bridge`/`alembic_cache`/`mesh_transfer`(MFnMesh 월드 포인트)/`corrective_batch_manager`/`solver_source`/`mirror_manager`.
- **효과**: 미러 없이 ~32 수동 매칭 → 0(설정 후 1클릭). L/R 미러 시 왼쪽 ~16만 생성 후 오른쪽 자동(절반).
- **검증**: 신규 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 sample_04.json 솔버+후디니 abc 필요). 전용 아이콘(주름 캐시→RBF 허브).
  계획서 [A00280_correctiveFromCache_plan.md](A00280_correctiveFromCache_plan.md) + 가이드 [A00280_correctiveFromCache](A00280_correctiveFromCache.md) + CHANGELOG + README 등록. #리깅 #페이셜 #RBF #후디니

> [!summary] A00260_ConstraintConverter — 닫힘(접힘) 노드 출력 + 노드 가로 배치(4개마다 줄바꿈) + 리로드 안정화 (v01.00→01.03)
- **닫힘 노드 출력**(`ref_/sample_02_close.py` 기준): 펼침(`sample_01_open.py`)과의 차이가
  세 컨테이너 핀(AdvancedSettings / Parents 배열 / Filter)의 `bIsExpanded=True` **3줄뿐**임을 diff 로
  확인 → 템플릿에서 제거. 붙여넣은 노드가 접힌 채라 길이가 짧다. 닫힘 샘플 입력으로 생성 결과가
  `sample_02_close.py` 와 **381줄 전부 동일** 검증.
- **노드 가로 배치**(`ref_/sample_03.py` 참고): 기존 세로 배치를 가로로 변경 — `col = idx % N`,
  `pos_x = start_x + 340·col`. 한 줄 **4개**를 넘으면 줄바꿈해 아래로(`row = idx // 4`,
  `pos_y = start_y + 280·row`). 간격은 sample_03 의 노드 간 X(약 307)를 참고.
- **리로드 안정화**: 닫힘(템플릿 파일)은 즉시 반영됐으나 배치(파이썬 모듈)는 안 바뀌던 문제 —
  `main_window` 가 import 시점에 옛 `ConstraintConverter` 를 바인딩(같은 깊이 모듈 reload 순서)했기 때문.
  `on_convert`/`_collect_options` 에서 **지역 import**(launch.py 패턴)로 바꿔 리로드 후 최신 클래스를
  잡도록 수정 → 코드 변경 즉시 반영. #리깅 #언리얼

> [!summary] A00145_RigConnect — Connect Closest 탭에 `Get Closest` 버튼 추가 (v01.07→01.08)
- **목적**: Driver 리스트의 각 오브젝트에 **가장 가까운 오브젝트가 무엇인지 발견**하고, 그 결과로
  `Driven` 리스트를 driver 순서대로 미리 채운다.
- **후보 풀**: `Driven` 에 항목이 있으면 그걸 풀로, 비어 있으면 **현재 씬 선택**을 풀로 사용(하이브리드).
  driver 자신은 풀에서 자동 제외(거리 0 회피).
- **핵심 설계**: 매칭을 공용 함수 `match_closest_pairs(drivers, pool)`(driver 순서 greedy 1:1, 쓰인 후보
  제거)로 빼고 **기존 `connect_closest` 와 신규 `find_closest_for_drivers` 가 공유** → 채워진 `Driven` 은
  곧 `Connect` 가 실제 연결할 페어의 **미리보기**가 된다. `connect_closest` 도 이 함수를 쓰도록 리팩터.
- **UI**: Driver TSL 버튼 행에 `Get Closest` 버튼(`add_button`). 핸들러는 `driver -> closest (dist)` 로그
  + 찾은 오브젝트를 **뷰포트에서 선택**해 발견 검증을 돕는다. 거리 기준은 기존과 동일한 월드 피벗 거리.
- **검증**: 변경 4파일 `py_compile` 통과. 실제 매칭/뷰포트 선택 동작은 Maya 런타임 확인 필요.
  가이드 `docs/A00145_RigConnect.md`(Get Closest 설명 + 헤더 버전 v01.08) 갱신. #A00145 #리깅

> [!summary] 신규 툴 `A00270_skinMigrate` — 토폴로지가 다른 두 메시 사이의 스킨 웨이트 전이 + 본 재매핑을 버튼 한 번으로
- **목적**: 외형은 비슷하나 토폴로지가 다른 리깅 메시 A, B 에서 ① A 의 웨이트/본을 B 로 **Transfer** →
  ② B 의 웨이트를 `A_joint_i → B_joint_i` 로 **Move** 하던 수동 2단계(Kangaroo Builder skinCluster 탭)를
  **1-click** 으로 단축. 결과적으로 B 가 자기 본 `[B_joint..]` 에 올바르게 바인드된다.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00270`/app core·ui 분리,
  coral_dark 리깅 테마). 전신은 Transfer/Move 를 각각 호출하던 `A00020_move_skineWeightTool`.
- **엔진 추상화 (UI 라디오로 선택)** `SkinMigrateManager.migrate(...)`:
  - `Kangaroo`(기본) — `kangarooTabTools.weights` 의 `transferSkinCluster`(bAutoCreateNewSkinCluster) +
    `moveSkinClusterWeights`(xJoints) 체이닝. 사용자가 수동으로 누르던 두 버튼과 **동일 결과**. 본 매핑은
    A00020 의 검증된 `['{joint}']` list-literal 포맷 사용.
  - `Native` — `cmds.copySkinWeights` + `maya.api` `MFnSkinCluster.getWeights/setWeights`. 플러그인 무의존,
    Move 는 본 1:1 컬럼 이동(per-vertex 최근접/스무딩 없음). setWeights 특성상 세밀 undo 미보장 → 정밀작업은 Kangaroo 권장.
- **입력/검증**: Source A / Target B(`<- Set`) + Joints A(From)/B(To) 두 TSL(행 순서 zip 매핑). 개수 일치·메시·
  joint 존재 검사 + **Strict joint check**(기본 ON, From 본이 A 에 안 묶였으면 에러로 순서/오타 조기 발견).
  옵션: Transfer Mode(기본 Closest Point), Remove unused influences(ON), Select result mesh. 전체 단일 undo 청크.
- **아이콘**: `icon/A00270_skinMigrate.svg`→`build_icons.py`(mayapy PySide2 QtSvg)로 32px PNG 렌더 —
  파랑 메시 A → 초록 메시 B + 화살표(웨이트 마이그레이션) 모티프. (초기 placeholder 가 animTool 과 동일했던 것 교체)
- **검증**: 신규 `.py` 전부 `py_compile` 통과, native 엔진 시그니처를 Maya API 사양에 맞춰 보정(skinCluster
  `unbind` 플래그 부재→`cmds.delete`, create 인자 `inf+[mesh]`, `addElements(list(...))`). 가이드 문서
  [A00270_skinMigrate](A00270_skinMigrate.md) + 계획서 + CHANGELOG + README 목록 등록. #리깅 #스킨

> [!summary] 신규 툴 `A00260_ConstraintConverter` — 마야 컨스트레인트 → 언리얼 Control Rig Parent Constraint 노드 텍스트 변환
- **목적**: 마야 씬의 컨스트레인트 세팅(타겟·웨이트·대상)을 **언리얼 Control Rig 의 Parent Constraint 노드
  텍스트**로 변환해 **클립보드에 복사** → UE 그래프에 `Ctrl+V` 붙여넣기. 출력 포맷 레퍼런스는 UE 에서
  복사한 원본 `ref_/smaple.py`(clavicle_out_l ← clavicle_l 0.6, upperarm_l 0.4) 를 그대로 따른다.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00260`/app 분리,
  green_dark 테마). 파일 생성 흐름은 `A00080_KWI_creator_V02`(PathManager + `0010_src`/`0020_out` +
  `{{KEY}}` TemplateEngine)를 따른다.
- **읽기**(씬→데이터) `constraint_reader`: 선택에서 컨스트레인트 수집(노드면 그대로/트랜스폼이면 하위
  `-type constraint`), `targetList`/`weightAliasList` 로 타겟·웨이트, 컨스트레인트 부모로 대상(child)을
  읽어 짧은 이름(네임스페이스·DAG 제거)으로. 지원: parent/point/orient/scaleConstraint.
- **생성**(데이터+옵션→텍스트) `node_builder`: 타겟 개수만큼 Parents 배열을 동적 조립 — 선언/정의는
  인덱스 **내림차순**, 컨테이너 `SubPins` **오름차순**, `bIsDynamicArray=True` 는 **첫 parent 에만**
  (UE 직렬화 형태 재현). 노드명 `ParentConstraint_N` 고유화 + Position Y 오프셋.
- **옵션(UI 전역 적용)**: Translate/Rotate/Scale 필터(기본 Translate 만), Maintain Offset(기본 ON),
  InterpolationType 드롭다운(Average/Shortest, 기본 Shortest). UI: Constraints TSL + 옵션 + Convert + 로그.
- **아이콘**: `icon/A00260_ConstraintConverter.png`(64px) — 타겟 2(녹색)→대상 1(UE 블루) 컨스트레인트
  모티프. drag-drop `ICON_NAME` 이 자동 참조(부재 시 `pythonFamily.png` 폴백).
- **검증**: 샘플 데이터로 생성한 결과가 `ref_/smaple.py` 와 **384줄 전부 동일**, 타겟 1·3개 케이스
  인덱스/SubPins/동적배열 플래그 정상, 신규 `.py` 14개 `py_compile` 통과. 가이드 문서
  [A00260_ConstraintConverter](A00260_ConstraintConverter.md) + README 목록 등록. #리깅 #언리얼

> [!summary] docs 학습 노트 분리 — `docs/study/` 신설 + 스킨 웨이트 전이 워크플로우 학습 문서 작성
- **배경**: `JUN_All/docs/` 루트는 **툴 사용법 안내 문서만** 두기로 정리. 특정 툴 안내가 아닌
  **작업 방법론·기법 학습 노트**를 담을 별도 경로가 필요해 **`docs/study/`** 를 신설(기존 `docs/plans/`
  =개발 계획 과 대칭). 이제 docs 는 3분할 — `docs/*.md`=툴 안내, `docs/plans/`=개발 계획, `docs/study/`=학습 노트.
- **신규 학습 문서** `docs/study/skinWeight_transfer_workflow.md`: 잘 웨이트된 메시 A 의 스킨 웨이트를
  토폴로지가 다른 메시 B 로 옮기는 작업 방식 정리. **Shrink Wrap + Blendshape 로 A 를 B 표면에 공간 정렬 →
  Kangaroo Transfer → 다듬기** 흐름의 원리("전이 정확도 = 공간 오버랩", closest-point 대응)와 우려 지점
  (투영 실패 구역·갭 누출·바인드 포즈·인플루언스 이름 매핑), 개선책(게임용 maxInf/prune/normalize 후처리,
  Geodesic Voxel Bind 보조, 스냅샷, Delta Mush, 구역 분할 전이), 전이 방식 비교표 수록.
  관련 개발 계획 [A00270_skinMigrate](plans/A00270_skinMigrate_plan.md)(Transfer+Move 1-click 툴)와 상호 링크.
- **인프라**: `docs/study/README.md`(작성 규칙 + 문서 목록 표) 신규, `docs/README.md` 에 `study/` 폴더
  안내 + 3분할 요약 추가. #docs #리깅

---

## 2026-06-23

> [!summary] Maya 툴 셸프 아이콘 생성 — Ari 스타일 학습 후 툴별 고유 32×32 아이콘 + drag-drop 연동
- **배경**: Maya 내부에서 도는 모든 툴이 셸프 설치 시 동일 기본 아이콘 `pythonFamily.png` 를 써
  셸프에서 구분 불가. Maya 사용자 아이콘 폴더의 **`Ari*` 9종을 학습**(32×32 ARGB, 다크 차콜 배경 +
  얇은 프레임 + 고채도 단순 도식 글리프)해 같은 톤의 **툴별 고유 아이콘**을 만들었다.
- **대상 20종**(베이스 템플릿·standalone `A00240` 제외, 버전 중복은 현행 우선): A00010_V02·A00020·
  A00030·A00040·A00050·A00060(V01/V02)·A00090·A00110·A00120·A00130·A00140·A00145·A00150·A00160·
  A00170·A00180·A00190·A00200·A00211·A00250. 각 툴 도메인을 상징하는 모티프(스켈레톤·본체인·키프레임·
  FKIK 스위치·NURBS 컨트롤·미러 메시·페이셜 마커·DAG 레인·메모 등)로 디자인.
- **방식**: SVG 작성 → 래스터화. 환경에 SVG 도구가 전무(cairosvg/Pillow/Inkscape 부재)했으나
  **Maya 2024 mayapy + PySide2 `QSvgRenderer`** 로 추가 설치 없이 32×32 ARGB(= Ari 포맷 일치) 출력.
  신규 **`JUN_All/dev/build_icons.py`**(개발 편의 스크립트)가 `tools/*/icon/*.svg` 를 일괄 PNG 로
  렌더(mayapy/QtSvg 우선, svglib/reportlab 폴백). 소스 SVG + 결과 PNG 를 각 툴 **`icon/`** 폴더에
  함께 둬 자기완결(드롭 설치 시 함께 이동)·재생성 가능.
- **drag-drop 연동(전체 처리)**: 기존 `__dragDrop_*.py` 18개의 `ICON_NAME` 을 **툴 폴더 내 아이콘
  절대경로 + 부재 시 `pythonFamily.png` 폴백**(`os.path.exists`)으로 교체(`image1=ICON_NAME` 호출부는
  무수정). drag-drop 이 없던 **A00020·A00030·A00090 은 신규 생성**(고유 베이스네임·`sys.modules.pop`
  충돌방지 규칙 준수, A00090 은 namespace 패키지라 `launch.run` 직접 호출).
- **Icon Label(셸프 라벨) 통일**: drag-drop 22개의 `cmds.shelfButton` 에 `imageOverlayLabel=TOOL_LABEL`
  추가 — Tooltip(`annotation`)과 **동일한 `TOOL_LABEL` 값**(예: `ConnBuilder`·`FKIK_Gen`)을 써 아이콘
  위 라벨과 툴팁이 일치한다(아이콘만으로 부족할 때 식별 보강). 값은 기존 축약 라벨 유지.
- **검증**: 아이콘 21개(A00060 V01/V02 2벌) 전부 **32×32 ARGB** 확인, drag-drop 21개 + build_icons
  `py_compile` 통과, PNG 는 `.gitignore` 대상 아님(추적 OK). 셸프 실설치 동작은 Maya 실행 확인 필요.
  계획서 신규 `docs/icon_plan.md`(Ari 분석·툴별 디자인표·도구체인·와이어링·검증). #Framework

> [!summary] A00110 animTool — Offset & Hold 기본 placeholder 10→20 (v01.19→01.20)
- Key Edit 탭 **Offset & Hold** 의 `Hold` 입력칸 placeholder 기본값을 `10` → `20` 으로 변경(UX 기본값
  조정, 로직 무변경). `version.py` 01.19→01.20. #A00110

> [!summary] Framework/테마 — Qt 툴 21개를 카테고리별 qss 색으로 통일
- **계획서 작성**(`docs/theme_category_unification_plan.md`) 후 적용. 각 툴 `launch.py` 의
  `ThemeManager.load_theme_*(..., "<color>")` 색 인자만 카테고리 표준으로 교체(로직 변경 없음).
- **카테고리→색**: Rigging=`coral_dark`(9), Animation=`blue_dark`(2), Modeling=`yellow_dark`(1),
  Facial=`red`(1), UE/Physics=`purple_dark`(1), Pipeline/Utility=`green_dark`(5), Template=`dark`(2).
- **변경 14건**: A00120/130/140(red)·A00150/170(yellow_dark)·A00160(green_dark)·A00190(blue_dark) →
  `coral_dark`; A00110(coral_dark)→`blue_dark`; A00080(dark)→`purple_dark`;
  A00210/211(blue_dark)·A00240(purple_dark)·A00250(coral_dark)→`green_dark`; A00008(red)→`dark`.
  나머지 7개는 이미 표준색이라 유지. 색 바뀐 13개 툴 `version.py` 패치 +1, 관련 가이드 docs(A00170/
  190/210/240) 테마 표기 갱신.
- **대상 외**: arch A(maya.cmds) 툴(A00000/10/20/30/40/50/60/70)은 `ColorThemeRegistry` 버튼색
  시스템이라 별도(후속). A00100/200/230 은 테마 호출 없음. **검증**: 변경 launch.py `py_compile` 통과,
  전 21개 매핑 재확인. 창 색 육안 확인은 Maya/standalone 실행 필요. #framework #theme

> [!summary] A00110 animTool — Key Edit 탭에 'Delete All Keys' 섹션 추가(v01.17→01.18)
- **Key Edit 탭에 접이식 섹션 'Delete All Keys' 추가**(기존 3섹션 → 4섹션, 기본 접힘). 선택 오브젝트를
  TSL(`JUN_mod_tsl_qt_v01`, `List Selected Objects` 버튼)에 리스트업하고, **리스트 전 항목의 모든
  키프레임을 일괄 삭제**하는 버튼을 둔다. 대상은 씬 선택이 아니라 리스트 항목(기존 Offset & Hold 와 동일 패턴).
- **코어**: `KeyframeManager.delete_all_keys(objects)` 추가 — `cmds.cutKey(clear=True)`(전 구간·전 채널,
  구간삭제와 달리 시간/채널 스코프 미적용), `undo_chunk` 로 Ctrl+Z 1회. 씬에서 사라진 항목은 `objExists`
  로 건너뛴다. 파괴적이라 UI 에 **확인 다이얼로그**(QMessageBox) 추가.
- **검증**: 변경 파일 `py_compile` 통과. 씬 키 삭제 동작은 Maya 실행 확인 필요. #A00110_animTool

> [!summary] A00180 abSymMesh — Mirror Deform 탭 'Selected vertices only' 추가(v02.03→02.04)
- **`Mirror Deform` 탭에 `Selected vertices only` 체크박스 추가**(Snap 탭과 동일 패턴). 체크 시 현재
  선택한 정점에만 미러 결과를 쓰고, 나머지는 anchor(Base / Deformed) 위치를 유지한다. 선택은 Base/Deformed
  어느 쪽이어도 됨(같은 토폴로지, 인덱스만 사용).
- **코어에 `indices` 인자 전파**: `snap_core.mirror_deformation` / `apply_mirrored_offsets`,
  `mesh_io.closest_surface_offsets` 가 `indices` 를 받아 **선택 정점만 계산**(무거운
  `getClosestPoint` 도 선택분만 실행). 출력은 전체 길이, 미선택 정점은 anchor 로 채운다.
- **검증**: indices 의미(선택만 미러·나머지 anchor 유지)를 순수 로직 수치 테스트로 확인, `py_compile` 통과.
  씬 편집 동작은 Maya 실행 확인 필요. #A00180_abSymMesh

> [!summary] A00180 abSymMesh — 탭 구조 + Snap to Sym / Mirror Deform 신규(v02.01→02.03)
- **UI 를 탭 구조로 재편**(`QTabWidget`): 기존 기능을 **`abSymMesh`** 탭으로, 신규 2탭 추가. 로그/푸터는
  탭 공용. 기존 `mesh_io`(벌크 정점 IO·undo 플러그인)·`undo_chunk` 인프라 재사용. 향후 기능도 탭으로 확장.
- **신규 `Snap to Sym` 탭** — 비대칭 메시를 대칭 레퍼런스에 **최근접 스냅**(Houdini nearpoint 이식,
  토폴로지 무관). 신규 **`app/core/snap_core.py`**(공간 격자 최근접 탐색, scipy 비의존, 순수 계산).
  - 모드: **Nearest Vertex**(기본, =VEX nearpoint) / **Closest Surface**(`MFnMesh.getClosestPoint`,
    `mesh_io.closest_surface_points`). Selected-only 옵션, Undo, 월드 공간.
  - **Make Symmetric Reference**(3방식): **Mirror one side**(정점 위치 반사 복사, 토폴로지 유지) /
    **Average both**(양쪽 평균) / **Mirror geometry (cut)**(반 잘라 미러, **토폴로지 재생성**;
    신규 **`app/core/mesh_ops.py`**: 시임 스냅→반대쪽 면 삭제→반사 복제+노멀 뒤집기→`polyUnite`/
    `polyMergeVertex`). Origin(World 0 / Pivot / BBox Center)·Source 면·Seam tol 옵션.
- **신규 `Mirror Deform` 탭** — **변형(deformed−base)을 미러 평면 건너편으로 반사**(Houdini Attribute
  Wrangle 미러 오프셋 이식). base/deformed 는 동일 토폴로지(오프셋은 인덱스로 읽음). **Apply onto =
  Base**(반사, VEX 동작) / **Deformed**(원변형 유지+반대쪽 반사=대칭화) 토글. 결과는 새 메시 출력 +
  Snap 탭 Reference 자동 연계.
  - **Match 방식 2종**: **Nearest Vertex**(`snap_core.mirror_deformation`, =VEX nearpoint) /
    **Closest Surface**(`mesh_io.closest_surface_offsets` — 표면 최근접점 + 면 정점 IDW 보간 →
    wrap/mesh-flow 식 부드러운 전이; 적용은 `snap_core.apply_mirrored_offsets`).
- **진행률 팝업**: 정점 수가 많은 무거운 작업(Snap / Make Symmetric Reference / Mirror Deformation)에
  게이지바 팝업(`QProgressDialog`, `_progress` 컨텍스트 매니저) + **Cancel**. 코어 루프에 `progress` 콜백을
  주기적으로 호출(약 200등분), 짧은 작업은 `setMinimumDuration(400)` 으로 팝업 생략. Cancel 시
  `_ProgressCancelled` 로 루프를 빠져나오며 **씬 편집(복제/setPoints) 전에 중단**해 잔여물이 남지 않게 했다.
- **견고성**: 격자 cell 을 '가장 긴 변' 기준으로 잡아 **평면/박판 메시에서 셸 탐색 폭발(무한 루프) 버그
  수정**, 탐색 반경을 점유 범위로 제한. **NaN/inf 정점 방어**(`_finite`/`count_invalid`로 건너뛰고 경고,
  원점이 NaN 이면 작업 중단).
- **검증**: 순수 로직(최근접 brute-force 대조·미러·대칭화·변형반사·NaN/엣지)을 별도 수치 테스트로 확인,
  변경/신규 파일 `py_compile` 통과. 씬 편집(geometry mirror·setPoints) 동작은 Maya 실행 확인 필요. #A00180_abSymMesh

> [!summary] A00090 ConnectionBuilder — 단일 창 + Mesh/Node 확장 + Create/Create All(v01.03→01.04)
- **단일 창 강제**: `main_window` 에 `WINDOW_OBJECT_NAME`+`setObjectName`, `launch.run` 이 새 창 생성 전
  `QApplication.topLevelWidgets()` 를 돌며 같은 objectName 창을 닫는다(A00145 패턴). 전역
  `window_instance` 가 리셋(리로드)된 뒤에도 이전 창을 확실히 닫아 **창 누적 방지**.
- **`Mesh for blendShape` → `Mesh / Node` 확장**: 입력 노드가 **mesh** 면 Rule `mapping` 이름으로
  blendShape target 복제(+deformer), **그 외(joint/transform/control)** 면 같은 이름의 double attr 생성.
  타입 판단·디스패치는 **신규 `app/core/target_builder.py`**(`TargetBuilder.is_mesh`/`build`)가 담당
  (BlendShapeManager·AttributeManager 는 그대로 재사용, core/ui 분리 유지).
- **버튼 분리**: 기존 `Create targets` → **`Create`**(콤보 선택 rule 1개) / **`Create All`**(`rules_v01`
  전체 rule). 다중 노드(콤마 구분) 지원. 생성 루프를 `undo_chunk` 로 묶음.
- **blendShape 누적(append)**: `BlendShapeManager.create_blendshape` 가 이미 blendShape 가 있으면 새
  target 만 다음 인덱스로 추가(`blendShape -edit -target`). "Create All" 로 여러 rule 의 target 이 한
  blendShape 에 모두 들어가도록 수정(기존엔 두 번째 rule 부터 통째로 skip 되던 문제 해결).
- **검증**: 변경 7개 파일 `py_compile` 통과. 노드 생성 동작은 Maya 실행 확인 필요. #A00090_ConnectionBuilder

> [!summary] A00145 RigConnect — Matrix Constraint 이식(Constraint 탭, v01.06→01.07)
- **레거시 `JUN_PY_MatrixCon_01_01.py`(행렬 컨스트레인트) 기능을 A00145 Constraint 탭에 이식**.
  `Matrix Constraint` 체크 시 일반 `*Constraint` 노드 대신 **`multMatrix`+`decomposeMatrix` 네트워크**로
  구속한다(컨스트레인트 노드 누적 없이 부모공간/오프셋 명시 제어).
- **신규 `app/core/matrix_constraint_manager.py`**(UI 비의존, `(made, errors)` 반환): `multMatrix`
  (offset·`target.worldMatrix`·`follower.parentInverseMatrix`) → `decomposeMatrix` → follower 채널 연결.
- **UI**: Constraint 탭에 `Matrix Constraint` 체크박스 + `Translate/Rotate/Scale` 채널 체크박스(기본 전부 on)
  추가. 체크 시 채널 토글 활성·constraint 종류 라디오 비활성(`_on_matrix_mode_toggled`). `Maintain Offset`
  은 일반 모드와 공유. `on_constrain` 에 분기 추가, `_run`(undo) 재사용.
- **원본 버그/개선 반영**: ① scale 연결이 translate 플래그로 잘못 게이팅되던 버그 수정, ② `maintain_offset`
  미사용 버그 수정(off 면 follower 가 target 에 스냅), ③ **joint 면 jointOrient 역행렬로 rotate 출력만 보정**
  (translate/scale 위치가 회전되지 않게 분리), ④ `parentInverseMatrix[0]` 사용으로 "부모 없으면 단위행렬
  그룹 생성" 분기 제거, ⑤ broadcast(target 1개→다수 follower) 지원, ⑥ 재실행 시 기존 입력 연결 해제·항목별
  예외 수집.
- **검증**: 변경 5개 파일 `py_compile` 통과. 노드 네트워크 실제 동작은 Maya 실행 확인 필요. #A00145_RigConnect

> [!summary] Framework 공통화 — 툴 전수 분석 후 저위험 공용 모듈 2종 승격
- **`JUN_All/tools` 33개 툴을 전수 분석**해 여러 툴에 복붙된 코드 패턴(undo 청크, 파일 탐색기
  Reveal, prefs 영속화, CollapsibleBox 등)을 찾고, 그중 **동작 변화가 없는 저위험 2종만** Framework
  로 승격(나머지는 호출부 API 변경이 커 다음 차수로 보류).
- **신규 `Framework/core/maya_undo.py`** — `undo_chunk()` 컨텍스트 매니저. `cmds.undoInfo(openChunk)/
  closeChunk` 보일러플레이트(여러 툴에 32곳 복붙)를 하나로 통일, 예외 시에도 `finally` 로 chunk 닫기
  보장. **15개 파일·28곳**을 `with undo_chunk():` 로 교체(`try/finally`→`with`, `try/except/finally`→
  `with` 안에 try/except 중첩, 동작 동일): A00110_animTool core 5(keyframe·copykey·offset_hold·pose·
  mirror), A00120 fkik_matcher, A00010_V02 hik_manager, A00200 arkit, A00150·A00160·A00170·A00180·
  A00190·A00145·A00060_V02. `finally` 가 `currentTime` 복원·constraint 정리까지 하는 **복잡 블록 4곳**
  (bake_manager·follow_match_manager·fkik_matcher 2)은 재들여쓰기 위험을 피해 의도적으로 보존(이미
  올바르게 chunk 를 닫음).
- **신규 `Framework/core/file_opener.py`** — `open_path()`(폴더 열기 / 파일 선택 reveal, win·mac·linux).
  A00240_PathTool 의 검증된 구현을 승격하고, A00210_FileManager(main_window·lineage_tab)·A00220_
  BackupTool 이 각자 복붙하던 `explorer /select,` 로직을 이 모듈 위임으로 교체(미사용 `sys`/`subprocess`
  import 정리). A00240 의 기존 `path_opener.py` 는 re-export 1줄로 축약해 호출부 무수정 유지.
- **검증**: 편집한 21개 파일 `py_compile` 통과, `open_path` 임포트·빈/없는 경로 예외 동작 확인.
  순감 105줄(190 추가/295 삭제). Maya 내부 undo 단일스텝 동작은 Maya 실행 확인 필요. #Framework

## 2026-06-22

> [!summary] A00250 SceneMemo — 씬 오브젝트 메모 툴 신규(v01.00)
- **신규 in-Maya PySide 툴**(A00110 기반, B형): 씬의 메시/커브/트랜스폼 등에 **사용자 메모**를
  남기고 씬을 닫았다 다시 열어도 보존, 한국어 입력·사후 편집 가능.
- **저장 방식**: 씬 내부 `JUN_memo_store`(network) 노드의 `junMemoData`(string/JSON)에 **노드 UUID
  키**로 저장 → `.ma/.mb` 안에 들어가 Save As/복사/리네임에도 유지. 노드는 `lockNode` 로 보호.
  `json.dumps(ensure_ascii=False)` 로 한국어 안전. core(`memo_store`/`memo_io`) ↔ ui 분리.
- **기능**: Add Selected / Remove / Save Memo / Search / Clean Orphans / Export·Import(마야 파일 옆
  `JUN_memo/<scene>_memo.json` 사이드카, 백업·공유용). 미저장 씬은 Export 불가.
- **다중 선택 일괄 메모**: 테이블 여러 행 선택 후 Save Memo 하면 선택한 모든 오브젝트에 같은 메모
  일괄 저장. **씬 선택은 행 우클릭 → Select in Scene 메뉴**로 제공(별도 버튼 없음). #A00250_SceneMemo

> [!summary] A00090 ConnectionBuilder — Source/Target 리스트화 + 1→n / n→n batch 연결(v01.02→01.03)
- **MetaHuman RBF 연결 UI 개편**: 단일 `QLineEdit` 입력을 **여러 노드 batch** 처리로 바꿨다.
  - **BlendShape 입력행 제거**(상단 `Mesh for blendShape`/Create targets·`BlendShapeManager` 는 유지).
  - **용어 정리**: *Base→Source*, *Driver→Target*(내부 식별자 `solver_node`/`driver_node` 의미는 유지).
  - **Source/Target 을 재사용 리스트 위젯**(`Framework/qt/MOD_tsl_qt_v01.JUN_mod_tsl_qt_v01`)으로 교체하고
    **좌·우로 나란히 배치**. `Is Solver` 는 Source 컬럼 상단, `Set Attr`/`Del Attr` 는 각 리스트에
    `add_button` 으로 부착(리스트 전체 노드 대상). 모든 버튼 높이 축소.
  - **Pair mode 체크박스**(`n->n (index pair)`): 해제=**1→n broadcast**(첫 Source→모든 Target),
    체크=**n→n index pair**(`Source[i]→Target[i]`, 개수 다르면 `[ERROR]` 후 무동작). Connect All /
    Connect / Disconnect / Validate 가 모두 이 모드를 따른다. n→n 도 선택 rule 1개의 mapping 을 전 쌍에 적용.
  - core(connection/attribute/blendshape/intermediate manager) 무수정 — UI 가 짝마다 단일 rule 로직을
    루프 호출하도록 재사용. 가이드 문서(신규 `A00090_ConnectionBuilder.md`)·plan·version 동기화. #A00090_ConnectionBuilder

> [!summary] A00210 FileManager — 노드 경로 팝업(v01.19) + 세팅 Profile(v01.20) + Log history 편집/삭제(v01.21)
- **Lineage 노드 우클릭 Reveal in File Explorer 동작 정리**(v01.18→01.19): 파일이 이 PC 에 있으면
  예전처럼 탐색기에서 폴더 열고 파일 선택(팝업 없음), **로컬에 없으면**(예: 다른 PC 에서 A00211 로 만든
  그래프) 그냥 실패하지 않고 그 노드 파일의 **경로를 선택·복사 가능한 팝업**으로 보여준다. 메뉴는 노드에
  key 가 있으면 활성(파일이 로컬에 없다는 이유로 회색 처리하지 않음). `node_path_info` 헬퍼 신설.
- **File Manager 세팅 Profile**(v01.19→01.20): Project Root·Store Repo·Scan Dir·Remote·Branch·Remote
  URL·Author·Recursive·Show Recorded Only 등 **사용자 입력 세팅 전체를 이름붙인 프로파일(JSON 1개)** 로
  저장·전환. 상단 **Profile** 그룹(콤보 + New/Rename/Delete), 전환 시 현재 값 **자동 저장** 후 새 프로파일
  로드 + Lineage/Path Structure 목록 새로고침, 창 종료 시 활성 프로파일 저장, 다음 실행 때 복원
  (`active.json`). 저장 위치 `~/.jun_filemanager/profiles/<name>.json`. 구 단일 `prefs.json` 은 첫 실행 시
  `Default` 로 1회 마이그레이션(원본 `.bak` 보존). `prefs.load()/save()` 는 활성 프로파일 대상으로 동작해
  하위호환 유지(A00211 무수정 연동). 가이드 문서·CHANGELOG·version 동기화. #A00210_FileManager
- **Log history 항목 편집/삭제**(v01.20→01.21): Log history 헤더에 **Edit 버튼** 추가 → `Edit Log
  History` 다이얼로그에서 항목별 **author/note 편집·개별 삭제**(timestamp 보존, 구조적 편집). 가이드
  문서·CHANGELOG·version 동기화. #A00210_FileManager

> [!summary] 신규 툴 A00211_RefLineage — 마야 씬 reference 관계 → A00210 Lineage JSON 내보내기(v01.00)
- **현재 Maya 씬의 reference 관계(중첩 포함)를 스캔해 A00210 Lineage 그래프로 내보내는 Maya 내 PySide
  툴 신설**. `cmds.referenceQuery` 로 씬→직속→중첩 reference 트리를 따라가 파일 1개=노드(절대경로 dedup,
  씬은 루트), **참조 대상→참조하는 파일** 방향의 reference 엣지(A00210 규약)로 기록한다. 포맷·설정 단일
  소스를 위해 A00210 의 `lineage`/`store`/`prefs` 모듈을 그대로 재사용 — JSON 포맷이 동일해 Lineage 탭에서
  바로 열린다(키는 project_root 상대, 루트 밖이면 빈 값). 미니 UI(Scan/Export) + 헤드리스
  `export_scene_references()`. Windows 타 드라이브 파일의 `relpath` ValueError 도 '루트 밖'으로 처리.
  가이드 문서(신규 `A00211_RefLineage.md`)·CHANGELOG 동기화. #A00211_RefLineage

> [!summary] A00220 BackupTool — 백업 성공 순간 공룡이 공중에서 360° 회전(v01.06) + Target Files 파일명 표시·Reveal(v01.07)
- **파일이 실제로 백업된 순간을 UI 로 또렷이 표시**(v01.05→01.06): 지금까지는 저장 순간 작은 점프(hop)
  한 번이라 놓치기 쉽고, 변경이 없어 실제로 복사되지 않아도 뛰던 문제가 있었다. `DinoWidget.spin()` 을
  신설해 **공룡이 공중에서 360° 한 바퀴 회전**하도록 하고, `_backup_targets` 에서 **한 개라도 백업에
  성공했을 때(`ok > 0`)만** 트리거(저장 상태 진입만으로는 안 돎). 회전은 스프라이트 중심 기준
  `translate/rotate`, 회전 중 모서리가 잘리지 않게 위젯 세로 여유를 대각선만큼 확보하고 주기 점프를 멈춘다.
  걷기(Active)·서있기(Deactive) 동작은 유지. PySide6 오프스크린으로 24프레임(0~360°) 잘림 없음 검증.
  CHANGELOG·version·가이드 문서 동기화. #A00220_BackupTool
- **Target Files 파일명만 표시 + 우클릭 Reveal**(v01.06→01.07): Target Files 목록을 전체 경로 대신
  **파일명(basename)만 표시**(전체 경로는 `Qt.UserRole`+툴팁에 보존, 백업/중복검사/prefs 는 전체 경로
  사용). 항목 **우클릭 → Reveal in File Explorer** 로 탐색기에서 파일 선택 상태로 열기(win `explorer
  /select,` / mac `open -R` / linux `xdg-open`). CHANGELOG·version 동기화. #A00220_BackupTool

> [!summary] A00210 Lineage — Reference 엣지 · 노드/엣지 색 지정 · 화살표 겹침 분리 · 엣지 종류 변환(v01.16→01.18)
- **A00210_FileManager Lineage 탭 기능 묶음**(v01.15→01.18):
  - **Reference(점선) 엣지**: 마야 파일 간 reference 관계를 계보(parents)와 별도로 표현. Connect Mode
    의 엣지 종류 드롭다운에서 `Reference (dashed)` 선택 후 참조 대상→참조하는 파일로 드래그. 레인/색/
    Auto Layout 에 영향 없고 자체 순환 검사·채운 삼각 화살촉. 노드별 `references` 로 저장.
  - **노드/엣지 색 수동 지정**: 러버밴드로 노드·엣지를 골라 `Set Color...` 로 한 번에 색 지정, `Reset
    Color` 로 기본색 복귀. 엣지 색은 그래프 JSON 의 `edge_colors`(`kind:src>dst`)로 저장(끝점 노드
    삭제 시 정리).
  - **겹치는 화살표 분리**: 같은 두 노드 사이의 계보+reference 화살표가 포개지던 것을 가로로 균등하게
    벌려 각 화살표·화살촉을 구분.
  - **엣지 종류 즉시 변환**: 화살표를 선택한 상태에서 엣지 종류 드롭다운을 바꾸면 선택된 화살표가
    Lineage↔Reference 로 즉시 변환(방향·색 유지, 모양 실선 빈 V↔점선 채운 삼각으로 갱신, 순환 거부).
  - 가이드 문서(A00210)·CHANGELOG·version 동기화. #A00210_FileManager

> [!summary] A00120 FKIK 구간 베이크 시 바깥 키 보존(v01.05)
- **A00120_FKIK 구간 베이크가 베이크 구간 밖의 기존 키를 모두 지우던 버그 수정**(v01.04→01.05):
  0~1000 키가 있을 때 500~600 만 베이크하면 그 밖의 키가 전부 사라졌다. 원인은 임시
  `parentConstraint` 가 걸리는 순간 Maya 가 `pairBlend` 를 끼워 기존 `animCurve` 를 플러그에서
  분리해, `bakeResults` 의 `preserveOutsideKeys=True` 가 바깥 키를 보지 못한 것. 컨스트레인트를
  걸기 **전에** `[start, end]` 밖 키를 값/탄젠트(타입·fixed 각도/가중치)로 스냅샷
  (`_snapshot_outside_keys`)하고 베이크·정리 후 복원(`_restore_outside_keys`)하도록 했다.
  `bake_constraint()` 도 재생 범위 기준 동일 가드 + `preserveOutsideKeys=True` 보강. 복원은
  `suspend_refresh()` 로 감싸 프레임마다 리드로우 안 함. 가이드 문서(신규 `A00120_FKIK.md`)·
  CHANGELOG·version 동기화. #A00120_FKIK

> [!summary] A00110 animTool · A00145 RigConnect — 리스트업 후 창/리스트가 작아지던 문제 수정(v01.17 / v01.04)
- **select 로 오브젝트를 tsl 에 채운 뒤 창 세로가 갑자기 작아지던 문제 수정**. (1) 공유 리스트 위젯
  `Framework/qt/MOD_tsl_qt_v01.py` 에 **최소 높이 바닥값 100px**(`DEFAULT_LIST_MIN_HEIGHT`, 명시값
  없는 리스트에 적용 — A00110 의 모든 리스트가 해당). (2) **A00110**(v01.16→01.17): `_fit_window` 가
  **탭 전환 시에는 grow_only**(늘리기만, 줄이지 않음)로 바뀌어 콘텐츠 짧은 탭을 눌러도 창이 축소되지
  않음(섹션 접기/펴기만 콘텐츠 높이로 축소). 공유 로그창 **maxHeight 160** 추가로 창 재확장 시 로그
  독식 방지. (3) **A00145**(v01.03→01.04): 창 **최소 크기 480×560** 보장(자동 리사이즈 없는 툴이라
  하한만으로 충분, 리스트들은 이미 `list_min_height` 명시). 가이드 문서(A00110)·WORKLOG 동기화.
  #A00110_animTool #A00145_RigConnect

> [!summary] A00145 RigConnect — Locators 자동생성 + parentConstraint Interp Type 고정(v01.04→01.06)
- **parentConstraint Interp Type 고정**(v01.05): constraint 의 `interpType` 을 **Shortest(2)** 로 강제 →
  다중 joint 가중 평균 시 짐벌 튐(회전 보간 폭주) 방지.
- **Locators 버튼 추가**(v01.06): follower 없이 **로케이터를 자동 생성**한 뒤 동일 스킨 웨이트 constraint
  를 적용. *average* = centroid 에 로케이터 1개 / *per-vertex* = 버텍스마다 1개. 생성 로케이터는
  `RigConnect_skinLoc_grp#` 로 그룹화하고 Followers 목록을 자동으로 채운다(신규
  `core/skin_constraint_manager.py`). 가이드 문서·version 동기화. #A00145_RigConnect

> [!summary] A00210 FileManager Lineage 탭 — 중간버튼 팬 범위 무제한화(v01.15)
- **A00210_FileManager Lineage 캔버스 중간버튼 팬이 막히던 문제 수정**(v01.14→01.15): 중간버튼 드래그
  팬은 스크롤바를 움직이는 방식이라 이동 범위가 `sceneRect`(콘텐츠 바운딩 + 여백 200px)에 갇혀, 노드
  영역 바깥 200px 에서 더 끌리지 않았다. (1) 초기 `sceneRect` 여백을 **한 뷰포트 크기 이상**(현재 줌
  배율로 환산, 최소 800)으로 넓히고, (2) `LineageView._pan_by` 신설 — 팬이 경계 600px 안으로 들어오면
  그 방향으로 `sceneRect` 를 계속 키워 노드 바깥으로도 자유롭게 이동(사실상 무한 팬). 다음 렌더에서
  콘텐츠 기준으로 다시 줄어 영구 부풀지 않음. 가이드 문서·CHANGELOG·version 동기화. #A00210_FileManager

## 2026-06-19

> [!summary] 신규 툴 A00240 PathTool — 경로 런처(카테고리·우클릭 편집·순서 변경·집/회사 프로파일) + Tree 탭(경로 트리뷰·깊이/파일/확장자 필터·Expand·우클릭 Reveal·폴더/파일 아이콘, v01.02)·버튼 Change Category(v01.03, standalone PySide6) + A00145 RigConnect Match 탭 신설(MEL Match Tool V05.04 이식·리팩토링, v01.03)·Constrain 탭에 Skin Weight to Constraint 추가(v01.02, 접이식) + A00220 BackupTool Settings 접이식화·창 슬림(v01.03)·스핀박스 화살표 PNG 복구·백업 log.txt(v01.02)·상태 표시를 Chrome Dino 애니메이션으로(v01.04)·Auto Backup 저장 즉시 백업(v01.05) + A00110 animTool Follow 탭 강화(Maintain Offset · 1<-n · Get Current) + A00110/A00120 뷰포트 프리즈(refresh suspend 누수) 수정 & Force Refresh 버튼 + A00210 FileManager Lineage 노드 로그 동기화(v01.08)·노드/연결 삭제 & 다중선택(v01.09)·러버밴드 intersect 선택(v01.10)·File Manager Show Recorded Only 필터(v01.11)·Load Image 시작 경로 thumbs 폴더(v01.12)·Settings Branch 편집형 드롭다운(v01.13)·검색/확장자/Recorded 필터 & 우클릭 Show in File Explorer & Log history Expand(v01.14) + Framework dark 테마 Win10 트리 행 가독성
- **A00230_StartupTool 부팅 시 툴 자동 실행 확장**: 기존 "부팅 시 폴더 팝업" 런처를 **폴더 + standalone
  툴 자동 실행**으로 확장. 신규 부팅 코디네이터 `startup.py` 가 `config/startup.json`(기존 `folders.json` 대체,
  `folders` + 신규 `tools` 배열)을 읽어 폴더를 탐색기로 팝업한 뒤 각 툴의 `launch.py` 를 `pythonw` **분리
  프로세스**로 실행(프로세스 분리로 `tools.<tool>.app.*` 패키지 충돌 없음). 기본 등록: A00210 FileManager ·
  A00220 BackupTool · A00240 PathTool. **새 툴 추가는 `tools` 에 `{ "tool": "A002NN_XXX", "enabled": true }`
  한 줄**(표준 위치 밖은 `launch` 경로 override) — 재설치 없이 다음 부팅에 반영. `install.py` 런처(.vbs)가
  `startup.py` 를 가리키도록 변경(기존 설치자는 `install.py` 1회 재실행). `open_folders.py` 는 폴더 로직 모듈로
  재사용·단독 실행 유지. README 갱신. #A00230_StartupTool
- **A00220_BackupTool Auto Backup = 저장 즉시 백업**(v01.04→01.05): Auto Backup 모드가 *주기 타이머*가
  아니라 *저장 시점*에 백업하도록 변경. 대상 파일을 `QFileSystemWatcher` 로 실시간 감시하다가 디스크에서
  바뀌는 즉시(=저장 순간) 그 파일만 백업. 연속 저장·임시파일 교체식 저장을 다루도록 변경을 ~300ms 디바운스
  후 처리하고 감시 경로를 재등록. 기존 `Interval` 주기 타이머는 감시가 놓친 변경을 잡는 **fallback** 으로 유지
  (mtime 비교로 중복 백업 방지). 실행 중 Auto Backup 토글 시 감시 즉시 시작/정지. 복사 루프를 `_backup_targets`
  로 분리해 주기 사이클·저장 감지가 공용. 안내 문서 동기화. #A00220_BackupTool
- **A00220_BackupTool 상태 표시 = Chrome Dino**(v01.03→01.04): Control 의 상태 글자
  (`Deactive`/`Active...`/`Saving`)를 **Chrome-Dino(T-Rex) 픽셀 애니메이션**으로 교체. 신규
  `app/ui/dino_widget.py` 가 코드 내장 비트맵을 **QPainter 로 그림**(이미지 에셋 0개·테마 무관·exe 번들 불필요).
  Active=제자리 달리기(다리 2프레임 교차 + 바닥 점선 스크롤) + 약 2.6초마다 **포물선 점프**, Deactive=가만히
  서 있음, Saving=`hop()` 으로 1회 추가 점프 강조. 자체 33fps QTimer 구동, 기존 점(...) 타이머(`_dot_timer`)·
  관련 메서드 제거. offscreen PNG 렌더로 4포즈(서기/달리기 A·B/점프) 모양 확인 후 통합. #A00220_BackupTool
- **A00240_PathTool 신규**(v01.00): 자주 쓰는 폴더 경로를 버튼으로 만들어 **클릭 시 탐색기로 여는** standalone
  PySide6 런처. **Create** 그룹의 `Category`(카테고리=`QGroupBox` 생성)·`Path` 버튼 — Path 는 **카테고리·버튼
  이름·경로(Browse)를 한 다이얼로그**(`AddPathDialog`)에서 한 번에 입력. 버튼 클릭=경로 열기(폴더는 그 폴더,
  파일이면 폴더+선택; Win `explorer /select,` 우선·mac/linux 폴백, `core/path_opener.py`). **수정/삭제는
  우클릭 메뉴**(카테고리: Rename/Delete, 버튼: Rename/Change Path/Delete) — 항목이 늘어도 화면 유지. 집/회사
  처럼 **JSON 별로 나뉜 Profile**(상단 콤보 + New/Rename/Delete, 최소 1개 유지, 마지막 활성 기억) 추가 —
  프로파일 1개=JSON 1개로 완전 분리. 저장은 `%USERPROFILE%` 가 아니라 **툴 내부 `data/`**(`profiles/<name>.json`
  + `active.json`), **onefile exe 면 exe 옆 `data/`** 로 분기(임시폴더 휘발 회피), `data/` 는 `.gitignore`.
  구버전 `~/.jun_pathtool/shortcuts.json` 은 첫 실행 시 `Default` 로 자동 마이그레이션. 탭은 `QTabWidget`
  (현재 ShortCut 1개, 확장 대비). core(prefs/path_opener)·ui 분리, 툴 고유 import 경로. #A00240_PathTool
- **A00240_PathTool 버튼 Change Category(카테고리 이동)**(v01.02→01.03): ShortCut 탭에서 **Path 버튼
  우클릭 메뉴에 Change Category** 추가 — 현재 카테고리를 뺀 목록(`QInputDialog.getItem`)에서 대상을 골라
  버튼을 그쪽 끝으로 이동(`_change_button_category`). 대상에 같은 이름 버튼이 있으면 차단, 다른 카테고리가
  없으면 안내. 버튼 데이터(경로 포함) 그대로 옮기고 프로파일 JSON 저장·재렌더. 안내 문서 동기화.
  #A00240_PathTool
- **A00240_PathTool Tree 탭 신설**(v01.01→01.02): 입력 경로를 **트리뷰**(QTreeWidget)로 보여주는 새 탭
  (A00210 Path Structure 의 트리 표시 취지). 옵션: (1) **Depth** 스핀박스(0=All, 변경 시 자동 재빌드),
  (2) **Show files** 체크박스(끄면 폴더만, File Types 자동 비활성), (3) **File Types** 체크 드롭다운(발견 확장자
  중 표시할 것만, A00210 File Manager 와 동일 `_CheckableMenu`), (4) **Expand** 버튼(800×620 큰 창),
  (5) **우클릭 → Reveal in File Explorer**(`path_opener.open_path` 재사용, 메인/Expand 트리 공용). 폴더/파일은
  **QStyle 표준 아이콘**으로 구분. Build 시 모든 파일을 캐시하고 Show files/File Types 는 재스캔 없이 즉시 필터,
  Depth/Path 만 재스캔. 로직은 새 `core/tree_scanner.py`(UI 비의존, `build_tree`/`collect_extensions`)로 분리.
  안내 문서 동기화. #A00240_PathTool
- **A00240_PathTool 카테고리 순서 변경**(v01.00→01.01): 카테고리가 생성 순서로만 쌓이고 순서를 못 바꾸던
  것을, 카테고리 **우클릭 메뉴에 Move Up / Move Down**(양 끝단 비활성) 추가로 자유롭게 재정렬. 화면 순서=
  `data["categories"]` 리스트 순서라 인접 항목과 swap 후 저장·재렌더(`_move_category`), 바뀐 순서는 프로파일
  JSON 에 저장. #A00240_PathTool
- **A00210_FileManager File Manager 탭 검색·필터·탐색기 연동 강화**(v01.13→01.14): (1) **Scan 이 전
  확장자 리스트업** — `.mb`/`.ma` 만이 아니라 모든 포맷(`scanner.scan(extensions=None)`). (2) **File Types
  체크 드롭다운** — 스캔에서 발견된 확장자 중 표시할 것만 체크(All 포함). 여러 개 연속 토글해도 안 닫히는
  `_CheckableMenu`(mouseReleaseEvent 에서 `action.trigger()` 후 닫기 차단), 버튼 라벨에 선택 요약. (3) **Name
  filter** — 목록 위 입력란+`Filter`(또는 Enter)로 제목에 키워드 포함 파일만(대소문자 무시), 빈 값=전체. 적용
  키워드를 입력란과 분리(`_name_filter`)해 다른 필터 토글 시에도 일관. (4) 세 필터(이름·확장자·Recorded)를
  `_apply_file_filter` 에서 **재스캔 없이 중첩** 적용. (5) **우클릭 → Show in File Explorer** — FileTable 에
  컨텍스트 메뉴+`reveal_requested` 시그널, `abs_path` 를 `explorer /select,`(win)/`open -R`/`xdg-open` 으로
  선택 표시(Lineage 탭 reveal 방식 재사용). (6) **Log history Expand** — 상세 패널이 좁아 긴 로그가 안 보이는
  문제로, 라벨 옆 `Expand` 버튼이 전체 폭 리사이즈 가능한 읽기전용 창에 같은 로그를 띄움(스냅샷). 안내 문서
  동기화. #A00210_FileManager
- **A00210_FileManager Settings Branch 편집형 드롭다운**(v01.12→01.13): Settings 의 **Branch** 입력을
  `QLineEdit` → **editable `QComboBox`**(`_BranchComboBox`)로 변경 — 드롭다운을 펼칠 때마다 Store Repo 의
  **실제 git 브랜치(로컬 + 원격추적, 중복 제거)** 를 채워 올바른 이름을 고르게 한다(목록에 없는 이름은 직접
  타이핑도 가능, 첫 clone/fetch 전 대비). `main`/`master` 혼동 같은 브랜치명 불일치로 나던
  `src refspec ... does not match any` push 오류를 줄임. 네트워크 fetch 없이 로컬 ref 만 읽는 새
  `GitSync.list_branches()`(`git branch` + `git branch -r --format`, `origin/HEAD` 류 제외) 추가. 안내
  문서 동기화. #A00210_FileManager
- **A00210_FileManager Load Image 시작 경로 = Store Repo/thumbs**(v01.11→01.12): File Manager 탭의
  **`Load Image...`** 파일 다이얼로그가 홈(`~`) 대신 **Store Repo 의 `thumbs` 폴더**에서 열리도록 변경 —
  거기 이미 저장된 썸네일을 **여러 파일에 재사용**하기 쉽게. Store Repo 미설정·thumbs 폴더 부재 시 홈으로
  폴백(`_thumbs_start_dir`). #A00210_FileManager
- **A00210_FileManager File Manager 탭 Show Recorded Only 필터**(v01.10→01.11): Scan 옆 **Recursive**
  옆에 **`Show Recorded Only`** 체크박스 추가 — 켜면 **record(Save Record)가 있는 파일만** 목록에 남긴다.
  Recursive 스캔으로 수많은 파일이 잡힐 때 **이 툴로 관리(기록) 중인 파일만** 추리는 용도. 마지막 scan 결과를
  원본으로 캐시(`_scanned_entries`)해 두고 `_apply_file_filter`(`has_record` 필터)로 **재스캔 없이 토글 즉시**
  반영, 상태는 prefs(`show_recorded_only`)에 저장. 용어는 툴 기존 어휘(Save Record·Record 컬럼·
  `records/<key>.json`)와 맞춰 **Recorded** 채택. 안내 문서 동기화. #A00210_FileManager
- **A00145_RigConnect Match 탭 신설**(v01.02→01.03): MEL `Match Tool V05.04` 를 **첫 번째 탭**으로
  이식·리팩토링. `Targets`/`Followers` TSL 로 follower 를 target 의 **위치/회전에 매칭**. 핵심 개선:
  (1) **rotateOrder 가 달라도 안전** — MEL 이 follower 의 rotateOrder 를 타깃 것으로 바꿨다 되돌리던
  방식(+ mesh/cluster 분기에서 복원이 누락되던 버그)을 버리고 `cmds.matchTransform`(임시 transform 경유)
  으로 통일. (2) **버텍스 타겟 노말 매칭** — 타겟이 `mesh.vtx[i]` 면 정점 월드 위치로 이동 + follower 의
  **+Y 축을 정점 노말에 정렬**(`maya.api.OpenMaya` `MFnMesh.getVertexNormal`, `_basis_from_normal`).
  (3) **버텍스 개별 리스트업** — 공용 TSL 위젯의 `cmds.ls(fl=True)` 로 `mesh.vtx[0:13]` 가 하나로 묶이지
  않고 정점별 항목으로 들어감. (4) **Create(Locators/Sphere/Cube)** 버튼은 "생성→목록→수동 Match" 가
  아니라 **타겟 수만큼 생성 후 즉시 매칭**하고 Followers 목록을 채움(곡선 데이터는 MEL 그대로 이식).
  (5) mesh→월드 centroid(getPoints 평균)·cluster→월드 rotatePivot 로 위치 매칭(MEL 의 local-space
  rotatePivot 질의 버그 수정), `Swap` 유지, **Blend Shape 버튼 제거**. 로직은 새
  `core/match_manager.py`(UI 비의존)로 분리. 안내 문서(`docs/A00145_RigConnect.md`) 동기화.
  #A00145_RigConnect
- **A00145_RigConnect Skin Weight to Constraint 추가**(v01.01→01.02): Constrain 탭을 **접이식 2섹션**
  (`CollapsibleBox`)으로 — 기존 **`Constraint`(펼침)** + 신규 **`Skin Weight to Constraint`(접힘)**. 선택한
  버텍스의 **스킨 웨이트 비율**대로 영향 joint 들을 constraint weight 로 follower 에 `parentConstraint`
  (예: `hip:0.2/spine_01:0.5/spine_02:0.3` → 그 비율의 weightAliasList setAttr). `Vertices`/`Followers`
  TSL 2개, `Max Influence`(상위 N joint 만 남기고 합=1 정규화, 0=무제한), `Maintain Offset`, **`Per-vertex`
  체크박스** — 해제 시 모든 버텍스 웨이트 **평균**을 전 follower 에 동일 적용, 체크 시 `vertices[i]→
  followers[i]` **1:1**(개수 일치). 로직은 새 `core/skin_constraint_manager.py`(skinCluster 탐색 →
  `skinPercent` 웨이트 조회 → 정규화 → weighted parentConstraint)로 분리. #A00145_RigConnect
- **A00220_BackupTool Settings 접이식화 + 창 슬림 + 스핀박스 화살표 복구**(v01.01→01.03): **Settings 를
  접이식 섹션**(공용 `JUN_mod_collapsible_qt`, A00110 과 동일)으로 바꾸되, 접을 때 **위쪽 파일 목록
  (textscrollList)이 늘어나던 문제**를 수정 — 토글 시 창을 sizeHint 로 재맞추면 늘어난 공간을 expanding
  목록이 흡수하므로, 대신 **본문 높이(`body_height()`)만큼만 창을 줄이거나 늘려** 목록 크기를 고정.
  `resizeEvent` 로 접힘 상태 높이를 추적해 사용자가 직접 창을 키우면 목록은 그에 맞춰 변함. 창을 세로형
  (~350px)으로 슬림화(Save Mode 라디오·분/초를 세로 적층, 스핀박스 폭 축소, 긴 라벨·버튼 단축). **분/초
  스핀박스 화살표가 직사각형으로 보이던 문제**는 테마 qss 가 `::up-arrow/::down-arrow` 를 CSS
  border-삼각형으로 그려 일부 Qt 에서 안 그려진 게 원인 — **9×9 PNG 화살표 아이콘**(`sb_up/down_dark/
  light.png`) `image:` 로 교체(다크=밝은 화살표/라이트=어두운 화살표), light 테마엔 누락됐던 `::up-button/
  ::down-button` 서브컨트롤 정의 추가, 12개 `*.qss` 일괄. `theme_manager` 는 `@STYLES@` 토큰을 qss 폴더
  절대경로로 치환(`_read_qss`)해 실행 위치와 무관하게 아이콘 경로 해석. 백업 1회마다 **`log.txt`** 에
  시각+원본→백업본 한 줄 누적(v01.02). (Max Versions 는 Version Up 모드 전용이라 Overwrite 모드에서
  비활성 — 의도된 동작.) #A00220_BackupTool #Framework
- **A00210_FileManager Lineage 러버밴드 intersect 선택**(v01.09→01.10): 빈 캔버스 드래그 다중선택을
  `ContainsItemShape`(사각형에 **완전히** 든 것만) → **`IntersectsItemShape`**(사각형에 **일부라도 걸친**
  노드·엣지 선택)로 변경 — 큰 노드/긴 화살표도 전체를 감싸지 않고 살짝 걸치면 잡힌다. #A00210_FileManager
- **A00210_FileManager Lineage 노드/연결 삭제 + 다중선택**(v01.09): Lineage 탭에서 **연결선(엣지)도
  클릭 선택**(얇은 곡선용 hit 영역 확대 + 선택 시 흰색·굵게 강조)해 **Delete/Backspace** 로 선택(노드·연결
  혼합)을 **확인 팝업 없이** 삭제 — 연결 삭제는 자식의 해당 부모 링크만 제거, 노드 삭제는 고아 참조까지 정리.
  **빈 캔버스 드래그 = 러버밴드 다중선택**(`ContainsItemShape`), Connect Mode 중엔 러버밴드 off(선 긋기
  집중)·해제 시 복원. **Delete Node** 버튼도 선택 노드를 **일괄(팝업 없이)** 삭제로 변경. #A00210_FileManager
- **A00210_FileManager Lineage 노드 로그 동기화**(v01.08): Lineage 탭 **Node** 패널에 **Log history
  (from record)** 읽기 전용 영역 추가 — File Manager 탭의 Save Record 가 쓰는 `records/<key>.json` 을
  `store.load(node.key)` 로 그대로 읽어 같은 작업 기록을 동일 포맷(`[timestamp] author` + note)으로 표시.
  노드 선택 시·`showEvent`(탭 복귀) 마다 디스크에서 다시 읽어 **File Manager 탭과 동기화**(재클릭 불필요).
  record 매핑 노드에만 표시(planned·루트 밖은 안내문). per-item 회색 foreground 보존 위해 `::item` color 는
  덮지 않음. #A00210_FileManager
- **Framework/styles (dark 테마 트리 행 가독성)**: Windows 10 에서 파일 목록(`QTreeWidget`,
  `alternatingRowColors`)의 **교대 행 배경이 거의 흰색**으로 떠 밝은 글자가 안 보이던 문제 수정. qss 에
  교대행/행 색이 없어 OS 네이티브 팔레트(Win10)가 밝게 칠한 게 원인. `QTreeView/QTreeWidget` 에
  `background #2b2b2b` + **`alternate-background-color #33363c`** + 텍스트/선택(테마 accent)·hover 를
  **명시**해 OS 무관하게 **Win11 처럼** 보이도록 했다. dark.qss + 6개 `*_dark.qss`(blue/brown/coral/green/
  purple/yellow) 일괄 적용(라이트 테마 제외). 이전 탭바·헤더 가독성 수정의 후속(트리 행 누락분). 공용
  Framework 라 dark 테마 전 Qt 툴에 반영. #Framework
- **A00110_animTool / A00120_FKIK 뷰포트 프리즈 수정**(A00110 v01.15→01.16, A00120 v01.03→01.04):
  베이크 시 쓰는 `cmds.refresh(suspend=True)` 는 **씬 전역 토글**이라 복원이 어떤 예외에도 실행돼야
  하는데, A00120 `fkik_matcher.bake()` 의 `finally` 가 임시 컨스트레인트 `cmds.delete()` 를
  `suspend=False` **보다 먼저** 실행 → delete 실패 시 복원이 건너뛰어져 **세션 전체가 프리즈**
  (Graph Editor 커브 편집이 프레임 이동 전까지 반영 안 됨)되는 버그. 전역 상태라 한 번 누수되면 A00110
  도 멈춰 보였다. 공용 컨텍스트 매니저 `Framework/core/maya_refresh.py` 의 **`suspend_refresh()`**
  (복원을 항상 먼저/무조건 보장)로 A00110(`bake_manager`, `follow_match_manager`)·A00120
  (`fkik_matcher`)의 suspend 사용처를 전부 통일하고, `bake_constraint()` 의 임시 컨스트레인트 삭제도
  `finally` 로 이동. A00110·A00120 UI 에 **Force Refresh (Unfreeze Viewport)** 버튼
  (`force_refresh()`) 추가 — 멈춘 세션을 즉시 복구. #A00110_animTool #A00120_FKIK
- **A00110_animTool Follow 탭**(v01.14→01.15): (1) **Maintain Offset** 체크박스 — 타겟↔follower
  의 거리·회전을 유지한 채 추종(`parentConstraint maintainOffset=True` 와 동등)하되, **컨스트레인트
  노드 없이 순수 행렬 연산**으로 구현해 사이클·평가순서 오류를 원천 차단. **Start(구간 시작) 프레임**에서
  페어마다 한 번 `offset = worldMatrix(flw) · worldInverseMatrix(tgt)` 를 측정하고 매 프레임
  `local = offset · worldMatrix(tgt) · parentInverseMatrix(flw)` 로 분해(레거시
  `JUN_PY_MatrixCon_01_01` 의 offsetMat 로직과 동일). 끄면 기존처럼 offset 0(정확히 일치).
  (2) **1<-n** 체크박스 — 켜면 타겟 1개를 모든 follower 가 추종(타겟이 1개가 아니면 경고 후 중단),
  끄면 기존 **n<-n**(인덱스 1:1). (3) **Get Current** 버튼 — Start/End 옆에 각각 두어 현재 Maya
  프레임(`currentTime`)으로 입력란 갱신. 로그에 `mode`(1<-n/n<-n)·`offset`(offset/no-offset) 표기.
  `match_follow(..., maintain_offset, one_to_many)` 로 확장, `_offset_matrix()` 신설,
  `_matched_state(..., offset)` 일반화. 안내 문서(`docs/A00110_animTool.md`) 동기화. #A00110_animTool

---

## 2026-06-18

> [!summary] 신규 툴 A00230 StartupTool — 부팅 시 지정 폴더 자동 팝업(JSON 관리) + A00220 BackupTool — 주기적 자동 백업(standalone PySide) + A00110 animTool Follow 탭(target 추종 베이크) & Offset/Hold 신설→Key Edit 접이식 섹션 재구성 + A00210 FileManager Lineage 탭(파일 브랜치/병합 그래프) & Path Structure 선택 기록(체크한 최상위 폴더만)
- **A00230_StartupTool**: Windows 부팅(로그인) 시 자주 쓰는 작업 폴더들을 **탐색기 창으로 자동 팝업**하는
  순수 Python 유틸리티 신규. 열 폴더는 `config/folders.json` 으로 관리·확장(`path`/`enabled`,
  `open_missing`). 경로는 **환경변수(`%USERPROFILE%` 등)·`~` 확장**을 지원해 **PC 가 바뀌어도 동일**하게
  동작하고, 존재하지 않는 경로는 조용히 skip + 중복 경로 dedupe. `install.py` 가 Startup 폴더에 고유명
  런처(`A00230_StartupTool.vbs`)를 1회 생성 — 로그인 시 **pythonw 로 콘솔창 없이** `open_folders.py`
  실행(런처엔 그 PC 의 절대경로가 박힘). `uninstall.py` 로 제거. JSON 로더는 **전체 줄 `//` 주석**을
  허용해 항목을 삭제 없이 토글 가능. Framework·PathManager 비의존(표준 라이브러리만). #A00230_StartupTool
- **A00210_FileManager**: **Lineage 탭 신설**(v01.02) — 여러 리비전 폴더에 흩어진 파일들
  (.mb/.ma 뿐 아니라 .fbx/.obj 등 **포맷 무관**)의 **브랜치/병합 관계(DAG)** 를 직접 기록하고
  `git log --graph` 스타일 **색상 레인 트리**로 본다.
  **인터랙티브 캔버스**(`QGraphicsView`): 노드 드래그 이동 + **Connect Mode** 로 노드→노드 선 긋기로
  부모 연결(자기연결·중복·**순환 자동 거부**). **레인 색상은 DAG 토폴로지에서 자동 계산**(`compute_lanes`,
  git-graph 컬럼 배정 — 브랜치=다른 색, 병합=레인 수렴), **Auto Layout**(컬럼=레인·행=위상순서, 이후
  드래그 위치 저장). **Planned**("제작 예정") placeholder 노드(점선·반투명). 노드 추가는 폴더
  **스캔(모든 포맷·확장자 필터)**·단일 **Add File**·**Add Planned** 3가지 — 루트 안이면
  project-relative key 로 기존 record/썸네일 자동 링크. 에셋별 이름 그래프 `<store_dir>/lineage/<name>.json`
  저장·기존 Push/Pull 로 git 동기화. core(`lineage.py`, Qt 비의존)/ui(`lineage_tab.py`) 분리,
  `path_structure` 패턴 미러. #A00210_FileManager
- **A00210_FileManager Lineage 보강**(v01.03): (1) **버전업/브랜치 수동 지정** — 노드별
  `relation`(`""`auto/`version`/`branch`) 추가. **Node** 패널 `Relation to parent` 콤보로 같은 부모의
  어느 자식을 **Version-up(부모와 같은 색=메인 라인 상속)** 으로, 어느 자식을 **Branch(강제로 새 레인=다른
  색)** 로 볼지 추가 순서와 무관하게 선택. `compute_lanes` 트렁크 선택을 `version` 최우선·`branch` 제외로
  바꾸되 미지정은 기존 기본(첫 자식) 유지(하위호환), 트렁크 레인을 먼저 예약해 다른 자식이 가로채던 케이스도
  정리. 색은 항상 관계에서 파생(의미↔색 불일치 방지), JSON `relation` 키로 저장·Push 동기화. (2) **캔버스
  탐색** — `LineageView(QGraphicsView)` 서브클래스로 **휠 줌**(`AnchorUnderMouse`, 0.15x~4.0x, 현재
  배율은 `transform().m11()`로 읽어 `fitInView` 후에도 정확)과 **중간 버튼 드래그 팬** 추가(좌클릭·노드
  드래그·Connect Mode 와 비충돌, PySide6/2 좌표 모두 대응). #A00210_FileManager
- **A00210_FileManager Lineage 노드 우클릭 메뉴**(v01.04): `NodeItem.contextMenuEvent` 로 노드 우클릭
  시 **Reveal in File Explorer** 제공 — `key`(project-relative)를 `store.project_root`와 합쳐 절대경로
  복원 후 탐색기로 폴더를 열고 **파일 선택**(Windows `explorer /select,`, macOS `open -R`/Linux
  `xdg-open` 폴백). 경로 해석 가능할 때만 활성(키 있음+루트 설정+파일 존재), planned·루트 밖·사라진 파일은
  비활성+안내. 이후 우클릭 액션을 계속 확장할 수 있는 구조. #A00210_FileManager
- **A00210_FileManager 썸네일 캡쳐 오버레이 검정화면 수정**(v01.05): Capture Region 시 화면이 전부
  검게 덮여 캡쳐 범위가 안 보이던 문제 해결. 원인은 오버레이 위젯에 `WA_TranslucentBackground` 가 없어
  반투명 dim 이 불투명(검정) 배경 위에 칠해진 것. (1) 투명 배경 속성 활성 → 실제 화면이 비쳐 보임,
  (2) 풀스크린 '상태'(`WindowFullScreen`) 제거하고 **가상 데스크탑 geometry** 로 전체 모니터를 덮음
  (풀스크린+반투명이 단일모니터 스냅/합성 깨짐을 유발 — **Windows 10/11 공통** 동작 위해), (3) 선택영역
  표시를 `CompositionMode_Clear`(드라이버 편차) 대신 **선택영역 제외 둘레 4개 영역만 dim** 으로 변경해
  선택영역이 확실히 투명. 결과적으로 Win+Shift+S 처럼 전체는 살짝 어둡고 드래그 영역만 또렷. #A00210_FileManager
- **A00210_FileManager 배포 사용자 데이터 리포 원클릭 동기화**(v01.06): 릴리즈본을 git 으로 받은 사용자가
  데이터(records/thumbs/lineage/path_structures)를 동기화 못 하던 문제 해결. 근본원인 3가지 — (1) `on_pull/
  on_push` 가 읽던 `remote_url` 이 prefs/UI 어디에도 없어 항상 빈 값 → `ensure_repo` 가 clone 못 하고 로컬
  init 만 함, (2) 기본 브랜치 `main` vs 데이터 리포 `master` 불일치, (3) 배포 PC 에 clone 할 기본 store_dir
  없음. 해결: **중앙 데이터 리포 URL/브랜치/기본 clone 경로(`~/.jun_filemanager/JUN_FileManager_data`)를 툴에
  번들**(`app/config/data_repo.py`, release_builder 가 `app/` 통째 복사하므로 자동 포함). prefs 기본값을 번들에서
  채우고 구버전 prefs 는 load 시 브랜치 마이그레이션(main→master), UI 에 **Remote URL** 필드 추가, **Pull
  한 번**에 repo 없으면 기본 경로로 자동 clone→pull. clone 실패 시 **로컬 init 폴백 제거**(인증/권한 오류
  표면화, 끊긴 빈 repo 방지). core(prefs/git_sync)·config(data_repo)·ui(main_window) 분리 유지. #A00210_FileManager
- **A00210_FileManager Path Structure 선택 기록**(v01.07): Path Structure 탭에서 베이스 폴더의 **모든**
  하위 경로를 기록하던 것을, **선택한 최상위 폴더만** 기록하도록 변경. **"Folders to record" 체크리스트**
  (`QListWidget`)에 최상위 하위 폴더를 체크박스와 함께 리스트업하고(Base 변경·Browse·**Scan** 시 채움,
  재스캔 시 기존 체크 이름 기준 보존), **"All" 체크박스**로 전체 선택/해제(전체 기록). **Capture** 는 체크된
  최상위 폴더만 모으고(폴더가 있는데 미체크면 경고), **Recursive** 면 그 하위 트리까지 포함. core 는
  `list_top_level()` 추가 + `_collect_folders()`/`capture()` 에 `include_top` 필터(None=전체, 하위호환).
  로직 `app/core/path_structure.py`, UI `app/ui/path_structure_tab.py`. #A00210_FileManager
- **A00220_BackupTool**: 컴퓨터 비정상 종료 대비 **주기적 자동 백업** standalone PySide6 앱 신규.
  대상 **파일 목록**을 분·초 주기로 각 원본 폴더의 `backup` 하위 폴더에 복사(`{base}_{suffix}{ext}`,
  예 `scene_BU.mb`). 폴더명·접미사(BU) UI 지정, **Overwrite(기본)** / **Version Up**(`_NN`,
  최근 N개만 유지·롤오버) 모드 선택. 상태 표시 `Stat : Deactive` / `Active...`(점 애니메이션) /
  `Saving`. **다음 저장까지 남은 시간 카운트다운**(`Next save in MM:SS`, 1초 갱신, v01.01) 추가.
  설정은 로컬 prefs(`~/.jun_backuptool/prefs.json`)에 영속. core(Qt 비의존)/ui 분리,
  A00210 standalone 구조 준수. #A00220_BackupTool
- **A00110_animTool**: **Follow 탭 신설**(v01.11) — 좌(Target)/우(Follower) 리스트로, 각 follower 가
  같은 인덱스 target 의 **월드 위치·회전(·스케일)과 동일**해지도록 구간 키를 베이크(컨스트레인트 없이
  `parentConstraint(maintainOffset=False)` 와 동등). **rotateOrder 무관** — target `worldMatrix` 를
  follower `parentInverseMatrix` 로 로컬화한 뒤 **follower rotateOrder 로 재분해**(Mirror Key 경로
  재사용). **blend(0~1)** 로 원본↔매치 혼합(위치/스케일 lerp·회전 쿼터니언 slerp)을 **키 값에
  베이크**(레이어 weight=1 유지), 선택된 애니 레이어(override `V=F` / additive `V=F−B`)에 기록.
  로직 `app/core/follow_match_manager.py`, UI 는 재사용 위젯 `JUN_mod_tsl_qt_v01` 2개. 더불어
  선택 레이어 판별을 `cmds.ls(type=animLayer)` 나열 후 레이어별 `selected` 검사로 구현(animLayer 에
  선택 레이어 목록 전역 쿼리가 없음). #A00110_animTool
- **A00110_animTool**: **Offset & Hold 기능 신설 → Key Edit 탭 접이식 재구성**(v01.12→01.14).
  리스트업한 컨트롤러의 키를 **포즈 유지(hold) + 보간(offset)** 구조로 재배치 — 오브젝트 커브들의
  **키 시점 합집합**을 포즈로 삼아 포즈마다 `[start+i·P, start+i·P+hold]`(P=hold+offset) plateau 를
  만들고 사이를 offset 길이로 보간한다. 값은 `getAttr(time=)` 로 샘플링(키 없던 커브도 보간값),
  plateau 안쪽 탄젠트 flat·보간 구간 spline(유지→가속→감속→유지), Start 비우면 오브젝트별 첫 키 앵커.
  로직 `app/core/offset_hold_manager.py`. 처음 별도 탭으로 추가(v01.12)했다가 **Key Edit 탭으로 통합**
  (v01.13), 다시 Key Edit 탭을 **Move Keys / Graph Editor / Offset & Hold 접이식 섹션 3개**로 분리
  (v01.14, Offset & Hold 기본 접힘). 접이식 위젯은 재사용 모듈 `Framework/qt/MOD_collapsible_qt_v01.py`
  (`JUN_mod_collapsible_qt_v01` + 숨김 시 sizeHint 0 인 `JUN_mod_fit_tab_page_v01`)로 분리, 레거시
  `JUN_PY_SelectionTool` 의 `frameLayout(collapsable=True)` 패턴 이식. 섹션 토글·탭 전환 시
  `_fit_window` 가 **창 크기를 현재 탭 콘텐츠에 맞춰 자동 조정**. #A00110_animTool
- **standalone Qt 패키지 충돌 수정**: A00080·A00210·A00220·release_builder_QT 가 모두 최상위
  `app` 으로 import 해, 한 인터프리터(Maya·공용 런처)에서 두 툴을 동시에 띄우면 `sys.modules['app']`
  가 첫 툴로 점유돼 두 번째 툴이 `ModuleNotFoundError`(또는 엉뚱한 창)로 실패하던 문제 해결. launch.py 는
  **툴 고유 경로**(`tools.<tool>.app...` / `dev.release_builder_QT.app...`)로, 내부 모듈은 **상대 import**
  (`from ..core import …`)로 전환 — in-Maya 툴(A00110)·템플릿(A00004/A00008)이 이미 쓰던 규약과 일치.
  4개 툴 동시 로드 검증 완료. A00080·A00210 의 launch/내부 import 경로 전환은 **전용 커밋으로 분리**
  푸시(A00220·release_builder 분은 각 기능 커밋에 포함). #Framework
- **Framework/styles (dark 테마 가독성)**: Windows 10 에서 **탭바·테이블 헤더** 글자가 배경과
  대비가 낮아 안 보이던 문제 수정. qss 에 `QTabBar::tab`/`QTabWidget::pane`/`QHeaderView::section`
  (+hover·corner)을 **명시**(어두운 배경·밝은 글자·테마 accent 테두리)해, OS 네이티브 렌더(Win10/11
  차이)와 무관하게 **Win11 처럼** 보이도록 했다. `dark.qss` + 6개 `*_dark.qss`(blue/brown/coral/
  green/purple/yellow) 일괄 적용, 라이트 테마 제외. 공용 Framework 라 dark 테마 전 Qt 툴에 반영.
  #Framework

## 2026-06-17

> [!summary] 신규 툴 2종(A00210 FileManager·A00010 HumanIK V02) + 윈도우 최상단 정책 개선 + 신규 툴 2종(A00200·Release Builder) + Mirror Key Behavior + 저장소 정리(레거시 아카이빙·포트폴리오 README·FileManager 데이터 분리·브랜치 정리) + A00210 Path Structure 탭
- **Framework/qt**: 모든 Qt 툴 창을 **마야 메인 윈도우에 parent** — 뷰포트 위에는 떠 있되 다른 툴
  창과는 정상 Z-order(밑에 있는 창을 클릭하면 위로 올라옴). `Qt.WindowStaysOnTopHint`(항상 최상단)
  폐기. 공용 헬퍼 `Framework/qt/maya_window.py` 의 `maya_main_window()` 추가, A00110+12개 Qt 툴 및
  A00008 템플릿에 일괄 적용(A00200 은 기존부터 동일 패턴) (`d2b5ad4`) #Framework
- **dev/release_builder_QT**: 릴리스 패키징용 **PySide Release Builder QT** 신규 (`7640a92`) #dev
- **A00200_CSV_tool**: **ARKit 페이셜 CSV import** 신규 툴 + 드래그&드롭 설치(`__dragDrop_A00200`)
  (`3d9ec1e`) #A00200_CSV_tool
- **A00110_animTool**: Mirror Key 탭에 **Behavior 모드**(기본 ON) 추가 — 반대쪽 컨트롤러의 고유
  forward/up 축 방향을 보존하며 미러. 소스의 **로컬 채널 값(translate/rotate)을 타겟에 그대로
  복사**한다(반사·행렬 연산 없음, 반사축 무관). Maya `mirror joints` 의 Behavior 세팅으로 만든
  좌우 축 반전 리그용. 체크박스로 기존 월드 반사(orientation)와 선택, 구간/현재프레임 둘 다 적용.
- **A00110_animTool**: Behavior 가 ON 이면 반사축이 무의미하므로 **Mirror Axis 라디오 비활성**.
- **A00110_animTool**: Mirror 실행(Mirror Selected·Mirror Current Frame)이 **씬 선택과 무관하게
  Source/Target 리스트의 오브젝트만** 대상으로 처리(선택 → `Resolve Pairs`/`Select Source` 로
  리스트 채우기 → 실행으로 단계 분리). (v01.08~01.09) #A00110_animTool
- **A00210_FileManager**: Maya 씬(`.mb`/`.ma`) **버전·작업기록 추적** standalone PySide6 앱 신규 —
  경로 스캔·파일별 작업자/타임스탬프 로그·**화면 영역 캡쳐 썸네일**·기록(records/thumbs) **git
  push/pull**(원본 미푸시). 키는 프로젝트 상대경로(cross-PC), 절대경로 설정은 로컬 prefs. core(Qt/Maya
  비의존)/ui 분리, 사용법 [A00210 가이드](A00210_FileManager.md) (`fd74913`) #A00210_FileManager
- **A00010_humanIKTool_V02**: HumanIK 툴 in-Maya PySide 재작성 신규 (`6ef7f76`) #A00010_humanIKTool
- **.gitignore**: PyInstaller 빌드 산출물(`build/`·`dist/`) 무시 추가 (`fd74913`)
- **저장소 아카이빙**: 레거시·학습 폴더 10개를 `_archive/` 로 이동(`git mv`, 히스토리 보존) —
  `legacy_tools/`(00_Old·00_RUN·01_Modules·01_Modules_Small·02_Modules_Old·03_Modules_Test·
  04_KWI_generator) + `study_notes/`(100_Memo·101_cellular_automata·101_maya_python_technic).
  추적되던 `.pyc` 12개 정리, 레거시→현행 매핑표 `_archive/README.md` 추가 (`5248196`) #archive
- **루트 README**: 채용·상사 대상 **포트폴리오형 루트 `README.md`** 신규 — 한국어 본문 + 영어 요약,
  도메인별 툴 하이라이트·기술 스택·저장소 구조·연락처(이메일/GitHub/Notion·웹 포트폴리오). 스크린샷
  자리 `JUN_All/docs/assets/` (`d73c8c7`) #docs
- **A00210_FileManager 데이터 분리**: 별도 원격(`JUN_FileManager_data`)으로 동기화되는 데이터 폴더가
  부모 트리 안에 **중첩(nested repo)** 돼 있던 임베디드-repo 위험 해소 — 부모 트리 밖으로 이동 +
  `store_dir` prefs 갱신, 부모 `.gitignore` 에 추가해 우발적 gitlink 커밋 방지 (`91949fd`) #A00210_FileManager
- **브랜치 정리**: `Dnable` 을 master 역할 기본 브랜치로 확정. `dev_archive`(로컬+원격)·`master`(로컬)
  삭제, 서버에 없던 `Dnable_bch` 추적 잔상 prune. 이후 일상 작업/푸시는 `dev` 로 일원화 #git
- **A00210_FileManager**: **Path Structure 탭** 신규(v01.01) — 베이스 폴더의 하위 폴더 구조를 JSON 으로
  저장해 다른 PC 와 git 동기화하고 **버튼 하나로 폴더만 재생성**(파일 미생성). 베이스는 project_root
  상대경로로 저장→PC 마다 자기 루트 아래 재생성. **Recursive** 토글(중첩 트리 전체 vs 최상위만),
  이름별 다중 저장, **Capture(미리보기)/Save 분리**, 트리뷰 preview(`build_tree_lines`). 기존 창을
  QTabWidget(File Manager/Path Structure)로 재구성, 로그 공유. 코어(`app/core/path_structure.py`,
  Qt 비의존)/ui 분리 (`4dfa979`) #A00210_FileManager

## 2026-06-16

> [!summary] 신규 병합 툴 2종 + Qt 인프라 정리 + JointTool Aim 재설계
- **A00145_RigConnect**: MEL ConnectionTool V04.02 + A00140 병합(4탭 PySide) 신규 툴, 사용법 [A00145 가이드](A00145_RigConnect.md) (`5592490`, `d1750df`) #A00145_RigConnect
- **A00060_jointTool_V02**: MEL JointTool V05.03 + A00060 병합(4탭) 신규 툴, 사용법 [A00060 V02 가이드](A00060_jointTool_V02.md) (`ec42af1`, `bbb78bd`) #A00060_jointTool_V02
- **A00060_jointTool_V02**: Aim 탭 재설계 — Aim axis 드롭박스(X/Y/Z) + twist-only IK식 정렬(joint 월드 위치 보존·constraint/cycle 제거·레퍼런스 안전, v01.01) (`4c67ac8`) #A00060_jointTool_V02
- **Framework/qt**: 모든 Qt 툴을 `Framework.qt.qt` 래퍼 경유로 일원화 (`f3c8d58`) #Framework
- **deps**: 외부 의존성 관리 중앙화 (`a13792c`)
- **A00110_animTool**: Smart bake 옵션(native `bakeResults -smart`, v01.07) + 비교 문서 (`859299d`, `c0d7db8`) #A00110_animTool
- **dragDrop**: 드롭 설치 파일명 고유화로 셸프 버튼 충돌 해결 (`30f0f09`)
- **A00190_FKIK_General_Tool**: 레거시 FK/IK 툴 PySide 리팩터 (`cab90a6`) #A00190_FKIK

## 2026-06-15

> [!summary] animTool/abSymMesh PySide 강화 + bake 성능
- **A00110_animTool**: Copy Key 탭(v01.03)·Mirror Key 탭(v01.04) 추가 + 문서화 (`f6139ac`, `147fa7f`, `be41423`, `8917cbf`) #A00110_animTool
- **A00180_abSymMesh**: Python/OpenMaya 재구현(속도)·app/ 레이아웃 + PySide UI·동작 문서 (`f01ced1`, `f6f5053`, `4719e56`) #A00180_abSymMesh
- **A00170_driverTool**: RemapVal + SphericalEye 를 탭 툴로 병합 (`96acac4`) #A00170_driverTool
- **A00150_remapVal**: 보간을 enum(Linear/Smooth/Spline)으로 (`2cb49aa`) #A00150_remapVal
- **A00120_FKIK**: per-frame 루프 대신 native `bakeResults` 로 bake (`b83c591`) #A00120_FKIK
- **A00080_KWI_creator**: 결합 파일 출력(base+setting+LD) (`61c459e`) #A00080_KWI_creator
- **dev/reload**: per-tool `reload_for_tool` 추가 + 전 Qt 런처 전환 (`1660c63`)
- **Framework/styles**: 체크박스·라디오 인디케이터 전 테마 가시성 수정 (`acf285e`, `730f8b4`) #Framework

---
