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

VERSION = "01.38"
LAST_UPDATE = "2026-10-29"
