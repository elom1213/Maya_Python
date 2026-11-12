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
- **v02.37 Constrain Objects to Locators**(2026-11-04, 기본 끔): 베이크 뒤 로케이터 -> 오브젝트, Parent(기본) · Point · Orient · Scale,
  Parent ↔ Point/Orient 배타, `mo=False`. 막힌 축 skip. ★ **scaleConstraint 는 키 있는 scale 축에 실패**("Destination attribute must be writable" —
  translate/rotate 와 달리 pairBlend 가 안 생긴다) → 키 있는 scale 축도 skip. 시험 `test_locator_bake_constrain.py` 34/34, UI 31/31.
- 시험 함정: 키 있는 오브젝트의 컨스트레인트는 pairBlend 를 거쳐 연결 → `listConnections(node, type=...)` 로 못 찾는다, `listRelatives(type=...)` 로.

- **v02.56 `Fast - parents don't move`**(2026-11-10, 기본 끔): 부모 쪽 행렬 `inverse(matrix)*worldMatrix` 를 Start 에서 한 번, 프레임마다
  자기 `matrix` 만 `getAttr -time` → 분해 → 임시 커브(createNode) + API addKeys → `copyKey`/`pasteKey replaceCompletely` → 임시 삭제.
  ★ `animCurve.ktv` 는 setAttr 불가 — copy/paste 경로가 undo · redo 모두 정확(1000 키 0.006 s).
  ★ **부모 정지 여부는 사용자가 고른다**(사용자 지시: 연결이 있어도 안 움직이는 그룹이 있다) — 툴이 연결로 판단하지 말 것.
  ★ 움직이는 부모를 `worldMatrix -time` 으로 프레임마다 읽기는 깊은 계층에서 일반 베이크보다 느렸다(0.91 vs 0.17 s) → 넣지 않음.
  ★ mayapy 기본 평가는 DG(off) 라 시간 변경이 거의 공짜 — 병렬(GUI 기본)로 바꿔야 "프레임마다 장면 전체 평가" 비용이 재현된다.
- ★ **v02.56 버그 수정**: `parentConstraint` 는 원본 **rotateAxis 를 무시** → 로케이터가 일정 각(23.26°) 어긋났다. 원본 자세로 놓고(`_snap_to`)
  `maintainOffset=True`. 시험 씬에 rotateAxis 를 넣지 않으면 못 잡는다.
- 시험 `tests/test_locator_bake_fast.py` 18/18, UI 36/36.

- **v02.58 애니메이션 레이어 컨트롤러 + `Blend only in Frame Range`**(2026-11-12, 기본 켬): 레이어 채널은 animBlendNode 구동이라
  옛 `_blocked_axes` 가 전 축 skip(컨스트레인트 0 개, 사용자 제보). ★ **컨스트레인트 명령의 `-layer` 플래그** = 새 override 레이어
  `LOC_Constraint` 에 축을 넣고(`animLayer -e -attribute`) 건다 — 키 있는 scale 도 된다. 구간 = 레이어 weight step 키 0/1/1/0.
  켜면 모든 오브젝트 레이어 경로, 끄면 레이어 오브젝트만. ★ mayapy 에선 `currentTime` 도 undo 대기열에 쌓인다 → 시험은 시간 이동 전에 undo.
  시험 `test_locator_bake_layers.py` 26/26, UI 38/38. **GUI 확인 아직.**

- **v02.59 `Bake to Keys`**(2026-11-12): 컨스트레인트 결과 → 오브젝트 키, 컨스트레인트 · LOC_Constraint · 로케이터 정리.
  ★ **Bake 탭은 레이어 오브젝트 키를 맨 위 override 레이어에 찍는다 → LOC_Constraint 자신에 들어가 레이어 삭제 시 사라진다.**
  해법 = `bake_layered(before_write=정리)` — 샘플 뒤 정리, **대상 레이어는 정리 뒤에** 정한다.
  ★ `addSelectedObjects` override 레이어는 전 채널 멤버 + 커브 없음 → 구간 안만 `setKeyframe -animLayer` 하면 구간 밖이 끝 값으로 늘어난다 →
  `edge_keys`(Start-1 / End+1 원래 값). Bake 탭엔 끔(컨스트레인트가 남아 있어 경계 값이 섞임).
  시험 `test_locator_bake_to_keys.py` 18/18. **GUI 확인 아직.**

관련: [[framework-progress-widget]], [[framework-timerange-widget]], [[wip-a00110-get-sel-range]], [[wip-a00110-counter-layer]]
