# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
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


# ---------------------------------------------------------------- rules (v01.11)
# Rules 탭은 이름이 **짧은 이름** 그대로라 동명 노드가 있을 수 있다. objExists 는 그런 이름에도
# True 를 주지만 cmds.select(이름) 은 "More than one object matches name" 으로 실패한다
# (mayapy 실측). 그래서 이름마다 cmds.ls 로 실제 노드를 펼쳐서 고른다.

def _matches(name):
    """name 에 해당하는 노드들(긴 이름). 없으면 빈 리스트. 잘못된 이름 문자열은 빈 리스트."""
    try:
        return cmds.ls(name, long=True) or []
    except Exception:
        return []


def name_status(objects):
    """이름마다 'ok' / 'missing' / 'ambiguous'. UI 가 목록 색을 칠하는 데 쓴다."""
    status = {}
    for name in objects:
        if name in status:
            continue
        matches = _matches(name)
        if not matches:
            status[name] = "missing"
        elif len(matches) > 1:
            status[name] = "ambiguous"
        else:
            status[name] = "ok"
    return status


def select_names(objects, add=False):
    """규칙의 이름 목록을 씬에서 선택한다. 동명 노드는 **전부** 고르고 ambiguous 로 보고한다.

    - missing 은 건너뛴다. add=False 이고 고를 것이 없으면 선택을 비운다.
    - 반환: {"found": [선택한 노드(긴 이름)...], "missing": [이름...],
             "ambiguous": [(이름, [긴 이름...]), ...]}
    """
    found, missing, ambiguous = [], [], []
    for name in objects:
        matches = _matches(name)
        if not matches:
            missing.append(name)
            continue
        if len(matches) > 1:
            ambiguous.append((name, list(matches)))
        for node in matches:
            if node not in found:
                found.append(node)

    if found:
        cmds.select(found, add=add)
    elif not add:
        cmds.select(clear=True)

    return {"found": found, "missing": missing, "ambiguous": ambiguous}
