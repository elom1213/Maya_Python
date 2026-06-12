# -*- coding: utf-8 -*-
"""
MayaScene - UI 보조용 maya.cmds 어댑터.

선택 가져오기 / 존재 확인만 담당한다(UI 가 cmds 를 직접 만지지 않게).
실제 노드 생성(build)은 pymel 기반이라 spherical_drive.py 가 담당한다.
"""

import maya.cmds as cmds


class MayaScene(object):

    @staticmethod
    def selection():
        return cmds.ls(sl=True, fl=True) or []

    @staticmethod
    def exists(obj):
        return bool(obj) and cmds.objExists(obj)

    @staticmethod
    def list_keyable_attrs(obj):
        return cmds.listAttr(obj, keyable=True) or []

    @staticmethod
    def distance(obj_a, obj_b):
        """두 오브젝트의 로컬 translate 사이 거리. 둘 중 하나라도 씬에 없으면 None.

        build(spherical_drive)의 거리 계산이 로컬 translate(jnt.translate) 기준이라 동일하게 맞춘다.
        """
        if not (MayaScene.exists(obj_a) and MayaScene.exists(obj_b)):
            return None
        ax, ay, az = cmds.getAttr('{0}.translate'.format(obj_a))[0]
        bx, by, bz = cmds.getAttr('{0}.translate'.format(obj_b))[0]
        return ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5
