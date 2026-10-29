---
name: wip-a00110-counter-layer
description: A00110_animTool_V02 Bake > Counter Layer 계획(2026-10-29) — 글로벌 레이어가 바꾼 자식의 월드 T/R 을 되돌리는 보정 additive 레이어 = 뮤트 스냅샷 worldMatrix + xform -ws -m + setKeyframe -animLayer -value 역산; 실측 21/21
metadata:
  node_type: memory
  type: project
  originSessionId: 52b79109-11ee-42fc-9bb6-a2c4571b1403
  modified: 2026-10-29T03:46:54.986Z
---

**계획 단계 (2026-10-29), 구현 전.** `docs/plans/A00110_animTool_V02_counter_layer_plan.md` · 실험 `tools/A00110_animTool_V02/tests/exp_counter_layer.py`(15/15 + 추가 6).
요청: `global_ctl > foot_l/r_ctl`, 발은 additive `lyr_01..n` 에 키, `global_ctl` 만 든 `lyr_glo` 가 발의 월드를 바꿈 → `lyr_glo` 는 그대로, 발 월드 T/R 이 **`lyr_glo` 뮤트 상태와 같아지는** 새 레이어 하나.

**Why:** `bakeResults -rwl` 은 어트리뷰트 단위 — 발의 로컬 값은 `lyr_glo` 전후 같고 **부모**가 바뀐 것이라 마야 레이어 기능으로는 못 한다. 수작업(프레임마다 발 되돌리고 키)의 자동화.

**How to apply:**
- 두 번 훑기: ① 레이어 `mute` → `currentTime` 루프로 `worldMatrix[0]` 스냅샷(`getAttr(time=)` 은 값 같지만 3배 느림) → 뮤트 복원. ② `xform(o, ws=True, m=W_pre)` → `xform -q -t` + `getAttr rotate` 로 로컬 목표 → **`setKeyframe(o, at=a, t=f, v=val, animLayer=L)`** 가 누적 모드(by-layer/by-component) · weight · 아래 override · JO · 회전 순서를 **전부 역산**한다. 우리는 역산 안 함.
- 회전 동치해: `alternateSolution` + `setToClosestCut(지금 로컬 회전)` + `asMatrix().isEquivalent` 확인([[euler-closest-solution-not-equivalent]]). 270° 드라이버에서 점프 23°.
- **매 프레임 키가 기본** — 드라이버 키(50f)에만 찍으면 0.95 유닛 틀림, 2 프레임마다 2.5e-3. 정수 프레임 1e-14, 반 프레임 1.15e-3(보간).
- **잠긴 채널은 `animLayer -at` · `xform` · `setKeyframe`(반환 0) 전부 조용히 지나간다** → `getAttr -lock` 사전 검사 + 경고.
- 새 레이어는 `children[-1]`(맨 위)에 생긴다. 구간 밖은 `s-1`/`e+1` identity(0) 키(미실측, 회귀 1항목). 발이 `lyr_glo` 에도 키가 있으면 그 기여까지 되돌아간다(정의상 옳음, 로그 노트).
- GUI 함정: `xform` = setAttr 라 **autoKeyframe ON 이면 활성 레이어에 자체 키** → 실행 중 끄고 복원(mayapy 로는 확인 불가).
- 거부: 레이어 뮤트 상태 · solo 존재 · Base 체크 · 비 애니 소스(컨스트레인트) 채널. 스케일 v1 제외.
- 비용 0.9 ms/(오브젝트·프레임) → 진행 팝업. UI = `Bake > Counter Layer`(TSL + 체크 레이어 목록 + Range + Channels T/R + Step + 이름 + Zero outside/Skip unchanged/Select new).
- `_SmartLayer` 는 `.pyc` — **디컴파일 금지**, 툴팁·Starter Guide 텍스트만 참고. 속도 비례 분배(Linear Offset 등)는 v2 후보.
- 같은 날 [[wip-a00110-layer-range-merge]] 도 `Bake` 하위 탭을 추가한다 — `main_window.py` Bake 튜플 · `version.py` 충돌 주의, 구현 전 `git log -3 -- tools/A00110_animTool_V02`.

관련: [[wip-a00110-fill-keys]] [[animated-attr-setkeyframe-plus-setattr]] [[animlayer-no-global-selected-query]] [[wip-a00110-tab-taxonomy]] [[mayapy-headless-verify]]
