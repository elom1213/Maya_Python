# Skin Tool
# 01.31  Weights > Smooth  - Kangaroo SkinCluster > Smooth 이식. 선택 버텍스의 웨이트를
#                           이웃과 평균(Iterations / Blend / Rigid / Keep Value One /
#                           Joint Locks 4모드 / Border Edges 3모드 + Mask Steps /
#                           Loop Curve / 소프트 셀렉션). 플러그인 무의존
#                           (core/weight_smooth_manager.py, ui/smooth_tab.py)

# 01.32  Weights > Transfer  - Target mode 추가. `Target list (1:1)` 을 고르면 Source
#                           Meshes 우측에 Target Meshes 리스트가 생기고, 행 순서로
#                           1:1 짝지어 전이한다(개수가 다르면 적은 쪽만큼).
#                           TRANSFER 버튼은 두 모드 모두 **진행률 팝업**을 띄운다
#                           (JUN_mod_progress_qt_v01, 메시/짝 하나마다 게이지)

# 01.33  Bind > Bind Pose  - `Update blendShape targets` (기본 켬, Keep current shape 전용).
#                           스킨 **앞** blendShape 의 타겟도 새 바인드 포즈에 맞게 돌린다 -
#                           조인트를 회전 · 스케일해도 타겟을 켠 모양이 유지된다. 저장된 타겟
#                           (in-between 포함)은 노드 값을, 라이브 타겟은 타겟 메시를 고친다.
#                           중립(envelope 0)에서 재므로 갱신할 때 weight 가 켜져 있어도 된다

# 01.34  Bind > Bind Pose  - UPDATE BIND POSE 가 진행률 팝업을 띄운다 (공용 JUN_mod_progress_qt_v01).
#                           skinCluster 마다 읽기 · 스킨 측정 · 행렬 · 굽기 · 노멀 · 타겟 · bindPose
#                           단계가 보이고, 스킨 측정과 타겟 갱신은 그 안에서도 게이지가 오른다

# 01.35  Select > By Weight - Bound Joints 리스트 아래에 조인트 이름 필터 (공용 JUN_mod_filter_qt).
#                           Number 가 `보이는 수 / 전체 수`. Check All / Uncheck All 은 보이는 행만.
#                           가려진 조인트의 체크는 유지되고 Select Vertices 에도 들어간다

# 01.36  Weights > Classic - Native 엔진에서 **선택 버텍스만**. Joints to Joints 는 선택 메시의
#                           버텍스(엣지/페이스 변환)만 본 컬럼 이동, Meshes to Meshes 는 To 메시에
#                           고른 버텍스만 전이하고 skinCluster 는 유지(고르지 않은 To 는 건너뜀).
#                           소프트 셀렉션은 falloff 비율. 컴포넌트 선택이 없으면 예전 그대로

# 01.37  Weights > Move 신규 - 조인트 n 개(From) -> k 개(To) 웨이트 이동, Kangaroo SkinCluster > Move 이식(플러그인 무의존,
#        Kangaroo 엔진도 선택). 버텍스마다 최근접 To(조인트 -> 자식 뼈 선분) + To 경계 스무딩(선택 안 이웃, 합 보존)
#        + Blend · 소프트 · Joint Locks · Border Edges. Respect selection(선택 버텍스만 / 메시 전체), 섬 검사, To 자동 추가.
#        Kangaroo 와 대조 시험(17 케이스 중 15 는 차이 0 ~ 2e-16, Border 2 는 Kangaroo 가 numpy 2 에서 죽어 성질로 확인).
#        Smooth 의 공용 함수를 core/skin_weights_common.py 로 옮김(동작 불변, 회귀 시험).

# 01.38  창 높이 자동 맞춤 - 탭을 바꿀 때마다(상위 · 하위) 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 페이지 전체가 보이고, 짧은 페이지로 가면 창이 줄어든다. 페이지가 화면보다 길면
#        화면 높이에서 멈추고 스크롤. 공용 Framework/qt/MOD_tabFit_qt_v01 (첫 적용 툴, 잘 되면 전 툴로).

# 01.39  트리 펼치기 - 화살표로 펼치면 한 단계만, Shift + 펼치기/접기 = 아래 전부 (Layer 탭 트리 · Lock 트리).
#        공용 Framework/qt/MOD_treeExpand_qt_v01

# 01.40  Weights > Flood 신규 - Kangaroo SkinCluster > Flood 이식(플러그인 무의존). 고른 조인트(들)에 웨이트 채우기 :
#        Replace/Add Closest · Replace/Add All · Scale All · Distribute, Smooth Steps · Blend · 소프트 · Joint Lines ·
#        Joint Locks · Border Edges. **씬에 같은 이름 조인트가 있어도 동작** - 원본은 인플루언스를 짧은 이름으로
#        다뤄 "More than one object matches name" 으로 죽는다 -> 조인트 · 인플루언스 · skinParent 를 전부 풀패스로.
#        원본 버그 둘 수정 : Blend 무시(Distribute 외) · Scale All 이 Value / 조인트 수로 곱함.
#        Kangaroo 와 대조 시험 19 케이스 차이 0 ~ 1e-16 (tests/test_weight_flood.py).
#        Move 도 같은 이름 대비 : 애매한 조인트 이름은 건너뛰고 알림, skinParent 는 풀패스로 풀릴 때만.

# 01.41  Weights > Flood - Joints 리스트에 `Get Bound Joints` 버튼. 메시를 고르면 그 skinCluster 의 조인트 전부,
#        버텍스 · 엣지 · 페이스를 고르면 거기에 웨이트가 있는 조인트만으로 리스트를 교체(같은 이름도 구별).

# 01.42  Weights > Flood - `Add Influence` 버튼. Get Bound Joints 로 읽은 메시를 기억해 두고(UUID, 리스트 위 `Mesh :`),
#        씬에서 고른 조인트를 그 skinCluster 에 웨이트 0 으로 추가 + 리스트에 붙인다(마야 Skin > Add Influence 와 같다).
#        이미 바인드된 것은 건너뛰고 알림, 같은 이름 조인트도 풀패스로, 한 번 = undo 한 스텝.

# 01.43  Weights > Classic 하위 탭 제거 -> Weights > Transfer 의 Target mode 에 `Classic` 추가. 고르면 예전 Classic 탭
#        (Engine Kangaroo/Native · Transfer Mode · From/To · Joints to Joints / Meshes to Meshes) 이 그 자리에 보이고
#        소스 전이 위젯은 숨는다. 위젯 · 핸들러 · 동작은 그대로, 모드를 바꾸면 창 높이를 다시 맞춘다.

# 01.44  리스트 이름이 아웃라이너처럼 - 같은 이름 노드가 있어도 `A|dup` 대신 `dup` 으로 보이고, 마우스를 올리면
#        전체 경로 툴팁. 리스트 우클릭 `Show Names` 로 Outliner Name / Full Path (전역, 기억). 툴이 쓰는 이름은 그대로.
#        공용 TSL 의 `name_display` 옵션을 이 툴의 리스트 11개에 켰다(첫 적용, 계획서 Framework_MOD_tsl_qt_name_display_plan).

# 01.45  Weights > Flood - Options 슬라이더(Value · Smooth Steps · Blend)가 보이게. 테마 qss 에 QSlider 규칙이 없어 어두운
#        배경에서 홈이 묻히고 손잡이만 보였다 -> 공용 JUN_mod_sliderStyle_qt_v01 이 보일 때 테마 색(green_dark)으로 칠한다.

VERSION = "01.45"
LAST_UPDATE = "2026-11-19"
