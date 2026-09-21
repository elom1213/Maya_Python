# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
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
#   2-b) (Keep current shape 모드) 잠긴(user) 버텍스 노멀도 현재 값으로 다시 굽는다.
#      skinCluster 는 deformUserNormals 로 잠긴 노멀을 스킨 행렬과 함께 회전시키므로,
#      1) 에서 변형이 항등이 되는 순간 노멀만 rest 로 되돌아간다. 위치는 유지되는데
#      셰이딩만 달라지는 증상이 이것이다. 잠기지 않은 노멀은 위치에서 계산되므로 둔다.
#      ★ **쓰는 방식이 중요하다** - face-vertex 마다 컴포넌트 명령으로 쓰면 마야가
#      메모리와 레퍼런스 편집으로 무너진다(v01.29 가 그랬다). `_bake_normals` 참고.
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
    """지오 플러그의 데이터를 (data, MFnMesh) 로 연다. 메시가 아니면 명확한 예외.

    **data 를 함께 돌려주는 이유**: `MPlug.asMObject()` 가 준 데이터는 그 MObject 가
    살아 있는 동안만 유효하다. `_mesh_from_plug(plug).getPoints()` 처럼 MObject 를
    지역 변수로만 두면, 함수가 반환되는 순간 데이터가 풀려 쓰레기 값(1e19 같은 수)을
    읽을 수 있다. 호출부가 data 를 붙들고 있다가 다 읽은 뒤에 놓아야 한다.
    """

    data = plug.asMObject()

    if data.isNull() or not data.hasFn(om.MFn.kMeshData):
        raise GeometryNotMesh(
            "{0} is not polygon mesh data (got {1})".format(what, data.apiTypeStr))

    return data, om.MFnMesh(data)


def _output_geometry_plug(deformer, index=0):
    """<deformer>.outputGeometry[index] 플러그."""
    fn = om.MFnDependencyNode(_depend_node(deformer))
    return fn.findPlug("outputGeometry", False).elementByLogicalIndex(index)


def _deformer_input_points(deformer, index=0):
    """디포머가 실제로 받는 입력 지오의 포인트 (상위 디포머 결과가 반영된 값)."""
    plug = _input_geometry_plug(deformer, index)
    data, fn = _mesh_from_plug(plug, "{0}.input[{1}]".format(deformer, index))
    points = fn.getPoints(om.MSpace.kObject)
    del fn, data                     # 다 읽은 뒤에 놓는다 (위 주석 참고)
    return points


def _deformer_output_points(deformer, index=0):
    """디포머가 내보내는 출력 지오의 포인트.

    화면의 shape 을 읽으면 하류 디포머까지 섞이므로, 반드시 이 디포머의 출력을 읽는다.
    """
    plug = _output_geometry_plug(deformer, index)
    data, fn = _mesh_from_plug(
        plug, "{0}.outputGeometry[{1}]".format(deformer, index))
    points = fn.getPoints(om.MSpace.kObject)
    del fn, data
    return points


# =========================
# 버텍스 노멀 (잠긴 노멀 유지)
# =========================
#
# skinCluster 는 `deformUserNormals` 가 켜져 있으면(기본값) **잠긴(user) 노멀을 스킨
# 행렬로 같이 회전시킨다.** 그래서 bindPreMatrix 를 현재 포즈로 바꿔 스킨 변형이 항등이
# 되는 순간, 회전이 사라지고 노멀이 Orig 셰이프에 저장된 rest 노멀로 되돌아간다.
# 위치는 pnts 에 구워서 유지되는데 노멀만 튀는 이유가 이것이다 (mayapy 로 확인).
#
# 잠기지 않은 노멀은 위치에서 다시 계산되므로 손댈 필요가 없다 — 위치가 같으면 노멀도
# 같다(확인 완료). 따라서 **잠긴 노멀 중 실제로 값이 달라진 것만** 다시 굽는다.


def _is_referenced(node):
    """참조된 노드인가.

    참조 메시에 노멀을 쓰면 **face-vertex 마다 레퍼런스 편집**이 생긴다 — API 로 쓰든
    명령으로 쓰든 마찬가지다(실측: face-vertex 89,700 개 -> 편집 131,698 개).
    """
    try:
        return bool(cmds.referenceQuery(node, isNodeReferenced=True))
    except Exception:
        return False


def _face_ids(counts):
    """면마다 꼭짓점 수가 담긴 배열 -> face-vertex 평탄 순서의 면 번호."""
    faces = []
    for face, count in enumerate(counts):
        faces.extend([face] * count)
    return faces


def _deformer_output_state(deformer, index=0, with_normals=True):
    """디포머 출력 메시를 **한 번만 당겨** 포인트와 노멀을 함께 읽는다.

    디포머 출력 플러그를 당기는 것(`plug.asMObject()`)은 **스킨 평가를 강제한다.**
    v01.29 는 노멀 때문에 이 당김을 세 번 더 했다(갱신 전 · 갱신 후 · 되읽기).
    포인트와 노멀은 **같은 메시 데이터**에서 나오므로 한 번에 읽고, 갱신 뒤 재확인은
    헤드 셰이프만 본다 — 당김이 v01.28 과 똑같이 **입력 1 · 출력 1** 로 돌아왔다.
    (마야가 죽던 원인은 이 읽기가 아니라 **쓰기 방식**이었다 - `_bake_normals` 참고.)

    반환: `(points, normals)` — `normals` 는 `with_normals` 일 때만이고
          `(faces, vertices, ids, values, data)` 꼴이다(앞의 셋은 face-vertex 평탄 순서).

    ★ **`values` 와 함께 `data`(메시 데이터 MObject)를 들고 나간다.** `getNormals()` 가
    준 배열은 그 데이터가 살아 있는 동안만 유효해서, 데이터를 놓고 나면 뒤이은
    `setAttr`(bindPreMatrix · pnts) 가 버퍼를 재활용하며 **값이 조용히 뒤바뀐다** —
    실제로 노멀이 이웃 face-vertex 값으로 밀려 들어갔다(v01.30 에서 잡음).
    값을 파이썬 튜플 수십만 개로 펴는 대신 데이터를 붙들면 메모리도 안 는다.
    """

    plug = _output_geometry_plug(deformer, index)
    data, fn = _mesh_from_plug(
        plug, "{0}.outputGeometry[{1}]".format(deformer, index))

    points = fn.getPoints(om.MSpace.kObject)

    normals = None
    if with_normals:
        counts, vertices = fn.getVertices()
        _n_counts, ids = fn.getNormalIds()
        normals = (_face_ids(counts), list(vertices), list(ids),
                   fn.getNormals(om.MSpace.kObject), data)

    del fn
    return points, normals


def _head_normal_state(shape):
    """체인 헤드 셰이프의 face-vertex 별 (잠금 여부, 노멀 인덱스, 노멀).

    **디포머를 돌리지 않는다** — 셰이프가 들고 있는 데이터를 그대로 읽을 뿐이다.
    갱신이 끝나면 스킨 출력 노멀이 곧 이 값이 되므로, "무엇이 달라질지" 는 이것과
    스킨 출력을 견주면 알 수 있다. 갱신 후에 출력을 다시 당길 필요가 없다.

    잠긴 노멀만 다시 구워야 한다. 안 잠긴 것까지 쓰면 **그 자리에서 잠겨**, 이후 디폼에
    노멀이 따라 돌지 않는 메시가 된다(노멀을 쓰는 일은 곧 잠그는 일이다).
    """

    fn = om.MFnMesh(_dag_path(shape))
    _counts, ids = fn.getNormalIds()
    values = fn.getNormals(om.MSpace.kObject)

    cache = {}
    flags = []
    for i in ids:
        if i not in cache:
            cache[i] = fn.isNormalLocked(i)
        flags.append(cache[i])

    # fn 도 함께 돌려준다 - 위 `_deformer_output_state` 와 같은 이유로, 이 함수가
    # 반환된 뒤에도 `values` 가 가리키는 데이터가 살아 있어야 한다.
    return flags, list(ids), values, fn


def _vertex_ranges(shape, vertices, limit=4000):
    """버텍스 번호들을 `shape.vtx[a:b]` 로 묶는다. 너무 잘게 갈라지면 None.

    연속된 번호는 한 덩어리로 묶이므로, 메시 대부분을 쓸 때는 컴포넌트가 몇 개 안 된다.
    """
    out = []
    ordered = sorted(set(vertices))
    if not ordered:
        return out

    start = prev = ordered[0]
    for v in ordered[1:]:
        if v == prev + 1:
            prev = v
            continue
        out.append((start, prev))
        start = prev = v
        if len(out) > limit:
            return None
    out.append((start, prev))

    return ["{0}.vtx[{1}]".format(shape, a) if a == b
            else "{0}.vtx[{1}:{2}]".format(shape, a, b) for a, b in out]


def _snapshot_normals_for_undo(shape, vertices):
    """노멀 값을 undo 큐에 남기는 **싼 명령 하나**.

    `MFnMesh` 로 쓴 노멀은 undo 에 안 올라간다. 그런데 `polyNormalPerVertex -freezeNormal`
    을 **먼저** 한 번 돌려 두면(이미 잠긴 노멀에는 값이 안 바뀌는 no-op 이다) 마야가 그
    시점의 노멀 데이터를 undo 레코드에 담아 둔다. 그 뒤의 API 쓰기는 큐에 없지만,
    Ctrl+Z 가 이 명령을 되돌리면서 **옛 노멀이 통째로 복구된다**(실측 1,560/1,560).

    컴포넌트를 `vtx[a:b]` 로 묶어 넘기므로 명령 하나에 인자 몇 개뿐이다 — v01.29 처럼
    face-vertex 마다 값을 실어 보내는 것과는 비용이 전혀 다르다.

    **쓸 버텍스만** 건다. `vtx[*]` 로 걸면 잠기지 않은 노멀까지 그 자리에서 잠긴다.
    """
    comps = _vertex_ranges(shape, vertices)
    if not comps:
        return False
    try:
        cmds.polyNormalPerVertex(*comps, freezeNormal=True)
        return True
    except Exception:
        return False


def _bake_normals(shape, faces, vertices, values, vertex_fv_count):
    """face-vertex 별 노멀을 shape 에 다시 쓴다. 쓴 개수를 돌려준다.

    ★ **`MFnMesh` 로 쓴다. 컴포넌트 명령(`polyNormalPerVertex`)으로 쓰면 안 된다** —
    v01.29 가 마야를 내린 이유다(실측).

      | face-vertex 359,400 장 메시 하나 | polyNormalPerVertex | MFnMesh |
      |---|---|---|
      | 시간           | 6.3 초        | 0.2 초 |
      | 마야 메모리     | **+1.2 GB**   | 늘지 않음 |

      undo 레코드가 face-vertex 하나에 3 KB 넘게 붙는다. 캐릭터 한 벌이면 수 GB 다.

      **참조(reference)된 리그에서는 더 나쁘다** — face-vertex 89,700 개에
      **레퍼런스 편집 131,698 개**가 생겼다(노멀을 안 쓰면 145 개). 편집 목록은 그 뒤
      모든 조작과 저장에서 다시 훑이므로 씬이 통째로 못 쓰게 된다.

    **대신 undo 에 안 올라간다** — 호출부가 그 사실을 로그로 알린다.
    `mesh.n[]` 은 파일로 저장될 때의 표현일 뿐이라 setAttr 해도 평가에 반영되지 않고,
    `normalPerVertex...vertexNormalXYZ` 구간 쓰기는 한 버텍스의 face-vertex 를 하나로
    뭉개 하드 엣지(split normal)를 잃는다(둘 다 확인).

    ── 두 가지로 나눠 쓰는 이유 ──────────────────────────────────────────────
    한 버텍스의 face-vertex 가 **전부 같은 값**이면 `setVertexNormals` 로 쓴다.
    `setFaceVertexNormals` 로 쓰면 공유돼 있던 노멀이 **쪼개져**(28 -> 56) 메시가
    괜히 무거워진다. 값이 갈리는(하드 엣지) 자리만 face-vertex 단위로 쓴다.
    """

    if not faces:
        return 0

    # 버텍스별로 모은다
    by_vertex = {}
    for k in range(len(faces)):
        by_vertex.setdefault(vertices[k], []).append(k)

    vtx_list, vtx_values = [], om.MVectorArray()
    fv_faces, fv_verts, fv_values = [], [], om.MVectorArray()

    for vertex, items in by_vertex.items():
        first = values[items[0]]
        same = all(abs(values[k].x - first.x) < 1e-6
                   and abs(values[k].y - first.y) < 1e-6
                   and abs(values[k].z - first.z) < 1e-6 for k in items)

        if same and len(items) == vertex_fv_count.get(vertex, -1):
            vtx_list.append(vertex)
            vtx_values.append(first)
            continue

        for k in items:
            fv_faces.append(faces[k])
            fv_verts.append(vertices[k])
            fv_values.append(values[k])

    # undo 를 위한 스냅샷을 먼저 남긴다 (위 함수 주석 참고).
    undoable = _snapshot_normals_for_undo(shape, vertices)

    fn = om.MFnMesh(_dag_path(shape))

    if vtx_list:
        fn.setVertexNormals(vtx_values, vtx_list, om.MSpace.kObject)
    if fv_faces:
        fn.setFaceVertexNormals(fv_values, fv_faces, fv_verts, om.MSpace.kObject)

    # ★ 하류에 알린다. face-vertex 마다 노멀을 주면 공유돼 있던 노멀이 쪼개지는데,
    #   API 로 쓰면 **그 사실이 디포머 출력까지 가지 않는다** — skinCluster 출력이
    #   옛 노멀 공유 구조를 들고 있어 값이 이웃과 뒤섞인다(실측: 40 개 중 26 개가 틀렸다).
    #   명령으로 쓸 때는 명령이 알아서 해 주던 일이다.
    cmds.dgdirty(shape)

    return len(faces) if undoable else -len(faces)


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

def update_bind_pose(skin_clusters, keep_shape=True, rebuild_dag_pose=True,
                     keep_normals=True):
    """현재 조인트 포즈를 새 바인드 포즈로 만든다.

    keep_shape=True  : 지금 보이는(변형된) 형상을 그대로 유지한 채 rest 로 굳힌다.
    keep_shape=False : bindPreMatrix 만 갱신 → 메시는 원래 rest 형상으로 스냅백한다
                       (Move Skinned Joints Tool 로 조인트를 옮긴 것과 같은 결과).
    keep_normals     : 잠긴(user) 버텍스 노멀도 함께 굽는다 (keep_shape 일 때만 뜻이 있다).
                       끄면 노멀은 rest 로 돌아간다 — 셰이딩이 달라진다.

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
                out_normals = None
                head_state = None

                if keep_shape:
                    try:
                        skin_in = _deformer_input_points(sc, geo_index)
                        # 출력은 **한 번만** 당긴다 - 포인트와 노멀을 같은 데이터에서.
                        skin_out, out_normals = _deformer_output_state(
                            sc, geo_index, with_normals=keep_normals)

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

                                # 잠긴(user) 노멀은 스킨 행렬을 따라 돌고 있었다.
                                # 바인드를 갱신하면 그 회전이 사라진다. 헤드 셰이프를
                                # **디포머를 돌리지 않고** 읽어 두면, 갱신 뒤에 무엇이
                                # 달라질지 지금 다 알 수 있다.
                                if keep_normals:
                                    head_state = _head_normal_state(head)

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
                        out_normals = None
                        head_state = None
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

                    # ---- 2-b) 잠긴 노멀도 현재 값으로 다시 굽는다 ------------
                    if keep_normals and out_normals and head_state:
                        count = _restore_locked_normals(head, out_normals,
                                                        head_state, messages)
                        if count:
                            if count > 0:
                                messages.append(
                                    "[Info] {0}: {1} locked vertex normal(s) re-baked "
                                    "so the shading stays as it was.".format(sc, count))
                            else:
                                messages.append(
                                    "[Warning] {0}: {1} locked vertex normal(s) "
                                    "re-baked, but they could not be put on the undo "
                                    "queue - Ctrl+Z will bring the joints back and "
                                    "leave these normals. Run Update Bind Pose again "
                                    "after an undo.".format(sc, -count))

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


def _restore_locked_normals(head, out_normals, head_state, messages):
    """바인드 갱신으로 rest 로 돌아갈 잠긴 노멀을, 갱신 전 값으로 다시 굽는다.

    위치는 pnts 에 굽는 것으로 유지되지만, 잠긴(user) 노멀은 skinCluster 가
    `deformUserNormals` 로 회전시키고 있던 것이라 스킨 변형이 항등이 되는 순간
    헤드(Orig) 셰이프의 rest 노멀로 돌아간다. 그래서 여기서 따로 굽는다.

    **갱신 전에 다 판단한다** — 갱신이 끝나면 스킨 출력 노멀은 헤드 값과 같아지므로,
    "무엇이 달라질지" 는 (스킨 출력 vs 헤드) 로 알 수 있다. v01.29 는 갱신 뒤에 출력을
    다시 당겨 견줬는데, 디포머 출력을 그렇게 여러 번 당길 이유가 없다(v01.30).

    잠기지 않은 노멀은 위치에서 계산되므로 손대지 않는다. 잠긴 것 중에서도 **실제로
    달라질 face-vertex 만** 쓴다 — 조인트를 옮기기만 한 경우처럼 노멀이 그대로면
    아무것도 건드리지 않는다.

    반환: 쓴 face-vertex 수.
    """

    faces, vertices, out_ids, out_values, _data = out_normals
    flags, head_ids, head_values, _fn = head_state

    if len(flags) != len(faces):
        messages.append(
            "[Warning] {0}: the input shape has {1} face-vertices but the skin output "
            "has {2}, so locked vertex normals were left untouched.".format(
                head.split("|")[-1], len(flags), len(faces)))
        return 0

    # 쓸 것만 모은다. face-vertex 가 수십만 개일 수 있으므로 중간 목록을 늘리지 않는다.
    write_faces, write_verts = [], []
    write_values = om.MVectorArray()

    for i, locked in enumerate(flags):
        if not locked:
            continue
        a = out_values[out_ids[i]]
        b = head_values[head_ids[i]]
        if (abs(a.x - b.x) > 1e-5 or abs(a.y - b.y) > 1e-5
                or abs(a.z - b.z) > 1e-5):
            write_faces.append(faces[i])
            write_verts.append(vertices[i])
            write_values.append(om.MVector(a.x, a.y, a.z))

    if not write_faces:
        return 0

    # ★ 참조된 셰이프에는 쓰지 않는다. 마야는 참조 메시의 노멀 변경을 **face-vertex 마다
    #   레퍼런스 편집**으로 보존한다 — face-vertex 89,700 개에 편집 131,698 개가 생겼다
    #   (노멀을 안 쓰면 145 개). 편집 목록은 그 뒤 모든 조작·저장에서 다시 훑이므로
    #   씬이 통째로 못 쓰게 된다. API 로 쓰든 명령으로 쓰든 마찬가지다(둘 다 실측).
    if _is_referenced(head):
        messages.append(
            "[Warning] {0} is referenced, so {1} locked vertex normal(s) were left "
            "alone. Writing them there would add about {2:,} reference edits to the "
            "scene - it bloats the file and can bring Maya down. Work in the rig file "
            "(or import the reference) and run again, or turn 'Keep locked vertex "
            "normals' off to stop this check.".format(
                head.split("|")[-1], len(write_faces), int(len(write_faces) * 1.5)))
        return 0

    fv_count = {}
    for v in vertices:
        fv_count[v] = fv_count.get(v, 0) + 1

    written = _bake_normals(head, write_faces, write_verts, write_values, fv_count)

    # 되읽어 확인 — 헤드 셰이프만 다시 읽는다(디포머를 돌리지 않는다).
    try:
        _flags, ids_now, values_now, _fn_now = _head_normal_state(head)
        worst = 0.0
        if len(ids_now) == len(head_ids):
            k = 0
            for i, locked in enumerate(flags):
                if not locked:
                    continue
                a = out_values[out_ids[i]]
                b = head_values[head_ids[i]]
                if (abs(a.x - b.x) > 1e-5 or abs(a.y - b.y) > 1e-5
                        or abs(a.z - b.z) > 1e-5):
                    got = values_now[ids_now[i]]
                    worst = max(worst, abs(a.x - got.x), abs(a.y - got.y),
                                abs(a.z - got.z))
                    k += 1
        if worst > 1e-3:
            messages.append(
                "[Warning] {0}: vertex normals still differ by up to {1:.4f} after "
                "re-baking.".format(head.split("|")[-1], worst))
    except Exception:
        pass

    return written


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

            # 잠긴(user) 노멀 — 있으면 바인드 갱신 때 따로 구워야 한다
            try:
                fn = om.MFnMesh(_dag_path(mesh))
                locked = sum(1 for i in range(fn.numNormals) if fn.isNormalLocked(i))
                deform = (cmds.getAttr(sc + ".deformUserNormals")
                          if cmds.attributeQuery("deformUserNormals", node=sc,
                                                 exists=True) else "n/a")
                lines.append("  locked norms : {0} / {1}  (deformUserNormals = {2})"
                             .format(locked, fn.numNormals, deform))
                if locked:
                    lines.append("     -> these rotate with the skin, so they are "
                                 "re-baked when the shape is kept")
            except Exception as e:
                lines.append("  locked norms : FAILED ({0})".format(e))

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
