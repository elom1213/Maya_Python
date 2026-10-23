---
name: wip-a00560-jalibatch
description: "A00560_JaliBatch(standalone, wav N개 → JALI 컨트롤러 레퍼런스 + 베이크 클립 .mb) · A00570_JaliReview(in-Maya 검수) — 2026-10-23 계획서만 작성, 코드 전. 핵심 판정: 레퍼런스된 animCurve 편집은 검수 씬 편집으로 쌓여 file -saveReference 없이는 클립이 안 바뀜, 같은 이름이라 교체 때 전파 → Swap 앞 편집 검사. M0 실측 8항목 먼저"
metadata:
  node_type: memory
  type: project
  originSessionId: 798f0898-035e-4b92-917a-642be0114c7a
  modified: 2026-10-23T06:39:52.997Z
---

**2026-10-23 — 계획 단계.** 사용자 용어: **JALI 툴** = `JUN_JALI`(VisemeNet 변환기 + MFA), **JALI 컨트롤러** =
`C:\Users\USER\Desktop\JP\0035_maya_src_rig\02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma`. 예시 자료
`JUN_JALI_Voice/0060_Vivian_voice/src_en`(wav + 대본 5쌍) · `out_en_002`(변환 결과 22열 txt · .visemenet.json · wav).

문서: `JUN_All/docs/plans/A00560_JaliBatch_pipeline_review.md`(계획 평가 · 개선 11개) · `A00560_JaliBatch_plan.md`(제작 계획 D1~D14, M0~M7, T1~T9, Q1~Q8).
사용자 요청: **A00540_JaliLipSync 코어를 참고 · 그대로 쓸 것** → 계획은 `Framework/jali/` 로 승격해 A00540 · A00560 워커 · A00570 이 공유(툴 간 import 금지 때문).

- 사용자 계획 = 클립 `.mb`(빈 씬 + 컨트롤러 레퍼런스 ns `JALI` + DUMMY_IN 키 → `bake_ctl_keys(copy)` 로 컨트롤러에 베이크) N 개, 검수 = 빈 씬 + 클립 레퍼런스(ns `CLIP`) + 아바타 레퍼런스, `CLIP:JALI:ARKIT_OUT.*` → 블렌드셰이프, 클립 교체는 `file -loadReference`. 뼈대는 유지.
- **틀어진 곳 (마야 레퍼런스 동작)**: ① 레퍼런스된 animCurve 키 수정("Allow edits on referenced animation curves")은 **검수 씬의 레퍼런스 편집**으로 쌓인다 — 클립 파일은 Reference Editor **Save Reference Edits** (`cmds.file(saveReference=True, referenceNode=…)`) 를 해야 바뀐다. ② 편집은 노드 이름 기준이고 모든 클립의 컨트롤러 · 커브 이름이 같으므로 **저장 안 한 편집이 교체 뒤 다음 클립에 적용**될 것으로 예상 → Swap 은 편집 0건일 때만(Save/Discard/Cancel). 둘 다 **M0 실측으로 확정할 것**(계획서 §6 M0-1 ~ M0-4, 아직 안 함).
- 파일 이름 `_f0105_0429` = 원본 영상 **30fps 프레임 구간**(클립 01 wav 10.80 s × 30 = 324 = 429 − 105) → 시작 프레임 기본 Filename, fps 기본 ntsc 30 을 **컨트롤러 레퍼런스 전에** 설정(mayapy 새 씬 · 컨트롤러 .ma 는 film 24, A00540 keyer 는 씬 fps 샘플).
- `bake_ctl_keys(mode='copy')` 는 DUMMY_IN → CTL 연결을 끊고 키를 복사하지만 DUMMY_IN 커브는 남긴다 → 클립에선 삭제. 커브 이름 `JALI_<ctl>_<attr>`.
- 공용 승격 계획(P0): `Framework/jali/`(keyer · mapping · lipsync_data · sequence · bake · mappings) · `Framework/core/mayapy_runner.py` · `Framework/qt/MOD_mayapyProcess_qt_v01.py`(A00210 `app/maya` 에서) — A00540 tests 132 · A00210 워커 시험 그대로 통과가 완료 조건.
- 변환(TensorFlow .venv · MFA) 은 1단계에서 호출하지 않는다 — 변환기 출력 폴더가 입력. 2단계 P4 = JUN_JALI `cli.py`(`converter.run_batch` 헤드리스).
- Bash 툴 heredoc 으로 긴 마크다운을 쓰면 "unexpected EOF" 로 깨진다(이 세션 2회) → 문서는 Write 도구로, 치환 스크립트는 scratchpad .py 로.

관련: [[wip-a00540-jalilipsync]], [[wip-jali-slider-ctl]], [[wip-a00210-maya-reference-tab]], [[maya-reference-import-traps]], [[release-layout-launch-py]], [[jun-jali-repo]]
