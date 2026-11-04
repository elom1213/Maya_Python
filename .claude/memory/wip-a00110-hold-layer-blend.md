---
name: wip-a00110-hold-layer-blend
description: A00110_V02 v02.39 Shift+A Layer Blend Key — 핫키가 고른 레이어에 (현재-N) 레이어 값 + 현재 Pose 키; additive 의 setKeyframe -animLayer -v 는 최종값 역산
metadata:
  type: project
---

2026-11-04 v02.39 구현. `core/hold_layer_manager.py` `HoldLayerManager`, UI = Hot Key > Main > Hold 의 `Layer Blend Key`.
계획서 `JUN_All/docs/plans/a00110_hold_layer_blend_plan.md`, 시험 `tests/test_hold_layer_blend.py` 29/29 · `_ui.py` 11/11.

- 핫키(`run_hold`, nameCommand)는 UI 를 못 읽는다 → UI 가 `HoldLayerManager.update` → **optionVar `JUN_A00110_holdLayer_*` 가 원본**, apply 가 그걸 읽는다(v02.40).
- **★ v02.39 버그: 클래스 변수에 설정을 두면 DEV 리로드 뒤 핫키가 옛 클래스를 읽는다.** reloader 는 같은 깊이 모듈을 sys.modules 등록 순서로 reload →
  `from .x import Cls` 하는 모듈이 x 보다 먼저 reload 되면 옛 Cls 를 잡는다(새 모듈을 기존 세션에 추가했을 때 특히). 핫키 · 콜백 진입점은
  호출 때 `module.Cls` 로 찾고, 상태는 optionVar 처럼 모듈 밖에 둘 것. 증상은 "조용히 아무것도 안 함".
- **★ additive 레이어에서 `setKeyframe obj -at a -v val -animLayer L` 의 val 은 최종(합성) 값** — 마야가 레이어 값을 역산한다.
  레이어 값 그대로 쓰려면 레이어 커브 노드에 `setKeyframe curve -t -v` + `keyframe -e -vc -absolute`(`_key_raw`). override 는 둘이 같다.
- Pose 키는 일부러 obj 경로(최종값 = Pose 값) — Pose Key 탭과 같은 의미.
- 멤버 판정은 `LayerKeyManager._blend_chain(plug)` 노드 ∩ `animLayer -q -blendNodes` (이름 비교 안 함).
- `getAttr plug -time t` 는 레이어 blend 를 거치면 옛 값이 나올 때가 있다 → 시험은 currentTime 을 옮겨 잰다.
- Hold 와 독립 수행, 바깥 undo_chunk 로 중첩(마야 허용) → Ctrl+Z 한 번. Hold 버튼은 Hold 만.
- v02.41 Pose Key `Use current values` → **v02.44 축마다 `Current`**(사용자: "각 어트리뷰트마다 필요한 체크"), optionVar `current_axes`(JSON 목록,
  옛 `use_current=1` 은 체크 축 전부로 옮겨 읽고 새로 쓰면 지움). **v02.45 기본 켜짐 = ry · tx · tz**(`DEFAULT_CURRENT_AXES`, 사용자 요구) —
  시험은 Pose 값 경로를 볼 때 `current_axes=[]` 를 명시해야 한다.
- **v02.46 키 축 = 축 체크 ∪ Current** (사용자 보고: Current 축에 레이어 키가 없다). v02.44~45 는 체크 ∩ Current 라 기본값끼리 안 겹쳐 Current 축이 빠졌다.
  `effective_axes()`. 같은 버전에 Graph Focus Auto-Focus 기본 ON. mayapy 에서는 `cmds.scriptJob` 이 None → `is_active()` False(기능 문제 아님). Pose Key 버튼 · Layer Blend 현재 프레임 키 모두 그 축만 **지금 값**으로.
  Shift+A 는 `capture_current()` 를 **Hold 전에** 불러 값을 잡는다 — Hold 가 커브를 바꾸면 키 없이 움직여 둔 값이 재평가로 사라진다.
- 시험 함정: `currentTime` 이동도 undo 큐에 들어간다 → undo 확인을 먼저, 값 재기는 redo 뒤에.
- v02.43 보기 게이트 `view_layer`(UI `Run only when viewing`, 기본 "" = 루트): 보는 레이어 = 에디터 **selected** → 없으면 preferred →
  없으면 루트, **정확히 그 하나**일 때만 Layer Blend. 사용자 이유: 다른 레이어 커브를 Hold 할 때 끼어들면 위험. mayapy 에선 새 레이어가 선택되지 않지만 GUI 는 만들면 선택된다.
- v02.42 사용자 요구: **선택한 오브젝트에만** 레이어 키(레이어의 다른 멤버 금지). `selected_objects()` 가 animLayer · objectSet · character 를
  뺀다(세트에 setKeyframe = 멤버 전체). mayapy 에선 v02.41 도 새지 않았다(재현 안 됨) — GUI 에서 다시 보이면 메시지 끝 오브젝트 이름으로 확인.

**Why:** 사용자 결정 2026-11-04 — −N 은 레이어 값 유지 · 레이어 없음/비멤버는 경고 후 건너뜀 · −N 기존 키 덮어쓰기.
**How to apply:** 레이어 키를 값으로 찍는 다른 기능도 additive 역산을 의식할 것([[wip-a00110-counter-layer]] 은 역산을 일부러 이용). 남은 것: 마야 GUI 확인.
