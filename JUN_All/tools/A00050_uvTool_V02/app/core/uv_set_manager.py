# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
# A00050_uvTool_V02 - UV 세트 검사 / 이름 정리 (maya.cmds, UI 비의존)
#
# 규칙은 하나다 — **메시는 `map1` 이라는 UV 세트 하나만 갖는다.**
# 게임 파이프라인에서 UV 세트가 둘 이상이거나 이름이 다르면 익스포트·머티리얼 쪽에서
# 엉뚱한 세트를 물게 된다. 이 툴은 그 규칙에 어긋난 메시를 **찾아 주고**(Catch),
# 첫 UV 세트의 **이름을 `map1` 으로 고친다**(Rename).
#
# ── mayapy(2024) 로 확인한 것 ─────────────────────────────────────────────
#  * `polyUVSet` 은 **오브젝트를 인자로 받는다** — 트랜스폼·셰이프 둘 다 된다.
#    V01 처럼 `cmds.select` 로 고른 뒤 부를 필요가 없다(선택을 건드리지 않는다).
#  * **이미 있는 이름으로 rename 하면 에러다** —
#    `RuntimeError: Cannot rename uv set to an existing uv set name.`
#    그래서 `['map1', 'uvSet1']` 같은 메시는 첫 세트를 `map1` 으로 바꿀 수 없다.
#    V01 은 이걸 `except: pass` 로 삼켜 **아무 일도 안 일어난 것을 알 수 없었다.**
#    여기서는 **미리 판정해서 사유를 돌려준다.**
#  * `map1` -> `map1` 도 같은 에러다 → 이미 맞는 메시는 **시도하지 않는다.**
#  * **기본 UV 세트는 지울 수 없다** (`The default uv set cannot be deleted.`).
#    그래서 이 툴은 **지우지 않는다** — 이름만 고친다.
#  * `ls(type="mesh")` 는 **중간(Orig) 셰이프까지** 준다(디포머가 붙은 메시).
#    같은 트랜스폼이 두 번 걸리므로 `noIntermediate=True` 로 거른다.
#  * UV 세트 rename 은 **undo 된다**.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


#: 규칙이 요구하는 UV 세트 이름.
DEFAULT_UV_SET = "map1"


# 검사 결과 상태 -----------------------------------------------------------
OK = "ok"                      # 규칙에 맞음 (map1 하나)
MULTIPLE = "multiple"          # UV 세트가 둘 이상
WRONG_NAME = "wrong_name"      # 하나뿐인데 이름이 map1 이 아님
NO_UV = "no_uv"                # UV 세트가 없음
MISSING = "missing"            # 씬에 없음
NOT_MESH = "not_mesh"          # 메시가 아님

#: 로그에 쓰는 사람 말 설명.
REASONS = {
    MULTIPLE: "has {count} UV sets ({sets}) - only '{default}' should be there",
    WRONG_NAME: "its only UV set is '{first}', not '{default}'",
    NO_UV: "has no UV set at all",
    MISSING: "is not in the scene",
    NOT_MESH: "is not a mesh",
}


# ==========================================================================
# 읽기
# ==========================================================================

def mesh_shapes(node):
    """node 아래의 **중간이 아닌** 메시 셰이프들(롱네임). 메시가 아니면 빈 리스트.

    셰이프를 직접 줘도 되고 트랜스폼을 줘도 된다.
    """
    if not node or not cmds.objExists(node):
        return []

    try:
        if cmds.nodeType(node) == "mesh":
            if cmds.getAttr(node + ".intermediateObject"):
                return []
            return cmds.ls(node, long=True) or []

        return cmds.listRelatives(node, shapes=True, fullPath=True,
                                  noIntermediate=True, type="mesh") or []
    except Exception:                                       # noqa: BLE001
        return []


def scene_meshes():
    """씬의 모든 메시 셰이프(중간 셰이프 제외, 롱네임)."""
    return cmds.ls(type="mesh", noIntermediate=True, long=True) or []


def uv_sets(node):
    """node 의 UV 세트 이름 목록. 없으면 빈 리스트.

    빈 결과를 마야가 `None` 으로 주므로 `or []` 로 받는다.
    """
    try:
        return list(cmds.polyUVSet(node, q=True, allUVSets=True) or [])
    except Exception:                                       # noqa: BLE001
        return []


def transform_of(shape):
    """셰이프의 부모 트랜스폼(롱네임). 없으면 셰이프 자신."""
    parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []

    return parents[0] if parents else shape


def check_shape(shape):
    """메시 셰이프 하나를 규칙에 비춰 본다.

    Returns:
        (status, sets) — status 는 OK / MULTIPLE / WRONG_NAME / NO_UV.
    """
    sets = uv_sets(shape)

    if not sets:
        return (NO_UV, sets)
    if len(sets) > 1:
        return (MULTIPLE, sets)
    if sets[0] != DEFAULT_UV_SET:
        return (WRONG_NAME, sets)

    return (OK, sets)


def describe(status, sets):
    """로그 한 줄에 붙일 사유. 규칙에 맞으면 빈 문자열."""
    if status == OK:
        return ""

    return REASONS[status].format(
        count=len(sets),
        sets=", ".join(sets) if sets else "-",
        first=sets[0] if sets else "-",
        default=DEFAULT_UV_SET)


# ==========================================================================
# Catch — 규칙에 맞지 않는 메시 찾기
# ==========================================================================

def find_offenders(nodes=None):
    """규칙에 어긋난 메시를 찾는다. `nodes` 가 없으면 **씬 전체**를 본다.

    Returns:
        (offenders, checked) — offenders 는
        [{transform, shape, status, sets, reason}, ...] (씬 순서),
        checked 는 실제로 검사한 셰이프 수.

    같은 트랜스폼에 셰이프가 여럿이면 셰이프마다 한 줄이 나온다 — 어느 셰이프가
    문제인지 알아야 고칠 수 있기 때문이다.
    """
    if nodes:
        shapes = []
        for node in nodes:
            shapes.extend(mesh_shapes(node))
        # 같은 셰이프가 두 번 들어오지 않게(트랜스폼과 셰이프를 함께 담은 경우).
        shapes = list(dict.fromkeys(shapes))
    else:
        shapes = scene_meshes()

    offenders = []

    for shape in shapes:
        status, sets = check_shape(shape)
        if status == OK:
            continue

        offenders.append({
            "transform": transform_of(shape),
            "shape": shape,
            "status": status,
            "sets": sets,
            "reason": describe(status, sets),
        })

    return (offenders, len(shapes))


# ==========================================================================
# Rename — 첫 UV 세트를 map1 으로
# ==========================================================================

# rename 결과 상태
RENAMED = "renamed"            # 이름을 바꿨다
ALREADY = "already"            # 이미 map1 하나뿐이라 할 일이 없다
EXTRA = "extra"                # 첫 세트는 map1 인데 다른 세트가 더 있다(이 툴은 못 지운다)
BLOCKED = "blocked"            # map1 이 이미 있어서 첫 세트를 바꿀 수 없다
FAILED = "failed"              # 마야가 거절했다(잠김·레퍼런스 등)


def rename_first_uv_set(nodes):
    """각 노드의 **첫 UV 세트**를 `map1` 으로 바꾼다. 전체가 undo 한 스텝.

    ★ 첫 세트만 본다(V01 과 같다). `polyUVSet(q=allUVSets)` 의 **순서 그대로**이고,
      현재 UV 세트(currentUVSet)가 아니다.

    ★ 이미 `map1` 이 있는 메시는 **바꿀 수 없다** — 마야가
      `Cannot rename uv set to an existing uv set name.` 로 거절한다. 조용히 넘기지 않고
      `BLOCKED` 로 돌려준다(V01 은 이것을 삼켜서, 아무 일도 없었다는 걸 알 수 없었다).

    Returns:
        records — [{node, shape, status, before, after, detail}, ...]
        status 는 RENAMED / ALREADY / BLOCKED / FAILED / NO_UV / MISSING / NOT_MESH.
    """
    records = []

    with undo_chunk():
        for node in nodes or []:
            if not node or not cmds.objExists(node):
                records.append(_record(node, None, MISSING, [], [], ""))
                continue

            shapes = mesh_shapes(node)
            if not shapes:
                records.append(_record(node, None, NOT_MESH, [], [], ""))
                continue

            for shape in shapes:
                records.append(_rename_one(node, shape))

    return records


def _record(node, shape, status, before, after, detail):
    return {"node": node, "shape": shape, "status": status,
            "before": list(before), "after": list(after), "detail": detail}


def _rename_one(node, shape):
    """셰이프 하나의 첫 UV 세트를 map1 으로."""
    before = uv_sets(shape)

    if not before:
        return _record(node, shape, NO_UV, before, before, "")

    first = before[0]

    if first == DEFAULT_UV_SET:
        if len(before) == 1:
            return _record(node, shape, ALREADY, before, before, "")

        # 첫 세트는 이미 map1 이라 rename 할 것이 없는데, 규칙에는 여전히 어긋난다.
        # "그냥 뒀다" 고만 하면 사용자는 고쳐진 줄 안다 → 남은 세트를 짚어 준다.
        return _record(
            node, shape, EXTRA, before, before,
            "'{0}' is already first, but {1} still there - this tool does not "
            "delete UV sets".format(
                DEFAULT_UV_SET, ", ".join(repr(s) for s in before[1:])))

    if DEFAULT_UV_SET in before:
        # 마야가 거절하는 조합. 시도하지 않고 사유를 돌려준다.
        return _record(
            node, shape, BLOCKED, before, before,
            "'{0}' already exists on this mesh".format(DEFAULT_UV_SET))

    try:
        cmds.polyUVSet(shape, rename=True, uvSet=first, newUVSet=DEFAULT_UV_SET)
    except Exception as exc:                                # noqa: BLE001
        return _record(node, shape, FAILED, before, uv_sets(shape), str(exc).strip())

    return _record(node, shape, RENAMED, before, uv_sets(shape), "")
