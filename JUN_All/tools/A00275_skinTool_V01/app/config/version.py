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

VERSION = "01.33"
LAST_UPDATE = "2026-09-28"
