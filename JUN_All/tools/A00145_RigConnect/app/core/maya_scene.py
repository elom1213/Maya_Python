# -*- coding: utf-8 -*-
"""
MayaScene - DCC 어댑터.

maya.cmds 호출을 한 곳으로 모은 얇은 래퍼. core/ui 의 다른 모듈은 cmds 를 직접
import 하지 않고 이 어댑터만 사용한다. (UI 비의존)

A00140_ConnectClosest 의 MayaScene 를 그대로 옮겨온 것이다(Connect Closest 탭용).
"""

import math

import maya.cmds as cmds


# 위치가 transform 의 translate 에 있지 않은 shape 타입.
# clusterHandle 은 transform.translate 가 (0,0,0) 인 채로 shape 의 origin
# (아이콘이 그려지고 rotate pivot 이 놓이는 지점)이 실제 클러스터 중심이다.
# translate 로 재면 클러스터가 전부 월드 원점으로 잡혀 거리 비교가 무의미해진다.
PIVOT_BASED_SHAPES = ("clusterHandle",)


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
    def _pivot_based_shape(obj):
        """obj(또는 그 shape)가 PIVOT_BASED_SHAPES 면 해당 shape 이름을 반환."""
        try:
            if cmds.nodeType(obj) in PIVOT_BASED_SHAPES:
                return obj
            shapes = cmds.listRelatives(obj, shapes=True, path=True) or []
            for shape in shapes:
                if cmds.nodeType(shape) in PIVOT_BASED_SHAPES:
                    return shape
        except Exception:
            pass
        return None

    @staticmethod
    def _transform_of(obj):
        """shape 이 주어지면 부모 transform 을, transform 이면 자기 자신을 반환."""
        if "transform" in (cmds.nodeType(obj, inherited=True) or []):
            return obj
        parents = cmds.listRelatives(obj, parent=True, path=True) or []
        return parents[0] if parents else obj

    @staticmethod
    def _local_to_world(xform_node, point):
        """transform 의 로컬 좌표 point 를 월드 좌표로 변환 (row-vector 규약)."""
        m = cmds.xform(xform_node, query=True, worldSpace=True, matrix=True)
        px, py, pz = point
        return [
            px * m[0] + py * m[4] + pz * m[8] + m[12],
            px * m[1] + py * m[5] + pz * m[9] + m[13],
            px * m[2] + py * m[6] + pz * m[10] + m[14],
        ]

    @staticmethod
    def world_position(obj):
        """오브젝트의 월드 위치.

        일반 노드는 transform 의 월드 translate. clusterHandle 처럼 위치가
        translate 가 아니라 shape 의 origin 에 있는 노드는 그 origin 을 월드로
        변환해서 쓴다(없으면 rotate pivot → translate 순으로 폴백).
        """
        shape = MayaScene._pivot_based_shape(obj)
        if shape:
            xform_node = MayaScene._transform_of(shape)
            try:
                origin = cmds.getAttr(shape + ".origin")[0]
                return MayaScene._local_to_world(xform_node, origin)
            except Exception:
                pass
            try:
                return cmds.xform(
                    xform_node, query=True, worldSpace=True, rotatePivot=True)
            except Exception:
                pass
            obj = xform_node

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
