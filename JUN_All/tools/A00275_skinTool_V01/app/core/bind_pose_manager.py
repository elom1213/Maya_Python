# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-20
# A00275_skinTool_V01 - 바인드 포즈 갱신 로직 (maya.cmds / maya.api, UI 비의존)
#
# "조인트를 이동·회전한 현재 상태를 새 바인드 포즈로 만든다."
#
# 마야에는 이걸 하는 단일 기능이 없다(mayapy 로 확인):
#   - skinCluster -e -recacheBindMatrices : bindPreMatrix 를 전혀 바꾸지 않는다. 무효.
#   - dagPose -reset                      : bindPose 노드가 갱신되지 않는다.
#                                           (Go to Bind Pose 가 여전히 옛 포즈로 간다)
#   - Move Skinned Joints Tool            : 목적이 다르다. "메시를 변형시키지 않고 조인트만
#                                           이동" 이라, 이미 변형된 상태를 굳히지는 못한다.
#
# 그래서 3단계를 직접 수행한다.
#
#   1) bindPreMatrix[i] = 해당 인플루언스의 현재 worldInverseMatrix
#      → 스킨 변형 행렬이 항등이 되어, skinCluster 출력 == skinCluster 입력 이 된다.
#   2) (Keep current shape 모드) 스킨이 만들어내던 변형량을 체인 입력 셰이프에 굽는다.
#      delta = skinCluster 출력 - skinCluster 입력  을 체인 헤드 셰이프에 더한다.
#      → 새 입력이 곧 예전 출력이 되어, 화면상 형상이 그대로 유지된다.
#   3) bindPose(dagPose) 노드를 현재 포즈로 다시 만들고 skinCluster.bindPose 에 재연결.
#      → 마야의 Go to Bind Pose 가 이제 이 포즈로 돌아온다.
#
# 왜 "체인 헤드"에 굽는가:
#   blendShape 는 정적 델타를 더하는 선형 연산이라 f(orig + d) = f(orig) + d 가 성립한다.
#   따라서 체인 맨 앞(orig) 에 d 를 더하면 skinCluster 입력이 정확히 d 만큼 이동한다.
#   블렌드셰이프가 스킨 앞이든 뒤든, 메시 트랜스폼이 원점이 아니어도 성립한다(검증 완료).
#   중간 셰이프(Orig)가 여러 개일 수 있으므로 이름으로 고르면 안 되고 연결을 타고 올라가야 한다.
#
# 알려진 한계:
#   blendShape 타겟 지오가 아직 "라이브로 연결"돼 있고 그 weight 가 0 이 아니면,
#   델타가 (target - base) 로 매 평가마다 재계산돼 우리가 더한 d 가 상쇄된다.
#   이 경우를 감지해 경고한다(타겟을 지워 델타를 고정하거나 weight 를 0 으로 두고 실행).

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_undo import undo_chunk


# =========================
# 낮은 수준 헬퍼
# =========================

def _dag_path(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDagPath(0)


def _depend_node(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDependNode(0)


class GeometryNotMesh(Exception):
    """대상 지오메트리가 폴리곤 메시가 아님 (nurbsSurface/curve/lattice 등)."""


def _input_geometry_plug(deformer, index=0):
    """<deformer>.input[index].inputGeometry 플러그.

    input 은 컴파운드 배열이라 child 를 이름으로 찾아야 한다(자식 순서는 노드 타입마다 다름).
    index 를 0 으로 고정하면 안 된다 — 한 디포머가 여러 지오를 변형하거나 지오를 뺐다 넣으면
    실제 논리 인덱스가 0 이 아닐 수 있고, 없는 인덱스를 읽으면 빈 데이터가 나와
    "(kInvalidParameter): Object is incompatible with this method" 로 터진다.
    """
    fn = om.MFnDependencyNode(_depend_node(deformer))
    ip = fn.findPlug("input", False).elementByLogicalIndex(index)

    for c in range(ip.numChildren()):
        if ip.child(c).partialName(useLongNames=True).endswith("inputGeometry"):
            return ip.child(c)

    return None


def _geometry_index(deformer, shape):
    """deformer 가 shape 을 변형할 때 쓰는 논리 인덱스.

    outputGeometry[i] 가 어디로 나가는지 따라가 shape 과 일치하는 i 를 찾는다.
    """

    shape_long = cmds.ls(shape, l=True)[0]

    indices = cmds.getAttr(deformer + ".input", mi=True) or [0]

    for i in indices:
        dest = cmds.listConnections(
            "{0}.outputGeometry[{1}]".format(deformer, i),
            s=False, d=True, sh=True) or []

        for d in dest:
            if cmds.ls(d, l=True) and cmds.ls(d, l=True)[0] == shape_long:
                return i

        # 하류에 다른 디포머가 더 있으면 그 끝까지 따라간다
        for d in dest:
            if _reaches_shape(d, shape_long, set()):
                return i

    return indices[0] if indices else 0


def _output_geometry_plug_names(node):
    """node 의 지오 출력 플러그 이름들.

    디포머는 `outputGeometry[i]` (배열)이지만 groupParts 같은 노드는 `outputGeometry`
    스칼라다. 후자에 대고 `getAttr(node.input, mi=True)` 를 부르면 예외가 난다.
    """

    if not cmds.attributeQuery("outputGeometry", node=node, exists=True):
        return []

    if cmds.attributeQuery("outputGeometry", node=node, multi=True):
        return ["{0}.outputGeometry[{1}]".format(node, i)
                for i in (cmds.getAttr(node + ".input", mi=True) or [0])]

    return ["{0}.outputGeometry".format(node)]


def _reaches_shape(node, shape_long, seen):
    """node 의 지오 출력이 결국 shape_long 에 도달하는가 (디포머 체인 하류 추적)."""

    if node in seen:
        return False
    seen.add(node)

    long_name = cmds.ls(node, l=True)
    if long_name and long_name[0] == shape_long:
        return True

    for plug in _output_geometry_plug_names(node):
        for d in (cmds.listConnections(plug, s=False, d=True, sh=True) or []):
            if _reaches_shape(d, shape_long, seen):
                return True

    return False


def _mesh_from_plug(plug, what):
    """지오 플러그의 데이터를 MFnMesh 로 연다. 메시가 아니면 명확한 예외."""

    data = plug.asMObject()

    if data.isNull() or not data.hasFn(om.MFn.kMeshData):
        raise GeometryNotMesh(
            "{0} is not polygon mesh data (got {1})".format(what, data.apiTypeStr))

    return om.MFnMesh(data)


def _deformer_input_points(deformer, index=0):
    """디포머가 실제로 받는 입력 지오의 포인트 (상위 디포머 결과가 반영된 값)."""
    plug = _input_geometry_plug(deformer, index)
    return _mesh_from_plug(plug, "{0}.input[{1}]".format(deformer, index)).getPoints(
        om.MSpace.kObject)


def _deformer_output_points(deformer, index=0):
    """디포머가 내보내는 출력 지오의 포인트.

    화면의 shape 을 읽으면 하류 디포머까지 섞이므로, 반드시 이 디포머의 출력을 읽는다.
    """
    fn = om.MFnDependencyNode(_depend_node(deformer))
    plug = fn.findPlug("outputGeometry", False).elementByLogicalIndex(index)
    return _mesh_from_plug(
        plug, "{0}.outputGeometry[{1}]".format(deformer, index)).getPoints(
            om.MSpace.kObject)


def _upstream_geometry_plug(node, out_plug_name):
    """node 의 "지오 입력" 플러그. 계속 거슬러 올라가기 위한 다음 발판.

    디포머는 `input[i].inputGeometry`, groupParts/tweak 같은 노드는 `inputGeometry`
    스칼라를 쓴다. 둘 다 처리해야 실제 리그의 체인을 끝까지 올라갈 수 있다.
    """

    if cmds.attributeQuery("input", node=node, exists=True):
        try:
            return _input_geometry_plug(node, _upstream_index(out_plug_name))
        except Exception:
            pass

    if cmds.attributeQuery("inputGeometry", node=node, exists=True):
        try:
            return om.MFnDependencyNode(_depend_node(node)).findPlug(
                "inputGeometry", False)
        except Exception:
            return None

    return None


def _upstream_index(out_plug_name):
    """'node.outputGeometry[3]' 형태의 플러그 이름에서 논리 인덱스를 뽑는다."""

    try:
        return int(out_plug_name.rsplit("[", 1)[1].split("]")[0])
    except Exception:
        return 0


def _chain_head_shape(deformer, index=0):
    """디포머 체인을 거슬러 올라가 실제 소스 메시 shape(보통 ...Orig)을 찾는다.

    못 찾으면 None. 메시가 아닌 지오면 GeometryNotMesh.
    """

    cur = _input_geometry_plug(deformer, index)
    if cur is None:
        return None

    seen = set()

    while True:
        src = cmds.listConnections(cur.name(), s=True, d=False, p=True) or []
        if not src:
            return None

        src_node = src[0].split(".")[0]
        if src_node in seen:          # 순환 방어
            return None
        seen.add(src_node)

        node_type = cmds.nodeType(src_node)

        if node_type == "mesh":
            return cmds.ls(src_node, l=True)[0]

        # 소스가 지오이긴 한데 메시가 아니면(nurbsSurface/nurbsCurve/lattice 등)
        # 형상 굽기는 불가능하다. 호출부가 알맞은 안내를 하도록 명시적으로 알린다.
        if node_type in ("nurbsSurface", "nurbsCurve", "lattice", "subdiv"):
            raise GeometryNotMesh("input geometry is {0}".format(node_type))

        nxt = _upstream_geometry_plug(src_node, src[0])
        if nxt is None:
            return None
        cur = nxt


def _fallback_head_shape(shape, vtx_count):
    """체인 워크가 실패했을 때 쓰는 예비 수단.

    변형되는 shape 과 같은 트랜스폼 아래에서, 버텍스 수가 같은 intermediate 셰이프를
    찾는다. 히스토리 구성이 특이해 연결을 끝까지 못 탄 경우를 구제한다.
    버텍스 수로 걸러내므로 엉뚱한 셰이프에 굽지는 않는다.
    """

    if not shape:
        return None

    parents = cmds.listRelatives(shape, parent=True, f=True) or []
    if not parents:
        return None

    for s in (cmds.listRelatives(parents[0], s=True, f=True, type="mesh") or []):
        if not cmds.getAttr(s + ".intermediateObject"):
            continue
        try:
            if cmds.polyEvaluate(s, v=True) == vtx_count:
                return cmds.ls(s, l=True)[0]
        except Exception:
            continue

    return None


def _influence_index_map(skin_cluster):
    """{matrix 논리 인덱스: 인플루언스 이름}.

    주의: `skinCluster -q -inf` 목록의 순서는 matrix[]/bindPreMatrix[] 의 논리 인덱스와
    다를 수 있다. 인플루언스를 뺐다 다시 넣으면 인덱스가 성겨져(예: [0,1,3,4,5,6])
    enumerate 로 번호를 매기면 엉뚱한 슬롯에 행렬이 들어가고, 결과는 더블 트랜스폼처럼
    보인다. 반드시 matrix[] 연결에서 매핑을 읽어야 한다.
    """

    mapping = {}

    for i in (cmds.getAttr(skin_cluster + ".matrix", mi=True) or []):
        con = cmds.listConnections("{0}.matrix[{1}]".format(skin_cluster, i),
                                   s=True, d=False) or []
        if con:
            mapping[i] = con[0]

    return mapping


def _live_blendshape_targets(mesh):
    """타겟 지오가 아직 연결돼 있는 blendShape + 그 중 weight != 0 인 것을 찾는다.

    반환: (live_blendshapes, risky) — risky 는 [(노드, [(타겟명, weight), ...]), ...]

    왜 위험한가: 타겟이 라이브로 연결돼 있으면 blendShape 출력은
        out = (1 - w) * orig + w * target
    이라 orig 에 d 를 더해도 실제로는 (1 - w)*d 만 반영된다. 즉 **w 에 비례해 상쇄**된다.
    w=1 이면 완전히 무시되고, w=0.5 면 절반만 먹는 식으로 '조용히 조금 틀린' 결과가 된다.
    (타겟을 지워 델타가 고정된 blendShape 은 이 문제가 없다 — 검증 완료)
    """

    live, risky = [], []

    history = cmds.listHistory(mesh, pdo=True) or []

    for node in history:
        if cmds.nodeType(node) != "blendShape":
            continue

        conns = cmds.listConnections(node + ".inputTarget", s=True, d=False,
                                     type="mesh") or []
        if not conns:
            continue

        live.append(node)

        hot = []
        for w in (cmds.listAttr(node + ".w", m=True) or []):
            try:
                value = cmds.getAttr("{0}.{1}".format(node, w))
                if abs(value) > 1e-6:
                    hot.append((w, value))
            except Exception:
                pass

        if hot:
            risky.append((node, hot))

    return live, risky


# =========================
# 씬 조회
# =========================

def skin_clusters_of(node):
    """트랜스폼/셰이프 이름을 받아 연결된 skinCluster 목록을 돌려준다."""

    shapes = []

    if cmds.nodeType(node) == "mesh":
        shapes = [node]
    else:
        shapes = cmds.listRelatives(node, s=True, f=True, type="mesh") or []

    found = []
    for s in shapes:
        if cmds.getAttr("{0}.intermediateObject".format(s)):
            continue
        for sc in cmds.ls(cmds.listHistory(s, pdo=True) or [], type="skinCluster"):
            if sc not in found:
                found.append(sc)

    return found


def mesh_of_skin_cluster(sc):
    """skinCluster 가 변형하는 (non-intermediate) 메시 shape 의 풀 패스."""

    geo = cmds.skinCluster(sc, q=True, g=True) or []
    for g in geo:
        if cmds.nodeType(g) == "mesh" and not cmds.getAttr(g + ".intermediateObject"):
            return cmds.ls(g, l=True)[0]

    return cmds.ls(geo[0], l=True)[0] if geo else None


def resolve_targets(nodes=None):
    """선택(또는 주어진 노드)에서 대상 skinCluster 를 모은다.

    메시를 골라도 되고 조인트를 골라도 된다. 조인트를 고르면 그 조인트가 영향을 주는
    모든 skinCluster 를 찾는다 (조인트만 선택한 채 버튼을 누르는 흐름을 지원).
    """

    nodes = nodes if nodes else (cmds.ls(sl=True, l=True) or [])
    if not nodes:
        return []

    found = []

    for n in nodes:
        node = n.split(".")[0]

        if cmds.nodeType(node) == "skinCluster":
            if node not in found:
                found.append(node)
            continue

        for sc in skin_clusters_of(node):
            if sc not in found:
                found.append(sc)

        # 조인트라면 그 조인트가 물린 skinCluster 들을
        if cmds.nodeType(node) in ("joint", "transform"):
            for sc in cmds.ls(cmds.listConnections(node, s=False, d=True) or [],
                              type="skinCluster"):
                if sc not in found:
                    found.append(sc)

    return found


# =========================
# 메인 동작
# =========================

def update_bind_pose(skin_clusters, keep_shape=True, rebuild_dag_pose=True):
    """현재 조인트 포즈를 새 바인드 포즈로 만든다.

    keep_shape=True  : 지금 보이는(변형된) 형상을 그대로 유지한 채 rest 로 굳힌다.
    keep_shape=False : bindPreMatrix 만 갱신 → 메시는 원래 rest 형상으로 스냅백한다
                       (Move Skinned Joints Tool 로 조인트를 옮긴 것과 같은 결과).

    반환: (처리한 skinCluster 수, 메시지 리스트)
    """

    messages = []

    if not skin_clusters:
        return 0, ["[Warning] No skinCluster found. Select a bound mesh or its joints."]

    done = 0

    with undo_chunk():

        for sc in skin_clusters:

            try:
                mesh = mesh_of_skin_cluster(sc)
                if not mesh:
                    messages.append("[Warning] {0}: no geometry found, skipped.".format(sc))
                    continue

                geo_index = _geometry_index(sc, mesh)

                # ---- 굽기 전에 스킨이 만들던 변형량을 확보한다 --------------
                delta = None
                head = None
                reason = None       # 굽지 못한 이유 (요약 줄에 그대로 싣는다)

                if keep_shape:
                    try:
                        skin_in = _deformer_input_points(sc, geo_index)
                        skin_out = _deformer_output_points(sc, geo_index)

                        if len(skin_in) != len(skin_out):
                            reason = ("skin input/output vertex counts differ "
                                      "({0} vs {1})".format(len(skin_in), len(skin_out)))
                        else:
                            head = _chain_head_shape(sc, geo_index)

                            if head is None:
                                # 체인을 못 탄 경우: 같은 트랜스폼의 intermediate 로 재시도
                                head = _fallback_head_shape(mesh, len(skin_in))
                                if head:
                                    messages.append(
                                        "[Info] {0}: input shape resolved by fallback "
                                        "({1}).".format(sc, head.split("|")[-1]))

                            if head is None:
                                reason = ("could not resolve the input (Orig) shape "
                                          "from the deformer chain")
                            elif cmds.polyEvaluate(head, v=True) != len(skin_in):
                                reason = ("input shape {0} has a different vertex count "
                                          "({1} vs {2})".format(
                                              head.split("|")[-1],
                                              cmds.polyEvaluate(head, v=True),
                                              len(skin_in)))
                                head = None
                            else:
                                delta = [(skin_out[i].x - skin_in[i].x,
                                          skin_out[i].y - skin_in[i].y,
                                          skin_out[i].z - skin_in[i].z)
                                         for i in range(len(skin_in))]

                        # 라이브 blendShape 타겟 경고
                        _, risky = _live_blendshape_targets(mesh)
                        for node, hot in risky:
                            detail = ", ".join("{0}={1:.3f}".format(n, v)
                                               for n, v in hot[:6])
                            if len(hot) > 6:
                                detail += ", ... (+{0})".format(len(hot) - 6)
                            messages.append(
                                "[Warning] {0}: blendShape '{1}' has LIVE target "
                                "geometry with non-zero weights ({2}). The baked offset "
                                "is cancelled in proportion to the weight, so the result "
                                "can be silently off. Set those weights to 0 (update at "
                                "neutral) or delete the target meshes to freeze the "
                                "deltas, then run again.".format(sc, node, detail))

                    except GeometryNotMesh as e:
                        head = None
                        delta = None
                        reason = ("{0} - 'Keep current shape' only works on polygon "
                                  "meshes. Use 'Snap mesh to rest shape' instead"
                                  .format(e))

                    if reason:
                        messages.append("[Warning] {0}: shape not kept - {1}.".format(
                            sc, reason))

                # ---- 1) bindPreMatrix = 현재 worldInverseMatrix -------------
                # 인덱스는 반드시 matrix[] 연결에서 얻는다 (아래 함수 주석 참고).
                index_map = _influence_index_map(sc)

                if not index_map:
                    messages.append(
                        "[Warning] {0}: no influence connection found, skipped.".format(sc))
                    continue

                blocked = []

                for idx, inf in sorted(index_map.items()):

                    plug = "{0}.bindPreMatrix[{1}]".format(sc, idx)

                    if (cmds.listConnections(plug, s=True, d=False)
                            or cmds.getAttr(plug, lock=True)):
                        blocked.append(inf)
                        continue

                    wim = cmds.getAttr(inf + ".worldInverseMatrix[0]")
                    cmds.setAttr(plug, *wim, type="matrix")

                if blocked:
                    messages.append(
                        "[Warning] {0}: bindPreMatrix is locked or connected for {1}. "
                        "Those influences were left untouched (unlock or disconnect "
                        "them to include them).".format(sc, ", ".join(blocked)))

                # ---- 2) 현재 형상을 체인 입력에 굽는다 -----------------------
                if keep_shape and head is not None and delta is not None:
                    _bake_delta(head, delta)

                # ---- 3) bindPose 노드 재생성 -------------------------------
                if rebuild_dag_pose:
                    bp_msg = _rebuild_bind_pose(sc, list(index_map.values()))
                    if bp_msg:
                        messages.append(bp_msg)

                done += 1

                if not keep_shape:
                    what = "mesh snapped to rest"
                elif delta is not None and head is not None:
                    what = "shape kept"
                else:
                    # keep 을 요청했지만 굽지 못한 경우를 "shape kept" 라고 보고하면 안 된다.
                    # 이유를 요약 줄에 함께 실어, 로그를 뒤져 짝을 맞출 필요가 없게 한다.
                    what = "bind matrices only - shape NOT kept: {0}".format(
                        reason or "unknown reason")

                messages.append(
                    "[OK] {0}: bind pose updated ({1} influences, {2}).".format(
                        sc, len(index_map), what))

            except Exception as e:
                messages.append("[Error] {0}: {1}".format(sc, e))

    return done, messages


def _read_tweaks(shape):
    """shape.pnts 의 기존 값 {idx: (x, y, z)}.

    getAttr(".pnts") 통짜 조회는 "compound with mixed type elements" 로 실패하므로
    MPlug 로 실제 존재하는 element 만 읽는다.
    """

    tweaks = {}

    try:
        plug = om.MFnDependencyNode(_depend_node(shape)).findPlug("pnts", False)
        for i in plug.getExistingArrayAttributeIndices():
            ep = plug.elementByLogicalIndex(i)
            tweaks[i] = (ep.child(0).asFloat(),
                         ep.child(1).asFloat(),
                         ep.child(2).asFloat())
    except Exception:
        pass

    return tweaks


def _bake_delta(shape, delta):
    """체인 헤드 셰이프에 델타를 더한다.

    MFnMesh.setPoints 를 쓰면 안 된다 — undo 큐에 안 올라가서, Ctrl+Z 를 누르면
    bindPreMatrix 만 되돌아가고 구운 형상은 남아 메시가 어긋난 채 방치된다.
    대신 pnts(tweak) 에 구간 setAttr 로 쓴다(undo 가능, 19k 버텍스도 0.1 초).

    반드시 "기존 pnts 에 더해야" 한다. 프리즈한 트랜스폼 등이 이미 tweak 으로 들어가
    있는 경우가 흔해서(예: ty=2 를 freeze 하면 전 버텍스에 (0,2,0) 이 남는다),
    덮어쓰면 그 값이 통째로 날아간다.
    """

    n = len(delta)
    cur = _read_tweaks(shape)

    flat = []
    for i in range(n):
        c = cur.get(i, (0.0, 0.0, 0.0))
        d = delta[i]
        flat.extend([c[0] + d[0], c[1] + d[1], c[2] + d[2]])

    if n == 1:
        cmds.setAttr("{0}.pnts[0]".format(shape),
                     flat[0], flat[1], flat[2], type="double3")
    else:
        cmds.setAttr("{0}.pnts[0:{1}]".format(shape, n - 1),
                     *flat, type="double3")


def _rebuild_bind_pose(sc, influences):
    """bindPose(dagPose) 노드를 현재 포즈로 다시 만들고 skinCluster 에 재연결한다.

    dagPose -reset 은 bindPose 를 갱신하지 못하므로(검증 완료) 지우고 새로 만든다.
    재연결을 빼먹으면 마야의 Go to Bind Pose 가 포즈를 못 찾는다.

    이름은 원래 노드 이름을 그대로 물려준다. 안 그러면 실행할 때마다 bindPose12,
    bindPose37 처럼 번호가 튀는 노드가 새로 생겨 씬이 지저분해진다.
    """

    old = cmds.listConnections(sc + ".bindPose", d=False, s=True,
                               type="dagPose") or []

    roots = _influence_roots(influences)
    if not roots:
        return "[Warning] {0}: no influence root, bindPose not rebuilt.".format(sc)

    old_name = old[0].split("|")[-1] if old else None

    for o in old:
        try:
            cmds.delete(o)
        except Exception:
            pass

    # 여러 루트가 있으면 전부 한 포즈에 담는다 (한쪽만 저장하면 나머지가 빠진다)
    new_bp = cmds.dagPose(*roots, save=True, bindPose=True)
    if isinstance(new_bp, (list, tuple)):
        new_bp = new_bp[0]

    if old_name and new_bp != old_name:
        try:
            new_bp = cmds.rename(new_bp, old_name)
        except Exception:
            pass

    try:
        cmds.connectAttr(new_bp + ".message", sc + ".bindPose", f=True)
    except Exception as e:
        return "[Warning] {0}: bindPose created but not connected ({1}).".format(sc, e)

    return None


def _influence_roots(influences):
    """인플루언스들의 최상위 조상(중복 제거). dagPose 저장의 시작점."""

    roots = []

    for inf in influences:
        node = inf
        while True:
            parent = cmds.listRelatives(node, parent=True, f=True, type="joint")
            if not parent:
                break
            node = parent[0]

        full = cmds.ls(node, l=True)[0]
        if full not in roots:
            roots.append(full)

    return roots


# =========================
# 조회 (UI 표시용)
# =========================

def diagnose(skin_clusters):
    """'shape NOT kept' 이 왜 났는지 알아내기 위한 진단 리포트.

    디포머 체인을 실제 연결 그대로 따라가며 출력하므로, 어느 단계에서 막혔는지 바로 보인다.
    씬은 전혀 건드리지 않는다(읽기 전용).
    """

    lines = []

    if not skin_clusters:
        return ["[Warning] Nothing loaded."]

    for sc in skin_clusters:

        lines.append("--- {0} ---".format(sc))

        try:
            mesh = mesh_of_skin_cluster(sc)
            lines.append("  geometry     : {0} ({1})".format(
                mesh.split("|")[-1] if mesh else "?",
                cmds.nodeType(mesh) if mesh else "?"))

            geo_index = _geometry_index(sc, mesh)
            lines.append("  geo index    : {0}  (input indices {1})".format(
                geo_index, cmds.getAttr(sc + ".input", mi=True)))

            imap = _influence_index_map(sc)
            lines.append("  influences   : {0}  (matrix indices {1})".format(
                len(imap), sorted(imap.keys())))

            # 입력/출력 지오 상태
            for label, getter in (("skin input ", _deformer_input_points),
                                  ("skin output", _deformer_output_points)):
                try:
                    pts = getter(sc, geo_index)
                    lines.append("  {0}  : {1} verts".format(label, len(pts)))
                except GeometryNotMesh as e:
                    lines.append("  {0}  : NOT A MESH ({1})".format(label, e))
                except Exception as e:
                    lines.append("  {0}  : FAILED ({1})".format(label, e))

            # 체인 워크
            lines.append("  chain walk   :")
            cur = _input_geometry_plug(sc, geo_index)
            seen = set()

            for _ in range(64):   # groupParts 가 수십 개 이어지는 리그가 있다
                if cur is None:
                    lines.append("    -> no geometry input plug, STOPPED")
                    break

                src = cmds.listConnections(cur.name(), s=True, d=False, p=True) or []
                if not src:
                    lines.append("    -> {0} has no incoming connection, STOPPED"
                                 .format(cur.name()))
                    break

                node = src[0].split(".")[0]
                lines.append("    <- {0}  [{1}]".format(src[0], cmds.nodeType(node)))

                if node in seen:
                    lines.append("    -> cycle detected, STOPPED")
                    break
                seen.add(node)

                if cmds.nodeType(node) == "mesh":
                    lines.append("    == input shape: {0} ({1} verts)".format(
                        node, cmds.polyEvaluate(node, v=True)))
                    break

                cur = _upstream_geometry_plug(node, src[0])

            # 최종 판정
            try:
                head = _chain_head_shape(sc, geo_index)
                lines.append("  resolved head: {0}".format(head or "NONE"))
            except GeometryNotMesh as e:
                lines.append("  resolved head: NONE ({0})".format(e))

            live, risky = _live_blendshape_targets(mesh) if mesh else ([], [])
            if live:
                lines.append("  live bs tgts : {0}".format(", ".join(live)))
                for node, hot in risky:
                    detail = ", ".join("{0}={1:.3f}".format(n, v) for n, v in hot[:6])
                    if len(hot) > 6:
                        detail += ", ... (+{0} more)".format(len(hot) - 6)
                    lines.append("     !! {0} non-zero weights: {1}".format(node, detail))
                    lines.append("        -> baked offset is cancelled in proportion "
                                 "to these weights; update at neutral (weights 0)")

        except Exception as e:
            lines.append("  [Error] {0}".format(e))

    return lines


def describe(skin_clusters):
    """대상 요약 문자열."""

    if not skin_clusters:
        return "Nothing loaded."

    if len(skin_clusters) == 1:
        sc = skin_clusters[0]
        mesh = mesh_of_skin_cluster(sc)
        infs = cmds.skinCluster(sc, q=True, inf=True) or []
        return "{0}  |  {1}  |  {2} influence(s)".format(
            sc, mesh.split("|")[-1] if mesh else "?", len(infs))

    return "{0} skinCluster(s): {1}".format(
        len(skin_clusters), ", ".join(skin_clusters))
