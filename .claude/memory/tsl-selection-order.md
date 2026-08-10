---
name: tsl-selection-order
description: "MOD_tsl_qt_v01 Order 체크박스 — 컴포넌트 선택 순서 유지, trackSelectionOrder pref 트랩"
metadata: 
  node_type: memory
  type: project
  originSessionId: 023af178-09b0-4514-8e85-069cf18e3ef9
  modified: 2026-08-10T08:43:50.098Z
---

공용 TSL 위젯 `Framework/qt/MOD_tsl_qt_v01.py` (2026-07-29, 구현+헤드리스 검증+푸시, 마야 실기 대기)에
헤더 행 **`Order` 체크박스**를 추가했다 — 켜면 Maya 에서 **고른 순서대로** 리스트에 담는다.

**Why:** `cmds.ls(sl=True)` 는 컴포넌트(vtx/edge/face)를 **인덱스 순서**로 돌려준다(5→0→3→1 로 찍어도
0,1,3,5). **오브젝트/트랜스폼은 pref 없이도 선택 순서를 유지**하므로 깨지는 건 컴포넌트 한정.

**How to apply:**
- 순서를 얻으려면 `cmds.selectPref(trackSelectionOrder=True)` + `cmds.ls(orderedSelection=True, flatten=True)`.
- **트랩**: pref 가 꺼져 있으면 `ls(orderedSelection=True)` 는 **에러 없이 조용히 인덱스 순서**를 준다 →
  가능 여부는 반환값이 아니라 `selectPref(q=True, trackSelectionOrder=True)` 로 판별할 것.
- pref 는 **켠 시점부터** 기록 → 켠 뒤 다시 선택해야 순서가 잡힌다(로그로 안내).
- **트랩 2 (2026-08-10 확인)**: 컴포넌트 순서는 **"선택 이벤트" 단위**로만 기록된다. pref 를 켜 두어도
  `cmds.select([vtx70, vtx10, vtx40])` 처럼 **한 번에 리스트로** 고르면 `ls(orderedSelection)` 이
  **인덱스 순서**를 준다. 하나씩(`select(..., add=True)` 차례로) 골라야 순서가 잡힌다. 실사용(클릭)은
  문제없지만 **헤드리스 테스트는 반드시 `add=True` 로 나눠 고를 것**. 오브젝트는 한 번에 골라도 유지.
- **TSL 위젯 없이 쓰기 (2026-08-10)**: 모듈 레벨 공개 헬퍼 `acquire_order_tracking()` /
  `release_order_tracking()` / `is_order_tracking()`. 자체 리스트 UI 를 쓰는 툴도 **같은 전역 refcount 를
  공유**해야 한다 — 각자 `selectPref` 를 켜고 끄면 한 창이 닫힐 때 다른 창의 순서 추적이 끊긴다.
  첫 적용: [[wip-a00420-wrapper]] 의 Guide Pairs 트리(QTreeWidget + 자체 `Order` 체크박스).
- 전역 pref 라 항상 켜지 않고 토글. 끌 때는 **우리가 켠 경우에만** 원복, 여러 TSL 대비 모듈 전역
  refcount(`_ORDER_REF`), 위젯 `destroyed` 시 자동 반납(람다가 self 대신 dict 홀더만 캡처).
- 옵션: `show_order`(기본 True, 체크박스 표시) / `order_default`(기본 False) /
  `set_order_tracking()` / `is_order_tracking()`. 호출부 75곳 AST 확인 — 위치 인자 2개 이상 없음.
- **"리스트 말고 지금 선택한 것으로 바로 실행" 버튼을 만들 땐 `maya_selection()`** (2026-07-30 public 노출,
  내부 `_maya_selection()` 위임)을 호출한다. Order 판정 + `flatten` + 폴백이 이미 들어 있어 Select/Add
  버튼과 **같은 규칙**이 보장된다 — 호출부에서 `ls(orderedSelection=...)` 를 다시 쓰지 말 것.
  첫 적용: A00060_jointTool_V02 `Match to Sel` (v01.04).
- **mayapy 로는 이 위젯을 못 띄운다**: `maya.standalone` 이 이미 `QGuiApplication` 을 만들어 둬
  `QWidget` 생성 실패. Maya 의미론은 mayapy 로, 위젯 배선은 **stub `maya.cmds` + 시스템 python PySide6** 로 검증.
- 문서: `JUN_All/docs/Framework_MOD_tsl_qt.md` (공용 위젯 문서, docs/README.md 에 "공용 위젯" 섹션).

관련: [[wip-tsl-uuid-selection]], [[mayapy-headless-verify]], [[framework-timerange-widget]]
