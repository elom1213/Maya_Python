---
name: wip-a00390-wavesgen-port
description: A00390 에 블렌더 Waves Gen(GPL-3.0) 바람 모델 · 프리셋 3x2 · Mix 이식 계획(2026-11-05, 구현 전, 결정 5개 대기)
metadata:
  type: project
---

2026-11-05 계획서 `JUN_All/docs/plans/A00390_WindTool_wavesgen_port_plan.md` (**구현 전, §8 결정 5개 대기**).

- 원본 `C:\Users\USER\Desktop\JP\0120_blender_plugin\0010_waveGen\__init__.py` (1,052줄), **GPL-3.0** → 코드 · 드라이버 식 복사 금지, 수식을 독립 구현 + 프리셋 출처 표기.
- 원본 모델: 뼈마다 **로컬 회전 누적**(차분 아님) 두 축 = Strength·(0.3+0.7u) + Flutter·u^Stiff·진행파, Cross 옆 파, Randomness 위상 흔들기, k0=12/n 정규화, 1/(1-0.7q) 보정, **Damped Track 끝 따라가기**가 결과를 깎는다 → 숫자만 옮기면 다른 그림(누적 280~430도).
- 프리셋 Slow Flow / Breeze / Fast Flutter × 옵션 2 + Mix(선형). Random · Stiff 전부 0, Cross 는 Fast 옵션1 만 0.33. 속도 = 0.13·s rad/frame(24fps) — 마야는 Hz 로.
- 원본 Mix 는 UI 콜백이라 재생 중 키 X, 속도는 프레임×속도라 바꾸면 위상이 튐 → 마야 노드 + 위상 적분이 우위.
- 권장: 새 `Flow` 모드(Lite 수정 X), **V03**(위상 엔진) — 사용자는 V02 라고 했다(결정 1).
- 블렌더 4.0.2(Steam) 헤드리스 골든 추출은 외부 코드 실행이라 자동 권한 검사에서 거부 — 승인 받기 전 우회 금지. 스크립트 `docs/plans/A00390_wavesgen_blender_probe.py`.

**Why:** 사용자가 Waves Gen 의 프리셋 · 실시간 속성을 내 바람 툴에 넣고 싶어 함.
**How to apply:** 결정 받은 뒤 계획서 §6 단계 1(순수 모델 + 골든 대조)부터. 관련 [[wip-a00390-windtool]] · [[wip-a00390-v02-envelope]].
