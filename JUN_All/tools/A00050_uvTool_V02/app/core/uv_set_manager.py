# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-23
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
#  * (v02.03 Delete) **지울 수 없는 것은 첫 번째(기본) UV 세트뿐**이다 — 이름이 무엇이든
#    `allUVSets` 의 첫 세트면 `The default uv set cannot be deleted.` 로 거절된다.
#    `['uvA', 'map1']` 은 uvA 를 못 지우고, `['uvA']` 도 못 지운다.
#    현재(current) UV 세트를 지우면 현재 세트는 기본 세트로 넘어간다. 삭제도 undo 된다.
#    지울 때마다 히스토리에 `deleteUVSet` 노드가 하나씩 생긴다(스킨 메시도 지워진다).

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


#: 규칙이 요구하는 UV 세트 이름의 **기본값**. 화면에서 바꿀 수 있다(v02.01).
DEFAULT_UV_SET = "map1"

#: 마야가 거절하는 유일한 이름 — 빈 문자열(`Invalid new uv set name specified`).
#  공백·`-`·`.`·`:`·`|`·숫자 시작까지 **마야는 그대로 받는다**(실측). 그래서 막지 않고,
#  앞뒤 공백만 떼어 낸다(오타일 가능성이 크다).



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


def clean_name(name):
    """화면에서 받은 UV 세트 이름을 다듬는다. 반환: (ok, cleaned, message)

    마야가 거절하는 것은 **빈 이름뿐**이다(`Invalid new uv set name specified`).
    공백이 낀 이름(`UV Map`)도 마야는 받으므로 막지 않는다 — 앞뒤 공백만 떼고,
    뗀 것이 있으면 알려 준다.
    """
    cleaned = (name or "").strip()

    if not cleaned:
        return (False, "", "The UV set name is empty - Maya refuses that "
                            "('Invalid new uv set name specified').")

    if cleaned != (name or ""):
        return (True, cleaned,
                "Spaces around the name were dropped - using '{0}'.".format(cleaned))

    return (True, cleaned, "")


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


def check_shape(shape, wanted=DEFAULT_UV_SET):
    """메시 셰이프 하나를 규칙에 비춰 본다.

    `wanted` 는 **원하는 UV 세트 이름**이다(화면에서 정한다, v02.01).

    Returns:
        (status, sets) — status 는 OK / MULTIPLE / WRONG_NAME / NO_UV.
    """
    sets = uv_sets(shape)

    if not sets:
        return (NO_UV, sets)
    if len(sets) > 1:
        return (MULTIPLE, sets)
    if sets[0] != wanted:
        return (WRONG_NAME, sets)

    return (OK, sets)


def describe(status, sets, wanted=DEFAULT_UV_SET):
    """로그 한 줄에 붙일 사유. 규칙에 맞으면 빈 문자열."""
    if status == OK:
        return ""

    return REASONS[status].format(
        count=len(sets),
        sets=", ".join(sets) if sets else "-",
        first=sets[0] if sets else "-",
        default=wanted)


# ==========================================================================
# Inspect — 오브젝트마다 UV 세트와 규칙 판정 (v02.02, UV Sets 표)
# ==========================================================================

def _collect_shapes(nodes):
    """nodes 아래의 메시 셰이프(중복 없이). 트랜스폼과 셰이프를 함께 담아도 한 번씩."""
    shapes = []
    for node in nodes or []:
        shapes.extend(mesh_shapes(node))
    return list(dict.fromkeys(shapes))


def inspect(nodes, wanted=DEFAULT_UV_SET):
    """노드마다 **UV 세트 이름들**과 **규칙 판정**을 준다. 씬은 바꾸지 않는다.

    UI 의 `UV Sets` 표(오브젝트 · UV 세트 · 규칙 세 칸)가 이것을 그대로 그린다.
    메시 셰이프마다 한 행이고, 메시가 아니거나 씬에 없는 노드도 **한 행으로 남긴다** -
    리스트에 올린 것이 표에서 조용히 사라지면 왜 빠졌는지 알 수 없다.

    Returns:
        [{node, transform, shape, sets, status, reason}, ...] (nodes 순서)
        status 는 OK / MULTIPLE / WRONG_NAME / NO_UV / MISSING / NOT_MESH.
    """
    rows = []
    seen = set()

    for node in nodes or []:
        if not node or not cmds.objExists(node):
            rows.append({"node": node, "transform": node, "shape": None, "sets": [],
                         "status": MISSING, "reason": REASONS[MISSING]})
            continue

        shapes = mesh_shapes(node)
        if not shapes:
            rows.append({"node": node, "transform": node, "shape": None, "sets": [],
                         "status": NOT_MESH, "reason": REASONS[NOT_MESH]})
            continue

        for shape in shapes:
            if shape in seen:
                continue
            seen.add(shape)
            status, sets = check_shape(shape, wanted)
            rows.append({"node": node, "transform": transform_of(shape), "shape": shape,
                         "sets": sets, "status": status,
                         "reason": describe(status, sets, wanted)})

    return rows


# ==========================================================================
# Catch — 규칙에 맞지 않는 메시 찾기
# ==========================================================================

def find_offenders(nodes=None, wanted=DEFAULT_UV_SET):
    """규칙에 어긋난 메시를 찾는다. `nodes` 가 없으면 **씬 전체**를 본다.

    `wanted` 는 화면에서 정한 **원하는 UV 세트 이름**이다 — Rename 이 붙일 이름과 같은
    값을 쓴다. 그래야 "잡은 것을 고치면 규칙에 맞는다" 가 성립한다.

    Returns:
        (offenders, checked) — offenders 는
        [{transform, shape, status, sets, reason}, ...] (씬 순서),
        checked 는 실제로 검사한 셰이프 수.

    같은 트랜스폼에 셰이프가 여럿이면 셰이프마다 한 줄이 나온다 — 어느 셰이프가
    문제인지 알아야 고칠 수 있기 때문이다.
    """
    if nodes:
        # 같은 셰이프가 두 번 들어오지 않게(트랜스폼과 셰이프를 함께 담은 경우).
        shapes = _collect_shapes(nodes)
    else:
        shapes = scene_meshes()

    offenders = []

    for shape in shapes:
        status, sets = check_shape(shape, wanted)
        if status == OK:
            continue

        offenders.append({
            "transform": transform_of(shape),
            "shape": shape,
            "status": status,
            "sets": sets,
            "reason": describe(status, sets, wanted),
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


def rename_first_uv_set(nodes, new_name=DEFAULT_UV_SET):
    """각 노드의 **첫 UV 세트**를 `new_name` 으로 바꾼다. 전체가 undo 한 스텝.

    `new_name` 은 화면에서 입력받는다(v02.01, 기본 `map1`). 빈 이름은 마야가 거절하므로
    호출 전에 `clean_name()` 으로 다듬어 넘긴다.

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
                records.append(_rename_one(node, shape, new_name))

    return records


def _record(node, shape, status, before, after, detail):
    return {"node": node, "shape": shape, "status": status,
            "before": list(before), "after": list(after), "detail": detail}


def _rename_one(node, shape, new_name=DEFAULT_UV_SET):
    """셰이프 하나의 첫 UV 세트를 `new_name` 으로."""
    before = uv_sets(shape)

    if not before:
        return _record(node, shape, NO_UV, before, before, "")

    first = before[0]

    if first == new_name:
        if len(before) == 1:
            return _record(node, shape, ALREADY, before, before, "")

        # 첫 세트는 이미 map1 이라 rename 할 것이 없는데, 규칙에는 여전히 어긋난다.
        # "그냥 뒀다" 고만 하면 사용자는 고쳐진 줄 안다 → 남은 세트를 짚어 준다.
        return _record(
            node, shape, EXTRA, before, before,
            "'{0}' is already first, but {1} still there - this tool does not "
            "delete UV sets".format(
                new_name, ", ".join(repr(s) for s in before[1:])))

    if new_name in before:
        # 마야가 거절하는 조합. 시도하지 않고 사유를 돌려준다.
        return _record(
            node, shape, BLOCKED, before, before,
            "'{0}' already exists on this mesh".format(new_name))

    try:
        cmds.polyUVSet(shape, rename=True, uvSet=first, newUVSet=new_name)
    except Exception as exc:                                # noqa: BLE001
        return _record(node, shape, FAILED, before, uv_sets(shape), str(exc).strip())

    return _record(node, shape, RENAMED, before, uv_sets(shape), "")


# ==========================================================================
# Delete — 규칙 이름이 아닌 UV 세트 지우기 (v02.03)
# ==========================================================================

# delete 결과 상태 (RENAMED 등과 같은 dict 모양으로 돌려준다)
DELETED = "deleted"            # 규칙 이름 외의 세트를 모두 지웠다
PARTIAL = "partial"            # 일부는 지웠지만 첫(기본) 세트가 규칙 이름이 아니라 남았다
NO_KEEPER = "no_keeper"        # 남길 세트(규칙 이름)가 없다 - 지우면 규칙 이름이 영영 없다


def delete_other_uv_sets(nodes, keep=DEFAULT_UV_SET):
    """각 노드에서 이름이 `keep` 이 **아닌** UV 세트를 모두 지운다. 전체가 undo 한 스텝.

    ★ 첫 번째(기본) UV 세트는 마야가 지우지 못하게 한다. 그래서
      - `keep` 이 아예 없는 메시(`['uvA']`, `['uvA', 'uvB']`)는 **하나도 지우지 않고**
        `NO_KEEPER` 로 돌려준다 — 지워 봐야 규칙 이름은 생기지 않는다. Rename 이 먼저다.
      - `keep` 이 있지만 첫 세트가 아닌 메시(`['uvA', 'map1']`)는 지울 수 있는 것만 지우고
        `PARTIAL` 로 첫 세트가 남았다고 알린다.

    Returns:
        records — [{node, shape, status, before, after, detail}, ...]
        status 는 DELETED / ALREADY / PARTIAL / NO_KEEPER / FAILED / NO_UV / MISSING / NOT_MESH.
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
                records.append(_delete_one(node, shape, keep))

    return records


def _delete_one(node, shape, keep=DEFAULT_UV_SET):
    """셰이프 하나에서 `keep` 이 아닌 UV 세트를 지운다."""
    before = uv_sets(shape)

    if not before:
        return _record(node, shape, NO_UV, before, before, "")

    if keep not in before:
        return _record(
            node, shape, NO_KEEPER, before, before,
            "there is no '{0}' to keep - rename a set to '{0}' first".format(keep))

    extras = [name for name in before if name != keep]
    if not extras:
        return _record(node, shape, ALREADY, before, before, "")

    default = before[0]
    errors = []
    for name in extras:
        if name == default:
            continue            # 마야가 거절한다 - 시도하지 않고 아래에서 알린다
        try:
            cmds.polyUVSet(shape, delete=True, uvSet=name)
        except Exception as exc:                            # noqa: BLE001
            errors.append("{0}: {1}".format(name, str(exc).strip()))

    after = uv_sets(shape)

    if errors:
        return _record(node, shape, FAILED, before, after, "; ".join(errors))

    if default != keep:
        return _record(
            node, shape, PARTIAL, before, after,
            "'{0}' is the default (first) UV set and Maya cannot delete it".format(default))

    return _record(node, shape, DELETED, before, after, "")
