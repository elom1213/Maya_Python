# -*- coding: utf-8 -*-
"""
RigMatcher - FK<->IK / IK<->IK 매칭 엔진.

원본 JUN_matcher_v02 클래스 이식. joint chain 생성/orient, IK + pole vector 셋업,
target -> follower transform 매칭, 그리고 spine/arm/leg/finger 별 케이지 매칭을 담당한다.

- target / follower 리스트는 원본처럼 textScrollList 에서 읽지 않고, UI 가 넘긴
  파이썬 리스트를 set_matcher 로 주입한다.
- 모든 씬 조작은 MayaScene 어댑터 경유. IK 생성은 ik_builder 사용.
- 알고리즘(orient 축 순서, pole vector 축, joint chain 인덱스, 거리 attribute 등)은
  원본과 동일하게 유지한다.
"""

import copy

from .maya_scene import MayaScene
from .ik_builder import create_ik_with_polevector


class RigMatcher(object):

    def __init__(self):
        self.tgt = None
        self.flw = None

        self.num_iter = 0

    # ----------------------------------------------------------------
    # joint chain
    # ----------------------------------------------------------------

    def create_joint_chain(self, objs, jntOrd="xyz", secAxOri="yup", suffix="_jnt"):
        joints = []
        MayaScene.select_clear()  # start clean

        for obj in objs:
            if not MayaScene.exists(obj):
                MayaScene.warning("Object '{0}' does not exist, skipping.".format(obj))
                continue

            pos = MayaScene.get_translation(obj, world=True)
            jnt = MayaScene.create_joint("{0}{1}".format(obj, suffix), pos)
            joints.append(jnt)

        # orient the joint chain
        if joints:
            MayaScene.orient_joint(joints[0], jntOrd, secAxOri)
            MayaScene.orient_joint_end(joints[-1])

        return joints

    @staticmethod
    def vector_element_wise_multiply(v1, v2):
        return [a * b for a, b in zip(v1, v2)]

    # ----------------------------------------------------------------
    # target / follower 리스트 주입
    # ----------------------------------------------------------------

    def set_matcher(self, tgt_list, flw_list):
        """원본 set_matcher. tgt/flw 리스트와 반복 횟수(둘 중 짧은 길이)를 설정."""
        self.tgt = tgt_list if tgt_list is not None else []
        self.flw = flw_list if flw_list is not None else []

        num_tgt = len(self.tgt)
        num_flw = len(self.flw)
        self.num_iter = num_tgt if num_tgt < num_flw else num_flw

    def type_is_set(self, type_input):
        return MayaScene.is_set(type_input)

    # ----------------------------------------------------------------
    # transform matching helpers
    # ----------------------------------------------------------------

    def match_set_members_to_single_tgt(self, str_tgt_single, str_setName,
                                        int_rotOrder=1, int_rotAxis=1,
                                        int_trs=1, int_rot=1):
        lst_tgt_single = [str_tgt_single]
        lst_members_from_set = MayaScene.sets_query(str_setName)

        for str_member_from_set in lst_members_from_set:
            lst_member_from_set = [str_member_from_set]
            MayaScene.match_transforms(
                lst_tgt_single, lst_member_from_set,
                int_rotOrder, int_rotAxis, int_trs, int_rot
            )

    def match_lst_to_single_tgt(self, str_tgt_single, str_lstName):
        if not isinstance(str_tgt_single, list):
            str_tgt_single = [str_tgt_single]
        for i in range(0, len(str_lstName)):
            MayaScene.match_transforms(str_tgt_single, str_lstName[i], 1, 1, 1, 1)

    def lock_translation(self, objs):
        for obj in objs:
            for axis in ["tx", "ty", "tz"]:
                attr = "{0}.{1}".format(obj, axis)
                if MayaScene.exists(attr):
                    MayaScene.set_attr_lock(attr, lock=True)

    def group_list_items(self, objs, name="newGroup"):
        """유효한 오브젝트들을 하나의 그룹으로 묶는다. "" / None 은 무시."""
        valid_objs = [obj for obj in objs if obj and MayaScene.exists(obj)]
        if not valid_objs:
            raise ValueError("No valid objects found in the list.")
        return MayaScene.group(valid_objs, name)

    def filter_ik_handles(self, objs):
        """리스트에서 IK handle 만 추려 반환."""
        return [
            obj for obj in objs
            if MayaScene.exists(obj) and MayaScene.object_type(obj) == "ikHandle"
        ]

    def set_pos_for_given_axi_only(self, obj_given, axi="x", moving_dir="x+", moving_dist=50):
        """
        주어진 단일 축으로만 오브젝트를 이동 (world space).

        obj_given   : target object name
        axi         : 'x', 'y', or 'z'
        moving_dir  : 'x+', 'x-', 'y+', 'y-', 'z+', 'z-'
        moving_dist : 이동 거리
        """
        if not MayaScene.exists(obj_given):
            raise RuntimeError("Object does not exist: {0}".format(obj_given))

        axi = axi.lower()
        if axi not in ("x", "y", "z"):
            raise ValueError("axi must be 'x', 'y', or 'z'")

        pos_ori_world = MayaScene.get_translation(obj_given, world=True)
        axis_index = {"x": 0, "y": 1, "z": 2}[axi]
        sign = 1 if moving_dir.endswith("+") else -1
        pos_ori_world[axis_index] += sign * moving_dist

        MayaScene.set_translation(obj_given, pos_ori_world, world=True)

    # ----------------------------------------------------------------
    # main match
    # ----------------------------------------------------------------

    def match(self, orient_to_joint=False, jntOrd="xyz", secAxOri="yup",
              is_leg=False, is_spine__=False, set_ik=False, pole_obj=None,
              helper_objs=None, tgt_given=None):
        member_tgts = copy.deepcopy(self.tgt)
        member_flws = copy.deepcopy(self.flw)
        lst_remain = []

        if orient_to_joint:
            member_tgts = self.create_joint_chain(member_tgts, jntOrd, secAxOri)

        if tgt_given:
            MayaScene.delete(member_tgts)
            member_tgts = tgt_given

        if is_leg:
            MayaScene.orient_joint(member_tgts[-3], "xzy", "yup")
            MayaScene.orient_joint_none(member_tgts[-1])
            MayaScene.match_transforms(member_tgts, helper_objs, 1, 1, 1, 1)
            lst_remain_A = create_ik_with_polevector(helper_objs[-2], helper_objs[-1], pole_obj, "ikSCsolver")
            lst_remain_B = create_ik_with_polevector(helper_objs[-3], helper_objs[-2], pole_obj, "ikSCsolver")

            lst_remain = [*lst_remain_A, *lst_remain_B]
            lst_remain_ik = self.filter_ik_handles(lst_remain)
            grp_remain = self.group_list_items(lst_remain_ik)

            MayaScene.set_translation(pole_obj[0], [0, 0, 0], world=False)
            self.set_pos_for_given_axi_only(pole_obj[0], axi="z", moving_dir="z+")
            posPole_local = MayaScene.get_translation(pole_obj[0], world=False)
            posPole_local[1] = 0
            MayaScene.set_translation(pole_obj[0], posPole_local, world=False)

            lst_remain_C = create_ik_with_polevector(helper_objs[0], helper_objs[2], pole_obj)
            lst_remain = [*lst_remain_A, *lst_remain_B, *lst_remain_C, grp_remain]

        elif is_spine__:
            MayaScene.orient_joint_none(member_tgts)
        elif set_ik and helper_objs:
            MayaScene.match_transforms(member_tgts, helper_objs, 1, 1, 1, 1)
            lst_remain = create_ik_with_polevector(helper_objs[0], helper_objs[2], pole_obj)

        for i in range(0, self.num_iter):
            member_flw = member_flws[i]
            member_tgt = member_tgts[i]

            if self.type_is_set(member_flw):
                if helper_objs:
                    helper_obj = helper_objs[i]
                    self.match_set_members_to_single_tgt(helper_obj, member_flw)
                else:
                    try:
                        self.match_set_members_to_single_tgt(member_tgt, member_flw)
                    except Exception:
                        print("match : error while matching set members to single target")
            else:
                member_flw = [member_flw]
                member_tgt = [member_tgt]
                MayaScene.match_transforms(member_tgt, member_flw, 1, 1, 1, 1)

        if orient_to_joint:
            MayaScene.delete(member_tgts)

        for item in lst_remain:
            try:
                MayaScene.delete(item)
            except Exception:
                print("match : error while deleting remaining item")

    # ----------------------------------------------------------------
    # helpers
    # ----------------------------------------------------------------

    def get_worldSpace_obj(self, obj):
        pos = MayaScene.get_translation(obj, world=True)
        loc = MayaScene.space_locator()[0]
        MayaScene.set_translation(loc, pos, world=True)
        return loc

    def match_flw_to_tgt_zro_rotate(self, tgt_idx=0, flw_idx=0, flw_given=None):
        member_flws = copy.deepcopy(self.flw)
        member_tgts = copy.deepcopy(self.tgt)
        if flw_given:
            member_flws = flw_given

        ws_obj = self.get_worldSpace_obj(member_tgts[tgt_idx])
        self.match_set_members_to_single_tgt(ws_obj, member_flws[flw_idx])

        MayaScene.delete(ws_obj)

    def get_distance(self, obj1, obj2):
        return MayaScene.distance(obj1, obj2)

    # ----------------------------------------------------------------
    # cage 별 매칭
    # ----------------------------------------------------------------

    def match_cage_spine(self):
        self.match(True, "yzx", "zup", False, True)

    def match_cage_arm_left(self, cage_given=None, pole_obj=None, helper_objs=None):
        self.match(True, "xyz", "yup", False, False, True, pole_obj, helper_objs)
        self.match_flw_to_tgt_zro_rotate(tgt_idx=2, flw_idx=2)

        pole_obj = cage_given.rnm_poleObj_armLeft[0]
        MayaScene.set_translation(pole_obj[0], [0, 0, 0], world=False)
        self.set_pos_for_given_axi_only(pole_obj[0], axi="z", moving_dir="z-")
        posPole_local = MayaScene.get_translation(pole_obj[0], world=False)
        posPole_local[1] = 0  # set ty to 0
        MayaScene.set_translation(pole_obj[0], posPole_local, world=False)

        self.match_set_members_to_single_tgt(pole_obj, cage_given.MSN_rnm_lst_arm_l[-1], int_rot=0)

        dist_arm_l_all = self.get_distance(self.tgt[0], self.tgt[2])
        dist_arm_l_up = self.get_distance(self.tgt[0], self.tgt[1])
        dist_arm_l_low = self.get_distance(self.tgt[1], self.tgt[2])

        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".Arm_L", dist_arm_l_all)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".arm_l_up", dist_arm_l_up)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".arm_l_low", dist_arm_l_low)

    def match_cage_arm_right(self, pole_obj=None, cage_given=None, helper_objs=None):
        jnts_arm_r_primX = self.create_joint_chain(self.tgt, suffix="_r_jnt")
        jnts_arm_l_from_oriRightArm = MayaScene.mirror_joint(jnts_arm_r_primX[0], ["_r_", "_l_"])
        jnts_arm_l_primX = self.create_joint_chain(jnts_arm_l_from_oriRightArm, suffix="_l_jnt_yUp")
        jnts_arm_r_primMX_yDwn = MayaScene.mirror_joint(jnts_arm_l_primX[0], ["_l_jnt_yUp", "_r_jnt_yDwn"])

        self.match(True, "xyz", "yup", False, False, True, pole_obj, helper_objs, tgt_given=jnts_arm_r_primMX_yDwn)
        self.match_flw_to_tgt_zro_rotate(tgt_idx=2, flw_idx=0, flw_given=cage_given.MSN_rnm_wrist_r_WS)

        member_tgts = copy.deepcopy(self.tgt)
        obj_wrist_r_Ydwn = self.get_worldSpace_obj(member_tgts[2])
        MayaScene.rotate(180, 0, 0, obj_wrist_r_Ydwn, relative=True, object_space=True)
        self.match_lst_to_single_tgt(obj_wrist_r_Ydwn, cage_given.MSN_rnm_lst_wrist_FK_Ydwn)

        dele_lst = [*jnts_arm_r_primX, *jnts_arm_l_from_oriRightArm, *jnts_arm_l_primX, *jnts_arm_r_primMX_yDwn, obj_wrist_r_Ydwn]
        for item in dele_lst:
            try:
                MayaScene.delete(item)
            except Exception:
                print("match_cage_arm_right : error while deleting temp joint")

        pole_obj = cage_given.rnm_poleObj_armRight[0]
        MayaScene.set_translation(pole_obj[0], [0, 0, 0], world=False)
        self.set_pos_for_given_axi_only(pole_obj[0], axi="z", moving_dir="z-")
        posPole_local = MayaScene.get_translation(pole_obj[0], world=False)
        posPole_local[1] = 0  # set ty to 0
        MayaScene.set_translation(pole_obj[0], posPole_local, world=False)

        self.match_set_members_to_single_tgt(pole_obj, cage_given.MSN_rnm_lst_arm_r[-1], int_rot=0)

        dist_arm_r_all = self.get_distance(self.tgt[0], self.tgt[2])
        dist_arm_r_up = self.get_distance(self.tgt[0], self.tgt[1])
        dist_arm_r_low = self.get_distance(self.tgt[1], self.tgt[2])

        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".Arm_r", dist_arm_r_all)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".arm_r_up", dist_arm_r_up)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".arm_r_low", dist_arm_r_low)

    def match_cage_leg_l(self, cage_given=None, pole_obj=None, helper_obj=None):
        self.match(True, "xzy", "zup", True, False, True, pole_obj, helper_obj)

        self.match_set_members_to_single_tgt(cage_given.rnm_poleObj_legLeft[0], cage_given.MSN_rnm_lst_leg_l[-1], int_rot=0)

        dist_leg_l_all = self.get_distance(self.tgt[0], self.tgt[2])
        dist_leg_l_up = self.get_distance(self.tgt[0], self.tgt[1])
        dist_leg_l_low = self.get_distance(self.tgt[1], self.tgt[2])

        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".Leg_L", dist_leg_l_all)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".leg_l_up", dist_leg_l_up)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".leg_l_low", dist_leg_l_low)

    def match_cage_leg_r(self, cage_given=None, pole_obj=None, helper_obj=None):
        self.match(True, "xzy", "zup", True, False, True, pole_obj, helper_obj)

        self.match_set_members_to_single_tgt(cage_given.rnm_poleObj_legRight[0], cage_given.MSN_rnm_lst_leg_r[-1], int_rot=0)

        dist_leg_r_all = self.get_distance(self.tgt[0], self.tgt[2])
        dist_leg_r_up = self.get_distance(self.tgt[0], self.tgt[1])
        dist_leg_r_low = self.get_distance(self.tgt[1], self.tgt[2])

        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".Leg_R", dist_leg_r_all)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".leg_r_up", dist_leg_r_up)
        MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".leg_r_low", dist_leg_r_low)

    def match_cage_fingers_left(self, cage_given=None):
        self.match()

    def match_cage_fingers_right(self, cage_given=None):
        self.match()
