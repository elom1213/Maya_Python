# -*- coding: utf-8 -*-
"""
MayaScene - UI 보조용 maya.cmds 어댑터.

선택 가져오기 / 어트리뷰트 나열 / 존재 확인만 담당한다(UI 가 cmds 를 직접 만지지 않게).
실제 노드 생성(build)은 pymel 기반이라 slerp_ramp.py 가 담당한다.
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
        # 첫 조인트의 keyable 어트리뷰트(rotateX/Y/Z, scaleX/Y/Z, translate, visibility 등).
        return cmds.listAttr(obj, keyable=True) or []
