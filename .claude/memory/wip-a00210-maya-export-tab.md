---
name: wip-a00210-maya-export-tab
description: A00210 FileManager v01.41 Maya > Export 하위탭 (2026-10-26 구현 완료, 사용자 실기 · UE 확인 대기) - 세트 규칙(json 하나) 솎아내기 · 재생 범위/fps/버전 · bakeResults 한 호출 → FBX · 최상위 본 월드 이동 두 단계 · 레퍼런스 임포트 + ns 제거 기본 ON · Overwrite 팝업 · mayapy 워커 probe/export · 하드웨어 선택은 v2
metadata:
  type: project
---

**A00210_FileManager v01.41 (2026-10-26) — Maya 탭 > `Export` 하위탭 구현 완료.** 계획서 `docs/plans/A00210_FileManager_maya_export_plan.md`
(§2 D1~D18 · §13 사용자 답 · §14 진행표 · §15 M0 실측), 사용 안내 `docs/A00210_FileManager.md` §4-E.

- 흐름: 파일 담기(공용 `MayaFilePicker`) → 규칙(`set_rules`, json 하나 = 규칙 하나, `~/.jun_filemanager/export_rules/` 또는 지정 폴더) →
  `Check Sets`(워커 `probe`: 세트 유무 · playback · fps · fileInfo version) → Range · Naming(Find/Replace → Insert Token/Char, 기본 `bake` 첫 토큰) →
  `Bake & Export` / `Export Only`(워커 `export`). **원본 마야 파일은 저장하지 않는다.**
- 사용자 결정: 레퍼런스 임포트 + ns 제거 **기본 ON**(FBX 가 `CHN:root` 를 남긴다, 실측) · Joints Only ON · **최상위 본이 그룹의 자식이면 마야 최상위로**
  (두 단계: 월드 로케이터 constraint + 베이크 → `parent -w` → 키 · 입력 비우고 로케이터에 constraint → 루트 재베이크; 1e-13 동치, 단순 unparent 는 틀림) ·
  기존 FBX 는 경고 팝업 **Overwrite / Cancel**(Existing 콤보 없음) · 하드웨어 선택은 **v2**(mayapy 병렬 + 친화도, GPU 는 무관).
- 함정(실측): `executeScriptNodes=False` 로 열면 `playbackOptions -q` 가 **이전 씬 값(단위 환산)** → `sceneConfigurationScriptNode.before` 문장 파싱 ·
  FBX 익스포터는 `.fbx` 아닌 이름에 `.fbx` 를 덧붙인다(임시는 `<stem>__part.fbx`) · `FBXExportBakeComplexAnimation -q` 는 문자열 'false' ·
  키 있는 채널엔 scaleConstraint 가 안 붙는다 · `bakeResults(simulation=True)` 가 False 보다 빠르다(78 × 6000 = 41 s).
- 공용화: `Framework/core/maya_fbx.py`(A00480 재노출) · `MayapyBar` 는 Maya 탭 아래 하나 · 워커는 Framework 를 import(spec datas) · `mayapy_process.run_job(cancel_grace_sec=1800)`.
- 검증: tests/test_export_core 50 · test_export_worker 31(실제 워커 프로세스) · test_export_ui 32(오프스크린). **실제 애니 파일 · UE 임포트는 사용자 확인 대기(Q9).**
- 같은 날 다른 세션이 A00560_JaliBatch 를 고치고 있었다 — A00560 경로는 손대지 않았고 커밋에도 넣지 않았다.

**Why:** 아바타 루트 본을 세트에 넣고 전 본을 베이크해 언리얼로 보내는 일괄 작업. 사용자가 계획서 → 답 → 구현 순서를 택했다.
**How to apply:** 레이아웃 · 동작을 바꿀 땐 계획서 §2 결정표 ID 로 말하고 §14 를 갱신. 관련: [[wip-a00210-maya-reference-tab]] · [[fbx-export-selected-scope]] ·
[[mayapy-headless-verify]] · [[wip-a00560-jalibatch]] · [[release-layout-launch-py]]
