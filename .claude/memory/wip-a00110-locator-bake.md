---
name: wip-a00110-locator-bake
description: A00110_animTool_V02 v02.36 Bake > Locator (LOC + Anim) - _SmartLayer 의 같은 버튼을 새로, bakeResults 한 번 + MDGMessage 시간 변경 콜백으로 게이지, 구간을 쪼개면 컨스트레인트가 끊긴다
metadata:
  type: project
---

**A00110_animTool_V02 v02.36 `Bake > Locator`** (2026-11-03). 사용자가 마야에서 `_SmartLayer` 패키지로 쓰던 **`LOC + Anim`**
(선택 오브젝트마다 로케이터 → 현재 타임라인 베이크)이 "가끔 답답하거나 오류" 라 새로 만들었다.
조건(사용자): 대상 TSL · 베이크 중 진행 팝업(게이지) · Start / End + `Get Current` · `Get Sel Range`.

- 코어 `app/core/locator_bake_manager.LocatorBakeManager.bake` — `<잎이름>_LOC` 월드 로케이터(회전 순서 복사) + 임시 parentConstraint
  (+ scaleConstraint) → **bakeResults 한 번**(simulation) → 컨스트레인트 삭제 → 오일러 필터. 실패 시 만든 것 삭제, undo 한 번.
- ★ **게이지 = `om.MDGMessage.addTimeChangeCallback`** — `simulation=True` 베이크는 프레임마다 시간을 옮기며 콜백을 부른다
  (mayapy 2024 실측 1~200 → 201 회, `simulation=False` 는 0 회). 단일 C++ 베이크에 진행률을 다는 일반 방법.
- ★ **구간을 쪼개 bakeResults 를 여러 번 부르면 안 된다** — 첫 호출의 `disableImplicitControl=True` 가 컨스트레인트를 끊어 다음 구간이 안 따라온다.
  그래서 Cancel 없음.
- 진행 팝업 단계 넘기기: core 의 `progress` 콜백에 `progress.phase = lambda name: dlg.begin_phase(name)` 속성을 붙여 넘긴다.
- 시험 `tests/test_locator_bake.py` 25/25(월드 T/R 1e-13), `tests/test_locator_bake_ui.py` 20/20(오프스크린). **마야 GUI 확인 아직.**
- 시험 장면 함정: `setAttr grp.s 2` 를 **parent 전에** 하면 `cmds.parent` 가 자식에 0.5 를 넣어 월드 스케일이 1 이 된다.

관련: [[framework-progress-widget]], [[framework-timerange-widget]], [[wip-a00110-get-sel-range]], [[wip-a00110-counter-layer]]
