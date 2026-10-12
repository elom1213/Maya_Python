---
name: wip-a00210-maya-reference-tab
description: A00210 FileManager Maya 탭 > Reference (v01.35) — 마야 파일들의 레퍼런스를 트리로 보고 체크한 것을 각 파일에 임포트해 제자리 저장. standalone 이라 마야 일은 mayapy 워커(QProcess). 처음 A00480 에 만들었다가 사용자 정정으로 옮김 · app/maya 폴더째 분리 가능
metadata:
  node_type: memory
  type: project
  originSessionId: 9851bc3c-33e0-43d3-9d39-fe7b39c172be
  modified: 2026-10-12T02:21:22.824Z
---

**A00210_FileManager v01.35 (2026-10-12) — Maya 탭, 첫 하위탭 Reference.** 계획서
`docs/plans/A00210_FileManager_maya_reference_plan.md` (§12 사용자 결정표, §13 진행표, §14 A00210 이식).

- **사용자가 처음 A00480_FileTool 에 요청했다가 "실수였다, A00210 으로" 라고 바꿨다** (2026-10-12). A00480 은 v01.09
  원상복구(새 커밋으로, 재작성 없음). 다시 A00480 쪽에 비슷한 요청이 와도 이 이력을 먼저 짚을 것.
- **A00210 은 마야 밖 standalone** → maya.cmds 가 필요한 일(.mb 읽기 · 임포트)은 `core/maya_worker.py` 를 **mayapy.exe 로
  띄워**(`ui/mayapy_process.py` QProcess + 진행률 팝업) 한다. stdout `JUNMSG {json}` 프로토콜(log / progress / result / error),
  결과는 job 폴더의 result.json, Cancel 은 플래그 파일(워커가 파일 경계에서 멈춤) → 120초 뒤 kill.
  `.ma` 만이면 머리글 파싱으로 이 프로세스에서 바로(`scan(allow_open=False)` → `.mb` 를 만나면 `needs_maya`).
- mayapy 경로: 칸 + Browse / Detect(`Program Files\Autodesk\Maya*\bin\mayapy.exe`, 새 버전 먼저). **A00210 prefs 프로파일의
  `mayapy_path`** 에 저장(비면 자동 탐색). 얼린 exe 는 `launch.spec` datas 로 `app/maya/core` 를 통째로 싣는다(워커가 디스크 .py 를 읽어야).
- **코드 배치**: `tools/A00210_FileManager/app/maya/{core,ui}` 한 폴더. 밖 import 는 Framework + prefs 뿐, 안은 상대 import
  (워커용 평범한 import 폴백). 뗄 때는 폴더를 새 툴의 `app/` 으로. 다음 하위탭은 `maya_tab.py` 에 `addTab` 한 줄.
- **마야 파일 고르기** = 공용 폴더 트리 `JUN_mod_fileTree_qt_v01(checkable_files=True, default_types=("ma","mb","fbx"))`
  (A00240 Tree 탭을 Framework 로 승격, A00240 v01.20 re-export). 트리 다중 체크 = 공용 `JUN_mod_checkTree_qt_v01`.
  Reveal / Copy file path 메뉴 = 공용 `Framework/qt/path_context.py`.
- **Maya File** = 공용 TSL(`attach_uuids=False`, Up/Down/Sort 끔 — 재정렬이 UUID 역할만 옮겨 UserRole 의 경로를 잃는다).
- **Reference 트리** = QTreeWidget(Reference | Used by). 최상위 = 직접 레퍼런스(경로 중복 제거) + 체크박스, 자식 = 중첩(체크 없음,
  부모와 함께 임포트), 기본 접힘, 끊긴 경로 빨강 · 체크 불가.
- **옵션 기본 ON**: Remove All Namespace(남는 레퍼런스 것은 건너뜀) · Backup(A00220 과 같은 `backup/`, `<이름>_REF_NN`).
  씬 보호(Reopen) 는 standalone 이라 없다.
- 검증: 실제 mayapy 워커 왕복 17 항목(스캔 · 임포트 · 재스캔 · 취소 · 에러), 오프스크린 UI(가짜 워커 = python) 14 항목,
  코어는 A00480 시절 mayapy 41 + 실제 파일 2개. **A00210 GUI 에서 실제 mayapy 로 돌려 본 것은 아직.**
- 테스트용 실제 파일(원본 수정 금지, 복사해서): `D:\D__02.Art\D__Asset\D__Character\D__CHN_Set_008\JP__Ctl\JP__Revision_0010_Defualt\0010_CHN_Ctl_Set008_0030.mb`,
  `D:\...\D__DHA_Set_008\JP__Ctl\JP__Revision_0010_Defualt\0010_DHA_Ctl_Set008_0020.mb`.

마야 동작 함정은 [[maya-reference-import-traps]]. 관련: [[release-layout-launch-py]](툴 간 import 금지의 이유),
[[qtreewidgetitem-checkable-default-flag]], [[wip-a00480-filetool]].
