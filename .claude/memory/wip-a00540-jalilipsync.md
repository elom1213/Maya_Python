---
name: wip-a00540-jalilipsync
description: "A00540_JaliLipSync v01.00 (2026-10-19) — VisemeNet txt(+json) · wav -> JALI 리그 키 (씬 fps 샘플, 매핑 json, JaLi 데이터/고정, Undo 한 번). 짝 = JUN_JALI 변환기. 원본 VisemeNet 은 추론도 무작위(net2 dropout 상수) · 출력이 끝 0.32초 짧다"
metadata:
  type: project
---

`A00540_JaliLipSync` **v01.00** (2026-10-19) — 계획서 `JUN_JALI/docs/0030_tool_plan.md` T3. 짝 저장소 [[jun-jali-repo]] 의
스탠드얼론 `VisemeNet Converter` 가 만든 `<이름>.txt`(100fps × 22열) + `<이름>.visemenet.json` 을 JALI 리그
(`angela_JALI.ma`: `CNT_JaLi.tx/ty` · `CNT_PHONEMES` · `CNT_COARTIC`)에 키로. TensorFlow 불필요(txt 만 읽음).

- 코어: `lipsync_data`(22열 검증 · json 검증 · `find_wav` = json source_wav → 같은 이름) · `mapping`(app/mappings/*.json,
  combine max/sum/avg, role "jali") · `keyer`(씬 fps 로 샘플 `round(f/fps*100)`, 구간 cutKey 후 setKeyframe, undo_chunk,
  잠김 · 비 animCurve 연결이면 아무것도 안 함) · `scene`(CNT_PHONEMES 네임스페이스 찾기, 사운드 노드 + GUI 면 타임슬라이더).
- **원본 VisemeNet 의 숨은 성질 2개 (실측)**: ① `model.py` 가 net2 LSTM 7개에 `DropoutWrapper(output_keep_prob=0.5)` 를
  **상수로** 넣어 추론도 무작위(같은 wav 최대 차 0.64) → 변환기 `Engine(deterministic=True)` 가 frozen 그래프의
  `*dropout/keep_prob` Const 를 1.0 으로 바꿔 불러온다(inference.py 무수정). ② 출력 줄 수 = `(mfcc 프레임 // 4) * 4 - 32`
  — 끝 0.32초가 빠지고 **시작은 맞다**(net2 64줄 창 · 앞 32줄 0 패딩).
- 검증: mayapy 2024 코어 19 (레퍼런스 리그 `angela:` 포함) + 오프스크린 UI 15. **마야 GUI 드롭 설치 · 소리 재생은 사용자 확인 전.**
- 테스트 함정: 비짐 배율 시험에서 "최댓값이 10 을 넘는다" 를 가정했다가 틀렸다(데이터 최댓값 < 1) — `keyer.sample()` 로 기대값을 계산할 것.

- **v01.01 계획서** `JUN_All/docs/plans/A00540_JaliLipSync_v0101_rules_manual_plan.md` (2026-10-22, 착수 전): 매핑 json v2(`nodes` 역할표 · `viseme_scale` · `jali{scale,range,fixed_default}`), Target Auto/Manual(역할 3칸, 빈 역할 건너뜀), JaLi scale 스핀박스, 매핑 바꾸면 스핀박스 리셋, scale > attr max 경고, `tests/` 신설. A0020 리그는 `CNT_JaLi` 휴식 0 + `DUMMY_IN_JALI` 기본 0.6 으로. A00550 Solo 는 `DUMMY_OUT` 에서 안 됨(`settable_plug` 가 유틸리티 output 에서 멈춤) → 별도.

관련: [[mayapy-headless-verify]], [[qapplication-before-maya-standalone]], [[new-tool-needs-icon]]
