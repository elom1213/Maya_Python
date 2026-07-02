# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-02
# A00340_SelectionTool - selection capture / restore (maya.cmds, UI 비의존)
#
# 선택 버튼이 담는 데이터는 오브젝트 이름 목록이다. 여기서는 현재 씬 선택을 그 목록으로
# 캡처하고(capture_selection), 반대로 목록을 씬에서 선택한다(select_objects).
# UI 가 maya.cmds 를 직접 만지지 않도록 이 어댑터를 통한다.

import maya.cmds as cmds


def capture_selection():
    """현재 씬 선택을 오브젝트 이름 목록으로 반환한다(선택 없으면 빈 리스트).

    이름은 cmds.ls 기본값(가능한 짧은 이름, 중복 시 부분 경로)을 그대로 쓴다.
    나중에 select 할 때 objExists 로 유효성만 확인한다.
    """
    return cmds.ls(selection=True) or []


def select_objects(objects, add=False):
    """objects 를 씬에서 선택한다.

    - 씬에 실제로 존재하는 것만 고른다(objExists). 사라진 것은 missing 으로 보고.
    - add=True 면 현재 선택을 유지한 채 추가 선택한다(빠른 누적 선택용).
    - add=False 인데 유효 오브젝트가 하나도 없으면 선택을 비운다(deselect all).

    (found, missing) 튜플을 반환한다. found/missing 은 이름 리스트.
    """
    found = [obj for obj in objects if cmds.objExists(obj)]
    missing = [obj for obj in objects if not cmds.objExists(obj)]

    if found:
        cmds.select(found, add=add)
    elif not add:
        cmds.select(clear=True)

    return found, missing
