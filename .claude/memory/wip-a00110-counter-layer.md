---
name: wip-a00110-counter-layer
description: "A00110_animTool_V02 v02.26 Bake > Counter Layer (2026-10-29) — 글로벌 레이어가 바꾼 자식의 월드 T/R 을 되돌리는 보정 additive 레이어 = 뮤트 스냅샷 worldMatrix + xform -ws -m + setKeyframe -animLayer -value 역산; 200 프레임 청크로 메모리 고정; 회귀 51/51, GUI 확인 아직"
metadata:
  node_type: memory
  type: project
  originSessionId: 52b79109-11ee-42fc-9bb6-a2c4571b1403
  modified: 2026-10-29T04:02:34.824Z
---

**v02.26 구현 완료 (2026-10-29), 마야 GUI 실기 확인 아직.** 계획서 `docs/plans/A00110_animTool_V02_counter_layer_plan.md` ·
코어 `app/core/counter_layer_manager.py`(`CounterLayerManager`) · 회귀 `tests/test_counter_layer.py`(51/51).
요청: `global_ctl > foot_l/r_ctl`, 발은 additive `lyr_01..n` 에 키, `global_ctl` 만 든 `lyr_glo` 가 발의 월드를 바꿈 → `lyr_glo` 는 그대로, 발 월드 T/R 이 **`lyr_glo` 뮤트 상태와 같아지는** 새 레이어 하나. 1000+ 프레임도 쓴다 → 메모리 설계 요청.

**Why:** `bakeResults -rwl` 은 어트리뷰트 단위 — 발의 로컬 값은 `lyr_glo` 전후 같고 **부모**가 바뀐 것이라 마야 레이어 기능으로는 못 한다.

**How to apply:**
- 두 번 훑기: ① 레이어 `mute` → `currentTime` 루프로 `worldMatrix[0]` 스냅샷(`getAttr(time=)` 은 값 같지만 3배 느림) → 뮤트 복원. ② `xform(o, ws=True, m=W_pre)` → `xform -q -t` + `getAttr rotate` 로 로컬 목표 → **`setKeyframe(o, at=a, t=f, v=val, animLayer=L)`** 가 누적 모드(by-layer/by-component) · weight · 아래 override · JO · 회전 순서를 **전부 역산**. 우리는 역산 안 함.
- **메모리**: `CHUNK_FRAMES=200` 청크로 "뮤트 → 스냅샷(`array('d')`) → 해제 → 키 → 버림" 반복, 상한 = 청크 × 오브젝트 × 16 double. **청크 2 부터는 보정 레이어 자신도 뮤트** — 앞 청크 키가 외삽돼 스냅샷을 오염시킨다(T7 로 확인).
- 회전 동치해: `alternateSolution` + `setToClosestCut(지금 로컬 회전)` + `asMatrix().isEquivalent`([[euler-closest-solution-not-equivalent]]). 270° 드라이버에서 점프 23°.
- **매 프레임 키가 기본** — 드라이버 키(50f)에만 찍으면 0.95 유닛 틀림, 2 프레임마다 2.5e-3. 정수 프레임 1e-14, 반 프레임 1.15e-3(보간). `step` 은 끝 프레임 항상 포함.
- **잠긴 채널은 `animLayer -at` · `xform` · `setKeyframe`(반환 0) 전부 조용히 지나간다** → `getAttr -lock` 사전 검사 + 경고. 컨스트레인트 등 비 애니 입력(부모 compound 포함)도 건너뛰고 경고.
- 구간 밖 identity 키는 **커브 노드에 직접** `setKeyframe(curve, t, v=0)` — `animLayer` 경로로 0 을 찍으면 "최종값 0" 역산이라 identity 가 아니다. 끄면 끝값 유지로 구간 밖이 7 유닛 어긋남(T8b).
- `skip_unchanged` 는 쓰기 루프에서 글로벌 켜진 월드 vs 스냅샷 비교 → 끝에 커브 삭제 + `removeAttribute`.
- 새 레이어는 `children[-1]`(맨 위), 이름 충돌은 마야가 `name1` 로 — 로그가 실제 이름을 전한다. `_select_only` 로 새 레이어만 selected+preferred.
- GUI 함정: `xform` = setAttr 라 **autoKeyframe ON 이면 활성 레이어에 자체 키** → 실행 중 끄고 복원(mayapy 로는 확인 불가 — 실기 1순위).
- 거부: 레이어 뮤트 상태 · solo 존재 · Base 체크 · T/R 둘 다 꺼짐. 스케일 v1 제외(월드 스케일 바뀌면 로그 노트).
- UI = `Bake > Counter Layer`(위젯 접두 `cl_`: `cl_tsl` · `lw_cl_layers`+`chk_cl_layers` · `rb_cl_timeline/custom` · `cl_range` · `cb_cl_t/r` · `sb_cl_step` · `le_cl_name` · `cb_cl_zero/skip/select` · `btn_cl_create`). 오브젝트 × 프레임 > `PROGRESS_THRESHOLD`(2000) 이면 `JUN_mod_progress_qt` 팝업 한 단계.
- `_SmartLayer` 는 `.pyc` — **디컴파일 금지**, 툴팁·Starter Guide 텍스트만 참고. 속도 비례 분배(Linear Offset 등)는 v2 후보.
- 같은 날 [[wip-a00110-layer-range-merge]] 도 `Bake` 하위 탭 계획 — 그쪽 구현 때 `BAKE_PAGES` 튜플 · `version.py` 에 이 탭이 이미 있음을 전제로.

관련: [[wip-a00110-fill-keys]] [[animated-attr-setkeyframe-plus-setattr]] [[animlayer-no-global-selected-query]] [[wip-a00110-tab-taxonomy]] [[mayapy-headless-verify]] [[qapplication-before-maya-standalone]]
