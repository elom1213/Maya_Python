# -*- coding: utf-8 -*-
"""
MayaScene - DCC 어댑터.

maya.cmds 호출을 한 곳으로 모은 얇은 래퍼. core/ui 의 다른 모듈은 cmds 를 직접
import 하지 않고 이 어댑터만 사용한다. (UI 비의존)

A00140_ConnectClosest 의 MayaScene 를 그대로 옮겨온 것이다(Connect Closest 탭용).
"""

import math

import maya.cmds as cmds


class MayaScene(object):

    # ----------------------------------------------------------------
    # selection / query
    # ----------------------------------------------------------------

    @staticmethod
    def selection():
        # flatten=True 로 컴포넌트가 아닌 오브젝트 단위로 받는다.
        return cmds.ls(sl=True, fl=True) or []

    @staticmethod
    def select(objs):
        cmds.select(objs)

    @staticmethod
    def select_clear():
        cmds.select(clear=True)

    @staticmethod
    def exists(obj):
        return cmds.objExists(obj)

    # ----------------------------------------------------------------
    # math helpers
    # ----------------------------------------------------------------

    @staticmethod
    def world_position(obj):
        return cmds.xform(obj, query=True, worldSpace=True, translation=True)

    @staticmethod
    def distance(obj1, obj2):
        pos1 = MayaScene.world_position(obj1)
        pos2 = MayaScene.world_position(obj2)
        return math.sqrt(
            (pos2[0] - pos1[0]) ** 2
            + (pos2[1] - pos1[1]) ** 2
            + (pos2[2] - pos1[2]) ** 2
        )

    # ----------------------------------------------------------------
    # constraints
    # driver 가 움직이면 driven 이 따라가도록 cmds.xxxConstraint(driver, driven) 순.
    # 반환값은 생성된 constraint 노드명(첫 번째 요소).
    # ----------------------------------------------------------------

    @staticmethod
    def parent_constraint(driver, driven, maintain_offset=True):
        return cmds.parentConstraint(driver, driven, mo=maintain_offset)[0]

    @staticmethod
    def point_constraint(driver, driven, maintain_offset=True):
        return cmds.pointConstraint(driver, driven, mo=maintain_offset)[0]

    @staticmethod
    def orient_constraint(driver, driven, maintain_offset=True):
        return cmds.orientConstraint(driver, driven, mo=maintain_offset)[0]

    @staticmethod
    def scale_constraint(driver, driven, maintain_offset=True):
        return cmds.scaleConstraint(driver, driven, mo=maintain_offset)[0]
