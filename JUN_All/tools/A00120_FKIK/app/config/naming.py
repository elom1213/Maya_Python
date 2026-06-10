# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - 리그 네이밍 데이터 (토큰 / 매칭 쌍 / 상수)
#
# 주의: 아래 토큰 문자열은 현장 리그 네이밍과 1:1 로 대응한다.
#       한 글자라도 바뀌면 매칭/셋업이 동작하지 않으므로 절대 임의로 수정하지 말 것.
#       (레거시 JUN_PY_FKIK_Tool_V02_01.py 의 하드코딩 값을 원문 그대로 옮겨온 것)
#
# 네이밍 컨벤션:
#   - position helper (target) : "*_xx_pos"  (shape: follicle / locator)
#   - controller    (follower) : "*_xx_ctl"  (shape: nurbsCurve)
#   - 묶음 그룹               : "BlendFKIKPos_grp"


# =========================
# 상수
# =========================

BLEND_GRP_TOKEN = "BlendFKIKPos_grp"

NUM_POS = 24                       # position / controller 개수 검증값

POS_SHAPES = ["follicle", "locator"]   # target(pos) 셰이프 타입
CTL_SHAPE  = ["nurbsCurve"]            # controller(ctl) 셰이프 타입


# =========================
# Setup : target(pos) 토큰
# =========================

# IK target pos
TGT_POS_TOKENS_IK = [
    "r_LegPole_xx_pos",
    "l_LegPole_xx_pos",
    "r_ArmPole_xx_pos",
    "l_ArmPole_xx_pos",
    "r_LegIkPos_xx_pos",
    "r_LegToeIkPos_xx_pos",
    "l_LegIkPos_xx_pos",
    "l_LegToeIkPos_xx_pos",
    "r_ArmIkPos_xx_pos",
    "l_ArmIkPos_xx_pos",
]

# FK target pos
TGT_POS_TOKENS_FK = [
    "l_ArmUpIK_xx_pos",
    "l_ArmLowIK_xx_pos",
    "l_HandIK_xx_pos",
    "r_ArmUpIK_xx_pos",
    "r_ArmLowIK_xx_pos",
    "r_HandIK_xx_pos",
    "l_LegUpIK_xx_pos",
    "l_LegLowIK_xx_pos",
    "l_LegAnkleIK_xx_pos",
    "l_LegFootBallIK_xx_pos",
    "r_LegUpIK_xx_pos",
    "r_LegLowIK_xx_pos",
    "r_LegAnkleIK_xx_pos",
    "r_LegFootBallIK_xx_pos",
]

TGT_POS_TOKENS = TGT_POS_TOKENS_IK + TGT_POS_TOKENS_FK   # 총 24


# =========================
# Setup : controller(ctl) 토큰
# =========================

# IK ctl
CTL_TOKENS_IK = [
    "r_LegPole_xx_ctl",
    "l_LegPole_xx_ctl",
    "r_ArmPole_xx_ctl",
    "l_ArmPole_xx_ctl",
    "r_foot_xx_ctl",
    "r_toe_xx_ctl",
    "l_foot_xx_ctl",
    "l_toe_xx_ctl",
    "r_ArmIK_xx_ctl",
    "l_ArmIK_xx_ctl",
]

# FK ctl
CTL_TOKENS_FK = [
    "l_UpperArm_xx_ctl",
    "l_LowerArm_xx_ctl",
    "l_WristFK_xx_ctl",
    "r_UpperArm_xx_ctl",
    "r_LowerArm_xx_ctl",
    "r_WristFK_xx_ctl",
    "l_UpperLegFK_xx_ctl",
    "l_LowerLegFK_xx_ctl",
    "l_ankleFK_xx_ctl",
    "l_FootFK_xx_ctl",
    "r_UpperLegFK_xx_ctl",
    "r_LowerLegFK_xx_ctl",
    "r_ankleFK_xx_ctl",
    "r_FootFK_xx_ctl",
]

CTL_TOKENS = CTL_TOKENS_IK + CTL_TOKENS_FK   # 총 24


# =========================
# Match : 방향별 정렬 토큰 (tgt[i] <-> flw[i] 가 대응)
# =========================

# FK 방향 (FK 컨트롤러를 매칭)
FK_TGT_TOKENS = [
    "l_ArmUpIK_xx_pos",
    "l_ArmLowIK_xx_pos",
    "l_HandIK_xx_pos",
    "r_ArmUpIK_xx_pos",
    "r_ArmLowIK_xx_pos",
    "r_HandIK_xx_pos",
    "l_LegUpIK_xx_pos",
    "l_LegLowIK_xx_pos",
    "l_LegAnkleIK_xx_pos",
    "l_LegFootBallIK_xx_pos",
    "r_LegUpIK_xx_pos",
    "r_LegLowIK_xx_pos",
    "r_LegAnkleIK_xx_pos",
    "r_LegFootBallIK_xx_pos",
]

FK_FLW_TOKENS = [
    "l_UpperArm_xx_ctl",
    "l_LowerArm_xx_ctl",
    "l_WristFK_xx_ctl",
    "r_UpperArm_xx_ctl",
    "r_LowerArm_xx_ctl",
    "r_WristFK_xx_ctl",
    "l_UpperLegFK_xx_ctl",
    "l_LowerLegFK_xx_ctl",
    "l_ankleFK_xx_ctl",
    "l_FootFK_xx_ctl",
    "r_UpperLegFK_xx_ctl",
    "r_LowerLegFK_xx_ctl",
    "r_ankleFK_xx_ctl",
    "r_FootFK_xx_ctl",
]

# IK 방향 (IK 컨트롤러를 매칭)
IK_TGT_TOKENS = [
    "r_LegPole_xx_pos",
    "l_LegPole_xx_pos",
    "r_ArmPole_xx_pos",
    "l_ArmPole_xx_pos",
    "r_LegIkPos_xx_pos",
    "r_LegToeIkPos_xx_pos",
    "l_LegIkPos_xx_pos",
    "l_LegToeIkPos_xx_pos",
    "r_ArmIkPos_xx_pos",
    "l_ArmIkPos_xx_pos",
]

IK_FLW_TOKENS = [
    "r_LegPole_xx_ctl",
    "l_LegPole_xx_ctl",
    "r_ArmPole_xx_ctl",
    "l_ArmPole_xx_ctl",
    "r_foot_xx_ctl",
    "r_toe_xx_ctl",
    "l_foot_xx_ctl",
    "l_toe_xx_ctl",
    "r_ArmIK_xx_ctl",
    "l_ArmIK_xx_ctl",
]


# =========================
# Match : 부위별 그룹 (Arm/Leg, L/R)
#   각 항목 = (target 토큰들, follower 토큰들) — 같은 index 끼리 대응
# =========================

LIMB_GROUPS = {
    "arm_l": (
        ["l_ArmPole_xx_pos", "l_ArmIkPos_xx_pos", "l_ArmUpIK_xx_pos", "l_ArmLowIK_xx_pos", "l_HandIK_xx_pos"],
        ["l_ArmPole_xx_ctl", "l_ArmIK_xx_ctl", "l_UpperArm_xx_ctl", "l_LowerArm_xx_ctl", "l_WristFK_xx_ctl"],
    ),
    "arm_r": (
        ["r_ArmPole_xx_pos", "r_ArmIkPos_xx_pos", "r_ArmUpIK_xx_pos", "r_ArmLowIK_xx_pos", "r_HandIK_xx_pos"],
        ["r_ArmPole_xx_ctl", "r_ArmIK_xx_ctl", "r_UpperArm_xx_ctl", "r_LowerArm_xx_ctl", "r_WristFK_xx_ctl"],
    ),
    "leg_l": (
        ["l_LegPole_xx_pos", "l_LegIkPos_xx_pos", "l_LegToeIkPos_xx_pos", "l_LegUpIK_xx_pos", "l_LegLowIK_xx_pos", "l_LegAnkleIK_xx_pos", "l_LegFootBallIK_xx_pos"],
        ["l_LegPole_xx_ctl", "l_foot_xx_ctl", "l_toe_xx_ctl", "l_UpperLegFK_xx_ctl", "l_LowerLegFK_xx_ctl", "l_ankleFK_xx_ctl", "l_FootFK_xx_ctl"],
    ),
    "leg_r": (
        ["r_LegPole_xx_pos", "r_LegIkPos_xx_pos", "r_LegToeIkPos_xx_pos", "r_LegUpIK_xx_pos", "r_LegLowIK_xx_pos", "r_LegAnkleIK_xx_pos", "r_LegFootBallIK_xx_pos"],
        ["r_LegPole_xx_ctl", "r_foot_xx_ctl", "r_toe_xx_ctl", "r_UpperLegFK_xx_ctl", "r_LowerLegFK_xx_ctl", "r_ankleFK_xx_ctl", "r_FootFK_xx_ctl"],
    ),
}
