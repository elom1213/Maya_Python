# -*- coding: utf-8 -*-
# A00480_FileTool - version info
#
# 01.00  신규. 파일 입출력 · 경로 툴.
#        Export : A00040_file_exporter_V02(v02.09) 화면과 동작을 그대로 옮겼다.
#        Import : A00030_quickTool_V02 의 Import FBX normal.
#        Path   : A00030_quickTool_V02 의 Copy Scene Folder · Open Scene Folder.
#        합치면서 생긴 것 — Export Path 의 `Scene` 버튼(씬 폴더를 바로 채운다),
#        FBX 플러그인이 없을 때 Export 도 트레이스백 대신 로그로 알린다.
#        원본 두 툴은 무수정 보존.

# 01.01  창 크기를 A00040_file_exporter_V02 와 같게(slate_dark 960 x 853).
#        테마가 자식에 입혀진 뒤 레이아웃 최소 크기로 맞추고(show 다음 이벤트 루프),
#        Export 탭 페이지 여백 0 · 창 좌우 여백 -2(탭 테두리만큼) · Pin 높이 22.
#        v01.00 은 테마 전 글자 크기로 재서 약 1290 x 890 으로 떴다.

# 01.02  Pin 버튼 글자가 안 보이던 것 수정. 크기(72 x 22)는 그대로, 테마의 padding 8px 을
#        이 버튼만 위아래 0 으로(글자 영역 4px -> 20px).

# 01.03  Export 규칙 - 내보내기 전에 모든 세트를 검사, 하나라도 걸리면 파일을 하나도 안 쓴다.
#        첫 규칙 Check Hide Mesh (세트 안 메시 중 씬에서 안 보이는 것). 규칙은 export_rules.EXPORT_RULES 한 줄로 는다.

# 01.04  Check Hide Mesh 는 메시 자신(트랜스폼 + 쉐입)만 본다 - 숨겨진 그룹 · 조인트 등 메시가 아닌 오브젝트는 괜찮다.

# 01.05  규칙이 짚은 노드를 마야에서 선택 - Check 와 규칙에 막힌 Export 둘 다(숨긴 메시 트랜스폼).

# 01.06  Export > Naming 을 A00330 Token 탭과 같은 토큰 방식으로 - 공용 위젯 Framework MOD_tokenName_qt.
#        칸마다 규칙 Custom / Numbering(세트 순번) / Set's Name, Add / Delete Token, Profile(json, data/).
#        기본 프로파일 Default = SK_MANU_CH_Name_Basic_Version. Set Name 버튼은 미리보기 줄 오른쪽.

# 01.07  창이 화면보다 커서 아래에 로그창 잔상(Win10 · Maya 2023) / 흰 영역(Win11 · Maya 2024)이
#        생기던 문제 수정. 탭을 스크롤 칸에 담고, fit_to_content 가 창 높이를 모니터 작업 영역에 맞춘다.

# 01.08  Naming 토큰 칸을 고쳐도 프로파일에 저장하지 않는다 - Profile 줄의 Save 버튼을 눌러야 저장(기본이 된다).
#        예전엔 고칠 때마다 바로 저장돼서, 다시 열면 고친 칸이 그 프로파일의 기본으로 나왔다. 공용 위젯 수정.

# 01.09  Naming 토큰 규칙에 Enum (정해진 값 중 고르기) - A00330 과 같은 공용 규칙 COMMON_RULES (Framework.core.token_naming).

# 01.10  Import 탭이 하위 탭 둘 - CSV / FBX. CSV = A00200_CSV_tool(ARKit Facial Import) 이식(원본 보존):
#        Live Link Face CSV 를 노드의 키프레임으로 + 같은 이름의 WAV(또는 동영상에서 ffmpeg 추출)를 씬 사운드로.
#        원본과 다른 점 - UI · 로그 전부 영어, 키를 받는 노드가 블렌드셰이프만이 아니라 **CSV 열과 같은 이름의
#        어트리뷰트를 가진 아무 노드**(ARKit 52 어트리뷰트를 단 컨트롤 등). Detect 가 블렌드셰이프 + ARKit
#        어트리뷰트 노드를 모두 찾고 Selected 로 씬 선택을 넣는다. FBX = 예전 Import 탭(Import FBX normal) 그대로.

# 01.11  Import > CSV 에 Value Scale - 키 값 = CSV 값 x 배율 (기본 1, 버튼 x1 / x10).
#        CSV 는 [0, 1] 이지만 AdvancedSkeleton 페이셜 컨트롤은 [0, 10] 을 받는다 -> x10.

# 01.12  Reference 탭 (하위 탭 Default) - 현재 씬의 레퍼런스를 중첩(이중 · 삼중)까지 트리로 보여 주고,
#        고른 파일들을 탐색기에서 열거나(Open in Explorer · 더블클릭 · 우클릭) 경로를 복사한다(한 줄에 하나).
#        상태 Loaded / Unloaded(회색, 그 안의 중첩은 로드돼야 보인다) / Missing(빨강, 폴더만 연다).
#        탭을 열 때마다 씬을 다시 읽는다(Refresh 버튼도).

# 01.13  Import > FBX 에 Mocap FBX Import (Exact Rotation) 섹션. 마야 FBX 임포터가 비 XYZ 회전 순서 조인트
#        (Vicon 모캡 Hips · RightArm 등)의 회전 키를 XYZ 동치 공식으로 뒤집어 자세가 틀리는 문제를, FBX 파일의
#        원본 키로 회전(+ 이동) 커브를 다시 써서 고친다. Normalize joints(기본 ON) = jointOrient 0 · rotateOrder xyz
#        (블렌더 경유 결과와 같은 표현). Skeletons only · 회전 순서를 고려한 언랩 · 파일과 비교 검증.
#        Fix Scene From FBX = 이미 임포트한 씬을 같은 방법으로. 로직은 Framework.core.maya_fbx_exact
#        (+ fbx_binary · euler_math). 계획서 docs/plans/A00480_FileTool_fbx_exact_import_plan.md.

# 01.14  Pin 켜짐(Pinned) = 연한 빨강 - 공용 Framework/qt/pin_style (A00240_PathTool 과 같은 색).
# 01.15  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식) · 처음 여는 폭은 예전 fit_to_content 그대로

# 01.16  Reference > Default : `Show` 콤보 - File 열을 **Full Path / File Name** 으로 바꿔 본다(사용자 요청).
#        글자만 바뀌고 Open in Explorer · Copy Path 는 그대로 전체 경로. 고른 모드는 optionVar 에 기억.
#        core.reference_ops.file_text / load_file_view / save_file_view. tests/test_reference.py 46 항목.

# 01.17  Reference > **Lineage** 하위 탭 - 현재 씬의 레퍼런스 관계를 **노드 그래프**로. 데이터는 A00211_RefLineage
#        (ref_scanner: 씬 → A00210 LineageGraph), 노드 · 화살표는 A00210 Lineage 탭의 NodeItem / EdgeItem / LineageView
#        그대로(참조 대상 → 참조하는 파일 회색 점선, 레인 자동색). 휠 줌 · 중간 버튼 팬 · 드래그 · 우클릭 Reveal / Copy Path.
#        `Export to Lineage` = A00211 과 같은 lineage JSON 을 A00210 Store Repo 에(덮어쓰기 확인). 두 툴이 없으면 안내문만.
#        ★ 툴 간 import 예외(사용자 지시). tests/test_reference_lineage.py 31 항목.

# 01.18  Reference > Lineage 에도 `Show` 콤보 - 노드 글자를 **File Name(기본) / Full Path** 로. Default 탭과 같은
#        optionVar 를 써서 한쪽에서 바꾸면 다른 쪽도 따라간다. **기본이 File Name**(Default 탭도). Export 는 늘 파일 이름.
#        Lineage 배치는 **깊은 노드가 위, 씬이 맨 아래**(A00211 v01.03 _layout - 화살표가 아래로 흐른다).
#        tests/test_reference_lineage.py 38 · test_reference.py 47.

# 01.19  Reference > Lineage : 빈 곳 드래그로 **러버밴드 다중 선택**(A00210 과 같은 IntersectsItemShape) + 고른 노드의
#        **전체 경로**가 캔버스 아래 `Selected` 칸(읽기 전용 · 복사 가능)에 보인다(여럿이면 수 + 파일 이름, 툴팁에 경로 전부).
#        tests/test_reference_lineage.py 44.

VERSION = "01.19"
LAST_UPDATE = "2026-10-30"
