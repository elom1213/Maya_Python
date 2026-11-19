# Mesh Tool
# 01.13  Match > Default 의 좌(Source) / 우(Targets) 리스트에 **Sort 버튼**. 짝은 리스트
#        순서로 맺어지므로 양쪽을 이름순으로 정렬하면 규칙적인 이름은 그대로 짝이 맞는다

# 01.14  **MeshDoctor 탭** — 옛 A00300_meshDoctor 를 통째로 이식. 메시를 읽기만 해서 진단하고
#        (요약 표 + 상세 리포트 + 0020_out/ 에 JSON·TXT), 안전한 원클릭 수정과 문제 컴포넌트
#        선택을 제공한다. 대상 리스트는 이 툴의 공용 TSL 위젯으로 통일. 아이콘도 새로 그렸다

# 01.15  창 가로를 A00400_CurveTool 과 같게 (사용자 요청). 세로 860 은 그대로
# 01.16  가로를 1176 -> 360 으로 되돌림. 01.15 는 **오프스크린에서 잰** A00400 의 최소 폭을
#        그대로 박은 값이라 마야에서 지나치게 넓었다. 오프스크린 px 은 폰트가 달라 마야보다
#        크게 나온다 - A00400 과 같은 가로는 그 툴의 resize 값(360)을 쓰는 것이 맞다

# 01.17  **UV Sets 탭**(MeshDoctor 오른쪽) - A00050_uvTool_V02(v02.03) 이식. UV 세트 규칙(map1 하나)
#        Catch / Delete / Rename + UV Sets 표(Object / UV Sets / Rule), 로그의 [wrong_name] 빨강.
#        코어 uv_set_manager.py · 표 uv_set_table.py 는 A00050 파일 그대로, 탭은 app/ui/uv_tab.py.
#        Help > UV Sets Rule. 원본 A00050_uvTool_V02 는 남긴다
# 01.18  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식)

# 01.19  트리 펼치기 - 화살표로 펼치면 한 단계만, Shift + 펼치기/접기 = 아래 전부 (Match · By Weight 짝 트리 · UV Set 표).
#        공용 Framework/qt/MOD_treeExpand_qt_v01

# 01.20  **LOD 탭**(맨 오른쪽) - 재생용 저폴리 프록시(LOD1 ~ LOD5) 메시를 빠르게 만든다. 바인딩 안 함.
#        Fast = numpy 그리드 클러스터링 + 셀마다 QEM 대표점 (polyReduce 대비 실제 아바타 12배, 구 17배),
#        Quality = polyReduce. 스킨 메시는 orig 셰이프(바인드 포즈)에서 줄인다. 노멀 버킷으로 얇은 부위 보호,
#        버텍스당 UV · 원본 재질, Combine per LOD, 기록 어트리뷰트 junLodSource(UUID) 등. Ctrl+Z 한 번.
#        코어 app/core/lod_manager.py, 탭 app/ui/lod_tab.py. 계획서 docs/plans/A00380_MeshTool_LOD_plan.md

# 01.21  **Quad Patch 탭**(Match 오른쪽) - 구멍을 쿼드 그리드로 메운다(블렌더 Grid Fill 류, 독자 구현).
#        Edge Border(보더 엣지 하나만 골라도 그 구멍 전체) / Faces(고른 면을 지우고 원래 면 위에 그리드,
#        UV 도 원래 면에서) / Extrude(보더 일부 사슬에서 Rows 줄). Coons 패치 + Relax, Rotation ·
#        Proportion · Auto Corners · Inset 링 · Smooth Border. 초록 와이어 미리보기는 undo 큐 밖,
#        Patch It = polyAppendVertex 로 원본 메시에 직접(트랜스폼 · 셰이프 · UUID 유지), Ctrl+Z 한 번.
#        코어 app/core/quad_patch.py, 탭 app/ui/quad_patch_tab.py. Help > Quad Patch Notes

VERSION = "01.21"
LAST_UPDATE = "2026-11-19"

# 01.06  Match 탭 From 리스트의 List From Mesh / Add / Del 버튼 글자가 잘리던 문제.
#        TSL 위젯 전체에 걸려 있던 setMaximumHeight 를 치우고 리스트에만 높이를 제한한다.
# 01.07  로그창을 공용 위젯 `JUN_mod_log_qt_v01` 로 교체 (Expand / Clear / Copy)
# 01.09  Match 탭을 하위 탭 Default / By Weight 로. Default = 기존 Match 그대로. By Weight =
#        스킨 메시(M_w) 조인트 웨이트를 마스크로 메시(M_j)들을 타깃(M_tgt) 쪽으로 웨이트 x 델타 만큼
#        (오브젝트 공간, 인덱스 대응). 짝짓기: 조인트 k -> 메시 k / 합 -> 모든 메시. Ctrl+Z 한 번
# 01.10  Match > Default 를 좌(Source) / 우(Targets) 리스트로. 우측 메시들을 좌측 모양으로 바꾼다.
#        좌 1개 = 1 <= n(전부 같은 모양), 여러 개 = n <= n(순서대로, 작은 쪽 수만큼 - 남는 메시는 로그).
#        예전의 'From 1개 + 씬 선택' 은 없어졌다. 리스트를 바꾸면 미리보기 세션도 버린다
# 01.11  Apply Match 가 도는 동안 공용 진행률 팝업(JUN_mod_progress_qt_v01). 단계 Reading meshes /
#        Writing vertices - 미리보기 세션이 있으면 Writing 만. 로그에 걸린 시간
# 01.12  By Weight: 블렌드셰이프 타겟 Edit(sculpt) 가 켜진 메시에서 Apply 가 pnts setAttr 에러로 실패하던 문제.
#        Edit 중이면 이동량을 그 타겟 아이템의 델타(inputPointsTarget)에 직접 더한다 (마야 move 와 같은 결과)
