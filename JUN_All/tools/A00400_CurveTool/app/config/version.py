# Curve Tool
#
# 01.00  Create / Direction  - 선택 엣지 연결 성분별 커브 생성 + 방향 통일
# 01.01  Line Width          - nurbsCurve.lineWidth 슬라이더
# 01.03  Wrap                - CV 개수가 달라도 커브가 커브 모양을 따르게 (envelope 0~1)
# 01.04  Points to Curve     - 리스트 순서대로 월드 위치를 잇는 커브 (Exact / Smoothed)
# 01.05  Smooth              - 선택 CV 를 슬라이더로 Smooth / Rough (소프트 셀렉션 폴오프 반영)
# 01.06  Tab taxonomy        - 상위 탭 = 카테고리(Create / Edit / Display), 하위 탭 = 기능
# 01.07  Joints              - 커브 위 균일 조인트 + 커브 바인드 + zro/con/ctl/tgt 컨트롤러
# 01.08  Smooth on closed    - 닫힌(주기) 커브도 Smooth / Rough (이음매를 넘어서)
# 01.09  Smooth keep sel     - 임시 커브 생성/삭제가 CV 선택을 지우던 것 수정
# 01.10  로그창을 공용 위젯 `JUN_mod_log_qt_v01` 로 교체 (Expand / Clear / Copy)
# 01.11  Edit > Combine       - Source 커브 쉐입을 Target 에 복사해 합친다 (인스턴스 아님)
# 01.13  Combine Placement    - 기본값: Source 를 Target 월드 위치(피벗)로 옮긴 모양으로 합친다
# 01.14  Joints on surfaces   - NURBS surface 도 U / V 방향 한 줄로 조인트 + 바인드 + 컨트롤러
# 01.15  Controls           - bs_controls 이식 : 컨트롤러 커브 34종 생성 + 색 + 셰이프 교체.
#                           셰이프 데이터는 Framework/rules/control_shapes.json (공용)
# 01.16  Display > Replace  - 셰이프 교체를 Controls 에서 떼어 하위 탭으로. 두 칸을 TSL 로,
#                           개수가 다르면 적은 쪽만큼 1:1
# 01.17  Color Palette      - Controls 색에 팔레트 팝업(임의 RGB) 추가 — ref_01.mel 과 같이
#                           overrideRGBColors + overrideColorRGB

# 01.18  Display > Transform - 리스트업한 커브의 **셰이프**를 각자의 피벗 기준으로
#                           스케일 / 이동 / 회전. CV 를 전부 골라 툴을 쓴 것과 같은 결과이고
#                           트랜스폼 채널은 건드리지 않는다. 축(X/Y/Z)마다 켜고 끈다.
#                           기본은 Scale 만 켬

# 01.19  Display > Transform - 값 칸 아홉 개를 전부 **슬라이더**로 끌어서 정한다. 슬라이더는
#                           자주 쓰는 구간(스케일 0~5 · 이동 ±10 · 회전 ±180)이고, 그보다 큰
#                           값을 쳐 넣으면 범위가 그 값까지 늘어난다

# 01.20  Display > Transform - **Live**(기본 켬) : 슬라이더를 끄는 동안 씬의 커브가 따라
#                           변한다. 세션이 잡아 둔 CV 원위치에서 매번 다시 계산해 누적되지
#                           않고, 드래그는 undo 큐에 안 쌓이다가 멎으면 한 항목으로 기록된다

VERSION = "01.20"
LAST_UPDATE = "2026-09-21"
