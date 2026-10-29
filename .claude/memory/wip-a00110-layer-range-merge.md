---
name: wip-a00110-layer-range-merge
description: A00110_animTool_V02 v02.27 Bake > Merge Layers(2026-10-29 구현) — 애니 레이어 구간 한정 병합 = bakeResults -rwl -time s:e -pok + 소스 중화(additive identity step / override weight 0) + 경계 insert fixed; 회귀 111/111, 정적 멤버 · by-layer triple · override 대상 규칙
metadata:
  type: project
---

**구현 완료 v02.27 (2026-10-29, 계획과 같은 날).** `app/core/layer_merge_manager.py` · `Bake > Merge Layers`(BAKE_PAGES 세 번째 — 같은 날 다른 세션이 v02.26 Counter Layer 를 넣음) · 회귀 `tests/test_layer_range_merge.py`(111/111, 약 4분) · 계획서 `docs/plans/A00110_animTool_V02_layer_range_merge_plan.md`. **GUI 확인 아직.**
요청: 마야 Merge Layers 를 **프레임 구간 안에서만**(`a + b => b` 기존 / `=> c` 새 레이어 / `b` 가 Base 포함), 전후 월드 움직임 동일.

**Why:** 마야 `animLayerMerge`(performAnimLayerMerge.mel) 의 본체는 `bakeResults -destinationLayer X -resolveWithoutLayer a -rwl b -time ":"` 한 줄이고
소스를 통째로 지운다. 구간 병합은 소스가 구간 밖에 살아야 하므로 (1) 구간 안 이중 기여 제거, (2) 경계 보간 두 문제가 전부다.

**How to apply:**
- bake 는 마야 그대로 + `time=(s,e)`, `preserveOutsideKeys=True`, 대상이 기존 레이어면 `rwl` 에 자신도 넣고 **mute 하지 않음**. `removeBakedAttributeFromLayer` 는 쓰지 않는다.
- 경계: 손대는 모든 기존 커브에 `setKeyframe -insert` `s-1`, `e+1` → **`keyTangent fixed`**(auto 는 이웃 키에 반응). bake 로 새로 생긴 커브(대상에 없던 채널 · 새 레이어)는 `s-1`/`e+1` identity 키 — 안 하면 끝값이 구간 밖으로 샌다.
- 소스 중화: **additive** = `cutKey (s,e)` + `s` identity 키 `-ott step` + `e` identity (identity 0, 스케일은 `scaleAccumulationMode` enum **Additive(0):Multiply(1)** → Multiply 면 1). **override** = `weight` 계단(s-1 cur step · s 0 step · e 0 step · e+1 cur). override 멤버는 **키 없이도 정적 값으로 덮으므로** plug 집합에 모든 멤버 포함(마야와 같음).
- **Base 대상**: `-destinationLayer BaseAnimation` 은 소스 레이어 커브를 **통째로 지운다**(bake-to-base) → 임시 additive(by-component · additive scale) 레이어를 `children[0]` 앞(= 맨 아래)에 굽고 `base'(f)=base(f)+c(f)` 로 접은 뒤 삭제. `children[0]` 이 맨 아래(제일 먼저 평가), `moveLayerAfter X` = X 위.
- 새 레이어: 마야 Auto 규칙(소스에 override 있으면 override, 누적 모드는 과반), **가장 위 소스 바로 위**에, override 면 weight 를 밖 0 / 안 1 로 게이트.
- **거부**: 대상 weight ≠ 1 또는 애니메이션(bakeResults 가 되돌려 나누지 않아 틀림 — 마야는 늘 새 레이어 weight 1 이라 이 경우가 없다), lock(편집이 조용히 무시), mute, solo 존재, 레퍼런스, 자식 레이어, Base 소스 → 새 레이어(v2), `Listed objects only` + override 소스.
- 정확도 계약: 정수 프레임 전부 동일(1e-15) · 구간 밖 반 프레임 동일 · 구간 안 프레임 사이는 bake 보간(마야 자체 병합도 7.9e-4 다름). smart bake 는 근사(7.9 차이) → 기본 OFF.
- `setKeyframe(plug, animLayer=root, t)` 는 **역산**해 넣는다(정적 5.0 → 5.03) — 값은 반드시 **커브 노드에** 쓴다.
- 성능: `bakeResults -rwl` 키당 0.22 ms(50 ctl × 300 plug × 1001 f = 66 s, 마야 자체 병합 139 s) → 진행 팝업 필수.
- UI 위치는 `Bake > Merge Layers`(Transfer > Layer 는 값 그대로 복사라 성격이 다름). 시험 씬은 레이어마다 따로 키(번갈아 키하면 역산이 섞임). 테스트 레이어 이름 `top` 은 **기본 카메라와 겹쳐 `top1`** 이 된다.
- **구현 중 추가된 규칙(실측)**: override **기존 대상** = 키 없는 멤버는 정적 값(blend 노드 `inputB`)을 경계에, 멤버 아니던 채널은 거부 · additive 대상의 정적 멤버(Additive 스케일 모드의 1)도 identity 아닌 **그 값**으로 경계 키 · additive 소스의 키 없는 정적 값도 기여(`_blend_input_plug` 로 `plug <- bn.output[X] <- bn.inputA[X]` 사슬을 내려가 그 레이어 노드의 `inputB[X]`) → 커브 만들어 밖 유지 · **by-layer 회전은 rotateX/Y/Z 세트**(하나 빠지면 2.0 틀림) · visibility(animBlendNodeBoolean)는 정적 감지 제외 · 잠긴 plug 는 bakeResults 가 조용히 건너뛴다(경고). `Qt.UserRole` 은 256(32 아님).
- UI: `Listed objects only` 대신 **`Selected objects only`**(씬 선택). Range 둘 다 비우면 `source_key_range` = 마야 전체 병합. 진행 팝업 기준 plug × 샘플 > 4000. bake 32 채널씩 나눠도 시간 같음.

관련: [[animlayer-copy-cut-traps]] [[wip-a00110-layer-key-copy]] [[wip-a00110-graph-focus]] [[mayapy-headless-verify]]
