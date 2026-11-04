---
name: wip-a00110-fix-sliding
description: A00110_V02 v02.48 Bake > Fix Sliding — 정지 구간마다 Shift+A(Hold + Layer Blend Key) 재현, B→A→D 보정, _debug_speed, KANA 실측 씬
metadata:
  type: project
---

2026-11-04 v02.48 구현. `core/fix_sliding_manager.py` `FixSlidingManager`, UI = Bake > Fix Sliding. 계획서
`JUN_All/docs/plans/a00110_fix_sliding_plan.md`(§9 = 이웃 구간 블렌드 침범 대안 A~E). 시험 `tests/test_fix_sliding.py` 30 · `_ui.py` 11.

- 정의(사용자): 스무딩 월드 속도 < Threshold(**최대 속도의 %**) 인 구간 [a, b] 마다 "그 구간 **T + R** 키를 고르고 Layer Blend Key 켠 채 Shift+A".
  **길이 > M 일 때만**(글자 뜻은 반대였지만 사용자가 > M 확정).
- 보정 **B(Merge gap G 기본 4) → A(블렌드 시작 = max(a'−N, 앞 구간 끝)) → D(b 에도 a' 레이어 값 + flat)** — 사용자 예시 [0,10]·[12,20], N=5 에서
  f7 키가 앞 구간을 다시 움직였다. 셋 끄면 순수 Shift+A → 핵심 시험은 손으로 selectKey + run_hold 한 결과와 1e-9 대조.
- Hold 대상 = Hot Key > Main `view_layer` 커브, Layer Blend = Hot Key > Main 설정 + `force=True`(enabled · 보기 게이트 무시).
- 디버그 노드는 **undo 를 끈 채**(밖에서 만들면 Ctrl+Z 한 번이 디버그만 되돌린다). 커브는 API `MFnAnimCurve.addKeys`.
- **v02.49**: 디버그 노드 = 오브젝트마다 `<이름>_debug_speed`(speed 흰 · smooth 밝은 하늘 · threshold 빨강 · result 초록 —
  **animCurve 의 `useCurveColor` + `curveColor`(double3)** 로 그래프 에디터 색), Layer · N 을 탭에서 고름(`run(layer=, offset=)`), 공용 Expand.
- **★ v02.50 크래시**: undo 를 끈 채(`undoInfo stateWithoutFlush=False`) 노드를 지우면 **바로 해제** → 그 커브가 그래프 에디터에 떠 있으면
  다음 paint 에서 `AnimUISlice.dll uiPainter` ACCESS_VIOLATION(진행 팝업 processEvents 가 방아쇠). → 디버그 노드 · 커브는 **재사용**(MFnAnimCurve.remove,
  `cutKey -clear` 는 커브 노드까지 지움), 커브 고치는 동안 이벤트 루프 금지 · GE `setUpdatesEnabled(False)`. `selectKey(clear=True)` 는 대상 없이 부르면 헤드리스에서 실패.
- `_SmartLayer` 는 .pyc — 디컴파일 안 함, 툴팁 문구만 참고([[wip-a00110-counter-layer]] 와 같은 결정).

**실측 씬(사용자 제공, 테스트용으로 써도 됨, 저장하지 말 것)**:
`C:\JUN\JUN_MUE\00_04_02_ANI_00_PJ_010\scenes\5040_cleanup_BCM_KANA\00010_cleanup_KANA_00010.mb` —
`origin:KANA:Cage:CH_l_foot_xx_ctl`, `origin:KANA:Cage:CH_r_foot_xx_ctl`(실제 모캡을 발 IK 에 베이크). 6830 f, 기본값 191 구간 · 34 s · 구간 안 월드 속도 0.

**Why:** 사용자가 손으로 하던 "구간 고르고 Shift+A" 를 자동화. **How to apply:** 고칠 때 순수 Shift+A 대조 시험(6)을 깨지 말 것. 남은 것: GUI 확인, 대안 E(이동 거리 비례) 는 다음 후보,
손 Shift+A 의 블렌드 침범은 범위 밖. 관련 [[wip-a00110-hold-layer-blend]].
