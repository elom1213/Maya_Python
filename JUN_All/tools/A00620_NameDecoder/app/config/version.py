# -*- coding: utf-8 -*-
# A00620_NameDecoder - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00620_NameDecoder_plan.md). 마야 FBX 임포터가 FBXASC### 로 바꾼 이름을
#        원래 글자(일본어 · 중국어 · 띄어쓰기 · 맨 앞 숫자)로 풀어 보여 준다. 씬은 바꾸지 않는다(Rename 탭 제외).
#        - Names       : Scene / Selected / Selected + Hierarchy 범위의 노드 · blendShape 타겟 · (옵션) 어트리뷰트 이름 표,
#                        디코드 글자로 검색, 행 클릭 = 마야 선택, Sync with Selection, 우클릭 복사, Export List / Map Template
#        - Blend Shapes: 타겟을 풀린 이름 + 웨이트 슬라이더로 (Shape Editor 는 FBXASC 로만 보인다), Reset All
#        - Rename to ASCII (View 메뉴로 켬): 번역표(원래 글자 -> ASCII) 로 미리보기 -> Apply, 원래 이름은 씬의
#          network 노드에 기억해 Restore Original Names. FBX 로 내보낼 때 원래 이름이 사라지므로 경고 후 실행.
#        디코더는 공용 Framework/core/fbx_name.py, 씬 스캔은 Framework/core/maya_fbx_names.py.

# 01.01  Blend Shapes 게이지를 잘 보이게 (A00290_BSTool_V02 Shape Editor WeightSlider 참고) - 슬라이더를 직접 그린다:
#        어두운 홈 + 채운 길이 = 웨이트(0~1 한 방향이라 채움, purple_dark 그라데이션) · 튀어나온 핸들 · 구동/잠긴 웨이트는 회색.
#        줄마다 배경을 번갈아 칠하고, 웨이트가 0 이 아닌 타겟 이름은 밝게 · 굵게.

# 01.02  Outliner 탭 (계획서 docs/plans/A00620_NameDecoder_outliner_plan.md) - 풀린 이름을 마야 아웃라이너처럼
#        노드 타입 아이콘 + DAG 계층으로. 마야 아웃라이너는 일본어 · 중국어 이름을 표시할 수 없어서 이 창이 대신한다.
#        - 첫 탭. Scope(Scene/Selected/Selected + Hierarchy) · Shapes · Blend Shapes(메시 아래 blendShape + 타겟) ·
#          Encoded branches only · Refresh(펼침 · 선택은 UUID 로 유지) · 숨은 노드 흐리게(기울임)
#        - 행 클릭 = 마야 선택, Sync with Selection(조상 펼침 + 스크롤, scriptJob 은 Names 와 하나 공유),
#          타겟 더블클릭 = Blend Shapes 탭의 그 행, 우클릭 Copy Decoded/Raw/Decoded Path · Select Hierarchy · Expand/Collapse
#        - 아이콘 = 공용 Framework/qt/maya_icons.py (`:/out_<type>.png`, 없으면 상속 타입 → out_dagNode → out_default),
#          blendShape 는 마야 리소스가 없어 icon/outliner_blendShape.svg · outliner_bsTarget.svg
#        - 필터 = 공용 MOD_filter 의 새 tree_recursive 모드(맞는 행 + 조상, 조상 펼침)
#        - Names 탭: Decoded 열에도 같은 아이콘, 우클릭 Show in Outliner

# 01.03  Outliner 탭: Alt + 가운데 버튼 드래그 = 위아래로 끌어 옮기기(마야 아웃라이너와 같은 조작).
#        공용 Framework/qt/MOD_altPan_qt_v01.py - 항목 단위 스크롤이어도 행 높이로 나눠 옮긴다, 그 클릭은 선택을 바꾸지 않는다.

VERSION = "01.03"
LAST_UPDATE = "2026-11-11"
