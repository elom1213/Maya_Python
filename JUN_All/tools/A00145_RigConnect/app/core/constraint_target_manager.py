# -*- coding: utf-8 -*-
"""
constraint_target_manager - Constrain 탭 'Target Replace' 로직.

주어진 constraint 들이 쓰고 있는 **타깃(드라이버) 오브젝트**를 모아서 보여 주고,
그중 하나를 씬의 다른 오브젝트로 갈아끼운다.

  before:  con_01 : [tgt_A_01, tgt_A_02]      con_02 : [tgt_A_02, tgt_A_03]
  replace: tgt_A_02  ->  tgt_B_02
  after :  con_01 : [tgt_A_01, tgt_B_02]      con_02 : [tgt_B_02, tgt_A_03]

해당 타깃을 갖고 있지 않은 constraint 는 손대지 않는다.

## 왜 '재생성'이 아니라 '연결 교체'인가

constraint 를 지우고 다시 만들면 노드 이름, 타깃 weight 에 물려 있는 연결
(IK/FK 스위치 어트리뷰트 등), 커스텀 어트리뷰트가 전부 날아간다. 그래서 여기서는
constraint 노드를 그대로 두고 `target[i]` 로 들어오는 입력 연결만 새 오브젝트 쪽으로
갈아끼운다. weight / 이름 / 다른 타깃은 전혀 건드리지 않는다.

`target[i]` 의 실제 멀티 인덱스는 들어오는 연결에서 역추적한다(targetList 순서에
의존하지 않는다). `targetWeight` 및 constraint 자기 자신이 소스인 연결
(pointOnPoly 의 targetU/targetV 등)은 타깃 판정에서 제외한다.

## Keep in place (오프셋 재계산)

새 타깃이 옛 타깃과 다른 위치에 있으면 driven 오브젝트가 튄다. `maintain_offset=True`
면 constraint 의 offset 을 다시 계산해 driven 을 제자리에 붙잡는다. 규약은 Maya 2024
에서 실측으로 확인했다.

- parentConstraint : 타깃별 offset 을 옛 타깃 -> 새 타깃 델타만큼 옮긴다. 위치는 전체
  월드 행렬로, 회전은 스케일을 뺀 회전만으로(두 오프셋이 서로 다른 공간에 산다 —
  `_restore_parent_offset` 참고). 오일러 순서는 driven 의 rotateOrder. 타깃이 여러
  개이고 weight 가 섞여 있어도 **정확**하다 — 타깃별 기여도만 그대로 유지되기 때문.
- pointConstraint  : offset 은 덧셈  ->  `offset += (t_before - t_after)`
- scaleConstraint  : offset 은 곱셈  ->  `offset *= (s_before / s_after)`
- orient/aim       : offset 은 회전 합성 -> `O_new = R_before * R_after^-1 * O_old`
  (오일러 순서 = driven 의 rotateOrder)
- 그 밖(geometry/normal/tangent/pointOnPoly/poleVector) : 보정할 offset 이 없어 그대로 둔다.

보정 후에는 driven 의 월드 행렬을 다시 읽어 실제로 제자리인지 검증하고, 어긋나면
경고를 남긴다(타깃 스케일 차이 등으로 offset 이 표현할 수 없는 경우).

UI 비의존: 위젯에서 읽은 이름 리스트만 받는다. (app/core <-> app/ui 분리)
"""

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

# 노드 해석 헬퍼는 constraint_transfer_manager 와 완전히 동일한 규칙이라 재사용한다.
from .constraint_transfer_manager import (
    _to_uuid, _path, _collect_constraint_uuids)


# driven 이 제자리에 남았는지 검증할 때 쓰는 월드 행렬 성분 허용 오차.
OFFSET_TOLERANCE = 1e-3

# joint 타깃일 때만 연결되는 target[i] 자식들.
# (constraint 쪽 자식, 타깃 쪽 어트리뷰트, (setAttr 종류, joint 가 아닐 때 쓸 기본값))
_JOINT_EXTRAS = (
    ("targetJointOrient", "jointOrient", ("double3", (0.0, 0.0, 0.0))),
    ("targetInverseScale", "inverseScale", ("double3", (1.0, 1.0, 1.0))),
    ("targetScaleCompensate", "segmentScaleCompensate", ("bool", False)),
)
_JOINT_EXTRA_NAMES = tuple(c[0] for c in _JOINT_EXTRAS)


# ------------------------------------------------------------------ 이름/노드

def _nice(path):
    """화면 표시용 이름(씬에서 유일해지는 가장 짧은 이름)."""
    if not path:
        return path
    names = cmds.ls(path) or []
    return names[0] if names else path


def _short(path):
    """계층/네임스페이스를 뗀 노드 이름."""
    return path.split("|")[-1].split(":")[-1]


def _long(name):
    names = cmds.ls(name, long=True) or []
    return names[0] if names else None


def _same_node(a, b):
    """두 이름이 같은 노드를 가리키는가."""
    la, lb = _long(a), _long(b)
    return la is not None and la == lb


def _owner_transform(name):
    """소스 노드가 셰이프면 그 트랜스폼을, 아니면 자기 자신을 롱네임으로 돌려준다."""
    node = _long(name)
    if node is None:
        return None
    try:
        if cmds.objectType(node, isAType="shape"):
            parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
            if parents:
                return parents[0]
    except Exception:
        pass
    return node


def _most_common(items):
    """가장 많이 나온 항목(동률이면 먼저 나온 것). 비었으면 None."""
    best, best_count = None, 0
    for item in items:
        count = items.count(item)
        if count > best_count:
            best, best_count = item, count
    return best


# ------------------------------------------------------------- 플러그 파싱/열거

def _incoming_pairs(node):
    """노드로 들어오는 (destination plug, source plug) 쌍 목록.

    `listConnections` 는 `con.target[0]` 같은 컴파운드 배열 원소 플러그에 대해서는
    None 을 돌려준다. 그래서 노드 단위로 한 번에 받아 와 직접 걸러 낸다.
    """
    conns = cmds.listConnections(
        node, source=True, destination=False, plugs=True, connections=True) or []
    return [(conns[k], conns[k + 1]) for k in range(0, len(conns) - 1, 2)]


def _target_index(plug):
    """'con.target[3].targetRotate' -> 3. 아니면 None."""
    if ".target[" not in plug:
        return None
    try:
        return int(plug.split(".target[", 1)[1].split("]", 1)[0])
    except (ValueError, IndexError):
        return None


def _child_name(plug, index):
    """target[i] 바로 아래 자식 이름('targetRotate' 등)."""
    token = ".target[{0}].".format(index)
    if token not in plug:
        return ""
    return plug.split(token, 1)[1].split(".")[0].split("[")[0]


def _target_entries(cn):
    """constraint 의 target[i] 별 정보 목록.

    Returns:
        [{"index": i, "node": <타깃 롱네임 or None>,
          "pairs": [(dest plug, src plug), ...]}, ...]  (인덱스 오름차순)
    """
    try:
        indices = cmds.getAttr("{0}.target".format(cn), multiIndices=True) or []
    except Exception:
        indices = []

    entries = dict((i, {"index": i, "node": None, "pairs": []}) for i in indices)
    owners = {}

    for dest, src in _incoming_pairs(cn):
        index = _target_index(dest)
        if index is None or index not in entries:
            continue
        child = _child_name(dest, index)
        if not child.startswith("target") or child == "targetWeight":
            continue
        src_node = src.split(".")[0]
        # targetU/targetV 처럼 constraint 자기 자신이 소스인 연결은 타깃이 아니다.
        if _same_node(src_node, cn):
            continue
        entries[index]["pairs"].append((dest, src))
        owner = _owner_transform(src_node)
        if owner:
            owners.setdefault(index, []).append(owner)

    for index, entry in entries.items():
        entry["node"] = _most_common(owners.get(index, []))
    return [entries[i] for i in sorted(entries)]


def _driven(cn):
    """constraint 가 구동하는 오브젝트. 부모 -> constraintParentInverseMatrix 순."""
    parents = cmds.listRelatives(cn, parent=True, fullPath=True) or []
    if parents:
        return parents[0]
    plug = "{0}.constraintParentInverseMatrix".format(cn)
    if cmds.objExists(plug):
        srcs = cmds.listConnections(
            plug, source=True, destination=False, fullPath=True) or []
        if srcs:
            return srcs[0]
    return None


# ------------------------------------------------------------------- 행렬 헬퍼

def _decompose(matrix, order):
    tm = om.MTransformationMatrix(matrix)
    t = tm.translation(om.MSpace.kTransform)
    e = tm.rotation(asQuaternion=False)
    if order:
        e = e.reorder(order)
    return ([t.x, t.y, t.z],
            [math.degrees(e.x), math.degrees(e.y), math.degrees(e.z)])


def _euler_matrix(rotate_deg, order):
    return om.MEulerRotation(
        math.radians(rotate_deg[0]), math.radians(rotate_deg[1]),
        math.radians(rotate_deg[2]), order).asMatrix()


def _rotation_only(matrix):
    """스케일/셰어를 뺀 순수 회전 행렬."""
    return om.MTransformationMatrix(matrix).rotation(asQuaternion=True).asMatrix()


def _world_matrix(node):
    return om.MMatrix(cmds.xform(node, q=True, ws=True, matrix=True))


# =========================================================== 공개 API : 목록

def list_targets(constraint_names):
    """constraint 들이 쓰는 타깃 오브젝트를 모아서 돌려준다.

    Args:
        constraint_names: constraint 노드 또는 constraint 가 걸린 트랜스폼 이름들.

    Returns:
        (rows, warnings)
        rows: [{"name": 표시 이름, "uuid": ..., "constraints": [사용 중인 constraint 이름],
                "total": 조사한 constraint 개수}, ...]  (처음 나온 순서)
    """
    if not constraint_names:
        raise ValueError("No constraints. Add constraints to the list.")

    con_uuids, warnings = _collect_constraint_uuids(constraint_names)
    if not con_uuids:
        raise ValueError("No valid constraints found in the list.")

    order = []
    info = {}
    scanned = 0

    for con_uuid in con_uuids:
        cn = _path(con_uuid)
        if cn is None:
            continue
        scanned += 1
        for entry in _target_entries(cn):
            node = entry["node"]
            if node is None:
                warnings.append(
                    "{0} : target[{1}] has no resolvable target node".format(
                        _nice(cn), entry["index"]))
                continue
            uuid = _to_uuid(node)
            if uuid is None:
                continue
            if uuid not in info:
                info[uuid] = {"uuid": uuid, "name": _nice(node), "constraints": []}
                order.append(uuid)
            name = _nice(cn)
            if name not in info[uuid]["constraints"]:
                info[uuid]["constraints"].append(name)

    rows = []
    for uuid in order:
        row = dict(info[uuid])
        row["total"] = scanned
        rows.append(row)
    return rows, warnings


# =========================================================== 교체 : 한 슬롯

def _equivalent_plug(src_plug, old_node, new_node):
    """옛 타깃의 소스 플러그에 대응하는 새 타깃 쪽 플러그. 못 만들면 None."""
    src_node, attr = src_plug.split(".", 1)
    src_long = _long(src_node) or src_node

    if _same_node(src_long, old_node):
        candidate = new_node
    else:
        # 옛 타깃의 셰이프에서 나온 연결(worldMesh 등) -> 새 타깃의 같은 타입 셰이프.
        shape_type = cmds.nodeType(src_long)
        shapes = cmds.listRelatives(
            new_node, shapes=True, fullPath=True, noIntermediate=True) or []
        same = [s for s in shapes if cmds.nodeType(s) == shape_type]
        candidate = same[0] if same else None

    if not candidate:
        return None
    plug = "{0}.{1}".format(candidate, attr)
    return plug if cmds.objExists(plug) else None


def _set_joint_default(plug, child):
    """joint 전용 자식을 joint 가 아닌 타깃에 맞는 기본값으로 되돌린다."""
    for name, _attr, (kind, value) in _JOINT_EXTRAS:
        if name != child:
            continue
        try:
            if kind == "double3":
                cmds.setAttr(plug, value[0], value[1], value[2], type="double3")
            else:
                cmds.setAttr(plug, value)
        except Exception:
            pass
        return


def _sync_joint_extras(cn, index, new_node):
    """새 타깃이 joint 면 jointOrient 계열 연결을 붙여 준다(옛 타깃이 joint 가 아니었던 경우)."""
    for child, attr, _default in _JOINT_EXTRAS:
        dest = "{0}.target[{1}].{2}".format(cn, index, child)
        if not cmds.objExists(dest):
            continue
        src = "{0}.{1}".format(new_node, attr)
        if not cmds.objExists(src):
            continue
        if cmds.listConnections(dest, source=True, destination=False, plugs=True):
            continue
        try:
            cmds.connectAttr(src, dest, force=True)
        except Exception:
            pass


def _rename_weight_attr(cn, index, old_node, new_node):
    """target[i].targetWeight 를 먹이는 weight 어트리뷰트 이름을 새 타깃 기준으로 바꾼다.

    Maya 가 자동으로 만든 이름(`<타깃>W<n>`)일 때만 손댄다. 빈 문자열이면 변경 없음.
    """
    dest = "{0}.target[{1}].targetWeight".format(cn, index)
    srcs = cmds.listConnections(
        dest, source=True, destination=False, plugs=True) or []
    if not srcs:
        return ""
    node, attr = srcs[0].split(".", 1)
    if not _same_node(node, cn):
        return ""

    old_short = _short(old_node)
    if not attr.startswith(old_short):
        return ""
    new_attr = _short(new_node) + attr[len(old_short):]
    if new_attr == attr:
        return ""
    if cmds.attributeQuery(new_attr, node=cn, exists=True):
        return "weight attribute '{0}' already exists".format(new_attr)
    try:
        cmds.renameAttr("{0}.{1}".format(cn, attr), new_attr)
    except Exception as e:
        return "weight rename failed : {0}".format(e)
    return "weight {0} -> {1}".format(attr, new_attr)


# ------------------------------------------------------------------ 오프셋 보정

def _rotate_order(cn, driven):
    """offset 오일러에 쓸 회전 순서(= driven 의 rotateOrder)."""
    plug = "{0}.constraintRotateOrder".format(cn)
    if cmds.objExists(plug):
        try:
            return cmds.getAttr(plug)
        except Exception:
            pass
    if driven:
        try:
            return cmds.getAttr("{0}.rotateOrder".format(driven))
        except Exception:
            pass
    return 0


def _capture(cn, ctype, driven, index, old_node):
    """교체 전 상태(오프셋 복원에 필요한 값)를 기록한다."""
    data = {"rotate_order": _rotate_order(cn, driven), "matrix": None}

    if driven:
        try:
            data["matrix"] = cmds.xform(driven, q=True, ws=True, matrix=True)
        except Exception:
            data["matrix"] = None
        for key, attr in (("t", "translate"), ("r", "rotate"), ("s", "scale")):
            try:
                data[key] = list(cmds.getAttr("{0}.{1}".format(driven, attr))[0])
            except Exception:
                data[key] = None

    if ctype == "parentConstraint":
        try:
            data["target_world"] = _world_matrix(old_node)
            data["offset_t"] = list(cmds.getAttr(
                "{0}.target[{1}].targetOffsetTranslate".format(cn, index))[0])
            data["offset_r"] = list(cmds.getAttr(
                "{0}.target[{1}].targetOffsetRotate".format(cn, index))[0])
        except Exception:
            data["target_world"] = None
    else:
        try:
            data["offset"] = list(cmds.getAttr("{0}.offset".format(cn))[0])
        except Exception:
            data["offset"] = None
    return data


def _restore_parent_offset(cn, index, before, new_node):
    """parentConstraint 의 타깃별 오프셋을 새 타깃 기준으로 다시 계산한다.

    Maya 2024 실측 결과, 두 오프셋은 서로 다른 공간에 산다.
      targetOffsetTranslate = (driven_world * inverse(target_world)) 의 이동   -> 타깃 스케일 포함
      targetOffsetRotate    = 스케일을 뺀 회전 차이                            -> 스케일 무관
    그래서 위치는 전체 행렬로, 회전은 순수 회전 행렬로 각각 옮겨야 타깃에 스케일이
    걸려 있어도 driven 이 제자리에 남는다.
    """
    if before.get("target_world") is None:
        return "offset not restored (could not read the old target)"

    order = before["rotate_order"]
    old_world = before["target_world"]
    new_world = _world_matrix(new_node)

    point = om.MPoint(*before["offset_t"]) * old_world * new_world.inverse()
    rotation = (_euler_matrix(before["offset_r"], order)
                * _rotation_only(old_world) * _rotation_only(new_world).inverse())
    _t, rotate = _decompose(rotation, order)

    cmds.setAttr("{0}.target[{1}].targetOffsetTranslate".format(cn, index),
                 point.x, point.y, point.z, type="double3")
    cmds.setAttr("{0}.target[{1}].targetOffsetRotate".format(cn, index),
                 rotate[0], rotate[1], rotate[2], type="double3")
    return ""


def _restore_point_offset(cn, driven, before):
    if before.get("offset") is None or not before.get("t") or not driven:
        return "offset not restored (no offset attribute)"
    after = cmds.getAttr("{0}.translate".format(driven))[0]
    values = [before["offset"][i] + (before["t"][i] - after[i]) for i in range(3)]
    cmds.setAttr("{0}.offset".format(cn), values[0], values[1], values[2])
    return ""


def _restore_scale_offset(cn, driven, before):
    if before.get("offset") is None or not before.get("s") or not driven:
        return "offset not restored (no offset attribute)"
    after = cmds.getAttr("{0}.scale".format(driven))[0]
    values = []
    for i in range(3):
        if abs(after[i]) < 1e-9:
            values.append(before["offset"][i])
        else:
            values.append(before["offset"][i] * before["s"][i] / after[i])
    cmds.setAttr("{0}.offset".format(cn), values[0], values[1], values[2])
    return ""


def _restore_rotate_offset(cn, driven, before):
    if before.get("offset") is None or not before.get("r") or not driven:
        return "offset not restored (no offset attribute)"
    order = before["rotate_order"]
    after = cmds.getAttr("{0}.rotate".format(driven))[0]
    matrix = (_euler_matrix(before["r"], order)
              * _euler_matrix(after, order).inverse()
              * _euler_matrix(before["offset"], order))
    _t, rotate = _decompose(matrix, order)
    cmds.setAttr("{0}.offset".format(cn), rotate[0], rotate[1], rotate[2])
    return ""


def _restore_offset(cn, ctype, driven, index, before, new_node):
    """driven 이 제자리에 남도록 offset 을 다시 계산한다. 문제가 있으면 메시지 반환."""
    if ctype == "parentConstraint":
        note = _restore_parent_offset(cn, index, before, new_node)
    elif ctype == "pointConstraint":
        note = _restore_point_offset(cn, driven, before)
    elif ctype == "scaleConstraint":
        note = _restore_scale_offset(cn, driven, before)
    elif ctype in ("orientConstraint", "aimConstraint"):
        note = _restore_rotate_offset(cn, driven, before)
    else:
        return "offset not restored ({0} has no offset to compensate)".format(ctype)
    if note:
        return note

    # 실제로 제자리인지 검증.
    if driven and before.get("matrix"):
        try:
            now = cmds.xform(driven, q=True, ws=True, matrix=True)
        except Exception:
            return ""
        error = max(abs(now[i] - before["matrix"][i]) for i in range(16))
        if error > OFFSET_TOLERANCE:
            return ("'{0}' moved (max error {1:.4f}) - the offset cannot express "
                    "this change".format(_nice(driven), error))
    return ""


def _replace_entry(cn, entry, old_node, new_node, maintain_offset, rename_weight):
    """target[i] 한 슬롯의 드라이버를 교체한다. (성공 여부, 메시지)"""
    index = entry["index"]
    ctype = cmds.nodeType(cn)
    driven = _driven(cn)

    # 먼저 모든 대응 플러그를 해석한다. 하나라도 못 만들면 아무것도 건드리지 않는다.
    plan = []
    missing = []
    for dest, src in entry["pairs"]:
        child = _child_name(dest, index)
        new_src = _equivalent_plug(src, old_node, new_node)
        if new_src:
            plan.append((dest, new_src))
        elif child in _JOINT_EXTRA_NAMES:
            # joint -> 비 joint 교체. 연결을 끊고 기본값으로 되돌린다.
            plan.append((dest, None))
        else:
            missing.append(child)
    if missing:
        return False, "{0} : cannot drive {1} from '{2}' - target left as is".format(
            _nice(cn), ", ".join(sorted(set(missing))), _nice(new_node))

    before = _capture(cn, ctype, driven, index, old_node) if maintain_offset else None

    for dest, new_src in plan:
        if new_src:
            cmds.connectAttr(new_src, dest, force=True)
            continue
        for src in cmds.listConnections(
                dest, source=True, destination=False, plugs=True) or []:
            try:
                cmds.disconnectAttr(src, dest)
            except Exception:
                pass
        _set_joint_default(dest, _child_name(dest, index))

    _sync_joint_extras(cn, index, new_node)

    notes = []
    if before is not None:
        note = _restore_offset(cn, ctype, driven, index, before, new_node)
        if note:
            notes.append(note)
    if rename_weight:
        note = _rename_weight_attr(cn, index, old_node, new_node)
        if note:
            notes.append(note)
    return True, "; ".join(notes)


# =========================================================== 공개 API : 교체

def _resolve_uuids(names, label, warnings):
    uuids = []
    for name in names:
        matches = cmds.ls(name, uuid=True) or []
        if not matches:
            warnings.append("Skipped {0} (not found): {1}".format(label, name))
            continue
        if len(matches) > 1:
            warnings.append(
                "Ambiguous {0} '{1}' ({2} matches) - using first.".format(
                    label, name, len(matches)))
        uuids.append(matches[0])
    return uuids


def _map_pairs(old_uuids, new_uuids, warnings):
    """옛 타깃 <-> 새 타깃 매핑. 새 타깃 1개면 전부 그쪽으로, 개수가 같으면 1:1."""
    if len(new_uuids) == 1:
        return [(old, new_uuids[0]) for old in old_uuids]
    if len(old_uuids) == len(new_uuids):
        return list(zip(old_uuids, new_uuids))
    count = min(len(old_uuids), len(new_uuids))
    warnings.append(
        "Count mismatch (targets {0} vs new targets {1}) - replacing {2} "
        "pair(s).".format(len(old_uuids), len(new_uuids), count))
    return list(zip(old_uuids[:count], new_uuids[:count]))


def replace_targets(constraint_names, old_targets, new_targets,
                    maintain_offset=True, rename_weight=False):
    """constraint 들의 타깃을 다른 오브젝트로 갈아끼운다.

    Args:
        constraint_names: constraint 노드 또는 constraint 가 걸린 트랜스폼 이름들.
        old_targets: 교체할 타깃 이름들(list_targets 결과에서 고른 것).
        new_targets: 대신 들어갈 오브젝트들. 1개면 모든 옛 타깃이 그것으로,
            개수가 같으면 인덱스 1:1.
        maintain_offset: True 면 offset 을 다시 계산해 driven 을 제자리에 둔다.
        rename_weight: True 면 weight 어트리뷰트 이름(`<타깃>W<n>`)도 새 타깃 기준으로.

    Returns:
        (results, warnings)
        results: [{"constraint": ..., "old": ..., "new": ..., "index": i,
                   "note": ...}, ...]
    """
    if not constraint_names:
        raise ValueError("No constraints. Add constraints to the list.")
    if not old_targets:
        raise ValueError("No target picked. Select the target(s) to replace "
                         "in the Targets list.")
    if not new_targets:
        raise ValueError("No new target. Add the replacement object(s) to the "
                         "New Target list.")

    con_uuids, warnings = _collect_constraint_uuids(constraint_names)
    if not con_uuids:
        raise ValueError("No valid constraints found in the list.")

    old_uuids = _resolve_uuids(old_targets, "target", warnings)
    new_uuids = _resolve_uuids(new_targets, "new target", warnings)
    if not old_uuids:
        raise ValueError("None of the picked targets exist in the scene.")
    if not new_uuids:
        raise ValueError("None of the new targets exist in the scene.")

    results = []

    for old_uuid, new_uuid in _map_pairs(old_uuids, new_uuids, warnings):
        old_node = _path(old_uuid)
        new_node = _path(new_uuid)
        if old_node is None or new_node is None:
            warnings.append("Skipped a pair (object no longer in scene).")
            continue
        if old_uuid == new_uuid:
            warnings.append("Skipped '{0}' - it is the same object as the new "
                            "target.".format(_nice(old_node)))
            continue

        for con_uuid in con_uuids:
            cn = _path(con_uuid)
            if cn is None:
                continue
            entries = _target_entries(cn)
            hits = [e for e in entries
                    if e["node"] and _to_uuid(e["node"]) == old_uuid]
            # 그 타깃을 쓰지 않는 constraint 는 방치한다.
            if not hits:
                continue
            if any(e["node"] and _to_uuid(e["node"]) == new_uuid for e in entries):
                warnings.append(
                    "Skipped {0} - '{1}' is already a target of it.".format(
                        _nice(cn), _nice(new_node)))
                continue

            for entry in hits:
                ok, note = _replace_entry(
                    cn, entry, old_node, new_node, maintain_offset, rename_weight)
                if not ok:
                    warnings.append(note)
                    continue
                results.append({
                    "constraint": _nice(cn),
                    "old": _nice(old_node),
                    "new": _nice(new_node),
                    "index": entry["index"],
                    "note": note,
                })

    return results, warnings
