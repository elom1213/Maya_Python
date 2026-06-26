# -*- coding: utf-8 -*-
"""
MayaScene - UI 보조용 maya.cmds 어댑터.

선택 가져오기 / 존재 확인만 담당한다(UI 가 cmds 를 직접 만지지 않게).
실제 노드 생성(build)은 pymel 기반이라 spherical_drive.py 가 담당한다.
"""

import maya.cmds as cmds
import maya.mel as mel


class MayaScene(object):

    @staticmethod
    def selection():
        return cmds.ls(sl=True, fl=True) or []

    @staticmethod
    def exists(obj):
        return bool(obj) and cmds.objExists(obj)

    @staticmethod
    def list_attrs(obj, search=""):
        """obj 의 어트리뷰트 목록(A00145_RigConnect Connect 탭 list_attrs 이식).

        keyable 만이 아니라 listAttr(obj) 전체를 본다.
        - search 가 있으면 listAttr(obj.search) 로 (그 attr + 자식들) 질의 →
          현재 리스트업되지 않은 어트리뷰트도 이름으로 찾아 보여줄 수 있다.
        - 이름에 "." 가 든 중첩 항목은 건너뛴다.
        - multi/compound 어트리뷰트는 getNextFreeMultiIndex 로 판정해
          listAttr -multi 로 자식 어트리뷰트까지 펼친다.
        """
        if not obj:
            return []

        if search:
            raw = cmds.listAttr(obj + "." + search) or []
        else:
            raw = cmds.listAttr(obj) or []

        result = []
        for attr in raw:
            # 중첩 어트리뷰트(이름에 ".") 는 건너뛴다.
            if "." in attr:
                continue

            full = "{0}.{1}".format(obj, attr)

            # getNextFreeMultiIndex 는 multi 어트리뷰트에서만 성공한다.
            try:
                idx = mel.eval('getNextFreeMultiIndex("{0}", 0)'.format(full))
                is_multi = True
            except Exception:
                is_multi = False

            if not is_multi:
                result.append(attr)
            else:
                children = cmds.listAttr(
                    "{0}.{1}[{2}]".format(obj, attr, idx), multi=True) or []
                result.extend(children)

        return result

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
