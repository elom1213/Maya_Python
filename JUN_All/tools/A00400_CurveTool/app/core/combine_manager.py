# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00400_CurveTool core - Source 커브들의 쉐입을 Target 커브 트랜스폼에 합친다. UI 비의존.
#
# ── 참고한 MEL 과 그 문제 ──────────────────────────────────────────────────
#   parent -s -add $srcShape $target;
# `-add` 는 쉐입을 **옮기거나 복사하지 않고 인스턴스**로 하나 더 매단다. 노드는 하나인데
# 부모가 둘이 된다(mayapy 실측: `listRelatives(shape, allParents=True)` -> ['A', 'B']).
# 그래서 A 를 지우면 B 의 쉐입도 사라진다. 실측으로 확인한 경로:
#   * `select -hi A; delete`  (아웃라이너에서 계층째 지우기)  -> B 의 쉐입도 삭제
#   * `delete |A|AShape`       (쉐입 경로 지우기)             -> B 의 쉐입도 삭제
#   * `delete A` / `doDelete`  (트랜스폼만)                    -> B 에 남는다
# 지우지 않더라도 A 의 CV 를 움직이면 B 도 같이 움직인다 - 같은 노드이기 때문이다.
#
# ── 여기서 하는 것 ─────────────────────────────────────────────────────────
#   1) Source 트랜스폼을 `duplicate` 한다 -> **독립된 새 쉐입 노드**(히스토리 없음)
#   2) 새 쉐입을 `parent -r -s` 로 Target 에 **옮긴다** (인스턴스가 아니다)
#   3) 남은 임시 트랜스폼을 지운다
#   4) Placement 에 따라 CV 를 놓는다 (v01.13)
#      * PLACE_TARGET (기본) - Source 를 **Target 월드 위치로 옮겼을 때의 모양**.
#        Maya `matchTransform -pos` 와 같이 **rotate pivot 끼리** 맞춘다(mayapy 실측:
#        matchTransform 후 A 의 월드 rp == B 의 월드 rp, translate 값끼리는 다르다).
#        회전·스케일은 Source 것을 그대로 둔다 - 월드 CV 에 (Target rp - Source rp) 를 더한다.
#      * PLACE_WORLD  - Source 가 **보이던 자리 그대로** (v01.11 의 Keep world position 켬)
#      * PLACE_LOCAL  - 로컬 CV 값을 그대로 (MEL `parent -s -add` 와 같음. 두 트랜스폼이
#        다르면 모양이 튄다)
# 결과 쉐입은 Source 와 아무 연결이 없어서 Source 를 지우거나 고쳐도 영향이 없다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


PLACE_TARGET = "target"   # Source 를 Target 월드 위치(rotate pivot)로 옮긴 모양
PLACE_WORLD = "world"     # Source 가 보이던 월드 위치 그대로
PLACE_LOCAL = "local"     # 로컬 CV 값 그대로 (MEL parent -s -add)
PLACEMENTS = (PLACE_TARGET, PLACE_WORLD, PLACE_LOCAL)


# ==========================================================================
# 조회
# ==========================================================================

def _long(node):
    found = cmds.ls(node, long=True) or []
    return found[0] if found else None


def curve_transform(node):
    """노드(트랜스폼 또는 커브 쉐입)에서 커브 트랜스폼의 long 경로. 아니면 None."""
    path = _long(node)
    if not path:
        return None
    if cmds.nodeType(path) == "nurbsCurve":
        path = cmds.listRelatives(path, parent=True, fullPath=True)[0]
    if cmds.nodeType(path) != "transform":
        return None
    return path if curve_shapes(path) else None


def curve_shapes(transform):
    """트랜스폼 바로 밑의 **보이는** nurbsCurve 쉐입(long). intermediate(Orig 등) 제외."""
    shapes = cmds.listRelatives(transform, shapes=True, fullPath=True,
                                noIntermediate=True) or []
    return [s for s in shapes if cmds.nodeType(s) == "nurbsCurve"]


def _cv_world_positions(shape):
    flat = cmds.xform(shape + ".cv[*]", query=True, worldSpace=True, translation=True) or []
    return [flat[i:i + 3] for i in range(0, len(flat), 3)]


def _leaf(path):
    return path.split("|")[-1]


# ==========================================================================
# 짝 짓기
# ==========================================================================

def build_pairs(sources, targets):
    """(source, target) 목록과 문제 메시지.

    * Target 1 개   -> 모든 Source 를 그 Target 에
    * Target N 개   -> Source 도 N 개일 때 **행 순서대로** 1:1
    반환: (pairs, error)  error 가 있으면 pairs 는 빈 목록.
    """
    if not sources:
        return [], "The Source list is empty."
    if not targets:
        return [], "The Target list is empty."
    if len(targets) == 1:
        return [(s, targets[0]) for s in sources], None
    if len(sources) == len(targets):
        return list(zip(sources, targets)), None
    return [], ("Source ({0}) and Target ({1}) counts differ. Use one Target, or the "
                "same number of Targets as Sources (paired by row).").format(
                    len(sources), len(targets))


# ==========================================================================
# 합치기
# ==========================================================================

def _world_pivot(transform):
    return cmds.xform(transform, query=True, worldSpace=True, rotatePivot=True)


def _copy_shapes(source, target, placement):
    """source 커브의 쉐입을 **복사해서** target 에 붙인다. 새 쉐입 long 경로 목록."""
    src_shapes = curve_shapes(source)
    world = None
    if placement in (PLACE_TARGET, PLACE_WORLD):
        world = [_cv_world_positions(s) for s in src_shapes]
    if placement == PLACE_TARGET:
        # matchTransform -pos 처럼 rotate pivot 을 맞춘 만큼 평행이동한다.
        offset = [t - s for t, s in zip(_world_pivot(target), _world_pivot(source))]
        world = [[[p[0] + offset[0], p[1] + offset[1], p[2] + offset[2]] for p in cvs]
                 for cvs in world]

    # 선택/자식까지 따라오지 않게 트랜스폼만 복제한다. upstream 을 복제하지 않으므로
    # 새 쉐입은 히스토리 없이 **현재 모양**을 그대로 가진다.
    temp = cmds.duplicate(source, returnRootsOnly=True, upstreamNodes=False)[0]
    temp = _long(temp)
    temp_shapes = curve_shapes(temp)

    base = _leaf(target) + "Shape"
    new_shapes = []
    try:
        for index, shape in enumerate(temp_shapes):
            moved = cmds.parent(shape, target, relative=True, shape=True)[0]
            moved = cmds.rename(moved, base + "#")
            moved = cmds.ls(moved, long=True)[0]
            if world is not None and index < len(world):
                for cv, pos in enumerate(world[index]):
                    cmds.xform("{0}.cv[{1}]".format(moved, cv),
                               worldSpace=True, translation=pos)
            new_shapes.append(moved)
    finally:
        # 남은 임시 트랜스폼(+ 함께 복제된 intermediate 쉐입 · 자식)을 지운다.
        if cmds.objExists(temp):
            cmds.delete(temp)
    return new_shapes


def combine_shapes(sources, targets, placement=PLACE_TARGET, delete_sources=False):
    """Source 커브 쉐입들을 Target 커브에 합친다. 전부 한 번의 undo.

    placement: PLACE_TARGET / PLACE_WORLD / PLACE_LOCAL (모듈 상단 주석 참고)

    반환: dict(ok, message, added=[(source, target, [new shapes])], skipped=[(item, why)],
               deleted=[source])
    """
    result = {"ok": False, "message": "", "added": [], "skipped": [], "deleted": []}
    if placement not in PLACEMENTS:
        result["message"] = "Unknown placement: {0}".format(placement)
        return result

    src = []
    for item in sources:
        path = curve_transform(item)
        if path:
            if path not in src:
                src.append(path)
        else:
            result["skipped"].append((item, "not a NURBS curve"))
    tgt = []
    for item in targets:
        path = curve_transform(item)
        if path:
            if path not in tgt:
                tgt.append(path)
        else:
            result["skipped"].append((item, "not a NURBS curve"))

    pairs, error = build_pairs(src, tgt)
    if error:
        result["message"] = error
        return result

    with undo_chunk():
        # 먼저 전부 UUID 로 잡아 둔다 - 쉐입을 옮기고 이름을 바꾸는 중에 경로가 흔들려도 안전.
        uuid_pairs = [(cmds.ls(s, uuid=True)[0], cmds.ls(t, uuid=True)[0]) for s, t in pairs]
        used_sources = []
        for s_uuid, t_uuid in uuid_pairs:
            source = (cmds.ls(s_uuid, long=True) or [None])[0]
            target = (cmds.ls(t_uuid, long=True) or [None])[0]
            if not source or not target:
                result["skipped"].append((source or target or "?", "node no longer exists"))
                continue
            if source == target:
                result["skipped"].append((source, "Source and Target are the same curve"))
                continue
            new_shapes = _copy_shapes(source, target, placement)
            result["added"].append((source, target, new_shapes))
            if s_uuid not in used_sources:
                used_sources.append(s_uuid)

        if delete_sources:
            target_uuids = set(t for _s, t in uuid_pairs)
            for s_uuid in used_sources:
                if s_uuid in target_uuids:
                    continue  # 다른 짝의 Target 이기도 하면 지우지 않는다
                path = (cmds.ls(s_uuid, long=True) or [None])[0]
                if not path:
                    continue
                # Target 이 이 Source 밑에 있으면 Source 를 지우는 순간 Target 도 사라진다
                targets_now = [(cmds.ls(t, long=True) or [""])[0] for t in target_uuids]
                if any(t.startswith(path + "|") for t in targets_now):
                    result["skipped"].append(
                        (path, "not deleted - a Target is under this Source"))
                    continue
                cmds.delete(path)
                result["deleted"].append(path)

    count = sum(len(new) for _s, _t, new in result["added"])
    if not result["added"]:
        result["message"] = "Nothing was combined."
        return result

    result["ok"] = True
    result["message"] = "Combined {0} shape(s) from {1} source curve(s) into {2} target(s){3}.".format(
        count, len(set(s for s, _t, _n in result["added"])),
        len(set(t for _s, t, _n in result["added"])),
        ", {0} source(s) deleted".format(len(result["deleted"])) if result["deleted"] else "")
    return result
