# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00145_RigConnect - Attribute > Delete 탭 로직 (지울 수 있는 어트리뷰트 목록 + 삭제)
#
# "지울 수 있는" 이 이 모듈의 전부다. 마야에서 지울 수 있는 어트리뷰트는 **사용자 정의
# 어트리뷰트의 최상위 항목**뿐이다. 실측으로 확인한 것 (Maya 2024):
#
#   deleteAttr translateX      -> "Cannot delete child 'translateX' of compound
#                                  attribute 'translate'."  (기본 어트리뷰트)
#   deleteAttr vecX            -> 같은 에러. 컴파운드 **자식은 따로 못 지운다**.
#   deleteAttr vec             -> OK. 부모를 지우면 자식이 함께 사라진다.
#   deleteAttr <locked>        -> "'node.attr' is locked and may not be removed."
#   deleteAttr <connected>     -> **OK**. 연결이나 키가 있어도 지워진다.
#
# 그래서 목록에는 컴파운드 **부모만** 올리고, 잠긴 것은 올리되 표시해 둔다. 잠금을
# 이 툴이 몰래 풀지는 않는다 - 잠금은 "건드리지 말라"는 의사표시이고, 실패 사유를
# 그대로 알려 주면 사용자가 풀고 다시 누르면 된다.

import maya.cmds as cmds


def _user_attrs(obj):
    """obj 의 **지울 수 있는** 사용자 정의 어트리뷰트 롱네임(컴파운드 자식 제외)."""
    attrs = cmds.listAttr(obj, userDefined=True) or []
    out = []
    for attr in attrs:
        # listAttr 은 자식을 "parent.child" 로 줄 때도, 평평한 이름으로 줄 때도 있다.
        if "." in attr:
            continue
        try:
            if cmds.attributeQuery(attr, node=obj, listParent=True):
                continue
        except Exception:
            # 별칭 등 attributeQuery 가 못 푸는 이름은 목록에 남긴다(삭제 시 판정된다).
            pass
        out.append(attr)
    return out


def _is_locked(obj, attr):
    try:
        return bool(cmds.getAttr("{0}.{1}".format(obj, attr), lock=True))
    except Exception:
        return False


def _is_referenced(obj):
    try:
        return bool(cmds.referenceQuery(obj, isNodeReferenced=True))
    except Exception:
        return False


def list_deletable(objects):
    """objects 가 가진 지울 수 있는 어트리뷰트들을 모아 준다.

    여러 오브젝트를 받으면 **합집합**을 돌려준다. 리깅에서 같은 이름의 어트리뷰트를
    좌우 컨트롤러에 나란히 만들어 두는 일이 흔해, 하나만 골라 지우는 것보다 "이 이름을
    가진 것 전부"를 지우는 쪽이 실제 작업에 맞는다. 몇 개가 가졌는지는 함께 돌려주므로
    호출부가 표시할 수 있다.

    Args:
        objects: 오브젝트 이름 리스트.

    Returns:
        (rows, missing) — rows 는 이름순 정렬된 dict 리스트
        {name, owners:[obj...], locked:[obj...], referenced:[obj...]},
        missing 은 씬에 없는 오브젝트 이름 리스트.

    Raises:
        ValueError: objects 가 비었을 때.
    """
    if not objects:
        raise ValueError("No objects. Add objects to the list on the left.")

    rows = {}
    missing = []

    for obj in objects:
        if not cmds.objExists(obj):
            missing.append(obj)
            continue
        referenced = _is_referenced(obj)
        for attr in _user_attrs(obj):
            row = rows.setdefault(
                attr, {"name": attr, "owners": [], "locked": [], "referenced": []})
            row["owners"].append(obj)
            if _is_locked(obj, attr):
                row["locked"].append(obj)
            if referenced:
                row["referenced"].append(obj)

    return [rows[k] for k in sorted(rows)], missing


def delete_attributes(objects, attrs):
    """objects 중 attrs 를 가진 것에서 그 어트리뷰트를 지운다.

    가지고 있지 않은 오브젝트는 **조용히 넘어간다** — 합집합 목록에서 고른 것이므로
    "이 오브젝트엔 원래 없음" 은 알릴 일이 아니다. 실패(잠김 등)만 보고한다.

    Returns:
        (deleted, failed) — deleted 는 "obj.attr" 리스트,
        failed 는 (obj, attr, reason) 튜플 리스트.

    Raises:
        ValueError: 오브젝트나 어트리뷰트가 비었을 때.
    """
    if not objects:
        raise ValueError("No objects. Add objects to the list on the left.")
    if not attrs:
        raise ValueError("No attributes selected. Select attributes to delete.")

    deleted, failed = [], []

    for obj in objects:
        if not cmds.objExists(obj):
            failed.append((obj, "", "object not found in scene"))
            continue

        for attr in attrs:
            full = "{0}.{1}".format(obj, attr)
            if not cmds.objExists(full):
                continue
            if _is_locked(obj, attr):
                failed.append((obj, attr, "locked - unlock it first"))
                continue
            try:
                cmds.deleteAttr(obj, attribute=attr)
                deleted.append(full)
            except Exception as e:
                failed.append((obj, attr, str(e)))

    return deleted, failed
