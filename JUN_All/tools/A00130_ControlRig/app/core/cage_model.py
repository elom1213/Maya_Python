# -*- coding: utf-8 -*-
"""
CageModel - 케이지(rig 구조) 데이터 모델.

원본 JUN_cage 클래스 이식. Maya Set 토큰(token)과 실제 씬 오브젝트 이름(rnm)을
매핑하고, 림(arm/leg/spine/finger)별 오브젝트 리스트·preferred angle·pole vector·
helper joint 를 보관한다.

- 토큰 문자열 상수는 constants.py 에서 가져온다.
- 모든 씬 조회는 MayaScene 어댑터 경유.
- 원본의 public 속성 이름(MSN_rnm_lst_*, rnm_poleObj_*, rnm_optionCtl 등)은
  RigMatcher 가 직접 참조하므로 그대로 유지한다.
- 원본에서 전역(JUN_cage_glo)이던 것을 인스턴스로 사용한다.
"""

from . import constants as c
from .maya_scene import MayaScene
from .selection_utils import make_hierarchy


class CageModel(object):

    def __init__(self):

        # --- set token : set name ---
        self.MSN_tkn_Cage_root = c.TKN_CAGE_ROOT
        self.MSN_tkn_Cage_01_pos = c.TKN_CAGE_01_POS
        self.MSN_tkn_Cage_03_Tgt = c.TKN_CAGE_03_TGT
        self.MSN_tkn_Cage_04_helper = c.TKN_CAGE_04_HELPER

        self.MSN_tkn_spine = c.TKN_SPINE

        self.MSN_tkn_C01_Fingers_zro_L = c.TKN_FINGERS_ZRO_L
        self.MSN_tkn_C01_Fingers_zro_R = c.TKN_FINGERS_ZRO_R

        self.MSN_tkn_A01_Arm_L_01_UpperArm = c.TKN_ARM_L_01_UPPERARM
        self.MSN_tkn_A01_Arm_L_02_LowerArm = c.TKN_ARM_L_02_LOWERARM
        self.MSN_tkn_A01_Arm_L_03_Wrist = c.TKN_ARM_L_03_WRIST
        self.MSN_tkn_A01_Arm_L_04_Pole = c.TKN_ARM_L_04_POLE

        self.MSN_tkn_A02_Arm_R_01_UpperArm = c.TKN_ARM_R_01_UPPERARM
        self.MSN_tkn_A02_Arm_R_02_LowerArm = c.TKN_ARM_R_02_LOWERARM
        self.MSN_tkn_A02_Arm_R_03_Wrist = c.TKN_ARM_R_03_WRIST
        self.MSN_tkn_A02_Arm_R_04_Pole = c.TKN_ARM_R_04_POLE

        self.MSN_tkn_A02_Arm_R_05_Wrist_WS = c.TKN_ARM_R_05_WRIST_WS
        self.MSN_tkn_A02_Arm_R_05_Wrist_LS = c.TKN_ARM_R_05_WRIST_LS
        self.MSN_tkn_A02_Arm_R_05_FK_Ydwn = c.TKN_ARM_R_05_FK_YDWN

        self.MSN_tkn_B01_Leg_L_01 = c.TKN_LEG_L_01
        self.MSN_tkn_B01_Leg_L_02 = c.TKN_LEG_L_02
        self.MSN_tkn_B01_Leg_L_03 = c.TKN_LEG_L_03
        self.MSN_tkn_B01_Leg_L_04 = c.TKN_LEG_L_04
        self.MSN_tkn_B01_Leg_L_05 = c.TKN_LEG_L_05
        self.MSN_tkn_B01_Leg_L_06_pole = c.TKN_LEG_L_06_POLE

        self.MSN_tkn_B02_Leg_R_01 = c.TKN_LEG_R_01
        self.MSN_tkn_B02_Leg_R_02 = c.TKN_LEG_R_02
        self.MSN_tkn_B02_Leg_R_03 = c.TKN_LEG_R_03
        self.MSN_tkn_B02_Leg_R_04 = c.TKN_LEG_R_04
        self.MSN_tkn_B02_Leg_R_05 = c.TKN_LEG_R_05
        self.MSN_tkn_B02_Leg_R_06_pole = c.TKN_LEG_R_06_POLE

        self.MSN_tkn_C04_pose_obects = c.TKN_POSE_OBJECTS

        self.MSN_tkn_A01_helper_arm_l = c.TKN_HELPER_ARM_L
        self.MSN_tkn_A02_helper_arm_r = c.TKN_HELPER_ARM_R
        self.MSN_tkn_A03_helper_leg_l = c.TKN_HELPER_LEG_L
        self.MSN_tkn_A04_helper_leg_r = c.TKN_HELPER_LEG_R

        # --- set token : real name 검색 토큰 ---
        self.tkn_CH_n_MainGlobal_xx_zro = c.TKN_MAIN_GLOBAL_ZRO
        self.tkn_optionCtl = c.TKN_OPTION_CTL

        self.tkn_poleObj_armLeft = c.TKN_POLEOBJ_ARM_L
        self.tkn_poleObj_armRight = c.TKN_POLEOBJ_ARM_R
        self.tkn_poleObj_legLefg = c.TKN_POLEOBJ_LEG_L
        self.tkn_poleObj_legRight = c.TKN_POLEOBJ_LEG_R

        # --- set token : preferred angle ---
        self.MSN_tkn_armJnt_l_PA = c.TKN_ARMJNT_L_PA
        self.MSN_tkn_armJnt_r_PA = c.TKN_ARMJNT_R_PA
        self.MSN_tkn_legJnt_l_PA = c.TKN_LEGJNT_L_PA
        self.MSN_tkn_legJnt_r_PA = c.TKN_LEGJNT_R_PA

        self.onm_tkn_armJnt_l_PA = c.ONM_ARMJNT_L_PA
        self.onm_tkn_armJnt_r_PA = c.ONM_ARMJNT_R_PA
        self.onm_tkn_legJnt_l_PA = c.ONM_LEGJNT_L_PA
        self.onm_tkn_legJnt_r_PA = c.ONM_LEGJNT_R_PA

        self.MSN_tkn_lst_Arm_L = [self.MSN_tkn_A01_Arm_L_01_UpperArm, self.MSN_tkn_A01_Arm_L_02_LowerArm, self.MSN_tkn_A01_Arm_L_03_Wrist, self.MSN_tkn_A01_Arm_L_04_Pole]
        self.MSN_tkn_lst_Arm_R = [self.MSN_tkn_A02_Arm_R_01_UpperArm, self.MSN_tkn_A02_Arm_R_02_LowerArm, self.MSN_tkn_A02_Arm_R_03_Wrist, self.MSN_tkn_A02_Arm_R_04_Pole]

        self.MSN_tkn_lst_leg_L = [self.MSN_tkn_B01_Leg_L_01, self.MSN_tkn_B01_Leg_L_02, self.MSN_tkn_B01_Leg_L_03, self.MSN_tkn_B01_Leg_L_04, self.MSN_tkn_B01_Leg_L_05, self.MSN_tkn_B01_Leg_L_06_pole]
        self.MSN_tkn_lst_leg_R = [self.MSN_tkn_B02_Leg_R_01, self.MSN_tkn_B02_Leg_R_02, self.MSN_tkn_B02_Leg_R_03, self.MSN_tkn_B02_Leg_R_04, self.MSN_tkn_B02_Leg_R_05, self.MSN_tkn_B02_Leg_R_06_pole]

        # --- real name (런타임에 set 에서 채워짐) ---
        self.MSN_rnm_Cage_01_pos_root = ""
        self.MSN_rnm_Cage_03_Tgt_root = ""

        self.MSN_rnm_wrist_r_WS = []
        self.MSN_rnm_wrist_r_LS = []

        self.MSN_rnm_Cage_01_pos_childe = None
        self.MSN_rnm_Cage_03_Tgt_childe = None

        self.MSN_rnm_lst_spine = []
        self.MSN_rnm_lst_shoulders = []

        self.MSN_rnm_lst_fingers_l = []
        self.MSN_rnm_lst_fingers_r = []

        self.MSN_rnm_lst_arm_l = []
        self.MSN_rnm_lst_arm_r = []
        self.MSN_rnm_lst_leg_l = []
        self.MSN_rnm_lst_leg_r = []

        self.MSN_rnm_lst_wrist_l_WS = []
        self.MSN_rnm_lst_wrist_l_LS = []
        self.MSN_rnm_lst_wrist_r_WS = []
        self.MSN_rnm_lst_wrist_r_LS = []
        self.MSN_rnm_lst_wrist_FK_Ydwn = []

        self.MSN_rnm_pose_objects = []

        self.rnm_CH_n_MainGlobal_xx_zro = []
        self.rnm_optionCtl = []

        self.rnm_armJnt_l_PA = []
        self.rnm_armJnt_r_PA = []
        self.rnm_legJnt_l_PA = []
        self.rnm_legJnt_r_PA = []

        self.rnm_poleObj_armLeft = []
        self.rnm_poleObj_armRight = []
        self.rnm_poleObj_legLeft = []
        self.rnm_poleObj_legRight = []

        self.rnm_helperJnts_arm_l = []
        self.rnm_helperJnts_arm_r = []
        self.rnm_helperJnts_leg_l = []
        self.rnm_helperJnts_leg_r = []

        # ===================================================================
        # dictionary 키 (정수 ID) — constants 와 동일
        self.idStart_lst_of_MSN = c.ID_START_LST_OF_MSN
        self.arm_l = c.ARM_L
        self.arm_r = c.ARM_R
        self.leg_l = c.LEG_L
        self.leg_r = c.LEG_R

        self.idStart_SingleMSN = c.ID_START_SINGLE_MSN
        self.spine = c.SPINE
        self.fingers_l = c.FINGERS_L
        self.fingers_r = c.FINGERS_R
        self.shoulder_all = c.SHOULDER_ALL
        self.shoulder_l = c.SHOULDER_L
        self.shoulder_r = c.SHOULDER_R
        self.wirst_l_WS = c.WRIST_L_WS
        self.wirst_l_LS = c.WRIST_L_LS
        self.wirst_r_WS = c.WRIST_R_WS
        self.wirst_r_LS = c.WRIST_R_LS
        self.wirst_r_FK_ydwn = c.WRIST_R_FK_YDWN
        self.pose_objects = c.POSE_OBJECTS

        self.idStart_PA = c.ID_START_PA
        self.elbowJnt_l = c.ELBOW_JNT_L
        self.elbowJnt_r = c.ELBOW_JNT_R
        self.kneeJnt_l = c.KNEE_JNT_L
        self.kneeJnt_r = c.KNEE_JNT_R

        self.idStart_poleVectorObjects = c.ID_START_POLE_VECTOR_OBJECTS
        self.poleVecObj_arm_l = c.POLE_VEC_OBJ_ARM_L
        self.poleVecObj_arm_r = c.POLE_VEC_OBJ_ARM_R
        self.poleVecObj_leg_l = c.POLE_VEC_OBJ_LEG_L
        self.poleVecObj_leg_r = c.POLE_VEC_OBJ_LEG_R

        self.idStart_helperJnts = c.ID_START_HELPER_JNTS
        self.key_helperJnts_arm_l = c.KEY_HELPER_JNTS_ARM_L
        self.key_helperJnts_arm_r = c.KEY_HELPER_JNTS_ARM_R
        self.key_helperJnts_leg_l = c.KEY_HELPER_JNTS_LEG_L
        self.key_helperJnts_leg_r = c.KEY_HELPER_JNTS_LEG_R

        self.idEnd = c.ID_END

        # value = list of MSN
        self.tkn_lstDic = {self.arm_l: self.MSN_tkn_lst_Arm_L,
                           self.arm_r: self.MSN_tkn_lst_Arm_R,
                           self.leg_l: self.MSN_tkn_lst_leg_L,
                           self.leg_r: self.MSN_tkn_lst_leg_R}

        self.rnm_lstDic = {self.arm_l: self.MSN_rnm_lst_arm_l,
                           self.arm_r: self.MSN_rnm_lst_arm_r,
                           self.leg_l: self.MSN_rnm_lst_leg_l,
                           self.leg_r: self.MSN_rnm_lst_leg_r}

        # value = string token
        self.tkn_strDic = {self.spine: self.MSN_tkn_spine,
                           self.fingers_l: self.MSN_tkn_C01_Fingers_zro_L,
                           self.fingers_r: self.MSN_tkn_C01_Fingers_zro_R,
                           self.wirst_l_WS: None,
                           self.wirst_l_LS: None,
                           self.wirst_r_WS: self.MSN_tkn_A02_Arm_R_05_Wrist_WS,
                           self.wirst_r_LS: self.MSN_tkn_A02_Arm_R_05_Wrist_LS,
                           self.wirst_r_FK_ydwn: self.MSN_tkn_A02_Arm_R_05_FK_Ydwn,
                           self.pose_objects: self.MSN_tkn_C04_pose_obects}

        self.rnm_strDic = {self.spine: self.MSN_rnm_lst_spine,
                           self.fingers_l: self.MSN_rnm_lst_fingers_l,
                           self.fingers_r: self.MSN_rnm_lst_fingers_r,
                           self.wirst_l_WS: None,
                           self.wirst_l_LS: None,
                           self.wirst_r_WS: self.MSN_rnm_lst_wrist_r_WS,
                           self.wirst_r_LS: self.MSN_rnm_lst_wrist_r_LS,
                           self.wirst_r_FK_ydwn: self.MSN_rnm_lst_wrist_FK_Ydwn,
                           self.pose_objects: self.MSN_rnm_pose_objects}

        # value = preferred angle joint
        self.tkn_MSN_PA = {self.elbowJnt_l: self.MSN_tkn_armJnt_l_PA,
                           self.elbowJnt_r: self.MSN_tkn_armJnt_r_PA,
                           self.kneeJnt_l: self.MSN_tkn_legJnt_l_PA,
                           self.kneeJnt_r: self.MSN_tkn_legJnt_r_PA}

        self.tkn_onm_PA = {self.elbowJnt_l: self.onm_tkn_armJnt_l_PA,
                           self.elbowJnt_r: self.onm_tkn_armJnt_r_PA,
                           self.kneeJnt_l: self.onm_tkn_legJnt_l_PA,
                           self.kneeJnt_r: self.onm_tkn_legJnt_r_PA}

        self.rnm_onm_PA = {self.elbowJnt_l: self.rnm_armJnt_l_PA,
                           self.elbowJnt_r: self.rnm_armJnt_r_PA,
                           self.kneeJnt_l: self.rnm_legJnt_l_PA,
                           self.kneeJnt_r: self.rnm_legJnt_r_PA}

        # value = pole vector object (helper joint 에 ik 걸 때 사용)
        self.dic_tkn_poleVecObjs = {self.poleVecObj_arm_l: self.tkn_poleObj_armLeft,
                                    self.poleVecObj_arm_r: self.tkn_poleObj_armRight,
                                    self.poleVecObj_leg_l: self.tkn_poleObj_legLefg,
                                    self.poleVecObj_leg_r: self.tkn_poleObj_legRight}

        self.dic_rnm_poleVecObjs = {self.poleVecObj_arm_l: self.rnm_poleObj_armLeft,
                                    self.poleVecObj_arm_r: self.rnm_poleObj_armRight,
                                    self.poleVecObj_leg_l: self.rnm_poleObj_legLeft,
                                    self.poleVecObj_leg_r: self.rnm_poleObj_legRight}

        self.dic_rnm_helperObjs = {self.key_helperJnts_arm_l: self.rnm_helperJnts_arm_l,
                                   self.key_helperJnts_arm_r: self.rnm_helperJnts_arm_r,
                                   self.key_helperJnts_leg_l: self.rnm_helperJnts_leg_l,
                                   self.key_helperJnts_leg_r: self.rnm_helperJnts_leg_r}

        # cage set name dictionary
        self.tkn_MSN = {self.wirst_r_WS: self.MSN_rnm_wrist_r_WS,
                        self.wirst_r_LS: self.MSN_rnm_wrist_r_LS}

        # checker 와 통신용 dictionary / list
        self.rnm_dic_all = {self.spine: self.MSN_rnm_lst_spine,
                            self.shoulder_all: self.MSN_rnm_lst_shoulders,
                            self.arm_l: self.MSN_rnm_lst_arm_l,
                            self.arm_r: self.MSN_rnm_lst_arm_r,
                            self.leg_l: self.MSN_rnm_lst_leg_l,
                            self.leg_r: self.MSN_rnm_lst_leg_r,
                            self.fingers_l: self.MSN_rnm_lst_fingers_l,
                            self.fingers_r: self.MSN_rnm_lst_fingers_r}

        self.rnm_lst_all = [self.MSN_rnm_lst_spine,
                            self.MSN_rnm_lst_shoulders,
                            self.MSN_rnm_lst_arm_l,
                            self.MSN_rnm_lst_arm_r,
                            self.MSN_rnm_lst_leg_l,
                            self.MSN_rnm_lst_leg_r,
                            self.MSN_rnm_lst_fingers_l,
                            self.MSN_rnm_lst_fingers_r]

        self.rnm_lst_PA = [None,
                           None,
                           self.rnm_armJnt_l_PA,
                           self.rnm_armJnt_r_PA,
                           self.rnm_legJnt_l_PA,
                           self.rnm_legJnt_r_PA,
                           None,
                           None]

        # cbg(checkbox) 인덱스 — 리스트로 감싸 참조 공유(원본 동작 유지)
        self.idx_spine = [-1]
        self.idx_shoulder = [-1]
        self.idx_arm_l = [-1]
        self.idx_arm_r = [-1]
        self.idx_leg_l = [-1]
        self.idx_leg_r = [-1]
        self.idx_fingers_l = [-1]
        self.idx_fingers_r = [-1]

        self.lst_idx = [self.idx_spine,
                        self.idx_shoulder,
                        self.idx_arm_l,
                        self.idx_arm_r,
                        self.idx_leg_l,
                        self.idx_leg_r,
                        self.idx_fingers_l,
                        self.idx_fingers_r]

        self.len_lst_idx = len(self.lst_idx)

        # pose object 연결 attribute
        self.attr_Con = c.ATTR_CON
        self.attr_Follow = c.ATTR_FOLLOW

    # ===================================================================
    # is__ predicate
    # ===================================================================

    def is_JUN(self, idx_given, idx_set):
        return True if idx_given == idx_set else False

    def is_spine(self, idx):
        return self.is_JUN(idx, self.idx_spine[0])

    def is_arm_left(self, idx):
        return self.is_JUN(idx, self.idx_arm_l[0])

    def is_arm_right(self, idx):
        return self.is_JUN(idx, self.idx_arm_r[0])

    def is_leg_left(self, idx):
        return self.is_JUN(idx, self.idx_leg_l[0])

    def is_leg_right(self, idx):
        return self.is_JUN(idx, self.idx_leg_r[0])

    def is_fingers_left(self, idx):
        return self.is_JUN(idx, self.idx_fingers_l[0])

    def is_fingers_right(self, idx):
        return self.is_JUN(idx, self.idx_fingers_r[0])

    # ===================================================================
    # setter (set 에서 real name 추출)
    # ===================================================================

    def set_rnm_str_pos_root(self, str_rnm):
        self.MSN_rnm_Cage_01_pos_root = str_rnm

    def set_rnm_str_tgt_root(self, str_rnm):
        self.MSN_rnm_Cage_03_Tgt_root = str_rnm

    def set_rnm_str_helper(self, str_rnm):
        str_setChild = MayaScene.sets_query(str_rnm)
        for str_set in str_setChild:
            if self.MSN_tkn_A01_helper_arm_l in str_set:
                self.rnm_helperJnts_arm_l.extend(MayaScene.sets_query(str_set))
                self.rnm_helperJnts_arm_l.sort()

            if self.MSN_tkn_A02_helper_arm_r in str_set:
                self.rnm_helperJnts_arm_r.extend(MayaScene.sets_query(str_set))
                self.rnm_helperJnts_arm_r.sort()

            if self.MSN_tkn_A03_helper_leg_l in str_set:
                self.rnm_helperJnts_leg_l.extend(MayaScene.sets_query(str_set))
                self.rnm_helperJnts_leg_l.sort()

            if self.MSN_tkn_A04_helper_leg_r in str_set:
                self.rnm_helperJnts_leg_r.extend(MayaScene.sets_query(str_set))
                self.rnm_helperJnts_leg_r.sort()

    def set_selected_objs(self, selected_items):
        """
        원본 set_tsl_selected_objs. textScrollList 대신 UI 가 선택 항목 리스트를 넘긴다.
        MainGlobal zro 노드를 찾고, 그 계층에서 option controller 를 찾아 보관.
        """
        for item in selected_items:
            if self.tkn_CH_n_MainGlobal_xx_zro in item:
                self.rnm_CH_n_MainGlobal_xx_zro.append(item)

        set_objs_child = set(make_hierarchy(self.rnm_CH_n_MainGlobal_xx_zro, True, True))
        for obj in set_objs_child:
            if self.tkn_optionCtl in obj:
                self.rnm_optionCtl.append(obj)

    def set_rnm_lst_pos_child(self):
        if self.MSN_rnm_Cage_01_pos_root is not None:
            self.MSN_rnm_Cage_01_pos_childe = MayaScene.sets_query(self.MSN_rnm_Cage_01_pos_root)
            self.MSN_rnm_Cage_01_pos_childe.sort()

    def set_rnm_lst_tgt_child(self):
        if self.MSN_rnm_Cage_03_Tgt_root is not None:
            self.MSN_rnm_Cage_03_Tgt_childe = MayaScene.sets_query(self.MSN_rnm_Cage_03_Tgt_root)
            self.MSN_rnm_Cage_03_Tgt_childe.sort()

    def value_is_singleMSN(self, key_input):
        return True if key_input >= self.idStart_SingleMSN and key_input < self.idStart_PA else False

    def value_is_jnt_for_PA(self, key_input):
        return True if key_input >= self.idStart_PA and key_input < self.idStart_poleVectorObjects else False

    def value_is_poleVectorObject(self, key_input):
        return True if key_input >= self.idStart_poleVectorObjects and key_input < self.idStart_helperJnts else False

    def value_is_helper_jnts(self, key_input):
        return True if key_input >= self.idStart_helperJnts and key_input < self.idEnd else False

    def set_MSN_rnm_for_given_key(self, key_input, MSN_rnm_pos):
        try:
            self.tkn_MSN[key_input].append(MSN_rnm_pos)
        except Exception:
            print("set_MSN_rnm_for_given_key : key not in tkn_MSN")

    def find_object_by_name(self, substring):
        # namespace 유무 모두 포함
        all_objs = MayaScene.ls("*:*", long=True) + MayaScene.ls("*", long=True)
        matches = []
        for obj in all_objs:
            short_name = obj.split(":")[-1]
            if substring in short_name:
                matches.append(obj)
        return matches

    def set_rnm_lst_member(self, key_input):

        if self.value_is_singleMSN(key_input):
            tkn_str_input = self.tkn_strDic[key_input]
            rnm_str_input = self.rnm_strDic[key_input]

            for MSN_rnm_pos in self.MSN_rnm_Cage_01_pos_childe:
                if tkn_str_input in MSN_rnm_pos:
                    self.set_MSN_rnm_for_given_key(key_input, MSN_rnm_pos)
                    for str_obj in MayaScene.sets_query(MSN_rnm_pos):
                        rnm_str_input.append(str_obj)

            rnm_str_input.sort()

        elif self.value_is_jnt_for_PA(key_input):
            tkn_MSN_PA_keyed = self.tkn_MSN_PA[key_input]
            tkn_onm_PA_keyed = self.tkn_onm_PA[key_input]
            rnm_onm_PA_keyed = self.rnm_onm_PA[key_input]

            for MSN_rnm_pos in self.MSN_rnm_Cage_01_pos_childe:
                if tkn_MSN_PA_keyed in MSN_rnm_pos:
                    self.set_MSN_rnm_for_given_key(key_input, MSN_rnm_pos)
                    for rnm_onm_from_set in MayaScene.sets_query(MSN_rnm_pos):
                        if tkn_onm_PA_keyed in rnm_onm_from_set:
                            rnm_onm_PA_keyed.append(rnm_onm_from_set)

        elif self.value_is_poleVectorObject(key_input):
            tkn_poleVecObj = self.dic_tkn_poleVecObjs[key_input]
            cage_rnm_poleVecObj = self.dic_rnm_poleVecObjs[key_input]
            secne_rnm_poleVecObj = self.find_object_by_name(tkn_poleVecObj)
            cage_rnm_poleVecObj.append(secne_rnm_poleVecObj)

        else:
            tkn_lst_input = self.tkn_lstDic[key_input]
            rnm_lst_input = self.rnm_lstDic[key_input]

            for tkn_setName in tkn_lst_input:
                for rnm_setName in self.MSN_rnm_Cage_01_pos_childe:
                    if tkn_setName in rnm_setName:
                        rnm_lst_input.append(rnm_setName)

            rnm_lst_input.sort()

    def clear_all(self):
        self.MSN_rnm_lst_spine.clear()
        self.MSN_rnm_lst_shoulders.clear()

        self.MSN_rnm_lst_fingers_l.clear()
        self.MSN_rnm_lst_fingers_r.clear()

        self.MSN_rnm_lst_arm_l.clear()
        self.MSN_rnm_lst_arm_r.clear()
        self.MSN_rnm_lst_leg_l.clear()
        self.MSN_rnm_lst_leg_r.clear()

        self.MSN_rnm_lst_wrist_l_WS.clear()
        self.MSN_rnm_lst_wrist_l_LS.clear()
        self.MSN_rnm_lst_wrist_r_WS.clear()
        self.MSN_rnm_lst_wrist_r_LS.clear()

        self.rnm_armJnt_l_PA.clear()
        self.rnm_armJnt_r_PA.clear()
        self.rnm_legJnt_l_PA.clear()
        self.rnm_legJnt_r_PA.clear()

        self.rnm_poleObj_armLeft.clear()
        self.rnm_poleObj_armRight.clear()
        self.rnm_poleObj_legLeft.clear()
        self.rnm_poleObj_legRight.clear()

        self.MSN_rnm_pose_objects.clear()
        # helper joint 리스트는 원본과 동일하게 clear 하지 않는다.

    def set_rnm_lst_all(self):
        self.clear_all()
        self.set_rnm_lst_pos_child()
        self.set_rnm_lst_tgt_child()

        self.set_rnm_lst_member(self.arm_l)
        self.set_rnm_lst_member(self.arm_r)
        self.set_rnm_lst_member(self.leg_l)
        self.set_rnm_lst_member(self.leg_r)

        self.set_rnm_lst_member(self.wirst_r_WS)
        self.set_rnm_lst_member(self.wirst_r_LS)
        self.set_rnm_lst_member(self.wirst_r_FK_ydwn)

        self.set_rnm_lst_member(self.spine)
        self.set_rnm_lst_member(self.fingers_l)
        self.set_rnm_lst_member(self.fingers_r)

        self.set_rnm_lst_member(self.elbowJnt_l)
        self.set_rnm_lst_member(self.elbowJnt_r)
        self.set_rnm_lst_member(self.kneeJnt_l)
        self.set_rnm_lst_member(self.kneeJnt_r)

        self.set_rnm_lst_member(self.poleVecObj_arm_l)
        self.set_rnm_lst_member(self.poleVecObj_arm_r)
        self.set_rnm_lst_member(self.poleVecObj_leg_l)
        self.set_rnm_lst_member(self.poleVecObj_leg_r)

        self.set_rnm_lst_member(self.pose_objects)

    def set_idx_for_cbg(self):
        for idx in range(self.len_lst_idx):
            self.lst_idx[idx][0] = idx

    # ===================================================================
    # getter
    # ===================================================================

    def get_rnm_dic(self, key_input):
        return self.rnm_dic_all[key_input]

    def get_rnm_lst(self, idx):
        return self.rnm_lst_all[idx]

    def get_rnm_PA(self, idx):
        return self.rnm_lst_PA[idx]

    def get_pos_objs(self):
        return self.MSN_rnm_pose_objects

    def get_pos_attr(self):
        return [self.attr_Con, self.attr_Follow]

    def get_pos_attr_con(self):
        return self.attr_Con

    def get_pos_attr_flw(self):
        return self.attr_Follow
