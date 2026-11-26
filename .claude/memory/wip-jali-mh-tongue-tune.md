---
name: wip-jali-mh-tongue-tune
description: "메타휴먼 JALI 리그 혀 조절 더미 JALI_TONGUE_TUNE 계획(2026-11-26, JUN_All/docs/plans/JALI_MH_TongueTune_plan.md, 구현 전 · 작업은 Maya_Python JUN_All 세션) - Brant 한국어 대사 혀 밑면 보임의 원인 3개 실측. 핵심 발견 = A00540 매핑이 COARTIC 에 음소와 같은 txt 열을 넣어 혀끝 올림이 1.61배"
metadata:
  node_type: memory
  type: project
  originSessionId: 29d3a330-6a45-48b1-b9aa-6d8535617271
  modified: 2026-11-26T01:53:30.298Z
---

계획서 `Maya_Python/JUN_All/docs/plans/JALI_MH_TongueTune_plan.md` (2026-11-26). 처음 JUN_JALI `docs/0150` 으로 썼다가 같은 날 사용자 지시로 이 자리로 옮김(JUN_JALI 에서는 삭제).
**이 작업은 Maya_Python `JUN_All` 세션에서 진행한다**(사용자 지시 2026-11-26). 사용자가 방법 2(rig 그룹 안 실시간 조절 더미)를 선택, Q1~Q5 "권장대로".
- **구현 · mayapy 검증 완료 (2026-11-26)**: `0010_sample_0060_JaLiTongue.mb` 생성, check 37 항목 OK(중립값 = 0050 과 1e-6 동일, 입술/턱 무변, 순환 없음, A00540 호환).
  Brant 복사본 `JUN_JALI/out/0150/0010_Metahuman_01_tune.mb` 에서 문제 구간 tipUp 최대 0.561 → 0.211. **사용자 GUI 확인(S7) 대기** — 값 조절 결과를 받으면 ATTRS 권장 기본을 바꿔 재생성(S8).
- 함정: 효과 예측 때 `coarticWeight` 가 `CO.GK → tongueTipDown` 도 줄이는 걸 빼서 110 프레임 예측 0.11 vs 실측 0.122 — 혀끝 순값(올림 − 내림)은 양쪽을 다 계산할 것.
대상 리그 `C:\JUN\JUN_Src_Rig\07_MH_sample_02\0010_sample_0050_JaLiMap.mb` → 결과 `0010_sample_0060_JaLiTongue.mb`, 스크립트 `JUN_JALI/examples/build_mh_jali_tongue_tune.py` · `check_…`.
관찰 씬 `D:\D__1010_PortFolio\00010_JALI_Brant\0010_Metahuman_01.mb` (30 fps, 레퍼런스 `oldRN` ns `MH`, 키는 `MH:DUMMY_IN_*` 23개).

- **원인 C1 (중요)**: A00540 `jali_slider_dummy_in.json` 이 `DUMMY_IN_COARTIC.LNTD/GK/MMM/FFF` 를 음소와 **같은 열**(LNTD GK MBP FV)에서 채운다 → 모든 프레임에서 CO == PH.
  0110 은 CO 를 별개 신호로 보고 `CO.LNTD` 1.00 을 줬으므로 혀끝 올림이 0.61 + 1.00 = 1.61 배, 대표 프레임 tipUp 의 50~64 % 가 중복 몫. 입술 쪽 `CO.MMM` · `CO.FFF` 도 같은 구조(사용자는 입술 "무난" 이라 미수정).
- C2 `RRR` → tipUp 0.63 은 영어 권설음 값(한국어 ㄹ 은 탄설). C3 입 벌림과 혀끝 올림이 같은 프레임에 겹침 → 설계에 `jawOpenSuppress`(CTRL_expressions.jawOpen 기반).
- 리그 식 `clamp((Σw·x)·Jaw/0.6,0,1) − tipDown` 으로 781 프레임 재계산 오차 0 → 권장값(coartic 0.3 · rrr 0.4 · suppress 0.6/ref 0.4) 효과 계산: 문제 구간 tipUp max 0.56 → 0.21.
- 같은 현상이 지정 구간 밖(286 · 361 · 531 · 575 · 666~685)에도 있다.

관련: [[wip-a00540-jalilipsync]], [[jun-jali-repo]], [[wip-jali-slider-ctl]], [[mayapy-headless-verify]]
