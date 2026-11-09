# -*- coding: utf-8 -*-
# A00610_PmxImporter - version info
#
# 01.00  첫 버전 (계획서 docs/plans/A00610_PmxImporter_plan.md). PMX 2.0/2.1 을 마야에 바로 임포트:
#        메시 하나(정점 순서 = PMX, 위치 (x,y,-z)x8 cm, UV (u,1-v), 감기 (c,b,a), 노멀 잠금, 추가 UV -> UV1~4) ·
#        재질마다 lambert + SG + file(알파 있는 텍스처는 투명도 연결) · 본마다 조인트(월드 정렬) · 스킨(BDEF1/2/4, SDEF/QDEF -> DQ) ·
#        버텍스 모프 -> 지오메트리 없는 blendShape. 이름 = PMX 고유 이름, 마야에 못 쓰는 글자는 FBXASC###.
#        코드페이지(cp949)로 못 읽는 텍스처 경로는 PMX 옆 maya_textures/ 에 FBXASC 이름으로 복사해 연결.
#        강체 · 조인트 · IK · 부여 · 표시 프레임 · 비버텍스 모프는 데이터(어트리뷰트 · 리포트)로만.

# 01.01  2차 1단계 (사용자 결정 2026-11-09: IK 근사 기본 켬 · 로컬축 기본 켬 · 외곽선/툰/스피어 보류).
#        부여(付与) 회전 = quatNodes 망 -> rotateAxis (부여 먼저, 자기 rotate 나중 = three.js GrantSolver 와 같은 순서, rotate 는 자유) ·
#        IK = ikHandle(링크 2+ RP, 1 SC, IK 본 아래) · 로컬축 / 고정축 -> jointOrient · 표시 프레임 -> 셋 + 모프 패널 -> Shape Editor 그룹 ·
#        엣지 배율 -> 컬러 셋 mmdEdgeScale(1 이 아닐 때만). Blender mmd_tools 와 포즈 메시 대조(시험 G13 · G14).

VERSION = "01.01"
LAST_UPDATE = "2026-11-09"
