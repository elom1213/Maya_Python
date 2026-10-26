---
name: wip-a00560-jalibatch
description: "A00560_JaliBatch v01.00(standalone, 변환 결과 폴더 → JALI 클립 .mb N 개, mayapy 워커) · A00570_JaliReview v01.00(in-Maya 레퍼런스 검수: Swap · Save Clip Edits · ARKIT_OUT → BS) — 2026-10-26 제작 완료, 코어는 Framework/jali 공용. GUI 눈 확인 · exe 빌드 · P4(변환기 CLI) 아직"
metadata:
  type: project
---

**2026-10-26 완료 (사용자 답 Q1 두 개 · Q3 30fps + UI 수정 가능 · 나머지 권장안).** 계획서 `JUN_All/docs/plans/A00560_JaliBatch_plan.md`
(§10 진행표 · §11 M0 실측), 안내 `docs/A00560_JaliBatch.md` · `docs/A00570_JaliReview.md` · `docs/Framework_jali.md`.
용어: **JALI 툴** = `JUN_JALI`, **JALI 컨트롤러** = `0035_maya_src_rig\02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma`, **클립** = 대사 하나의 `.mb`.
예시 자료 `JUN_JALI_Voice/0060_Vivian_voice/out_en_002`(5 클립).

- **P0 공용 승격 (커밋 "refactor(Framework): jali · mayapy 승격")**: A00540 `app/core` 5 모듈 + `mappings/*.json` → `Framework/jali`(A00540 v01.03 은 얇은 재노출,
  tests 132 그대로), 새 `bake.py`(JUN_JALI `bake_ctl_keys` 이식 + cleanup_dummy_in · rename_curves) · `clip_stamp.py` · `time_units.py` · `clip_manifest.py`.
  A00210 `mayapy_runner` → `Framework/core`, `mayapy_process` → `Framework/qt/MOD_mayapyProcess_qt_v01`(`run_job(..., worker=경로)`), A00210 v01.40 재노출.
- **A00560 클립** = 빈 씬(fps 먼저!) + 컨트롤러 레퍼런스 ns `JALI` + `keyer.apply_sequence` → `bake(copy)` + DUMMY_IN 커브 삭제 + 커브 이름 `JALI_<ctl>_<attr>`
  + wav 복사 사운드 + fileInfo 도장 + `jali_clips.manifest.json`. 베이크 채널 24(슬라이더 22 + JaLi 2 — 매핑에 없는 coartic 하나는 bakeResults 로 평평하게).
  Start 는 전 클립 공통값 + 표에서 개별 수정(매니페스트에 저장), **파일 이름은 읽지 않는다**. 실패 클립은 다음 계속, 취소는 클립 경계. Skip/Overwrite/backup.
  Validate 탭(열기만: failedEdits · 베이크 채널 · DUMMY_IN 잔여 · 도장 mtime) + Repath(그때만 저장). 5 클립 5.5 s, .mb 50~150 KB.
- **A00570** = 빈 씬 + 아바타 레퍼런스 + 클립 레퍼런스 ns `CLIP`. Swap 은 **pending 0 일 때만**(아니면 Save/Discard/Cancel), Save Clip Edits = `cmds.file(<클립 경로>, saveReference=True)`,
  Discard = unload → `referenceEdit -removeEdits -onReferenceNode` → load. Connect 는 별칭 일치, 연결 편집은 **아바타 RN** 에 남아 교체 뒤에도 산다.
  Open Clip(임시 아바타 ns `REVIEW_AVATAR`) + Save Clip & Close. 재생 범위 · 상태는 매니페스트(레퍼런스된 클립의 fileInfo 는 안 보임).
- 마야 레퍼런스 편집의 함정(시각 24fps 환산 · onReferenceNode · refAnimCurvesEditable)은 [[maya-reference-fcurve-edit-traps]].
- 검증: A00560 core 33(python) · worker 32(실제 mayapy 하위 프로세스) · UI 30(PySide6 오프스크린 + 실제 mayapy 1회); A00570 core 33 · UI 24(mayapy 오프스크린).
- **남은 것**: 실제 화면 확인(두 창 · 셸프 드롭 · 타임슬라이더 소리 · 그래프 에디터 편집 흐름) · `build_exe.bat` 미실행 · **P4(2단계)** JUN_JALI `cli.py` 호출 + Convert 단계 안 함.
- 테스트 함정: `arkit_connect.plan` 은 연결 전에 계획을 다 세우므로 규칙으로 두 소스가 같은 타겟을 노리면 `claimed` 로 먼저 온 쪽만(안 그러면 force 가 덮는다).
  A00560 test_ui 에서 fake 워커가 Overwrite 로 다시 만들면 `edited` 가 `generated` 로 돌아간다(실제 워커와 같다).

관련: [[wip-a00540-jalilipsync]], [[wip-jali-slider-ctl]], [[wip-a00210-maya-reference-tab]], [[maya-reference-import-traps]], [[release-layout-launch-py]], [[jun-jali-repo]], [[no-filename-dependent-data]]
