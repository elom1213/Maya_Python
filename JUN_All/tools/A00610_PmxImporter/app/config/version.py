# -*- coding: utf-8 -*-
# A00610_PmxImporter - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00610_PmxImporter_plan.md). PMX 2.0/2.1 을 마야에 바로 임포트:
#        메시 하나(정점 순서 = PMX, 위치 (x,y,-z)x8 cm, UV (u,1-v), 감기 (c,b,a), 노멀 잠금, 추가 UV -> UV1~4) ·
#        재질마다 lambert + SG + file(알파 있는 텍스처는 투명도 연결) · 본마다 조인트(월드 정렬) · 스킨(BDEF1/2/4, SDEF/QDEF -> DQ) ·
#        버텍스 모프 -> 지오메트리 없는 blendShape. 이름 = PMX 고유 이름, 마야에 못 쓰는 글자는 FBXASC###.
#        코드페이지(cp949)로 못 읽는 텍스처 경로는 PMX 옆 maya_textures/ 에 FBXASC 이름으로 복사해 연결.
#        강체 · 조인트 · IK · 부여 · 표시 프레임 · 비버텍스 모프는 데이터(어트리뷰트 · 리포트)로만.

VERSION = "01.00"
LAST_UPDATE = "2026-11-09"
