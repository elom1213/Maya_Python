---
name: wip-a00640-attrslider
description: "A00640_AttrSlider — 선택 노드의 채널박스 어트리뷰트 · blendShape 타겟을 슬라이더로, FBXASC 풀기 (v01.00, 2026-11-20, GUI 확인 아직)"
metadata:
  type: project
---

`A00640_AttrSlider` v01.00 (2026-11-20) — liteDriver(A00390 V03) 어트리뷰트 조절 요청에서 시작한 in-Maya PySide 툴.
A00620 에 탭으로 넣지 않은 이유: A00620 = 읽기 전용 이름 해독, A00145 = 무거운 리깅 창. **슬라이더 기능 요청은 이 툴로.**

- **범위 규칙 순서: 사용자(어트리뷰트 이름 기준 optionVar) > 소프트 > 하드 > 최소만 > 자동.**
  ★ 소프트를 하드보다 먼저: blendShape weight 는 하드 -10~10 + 소프트 0~1 을 둘 다 가진다(하드 먼저면 -10~10 슬라이더).
- 상태 실측(mayapy): animCurveT* · animBlendNode* 소스 = setAttr 되지만 시간 이동 시 복귀 → Keyed(분홍) · `Auto Key`.
  ★ 드리븐 키 animCurveU* = setAttr 가 **에러 없이** 들어가고 곧 덮어씀 → Driven(비활성). 일반 연결 · 잠금 = 에러.
- ★ FBXASC 이름의 어트리뷰트는 `attributeQuery(niceName)` 도 FBXASC 그대로 → long 이름을 `fbx_name.decode`.
- 드래그 = undoInfo open(sliderPressed)/close(sliderReleased), Auto Key 는 놓을 때 한 번. 숫자 칸 keyboardTracking 끔.
- 행은 새로 만들 때마다 `slider_style.apply()` (공용 sliderStyle 은 Show 때만 칠한다).
- 채널박스 판정 · enum 파싱은 A00145 와 같은 규칙을 복제(툴 간 import 금지) — Framework 합치기는 계획서 §6 3단계.
- 다음 단계(계획서 §6): 여러 노드 같은 어트리뷰트 한 슬라이더(Common), 즐겨찾기.
- 시험 `tests/test_attr_slider.py` 75. 시험 함정: mayapy 에 `undoInfo(flush=)` 는 없다 → `cmds.flushUndo()`. 로케이터를 고르면 셰이프 섹션도 나온다(정상).

관련: [[wip-a00620-namedecoder]], [[wip-a00390-windtool]], [[feedback-sliders-use-shared-style]], [[wip-a00145-set-value]]
