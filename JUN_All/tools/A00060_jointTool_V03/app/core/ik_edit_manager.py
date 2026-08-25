# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-25
# A00060_jointTool_V03 - 이미 설치된 ikHandle 을 그대로 둔 채 본 체인을 수정한다.
#
# 마야 2024 의 컨스트레인트에는 Update(Update Offset) 버튼이 있어서, 드리븐을 손으로
# 옮긴 뒤 그 자리를 새 오프셋으로 굳힐 수 있다(실체는 `parentConstraint -e -maintainOffset`).
# **ikHandle 에는 그런 버튼이 없다** - AEikHandleTemplate.mel 을 봐도 없고, 명령에도 없다.
# 이 모듈이 그 자리를 메운다.
#
# ── 무엇이 문제인가 ─────────────────────────────────────────────────────────
#
# IK 가 걸린 체인은 조인트를 못 움직인다. 솔버가 매 평가마다 되돌려 놓기 때문이다
# (실측: 중간 조인트를 (2,5,1) 로 보내도 (0.00068, 5.2, 1.72) 로 끌려간다).
# IK 를 끄면 움직일 수 있지만, 다시 켜면 두 가지가 어긋난다.
#
#   1. **핸들 위치** - 체인 끝이 옮겨졌는데 핸들은 옛 자리에 있다.
#   2. **폴 벡터**   - 이게 진짜 함정이다. 핸들만 이펙터로 스냅하면 체인이 옛 평면으로
#      비틀린다. 실측 최대 편차 **1.615**. 폴 벡터는 "루트에서 뻗은 벡터"이고 체인이
#      놓일 평면을 정하는데, 체인을 고치면 그 평면이 바뀌기 때문이다.
#
# ── 어떻게 고치는가 ─────────────────────────────────────────────────────────
#
# 편집이 끝난 체인에서 **원하는 폴 벡터를 역산**해 넣는다. 폴 벡터 컨스트레인트가
# 걸려 있으면 컨스트레인트를 그대로 둔 채 **offset 만** 갱신한다 - 마야 2024 의
# Update Offset 과 정확히 같은 발상이다.
#
#   poleVectorConstraint 의 식 (Maya 2024 실측):
#       pv = (target_world - ikRoot_world) * handle.parentInverseMatrix(3x3) + offset
#
#   offset 은 출력(핸들 부모) 공간에서 그대로 더해지므로 역산이 선형이다:
#       new_offset = desired_pv - (current_pv - current_offset)
#
# 원하는 폴 벡터는 편집된 체인의 팔꿈치 방향이다 - 루트->중간 벡터에서 체인 축
# 성분을 뺀 **수직 성분**을 쓴다(축과 평행해질 위험이 없다).
#
# twist 가 0 이 아니면 솔버가 그 각만큼 평면을 더 돌리므로(실측 편차 1.06),
# 원하는 폴 벡터를 체인 축 기준 **-twist** 만큼 미리 돌려 상쇄한다. twist 값 자체는
# 애니메이션 채널이라 건드리지 않는다. (ikRPsolver 는 roll 을 쓰지 않는다 - 실측.)
#
# 결과: 위치·회전 모두 편차 **0.00000000**. 핸들을 끌었다 놔도, 씬을 저장했다 열어도 유지된다.
#
# ── 상태는 씬에 둔다 ────────────────────────────────────────────────────────
#
# A00275 의 Edit Mesh 와 같은 규칙이다. 편집 중이라는 사실과 되돌릴 스냅샷은 UI 가
# 아니라 **ikHandle 노드의 어트리뷰트**에 있다. 툴을 껐다 켜도, 씬을 저장했다 열어도
# 이어서 확정하거나 취소할 수 있다.

import json
import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_undo import undo_chunk


# 편집 중임을 표시하는 부울 어트리뷰트 (ikHandle 에 붙는다)
EDIT_TAG_ATTR = "JUN_ikEdit"

# 편집 시작 시점 스냅샷(JSON). 취소/복원용.
DATA_ATTR = "JUN_ikEditData"

# 폴 벡터를 쓰는 솔버. 이 둘만 폴 벡터 갱신 대상이다.
RP_LIKE_SOLVERS = ("ikRPsolver", "ikSpringSolver")

# 폴 벡터가 없는(핸들 스냅만 하면 되는) 솔버.
SC_SOLVERS = ("ikSCsolver",)

# 커브가 체인을 구동하므로 "핸들 스냅" 이라는 개념이 성립하지 않는다.
CURVE_SOLVERS = ("ikSplineSolver",)

# 폴 벡터 갱신 방법
PV_MODE_OFFSET = "offset"    # 컨스트레인트 offset 을 갱신 (기본)
PV_MODE_TARGET = "target"    # 폴 벡터 타깃(로케이터) 자체를 새 평면으로 옮긴다

# 핸들을 무엇으로 옮길지
SNAP_HANDLE = "handle"       # 핸들 자신 (기본)
SNAP_PARENT = "parent"       # 핸들의 부모를 옮겨 핸들의 로컬 오프셋을 지킨다

_XFORM_ATTRS = ("translateX", "translateY", "translateZ",
                "rotateX", "rotateY", "rotateZ",
                "scaleX", "scaleY", "scaleZ")


# =========================
# 낮은 수준 헬퍼
# =========================

def _long(node):
    found = cmds.ls(node, l=True) or []
    return found[0] if found else None


def _uuid(node):
    found = cmds.ls(node, uuid=True) or []
    return found[0] if found else None


def _from_uuid(uuid):
    found = cmds.ls(uuid, l=True) or []
    return found[0] if found else None


def _short(node):
    return node.split("|")[-1] if node else ""


def _flush(node):
    """DG 를 강제로 평가시켜 최신 월드 값을 읽을 수 있게 한다.

    컨스트레인트가 걸린 노드는 setAttr 직후에 조회하면 아직 되돌려지기 전 값이 나온다
    (실측: point 컨스트레인트가 걸린 핸들에 xform 을 걸면 그 값이 잠깐 그대로 읽힌다).
    """
    try:
        cmds.dgdirty(node)
    except Exception:
        pass
    for plug in (".worldMatrix[0]", ".translate"):
        try:
            cmds.dgeval(node + plug)
            return
        except Exception:
            continue


def world_pos(node):
    return cmds.xform(node, q=True, ws=True, t=True)


def world_rot(node):
    return cmds.xform(node, q=True, ws=True, ro=True)


def _sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _scaled(a, s):
    return [a[0] * s, a[1] * s, a[2] * s]


def _length(a):
    return math.sqrt(_dot(a, a))


def _rotation_only(matrix16):
    """4x4 에서 평행이동을 뺀 선형부만. 벡터를 공간 변환할 때 쓴다."""
    m = matrix16
    return om.MMatrix([m[0], m[1], m[2], 0.0,
                       m[4], m[5], m[6], 0.0,
                       m[8], m[9], m[10], 0.0,
                       0.0, 0.0, 0.0, 1.0])


def world_vector_to_parent(node, vec):
    """월드 벡터를 node 의 부모 공간으로. poleVector 어트리뷰트가 사는 공간이다."""
    pim = cmds.getAttr(node + ".parentInverseMatrix")
    r = om.MVector(*vec) * _rotation_only(pim)
    return [r.x, r.y, r.z]


def _rotate_about(vec, axis, degrees):
    """vec 를 axis 둘레로 degrees 만큼 회전."""
    a = om.MVector(*axis)
    if a.length() < 1e-12:
        return list(vec)
    q = om.MQuaternion(math.radians(degrees), a.normal())
    r = om.MVector(*vec).rotateBy(q)
    return [r.x, r.y, r.z]


def _writable(plug):
    """setAttr 이 실제로 '먹는지'.

    `getAttr(plug, settable=True)` 는 믿을 수 없다 - **컨스트레인트가 구동하는 트랜스폼에
    대해서도 True 를 돌려준다**(실측: pointConstraint 가 걸린 ikHandle 의 translateX 가
    settable=True). 그 말을 믿으면 핸들을 옮겼다고 보고해 놓고 실제로는 컨스트레인트가
    도로 끌어가, 편차 1.0 이 조용히 남는다. 잠금과 입력 연결을 직접 본다.

    컴파운드(translate 등)를 넘기면 자식 플러그까지 함께 본다.
    """
    if not cmds.objExists(plug):
        return False

    plugs = [plug]
    node, attr = plug.split(".", 1)
    try:
        for kid in (cmds.attributeQuery(attr, node=node, listChildren=True) or []):
            plugs.append("{0}.{1}".format(node, kid))
    except Exception:
        pass

    for p in plugs:
        try:
            if cmds.getAttr(p, lock=True):
                return False
            if cmds.connectionInfo(p, isDestination=True):
                return False
        except Exception:
            return False
    return True


def _translate_settable(node):
    return _writable(node + ".translate")


# =========================
# ikHandle 조회
# =========================

def handle_solver(handle):
    try:
        return cmds.ikHandle(handle, q=True, solver=True)
    except Exception:
        return ""


def chain_joints(handle):
    """루트부터 끝 조인트까지 전부.

    `ikHandle -q -jointList` 는 **끝 조인트를 빼고** 준다(실측: 4조인트 체인에서 3개).
    끝 조인트는 이펙터의 translate 를 구동하는 조인트다 - 이펙터 translateX 의 입력이
    곧 끝 조인트다.
    """
    jl = cmds.ikHandle(handle, q=True, jointList=True) or []
    jl = [_long(j) for j in jl if _long(j)]

    end = None
    eff = cmds.ikHandle(handle, q=True, endEffector=True)
    if eff and cmds.objExists(eff):
        src = cmds.listConnections(eff + ".translateX", d=False, s=True) or []
        if src:
            end = _long(src[0])
    if not end and jl:
        # 폴백: 마지막 조인트의 조인트 자식
        kids = cmds.listRelatives(jl[-1], c=True, type="joint", f=True) or []
        end = kids[0] if kids else None

    if end and end not in jl:
        jl.append(end)
    return jl


def end_effector(handle):
    eff = cmds.ikHandle(handle, q=True, endEffector=True)
    return _long(eff) if eff and cmds.objExists(eff) else None


def pole_vector_constraint(handle):
    """핸들의 poleVector 를 구동하는 poleVectorConstraint. 없으면 None."""
    cons = cmds.listConnections(handle + ".poleVectorX", d=False, s=True,
                                type="poleVectorConstraint") or []
    return _long(cons[0]) if cons else None


def pole_vector_driver(handle):
    """poleVector 를 구동하는 무엇이든(컨스트레인트가 아닐 수도 있다)."""
    cons = cmds.listConnections(handle + ".poleVector", d=False, s=True) or []
    if not cons:
        for axis in "XYZ":
            cons = cmds.listConnections(handle + ".poleVector" + axis,
                                        d=False, s=True) or []
            if cons:
                break
    return _long(cons[0]) if cons else None


def pole_vector_targets(constraint):
    try:
        return cmds.poleVectorConstraint(constraint, q=True, targetList=True) or []
    except Exception:
        return []


# =========================
# 편집 상태 (씬에 저장)
# =========================

def is_editing(handle):
    return bool(handle and cmds.objExists(handle) and
                cmds.attributeQuery(EDIT_TAG_ATTR, node=handle, exists=True))


def editing_of(handles):
    return [h for h in (handles or []) if is_editing(h)]


def find_editing_in_scene():
    """툴 밖에서 시작된(또는 툴을 껐다 켠) 편집을 되찾는다."""
    out = []
    for h in (cmds.ls(type="ikHandle", l=True) or []):
        if is_editing(h):
            out.append(h)
    return out


def _read_data(handle):
    plug = "{0}.{1}".format(handle, DATA_ATTR)
    if not cmds.attributeQuery(DATA_ATTR, node=handle, exists=True):
        return {}
    try:
        return json.loads(cmds.getAttr(plug) or "")
    except Exception:
        return {}


def _write_data(handle, payload):
    plug = "{0}.{1}".format(handle, DATA_ATTR)
    if not cmds.attributeQuery(DATA_ATTR, node=handle, exists=True):
        cmds.addAttr(handle, ln=DATA_ATTR, dt="string")
    cmds.setAttr(plug, json.dumps(payload), type="string")


def _mark(handle, on):
    exists = cmds.attributeQuery(EDIT_TAG_ATTR, node=handle, exists=True)
    if on and not exists:
        cmds.addAttr(handle, ln=EDIT_TAG_ATTR, at="bool")
        cmds.setAttr("{0}.{1}".format(handle, EDIT_TAG_ATTR), True)
    elif not on and exists:
        try:
            cmds.deleteAttr("{0}.{1}".format(handle, EDIT_TAG_ATTR))
        except Exception:
            pass


def _clear_state(handle):
    _mark(handle, False)
    if cmds.attributeQuery(DATA_ATTR, node=handle, exists=True):
        try:
            cmds.deleteAttr("{0}.{1}".format(handle, DATA_ATTR))
        except Exception:
            pass


# =========================
# 대상 해석
# =========================

def resolve_targets(nodes=None):
    """선택에서 ikHandle 을 찾는다.

    핸들 자체 / 체인 안의 조인트 / 핸들을 구동하는 컨트롤러 중 무엇을 골라도 된다.
    """
    if nodes is None:
        nodes = cmds.ls(sl=True, l=True) or []
    if not nodes:
        raise RuntimeError("Nothing selected. Select an IK handle or a joint of an IK chain.")

    found = []

    def add(h):
        h = _long(h)
        if h and h not in found:
            found.append(h)

    all_handles = cmds.ls(type="ikHandle", l=True) or []
    chains = {}
    for h in all_handles:
        chains[h] = set(chain_joints(h))

    for n in nodes:
        n = _long(n) or n
        if not n or not cmds.objExists(n):
            continue

        # 핸들 자체
        shapes = cmds.listRelatives(n, s=True, f=True) or []
        if cmds.nodeType(n) == "ikHandle":
            add(n)
            continue
        if any(cmds.nodeType(s) == "ikHandle" for s in shapes):
            add(n)
            continue

        # 체인 안의 조인트
        hit = False
        for h, js in chains.items():
            if n in js:
                add(h)
                hit = True
        if hit:
            continue

        # 이 노드가 구동하는 핸들 (컨트롤러를 골랐을 때)
        downstream = cmds.listConnections(n, s=False, d=True, type="ikHandle") or []
        for h in downstream:
            add(h)

    if not found:
        raise RuntimeError(
            "No IK handle found from the selection. Select the handle itself, "
            "any joint of the IK chain, or the control that drives the handle.")
    return found


def describe(handles):
    if not handles:
        return "No IK handle loaded."
    parts = []
    for h in handles:
        if not cmds.objExists(h):
            continue
        parts.append("{0} ({1}, {2} joints)".format(
            _short(h), handle_solver(h) or "?", len(chain_joints(h))))
    return "   |   ".join(parts) if parts else "No IK handle loaded."


def inspect(handle):
    """편집 전에 무엇이 되고 무엇이 막히는지 미리 알려 준다."""
    info = {
        "handle": handle,
        "solver": handle_solver(handle),
        "joints": chain_joints(handle),
        "effector": end_effector(handle),
        "pv_constraint": None,
        "pv_driver": None,
        "pv_targets": [],
        "twist": 0.0,
        "blockers": [],
        "notes": [],
    }

    solver = info["solver"]
    if solver in CURVE_SOLVERS:
        info["blockers"].append(
            "{0} is driven by a curve, not by a handle position - "
            "rebuild the curve instead.".format(solver))
        return info

    if not info["joints"]:
        info["blockers"].append("Could not resolve the joint chain of this handle.")
        return info

    if not info["effector"]:
        info["blockers"].append("Could not find the end effector of this handle.")

    if solver in RP_LIKE_SOLVERS:
        con = pole_vector_constraint(handle)
        info["pv_constraint"] = con
        if con:
            info["pv_targets"] = pole_vector_targets(con)
            info["notes"].append(
                "Pole vector constraint '{0}' will be kept; only its offset is updated."
                .format(_short(con)))
        else:
            driver = pole_vector_driver(handle)
            info["pv_driver"] = driver
            if driver:
                info["blockers"].append(
                    "poleVector is driven by '{0}' which is not a poleVectorConstraint - "
                    "the pole vector cannot be updated.".format(_short(driver)))
            else:
                info["notes"].append("No pole vector constraint - poleVector is set directly.")
        try:
            info["twist"] = cmds.getAttr(handle + ".twist")
        except Exception:
            pass
    elif solver in SC_SOLVERS:
        info["notes"].append("Single chain solver - no pole vector, the handle snap is enough.")

    return info


# =========================
# 편집 시작
# =========================

def _capture_joint(j):
    return {
        "uuid": _uuid(j),
        "t": list(cmds.getAttr(j + ".translate")[0]),
        "r": list(cmds.getAttr(j + ".rotate")[0]),
        "s": list(cmds.getAttr(j + ".scale")[0]),
        "jo": list(cmds.getAttr(j + ".jointOrient")[0]),
        "pa": list(cmds.getAttr(j + ".preferredAngle")[0]),
        "locked": [a for a in _XFORM_ATTRS
                   if cmds.getAttr("{0}.{1}".format(j, a), lock=True)],
    }


def _disable_ik(handle, data):
    """이 핸들의 IK 를 끈다. 되도록 핸들 하나만, 안 되면 씬 전체.

    ikBlend 가 FK/IK 스위치에 연결돼 있으면 setAttr 이 RuntimeError 를 낸다(실측).
    그럴 때만 `ikSystem -e -solve 0`(마야의 "Enable IK Solvers" 토글)으로 물러선다.
    """
    plug = handle + ".ikBlend"
    if _writable(plug):
        data["blend_mode"] = "ikBlend"
        data["ikBlend"] = cmds.getAttr(plug)
        cmds.setAttr(plug, 0.0)
        return "IK disabled on '{0}' (ikBlend 0).".format(_short(handle))

    data["blend_mode"] = "ikSystem"
    data["ik_system_solve"] = bool(cmds.ikSystem(q=True, solve=True))
    cmds.ikSystem(e=True, solve=False)
    return ("'{0}'.ikBlend is driven, so IK solving was disabled scene-wide "
            "(Enable IK Solvers off) for this edit.".format(_short(handle)))


def _restore_ik(handle, data):
    if data.get("blend_mode") == "ikBlend":
        plug = handle + ".ikBlend"
        if _writable(plug):
            cmds.setAttr(plug, data.get("ikBlend", 1.0))
    else:
        cmds.ikSystem(e=True, solve=bool(data.get("ik_system_solve", True)))


def reassert_disabled(handles):
    """진행 중인 편집을 되찾았을 때 IK 가 다시 켜져 있으면 도로 끈다.

    `ikSystem -solve` 는 씬이 아니라 세션 상태라 마야를 다시 켜면 살아난다.
    """
    messages = []
    for h in editing_of(handles):
        data = _read_data(h)
        if data.get("blend_mode") == "ikSystem":
            if cmds.ikSystem(q=True, solve=True):
                cmds.ikSystem(e=True, solve=False)
                messages.append(
                    "Re-disabled scene-wide IK solving for the edit in progress on "
                    "'{0}'.".format(_short(h)))
        else:
            plug = h + ".ikBlend"
            if _writable(plug) and abs(cmds.getAttr(plug)) > 1e-9:
                cmds.setAttr(plug, 0.0)
                messages.append("Re-disabled IK on '{0}'.".format(_short(h)))
    return messages


def begin_edit(handles):
    """IK 를 끄고 스냅샷을 남긴다. 이제 조인트를 자유롭게 움직일 수 있다."""
    messages = []
    started = []

    with undo_chunk():
        for h in handles:
            if not cmds.objExists(h):
                messages.append("[Warning] '{0}' no longer exists.".format(_short(h)))
                continue
            if is_editing(h):
                messages.append("[Info] '{0}' is already in edit mode.".format(_short(h)))
                continue

            info = inspect(h)
            if info["blockers"]:
                for b in info["blockers"]:
                    messages.append("[Warning] {0}: {1}".format(_short(h), b))
                continue

            joints = info["joints"]
            data = {
                "handle_uuid": _uuid(h),
                "solver": info["solver"],
                "joints": [_capture_joint(j) for j in joints],
                "handle_t": list(cmds.getAttr(h + ".translate")[0]),
                "handle_r": list(cmds.getAttr(h + ".rotate")[0]),
                "handle_world": world_pos(h),
                "twist": info["twist"],
                "pv_con": _uuid(info["pv_constraint"]) if info["pv_constraint"] else None,
                "pv_offset": (list(cmds.getAttr(info["pv_constraint"] + ".offset")[0])
                              if info["pv_constraint"] else None),
                "pv_value": (list(cmds.getAttr(h + ".poleVector")[0])
                             if cmds.objExists(h + ".poleVector") else None),
                "pv_target_world": {},
            }
            for t in info["pv_targets"]:
                data["pv_target_world"][_uuid(t)] = world_pos(t)

            messages.append(_disable_ik(h, data))

            _write_data(h, data)
            _mark(h, True)
            started.append(h)

            for note in info["notes"]:
                messages.append("[Info] {0}: {1}".format(_short(h), note))

    if started:
        messages.append(
            "[OK] Edit mode ON for {0} handle(s). Move / rotate the chain joints, then "
            "press the button again to keep the change.".format(len(started)))
    return messages


# =========================
# 폴 벡터 계산
# =========================

def desired_pole_vector_world(root, mid, end):
    """편집된 체인의 팔꿈치 방향(루트 기준 월드 벡터).

    루트->중간 벡터에서 체인 축(루트->끝) 성분을 뺀 **수직 성분**이다. 축과 평행해질 수
    없으므로 평면 정의가 안정적이고, 길이는 체인 길이에 맞춰 눈에 띄는 크기로 둔다.
    """
    axis = _sub(end, root)
    to_mid = _sub(mid, root)
    aa = _dot(axis, axis)
    if aa < 1e-12:
        return None
    proj = _scaled(axis, _dot(to_mid, axis) / aa)
    perp = _sub(to_mid, proj)
    plen = _length(perp)
    if plen < 1e-7:
        return None
    return _scaled(perp, _length(axis) / plen)


def _apply_pole_vector(handle, joints, data, pv_mode, messages):
    """편집된 체인에 맞는 폴 벡터를 넣는다. 성공하면 True."""
    solver = handle_solver(handle)
    if solver not in RP_LIKE_SOLVERS:
        return True

    root, mid, end = world_pos(joints[0]), world_pos(joints[1]), world_pos(joints[-1])
    desired_w = desired_pole_vector_world(root, mid, end)
    if desired_w is None:
        messages.append(
            "[Warning] {0}: the chain is straight, so there is no elbow direction to "
            "read - pole vector left as it was.".format(_short(handle)))
        return False

    # twist 는 솔버가 폴 벡터 평면 위에 **추가로** 얹는 회전이다. 값을 건드리지 않고
    # 결과만 맞추려면 원하는 벡터를 축 기준 -twist 만큼 미리 돌려 상쇄한다.
    twist = 0.0
    try:
        twist = cmds.getAttr(handle + ".twist")
    except Exception:
        pass
    if abs(twist) > 1e-9:
        desired_w = _rotate_about(desired_w, _sub(end, root), -twist)
        messages.append("[Info] {0}: compensated for twist {1:.4f}.".format(
            _short(handle), twist))

    con = pole_vector_constraint(handle)

    # --- 타깃 자체를 옮기는 모드 ---
    if con and pv_mode == PV_MODE_TARGET:
        targets = pole_vector_targets(con)
        if len(targets) != 1:
            messages.append(
                "[Warning] {0}: 'Move PV Target' needs exactly one pole vector target "
                "({1} found) - updated the constraint offset instead.".format(
                    _short(handle), len(targets)))
        else:
            tgt = _long(targets[0])
            dist = _length(_sub(world_pos(tgt), root)) or _length(desired_w)
            dvec = _scaled(desired_w, dist / _length(desired_w))
            want = [root[0] + dvec[0], root[1] + dvec[1], root[2] + dvec[2]]
            ok, how = _set_world_position(tgt, want)
            if ok:
                # 타깃을 옮겼으면 오프셋은 방해만 된다.
                cmds.setAttr(con + ".offset", 0, 0, 0)
                messages.append("[OK] {0}: moved pole vector target '{1}' onto the new "
                                "chain plane ({2}).".format(_short(handle), _short(tgt), how))
                return True
            messages.append(
                "[Warning] {0}: could not move '{1}' ({2}) - updated the constraint "
                "offset instead.".format(_short(handle), _short(tgt), how))

    desired_local = world_vector_to_parent(handle, desired_w)

    # --- 컨스트레인트 offset 갱신 (마야의 Update Offset 과 같은 발상) ---
    if con:
        _flush(handle)
        cur_pv = list(cmds.getAttr(handle + ".poleVector")[0])
        cur_off = list(cmds.getAttr(con + ".offset")[0])
        new_off = [desired_local[i] - (cur_pv[i] - cur_off[i]) for i in range(3)]
        cmds.setAttr(con + ".offset", *new_off)
        messages.append(
            "[OK] {0}: pole vector constraint '{1}' kept, offset updated to "
            "({2:.4f}, {3:.4f}, {4:.4f}).".format(
                _short(handle), _short(con), new_off[0], new_off[1], new_off[2]))
        return True

    # --- 컨스트레인트가 없으면 poleVector 를 직접 ---
    if all(_writable(handle + ".poleVector" + a) for a in "XYZ"):
        cmds.setAttr(handle + ".poleVector", *desired_local)
        messages.append("[OK] {0}: poleVector set to ({1:.4f}, {2:.4f}, {3:.4f}).".format(
            _short(handle), desired_local[0], desired_local[1], desired_local[2]))
        return True

    driver = pole_vector_driver(handle)
    messages.append(
        "[Warning] {0}: poleVector is driven by '{1}' and could not be updated - the "
        "chain may twist.".format(_short(handle), _short(driver) if driver else "?"))
    return False


# =========================
# 핸들 스냅
# =========================

def _point_constraint_of(node):
    cons = cmds.listConnections(node + ".translateX", d=False, s=True,
                                type="pointConstraint") or []
    return _long(cons[0]) if cons else None


def _set_world_position(node, want):
    """node 를 월드 좌표 want 로. 반환 (성공, 방법 설명)."""
    if _translate_settable(node):
        cmds.xform(node, ws=True, t=want)
        return True, "moved directly"

    # translate 가 구동되고 있으면 pointConstraint 의 offset 으로 밀어 준다.
    # 마야 2024 의 컨스트레인트 Update Offset 과 같은 발상이다.
    con = _point_constraint_of(node)
    if con and _writable(con + ".offsetX"):
        # 델타를 **핸들의 트랜스폼에서** 내면 안 된다. IK 가 꺼져 있는 동안 ikHandle 은
        # snapEnable(기본 ON) 때문에 이미 이펙터에 붙어 있어서, 읽히는 값이 컨스트레인트가
        # 밀어 넣을 값이 아니다 - 델타가 0 으로 나오고 아무것도 고쳐지지 않는다.
        # 컨스트레인트의 출력 플러그(constraintTranslate)를 직접 본다.
        pim = om.MMatrix(cmds.getAttr(node + ".parentInverseMatrix"))
        want_local = om.MPoint(want[0], want[1], want[2]) * pim
        out = cmds.getAttr(con + ".constraintTranslate")[0]
        old = list(cmds.getAttr(con + ".offset")[0])
        new = [old[0] + (want_local.x - out[0]),
               old[1] + (want_local.y - out[1]),
               old[2] + (want_local.z - out[2])]
        cmds.setAttr(con + ".offset", *new)
        _flush(node)
        return True, "via pointConstraint '{0}' offset".format(_short(con))

    driver = (cmds.listConnections(node + ".translateX", d=False, s=True) or [None])[0]
    return False, ("translate is driven by '{0}'".format(_short(driver))
                   if driver else "translate is locked")


def _snap_handle(handle, effector, snap_mode, messages):
    want = world_pos(effector)

    if snap_mode == SNAP_PARENT:
        parents = cmds.listRelatives(handle, p=True, f=True) or []
        if not parents:
            messages.append(
                "[Warning] {0}: 'Snap handle's parent' was asked for but the handle has "
                "no parent - moved the handle itself.".format(_short(handle)))
        else:
            parent = parents[0]
            delta = _sub(want, world_pos(handle))
            ppos = world_pos(parent)
            ok, how = _set_world_position(
                parent, [ppos[0] + delta[0], ppos[1] + delta[1], ppos[2] + delta[2]])
            if ok:
                messages.append("[OK] {0}: moved parent '{1}' so the handle lands on the "
                                "effector ({2}).".format(_short(handle), _short(parent), how))
                return True
            messages.append("[Warning] {0}: could not move parent '{1}' ({2}) - moved the "
                            "handle itself.".format(_short(handle), _short(parent), how))

    ok, how = _set_world_position(handle, want)
    if ok:
        messages.append("[OK] {0}: snapped to the effector ({1}).".format(_short(handle), how))
    else:
        messages.append("[Warning] {0}: could not be snapped to the effector - {1}. "
                        "The chain will pop.".format(_short(handle), how))
    return ok


# =========================
# 편집 종료 / 즉시 갱신
# =========================

def _update_one(handle, snap_mode, pv_mode, set_preferred, messages):
    """IK 가 꺼진 상태에서 호출한다. 편집된 포즈를 기준으로 핸들/폴 벡터를 맞춘다.

    반환 : 편집된 포즈 (측정용)
    """
    joints = chain_joints(handle)
    edited = [(world_pos(j), world_rot(j)) for j in joints]

    effector = end_effector(handle)
    if effector:
        _snap_handle(handle, effector, snap_mode, messages)
    else:
        messages.append("[Warning] {0}: no end effector - cannot snap the handle.".format(
            _short(handle)))

    _apply_pole_vector(handle, joints, {}, pv_mode, messages)

    if set_preferred:
        for j in joints:
            try:
                cmds.joint(j, e=True, setPreferredAngles=True)
            except Exception:
                pass
        messages.append("[Info] {0}: preferred angles set from the edited pose.".format(
            _short(handle)))

    return joints, edited


def _measure(handle, joints, edited, messages):
    """IK 를 되켠 뒤 편집한 포즈와 얼마나 다른지 실측해 보고한다."""
    _flush(handle)
    for j in joints:
        _flush(j)

    dev_t = 0.0
    dev_r = 0.0
    for i, j in enumerate(joints):
        if not cmds.objExists(j):
            continue
        wt, wr = world_pos(j), world_rot(j)
        dev_t = max(dev_t, max(abs(a - b) for a, b in zip(wt, edited[i][0])))
        dev_r = max(dev_r, max(abs(a - b) for a, b in zip(wr, edited[i][1])))

    messages.append(
        "[Result] {0}: max deviation from the edited pose - position {1:.6f}, "
        "rotation {2:.6f} deg.".format(_short(handle), dev_t, dev_r))
    return dev_t, dev_r


def end_edit(handles, snap_mode=SNAP_HANDLE, pv_mode=PV_MODE_OFFSET, set_preferred=True):
    """편집을 확정한다. 핸들과 폴 벡터를 편집된 체인에 맞추고 IK 를 되켠다."""
    messages = []
    results = []

    with undo_chunk():
        for h in handles:
            if not cmds.objExists(h):
                messages.append("[Warning] '{0}' no longer exists.".format(_short(h)))
                continue
            if not is_editing(h):
                messages.append("[Warning] '{0}' is not in edit mode.".format(_short(h)))
                continue

            data = _read_data(h)

            joints, edited = _update_one(h, snap_mode, pv_mode, set_preferred, messages)

            _restore_ik(h, data)
            dev_t, dev_r = _measure(h, joints, edited, messages)

            _clear_state(h)
            results.append((h, dev_t, dev_r))

    return results, messages


def update_now(handles, snap_mode=SNAP_HANDLE, pv_mode=PV_MODE_OFFSET, set_preferred=True):
    """편집 세션 없이 지금 상태로 한 번 맞춘다 (마야 컨스트레인트의 Update 버튼에 대응).

    이미 IK 를 끄고 체인을 고쳐 둔 상황에서 쓴다. 편집 상태 표시는 만들지도 지우지도 않는다.
    """
    messages = []
    results = []

    with undo_chunk():
        for h in handles:
            if not cmds.objExists(h):
                messages.append("[Warning] '{0}' no longer exists.".format(_short(h)))
                continue

            info = inspect(h)
            if info["blockers"]:
                for b in info["blockers"]:
                    messages.append("[Warning] {0}: {1}".format(_short(h), b))
                continue

            temp = {}
            note = _disable_ik(h, temp)
            messages.append("[Info] " + note)

            joints, edited = _update_one(h, snap_mode, pv_mode, set_preferred, messages)

            _restore_ik(h, temp)
            dev_t, dev_r = _measure(h, joints, edited, messages)
            results.append((h, dev_t, dev_r))

    return results, messages


# =========================
# 취소
# =========================

def cancel_edit(handles):
    """편집 시작 시점으로 되돌린다."""
    messages = []

    with undo_chunk():
        for h in handles:
            if not cmds.objExists(h):
                continue
            if not is_editing(h):
                messages.append("[Warning] '{0}' is not in edit mode.".format(_short(h)))
                continue

            data = _read_data(h)

            for rec in data.get("joints", []):
                j = _from_uuid(rec.get("uuid"))
                if not j:
                    continue
                for attr, key in (("translate", "t"), ("rotate", "r"),
                                  ("scale", "s"), ("jointOrient", "jo"),
                                  ("preferredAngle", "pa")):
                    values = rec.get(key)
                    if not values:
                        continue
                    plug = "{0}.{1}".format(j, attr)
                    if _writable(plug):
                        cmds.setAttr(plug, *values)

            if _translate_settable(h) and data.get("handle_t"):
                cmds.setAttr(h + ".translate", *data["handle_t"])
            if data.get("handle_r") and _writable(h + ".rotateX"):
                cmds.setAttr(h + ".rotate", *data["handle_r"])

            con = _from_uuid(data.get("pv_con")) if data.get("pv_con") else None
            if con and data.get("pv_offset"):
                cmds.setAttr(con + ".offset", *data["pv_offset"])

            for uuid, pos in (data.get("pv_target_world") or {}).items():
                tgt = _from_uuid(uuid)
                if tgt and _translate_settable(tgt):
                    cmds.xform(tgt, ws=True, t=pos)

            if not con and data.get("pv_value") and cmds.objExists(h + ".poleVector"):
                if all(_writable(h + ".poleVector" + a) for a in "XYZ"):
                    cmds.setAttr(h + ".poleVector", *data["pv_value"])

            _restore_ik(h, data)
            _clear_state(h)
            messages.append("[OK] {0}: edit cancelled, chain restored.".format(_short(h)))

    return messages
