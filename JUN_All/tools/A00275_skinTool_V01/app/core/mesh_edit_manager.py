# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
# A00275_skinTool_V01 - Edit Mesh (메시 편집 모드) 로직 (maya.cmds / maya.api, UI 비의존)
#
# "바인드된 메시를 웨이트 수치 하나 건드리지 않고 형상·위치만 고친다."
#
#   Edit ON  -> skinCluster envelope 를 0 으로 내려 **rest 셰이프**를 보여 주고,
#               스킨이 잠가 둔 메시 트랜스폼 t/r/s 를 풀어 준다.
#               → 버텍스/엣지/페이스를 옮기든 메시 자체를 옮기든 화면과 1:1 로 움직인다.
#   Edit OFF -> 그 편집 결과를 **새 rest 상태**로 굳히고 envelope·잠금을 되돌린다.
#
# weightList 는 어느 단계에서도 읽지도 쓰지도 않는다. **버텍스별 웨이트 동일성은 정의상 보장.**
#
# ## 왜 그냥 만지면 안 되는가 (Maya 2024 mayapy 실측)
#
# 1) **skinCluster 는 메시 트랜스폼의 translate/rotate/scale 9개를 잠근다.**
#    바인드 직후 `getAttr(mesh.tx, lock=True)` 가 True 다. 안 풀면 "메시 자체의 이동" 이
#    `setAttr: The attribute 'box.translateX' is locked` 로 막힌다.
#
# 2) **뷰포트에서 버텍스를 옮기면 `<shape>.pnts` 에 들어가고, 이건 스킨 *뒤*에 더해진다.**
#    실측: 같은 편집을 두 포즈에서 재 보면 오프셋이 월드 기준으로 **똑같다**(1.0, 0, 0).
#    즉 조인트를 돌려도 따라가지 않는, 포즈와 무관한 상수 오프셋이다.
#    같은 편집을 체인 헤드(Orig)에 넣으면 포즈에 따라 제대로 회전한다
#    (실측: 포즈 A 에서 (0.866, 0.5, 0) / 포즈 B 에서 (0.5, -0.866, 0)).
#    → **확정할 때 `pnts` 를 체인 헤드로 옮겨 주지 않으면 "고친 메시" 가 아니라
#      "화면에만 맞는 메시" 가 된다.** 이 이동이 이 모듈의 핵심이다.
#    (체인 앞쪽에 `tweak` 노드가 있는 리그는 편집이 거기로 들어가고, 그건 이미 스킨
#     입력이라 옮길 것이 없다. 두 경우를 모두 처리한다.)
#
# 3) **메시 자체를 옮기면 `skinCluster.geomMatrix` 를 따라 갱신해야 한다.**
#    geomMatrix 는 "바인드 시점의 메시 월드 행렬"(멀티 아님, 단일 matrix)이고,
#    스킨은 이 공간에서 계산한 뒤 결과를 메시 로컬로 되돌린다. 메시를 옮겨 두고
#    geomMatrix 를 그대로 두면 옛 자리 기준으로 계산된 변형이 새 자리에 얹혀
#    어긋난다(실측 확인).
#        geomMatrix' = geomMatrix * G0^-1 * G1     (G0/G1 = 편집 전/후 메시 월드 행렬)
#    바인드 포즈에서는 스킨 행렬이 항등이라 **메시는 놓아 둔 자리에 그대로 있고**,
#    조인트를 돌리면 새 자리에서 다시 바인드된 것처럼 변형된다(실측 오차 0).
#
# 편집 상태는 UI 가 아니라 **씬(메시 셰이프의 어트리뷰트)** 에 있다. 툴을 껐다 켜도,
# 다른 창에서도 확정할 수 있고, 씬을 저장했다 열어도 남는다.

import json

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_undo import undo_chunk
from Framework.core import maya_shape

# 체인 헤드 탐색 / 델타 굽기 / 인덱스 규칙은 Bind Pose 탭과 완전히 같아 재사용한다.
from . import bind_pose_manager as bp


# 편집 중임을 표시하는 부울 어트리뷰트 (메시 셰이프에 붙는다)
EDIT_TAG_ATTR = "JUN_meshEdit"

# 편집 시작 시점 상태(JSON). 취소/복원용.
DATA_ATTR = "JUN_meshEditData"

# 편집 중 풀어 줄 트랜스폼 어트리뷰트 (skinCluster 가 잠그는 것들)
_XFORM_ATTRS = ("translateX", "translateY", "translateZ",
                "rotateX", "rotateY", "rotateZ",
                "scaleX", "scaleY", "scaleZ")

# 두 행렬이 같다고 볼 허용 오차
_EPS = 1e-9


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
    """UUID -> 롱네임. 리네임/동명 노드에 안전하다."""
    if not uuid:
        return None
    found = cmds.ls(uuid, l=True) or []
    return found[0] if found else None


def _transform_of(shape):
    parents = cmds.listRelatives(shape, parent=True, f=True) or []
    return parents[0] if parents else None


def skin_clusters_of_shape(shape):
    """이 셰이프를 실제로 변형하는 skinCluster 들 (하류 -> 상류 순)."""

    found = []

    for sc in cmds.ls(cmds.listHistory(shape, pdo=True) or [], type="skinCluster"):
        if sc in found:
            continue
        if shape in maya_shape.deformed_shapes(sc):
            found.append(sc)

    return found


def _tweak_plugs(shape):
    """편집 결과가 떨어질 수 있는 (노드, 플러그 경로) 목록.

    - `<shape>.pnts`            : 히스토리가 있는 셰이프의 tweak. **스킨 뒤**에 적용된다.
    - `<tweak>.vlist[0].vertex` : 체인 앞쪽 tweak 노드. 이미 스킨 입력이다.
    """

    plugs = [(shape, "pnts")]

    for tw in cmds.ls(cmds.listHistory(shape) or [], type="tweak"):
        plugs.append((_long(tw) or tw, "vlist[0].vertex"))

    return plugs


def _read_sparse(node, plug):
    """{인덱스: [x, y, z]} — 실제로 존재하는 element 만 읽는다.

    `getAttr("<shape>.pnts")` 통짜 조회는 "compound with mixed type elements" 로
    실패하므로 인덱스를 먼저 얻어 element 단위로 읽는다.
    """

    values = {}
    base = "{0}.{1}".format(node, plug)

    try:
        indices = cmds.getAttr(base, mi=True) or []
    except Exception:
        return values

    for i in indices:
        try:
            values[int(i)] = list(cmds.getAttr("{0}[{1}]".format(base, i))[0])
        except Exception:
            pass

    return values


def _write_sparse(node, plug, values):
    """스냅샷을 되돌린다.

    스냅샷에 있던 인덱스는 그 값으로 되돌리고, **편집 중에 새로 생긴 인덱스는 지운다**
    (0 으로 덮기만 하면 element 가 남아 셰이프가 계속 "tweak 을 가진" 상태가 된다).
    지우지 못하면 0 으로 덮어 결과만이라도 같게 만든다.
    """

    base = "{0}.{1}".format(node, plug)

    try:
        current = set(int(i) for i in (cmds.getAttr(base, mi=True) or []))
    except Exception:
        current = set()

    failed = 0

    for i in sorted(current | set(int(k) for k in values)):

        element = "{0}[{1}]".format(base, i)
        value = values.get(str(i), values.get(i))

        if value is None:
            try:
                cmds.removeMultiInstance(element, b=True)
                continue
            except Exception:
                value = [0.0, 0.0, 0.0]

        try:
            cmds.setAttr(element, value[0], value[1], value[2], type="double3")
        except Exception:
            failed += 1

    return failed


# =========================
# 상태 조회
# =========================

def is_editing(shape):
    """이 메시 셰이프가 편집 모드인가."""
    return bool(shape) and cmds.objExists(shape) and cmds.attributeQuery(
        EDIT_TAG_ATTR, node=shape, exists=True)


def editing_of(shapes):
    """주어진 목록 중 편집 모드인 셰이프들."""
    return [s for s in (shapes or []) if is_editing(s)]


def find_editing_in_scene():
    """씬 전체에서 편집 모드인 메시를 찾는다.

    편집 상태는 씬(노드)에 있고 UI 에 있지 않다. 툴을 닫았다 열어도 되찾아야 한다.
    """
    return [s for s in (cmds.ls(type="mesh", l=True) or []) if is_editing(s)]


def _read_data(shape):
    if not cmds.attributeQuery(DATA_ATTR, node=shape, exists=True):
        return None
    try:
        return json.loads(cmds.getAttr("{0}.{1}".format(shape, DATA_ATTR)) or "")
    except Exception:
        return None


def _write_data(shape, payload):
    plug = "{0}.{1}".format(shape, DATA_ATTR)
    if not cmds.attributeQuery(DATA_ATTR, node=shape, exists=True):
        cmds.addAttr(shape, ln=DATA_ATTR, dt="string")
    cmds.setAttr(plug, json.dumps(payload), type="string")


def _mark(shape, on):
    """편집 표시 어트리뷰트를 붙이거나 뗀다."""

    exists = cmds.attributeQuery(EDIT_TAG_ATTR, node=shape, exists=True)

    if on and not exists:
        cmds.addAttr(shape, ln=EDIT_TAG_ATTR, at="bool")
        cmds.setAttr("{0}.{1}".format(shape, EDIT_TAG_ATTR), True)
    elif not on and exists:
        try:
            cmds.deleteAttr("{0}.{1}".format(shape, EDIT_TAG_ATTR))
        except Exception:
            pass


def _clear_state(shape):
    _mark(shape, False)
    if cmds.attributeQuery(DATA_ATTR, node=shape, exists=True):
        try:
            cmds.deleteAttr("{0}.{1}".format(shape, DATA_ATTR))
        except Exception:
            pass


# =========================
# 대상 해석
# =========================

def resolve_targets(nodes=None):
    """선택에서 대상 **메시 셰이프**를 모은다.

    메시(트랜스폼/셰이프/컴포넌트)를 골라도 되고 skinCluster 를 골라도 된다.
    스킨이 걸려 있지 않은 메시는 이 탭의 대상이 아니라 제외한다.
    """

    nodes = nodes if nodes else (cmds.ls(sl=True, l=True) or [])
    if not nodes:
        return []

    found = []

    for n in nodes:

        node = n.split(".")[0]

        if not cmds.objExists(node):
            continue

        if cmds.nodeType(node) == "skinCluster":
            shapes = [s for s in maya_shape.deformed_shapes(node)
                      if cmds.nodeType(s) == "mesh"]
        else:
            shape = maya_shape.shape_path(node, type_="mesh")
            shapes = [shape] if shape else []

        for shape in shapes:
            shape = _long(shape)
            if not shape or shape in found:
                continue
            if not skin_clusters_of_shape(shape):
                continue
            found.append(shape)

    return found


def describe(shapes):
    """대상 요약 문자열 + 편집 중 표시."""

    if not shapes:
        return "Nothing loaded."

    if len(shapes) == 1:
        shape = shapes[0]
        skins = skin_clusters_of_shape(shape) if cmds.objExists(shape) else []
        try:
            count = maya_shape.vertex_count(shape)
        except Exception:
            count = "?"
        text = "{0}  |  {1} vert(s)  |  {2}".format(
            shape.split("|")[-1], count,
            ", ".join(skins) if skins else "no skinCluster")
    else:
        text = "{0} mesh(es): {1}".format(
            len(shapes), ", ".join(s.split("|")[-1] for s in shapes))

    editing = editing_of(shapes)
    if editing:
        text += "   [editing: {0}]".format(
            ", ".join(s.split("|")[-1] for s in editing))

    return text


# =========================
# Edit ON
# =========================

def begin_edit(shapes):
    """편집 모드 진입. rest 셰이프를 보여 주고 트랜스폼 잠금을 푼다.

    반환: (처리한 메시 수, 메시지 리스트)
    """

    messages = []

    if not shapes:
        return 0, ["[Warning] No skinned mesh loaded. Select a bound mesh."]

    done = 0

    with undo_chunk():

        for shape in shapes:

            short = shape.split("|")[-1]

            try:
                if is_editing(shape):
                    messages.append("[Info] {0}: already in edit mode.".format(short))
                    continue

                skins = skin_clusters_of_shape(shape)
                if not skins:
                    messages.append(
                        "[Warning] {0}: no skinCluster, skipped.".format(short))
                    continue

                xform = _transform_of(shape)

                data = {
                    "shape": _uuid(shape),
                    "xform": _uuid(xform) if xform else None,
                    "count": int(cmds.polyEvaluate(shape, v=True)),
                    "skins": [],
                    "attrs": {},
                    "tweaks": [],
                    "world": (list(cmds.getAttr(xform + ".worldMatrix[0]"))
                              if xform else None),
                }

                # 포즈 상태를 envelope 를 내리기 **전에** 재 둔다 (내린 뒤엔 잴 수 없다).
                posed = _is_posed(skins[0], shape)

                # ---- skinCluster 별 envelope / geomMatrix 백업 ----
                for sc in skins:

                    entry = {"uuid": _uuid(sc), "name": sc, "envelope": None,
                             "geomMatrix": None}

                    plug = sc + ".envelope"
                    if cmds.listConnections(plug, s=True, d=False):
                        messages.append(
                            "[Warning] {0}: envelope is connected - cannot switch to "
                            "the rest shape. Disconnect it and try again.".format(sc))
                    elif cmds.getAttr(plug, lock=True):
                        messages.append(
                            "[Warning] {0}: envelope is locked - cannot switch to the "
                            "rest shape.".format(sc))
                    else:
                        entry["envelope"] = cmds.getAttr(plug)
                        cmds.setAttr(plug, 0.0)

                    gm = sc + ".geomMatrix"
                    if cmds.attributeQuery("geomMatrix", node=sc, exists=True):
                        if cmds.listConnections(gm, s=True, d=False):
                            messages.append(
                                "[Warning] {0}: geomMatrix is connected - moving the "
                                "mesh itself will not be committed.".format(sc))
                        else:
                            entry["geomMatrix"] = list(cmds.getAttr(gm))

                    data["skins"].append(entry)

                # ---- 트랜스폼 잠금 해제 (스킨이 t/r/s 를 잠가 둔다) ----
                if xform:
                    stuck = []
                    for attr in _XFORM_ATTRS:
                        plug = "{0}.{1}".format(xform, attr)
                        if not cmds.objExists(plug):
                            continue
                        locked = bool(cmds.getAttr(plug, lock=True))
                        data["attrs"][attr] = {"lock": locked,
                                               "value": cmds.getAttr(plug)}
                        if cmds.listConnections(plug, s=True, d=False):
                            stuck.append(attr)
                            continue
                        if locked:
                            cmds.setAttr(plug, lock=False)
                    if stuck:
                        messages.append(
                            "[Warning] {0}: {1} is connected (constraint / expression) "
                            "- moving the mesh itself is limited.".format(
                                xform.split("|")[-1], ", ".join(stuck)))

                # ---- 되돌리기용 tweak 스냅샷 ----
                for node, plug in _tweak_plugs(shape):
                    data["tweaks"].append({
                        "uuid": _uuid(node),
                        "plug": plug,
                        "values": {str(k): v
                                   for k, v in _read_sparse(node, plug).items()},
                    })

                _write_data(shape, data)
                _mark(shape, True)

                done += 1

                messages.append(
                    "[OK] {0}: edit mode ON - the mesh now shows its rest shape "
                    "({1} skinCluster(s) held at envelope 0).".format(short, len(skins)))

                if posed:
                    messages.append(
                        "[Info] {0}: the rig is posed, so the mesh jumped to its rest "
                        "shape. Edit it there - the fix will follow the joints.".format(
                            short))

            except Exception as e:
                messages.append("[Error] {0}: {1}".format(short, e))

    return done, messages


def _is_posed(skin_cluster, shape):
    """지금 리그가 바인드 포즈에서 벗어나 있는가 (스킨 입출력 차이로 판정)."""

    try:
        index = bp._geometry_index(skin_cluster, shape)
        src = bp._deformer_input_points(skin_cluster, index)
        dst = bp._deformer_output_points(skin_cluster, index)
        if len(src) != len(dst):
            return True
        for i in range(len(src)):
            if (src[i] - dst[i]).length() > 1e-5:
                return True
    except Exception:
        return False

    return False


# =========================
# Edit OFF (확정)
# =========================

def end_edit(shapes):
    """편집 모드 종료. 지금 보이는 메시를 새 rest 상태로 굳힌다.

    1) `<shape>.pnts` 에 떨어진 편집(스킨 뒤 적용)을 체인 헤드(Orig)로 옮긴다.
    2) 메시 자체를 옮겼으면 `geomMatrix` 를 따라 갱신한다.
    3) envelope 와 트랜스폼 잠금을 되돌린다.

    반환: (처리한 메시 수, 메시지 리스트)
    """

    messages = []

    if not shapes:
        return 0, ["[Warning] Nothing loaded."]

    done = 0

    with undo_chunk():

        for shape in shapes:

            short = shape.split("|")[-1]

            try:
                if not is_editing(shape):
                    messages.append(
                        "[Info] {0}: not in edit mode, skipped.".format(short))
                    continue

                data = _read_data(shape) or {}
                skins = skin_clusters_of_shape(shape)

                count = int(cmds.polyEvaluate(shape, v=True))
                same_topology = (count == data.get("count", count))

                if not same_topology:
                    messages.append(
                        "[Warning] {0}: the vertex count changed ({1} -> {2}). Skin "
                        "weights follow Maya's own remapping and the tweak transfer "
                        "below is skipped - check the result.".format(
                            short, data.get("count"), count))

                # ---- 1) 스킨 뒤에 얹힌 편집을 rest 셰이프로 옮긴다 ----
                if same_topology:
                    for line in _migrate_shape_tweaks(shape, skins, data, count):
                        messages.append(line)

                # ---- 2) 메시 자체를 옮겼으면 geomMatrix 갱신 ----
                for line in _commit_geom_matrix(shape, skins, data):
                    messages.append(line)

                # ---- 3) envelope 복구 ----
                restored = 0
                for entry in (data.get("skins") or []):
                    sc = _from_uuid(entry.get("uuid")) or entry.get("name")
                    if not sc or not cmds.objExists(sc):
                        continue
                    if entry.get("envelope") is None:
                        continue
                    try:
                        cmds.setAttr(sc + ".envelope", entry["envelope"])
                        restored += 1
                    except Exception as e:
                        messages.append(
                            "[Warning] {0}: could not restore the envelope "
                            "({1}).".format(sc, e))

                # ---- 4) 트랜스폼 잠금 복구 ----
                _restore_locks(data, messages)

                _clear_state(shape)

                done += 1
                messages.append(
                    "[OK] {0}: edit mode OFF - the edited mesh is the new rest shape "
                    "({1} skinCluster(s) restored, weights unchanged).".format(
                        short, restored))

            except Exception as e:
                messages.append("[Error] {0}: {1}".format(short, e))

    return done, messages


def _migrate_shape_tweaks(shape, skins, data, count):
    """`<shape>.pnts` 의 편집분을 체인 헤드(Orig)로 옮긴다.

    옮기지 않으면 그 편집은 **포즈와 무관한 상수 오프셋**으로 남아 조인트를 따라가지
    않는다(모듈 상단 주석의 실측 참고). 체인 앞쪽 tweak 노드에 떨어진 편집은 이미 스킨
    입력이므로 손댈 것이 없다.
    """

    lines = []
    short = shape.split("|")[-1]

    start = {}
    for entry in (data.get("tweaks") or []):
        node = _from_uuid(entry.get("uuid"))
        if node and node == _long(shape) and entry.get("plug") == "pnts":
            start = entry.get("values") or {}
            break

    current = _read_sparse(shape, "pnts")

    indices = set(current) | set(int(k) for k in start)
    delta = {}

    for i in indices:
        now = current.get(i, [0.0, 0.0, 0.0])
        was = start.get(str(i), [0.0, 0.0, 0.0])
        d = (now[0] - was[0], now[1] - was[1], now[2] - was[2])
        if abs(d[0]) > 1e-9 or abs(d[1]) > 1e-9 or abs(d[2]) > 1e-9:
            delta[i] = d

    if not delta:
        return lines

    if not skins:
        return ["[Warning] {0}: no skinCluster, tweaks left as they are.".format(short)]

    sc = skins[0]
    head = None

    try:
        index = bp._geometry_index(sc, shape)
        head = bp._chain_head_shape(sc, index)
    except bp.GeometryNotMesh as e:
        lines.append("[Warning] {0}: {1}.".format(short, e))
    except Exception as e:
        lines.append("[Warning] {0}: could not walk the deformer chain ({1}).".format(
            short, e))

    if head is None:
        head = bp._fallback_head_shape(shape, count)
        if head:
            lines.append("[Info] {0}: input shape resolved by fallback ({1}).".format(
                short, head.split("|")[-1]))

    if head is None:
        lines.append(
            "[Warning] {0}: could not resolve the input (Orig) shape, so {1} edited "
            "vertex/vertices stay as a post-deformation tweak - they will NOT follow "
            "the joints. Run Diagnose on the Bind Pose tab to see where the chain "
            "stops.".format(short, len(delta)))
        return lines

    head_count = int(cmds.polyEvaluate(head, v=True))
    if head_count != count:
        lines.append(
            "[Warning] {0}: input shape {1} has a different vertex count ({2} vs {3}) "
            "- the edited vertices stay as a post-deformation tweak.".format(
                short, head.split("|")[-1], head_count, count))
        return lines

    # 라이브 blendShape 타겟은 굽는 델타를 weight 비율만큼 상쇄한다 (Bind Pose 탭과 동일).
    try:
        _, risky = bp._live_blendshape_targets(shape)
    except Exception:
        risky = []

    for node, hot in risky:
        detail = ", ".join("{0}={1:.3f}".format(n, v) for n, v in hot[:6])
        if len(hot) > 6:
            detail += ", ... (+{0})".format(len(hot) - 6)
        lines.append(
            "[Warning] {0}: blendShape '{1}' has LIVE target geometry with non-zero "
            "weights ({2}). The mesh edit is cancelled in proportion to the weight. "
            "Edit at neutral (weights 0) or delete the target meshes.".format(
                short, node, detail))

    before = _world_points(shape)

    full = [delta.get(i, (0.0, 0.0, 0.0)) for i in range(count)]
    bp._bake_delta(head, full)

    # 헤드로 옮겼으니 셰이프 위의 tweak 은 편집 시작 시점 값으로 되돌린다.
    _write_sparse(shape, "pnts", start)

    lines.append(
        "[OK] {0}: moved {1} edited vertex/vertices onto the rest shape {2} - they now "
        "follow the joints.".format(short, len(delta), head.split("|")[-1]))

    # 옮기는 과정에서 형상이 달라지지 않았는지 스스로 확인한다 (헤드와 스킨 사이에
    # 다른 디포머가 있으면 델타가 그대로 통과하지 않을 수 있다).
    after = _world_points(shape)
    if before is not None and after is not None and len(before) == len(after):
        worst = max((before[i] - after[i]).length() for i in range(len(before)))
        if worst > 1e-4:
            lines.append(
                "[Warning] {0}: the shape moved by up to {1:.4f} while the edit was "
                "transferred onto the rest shape. A deformer between the rest shape "
                "and the skin is changing it - check the result.".format(short, worst))

    return lines


def _world_points(shape):
    try:
        return om.MFnMesh(maya_shape.shape_dag(shape)).getPoints(om.MSpace.kWorld)
    except Exception:
        return None


def _commit_geom_matrix(shape, skins, data):
    """메시 자체를 옮겼으면 skinCluster.geomMatrix 를 같은 만큼 옮긴다."""

    lines = []
    short = shape.split("|")[-1]

    xform = _from_uuid(data.get("xform")) or _transform_of(shape)
    world0 = data.get("world")

    if not xform or not world0:
        return lines

    g0 = om.MMatrix(world0)
    g1 = om.MMatrix(cmds.getAttr(xform + ".worldMatrix[0]"))

    if g0.isEquivalent(g1, _EPS):
        return lines

    # 월드 공간에서 메시에 얹힌 변화량. (row-vector 규약: p * G0 * D == p * G1)
    d = g0.inverse() * g1

    moved = 0

    for entry in (data.get("skins") or []):

        sc = _from_uuid(entry.get("uuid")) or entry.get("name")
        if not sc or not cmds.objExists(sc):
            continue

        gm0 = entry.get("geomMatrix")
        if gm0 is None:
            lines.append(
                "[Warning] {0}: geomMatrix was not captured (locked or connected) - "
                "moving the mesh itself was not committed.".format(sc))
            continue

        try:
            cmds.setAttr(sc + ".geomMatrix", *list(om.MMatrix(gm0) * d), type="matrix")
            moved += 1
        except Exception as e:
            lines.append(
                "[Warning] {0}: could not update geomMatrix ({1}).".format(sc, e))

    if moved:
        lines.append(
            "[OK] {0}: the mesh itself moved - geomMatrix updated on {1} "
            "skinCluster(s), so the skin now deforms from the new place.".format(
                short, moved))

    return lines


def _restore_locks(data, messages):
    """편집을 시작할 때 잠겨 있던 t/r/s 를 다시 잠근다."""

    xform = _from_uuid(data.get("xform"))
    if not xform:
        return

    for attr, info in (data.get("attrs") or {}).items():
        if not info.get("lock"):
            continue
        plug = "{0}.{1}".format(xform, attr)
        if not cmds.objExists(plug):
            continue
        try:
            cmds.setAttr(plug, lock=True)
        except Exception as e:
            messages.append("[Warning] {0}: could not re-lock ({1}).".format(plug, e))


# =========================
# 취소
# =========================

def cancel_edit(shapes):
    """편집을 버리고 메시를 편집 시작 시점으로 되돌린다.

    되돌리는 것: 버텍스 tweak, 메시 트랜스폼 값, envelope, 잠금.
    되돌리지 못하는 것: 토폴로지를 바꾼 편집 — 그때는 무엇을 못 되돌렸는지 알린다
    (Ctrl+Z 로 마저 되돌리면 된다).

    반환: (처리한 메시 수, 메시지 리스트)
    """

    messages = []

    if not shapes:
        return 0, ["[Warning] Nothing loaded."]

    done = 0

    with undo_chunk():

        for shape in shapes:

            short = shape.split("|")[-1]

            try:
                if not is_editing(shape):
                    messages.append(
                        "[Info] {0}: not in edit mode, skipped.".format(short))
                    continue

                data = _read_data(shape) or {}

                count = int(cmds.polyEvaluate(shape, v=True))

                if count != data.get("count", count):
                    messages.append(
                        "[Warning] {0}: the vertex count changed ({1} -> {2}) - the "
                        "vertex edits could not be restored. Use Ctrl+Z for "
                        "those.".format(short, data.get("count"), count))
                else:
                    failed = 0
                    for entry in (data.get("tweaks") or []):
                        node = _from_uuid(entry.get("uuid"))
                        if not node:
                            continue
                        failed += _write_sparse(node, entry.get("plug"),
                                                entry.get("values") or {})
                    if failed:
                        messages.append(
                            "[Warning] {0}: {1} vertex tweak(s) could not be "
                            "restored.".format(short, failed))

                # 트랜스폼 값 복구 (아직 잠금이 풀린 상태에서 먼저 쓴다)
                xform = _from_uuid(data.get("xform"))
                if xform:
                    stuck = []
                    for attr, info in (data.get("attrs") or {}).items():
                        plug = "{0}.{1}".format(xform, attr)
                        if not cmds.objExists(plug) or "value" not in info:
                            continue
                        if cmds.listConnections(plug, s=True, d=False):
                            stuck.append(attr)
                            continue
                        try:
                            cmds.setAttr(plug, lock=False)
                            cmds.setAttr(plug, info["value"])
                        except Exception:
                            stuck.append(attr)
                    if stuck:
                        messages.append("[Warning] {0}: could not restore {1}.".format(
                            short, ", ".join(stuck)))

                # envelope 복구
                for entry in (data.get("skins") or []):
                    sc = _from_uuid(entry.get("uuid")) or entry.get("name")
                    if not sc or not cmds.objExists(sc):
                        continue
                    if entry.get("envelope") is None:
                        continue
                    try:
                        cmds.setAttr(sc + ".envelope", entry["envelope"])
                    except Exception:
                        pass

                _restore_locks(data, messages)
                _clear_state(shape)

                done += 1
                messages.append(
                    "[OK] {0}: edit cancelled - the mesh was restored.".format(short))

            except Exception as e:
                messages.append("[Error] {0}: {1}".format(short, e))

    return done, messages
