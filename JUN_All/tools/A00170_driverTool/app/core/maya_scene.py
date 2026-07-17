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
        - multi/compound 어트리뷰트는 attributeQuery(multi=True) 로 조용히 판정하고,
          multi 로 확정된 것만 getNextFreeMultiIndex 로 다음 free index 를 구해
          listAttr -multi 로 자식 어트리뷰트까지 펼친다.

        NOTE: 예전엔 모든 어트리뷰트에 getNextFreeMultiIndex 를 호출해 multi 여부를 판정했는데,
        그 MEL 프로시저는 non-multi(스칼라)에서 `attr[0]` 을 찾다 실패해
        "No object matches name" 에러를 **어트리뷰트 개수만큼** 출력했다(catch 해도 출력은 남음).
        attributeQuery 로 먼저 걸러 multi 에만 호출하면 결과는 동일하고 에러가 사라진다.
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

            # multi 여부를 조용히 판정(getNextFreeMultiIndex 는 non-multi 에서 에러 출력).
            try:
                is_multi = bool(cmds.attributeQuery(attr, node=obj, multi=True))
            except Exception:
                is_multi = False

            if not is_multi:
                result.append(attr)
                continue

            # multi 확정 → 다음 free index 의 (컴파운드) 자식까지 펼친다(여기선 에러 안 남).
            full = "{0}.{1}".format(obj, attr)
            try:
                idx = mel.eval('getNextFreeMultiIndex("{0}", 0)'.format(full))
                children = cmds.listAttr(
                    "{0}[{1}]".format(full, idx), multi=True) or []
            except Exception:
                children = []
            result.extend(children if children else [attr])

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
