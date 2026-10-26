---
name: wip-a00210-maya-export-tab
description: A00210 FileManager Maya > Export 하위탭 (계획만, 2026-10-26) - 마야 파일 N 개에서 세트 규칙(Bake) 솎아내기 · 타임라인/fps 진단 · bakeResults -> FBX (UE) · Export Only · 이름 삽입/치환 미리보기 · mayapy 워커 probe/export. 하드웨어 선택은 v2(병렬 워커)
metadata:
  type: project
---

**A00210_FileManager Maya 탭 > `Export` 하위탭 — 계획서만 작성 (2026-10-26, 코드 전).**
계획서 `docs/plans/A00210_FileManager_maya_export_plan.md` (§2 결정 D1~D18 · §3 json 형식 · §5 함수 · §6 UI · §8 M0 · §13 질문 Q1~Q9 · §14 진행표).

- 요청: 마야 파일 여러 개 → **규칙(세트 이름 `Bake`, 최상위든 다른 세트 안이든)** 이 있는 파일만 골라, 파일마다 **타임라인 min/max · fps · 버전** 표 →
  `Bake & Export`(세트 멤버 + 자손 T/R/S `bakeResults` → FBX, 아바타 루트 본 → UE, 30fps 6000 프레임급) / `Export Only` / 이름 **자리 삽입 + 찾기/바꾸기 + 미리보기**
  (`anim_01` → `anim_bake_01`) / 진행률 팝업 / 하드웨어 선택(미뤄도 됨 → **v2**).
- 권장 결정: 코드는 `app/maya/{core,ui}`(Reference 와 같은 분리 단위) · A00480 FBX 헬퍼 **`Framework/core/maya_fbx.py` 승격**(툴 간 import 금지) · 파일 고르기 `MayaFilePicker` · mayapy 칸은 MayaTab 공용 `MayapyBar` ·
  규칙 하나 = json 하나(`~/.jun_filemanager/export_rules/`, 폴더 변경 가능, A00340 select_rules 태도) · `Import References & Remove Namespaces` 기본 ON(레퍼런스 노드 베이크 = 편집 수만 개 · UE 본 이름 `CHN:`) ·
  `bakeResults(simulation=True, disableImplicitControl=True)` **한 호출**(안의 진행률은 못 보임 → 경과 시간 · 파일 경계 취소 · `cancel_grace_sec=1800`) · FBX 는 선택 내보내기 + `playbackOptions` = 범위 · **원본 마야 파일은 저장하지 않는다**.
- **하드웨어(R8)**: 조인트 베이크는 CPU 단일 스레드 DG 평가 → GPU 선택은 무의미. 실효 = mayapy 워커 N 개 병렬 + CPU 친화도(공용 러너 `run_jobs` 확장, 별도 계획서).
- 다음: 사용자 Q1~Q9 답 → **M0 실측**(FBX 네임스페이스 · bakeResults 6000 프레임 시간 · fileInfo version · FBX 타임스팬) → M1~M6.

**Why:** 요청이 길고 결정이 많아 계획서를 먼저 받기로 했다(사용자: "작업 계획서만 보고도 기능을 바로 만들 수 있을 정도").
**How to apply:** 구현 세션은 계획서 §14 진행표와 `git log` 로 이어 간다. 관련: [[wip-a00210-maya-reference-tab]] · [[fbx-export-selected-scope]] · [[mayapy-headless-verify]] · [[wip-a00560-jalibatch]] · [[release-layout-launch-py]]
