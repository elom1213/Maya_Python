---
name: wip-a00390-wavesgen-port
description: A00390 V03 v03.04 Flow 탭 = 블렌더 Waves Gen 바람(프리셋 3x2 · Mix · 끝 따라가기) 마야 노드 이식, 블렌더 골든 12/12 (2026-11-05, 사용자 GUI 확인 OK)
metadata:
  type: project
---

2026-11-05 계획서 `JUN_All/docs/plans/A00390_WindTool_wavesgen_port_plan.md` (**V03 v03.04 구현 완료 2026-11-05, 사용자 GUI 확인 OK "잘 된다"** — 결정: V03 · 끝 따라가기까지 · Mix · 개인용 · 블렌더 실행 허가).

- 원본 `C:\Users\USER\Desktop\JP\0120_blender_plugin\0010_waveGen\__init__.py` (1,052줄), **GPL-3.0** → 코드 · 드라이버 식 복사 금지, 수식을 독립 구현 + 프리셋 출처 표기.
- 원본 모델: 뼈마다 **로컬 회전 누적**(차분 아님) 두 축 = Strength·(0.3+0.7u) + Flutter·u^Stiff·진행파, Cross 옆 파, Randomness 위상 흔들기, k0=12/n 정규화, 1/(1-0.7q) 보정, **Damped Track 끝 따라가기**가 결과를 깎는다 → 숫자만 옮기면 다른 그림(누적 280~430도).
- 프리셋 Slow Flow / Breeze / Fast Flutter × 옵션 2 + Mix(선형). Random · Stiff 전부 0, Cross 는 Fast 옵션1 만 0.33. 속도 = 0.13·s rad/frame(24fps) — 마야는 Hz 로.
- 원본 Mix 는 UI 콜백이라 재생 중 키 X, 속도는 프레임×속도라 바꾸면 위상이 튐 → 마야 노드 + 위상 적분이 우위.
- 권장: 새 `Flow` 모드(Lite 수정 X), **V03**(위상 엔진) — 사용자는 V02 라고 했다(결정 1).
- 블렌더 4.0.2(Steam) 헤드리스 골든 추출은 외부 코드 실행이라 자동 권한 검사에서 거부 — 승인 받기 전 우회 금지. 스크립트 `docs/plans/A00390_wavesgen_blender_probe.py`.

**Why:** 사용자가 Waves Gen 의 프리셋 · 실시간 속성을 내 바람 툴에 넣고 싶어 함.
**How to apply:** 결정 받은 뒤 계획서 §6 단계 1(순수 모델 + 골든 대조)부터. 관련 [[wip-a00390-windtool]] · [[wip-a00390-v02-envelope]].
- **구현(v03.04)**: `app/core/flow_model.py`(순수) · `flow_presets.py` · `flow_manager.py` · `app/ui/flow_tab.py`, 시험 golden 12 · maya 28 · UI 16, `tests/perf_flow.py`.
  - 골든: Blender 4.0.2 헤드리스로 애드온 실행 OK(사용자 허가) → `tests/data/wavesgen_golden.json`. 블렌더 행렬은 축 길이가 1 에서 살짝 벗어난다 → 비교 전 정규화.
  - sin = `eulerToQuat(rotateX=2θ).outputQuatX`(정확), 각도 입력은 unitConversion π/180 을 직접 만든다. quatProd(a,b) = a 다음 b. angleBetween→axisAngleToQuat = v1→v2.
  - ★ 뼈 축은 **연결 전에** 전부 구할 것(루프 안에서 구하면 앞 뼈 회전이 섞인다). blendTwoAttr 는 float 정밀도.
  - 위상 엔진 `flowPhaseEngine` 상시(키 사이 직선 → W·(SA+(SB−SA)M) 3차 → Simpson 정확), 어트리뷰트 직접 참조라 멈춘 상태에서도 갱신. 툴이 찍는 키는 linear.
