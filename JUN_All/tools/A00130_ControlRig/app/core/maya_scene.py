# -*- coding: utf-8 -*-
"""
MayaScene - DCC 어댑터.

원본 JUN_PY_ControlRigTool_V01_07.py 의 코드 곳곳에 흩어져 있던 maya.cmds 호출을
한 곳으로 모은 얇은 래퍼. core/ui 의 다른 모듈은 cmds 를 직접 import 하지 않고
이 어댑터만 사용한다. (UI 비의존)

각 메서드는 원본의 cmds 호출과 동작이 동일하도록 1:1 로 이식했다.
"""

import math

import maya.cmds as cmds


class MayaScene(object):

    # ----------------------------------------------------------------
    # selection / query
    # ----------------------------------------------------------------

    @staticmethod
    def selection():
        return cmds.ls(sl=True, fl=True)

    @staticmethod
    def select(objs):
        cmds.select(objs)

    @staticmethod
    def select_clear():
        cmds.select(clear=True)

    @staticmethod
    def exists(obj):
        return cmds.objExists(obj)

    @staticmethod
    def object_type(obj):
        return cmds.objectType(obj)

    @staticmethod
    def is_set(obj):
        # 원본 type_is_set : cmds.objectType(x) in "objectSet"
        return cmds.objectType(obj) in "objectSet"

    @staticmethod
    def warning(message):
        cmds.warning(message)

    @staticmethod
    def ls(pattern, long=False):
        return cmds.ls(pattern, long=long)

    # ----------------------------------------------------------------
    # hierarchy / sets
    # ----------------------------------------------------------------

    @staticmethod
    def list_all_descendents(obj, shapes=False):
        return cmds.listRelatives(
            obj, allDescendents=True, path=True, shapes=shapes
        )

    @staticmethod
    def list_all_descendents_full_path(obj):
        return cmds.listRelatives(obj, allDescendents=True, fullPath=True)

    @staticmethod
    def sets_query(set_name):
        return cmds.sets(set_name, query=True)

    # ----------------------------------------------------------------
    # transform query / set
    # ----------------------------------------------------------------

    @staticmethod
    def get_translation(obj, world=True):
        return cmds.xform(obj, q=True, worldSpace=world, translation=True)

    @staticmethod
    def set_translation(obj, value, world=True):
        cmds.xform(obj, worldSpace=world, translation=value)

    @staticmethod
    def get_rotation(obj, world=True):
        return cmds.xform(obj, q=True, worldSpace=world, rotation=True)

    @staticmethod
    def set_rotation(obj, value, world=True):
        cmds.xform(obj, worldSpace=world, rotation=value)

    @staticmethod
    def get_rotate_order(obj):
        return cmds.xform(obj, q=True, rotateOrder=True)

    @staticmethod
    def set_rotate_order(obj, value):
        cmds.xform(obj, rotateOrder=value)

    @staticmethod
    def get_rotate_axis(obj):
        return cmds.xform(obj, q=True, rotateAxis=True)

    @staticmethod
    def set_rotate_axis(obj, value):
        cmds.xform(obj, rotateAxis=value)

    @staticmethod
    def rotate(rx, ry, rz, obj, relative=True, object_space=True):
        cmds.rotate(rx, ry, rz, obj, relative=relative, objectSpace=object_space)

    # ----------------------------------------------------------------
    # joints / IK
    # ----------------------------------------------------------------

    @staticmethod
    def create_joint(name, position):
        return cmds.joint(name=name, position=position)

    @staticmethod
    def orient_joint(joint, orient_joint, secondary_axis_orient,
                     children=True, zero_scale_orient=True):
        cmds.joint(
            joint,
            edit=True,
            orientJoint=orient_joint,
            secondaryAxisOrient=secondary_axis_orient,
            children=children,
            zeroScaleOrient=zero_scale_orient,
        )

    @staticmethod
    def orient_joint_none(joint, children=True, zero_scale_orient=True):
        cmds.joint(
            joint,
            edit=True,
            orientJoint="none",
            children=children,
            zeroScaleOrient=zero_scale_orient,
        )

    @staticmethod
    def orient_joint_end(joint):
        # 원본: cmds.joint(joints[-1], e=True, oj='none', ch=True, zso=True)
        cmds.joint(joint, e=True, oj="none", ch=True, zso=True)

    @staticmethod
    def set_preferred_angles(joint):
        cmds.joint(joint, edit=True, setPreferredAngles=True)

    @staticmethod
    def ik_handle(start_joint, end_joint, solver):
        return cmds.ikHandle(sj=start_joint, ee=end_joint, sol=solver)

    @staticmethod
    def pole_vector_constraint(pv_object, ik_handle):
        return cmds.poleVectorConstraint(pv_object, ik_handle)

    @staticmethod
    def parent_constraint(driver, target, maintain_offset=True):
        return cmds.parentConstraint(driver, target, mo=maintain_offset)

    @staticmethod
    def mirror_joint(joint, search_replace):
        return cmds.mirrorJoint(
            joint,
            mirrorYZ=True,
            mirrorBehavior=True,
            searchReplace=search_replace,
        )

    # ----------------------------------------------------------------
    # general object operations
    # ----------------------------------------------------------------

    @staticmethod
    def duplicate(obj):
        return cmds.duplicate(obj)

    @staticmethod
    def rename(obj, new_name):
        return cmds.rename(obj, new_name)

    @staticmethod
    def parent_to_world(obj):
        cmds.parent(obj, world=True)

    @staticmethod
    def delete(obj):
        cmds.delete(obj)

    @staticmethod
    def group(objs, name):
        return cmds.group(objs, name=name)

    @staticmethod
    def space_locator():
        return cmds.spaceLocator()

    @staticmethod
    def set_attr(attr, value):
        cmds.setAttr(attr, value)

    @staticmethod
    def set_attr_lock(attr, lock=True):
        cmds.setAttr(attr, lock=lock)

    @staticmethod
    def set_visibility(obj, value):
        cmds.setAttr(obj + ".visibility", value)

    @staticmethod
    def list_connections(node, attr):
        full_attr = "{0}.{1}".format(node, attr)
        return cmds.listConnections(full_attr, s=True, d=True) or []

    # ----------------------------------------------------------------
    # math helpers
    # ----------------------------------------------------------------

    @staticmethod
    def distance(obj1, obj2):
        pos1 = cmds.xform(obj1, query=True, worldSpace=True, translation=True)
        pos2 = cmds.xform(obj2, query=True, worldSpace=True, translation=True)
        return math.sqrt(
            (pos2[0] - pos1[0]) ** 2
            + (pos2[1] - pos1[1]) ** 2
            + (pos2[2] - pos1[2]) ** 2
        )

    # ----------------------------------------------------------------
    # transform matching (원본 JUN_MATCH_twoObjects)
    # ----------------------------------------------------------------

    @staticmethod
    def match_transforms(tgt_list, flw_list,
                         match_rot_order=1, match_rot_axis=1,
                         match_trs=1, match_rot=1):
        """
        target 의 transform 을 follower 로 복사한다.

        원본 JUN_MATCH_twoObjects 와 동일한 동작(조건 분기 포함)을 유지한다.
        rotateOrder 를 target 값으로 잠깐 바꿔 적용한 뒤 follower 의 원래
        rotateOrder 로 되돌린다.
        """
        # 원본 동작 보존: flw_list 가 list 가 아닐 때 tgt_list 를 감싼다.
        if not isinstance(flw_list, list):
            tgt_list = [tgt_list]

        if not isinstance(flw_list, list):
            flw_list = [flw_list]

        for i in range(0, len(tgt_list)):

            rot_order = cmds.xform(tgt_list[i], q=True, rotateOrder=True)
            rot_axis = cmds.xform(tgt_list[i], q=True, rotateAxis=True)
            trs = cmds.xform(tgt_list[i], q=True, worldSpace=True, translation=True)
            rot = cmds.xform(tgt_list[i], q=True, worldSpace=True, rotation=True)

            try:
                rot_order_ori = cmds.xform(flw_list[i], q=True, rotateOrder=True)

                if match_rot_order == 1:
                    cmds.xform(flw_list[i], rotateOrder=rot_order)

                if match_rot_axis == 1:
                    cmds.xform(flw_list[i], rotateAxis=rot_axis)

                if match_trs == 1:
                    cmds.xform(flw_list[i], worldSpace=True, translation=trs)

                if match_rot == 1:
                    cmds.xform(flw_list[i], worldSpace=True, rotation=rot)

                cmds.xform(flw_list[i], rotateOrder=rot_order_ori)
            except Exception:
                print("match error : failed to match transform")
