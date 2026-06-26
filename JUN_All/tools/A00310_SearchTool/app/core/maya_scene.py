# -*- coding: utf-8 -*-
"""
MayaScene - UI 보조용 maya.cmds 어댑터.

선택 가져오기 / 계층 펼치기 / 노드 타입 질의 / 존재 확인만 담당한다(UI 가 cmds 를
직접 만지지 않게). 레거시 JUN_PY_SelectionTool / JUN_PY_SearchTool 의 보조 함수
(BF_SELECTION_makeList_hierarchy, objectType 분기)를 이식했다.
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
    def select(objects):
        cmds.select(objects)

    # ----------------------------------------------------------------
    # 계층 펼치기 (레거시 BF_SELECTION_makeList_hierarchy 이식)
    # ----------------------------------------------------------------

    @staticmethod
    def _hierarchy_without_shape(obj):
        """obj 와 그 모든 자손(transform 만, shape 제외) 리스트를 반환."""
        children = cmds.listRelatives(obj, allDescendents=True, path=True)

        if children:
            result = list(children)
            result.append(obj)
        else:
            result = [obj]

        shapes = cmds.listRelatives(result, allDescendents=True, path=True,
                                    shapes=True)
        if shapes:
            for shape in shapes:
                if shape in result:
                    result.remove(shape)
        return result

    @staticmethod
    def expand_hierarchy(objects):
        """선택 리스트를 각 항목의 계층(자손 transform 포함)으로 펼친다.

        레거시처럼 자손이 위로 오도록 reverse 한 뒤 중복을 제거한다.
        """
        result = []
        for obj in objects:
            children = MayaScene._hierarchy_without_shape(obj)
            children.reverse()
            result.extend(children)

        seen = []
        for item in result:
            if item not in seen:
                seen.append(item)
        return seen

    # ----------------------------------------------------------------
    # 노드 타입 (레거시 JUN_cmd_SelTool_toolSelType_btn_V02 이식)
    # ----------------------------------------------------------------

    @staticmethod
    def node_type(obj):
        """obj 의 노드 타입. shape 가 있으면 첫 shape 의 타입, 없으면 transform 타입."""
        shapes = cmds.listRelatives(obj, shapes=True)
        if shapes:
            return cmds.objectType("{0}|{1}".format(obj, shapes[0]))
        return cmds.objectType(obj)
