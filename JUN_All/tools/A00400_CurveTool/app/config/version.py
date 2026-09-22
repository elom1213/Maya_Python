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

# 01.21  Display > Shape Edit  - 옛 `Line Width` 탭을 옛 `Transform` 탭 안으로 합치고,
#                           그 탭 이름을 **Shape Edit** 으로. 이 탭이 건드리는 것은 전부
#                           셰이프 노드다(CV 도 lineWidth 도) — 트랜스폼 채널은 불변.
#                           커브 목록(TSL)을 한 번만 만들면 모양도 굵기도 손본다

# 01.22  Display > Replace  - 대상이 **레퍼런스**면 셰이프 노드를 지울 수 없다. 그럴 때는
#                           셰이프를 바꾸는 대신 **CV 를 하나씩 대응 CV 에 맞춘다**
#                           (`crv_to_replace.cv[i]` <- `crv_replacement.cv[i]`).
#                           Mirror 를 켜면 대응 CV 의 **월드 위치를 X 만 뒤집은** 자리로

# 01.23  Display > Replace 에 **Resolve Pair from Selection** 버튼. 교체본의 반대쪽 이름을
#                           공용 미러 토큰 규칙으로 만들어, 그 커브가 씬에 있으면
#                           좌측 `Shapes to replace` 에 짝지어 채운다. 짝은 리스트 순서로
#                           맺어지므로 **양쪽을 짝지어진 것만으로 함께** 다시 채운다

# 01.24  Create > Controls  - `Thickness` 칸 삭제. 선 굵기(`nurbsCurve.lineWidth`)는
#                           `Display > Shape Edit` 이 담당한다(v01.21 에 합쳐진 옛
#                           `Line Width` 탭). 같은 기능이 두 곳에 있던 것을 한 곳으로

VERSION = "01.24"
LAST_UPDATE = "2026-09-22"
