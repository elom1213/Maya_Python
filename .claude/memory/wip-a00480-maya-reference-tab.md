---
name: wip-a00480-maya-reference-tab
description: A00480 FileTool Maya 탭 > Reference (v01.10) — 마야 파일들의 레퍼런스를 트리로 보고 체크한 것을 각 파일에 임포트해 제자리 저장. 공용 폴더 트리(A00240 Tree 승격) · app/maya 폴더째 분리 가능
metadata:
  node_type: memory
  type: project
  originSessionId: 9851bc3c-33e0-43d3-9d39-fe7b39c172be
  modified: 2026-10-12T01:59:01.004Z
---

**A00480_FileTool v01.10 (2026-10-12) — Maya 탭, 첫 하위탭 Reference.** 계획서
`docs/plans/A00480_FileTool_maya_tab_reference_plan.md` (§12 사용자 결정표, §13 진행표).

- **코드 배치**: `tools/A00480_FileTool/app/maya/{core,ui}` 한 폴더. 폴더 밖 import 는 Framework 뿐, 안에서는
  상대 import 만 — 사용자가 "나중에 독립 툴로 뗄지도 모른다" 고 했기 때문. 뗄 때는 폴더를 새 툴의 `app/` 으로
  복사하고 launch.py · main_window 만 새로 쓴다. 다음 하위탭은 `maya_tab.py` 에 `addTab` 한 줄.
- **마야 파일 고르기** = 공용 폴더 트리 `JUN_mod_fileTree_qt_v01(checkable_files=True, default_types=("ma","mb","fbx"))`
  — A00240 Tree 탭을 Framework 로 승격(A00240 v01.20, re-export). 트리 체크 다중 전파는 공용 `JUN_mod_checkTree_qt_v01`.
  Reveal / Copy file path 메뉴는 공용 `Framework/qt/path_context.py`.
- **Maya File** = 공용 TSL(`attach_uuids=False`, Up/Down/Sort 끔 — 재정렬이 UUID 역할만 옮겨 UserRole 의 경로를 잃는다).
  행 텍스트 = 파일명(같은 이름이면 `name  (폴더)`), UserRole = 절대경로.
- **Reference 트리** = QTreeWidget(Reference | Used by). 최상위 = 직접 레퍼런스(경로 중복 제거) + 체크박스,
  자식 = 중첩(체크 없음 — 부모를 임포트하면 자동으로 같이), 기본 전부 접힘, 끊긴 경로 빨강 · 체크 불가.
- **옵션 기본 ON**: Remove All Namespace(씬의 모든 네임스페이스 병합, 남는 레퍼런스 것은 건너뜀) · Backup
  (A00220 과 같은 `backup/` 폴더, `<이름>_REF_NN` 으로 구분, log.txt 한 줄) · Reopen current scene.
- **Import 대상** = 마지막 Get Reference 로 스캔한 파일들 × 체크된 레퍼런스. 실행 전 확인 팝업(파일 ← 레퍼런스 목록).
  현재 씬이 수정돼 있으면 Save / Don't Save / Cancel.
- 사용 형태(사용자): 마야를 이 작업을 위해 띄워 여러 파일을 한 번에 처리하고 같은 파일에 덮어쓴다.
- 검증: mayapy 2024 샘플 41 + 실제 파일 2개(복사본, 스캔 10s · 임포트 17s) · 오프스크린 UI 24. **마야 GUI 확인 아직.**
- 테스트용 실제 파일(원본 수정 금지, 복사해서): `D:\D__02.Art\D__Asset\D__Character\D__CHN_Set_008\JP__Ctl\JP__Revision_0010_Defualt\0010_CHN_Ctl_Set008_0030.mb`,
  `D:\...\D__DHA_Set_008\JP__Ctl\JP__Revision_0010_Defualt\0010_DHA_Ctl_Set008_0020.mb`.

마야 동작 함정은 [[maya-reference-import-traps]]. 관련: [[wip-a00480-filetool]], [[release-layout-launch-py]](툴 간 import 금지의 이유),
[[qtreewidgetitem-checkable-default-flag]].
