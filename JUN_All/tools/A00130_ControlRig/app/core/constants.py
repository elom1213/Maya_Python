# -*- coding: utf-8 -*-
"""
Control Rig Tool - 토큰/식별자 상수.

원본 JUN_PY_ControlRigTool_V01_07.py 의 JUN_cage 클래스에 하드코딩되어 있던
Maya Set 네이밍 토큰(MSN_tkn_*)과 dictionary 키로 쓰이던 정수 ID 들을 한곳에 모은다.

약어:
    MSN : Maya Set Name
    tkn : token (set 이름에 포함되는 부분 문자열)
    rnm : real name (씬의 실제 오브젝트 이름)
    onm : object name
    PA  : preferred angle
"""


# =====================================================================
# Maya Set Name 토큰 (set 이름 부분 매칭용)
# =====================================================================

TKN_CAGE_ROOT = "Cage"

TKN_CAGE_01_POS = "Cage_01_pos"
TKN_CAGE_03_TGT = "Cage_03_Tgt"
TKN_CAGE_04_HELPER = "Cage_04_helper"

TKN_SPINE = "A00_Spine"

TKN_FINGERS_ZRO_L = "C01_Fingers_zro_L_meta_X"
TKN_FINGERS_ZRO_R = "C01_Fingers_zro_R_meta_X"

# Arm Left
TKN_ARM_L_01_UPPERARM = "A01_Arm_L_01_UpperArm"
TKN_ARM_L_02_LOWERARM = "A01_Arm_L_02_LowerArm"
TKN_ARM_L_03_WRIST = "A01_Arm_L_03_Wrist"
TKN_ARM_L_04_POLE = "A01_Arm_L_04_Pole"

# Arm Right
TKN_ARM_R_01_UPPERARM = "A02_Arm_R_01_UpperArm"
TKN_ARM_R_02_LOWERARM = "A02_Arm_R_02_LowerArm"
TKN_ARM_R_03_WRIST = "A02_Arm_R_03_Wrist"
TKN_ARM_R_04_POLE = "A02_Arm_R_04_Pole"

TKN_ARM_R_05_WRIST_WS = "Arm_R_03_Wrist_World"
TKN_ARM_R_05_WRIST_LS = "Arm_R_03_Wrist_Local"
TKN_ARM_R_05_FK_YDWN = "Arm_R_03_Wrist_FK_Ydwn"

# Leg Left
TKN_LEG_L_01 = "B01_Leg_L_01"
TKN_LEG_L_02 = "B01_Leg_L_02"
TKN_LEG_L_03 = "B01_Leg_L_03"
TKN_LEG_L_04 = "B01_Leg_L_04"
TKN_LEG_L_05 = "B01_Leg_L_05"
TKN_LEG_L_06_POLE = "B01_Leg_L_06_pole"

# Leg Right
TKN_LEG_R_01 = "B02_Leg_R_01"
TKN_LEG_R_02 = "B02_Leg_R_02"
TKN_LEG_R_03 = "B02_Leg_R_03"
TKN_LEG_R_04 = "B02_Leg_R_04"
TKN_LEG_R_05 = "B02_Leg_R_05"
TKN_LEG_R_06_POLE = "B02_Leg_R_06_pole"

TKN_POSE_OBJECTS = "C04_pose_obects"

# helper joint sets
TKN_HELPER_ARM_L = "A01_helper_arm_l"
TKN_HELPER_ARM_R = "A02_helper_arm_r"
TKN_HELPER_LEG_L = "A03_helper_leg_l"
TKN_HELPER_LEG_R = "A04_helper_leg_r"

# real-name 검색용 토큰
TKN_MAIN_GLOBAL_ZRO = "CH_n_MainGlobal_xx_zro"
TKN_OPTION_CTL = "OptionAll_xx_ctl"

TKN_POLEOBJ_ARM_L = "CH_l_ArmPoleSetup_xx_pos"
TKN_POLEOBJ_ARM_R = "CH_r_ArmPoleSetup_xx_pos"
TKN_POLEOBJ_LEG_L = "CH_l_LegPoleSetup_xx_pos"
TKN_POLEOBJ_LEG_R = "CH_r_LegPoleSetup_xx_pos"

# preferred angle 토큰
TKN_ARMJNT_L_PA = "A01_Arm_L_02_LowerArm"
TKN_ARMJNT_R_PA = "A02_Arm_R_02_LowerArm"
TKN_LEGJNT_L_PA = "B01_Leg_L_02"
TKN_LEGJNT_R_PA = "B02_Leg_R_02"

ONM_ARMJNT_L_PA = "l_LowerArm_xx_ikjnt"
ONM_ARMJNT_R_PA = "r_LowerArm_xx_ikjnt"
ONM_LEGJNT_L_PA = "l_knee_ikjnt"
ONM_LEGJNT_R_PA = "r_knee_ikjnt"

# pose object 연결 attribute 이름
ATTR_CON = "Con"
ATTR_FOLLOW = "Follow"


# =====================================================================
# dictionary 키로 쓰이는 정수 ID 스킴
#   원본 JUN_cage 의 self.arm_l/self.spine/... 정수 ID 를 그대로 유지한다.
#   set_rnm_lst_member 의 분기(value_is_*)가 이 범위에 의존하므로 값 변경 금지.
# =====================================================================

# list-of-MSN (0 ~)
ID_START_LST_OF_MSN = 0
ARM_L = 0
ARM_R = 1
LEG_L = 2
LEG_R = 3

# single MSN (100 ~)
ID_START_SINGLE_MSN = 100
SPINE = 100
FINGERS_L = 101
FINGERS_R = 102
SHOULDER_ALL = 103
SHOULDER_L = 104
SHOULDER_R = 105
WRIST_L_WS = 106
WRIST_L_LS = 107
WRIST_R_WS = 108
WRIST_R_LS = 109
WRIST_R_FK_YDWN = 110
POSE_OBJECTS = 111

# preferred angle joints (200 ~)
ID_START_PA = 200
ELBOW_JNT_L = 200
ELBOW_JNT_R = 201
KNEE_JNT_L = 202
KNEE_JNT_R = 203

# pole vector objects (300 ~)
ID_START_POLE_VECTOR_OBJECTS = 300
POLE_VEC_OBJ_ARM_L = 300
POLE_VEC_OBJ_ARM_R = 301
POLE_VEC_OBJ_LEG_L = 302
POLE_VEC_OBJ_LEG_R = 303

# helper joints (400 ~)
ID_START_HELPER_JNTS = 400
KEY_HELPER_JNTS_ARM_L = 400
KEY_HELPER_JNTS_ARM_R = 401
KEY_HELPER_JNTS_LEG_L = 402
KEY_HELPER_JNTS_LEG_R = 403

ID_END = 999
