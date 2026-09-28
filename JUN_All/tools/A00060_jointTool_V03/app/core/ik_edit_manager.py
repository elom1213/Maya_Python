# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-28
# A00060_jointTool_V03 - 이미 설치된 ikHandle 을 그대로 둔 채 본 체인을 수정한다.
#
# 마야 2024 의 컨스트레인트에는 Update(Update Offset) 버튼이 있어서, 드리븐을 손으로
# 옮긴 뒤 그 자리를 새 오프셋으로 굳힐 수 있다(실체는 `parentConstraint -e -maintainOffset`).
# **ikHandle 에는 그런 버튼이 없다** - AEikHandleTemplate.mel 을 봐도 없고, 명령에도 없다.
# 이 모듈이 그 자리를 메운다.
#
# ── v03.13 : offset 을 지키는 모드 (PV_MODE_KEEP, 기본) ─────────────────────
#
# 아래 두 옛 모드는 "체인이 먼저, 폴 벡터가 따라간다" 였다(offset 을 역산). 새 모드는
# 반대로 **"폴 타깃이 먼저, 체인이 따라간다"** — offset 은 한 글자도 안 바꾼다.
#
#   1. 폴 평면 = 체인 축(루트->끝) + poleVector(월드, twist 만큼 더 돌린 것)
#   2. 중간 조인트 전부를 그 평면에 **수직 투영**. 폴 반대편에 떨어지면 축에 대해
#      거울 반사해 폴 쪽으로 (그대로 두면 솔버가 체인을 뒤집는다 - 실측 편차 6.39)
#   3. 뼈 축 재정렬: X -> 다음 조인트, up = Y/Z 중 지금 월드 +Y 를 더 향한 축을
#      **평면 법선** 쪽으로 (투영 뒤 체인이 한 평면이라 한 축으로만 굽는다)
#      회전이 parentConstraint 로 구동되면 그 타깃 offset 을 다시 굳힌다
#   4. 끝 조인트 · 체인 밖 자식들은 월드 자리를 지킨다
#   5. restTranslate <- constraintTranslate (weight 1 이면 출력엔 영향 없다 - 정리용)
#
# 2조인트 체인(중간 조인트 없음)은 X 만 뼈에 맞추고, 뼈 둘레 회전은 **솔버에게 받는다**
# (_settle_twist). 이런 체인은 어느 축이 폴을 볼지 솔버가 정해서 up 규칙과 90 도 어긋났다.
# 여러 핸들은 부모 체인부터 맞추고, IK 는 전부 맞춘 뒤 한꺼번에 켠다.
# 실측(케이지 Cage_v002_0060): 팔 · 다리 · Drv 체인 16개 + Match 가 찾은 2개 전부 offset 불변, 편차 0.
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

# ── 레퍼런스에서 온 핸들 ────────────────────────────────────────────────────
#
# 케이지 파일을 **레퍼런스로 불러와** 그 안의 조인트를 고치는 것이 A00130_ControlRig_V02
# 의 작업 방식이다. 실측 결과 레퍼런스 노드에도 `setAttr` · `addAttr` · `deleteAttr` 이
# 전부 먹고(편집은 reference edit 으로 저장돼 씬을 다시 열어도 남는다), 이 모듈이 하는
# 일 중 레퍼런스가 막는 것은 없다 - 단 하나, **솔버 이름 비교**만 빼고. 위 handle_solver()
# 참고. (`rename` 은 막히지만 이 모듈은 이름을 바꾸지 않는다.)

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
PV_MODE_KEEP = "keep"        # offset 을 지키고 체인을 폴 평면에 맞춘다 (기본, v03.13)
PV_MODE_OFFSET = "offset"    # 컨스트레인트 offset 을 갱신
PV_MODE_TARGET = "target"    # 폴 벡터 타깃(로케이터) 자체를 새 평면으로 옮긴다

# up 축 판정: 두 축 모두 월드 +Y 와 이만큼도 가깝지 않으면(뼈가 거의 수직) 동률로 본다
UP_AMBIGUOUS_DOT = 0.5

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
    """핸들이 쓰는 솔버의 **타입 이름** (`ikRPsolver` / `ikSCsolver` / ...).

    `ikHandle -q -solver` 가 주는 것은 솔버의 **노드 이름**이다. 그래서 **레퍼런스에서 온
    핸들이면 `CAGE:ikRPsolver` 처럼 네임스페이스가 붙어 온다**(실측 - 솔버 노드까지 함께
    레퍼런스된다). 그 이름을 `("ikRPsolver", ...)` 과 그대로 비교하면 **에러 없이 어긋나서**
    폴 벡터 갱신이 통째로 건너뛰어지고, 체인이 옛 평면으로 비틀린 채 확정된다
    (실측 편차 2.03 / 45.8도).

    그래서 이름이 아니라 **노드 타입**으로 판정한다 - 네임스페이스에도, 솔버 노드를
    리네임한 씬에도 흔들리지 않는다.
    """
    try:
        node = cmds.ikHandle(handle, q=True, solver=True)
    except Exception:
        return ""
    if not node:
        return ""
    try:
        if cmds.objExists(node):
            return cmds.nodeType(node)
    except Exception:
        pass
    # 노드를 못 찾으면 최소한 네임스페이스만이라도 뗀다
    return node.split(":")[-1]


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
                "Pole vector constraint '{0}' will be kept (Keep offset leaves its offset "
                "as it is; the other modes update the offset or move the target)."
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
# offset 유지 모드 (PV_MODE_KEEP) - 체인을 폴 평면에 맞춘다
# =========================

def _mvec(v):
    return om.MVector(v[0], v[1], v[2])


def _world_matrix(node):
    return om.MMatrix(cmds.getAttr(node + ".worldMatrix[0]"))


def _row(m, i):
    return om.MVector(m.getElement(i, 0), m.getElement(i, 1), m.getElement(i, 2))


def _pure_rotation(m):
    """행을 정규화(스케일 제거)하고 평행이동을 뺀 3x3. 조인트 스케일이 스트레치로 1 이 아니어도 된다."""
    rows = []
    for i in range(3):
        v = _row(m, i).normal()
        rows += [v.x, v.y, v.z, 0.0]
    return om.MMatrix(rows + [0.0, 0.0, 0.0, 1.0])


def _frame(x_dir, up_index, up_dir, origin=None):
    """X = x_dir, up_index(1=Y, 2=Z) 축 = up_dir 의 X 수직 성분인 오른손 좌표계."""
    x = x_dir.normal()
    u = (up_dir - x * (up_dir * x)).normal()
    if up_index == 1:
        y, z = u, (x ^ u).normal()
    else:
        z, y = u, (u ^ x).normal()
    o = origin or om.MVector()
    return om.MMatrix([x.x, x.y, x.z, 0.0, y.x, y.y, y.z, 0.0,
                       z.x, z.y, z.z, 0.0, o.x, o.y, o.z, 1.0])


def pole_vector_world(handle):
    """핸들의 poleVector(부모 공간) 를 월드 벡터로. 컨스트레인트 출력이든 직접 값이든."""
    pv = om.MVector(*cmds.getAttr(handle + ".poleVector")[0])
    return pv * _rotation_only(cmds.getAttr(handle + ".parentMatrix[0]"))


def pole_plane(handle, joints):
    """`(axis_unit, side_unit, normal_unit)` 또는 None.

    side = 폴 쪽을 가리키는 평면 안의 방향(축에 수직), normal = axis x side.
    twist 는 솔버가 평면을 축 둘레로 **더** 돌리는 각이라 같은 만큼 돌린다.
    """
    root, end = _mvec(world_pos(joints[0])), _mvec(world_pos(joints[-1]))
    axis = end - root
    if axis.length() < 1e-9:
        return None
    pv = pole_vector_world(handle)
    twist = cmds.getAttr(handle + ".twist") if cmds.objExists(handle + ".twist") else 0.0
    if abs(twist) > 1e-9:
        pv = _mvec(_rotate_about([pv.x, pv.y, pv.z], [axis.x, axis.y, axis.z], twist))
    a = axis.normal()
    side = pv - a * (pv * a)
    if side.length() < 1e-9:
        return None
    side = side.normal()
    return a, side, (a ^ side).normal()


def pick_up_axis(joint, normal):
    """재정렬 때 쓸 up 축과 그 방향. `(index 1=Y/2=Z, 방향 벡터, 설명)`.

    규칙(사용자 지정 2026-09-28): Y · Z 중 **지금 월드 +Y 를 더 향한 축**을 up 으로,
    그 축을 **폴 평면 법선 쪽**으로(법선 두 부호 중 지금 축에 가까운 쪽 - 최소 회전).
    다리처럼 뼈가 거의 수직이면 Y · Z 둘 다 수평이라 +Y 판정이 동률이 된다 - 그때는
    지금 법선에 더 가까운 축을 쓴다(리그의 굽힘 축을 그대로 지킨다).
    """
    m = _world_matrix(joint)
    y, z = _row(m, 1).normal(), _row(m, 2).normal()
    up = om.MVector(0.0, 1.0, 0.0)
    dy, dz = y * up, z * up
    if max(dy, dz) < UP_AMBIGUOUS_DOT:
        index = 1 if abs(y * normal) >= abs(z * normal) else 2
        why = "bone near vertical - axis closest to the pole plane normal"
    else:
        index = 1 if dy >= dz else 2
        why = "axis most toward world +Y"
    cur = y if index == 1 else z
    n = normal if cur * normal >= 0.0 else -normal
    return index, n, why


def _set_local_translate(joint, world_point):
    """쓸 수 있는 축만 쓴다. 쓰지 못한(잠김/구동) 축 이름 목록을 돌려준다.

    케이지의 Drv 체인은 끝 조인트 `tx` 를 거리 노드가 구동한다(`multiplyDivide80.ox ->
    CH_l_WristDrv_xx_ikjnt.tx`) - 뼈 길이는 리그가 정한다. 그 축은 리그에 맡긴다.
    """
    pim = om.MMatrix(cmds.getAttr(joint + ".parentInverseMatrix[0]"))
    lp = om.MPoint(world_point) * pim
    blocked = []
    for axis, value in zip("XYZ", (lp.x, lp.y, lp.z)):
        plug = "{0}.translate{1}".format(joint, axis)
        if _writable(plug):
            cmds.setAttr(plug, value)
        else:
            blocked.append("t" + axis.lower())
    return blocked


def _euler_degrees(matrix, rotate_order=0):
    e = om.MEulerRotation.decompose(_pure_rotation(matrix), rotate_order)
    return [math.degrees(e.x), math.degrees(e.y), math.degrees(e.z)]


def _orient_joint_world(joint, want_rot):
    """rotate 는 그대로 두고 jointOrient 를 풀어 월드 회전 = want_rot.

    joint world = rotate x jointOrient x parent  ->  jo = R^-1 x want x parent^-1
    """
    r = cmds.getAttr(joint + ".rotate")[0]
    ro = cmds.getAttr(joint + ".rotateOrder")
    R = om.MEulerRotation([math.radians(v) for v in r], ro).asMatrix()
    parent = _pure_rotation(om.MMatrix(cmds.getAttr(joint + ".parentMatrix[0]")))
    jo = R.inverse() * want_rot * parent.inverse()
    cmds.setAttr(joint + ".jointOrient", *_euler_degrees(jo))


def _rotate_driver(joint):
    cons = cmds.listConnections(joint + ".rotateX", s=True, d=False) or []
    return _long(cons[0]) if cons else None


def _refit_parent_constraint(con, want_world):
    """parentConstraint 의 타깃 offset 들을 드리븐 월드 = want_world 가 되게 다시 굳힌다.

    `parentConstraint -e -maintainOffset` 은 드리븐의 **지금** 자리를 굳히는데, 조인트
    회전은 컨스트레인트가 되쓰고 있어 "지금" 이 원하는 자리가 아니다. 그래서 직접 푼다.
    offset 회전은 타깃이 아니라 **드리븐의 rotate order**(constraintRotateOrder)로 풀어야
    한다 - targetRotateOrder 로 풀면 0.03 ~ 1.4 도 어긋난다(실측).
    """
    targets = cmds.parentConstraint(con, q=True, targetList=True) or []
    ro = cmds.getAttr(con + ".constraintRotateOrder")
    for i, t in enumerate(targets):
        off = want_world * _world_matrix(t).inverse()
        tr = om.MTransformationMatrix(off).translation(om.MSpace.kTransform)
        cmds.setAttr("{0}.target[{1}].targetOffsetTranslate".format(con, i), tr.x, tr.y, tr.z)
        cmds.setAttr("{0}.target[{1}].targetOffsetRotate".format(con, i),
                     *_euler_degrees(off, ro))


def _chain_children(joints):
    """체인 조인트(끝 제외)의 자식 중 체인 밖 트랜스폼. 재정렬해도 월드 자리를 지킬 것들."""
    chain = set(joints)
    out = []
    for j in joints[:-1]:
        for c in (cmds.listRelatives(j, c=True, f=True, type="transform") or []):
            if c in chain:
                continue
            if cmds.objectType(c, isAType="ikEffector") or cmds.objectType(c, isAType="constraint"):
                continue
            out.append((c, world_pos(c), world_rot(c)))
    return out


def _x_sign(joint, child):
    """지금 X 가 자식 쪽이면 +1, 반대쪽이면 -1.

    케이지의 **오른팔 체인은 -X 가 뼈를 따라간다**(자식 translateX = -22.906, 미러 규약).
    "X 를 다음 조인트로" 를 +X 로 강제하면 오른쪽 규약이 조용히 뒤집힌다 - 부호는 지킨다.
    """
    x = _row(_world_matrix(joint), 0)
    bone = _mvec(world_pos(child)) - _mvec(world_pos(joint))
    return -1.0 if x * bone < 0.0 else 1.0


def _set_joint_world_rotation(joint, want, name, messages):
    """조인트 월드 회전 = want(4x4, 평행이동 = 조인트 자리). 회전이 구동되면 그 구동을 고친다."""
    driver = _rotate_driver(joint)
    if driver is None:
        _orient_joint_world(joint, _pure_rotation(want))
        return True
    if cmds.nodeType(driver) == "parentConstraint":
        _refit_parent_constraint(driver, want)
        messages.append("[Info] {0}: '{1}' is rotated by '{2}' - its target offsets were "
                        "refitted.".format(name, _short(joint), _short(driver)))
        return True
    messages.append("[Warning] {0}: '{1}' rotation is driven by '{2}' - not re-oriented."
                    .format(name, _short(joint), _short(driver)))
    return False


def _restore_children(kids, name, messages):
    for c, t, r in kids:
        try:
            cmds.xform(c, ws=True, t=t)
            cmds.xform(c, ws=True, ro=r)
        except Exception:
            pass
        # xform 은 잠긴/구동 채널을 조용히 건너뛴다 - 되읽어 확인한다
        if max(abs(x - y) for x, y in zip(world_pos(c), t)) > 1e-4:
            messages.append("[Warning] {0}: child '{1}' could not be kept in place (its "
                            "channels are locked or driven).".format(name, _short(c)))


def _settle_twist(handle, joints, kids, name, messages):
    """2조인트 체인: 뼈 둘레 회전은 **솔버가 정한다** - 그 답을 받아 rest 로 굳힌다.

    중간 조인트가 없는 RP 체인은 "어느 축이 폴을 보는가" 를 솔버가 스스로 정한다
    (실측 기본 -Y, twist 로만 바뀐다 - A00130 ik_axis). up 축 규칙으로 정하면 ankle · foot
    에서 90 도 어긋났다(실측). 그래서 X 를 뼈에 맞춘 뒤 IK 를 잠깐 켜서 솔버의 회전을 읽고,
    끄고 그 회전을 jointOrient 로 넣는다 - 폴이 먼저, 체인이 따라간다.
    """
    plug = handle + ".ikBlend"
    if not _writable(plug):
        messages.append("[Warning] {0}: ikBlend is driven - could not read the solver's twist, "
                        "the root may turn about the bone when IK comes back.".format(name))
        return False
    effector = end_effector(handle)
    if effector:
        _set_world_position(handle, world_pos(effector))
    end_rot = _pure_rotation(_world_matrix(joints[-1]))
    # 마지막에 IK 를 켤 때와 **같은 조건**으로 읽는다 - 솔버는 preferred angle 포즈로 평면을
    # 잡으므로, 안 맞추면 Match 가 남긴 옛 pa 로 풀어 최종 결과와 90 도 달랐다(실측 Wrist_xx_hdl).
    for j in joints:
        try:
            cmds.joint(j, e=True, setPreferredAngles=True)
        except Exception:
            pass
    old = cmds.getAttr(plug)
    cmds.setAttr(plug, 1.0)
    for n in [handle] + joints:
        _flush(n)
    solved = _world_matrix(joints[0])
    cmds.setAttr(plug, old)
    _flush(joints[0])
    _set_joint_world_rotation(joints[0], solved, name, messages)
    _orient_joint_world(joints[-1], end_rot)
    _restore_children(kids, name, messages)
    return True


def fit_to_pole_plane(handle, messages, reorient=True):
    """PV_MODE_KEEP 의 본체. offset 은 건드리지 않고 체인을 폴 평면에 맞춘다.

    IK 가 꺼진 상태에서 부른다. 반환: `{"moved": [..], "mirrored": n, "lengths": [..]}`
    또는 맞출 수 없으면 None(메시지에 이유).
    """
    name = _short(handle)
    solver = handle_solver(handle)
    joints = chain_joints(handle)
    if solver not in RP_LIKE_SOLVERS or len(joints) < 2:
        return None

    plane = pole_plane(handle, joints)
    if plane is None:
        messages.append("[Warning] {0}: the pole vector lies on the chain axis - no pole plane, "
                        "chain left as it is.".format(name))
        return None
    a, side, n = plane

    for j in joints[1:-1]:
        if not _writable(j + ".translate"):
            messages.append("[Warning] {0}: '{1}' translate is locked or driven - cannot put it "
                            "on the pole plane, chain left as it is.".format(name, _short(j)))
            return None

    p = [_mvec(world_pos(j)) for j in joints]
    new_p = [p[0]]
    moved, mirrored = [], 0
    for i in range(1, len(p) - 1):
        d = p[i] - p[0]
        q = d - n * (d * n)                 # 평면에 수직 투영
        along = a * (q * a)
        perp = q - along
        if perp.length() < 1e-7:
            messages.append("[Warning] {0}: '{1}' lies on the chain axis - the chain is straight "
                            "and cannot bend toward the pole.".format(name, _short(joints[i])))
        elif perp * side < 0.0:
            perp = -perp                    # 폴 반대편 -> 축에 대해 거울 반사
            mirrored += 1
            messages.append("[Info] {0}: '{1}' was on the far side of the pole - mirrored to the "
                            "pole side.".format(name, _short(joints[i])))
        new_p.append(p[0] + along + perp)
        moved.append((new_p[-1] - p[i]).length())
    new_p.append(p[-1])

    end_rot = _pure_rotation(_world_matrix(joints[-1]))
    kids = _chain_children(joints)

    # up 축 · X 부호는 옮기기 **전** 방향으로 정한다 (지금 월드 +Y 를 더 향한 축, 지금 규약)
    ups = [pick_up_axis(j, n) for j in joints[:-1]] if reorient else []
    signs = [_x_sign(joints[i], joints[i + 1]) for i in range(len(joints) - 1)] if reorient else []

    fit = {"handle": handle, "name": name, "joints": joints, "new_p": new_p, "ups": ups,
           "signs": signs, "end_rot": end_rot, "kids": kids, "reorient": reorient,
           "moved": moved, "mirrored": mirrored,
           "lengths": [(new_p[i + 1] - new_p[i]).length() for i in range(len(new_p) - 1)]}
    settled = place_fit(fit, messages)

    if settled:
        messages.append("[Info] {0}: X aimed at the next joint, the turn about the bone taken "
                        "from the solver (two-joint chain).".format(name))
    elif reorient:
        axis_note = ", ".join("{0} {1}X / up {2}".format(_short(joints[i]),
                                                         "-" if signs[i] < 0 else "+",
                                                         "YZ"[ups[i][0] - 1])
                              for i in range(len(ups)))
        messages.append("[Info] {0}: re-oriented X to the next joint, up axis toward the pole "
                        "plane normal ({1}).".format(name, axis_note))
    if moved:
        messages.append("[OK] {0}: mid joint(s) fitted to the pole plane - moved {1}.".format(
            name, ", ".join("{0:.4f}".format(m) for m in moved)))
    return fit


def place_fit(fit, messages):
    """fit_to_pole_plane 이 계산한 **월드 목표**대로 체인을 놓는다. 2조인트면 twist 를 굳혔나.

    계산과 놓기를 나눈 까닭: 호출하는 쪽이 IK 를 켜기 전에 리그 값을 바꿀 수 있다 -
    A00130 은 바뀐 뼈 길이를 옵션 컨트롤러(스트레치 휴지 길이)에 쓰는데, 그러면 스트레치가
    풀려 조인트 스케일이 바뀌고 체인이 줄어든다(실측: 1.206 -> 1, wrist 6.26 이탈).
    같은 월드 목표로 **한 번 더 놓으면** 그 변화가 지워진다. 같은 목표로 다시 놓는 것은
    아무것도 바꾸지 않는다(멱등).
    """
    handle, name, joints = fit["handle"], fit["name"], fit["joints"]
    new_p, ups, signs = fit["new_p"], fit["ups"], fit["signs"]

    for i in range(len(joints) - 1):
        j = joints[i]
        if i > 0:
            _set_local_translate(j, new_p[i])
        if not fit["reorient"]:
            continue
        index, up_dir, _why = ups[i]
        bone = (new_p[i + 1] - new_p[i]) * signs[i]
        _set_joint_world_rotation(j, _frame(bone, index, up_dir, origin=new_p[i]), name, messages)

    # 끝 조인트: 부모가 돌아도 월드 자리 · 회전을 지킨다 (2조인트 체인도 - 루트가 돌면 옮겨진다)
    blocked = _set_local_translate(joints[-1], new_p[-1])
    if blocked:
        messages.append("[Info] {0}: end joint '{1}' {2} is driven by the rig - left to it."
                        .format(name, _short(joints[-1]), "/".join(blocked)))
    _orient_joint_world(joints[-1], fit["end_rot"])
    _restore_children(fit["kids"], name, messages)

    settled = False
    if fit["reorient"] and len(joints) == 2:
        settled = _settle_twist(handle, joints, fit["kids"], name, messages)

    con = pole_vector_constraint(handle)
    if con and _writable(con + ".restTranslate"):
        cmds.setAttr(con + ".restTranslate", *cmds.getAttr(con + ".constraintTranslate")[0])
    return settled


def _chain_depth(handle):
    joints = chain_joints(handle)
    return len(joints[0].split("|")) if joints else 0


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
    edited = [(world_pos(j), world_rot(j), _world_quat(j)) for j in joints]

    effector = end_effector(handle)
    if effector:
        _snap_handle(handle, effector, snap_mode, messages)
    else:
        messages.append("[Warning] {0}: no end effector - cannot snap the handle.".format(
            _short(handle)))

    if pv_mode != PV_MODE_KEEP:
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


def _world_quat(node):
    return om.MTransformationMatrix(_pure_rotation(_world_matrix(node))).rotation(asQuaternion=True)


def _angle_deg(q1, q2):
    """두 방향 사이의 실제 각도(0~180). 오일러 세 값을 따로 빼면 같은 방향도
    (180, a, 180) / (0, 180-a, 0) 처럼 표기만 달라 90 · 270 · 356 도로 나온다(실측, v03.13)."""
    d = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w)
    return math.degrees(2.0 * math.acos(min(1.0, d)))


def _measure(handle, joints, edited, messages):
    """IK 를 되켠 뒤 편집한 포즈와 얼마나 다른지 실측해 보고한다.

    회전은 두 방향 사이의 **각도**로 잰다(v03.13 - 전에는 오일러 성분 차라 표기 차이가 섞였다).
    """
    _flush(handle)
    for j in joints:
        _flush(j)

    dev_t = 0.0
    dev_r = 0.0
    for i, j in enumerate(joints):
        if not cmds.objExists(j):
            continue
        wt = world_pos(j)
        dev_t = max(dev_t, max(abs(a - b) for a, b in zip(wt, edited[i][0])))
        if len(edited[i]) > 2:
            dev_r = max(dev_r, _angle_deg(_world_quat(j), edited[i][2]))
        else:
            dev_r = max(dev_r, max(abs(a - b) for a, b in zip(world_rot(j), edited[i][1])))

    messages.append(
        "[Result] {0}: max deviation from the edited pose - position {1:.6f}, "
        "rotation {2:.6f} deg.".format(_short(handle), dev_t, dev_r))
    return dev_t, dev_r


def _pv_offsets(handles):
    out = {}
    for h in handles:
        con = pole_vector_constraint(h) if cmds.objExists(h) else None
        if con:
            out[h] = list(cmds.getAttr(con + ".offset")[0])
    return out


def _fit_all(handles, reorient, messages, fits_out, after_fit=None):
    """PV_MODE_KEEP: 스냅 전에 체인을 전부 폴 평면에 맞춘다.

    **부모 체인 먼저.** Drv 체인처럼 다른 체인 안에 든 체인은 바깥 체인을 맞춘 뒤(그 자식으로서
    월드 자리가 지켜진 뒤) 맞춰야 한다. 또 바깥 체인의 중간 조인트가 옮겨지면 그것을 따라가는
    폴 타깃(예: elbow 타깃)도 옮겨지므로, 안쪽 체인의 폴 평면은 그 뒤에 읽어야 맞다.

    `after_fit(fits)` 를 주면 맞춘 **직후, IK 를 켜기 전에** 부른다(돌려준 메시지는 로그로).
    그 안에서 리그 값(스트레치 길이 등)이 바뀌어 체인이 흔들릴 수 있으므로, 부른 뒤 같은
    월드 목표로 **다시 놓는다**(place_fit).
    """
    fits = {}
    order = sorted(handles, key=_chain_depth)
    for h in order:
        fit = fit_to_pole_plane(h, messages, reorient=reorient)
        if fit is not None:
            fits[h] = fit
    if after_fit is not None and fits:
        messages.extend(after_fit(fits) or [])
        again = []
        for h in order:
            if h in fits:
                place_fit(fits[h], again)
        messages.extend(m for m in again if "[Warning]" in m and m not in messages)
    if fits_out is not None:
        fits_out.update(fits)


def _report_offsets(before, messages):
    for h, old in before.items():
        con = pole_vector_constraint(h)
        new = list(cmds.getAttr(con + ".offset")[0]) if con else old
        if max(abs(x - y) for x, y in zip(old, new)) < 1e-9:
            messages.append("[OK] {0}: pole vector offset kept ({1:.4f}, {2:.4f}, {3:.4f}).".format(
                _short(h), old[0], old[1], old[2]))
        else:
            messages.append("[Warning] {0}: pole vector offset changed ({1} -> {2}).".format(
                _short(h), old, new))


def end_edit(handles, snap_mode=SNAP_HANDLE, pv_mode=PV_MODE_KEEP, set_preferred=True,
             reorient=True, fits_out=None, after_fit=None):
    """편집을 확정한다. 핸들과 폴 벡터를 편집된 체인에 맞추고 IK 를 되켠다.

    `pv_mode=PV_MODE_KEEP`(기본)이면 폴 벡터는 그대로 두고 체인을 폴 평면에 맞춘다.
    `fits_out` 에 dict 를 넘기면 핸들별 맞춤 결과(옮긴 거리 · 새 뼈 길이)를 채워 준다.
    `after_fit(fits)` 는 맞춘 뒤 IK 를 켜기 전에 불린다(_fit_all).
    """
    messages = []
    results = []

    with undo_chunk():
        live = []
        for h in handles:
            if not cmds.objExists(h):
                messages.append("[Warning] '{0}' no longer exists.".format(_short(h)))
                continue
            if not is_editing(h):
                messages.append("[Warning] '{0}' is not in edit mode.".format(_short(h)))
                continue
            live.append(h)

        if pv_mode != PV_MODE_KEEP:
            # 옛 두 모드 - v03.12 까지와 같은 순서 그대로
            for h in live:
                data = _read_data(h)
                joints, edited = _update_one(h, snap_mode, pv_mode, set_preferred, messages)
                _restore_ik(h, data)
                dev_t, dev_r = _measure(h, joints, edited, messages)
                _clear_state(h)
                results.append((h, dev_t, dev_r))
            return results, messages

        offsets = _pv_offsets(live)
        _fit_all(live, reorient, messages, fits_out, after_fit)

        # 스냅 · preferred angle 은 **전부** 끝낸 뒤 IK 를 켠다 - 하나씩 켜면 먼저 켠
        # 바깥 체인의 솔버가 아직 안 끝난 안쪽 체인의 부모를 움직인다.
        pending = []
        for h in live:
            data = _read_data(h)
            joints, edited = _update_one(h, snap_mode, pv_mode, set_preferred, messages)
            pending.append((h, data, joints, edited))

        for h, data, _joints, _edited in pending:
            _restore_ik(h, data)
        for h, _data, joints, edited in pending:
            dev_t, dev_r = _measure(h, joints, edited, messages)
            _clear_state(h)
            results.append((h, dev_t, dev_r))

        _report_offsets(offsets, messages)

    return results, messages


def update_now(handles, snap_mode=SNAP_HANDLE, pv_mode=PV_MODE_KEEP, set_preferred=True,
               reorient=True, fits_out=None, after_fit=None):
    """편집 세션 없이 지금 상태로 한 번 맞춘다 (마야 컨스트레인트의 Update 버튼에 대응).

    이미 IK 를 끄고 체인을 고쳐 둔 상황에서 쓴다. 편집 상태 표시는 만들지도 지우지도 않는다.
    """
    messages = []
    results = []

    with undo_chunk():
        live = []
        for h in handles:
            if not cmds.objExists(h):
                messages.append("[Warning] '{0}' no longer exists.".format(_short(h)))
                continue

            info = inspect(h)
            if info["blockers"]:
                for b in info["blockers"]:
                    messages.append("[Warning] {0}: {1}".format(_short(h), b))
                continue
            live.append(h)

        if pv_mode != PV_MODE_KEEP:
            for h in live:
                temp = {}
                note = _disable_ik(h, temp)
                messages.append("[Info] " + note)

                joints, edited = _update_one(h, snap_mode, pv_mode, set_preferred, messages)

                _restore_ik(h, temp)
                dev_t, dev_r = _measure(h, joints, edited, messages)
                results.append((h, dev_t, dev_r))
            return results, messages

        # 새 모드: end_edit 과 같은 순서 (전부 끄고 -> 부모부터 맞추고 -> 스냅 -> 전부 켠다)
        temps = {}
        for h in live:
            temps[h] = {}
            messages.append("[Info] " + _disable_ik(h, temps[h]))
        offsets = _pv_offsets(live)
        _fit_all(live, reorient, messages, fits_out, after_fit)
        pending = []
        for h in live:
            joints, edited = _update_one(h, snap_mode, pv_mode, set_preferred, messages)
            pending.append((h, joints, edited))
        for h in live:
            _restore_ik(h, temps[h])
        for h, joints, edited in pending:
            dev_t, dev_r = _measure(h, joints, edited, messages)
            results.append((h, dev_t, dev_r))
        _report_offsets(offsets, messages)

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
