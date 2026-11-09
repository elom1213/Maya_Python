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

VERSION = "01.00"
LAST_UPDATE = "2026-11-09"
