---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-11-09
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

**이 파일은 현재 월을 담는다.** 지난 달은 [`worklog/`](worklog/) 로 내려간다 —
파일 자체는 늘 이 경로에 있으므로 이 문서를 가리키는 링크는 깨지지 않는다.
트리거와 절차는 [`worklog/README.md`](worklog/README.md).

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 지난 달 보관

| 월 | 파일 | 작업일 |
|----|------|--------|
| 2026-10 | [`worklog/2026-10.md`](worklog/2026-10.md) | 14일 |
| 2026-09 | [`worklog/2026-09.md`](worklog/2026-09.md) | 16일 |
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-11-09 (오늘)

> [!summary] **A00610_PmxImporter v01.00 신규** - PMX(MMD)를 마야에 바로 임포트 (`docs/A00610_PmxImporter.md`) `#A00610_PmxImporter`
- 요청: 계획서대로 구현. 사용자 결정 — 이름은 PMX 고유 이름(못 쓰는 글자는 FBXASC) · 머티리얼 lambert · IK 본 기본 생성 · PMX 의 다른 데이터(물리 등)를 계획서에 정리.
- 구현: 파서(2.0/2.1, 강체 · 조인트까지) · 메시 하나(정점 순서 = PMX, 노멀 잠금, 추가 UV) · lambert + 텍스처(알파 → 투명도) · 조인트 436 · 스킨(SDEF/QDEF → DQ) · 지오메트리 없는 blendShape 52 · 리포트. Miyabi 1.4초.
- 실측으로 바뀐 것: 마야가 cp949 밖 글자 경로(`颜.png`)의 이미지를 못 읽음 → `maya_textures/` 에 FBXASC 이름으로 복사 · `.ma` 저장이 cp949 밖 글자를 `?` 로 깨뜨림 → 문자열 어트리뷰트는 ASCII(FBXASC / JSON 이스케이프) · undo 청크 하나로 임포트 전체가 되돌아감 → `Remove Last Import` 없음 · `getVertexNormal` 은 잠긴 노멀을 무시(시험은 face-vertex 로).
- 시험: core 61/61 · mayapy 60/60 — 기준 mb(CATS → FBX) 대비 위치 2.8e-5 cm · UV 0 · 면 전부 같음 · 모프 51개 1.1e-4 · 웨이트 = PMX · 포즈 변형 7.6e-6 · 저장 왕복. **GUI 확인 아직.**
- 계획서 갱신: §13 결정 기록, **§14 PMX 안의 데이터 전체**(강체 318 · 조인트 442 · 표시 프레임 14 · IK 4 · 부여 30 …), 부여 본 2차 방법.
- 번호: 다른 세션이 같은 A00610 으로 NameDecoder 계획을 먼저 커밋 → 그쪽이 A00620 으로 옮김. ToolLauncher `UTIL` > `File` 에 버튼.

> [!summary] **A00620_NameDecoder v01.00 신규** - FBXASC 이름을 원래 글자로 읽는 툴 (`docs/A00620_NameDecoder.md`) `#A00620_NameDecoder`
- 요청: FBX 로 들어온 일본어 · 중국어 · 띄어쓰기 이름이 `FBXASC227FBXASC129FBXASC130` 처럼 보인다 - 노드 · 블렌드셰이프 타겟 이름을 읽고 싶다. 새 툴 vs 기존 툴 판단 → 새 툴(계획서 §4).
- 실측: 마야는 유니코드 이름을 못 받는다(rename · aliasAttr 에러, OpenMaya setName 은 조용히 무시). **FBX 익스포터는 FBXASC 를 원래 글자로 되돌려 쓴다** → 기본은 읽기 전용, ASCII 이름 바꾸기는 숨긴 선택 기능 + Restore.
- Names(스캔 · 풀린 글자 검색 · 선택 · Sync · 복사 · csv/json) · Blend Shapes(풀린 이름 + 슬라이더) · Rename to ASCII(번역표 → Preview → Apply, 원래 이름은 network 노드에).
- 공용 `Framework/core/fbx_name.py`(인코딩 · 디코딩) · `maya_fbx_names.py`(씬 스캔). **임포터는 맨 앞 숫자도 FBXASC 로 바꾼다**(`1abc` → `FBXASC049abc`, 실측) → `fbx_binary.maya_node_name` 을 공용 인코더로 바꿔 바로잡음(A00480 test_fbx_core 40/40 · test_fbx_exact 25/25).
- 번호: 처음 A00610 으로 계획했으나 다른 세션 `A00610_PmxImporter` 와 겹쳐(드롭 파일 `__dragDrop_A00610.py` 이름 충돌) A00620 으로 옮김.
- 시험 61/61 (예시 `0010_Miyabi_base_02.mb` 노드 149 · 타겟 52 포함). 마야 GUI 확인 아직(일본어 글꼴).

> [!summary] **A00610_PmxImporter 계획서** (`docs/plans/A00610_PmxImporter_plan.md`) `#A00610_PmxImporter`
- 요청: PMX(MMD)를 마야에 바로 임포트 - 스킨 메시 · 본 · 블렌드셰이프 · 머티리얼 · 텍스처까지. 지금은 CATS(블렌더) → FBX → 마야 손질로 하는 중.
- 실측: Miyabi.pmx(정점 27,086 · 재질 23 · 본 436 · 버텍스 모프 52 · 추가 UV 2) 를 기준 mb(`0010_Miyabi_base_02.mb`)와 대조 -
  위치 `(x, y, -z) × 8` 오차 2.8e-5 · UV `(u, 1-v)` 0 · 면 감기 `(c, b, a)` · 모프 델타 6.2e-5. 텍스처 `颜` · `髮` · `内` 는 RGBA(기준 mb 는 투명도 연결 없음).
- 계획: PMX 규격 요약 · 이름 규칙(CATS 호환 본 이름 + 모델별 이름 맵 JSON) · 재질/알파 · 스킨(물리 인덱스 한 번에) · 지오메트리 없는 blendShape 입력 · 골든 대조 G1~G12 · M0~M9.
  IK · 부여(付与) · 물리는 데이터만 보존하고 2차. 프로브 스크립트 3개를 계획서 옆에 둠.

> [!summary] A00400_CurveTool **v01.32 Create > From Hair** `#A00400_CurveTool`
- 요청: Houdini `0010_hairShrink_LUN_01.hip` 의 foreach 루프(헤어 메시 가닥마다 커브)를 마야에서 — A00400 에 추가, 작은 메시 · 짧은 커브 거르기, Houdini 보다 빠르게.
- 분석: hip(ASCII cpio)을 풀고 hython 으로 쿡 — Labs `straight_skeleton_3d`(VDB 수축) 149 가닥 71.5 초, 커브 없음 3 · 조각 2. 입력은 전부 "뿌리 열린 쿼드 튜브 + 끝 팬". 계획서 `plans/A00400_CurveTool_hair_centerline_plan.md`.
- 구현: 열린 끝에서 링 BFS → 링 중심점(cv[0] = 뿌리), 불규칙 · 닫힌 메시는 측지 거리 구간. 필터 2종, Count / Spacing / Per Ring, Degree 1/3, Analyze, Select Skipped, Send to Joints(By parameter = 조인트가 CV 위).
- 실측 함정: 끝에 이웃 아닌 정점 2개 → 거짓 가지(최소 가지 길이로), 엣지만 따라 잰 거리는 둘레 경로를 과대평가 → 닫힌 튜브 끝이 극점 대신 링 정점(면 대각선 이웃으로).
- LUN 149 가닥: 커브 148 + 퇴화 1, 약 1.1 초, Houdini 결과와 편차 중앙값 0.11 cm. 시험 `test_hair_curve.py` 66/66, `test_ribbon.py` 75/75. **GUI 확인 아직.**

> [!summary] A00210_FileManager **v01.53 Sync Status 이름 순** `#A00210_FileManager`
- 요청: Sync / Status 의 경로 · 파일을 이름 순으로. 추적 제외(흐린 색)는 지금처럼 아래에 두되 그 안도 이름 순.
- 원인: 파일 줄은 비교 결과 순서, 폴더 줄은 처음 나온 파일 때 생긴 순서로 붙었다.
- 구현: 다 그린 뒤 `_sort_tree_items` 로 단계마다 정렬 — 추적 폴더 → 추적 파일 → 제외 폴더 → 제외 파일, 이름(대소문자 무시).
- 시험 UI 108/108(+2), core 65/65. **GUI 확인 아직.**

## 2026-11-06

> [!summary] A00480_FileTool **v01.21 Reference > Default `Replace...`** `#A00480_FileTool`
- 요청: Reference > Default 트리에서 고른 레퍼런스를 다른 파일로 교체.
- `Replace...` 버튼 + 우클릭 `Replace Reference...` — 파일 고르기 → 확인(undo 안 됨) → `file -loadReference` → 트리 다시 읽기. 여러 행 = 같은 파일.
- mayapy 실측: 네임스페이스 · 컨스트레인트 유지, 언로드는 `loadReferenceDepth none` 이면 언로드 그대로, **중첩 레퍼런스 교체는 저장 안 됨**(마야 경고) → 막지 않고 확인 창 · 로그로 알림. 부모 + 중첩을 같이 고르면 부모만.
- 시험 `test_reference_replace.py` 20/20, `test_reference.py` 47/47, `test_reference_lineage.py` 44/44. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.54 Match Follow 진행 팝업** `#A00110_animTool`
- 요청: Transfer > Follow 의 Match Follow 를 누르면 팝업으로 진행도를 보여 줄 것.
- 공용 `JUN_mod_progress_qt_v01` 사용. core `FollowMatchManager.match_follow(progress=None)` 콜백 — 단위 = 페어 × 프레임(Blend < 1 이면 원본 읽기까지 ×2), 세부 줄 `Follower k/N : 이름`, 로그에 경과 시간.
- 시험 `test_follow_progress.py` 13/13(총량 · 단조 증가 · 콜백 없이도 같음 · UI 팝업 열림/닫힘), `test_follow_point.py` 14/14. **GUI 확인 아직.**

> [!summary] A00390_WindTool_V03 **v03.06 Chain Wave Lite 에 Tip Follow** `#A00390_WindTool`
- 요청: Flow 의 Tip Follow(체인이 Tip 을 쫓는 기능)를 Chain Wave Lite 에서도 쓸 수 있게 이식.
- Flow 의 Tip 생성 · 따라가기 · 이득 블록을 `flow_manager.make_tip / tip_follow_quat / follow_gain` 으로 떼어 Flow · Lite 가 같은 코드를 쓴다(Flow 회귀 56/56 불변).
- Lite: `_apply_angle(quat_out=True)` 로 노드 회전을 쿼터니언으로 받아 slerp → quatToEuler → rotate. 드라이버 `windTipFollow`, Tip `*_liteTip`(루트의 부모 아래). UI `Tip Follow` 줄(기본 꺼짐).
- 시험 `test_lite_tip_follow.py` 24/24(follow 0 = 예전 Lite 위치 3e-14 · Tip 을 옮기면 끝이 따라감 · 리그 이동 · FK 체인 · 제거 · 굽기 · UI), Flutter 14/14. **GUI 확인 아직.**

> [!summary] A00210_FileManager **v01.52 Sync Status File Types** `#A00210_FileManager`
- 요청: Sync / Status 에도 File Manager 처럼 확장자별로 파일을 보는 기능.
- 구현: `Filter` 줄에 `File Types` 버튼(확장자 · 개수 체크 메뉴, All, 닫히지 않는 메뉴 공용화 `checkable_menu.py`), 끈 확장자 prefs `sync_types_off`.
- 시험: UI 106/106, File Manager 쪽 시험 통과.

> [!summary] A00210_FileManager **v01.51 Sync Status 빈 폴더 표시** `#A00210_FileManager`
- 요청: `1999_=== - 복사본` 같은 빈 폴더가 실제로 있는데 Status 트리에 안 보인다.
- 원인: 매니페스트가 파일만 적어 파일 없는 폴더는 트리에 생기지 않았다.
- 구현: 스캔이 가장 안쪽 빈 폴더를 `empty_dirs` 에 기록 → `sync_compare.empty_dirs` 로 PC 별 있음 / 없음(Empty folder · Missing · Only here), 위 폴더 상태에도 반영. 옛 매니페스트는 모름 처리.
- 실측: JUN_MUE 빈 폴더 181개(복사본 구분 폴더 5개 포함). 시험 core 65/65 · UI 96/96.

> [!summary] A00210_FileManager **v01.50 Sync PC 이름** `#A00210_FileManager`
- 요청: Sync / Status 에 `P4T7MBN` 같은 컴퓨터 이름 대신 직관적인 PC 이름을 붙이고 싶다(기존 기능 없음 → 새로).
- 구현: `PC Names...` 창(PC · 이름 · 스캔한 루트) → `_sync_settings.json` 의 `pc_names`(모든 PC 공유). 화면의 모든 PC 표기가 이름으로, 매니페스트 파일은 컴퓨터 이름 그대로.
- 시험: `test_sync_ui.py` 91/91, `test_sync_core.py` 57/57, 나머지 A00210 시험 통과.

## 2026-11-05

> [!summary] A00390_WindTool_V03 **v03.05 Chain Wave Lite 에 Flutter** `#A00390_WindTool`
- 요청: Flow(Waves Gen)의 Flutter 기능을 Lite 탭으로 이식.
- 구현: Lite 의 월드 각도 파형(차분) 위에, 같은 위상의 사인(노드별 LUT 재사용)을 로컬 회전에 그대로 더해 끝으로 누적 — `windFlutter`(도/뼈, 12뼈 기준) · `windFlutterStiffness`, 노드당 4개.
  기본 0 = 예전 Lite 와 diff 0, 체크 끄면 노드 없음.
- 시험: `test_lite_flutter.py` 14/14, Flow UI 16/16, tabFit 31툴 0 fail.

> [!summary] A00390_WindTool_V03 **v03.04 Flow 탭 — Waves Gen(블렌더) 바람 이식** `#A00390_WindTool`
- 요청: 계획서대로 V03 에, 끝 따라가기까지, Mix 포함(개인용, 블렌더 애드온 실행 허가).
- 블렌더 4.0.2 헤드리스로 애드온을 돌려 기준 데이터(12 경우 × 뼈 12 × 60 f) → 순수 모델 `flow_model` 12/12 → 마야 노드망 12/12(0.013% · 0.09도).
  노드망: sin 은 eulerToQuat(정확), 바람 = 두 축 쿼터니언, 끝 따라가기 = angleBetween 최소 회전 + quatSlerp. 위상 엔진 표현식 1개(키 걸린 speed · Mix · timeScale 을 Simpson 정확 적분, 역행 0).
  프리셋 3 × 옵션 2 → 드라이버 A/B + flowMix(blendTwoAttr, 키 가능), Live Edit, Key Mix, Load From Driver.
- 함정: 뼈 축을 연결 루프 안에서 구하면 앞 뼈 회전이 섞인다(블렌더 대조로 잡음) → 연결 전에 전부.
- 시험: golden 12 · maya 28 · UI 16, tabFit 31툴 0 fail, 재생 30체인 4.8 ms. **GUI 확인 아직.**
- ⚠️ 이 턴 첫 푸시에 다른 세션 커밋 `6aa97fb5`(A00600_SceneCleanup v01.00)가 함께 나갔다(확인 · 푸시를 한 줄로 실행) — 사용자 보고, 메모리 `push-check-outgoing-separately`.

> [!summary] **A00600_SceneCleanup v01.00 새 툴** — 체크한 항목대로 열린 씬 정리 `#A00600_SceneCleanup`
- 요청: 레이어 · 애니메이션 레이어 · 안 쓰는 머티리얼 제거를 체크박스(기본 모두 체크)로, 항목은 계속 늘어남. 기존 툴 대신 새 툴로 판단(A00480 = 파일 입출력, A00470 = 머티리얼만, A00210 = 마야 밖 일괄).
- 결정: 머티리얼 = **Hypershade Delete Unused Nodes 와 같게** → MEL `MLdeleteUnused` 그대로. 애니메이션 레이어 = **BaseAnimation 도 안 보이게** → 루트 삭제(홀로 남은 BaseAnimation 도).
- 구조: 공용 `Framework/core/maya_cleanup.py` + `cleanup_items.ITEMS`(항목 = 클래스 하나) + runner(undo 청크 하나, 항목 실패 격리, Layer Editor 갱신). 계획서 `plans/A00600_SceneCleanup_plan.md`.
- 실측: `MLdeleteUnused` 는 mayapy 에서 source 필요 · undo 한 번 복원 · 레퍼런스 애니메이션 레이어가 있으면 루트를 못 지움(경고).
- 시험 `test_scene_cleanup.py` 33/33(Hypershade 직접 호출과 지운 목록 대조 포함). ToolLauncher UTIL > Scene 에 버튼. **GUI 확인 아직.**

> [!summary] A00390_WindTool **Waves Gen(블렌더) 이식 계획서** (구현 전) `#A00390_WindTool`
- 요청: 무료 블렌더 애드온 Waves Gen(GPL-3.0) 분석 → 장점 · 보완점을 A00390 V02 에 이식, 바람 프리셋 3개를 그대로 옮길 수 있는지, 진폭 · 속도를 실시간으로 바꿀 수 있는지.
- 결론: 숫자만 옮기면 다른 그림(진폭 · 파장 · 속도의 뜻이 다름, 끝 따라가기 Damped Track 이 결과를 깎는 구조). Waves Gen 운동 모델(누적 두 축 회전 + 기울기 + 끝 따라가기)을 새 `Flow` 모드로 노드 구현하면 프리셋을 같은 뜻으로 이식 가능.
  실시간은 노드라 전부 키 가능 — Mix 까지 키로(원본은 UI 콜백). 속도 키 · Mix 키는 위상 적분 필요 → V03 위상 엔진(V02 는 느린 표현식) → V03 권장. 코드 복사 금지(GPL), 수식 독립 구현 + 출처 표기.
- 블렌더 4.0.2 헤드리스 기준 데이터 추출은 외부 코드 실행이라 자동 권한 검사에서 막힘 → 승인 대기(측정 스크립트는 계획서 옆).
- 문서: [`plans/A00390_WindTool_wavesgen_port_plan.md`](plans/A00390_WindTool_wavesgen_port_plan.md)

> [!summary] A00210_FileManager **v01.49 Sync 트리 다듬기** + Framework **tabFit 중첩 탭 보정 수정** `#A00210_FileManager` `#Framework`
- 요청: Status 트리 처음엔 접힘 · `Show` 의 OK · Excluded 기본 체크 · 상위 폴더에서 하위 파일 상태(재귀) · 색(Missing 연한 빨강 / Outdated 노랑 / Conflict 하늘 / OK 초록) · Excluded 에 체크 트리 · Status 창 세로 2.2 배.
- 구현: Status 열을 경로 옆으로, 폴더 줄 = 아래 **모든** 파일 상태(`Missing (1) · Ahead (2)` / `OK`), 펼침 상태 유지 · 필터면 펼침, 트리 힌트 1075(717 → 1600, 2.23 배).
  Excluded 왼쪽에 게으른 체크 트리(공용 checkTree · treeExpand) → `Exclude Checked (All PCs / This PC)`, 폴더 아래 체크는 합침, 제외 · 무시는 회색.
- 덤: tabFit 이 스크롤 칸 안의 **중첩 탭**도 hfw 가 아니라고 봐서 긴 Status 페이지를 두 번 빼 Roots / Excluded 에서 창이 246px — `_hfw_reaches_parent` 로 수정(부모 레이아웃 hfw 면 hfw).
- 시험: sync UI 78/78 · core 53, tabFit 롤아웃 31툴 0 fail(mayapy), A00275 34, treeExpand 19, viewZoom 32, A00210 기존 43 · 32 · 28. **GUI 확인 아직.**

> [!summary] **Framework `MOD_treeExpand_qt_v01` (트리 펼치기 = 한 단계, Shift = 아래 전부)** + 툴 16개 적용 · A00210 **v01.48** `#Framework`
- 요청: A00210 Sync 트리를 접었다 펼치면 아래가 전부 열린다 → 화살표는 한 단계만, Shift + 펼치기/접기 = 아래 전부. 다른 트리도, 앞으로 만들 툴도 공용 코드로.
- 구현: `JUN_mod_treeExpand_qt_v01(tree)` 한 줄 — 사용자 입력 중의 펼침만(코드 expandAll 그대로), Shift 는 이벤트 modifiers, `*` 키 = 전부, 게으른 트리는 너비 우선 + 2000 한도.
  적용: A00010 · A00050 · A00110 · A00130 · A00145 · A00210 · A00211 · A00275 · A00290 / V02 · A00330 · A00340 · A00380 · A00420 · A00470 · A00480(트리 26개, 각 버전 +1). `MOD_fileTree` 는 같은 규칙을 자체로 가져서 제외.
- A00210 v01.48: 덤으로 Sync > Status 가 16px 잘리던 것(줄바꿈 `PCs:` 라벨) 수정 — tabFit 롤아웃 시험에서 발견.
- 시험: `test_tree_expand.py` 19/19(PySide6 · mayapy PySide2), tabFit 롤아웃 31툴 0 fail, A00110 Layers 46 · A00275 34 · 15 · A00480 47 · A00340 51 · A00210 52 · 32. **GUI 손 확인 아직.**
- 문서: `docs/Framework_MOD_treeExpand_qt.md`.

> [!summary] A00210_FileManager **v01.47 Sync 탭 (Sync Tracker 1차)** `#A00210_FileManager`
- 요청: 계획서대로 진행 — PC 간 작업 파일(정션 `C:\JUN\JUN_MUE`)의 최신본 · 빠진 PC 추적.
- 구현: PC 별 매니페스트(경로 · 크기 · 시각 · SHA-256 · 해시 이력 10개) → `<데이터 폴더>/manifests/<root>/<PC>.json`, 공유 설정 `_sync_settings.json`.
  비교 = 해시 + 이력(Missing · Outdated · Ahead · Only here · Conflict, 처음 보는 다른 내용은 시각으로 `?`). 하위 탭 Status · Roots(여러 루트 · PC 별 경로) · Excluded(공유 / 이 PC 만 · 무시 패턴).
  스캔은 QThread(크기 · 시각 같으면 해시 재사용, 저장 중 파일 건너뜀, 루트 안 정션 안 따라감). Push/Pull 은 MainWindow `_ready_git` 검사 재사용.
- 시험: `test_sync_core.py` 53/53 · `test_sync_ui.py` 52/52, 기존 43 · 28 · 50 · 32. 실측 `C:/JUN/JUN_MUE` 320 파일 · 13.9 GB 첫 스캔 10.9 s · 재스캔 0.03 s. **GUI 확인 아직.**
- 문서: 안내 4-F, 계획서 8장, 포트폴리오 EN/KR.

> [!summary] A00210_FileManager **Sync Tracker 계획서** (구현 보류) `#A00210_FileManager`
- 요청: 여러 PC 가 정션 `C:\JUN\JUN_MUE` 로 같은 경로를 쓰는데, 어느 PC 가 최신본이고 어느 PC 에 파일이 없거나 옛것인지 감지하고 싶다(현재 전송 = 구글 드라이브 수동).
- 안: PC 별 매니페스트 json(경로 · 크기 · 시각 · SHA-256 · 해시 이력)을 기존 데이터 저장소 `profiles/MUE/manifests/<루트>/<PC>.json` 으로 주고받아 Missing / Outdated / Ahead / Only here / Conflict 판정. 드라이브 다운로드는 시각을 바꾸므로 판정은 해시.
- 결정: A00210 `Sync` 탭 · 추적 루트 여러 개(PC 별 경로) · 루트별 제외 경로(하위 전부) · PC 열 동적(현재 2대, 늘어남) · **구현 보류**.
- 문서: [`plans/A00210_FileManager_sync_tracker_plan.md`](plans/A00210_FileManager_sync_tracker_plan.md)

> [!summary] A00110_animTool_V02 **v02.52 Shift+A 가 구간 끝 b 에도 레이어 키** `#A00110_animTool`
- 요청: [a, b] 를 고르고 Shift+A 하면 Layer 에 b 에도 키, 값은 a−N · a 를 찍은 뒤 정해진 a 와 같게.
- 구현: `HoldLayerManager.range_end()`(Hold 전에), `run_hold` → `apply(hold_end=b)` — Fix Sliding 대안 D 와 같은 경로(모든 키 찍은 레이어 채널, a out / b in flat).
- 시험: `test_hold_layer_blend.py` 86/86(RB: f50 · f60 · f90, b 값 = a 값 1e-9, [a, b] 상수, undo 한 번, 선택 없으면 b 없음), UI 21/21.
  Fix Sliding 시험 6 의 "순수 Shift+A" 기준을 Lock 켬으로 바꿈(40/40). **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.51 Bake > Bake 구간 밖 키 보존** `#A00110_animTool`
- 보고: 컨스트레인트를 걸고 Bake List 로 [10, 50] 만 구우면 그 밖의 기존 키가 지워진다(오브젝트는 Base + 다른 레이어에 키).
- 실측(mayapy): 레이어 없으면 정상. **레이어 멤버 채널**에서 `bakeResults -time -preserveOutsideKeys` 는 Base 커브를 [s, e] 의 41 키만 남기고 바꾸고
  (구간 밖 f70 tx 8.0 → 1.0), 합성값을 Base 에 써서 구간 안에서 위 레이어를 이중 계산. keep / bake down 둘 다 컨스트레인트는 남김.
- 수정 `BakeManager.bake_layered`: 컨스트레인트 켠 채 샘플 → 채널마다 대상 레이어(덮는 맨 위 override · 없으면 Base) 커브의 [s, e] 만 지우고
  (s-1 / e+1 fixed 모양 보존 — 듬성한 커브 보간 보호) `setKeyframe -animLayer 대상 -value` 역산. additive · override · 뮤트 · 잠김 처리.
- 덤으로 찾은 버그: `bakeResults -smart` 가 레이어 없이도 구간 밖 60 f 값을 바꿈 → dense + 구간 안만 Douglas-Peucker. `filterCurve -simplify` 는 허용오차 무시(실측).
- 한계: 키가 없던 채널은 원래 값이 컨스트레인트 순간 pairBlend 입력 0 → 마야 기본대로.
- 시험: `test_bake_layers.py` 19/19, 회귀 40 · 81 · 111 · 31. **GUI 확인 아직.**

## 2026-11-04

> [!summary] A00110_animTool_V02 **v02.50 Fix Sliding 크래시 수정** `#A00110_animTool`
- 보고: Fix Sliding 실행 중 마야 크래시 2 회(MayaCrashLog261104.1716 / .1749). 사용자 확인 = 두 번째 이후 실행, 디버그 커브가 그래프 에디터에 떠 있던 경우 있음.
- 분석: 버튼 → Python → `processEvents`(진행 팝업) → 그래프 에디터 paint → `AnimUISlice.dll TanimCurveCallbackManager::uiPainter` ACCESS_VIOLATION(0xFFFFFFFF).
  v02.49 `write_debug` 가 **undo 를 끈 채** 디버그 노드를 지우고 다시 만들었다 → 지운 커브가 바로 해제 → 그래프 에디터가 해제된 커브를 그림.
- 수정: ① 디버그 노드 · 커브 재사용(`MFnAnimCurve.remove` 7000 키 0.015 s, 노드 유지 — `cutKey -clear` 는 커브 노드까지 지워서 안 씀) · 옛 노드는 안내만
  ② Applying · Debug 동안 게이지는 단계 끝에만 ③ 그래프 에디터 `setUpdatesEnabled(False)` ④ 키 선택 비우기(`selectKey(clear=True)` 는 대상 없이 실패 → 골라진 커브를 remove).
- 시험: 40/40 · UI 15/15 · 회귀 81 · 21, KANA 두 번 연속 실행 — 노드 2 · 커브 8 재사용(UUID 동일), 33.4 s. 그래프 에디터 크래시 자체는 mayapy 에 GE 가 없어 재현 불가 → **GUI 확인 필요**.

> [!summary] A00110_animTool_V02 **v02.49 Fix Sliding 업데이트** `#A00110_animTool`
- 요청 4건: ① 디버그 노드를 TSL 오브젝트마다 `<이름>_debug_speed`(speed / smooth / threshold / result + source / info, 옛 단일 노드 정리)
  ② 그래프 에디터 커브 색 흰 · 밝은 하늘 · 빨강 · 초록(`animCurve.useCurveColor` + `curveColor`, mayapy 실측) ③ 탭에서 Layer 콤보 + Frames before (N)
  (처음 값 = Hot Key > Main, 펼칠 때 갱신, Hot Key 설정은 안 바뀜 — `run(layer=, offset=)` · `apply(layer=, offset=)`) ④ 공용 Expand 로 별도 창.
- 시험: `test_fix_sliding.py` 36/36 · `_ui` 15/15, 회귀 81 · 21 · 46. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.48 Bake > Fix Sliding** `#A00110_animTool`
- 계획서대로 구현: `core/fix_sliding_manager.py`(순수 함수 speeds · smooth · still_spans · merge_gaps · split_spans · blend_start + currentTime 샘플링 · preview · run · `_debug_speed`),
  `KeyframeManager._hold_curve / hold_range`(Shift+A 동작 불변), `HoldLayerManager.apply(force, ramp_start, hold_end)`, Bake > Fix Sliding 탭(TSL · 구간 · Speed · Spans · Keys · Preview / Fix Sliding · 진행 팝업 · optionVar).
- 정지 구간 [a, b] 마다 Hold + Layer Blend Key, B(Merge gap 4) → A(블렌드 시작 클램프) → D(b 에도 같은 레이어 값). 셋 끄면 순수 Shift+A.
- 시험: `test_fix_sliding.py` 30/30(핵심: 손으로 selectKey + run_hold 한 결과와 1e-9 일치 · 사용자 예시 [0,10]·[12,20] 에 f7 키 없음), UI 11/11,
  회귀 81 · 21 · 46 · 31 · 92 통과. **실측 KANA 씬**(사용자 제공, 저장 안 함): 6830 f 발 IK 둘, 191 구간, 34 s, 구간 안 월드 속도 0.69/0.82 → 0. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **Bake > Fix Sliding 계획서** (`docs/plans/a00110_fix_sliding_plan.md`) `#A00110_animTool`
- 요구: `_SmartLayer` Fix Sliding 처럼 속도(원래 · 스무딩 · Threshold)로 정지 구간 [a, b] 를 찾되, 결과는 **그 구간 T/R 키를 고르고 Layer Blend Key 켠 채 Shift+A** 한 것과 같게.
  길이 > M 인 구간만(사용자 확정), Threshold = 최대 속도의 %, TSL 로 대상 리스트업, `_debug_speed` 4 커브.
- `_SmartLayer` 는 .pyc — 디컴파일 안 함, 툴팁 문구로 원리만 확인. 계획: Hold 커브 단위 리팩터 · `HoldLayerManager` `force` · 새 `FixSlidingManager`(순수 함수 + currentTime 샘플링) ·
  Bake > Fix Sliding 탭, 핵심 시험 = 손으로 selectKey + run_hold 한 결과와 1e-9 대조. 구현은 다음.
- 개정: 이웃 구간 블렌드 침범([0,10] · [12,20], N=5 → f7 키) 대안 A~E 를 §9 에 기록, **B(Merge gap, G 기본 4) → A(블렌드 시작을 앞 구간 끝에서 자름) → D(구간 끝 b 에 레이어 키 + flat)** 순서로 결정.

> [!summary] A00110_animTool_V02 **v02.47 Layer Blend 기준 = 고른 구간의 a** `#A00110_animTool`
- 요구: 현재 프레임 / −N 이 아니라, 그래프 에디터에서 [a, b] 를 고르고 Shift+A 하면 **a 와 a − N** 에 레이어 키.
- 구현: `HoldLayerManager.range_start()`(고른 키 최소 시간, Hold 전에), `run_hold` 가 frame=a 로 capture · apply, 없으면 현재 프레임.
  `values_at()` — a ≠ 현재 시간이면 undo 끈 채 시간 이동해 읽고 복귀.
- ★ 실측: 레이어가 있으면 `getAttr -time` · `MDGContext` 는 Base 값만, `currentTime -update false` 는 옛 값 → 실제 시간 이동만 맞다.
  `setKeyframe -animLayer -v` additive 역산은 키 시간 기준.
- 시험: 81/81(RA: [60,90] 선택 · 현재 100 → f60 · f50, 시간 복귀, undo 한 번, Current = f60 값, 키 없으면 현재 프레임) · UI 21/21. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.46 Current 축 키 누락 수정 + Auto-Focus 기본 ON** `#A00110_animTool`
- 보고: Layer Blend Key 로 AnimLayer1 에 찍힌 키를 보면 Pose Key `Current` 를 켠 축에 키가 없다.
- 원인: 키 축 = 축 체크만, Current 는 그 안에서 값만 바꿈(체크 ∩ Current) → 기본값(체크 rx rz ty / Current ry tx tz)이 안 겹쳐 Current 축이 통째로 빠짐.
- 수정: 키 축 = 체크 ∪ Current (`HoldLayerManager.effective_axes`, `set_pose_keys`, UI 수집, capture). + View > Graph Focus `Auto-Focus on Selection` 을 툴 열 때 ON.
- 시험: 73/73 · UI 21/21, 창 띄우는 기존 시험 5개(46 · 31 · 14 · 68 · 111) 통과. mayapy 는 scriptJob 이 None 이라 Auto-Focus 는 토글 · 설치 호출로 확인. **GUI 확인 아직.**

> [!summary] A00340_SelectionTool **v01.20 Share 덮어쓰기** `#A00340_SelectionTool`
- 보고: Buttons 의 `MUE_BCM` 을 Share 로 공유 쪽에 덮어쓰려 하면 "already exists" 팝업만 뜨고 막힘.
- 원인: `prefs.share_profile()` 이 공유에 같은 이름이 있으면 무조건 ValueError.
- 수정: Share 때 같은 이름이 있으면 **덮어쓸지 묻는다**(기본 No) → Yes 면 `share_profile(name, overwrite=True)` 로 교체 후 공유 것으로 전환.
  네임스페이스 매핑은 로컬에 있으면 그것, 없으면 공유 것 유지. 같은 드라이브는 `os.replace`, 다른 드라이브(NAS)는 복사 후 삭제.
- 시험: `test_shared_profiles.py` 51/51(prefs 덮어쓰기 · 매핑 두 경우 · UI No/Yes), `test_namespace_remap.py` 30/30. **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.44 Pose Key `Current` 축마다** `#A00110_animTool`
- 요구: `Use current values` 는 어트리뷰트마다 필요한 체크 → 전역 체크박스 대신 Pose Key 행마다 `Current`.
- 구현: `PoseKeyManager.set_pose_keys(current_axes=)`, `HoldLayerManager` 설정 `use_current` → `current_axes`(optionVar JSON, 옛 값은 체크 축 전부로 옮김),
  capture · apply 모두 축마다. 켠 행만 값 칸 비활성, Layer Blend 메시지 `current: tx`.
- 시험: 69/69(축마다 Pose Key · Layer Blend additive/override · 옛 설정 옮기기) · UI 19/19. **GUI 확인 아직.**
- **v02.45** 같은 날 추가 요청: `Current` 기본 켜짐 = rotate Y · translate X · translate Z(`DEFAULT_CURRENT_AXES`, 저장값 없을 때). 70/70 · UI 19/19.

> [!summary] A00110_animTool_V02 **v02.43 Layer Blend Key 보기 게이트** `#A00110_animTool`
- 요구: AnimLayer1 을 보며 그 구간 키를 골라 Shift+A 하면 Layer Blend 가 돌면 안 됨 → 고른 레이어(기본 BaseAnimation)를 볼 때만 동작.
- 구현: `HoldLayerManager.viewed_layers()`(에디터 선택 → preferred → 루트) · `view_gate()` — 보는 레이어가 정확히 그 하나일 때만,
  아니면 Hold 만 하고 `skipped - viewing '...'`. UI `Run only when viewing` 콤보(첫 항목 = 루트, 펼칠 때 갱신, optionVar `view_layer`, "" = 루트).
- 시험: 63/63(AnimLayer1 보며 그 커브 Hold → Layer Blend 건너뜀 · Base 에서 동작 · 둘 보기 · 게이트 반대 · preferred 폴백) · UI 19/19. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.42 Layer Blend Key = 선택한 오브젝트만** `#A00110_animTool`
- 요구: Layer 에 AnimLayer1 이 설정돼 있어도 AnimLayer1 의 모든 오브젝트가 아니라 **마야에서 선택한 오브젝트에만** 레이어 키.
- 조사(mayapy): v02.41 도 선택 오브젝트에만 찍힘 — 선택만 / 레이어 노드 · 세트 · 캐릭터 세트 섞임 / Use current values 켬끔 전부 A 만.
  Hold 쪽도 오브젝트 선택을 바꾸면 그래프 에디터 키 선택이 풀려 새지 않음. **재현 안 됨.**
- 방어: `selected_objects()`(ls -sl -objectsOnly, animLayer · objectSet · character 제외), run_hold 가 선택을 한 번 읽어 capture / apply 공유,
  메시지에 키 찍은 오브젝트 이름. 시험 51/51 · UI 16/16. **GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.41 Pose Key `Use current values`** `#A00110_animTool`
- 요청: Pose Key 에 "선택 컨트롤러의 체크 축에 지금 프레임 값으로 키" 체크박스, 켜져 있으면 Layer Blend Key 의 레이어 키도 같은 방식.
- 구현: `PoseKeyManager.set_pose_keys(use_current=)`(키 찍기 전에 전부 읽기), `HoldLayerManager` `use_current` 설정(optionVar) +
  `capture_current()` — `run_hold` 가 **Hold 전에** 값을 읽어 apply 에 넘김(Hold 가 커브를 바꾸면 움직여 둔 값이 사라지므로). 켜면 값 칸 비활성.
- 시험: 41/41(키 없이 바꾼 값 키 · additive/override 최종값 유지 · Hold 전 값 · undo 한 번) · UI 16/16. **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.40 Layer Blend Key 버그 수정** `#A00110_animTool`
- 보고: 컨트롤러가 AnimLayer1 에 있는데 Shift+A 가 Hold 만 하고 레이어의 현재 / −N 프레임 키를 안 찍음.
- 원인(mayapy 재현): DEV 리로드가 같은 깊이 모듈을 `sys.modules` 등록 순서로 reload → v02.38 세션에서 다시 열면 `hotkey_manager` 가 먼저 reload 돼
  **옛 `HoldLayerManager`** 를 잡음. UI 는 새 클래스에 설정, 핫키는 옛 클래스(enabled=False) → 메시지 없이 건너뜀.
- 수정: 설정 원본 = optionVar(update 쓰기 · apply 읽기), `run_hold` 는 호출 때 모듈 속성 조회, 예외는 뷰포트 에러 한 줄, `no layer chosen` 경고, 콤보 펼칠 때 레이어 갱신.
- 시험: 33/33(RL1 = 그 리로드 순서 재현 후 run_hold 가 키) · UI 12/12. **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.39 Shift+A Layer Blend Key** `#A00110_animTool`
- 요청: 계획서 `docs/plans/a00110_hold_layer_blend_plan.md` 대로 — Shift+A 가 Hold 에 더해 고른 레이어에 (현재 − N) 레이어 값 키 + 현재 프레임 Pose Key 키.
- 구현: `core/hold_layer_manager.py`(settings 저장소 + apply), `run_hold` 가 Hold + apply 를 한 undo 청크로, Hot Key > Main 에 `Layer Blend Key` 체크 · Layer 콤보(Refresh, missing) · Frames before,
  Pose Key 행 변경까지 push, optionVar 복원. 멤버 판정 = blend 사슬에 그 레이어 노드가 있는지.
- ★ 실측: additive 레이어에서 `setKeyframe -animLayer -value` 는 **최종값 역산** → −N 키는 커브에 직접(레이어 값 보존), Pose 키는 같은 호출로 **최종값 = Pose**.
  `getAttr -time` 은 레이어 blend 뒤 옛 값이 나올 때가 있다.
- 시험: 새 29/29(Additive · Override · 비멤버 · 없음 · 잠김 · 뮤트 · run_hold undo 한 번) + UI 11/11. **마야 GUI 확인 아직.**

> [!summary] A00210_FileManager **v01.46 화면 경로 표기 통일** `#A00210_FileManager`
- 요청: Store Repo 등에서 같은 경로가 `C:\...` 와 `C:/...` 로 다르게 보임 → 하나로.
- 구현: 슬래시(`/`)로 통일(NAS `//서버/...`). `app/core/paths.py` `ui_path`(normpath + /, UNC 유지) · `ui_text`(로그 안 Windows 경로만).
  프로파일 읽기(경로 키 8개) · 입력 마침 · Browse · `MainWindow.log`(모든 탭) · 툴팁 · 안내창 · Maya 탭(예전 normpath `\`) · `data_dir_of` 결과.
- 시험: 새 28/28(`\` 프로파일과 `/` 프로파일이 같은 글자, 로그, mayapy Browse), 기존 43/43 · 50/50 · 32/32(비교를 표기 무관으로 고침) · 31/31, A00480 44/44.

> [!summary] A00210_FileManager **v01.45 데이터 폴더 구조 (안 A) — 코드 · 리허설 완료, 원격 반영 대기** `#A00210_FileManager`
- 사용자: 안 A 확정 + `JUN_FileManager_data` Private 전환 → 확인(익명 API 404, 자격증명 없는 git 거부, 이 PC 자격증명 OK).
- 코드: Settings `Data Folder`(profiles/ 하위), 데이터 폴더 = `<Store Repo>/profiles/<folder>`(`prefs.data_dir_of`, A00211 공유), Push = 내 폴더만 → rebase → push(거절 재시도),
  클론 브랜치 확인 + `Switch to main`, 옛 프로파일 자동 변환(저장 폴더 이름 우선 → soundAliance=SA), 기본 브랜치 main, 비공개 URL → 공용.
- 시험: 새 43/43, 기존 50/50 · 32/32 · 31/31, A00480 Lineage 44/44. 실제 프로파일 10개 변환 = 계획 표.
- 리허설: `_migrate/`(백업 미러 2 + 클론, push 막힘) Dnable 265 · MUE 128 · SA 11 · src_rig 7 일치 · 기록 보존, 프로파일 10개 읽기 수 불일치 0.
  **다음: 계획서 §5 원격 반영(푸시 요청 턴). 그 전엔 A00210 Pull/Push 쓰지 말 것.**
- **반영(사용자 "푸시해")**: 데이터 저장소 `main` `8bc1d5b` + `archive/*` 태그 5개 푸시(옛 브랜치 유지), 이 PC 클론 `main` 전환(툴 `switch_branch`),
  Rig_Src · soundAliance · MUE store_dir → `JUN_FileManager_data`(프로파일 백업 후). **10개 프로파일 브랜치 OK · 파일 수 옛 클론과 같음.**
  남은 것: GitHub 기본 브랜치 `main`(사용자 — gh 미로그인), 1~2주 뒤 비공개 저장소 Archive · 옛 클론 · 옛 브랜치 정리.

> [!summary] **A00210 데이터 저장소 구조 변경 계획서** (`docs/plans/A00210_FileManager_data_folders_plan.md`) + FileManager 데이터 푸시 `#A00210_FileManager`
- 데이터 푸시: `JUN_FileManager_data` Dnable 미반영 82건(08-24 이후)을 `4690a34` 로 커밋 · 푸시(툴 Push 와 같은 형식). SA · src_rig · MUE 는 이미 원격과 같음.
- 관찰: 프로파일마다 브랜치(Dnable · SA · src_rig, 비공개 MUE) + 브랜치마다 클론, Dnable 한 브랜치에 프로파일 7개 데이터가 이미 섞임,
  **soundAliance 프로파일 branch=Dnable 인데 클론은 SA**(어긋남), master 는 06-19 이후 멈춤.
- 계획: `main` 하나 + `profiles/<data_folder>/`, 비공개는 저장소로 분리. 코드(prefs `data_folder` · `data_dir_of` · GitSync 내 폴더만 add + rebase 재시도 · check_branch · A00211)
  → 리허설 → (푸시 턴) 반영 → PC 전환 → 정리. **리허설 실측: 265=265 · 11=11 · 7=7 blob 차이 0, 기록 보존, 최장 경로 128자.**
- 개정: 비공개 저장소 폐지 요청 → MUE 도 `JUN_FileManager_data/profiles/MUE`. ★ 그 저장소가 **공개**(API 200)라 MUE 가 공개됨 →
  §0-A 결정(A Private 전환 후 기록째 권장 / B 공개 + 스냅숏 / C 공개 + 기록째). 리허설 MUE 128=128 blob 0, 기록째면 비공개 커밋 15 공개. 비공개 저장소는 Archive.

> [!summary] **A00220_BackupTool Save Cache 계획서** (`docs/plans/A00220_BackupTool_save_cache_plan.md`) `#A00220_BackupTool`
- 요청: 마야 저장을 SSD 캐시에 먼저 → 몇 초 뒤 원래 HDD 경로로 복사(덮어쓰기), n 개 파일, 체감 저장 속도 개선 + 저장 보장.
- 실측(이 PC C: NVMe · D: SATA HDD): python 쓰기 300MB 는 HDD 도 0.07s(OS 쓰기 캐시), 1.5GB 부터 1.7s(fsync 10s).
  **마야 실제 저장 426MB .mb · 904MB .ma 는 SSD = HDD (4~6s, 직렬화가 전부)** → 로컬 HDD 는 이득 거의 없음, NAS · 초대형 파일이 후보.
- 계획: 1단계 = 실제 씬 · NAS 실측 게이트(차이 없으면 중단). 진행 시 마야 저장 훅(rename → save → rename) + 파일 큐 + A00220 지연 복사기
  (최신만 · `os.replace` 원자 교체 · 충돌 사본 · 재시도 · 재시작 재개 · 종료/열기 훅). 구현은 사용자 확인 뒤.

> [!summary] **Framework `MOD_viewZoom_qt_v01` (리스트 · 트리 확대 / 축소 공용)** + A00110_animTool_V02 **v02.38 View > Layers 확대** `#Framework` `#A00110_animTool_V02`
- 요청: Layers 목록 행이 낮아 고르기 · Mute 체크가 불편 → 행을 키우거나, 확대 / 축소를 공용 기능으로 만들어 툴마다 공유.
- 공용: 뷰 하나에 붙이면 배율 하나로 글자 · 헤더 · 행 높이 · 체크박스 · 들여쓰기. Ctrl + 휠 · `Zoom [-] 150% [+]` · QSettings 기억 · 체크 칸 전체 클릭(행 선택 안 바뀜).
  ★ 아이템 뷰 체크박스는 스타일이 13px 고정으로 그려 qss 로 못 키움 → 델리게이트가 직접 그림. ★ 테마 qss `QWidget { font-size: 12px }` 가 `setFont` 를 덮음
  → 뷰 자신의 스타일시트에 px 로, 기준 = 부모 글꼴(Show 때 재적용). ★ 오프스크린 `QFontInfo.pixelSize()` 는 -1 → QFont 의 px / pt×DPI.
- A00110: Layers 기본 150%, Expand 창 440x600. 시험: 공용 **32/32 (PySide6 · PySide2)**, A00110 Layers 46/46 · 37/37. 테마 입힌 실화면 캡처 확인(오프스크린). **마야 GUI 확인 아직**.

> [!summary] A00110_animTool_V02 **v02.37 Bake > Locator — `Constrain Objects to Locators`** `#A00110_animTool_V02`
- 요청: LOC + Anim 으로 로케이터를 굽고 나서 각 로케이터가 각 오브젝트에 컨스트레인트를 걸게 — 기본 parent, point · rotate(orient) · scale 도.
- 구현: 체크 그룹(기본 끔) + Parent(기본) / Point / Orient / Scale, Parent ↔ Point·Orient 배타. 코어 `constrain_objects` — `mo=False`(로케이터 = 오브젝트 월드),
  잠긴 축 · 키 아닌 구동 축 skip, **scale 은 pairBlend 가 없어 키 있는 축에 scaleConstraint 가 실패 → 키 있는 축도 skip**(마야 Constrain > Scale 과 같음). 진행 팝업 `Constraining` 단계.
- 시험: 컨스트레인트 **34/34**(오브젝트 월드 오차 1e-15), UI 31/31, 기존 25/25 · 46/46 · 14/14. **마야 GUI 확인 아직**.

## 2026-11-03

> [!summary] **`SwingTwistEvaluatorNode` 대체 검토 + 계획서** (`docs/plans/A00590_SwingTwistNative_plan.md`) `#A00590_SwingTwistNative`
- 요청: MetaHuman for Maya 의 `SwingTwistEvaluatorNode`(Epic 플러그인) 의존 제거 — 마야 노드만으로 완벽 재현 가능한지 검토, 가능하면 계획서.
- 검토: 어트리뷰트 실측(입력 도 단위 · 트위스트 축 X 고정 · XYZ 고정 · jointOrient 무시) + UE RigLogic `TwistSwingJointsEvaluator` 수식과 일치 확인.
  `quatNodes`(Autodesk 동봉) 프로토타입 망 vs 원본 3000 샘플 **행렬 3e-15 · 오일러 3e-13°**, 특이 입력 22 개 오차 0 → **가능**.
- 주의: Pose Editor 의 DNA export 는 원본 노드를 찾으므로 변환 씬은 swing/twist 가 빠짐 → `Restore` 단계 계획. 구현은 사용자 확인(툴 위치 · 테스트 씬) 뒤.

> [!summary] A00210_FileManager **v01.44 Store Repo 칸 읽기 전용** `#A00210_FileManager`
- 요청: File Manager 의 Store Repo 경로가 붙여넣기만으로 바뀌어 실수가 생길 수 있음 → Browse 로만 바꾸게.
- 구현: `ipf_store_dir.setReadOnly(True)`(Remote 의 Store Repo · Local 의 Shared Folder 같은 칸) + 툴팁 안내. 선택 · 복사 · 코드의 setText(Browse · 모드 전환 · 프로파일 · 기본 경로)는 그대로.

> [!summary] A00110_animTool_V02 **v02.36 Bake > Locator — `LOC + Anim`(오브젝트마다 로케이터를 만들어 구간 월드 베이크)** `#A00110_animTool_V02`
- 요청: 마야에서 `_SmartLayer` 패키지로 쓰던 `LOC + Anim`(선택 오브젝트마다 로케이터 → 현재 타임라인 베이크)이 가끔 답답하거나 오류 → Bake 탭 하위 탭으로 새로.
  조건: 대상 오브젝트 TSL · 베이크 중 진행 팝업(게이지) · Start / End UI + `Get Current` · `Get Sel Range`.
- 구현: 새 하위 탭 `Locator`(Bake 다음). 코어 `LocatorBakeManager` — 로케이터 `<이름>_LOC`(월드, 회전 순서 복사) + 임시 parentConstraint(+ scaleConstraint)
  → **`bakeResults` 한 번** → 컨스트레인트 삭제 → 오일러 필터. 게이지는 **`MDGMessage.addTimeChangeCallback`** — simulation 베이크가 프레임마다 부른다(실측 201 회 / 200 프레임).
  구간을 쪼개면 첫 호출이 컨스트레인트를 끊어 안 됨 → 한 번 + 콜백. 실패 시 만든 것 삭제, undo 한 번. 구간 칸은 공용 timeRange + `Get Timeline`.
- 시험: 코어 **25/25**(월드 T/R 오차 1e-13 · 조인트 · 스케일 부모 · 이름 충돌 · 실패 정리 · undo), UI 오프스크린 **20/20**(진행 팝업 3단계 · 100% · 버튼들), 기존 시험 46/46 · 14/14 그대로.
  **마야 GUI 확인 아직**(실제 리그 · 팝업 모양).

> [!summary] A00400_CurveTool **v01.31 Display > Replace 두 리스트에 `Sort` 버튼** `#A00400_CurveTool`
- 요청: "A00400_CurveTool / Display / Replace 의 tsl 두개에 sort 버튼 추가해."
- 공용 TSL 에 이미 있던 Sort(이름순, UUID 유지)를 `show_sort=True` 로 켰다. 짝은 리스트 순서대로라 양쪽을 정렬하면 이름순 짝. **마야 GUI 확인 아직.**

> [!summary] A00510_release_builder **v01.04 마야 UI 테마 오염 수정 + `Run_ReleaseBuilder.bat` · 아이콘 바로가기** `#A00510_release_builder`
- 요청: "__dragDrop_A00510 툴을 마야에서 쓰니 마야의 모든 UI 가 이 툴의 UI 와 유사하게 변한다. 마야 UI 가 변하지 않도록. 그리고 실행 bat 파일과, 그 파일의 아이콘도 평소에 보이도록."
- 원인: `launch.run()` 이 마야 안에서도 `ThemeManager.load_theme_dev(app, ...)` 로 qss 를 **QApplication(=마야)** 에 입혔다. 덤으로 launch import 만으로 AUMID 를 지정해 마야 프로세스의 작업 표시줄 ID 도 바꿨다.
- 수정: 앱 전역(qss · 앱 아이콘 · AUMID)은 이 프로세스가 앱을 만들 때만, 마야 안에서는 `load_theme_to_widget(win)` 로 창에만. 다시 누르면 이전 창을 닫는다.
- bat: `Run_ReleaseBuilder.bat` — PySide6/2 있는 64비트 파이썬을 찾아 pythonw 로 실행(설치 없음). `.bat` 은 아이콘을 못 가지므로 `make_shortcut.py` 가 툴 아이콘 + AUMID 를 박은 `Release Builder.lnk` 를 같은 폴더에 만든다(공용 `shell_integration.create_shortcut`, 절대 경로라 gitignore, 스탬프로 바뀔 때만 재생성).
- 오프스크린 검증: 마야 상황(앱 선존재)에서 앱 qss · 다른 위젯 · AUMID 그대로, 창에만 qss · standalone 은 앱 qss 후 정상 종료 · bat `--no-launch` 로 바로가기 생성 확인. **실제 마야 GUI 확인 아직.**

> [!summary] A00210_FileManager **v01.43 Maya > Reference `Delete Display Layers` · `Delete Anim Layers`(기본 ON) + 탭 스크롤 제거** · Framework tabFit **PySide6 수정** `#A00210_FileManager` `#Framework`
- 요청: "각 탭 세로 길이를 줄이든 UI 에 맞게 조절되든 스크롤로 보지 않게. Maya / Reference 탭에 선택한 씬의 모든 레이어, 애니메이션 레이어를 지우는 체크박스(기본 둘 다 체크)."
- 원인: v01.42 의 탭 높이 자동 맞춤이 **PySide6 에서 한 번도 돌지 않았다** — `MOD_tabFit_qt_v01` 이 `int(QSizePolicy.Policy)` 로 TypeError → 매번 `fit skipped`. `_enum_int()` 로 고침(PySide2 동작 그대로).
  덤으로 `tabs_scroll` 안 탭의 hfw 보정 오차(Export 가 File Manager 높이로 열림)도 고침. 롤아웃 시험 **31 툴 · 134 검사 · 0 실패**.
- 축소: 공용 `MOD_fileTree_qt_v01` 에 `tree_hint_height`(기본 None = 그대로), A00210 의 리스트 · 트리 · 표 sizeHint 를 짧게, File Manager Settings 한 줄 절약.
  실화면 실측(작업 영역 2560x1552) File Manager 1480 → 1348 · Reference 987 · Export 1363, **모든 탭 스크롤바 없음.**
- 레이어: `ref_importer.delete_display_layers` / `delete_animation_layers` — 임포트 · 네임스페이스 뒤, 저장 전. 레퍼런스로 남는 것의 레이어는 건너뜀. 애니 레이어는 루트 삭제(`delete BaseAnimation;` 과 같음).
  mayapy 2024 실측: 디스플레이 3 · 애니 4 삭제, 남은 레퍼런스 레이어 `K:KEEP_LYR` 유지, 오브젝트 · Base 커브(0, 3) 유지. A00210 시험 32/32 · 50/50. **실제 파일 GUI 확인 아직.**

> [!summary] A00130_ControlRig_V02 **v02.30 Match 표 체크박스 — 체크된 행만 Match, 나머지 세트는 그대로** `#A00130_ControlRig_V02`
- 요청: "Match 탭 목록마다 체크박스, 체크된 것만 Match, 안 된 것은 방치. 기본은 전부 체크, 모두 체크 / 모두 해제 버튼."
- 구현(UI 만, `match_manager` 는 그대로): 행 0열 체크박스 + `Check All` · `Uncheck All` · `n / m checked`. `on_match` 가 체크된 행만 `match_manager.apply` 에 넘긴다. 체크 해제는 (조인트, 세트_wanted) 키 집합으로 기억해 표를 다시 그려도 유지. 다중 선택 전파는 공용 `JUN_mod_checkTree_qt_v01`.
- IK 세션은 체크와 무관하게 `D01_IK_handle` 전체 — 해제된 세트가 IK 체인이면 닫을 때 폴 평면 맞춤으로 움직일 수 있다(문서 §4.1e 에 명시).
- mayapy 2024 오프스크린 **13/13** (해제 행 원점 유지 · 체크 행 이동 · 갱신 후 유지 · Uncheck All 무동작 · Check All · 다중 전파). **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.35 Hot Key > Main `Animation Layers > Delete BaseAnimation` — MEL `delete BaseAnimation;` 과 같은 결과** · A00030_quickTool_V02 v02.10 에서 제거 `#A00110_animTool_V02` `#A00030_quickTool_V02`
- 요청: "delete BaseAnimation 이 mel 명령이 친 것과 같은 결과가 되도록 버튼을 추가." → 처음엔 A00030 v02.09 에 넣었다가 "A00110_animTool_V02 / Hot Key / Main 에 이식하고 A00030 에서 빼" 로 옮겼다. A00030 v02.10 은 코드가 v02.08 과 같다(이력만 남김).
- 구현: `AnimLayerManager.delete_root()` — 루트를 `animLayer -q -root` 로 찾아(이름을 박지 않음) `cmds.delete`. 마야가 자식 레이어 · blend 노드 · 레이어 커브를 지우고 Base 커브를 다시 직접 연결한다. UI 는 Hot Key > Main 의 새 `Animation Layers` 그룹 버튼 + 확인 팝업(기본 No), 지운 뒤 View > Layers 갱신. 되돌릴 수 없어 단축키는 걸지 않았다.
- mayapy 실측: 레이어 3단에서 mel 과 **남은 노드 · 프레임 1/5/10 값 · tx 입력 연결이 같다**. 이 삭제는 **undo 로 레이어가 돌아오지 않아서**(standalone, undo 켠 상태) 팝업을 둔다. 시험 `tests/test_anim_layers.py` **46/46**(D1~D6 추가). **마야 GUI 확인 아직** — 팝업 · GUI 에서의 undo.

---
