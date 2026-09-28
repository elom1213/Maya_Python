# 03.12  Create > From Curve  - `By Count` : 개수(2 이상)를 정해 커브를 따라 조인트.
#                           자리는 POCI(turnOnPercentage) parameter 0~1 등분 -
#                           3 이면 0 / 0.5 / 1.0. `Create as chain` 을 끄면 자리마다
#                           따로 떨어진 루트 조인트

# 03.13  Chain > IK Edit - Pole vector `Keep offset - fit the chain to the pole plane`
#                           (새 기본). poleVectorConstraint offset 을 안 바꾸고, 중간 조인트를
#                           폴 평면에 투영(반대편이면 거울 반사) · X 를 다음 조인트로(-X 규약
#                           유지) · up 축을 평면 법선으로 · 2조인트 체인은 솔버의 비틀림을 굳힘 ·
#                           restTranslate = constraintTranslate. 옛 두 모드는 그대로.
#                           편차 회전을 오일러 성분 차 대신 두 방향 사이 각도로 잰다
#                           (같은 방향이 90/270/356 도로 보고되던 것).
#                           계획서: docs/plans/A00060_A00130_ik_edit_keep_pv_offset_plan.md

VERSION = "03.13"
LAST_UPDATE = "2026-09-28"
