# -*- coding: utf-8 -*-
"""
mirror_manager - Mirror 탭 로직.

리스트업된 오브젝트(와 그 자식들)를 통째로 복제해 **반대쪽 리그**를 만든다.
이름은 공용 규칙(`Framework/rules/mirror_tokens.json`)의 좌/우 토큰으로 바꾸고,
계층 안에서 유지되어야 할 관계를 규칙대로 다시 세운다:

  - 스킨 웨이트 (skinCluster)  : 인플루언스를 반대쪽 조인트로 갈아끼우고 웨이트 그대로
  - 컨스트레인트               : 드라이버/드리븐을 반대쪽 짝으로 다시 건다
  - 클러스터                   : 핸들·웨이트를 반대쪽으로

**스코프 규칙**: 미러 대상은 리스트에 올라온 오브젝트와 그 자손뿐이다. 스코프 밖 노드는
복제하지 않고 *그대로 참조*한다 - 스코프 밖 메시에 스킨이 걸려 있어도 그 메시는 복제되지
않고, 스코프 밖 조인트가 드라이버면 미러된 컨스트레인트도 같은 조인트를 본다(센터 처리).

--------------------------------------------------------------------------
미러 수학
--------------------------------------------------------------------------
반사 평면은 YZ / XY / XZ 중 하나이고, 각 평면의 **법선 축**만 알면 된다
(YZ -> X, XZ -> Y, XY -> Z). 월드 행렬 M 의 행 0~2 가 로컬 축, 행 3 이 위치다.

  Orientation : 축 3개는 그대로, 위치만 법선 성분을 뒤집는다.
  Behavior    : 위치는 같고, 각 축 행에서 **법선 성분만 남기고 나머지 둘을 뒤집는다**.

Behavior 식은 "반사한 뒤 세 축을 모두 뒤집기"(= -(M·S))와 같다. 세 축을 모두 뒤집어야
행렬식이 양수로 돌아와 오른손 좌표계가 유지되고, 같은 로컬 회전값이 좌우 대칭 동작을
만든다. Maya 2024 의 `mirrorJoint -mirrorYZ -mirrorBehavior` 결과와 행렬 단위로 일치하는
것을 mayapy 로 확인했다(`mirrorBehavior=False` 는 회전이 원본과 완전히 동일).

메시는 사정이 다르다. 위 두 방식 모두 **강체 회전**이라 지오메트리는 회전만 하고 뒤집히지
않는다(왼쪽 신발이 오른쪽에서도 왼쪽 신발로 보인다). 그래서 메시는 트랜스폼을 위 규칙대로
놓은 뒤, 오브젝트 공간에서 보정 행렬 `C = (M·S)·M_new^-1` 로 정점을 한 번 더 반사하고
노멀을 뒤집는다. 결과의 월드 형상은 원본의 정확한 거울상이 된다.

조인트는 회전을 `rotate` 가 아니라 `jointOrient` 에 넣는다(rotate 0). `xform -ws -m` 는
회전을 `rotate` 에 넣으므로, 그 뒤에 로컬 행렬을 다시 읽어 `jointOrient` 로 옮긴다.

UI 비의존: 위젯에서 읽은 list/str/bool 값만 받는다. (app/core <-> app/ui 분리)
"""

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core import maya_skin
from Framework.core.mirror_tokens import MirrorTokenStore


# 반사 평면. 값은 UI 라디오의 식별자로도 쓴다.
PLANE_YZ = "yz"
PLANE_XY = "xy"
PLANE_XZ = "xz"

MIRROR_PLANES = (
    ("YZ", PLANE_YZ),
    ("XY", PLANE_XY),
    ("XZ", PLANE_XZ),
)

# 평면 -> 그 평면의 법선 축 인덱스(0=X, 1=Y, 2=Z).
_PLANE_NORMAL = {PLANE_YZ: 0, PLANE_XZ: 1, PLANE_XY: 2}

# 미러 방식.
MODE_BEHAVIOR = "behavior"
MODE_ORIENTATION = "orientation"

MIRROR_MODES = (
    ("Behavior", MODE_BEHAVIOR),
    ("Orientation", MODE_ORIENTATION),
)

# 토큰을 못 찾은 노드에 붙이는 접미사('Disable token check' 일 때만 쓰인다).
NO_TOKEN_SUFFIX = "_mir"

# 토큰이 없어 미러를 중단했을 때, 그 오브젝트들을 담아 두는 세트 이름.
# 이름을 고정해 두고 **비워서 재사용**한다(같은 이름으로 sets 를 또 만들면
# mirror_noToken_set1, ...2 로 쌓인다). 로그에서 이름을 찾아 헤매지 않고 바로 고를 수 있다.
MISSING_TOKEN_SET = "mirror_noToken_set"

# 이름 목록을 로그에 찍을 때 한 줄에 몇 개씩 묶을지.
_NAMES_PER_LINE = 4


class MissingTokenError(RuntimeError):
    """규칙에 맞는 좌/우 토큰이 없는 오브젝트가 있어 미러를 중단했다.

    nodes    : 토큰이 없는 오브젝트(롱네임)
    set_name : 그 오브젝트들을 담은 세트 이름(만들지 못했으면 None)
    report   : 중단 전까지 모은 로그 줄(이름 목록 포함)

    예외로 던지면 `mirror()` 의 반환값(warnings)이 통째로 사라져서 **이름이 로그에
    안 남는다.** 그래서 보고할 내용을 예외에 실어 보낸다.
    """

    def __init__(self, message, nodes, set_name, report):
        super(MissingTokenError, self).__init__(message)
        self.nodes = list(nodes)
        self.set_name = set_name
        self.report = list(report)


# 다시 세울 컨스트레인트 타입 -> cmds 명령.
_CONSTRAINT_FN = {
    "parentConstraint": cmds.parentConstraint,
    "pointConstraint": cmds.pointConstraint,
    "orientConstraint": cmds.orientConstraint,
    "scaleConstraint": cmds.scaleConstraint,
    "aimConstraint": cmds.aimConstraint,
    "poleVectorConstraint": cmds.poleVectorConstraint,
    "geometryConstraint": cmds.geometryConstraint,
    "normalConstraint": cmds.normalConstraint,
    "tangentConstraint": cmds.tangentConstraint,
}

# 타입별 (skip 플래그 이름, 검사할 채널). 어떤 채널을 실제로 구동하는지는 씬 연결로 판정해
# 구동하지 않는 축을 skip 으로 넘긴다(원본의 skip 설정을 그대로 재현하는 유일한 방법).
_SKIP_CHANNELS = {
    "parentConstraint": (("skipTranslate", "translate"), ("skipRotate", "rotate")),
    "pointConstraint": (("skip", "translate"),),
    "orientConstraint": (("skip", "rotate"),),
    "scaleConstraint": (("skip", "scale"),),
    "aimConstraint": (("skip", "rotate"),),
    "normalConstraint": (("skip", "rotate"),),
    "tangentConstraint": (("skip", "rotate"),),
    "geometryConstraint": (("skip", "translate"),),
}

# maintainOffset 플래그가 없는 타입.
_NO_MAINTAIN_OFFSET = {
    "poleVectorConstraint", "geometryConstraint",
    "normalConstraint", "tangentConstraint",
}


# ==================================================================
# 이름 / 노드 헬퍼
# ==================================================================

def _long(node):
    """노드의 롱네임(DAG 풀패스). 없으면 None."""
    got = cmds.ls(node, long=True) or []
    return got[0] if got else None


def _short(node):
    """DAG 경로를 뗀 짧은 이름(네임스페이스는 남긴다)."""
    return node.split("|")[-1]


def _uuid(node):
    got = cmds.ls(node, uuid=True) or []
    return got[0] if got else None


def _by_uuid(uuid):
    got = cmds.ls(uuid, long=True) or []
    return got[0] if got else None


def _same_node(a, b):
    """이름이 달라도(짧은 이름 / 풀패스) 같은 노드인지 UUID 로 판정."""
    if a == b:
        return True
    ua, ub = _uuid(a), _uuid(b)
    return bool(ua) and ua == ub


def _is_constraint(node):
    """*Constraint 노드인가. 타입 상속으로 판정한다(이름 규칙에 기대지 않는다)."""
    return "constraint" in (cmds.nodeType(node, inherited=True) or [])


def _shape_of(node, type_):
    """node 아래의 (중간이 아닌) 첫 shape. 없으면 None."""
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True,
                                type=type_, noIntermediate=True) or []
    return shapes[0] if shapes else None


def _deformable_shape(node):
    """cluster/skinCluster 가 붙을 수 있는 shape 하나. (mesh -> nurbsCurve -> nurbsSurface)"""
    for type_ in ("mesh", "nurbsCurve", "nurbsSurface"):
        shape = _shape_of(node, type_)
        if shape:
            return shape
    return None


def _component_count(shape):
    """shape 의 웨이트 성분 개수(메시 정점 / 커브·서피스 CV)."""
    type_ = cmds.nodeType(shape)
    if type_ == "mesh":
        return int(cmds.polyEvaluate(shape, vertex=True))
    if type_ == "nurbsCurve":
        spans = cmds.getAttr(shape + ".spans")
        degree = cmds.getAttr(shape + ".degree")
        form = cmds.getAttr(shape + ".form")
        return int(spans if form == 2 else spans + degree)
    if type_ == "nurbsSurface":
        cvs = cmds.ls(shape + ".cv[*][*]", flatten=True) or []
        return len(cvs)
    return 0


# ==================================================================
# 미러 행렬
# ==================================================================

def _mirror_matrix(matrix, axis, behavior):
    """월드 행렬 16개 값을 미러한다.

    axis     : 반사 평면의 법선 축 인덱스(0/1/2)
    behavior : True 면 Behavior, False 면 Orientation
    """
    out = list(matrix)
    if behavior:
        for row in range(3):
            for col in range(3):
                if col != axis:
                    out[row * 4 + col] = -out[row * 4 + col]
    out[12 + axis] = -out[12 + axis]
    return out


def _reflected_matrix(matrix, axis):
    """진짜 반사(M·S). 행렬식이 음수라 트랜스폼으로는 쓸 수 없고, 메시 정점 보정에만 쓴다."""
    out = list(matrix)
    for row in range(4):
        out[row * 4 + axis] = -out[row * 4 + axis]
    return out


def _unlock_transform(node):
    """t/r/s(조인트는 jointOrient 까지) 잠금을 잠시 푼다. 반환: 되돌릴 plug 목록.

    **스킨된 메시는 마야가 트랜스폼 채널을 잠가 두고, 복제본도 잠긴 채로 나온다.**
    (히스토리를 지워도 잠금은 남는다.) 그런데 `cmds.xform` 은 잠긴 채널에 대해
    에러도 없이 **조용히 아무것도 하지 않는다** - 미러가 소리 없이 실패해서, 메시만
    제자리에 남고 지오메트리 보정이 그걸 가려 버린다(월드 형상은 맞아 보인다).
    그래서 놓기 직전에만 풀고 원래 상태로 되돌린다.
    """
    attrs = ["translate", "rotate", "scale"]
    if cmds.attributeQuery("jointOrient", node=node, exists=True):
        attrs.append("jointOrient")

    restore = []
    for attr in attrs:
        for plug in [node + "." + attr] + [node + "." + attr + axis for axis in "XYZ"]:
            if not cmds.objExists(plug):
                continue
            if cmds.getAttr(plug, lock=True):
                cmds.setAttr(plug, lock=False)
                restore.append(plug)
    return restore


def _apply_world_matrix(node, matrix):
    """월드 행렬을 적용한다. 조인트는 회전을 jointOrient 로 옮긴다(rotate 0).

    적용 뒤 결과를 되읽어 확인한다. 잠김/연결된 채널은 `xform` 이 조용히 넘어가므로,
    확인하지 않으면 어디가 안 놓였는지 알 길이 없다.
    """
    restore = _unlock_transform(node)
    try:
        cmds.xform(node, worldSpace=True, matrix=list(matrix))
        if cmds.nodeType(node) == "joint":
            _bake_rotate_into_joint_orient(node)
    finally:
        for plug in restore:
            try:
                cmds.setAttr(plug, lock=True)
            except Exception:
                pass

    result = cmds.xform(node, query=True, worldSpace=True, matrix=True)
    if max(abs(a - b) for a, b in zip(result, matrix)) > 1e-4:
        raise RuntimeError("transform channels are locked or connected")


def _bake_rotate_into_joint_orient(joint):
    """`xform` 이 rotate 에 넣은 회전을 jointOrient 로 옮기고 rotate 를 0 으로.

    로컬 회전 = [rotateAxis][rotate][jointOrient] 이므로, rotate = 0 으로 두려면
    jointOrient = rotateAxis^-1 * (로컬 회전 전체) 다. jointOrient 의 회전 순서는
    항상 XYZ 라서 rotateOrder 와 무관하다.
    """
    local = om.MMatrix(cmds.xform(joint, query=True, matrix=True))
    rot = om.MTransformationMatrix(local).rotation(asQuaternion=True).asMatrix()

    ra = cmds.getAttr(joint + ".rotateAxis")[0]
    ra_matrix = om.MEulerRotation(
        [math.radians(v) for v in ra], om.MEulerRotation.kXYZ).asMatrix()

    jo = om.MTransformationMatrix(ra_matrix.inverse() * rot).rotation(asQuaternion=False)
    jo.reorderIt(om.MEulerRotation.kXYZ)

    cmds.setAttr(joint + ".jointOrient",
                 math.degrees(jo.x), math.degrees(jo.y), math.degrees(jo.z))
    cmds.setAttr(joint + ".rotate", 0.0, 0.0, 0.0)


# ==================================================================
# 스코프 / 이름 계획
# ==================================================================

def _resolve_roots(roots, warnings):
    """리스트업된 이름을 롱네임으로 풀고, 중복과 '다른 루트의 자손' 을 걷어낸다."""
    resolved = []
    for item in roots:
        name = (item or "").strip()
        if not name:
            continue
        if "." in name:
            warnings.append("'{0}' is a component - only objects can be mirrored.".format(name))
            continue
        path = _long(name)
        if not path:
            warnings.append("'{0}' does not exist.".format(name))
            continue
        if path not in resolved:
            resolved.append(path)

    final = []
    for path in resolved:
        parent = next((other for other in resolved
                       if other != path and path.startswith(other + "|")), None)
        if parent:
            warnings.append(
                "'{0}' is already inside '{1}' - listed twice, mirrored once.".format(
                    _short(path), _short(parent)))
            continue
        final.append(path)
    return final


def _hierarchy(root):
    """root 와 그 자손 transform 을 **부모 -> 자식** 순으로. 컨스트레인트 노드는 뺀다."""
    out = []

    def walk(node):
        out.append(node)
        for child in cmds.listRelatives(node, children=True, fullPath=True,
                                        type="transform") or []:
            if _is_constraint(child):
                continue
            walk(child)

    walk(root)
    return out


def _plan_names(nodes, token_pairs):
    """스코프 노드마다 미러 이름을 정한다.

    반환: (names, missing)
        names   : {롱네임: 미러된 짧은 이름}
        missing : 토큰을 못 찾은 노드 목록(경고 대상)
    """
    names = {}
    missing = []
    for node in nodes:
        mirrored, _token = MirrorTokenStore.mirror_node_name(node, token_pairs)
        if mirrored is None:
            missing.append(node)
            mirrored = _short(node) + NO_TOKEN_SUFFIX
        names[node] = mirrored
    return names, missing


def _name_lines(nodes, per_line=_NAMES_PER_LINE):
    """이름 목록을 로그용 줄로 묶는다.

    하나씩 한 줄이면 수백 줄이 쏟아지고, 한 줄에 다 넣으면 잘려 읽을 수 없다.
    """
    shorts = [_short(node) for node in nodes]
    return ["  " + ", ".join(shorts[i:i + per_line])
            for i in range(0, len(shorts), per_line)]


def _make_missing_token_set(nodes, warnings):
    """토큰이 없는 오브젝트를 세트 하나로 묶는다. 반환: 세트 이름 또는 None.

    이름(`MISSING_TOKEN_SET`)이 이미 있으면 **비우고 다시 채운다** - 같은 이름으로
    `cmds.sets` 를 또 부르면 `..._set1`, `..._set2` 로 쌓여서, 정작 어느 것이 방금
    것인지 알 수 없게 된다. 노드를 그대로 두므로 세트를 참조하던 것도 안 끊긴다.
    """
    name = MISSING_TOKEN_SET
    try:
        if cmds.objExists(name) and cmds.nodeType(name) == "objectSet":
            cmds.sets(clear=name)
            cmds.sets(nodes, addElement=name)
            return name
        return cmds.sets(nodes, name=name)
    except Exception as e:
        warnings.append("Could not collect them in a set ({0}).".format(e))
        return None


def _mirror_name(name, token_pairs):
    """부수 노드(skinCluster / cluster / constraint) 이름용. 토큰이 없으면 접미사."""
    mirrored, _token = MirrorTokenStore.opposite_name(_short(name), token_pairs)
    return mirrored or (_short(name) + NO_TOKEN_SUFFIX)


# ==================================================================
# 복제
# ==================================================================

def _duplicate_root(root):
    """root 계층을 복제하고, 다시 만들 것들(컨스트레인트·디포머 흔적)을 걷어낸다."""
    dup = _long(cmds.duplicate(root, renameChildren=True, upstreamNodes=False)[0])

    # 복제본 안의 컨스트레인트 노드 - 뒤에서 규칙대로 다시 만든다.
    junk = [n for n in (cmds.listRelatives(dup, allDescendents=True, fullPath=True,
                                           type="transform") or [])
            if _is_constraint(n)]
    if _is_constraint(dup):
        junk.append(dup)
    if junk:
        cmds.delete(junk)

    # 복제로 딸려온 clusterHandle 셰이프는 아무 클러스터에도 연결되지 않은 껍데기다.
    handles = cmds.listRelatives(dup, allDescendents=True, fullPath=True,
                                 type="clusterHandle") or []
    handles += cmds.listRelatives(dup, shapes=True, fullPath=True,
                                  type="clusterHandle") or []
    if handles:
        cmds.delete(handles)

    # 복제본에 디포머 히스토리가 남지 않게 한 번 더 정리한다(스킨은 뒤에서 다시 만든다).
    targets = [dup] + (cmds.listRelatives(dup, allDescendents=True, fullPath=True,
                                          type="transform") or [])
    for node in targets:
        try:
            cmds.delete(node, constructionHistory=True)
        except Exception:
            pass

    return _long(dup)


def _pair_hierarchy(orig, dup, pairs):
    """원본/복제본을 같은 순서로 훑어 1:1 로 짝짓는다.

    복제본은 계층이 그대로라 자식 순서가 같다. 이름은 `renameChildren` 때문에 다르므로
    이름이 아니라 **자리**로 맞춘다.
    """
    pairs.append((orig, dup))

    orig_children = [c for c in (cmds.listRelatives(orig, children=True, fullPath=True,
                                                    type="transform") or [])
                     if not _is_constraint(c)]
    dup_children = [c for c in (cmds.listRelatives(dup, children=True, fullPath=True,
                                                   type="transform") or [])
                    if not _is_constraint(c)]

    if len(orig_children) != len(dup_children):
        raise RuntimeError(
            "Duplicate of '{0}' does not match the original hierarchy "
            "({1} vs {2} children).".format(_short(orig), len(orig_children),
                                            len(dup_children)))

    for a, b in zip(orig_children, dup_children):
        _pair_hierarchy(a, b, pairs)


def _rename_dup(dup_uuid, new_short, token_pairs, warnings):
    """복제 노드와 그 shape 의 이름을 미러 이름으로. (경로가 바뀌므로 UUID 로 잡는다)"""
    path = _by_uuid(dup_uuid)
    if not path:
        return
    try:
        path = _long(cmds.rename(path, new_short))
    except Exception as e:
        warnings.append("Rename to '{0}' failed ({1}).".format(new_short, e))
        return

    # 마야는 트랜스폼을 리네임하면 `<transform>Shape*` 셰이프를 **알아서 따라 바꾼다**.
    # 그걸 모르고 셰이프 이름까지 미러하면 이미 맞는 이름을 반대쪽으로 되돌려 버린다
    # (mesh_r_01Shape1 -> mesh_l_01Shape1). 그래서 마야가 손대지 않은 셰이프만 바꾼다.
    for shape in cmds.listRelatives(path, shapes=True, fullPath=True) or []:
        short = _short(shape)
        if short.startswith(new_short):
            continue
        mirrored, token = MirrorTokenStore.opposite_name(short, token_pairs)
        if not token:
            mirrored = new_short + "Shape"
        try:
            cmds.rename(shape, mirrored)
        except Exception:
            pass


# ==================================================================
# 메시 지오메트리 반사
# ==================================================================

def _reflect_mesh(orig, dup, axis, new_matrix, warnings):
    """복제 메시의 정점을 오브젝트 공간에서 반사해 월드 형상을 원본의 거울상으로 만든다.

    트랜스폼은 Behavior/Orientation 규칙대로 이미 놓여 있다(강체 회전이라 형상은 안 뒤집힌다).
    보정 행렬 `C = (M·S)·M_new^-1` 를 정점에 곱하면 월드 결과가 진짜 거울상이 된다.
    행렬식이 음수라 페이스가 뒤집히므로 노멀도 되돌린다.
    """
    shapes = cmds.listRelatives(dup, shapes=True, fullPath=True,
                                type="mesh", noIntermediate=True) or []
    if not shapes:
        return

    src = cmds.xform(orig, query=True, worldSpace=True, matrix=True)
    correction = (om.MMatrix(_reflected_matrix(src, axis))
                  * om.MMatrix(new_matrix).inverse())

    for shape in shapes:
        sel = om.MSelectionList()
        sel.add(shape)
        fn = om.MFnMesh(sel.getDagPath(0))
        points = fn.getPoints(om.MSpace.kObject)
        for i in range(len(points)):
            points[i] = points[i] * correction
        fn.setPoints(points, om.MSpace.kObject)

    try:
        cmds.polyNormal(shapes, normalMode=0, userNormalMode=0,
                        constructionHistory=False)
    except Exception as e:
        warnings.append("Could not flip normals on '{0}' ({1}).".format(_short(dup), e))


# ==================================================================
# 스킨 웨이트
# ==================================================================

def _all_components(shape):
    """shape 의 전체 성분. 반환: (MDagPath, MObject component, count)"""
    sel = om.MSelectionList()
    sel.add(shape)
    dag = sel.getDagPath(0)

    type_ = cmds.nodeType(shape)
    comp_fn = om.MFnSingleIndexedComponent()
    if type_ == "mesh":
        comp = comp_fn.create(om.MFn.kMeshVertComponent)
    elif type_ == "nurbsCurve":
        comp = comp_fn.create(om.MFn.kCurveCVComponent)
    else:
        raise RuntimeError("'{0}' is not a mesh or curve.".format(shape))

    count = _component_count(shape)
    comp_fn.setCompleteData(count)
    return dag, comp, count


def _skin_cluster_of(shape):
    clusters = cmds.ls(cmds.listHistory(shape) or [], type="skinCluster") or []
    return clusters[0] if clusters else None


def _copy_skin(orig, dup, node_map, token_pairs, warnings):
    """원본 메시의 skinCluster 를 복제 메시에 다시 만든다(인플루언스는 반대쪽으로).

    스코프 밖 인플루언스(센터 조인트 등)는 **자기 자신**을 그대로 쓴다.
    반환: 새 skinCluster 이름 또는 None.
    """
    src_shape = _deformable_shape(orig)
    if not src_shape:
        return None
    skin = _skin_cluster_of(src_shape)
    if not skin:
        return None

    dst_shape = _deformable_shape(dup)
    if not dst_shape:
        warnings.append("'{0}' has no deformable shape - skin not copied.".format(_short(dup)))
        return None

    fn = maya_skin.skin_fn(skin)
    src_influences = maya_skin.influence_paths(fn)          # 웨이트 열 순서
    dst_influences = [node_map.get(inf, inf) for inf in src_influences]

    missing = [inf for inf in dst_influences if not cmds.objExists(inf)]
    if missing:
        warnings.append("Influence(s) missing for '{0}': {1}".format(
            _short(dup), ", ".join(_short(m) for m in missing)))
        return None

    new_skin = cmds.skinCluster(
        dst_influences, dst_shape,
        toSelectedBones=True,
        maximumInfluences=cmds.getAttr(skin + ".maxInfluences"),
        obeyMaxInfluences=cmds.getAttr(skin + ".maintainMaxInfluences"),
        skinMethod=cmds.getAttr(skin + ".skinningMethod"),
        normalizeWeights=cmds.getAttr(skin + ".normalizeWeights"),
        name=_mirror_name(skin, token_pairs))[0]

    src_dag, src_comp, src_count = _all_components(src_shape)
    dst_dag, dst_comp, dst_count = _all_components(dst_shape)
    if src_count != dst_count:
        warnings.append("'{0}' component count changed ({1} -> {2}) - weights skipped.".format(
            _short(dup), src_count, dst_count))
        return new_skin

    weights, n_src = fn.getWeights(src_dag, src_comp)

    new_fn = maya_skin.skin_fn(new_skin)
    new_influences = maya_skin.influence_paths(new_fn)
    n_dst = len(new_influences)

    # 소스의 **물리** 열 i -> 타겟의 물리 열. 두 skinCluster 의 인플루언스 순서가 같다는
    # 보장이 없으므로 경로로 다시 찾는다.
    slot = {path: i for i, path in enumerate(new_influences)}
    column = [slot.get(_long(inf), -1) for inf in dst_influences]
    if -1 in column:
        warnings.append("Influence order mismatch on '{0}' - weights skipped.".format(_short(dup)))
        return new_skin

    values = [0.0] * (src_count * n_dst)
    for vtx in range(src_count):
        src_base = vtx * n_src
        dst_base = vtx * n_dst
        for i in range(n_src):
            col = column[i]
            if col >= 0:
                values[dst_base + col] += weights[src_base + i]

    # 쓰는 동안 마야가 정규화로 값을 건드리지 않게 잠시 끈다.
    normalize = cmds.getAttr(new_skin + ".normalizeWeights")
    cmds.setAttr(new_skin + ".normalizeWeights", 0)
    try:
        new_fn.setWeights(dst_dag, dst_comp, maya_skin.weight_indices(n_dst),
                          om.MDoubleArray(values), False)
    finally:
        cmds.setAttr(new_skin + ".normalizeWeights", normalize)

    return new_skin


# ==================================================================
# 클러스터
# ==================================================================

def _cluster_handle(cluster):
    """cluster 를 구동하는 핸들 트랜스폼(weightedNode). 없으면 None."""
    conns = cmds.listConnections(cluster + ".matrix", source=True, destination=False) or []
    return _long(conns[0]) if conns else None


def _geometry_index(geos, indices, shape):
    """디포머가 물고 있는 지오메트리 목록에서 shape 의 **논리** 인덱스를 찾는다."""
    for geo, index in zip(geos or [], indices or []):
        if _same_node(geo, shape):
            return index
    return None


def _copy_clusters(scope, node_map, axis, other_behavior, token_pairs, warnings):
    """스코프 안 지오메트리를 변형하는 cluster 를 반대쪽에 다시 만든다.

    한 cluster 가 여러 지오메트리를 물고 있으면 **하나의 미러 cluster** 로 묶는다.
    핸들이 스코프 안이면 이미 미러된 복제본을 weightedNode 로 쓰고, 스코프 밖이면
    미러 위치에 빈 트랜스폼을 새로 만든다. `bindState=True` 가 핸들의 현재 트랜스폼을
    상쇄해 주므로 생성 직후 형상이 튀지 않는다.
    """
    created = []

    # cluster -> [(원본 shape, 복제 shape), ...]
    grouped = {}
    for orig in scope:
        src_shape = _deformable_shape(orig)
        if not src_shape:
            continue
        dup = node_map.get(orig)
        dst_shape = _deformable_shape(dup) if dup else None
        if not dst_shape:
            continue
        for cluster in cmds.ls(cmds.listHistory(src_shape) or [], type="cluster") or []:
            grouped.setdefault(cluster, []).append((src_shape, dst_shape))

    for cluster in sorted(grouped):
        geo_pairs = grouped[cluster]
        try:
            handle = _cluster_handle(cluster)
            if handle and handle in node_map:
                new_handle = node_map[handle]
            else:
                new_handle = cmds.group(empty=True,
                                        name=_mirror_name(handle or cluster, token_pairs))
                if handle:
                    _apply_world_matrix(new_handle, _mirror_matrix(
                        cmds.xform(handle, query=True, worldSpace=True, matrix=True),
                        axis, other_behavior))

            new_cluster = cmds.cluster(
                [dst for _src, dst in geo_pairs],
                weightedNode=(new_handle, new_handle),
                bindState=True,
                name=_mirror_name(cluster, token_pairs))[0]

            for attr in ("envelope", "relative"):
                if cmds.attributeQuery(attr, node=cluster, exists=True):
                    cmds.setAttr(new_cluster + "." + attr,
                                 cmds.getAttr(cluster + "." + attr))

            src_geos = cmds.deformer(cluster, query=True, geometry=True) or []
            src_idx = cmds.deformer(cluster, query=True, geometryIndices=True) or []
            dst_geos = cmds.deformer(new_cluster, query=True, geometry=True) or []
            dst_idx = cmds.deformer(new_cluster, query=True, geometryIndices=True) or []

            for src_shape, dst_shape in geo_pairs:
                gi_src = _geometry_index(src_geos, src_idx, src_shape)
                gi_dst = _geometry_index(dst_geos, dst_idx, dst_shape)
                if gi_src is None or gi_dst is None:
                    warnings.append("Cluster '{0}' weights skipped for '{1}'.".format(
                        _short(cluster), _short(dst_shape)))
                    continue
                count = _component_count(src_shape)
                if count <= 0:
                    continue
                # 범위 지정 get/setAttr 은 값이 안 들어간 자리를 기본값으로 채워 준다.
                values = cmds.getAttr("{0}.weightList[{1}].weights[0:{2}]".format(
                    cluster, gi_src, count - 1))
                cmds.setAttr("{0}.weightList[{1}].weights[0:{2}]".format(
                    new_cluster, gi_dst, count - 1), *values)

            created.append(new_cluster)
        except Exception as e:
            warnings.append("Cluster '{0}' could not be mirrored ({1}).".format(
                _short(cluster), e))

    return created


# ==================================================================
# 컨스트레인트
# ==================================================================

def _upstream_nodes(plug, depth=2):
    """plug 로 흘러드는 노드들(중간 노드 depth 홉까지).

    컨스트레인트가 채널을 구동하더라도 키가 있으면 `pairBlend` 를, 애님 레이어가 있으면
    `animBlendNode*` 를 한 단계 거쳐 들어온다. 한 홉만 보면 "구동 안 함" 으로 잘못 읽는다.
    """
    found = set()
    todo = [(plug, 0)]
    while todo:
        target, level = todo.pop()
        for source in cmds.listConnections(target, source=True, destination=False,
                                           plugs=True) or []:
            node = source.split(".")[0]
            if node in found:
                continue
            found.add(node)
            if level < depth:
                todo.append((node, level + 1))
    return found


def _driven_axes(constraint, driven, channel):
    """constraint 가 driven 의 channel(translate/rotate/scale) 중 구동하는 축 목록."""
    axes = []
    for axis in "xyz":
        plug = "{0}.{1}{2}".format(driven, channel, axis.upper())
        if not cmds.objExists(plug):
            continue
        if any(_same_node(node, constraint) for node in _upstream_nodes(plug)):
            axes.append(axis)
    return axes


def _constraints_driving(node):
    """node 를 구동하는 컨스트레인트 노드 목록(중복 없이)."""
    found = cmds.listConnections(node, source=True, destination=False,
                                 type="constraint") or []
    out = []
    for con in found:
        path = _long(con) or con
        if path not in out:
            out.append(path)
    return out


def _mirror_constraint(constraint, driven, node_map, token_pairs, warnings):
    """컨스트레인트 하나를 반대쪽 짝으로 다시 만든다. 반환: 새 노드 또는 None.

    드라이버가 스코프 밖이면 **같은 드라이버**를 그대로 쓴다(센터 컨트롤).
    미러된 오브젝트는 이미 제자리에 놓여 있으므로 `maintainOffset=True` 로 만들면
    원본이 오프셋을 갖고 있든 아니든 그대로 재현된다.
    """
    ctype = cmds.nodeType(constraint)
    fn = _CONSTRAINT_FN.get(ctype)
    if fn is None:
        warnings.append("'{0}' ({1}) is not supported - skipped.".format(
            _short(constraint), ctype))
        return None

    new_driven = node_map.get(driven)
    if not new_driven:
        return None

    targets = fn(constraint, query=True, targetList=True) or []
    if not targets:
        warnings.append("'{0}' has no target - skipped.".format(_short(constraint)))
        return None

    new_targets = []
    for target in targets:
        path = _long(target)
        if not path:
            warnings.append("Target '{0}' of '{1}' is gone - skipped.".format(
                target, _short(constraint)))
            return None
        new_targets.append(node_map.get(path, path))

    kwargs = {}
    if ctype not in _NO_MAINTAIN_OFFSET:
        kwargs["maintainOffset"] = True

    driven_any = (ctype not in _SKIP_CHANNELS)
    for flag, channel in _SKIP_CHANNELS.get(ctype, ()):
        driven_axes = _driven_axes(constraint, driven, channel)
        if driven_axes:
            driven_any = True
        skipped = [axis for axis in "xyz" if axis not in driven_axes]
        if skipped:
            kwargs[flag] = skipped

    if not driven_any:
        warnings.append("'{0}' drives no channel of '{1}' - skipped.".format(
            _short(constraint), _short(driven)))
        return None

    aliases = fn(constraint, query=True, weightAliasList=True) or []
    weights = [cmds.getAttr(constraint + "." + alias) for alias in aliases]

    new_constraint = fn(*(new_targets + [new_driven]), **kwargs)[0]

    # 타겟 가중치 (targetList 순서 == weightAliasList 순서)
    new_aliases = fn(new_constraint, query=True, weightAliasList=True) or []
    for alias, value in zip(new_aliases, weights):
        try:
            cmds.setAttr(new_constraint + "." + alias, value)
        except Exception:
            pass

    # 회전 보간 방식 등, 타입에 따라 있을 수도 없을 수도 있는 설정.
    for attr in ("interpType", "worldUpType", "aimVector", "upVector", "worldUpVector"):
        if not cmds.attributeQuery(attr, node=constraint, exists=True):
            continue
        if not cmds.attributeQuery(attr, node=new_constraint, exists=True):
            continue
        value = cmds.getAttr(constraint + "." + attr)
        try:
            if isinstance(value, list) and value and isinstance(value[0], tuple):
                cmds.setAttr(new_constraint + "." + attr, *value[0])
            else:
                cmds.setAttr(new_constraint + "." + attr, value)
        except Exception:
            pass

    # aim/normal/tangent 의 world up object 도 반대쪽으로 갈아끼운다.
    if cmds.attributeQuery("worldUpMatrix", node=constraint, exists=True):
        sources = cmds.listConnections(constraint + ".worldUpMatrix", source=True,
                                       destination=False, plugs=True) or []
        if sources:
            node, attr = sources[0].split(".", 1)
            path = _long(node)
            up_object = node_map.get(path, path)
            if up_object:
                try:
                    cmds.connectAttr("{0}.{1}".format(up_object, attr),
                                     new_constraint + ".worldUpMatrix", force=True)
                except Exception:
                    pass

    try:
        cmds.rename(new_constraint, _mirror_name(constraint, token_pairs))
    except Exception:
        pass

    return new_constraint


# ==================================================================
# 진입점
# ==================================================================

def mirror(objects, plane=PLANE_YZ, joint_mode=MODE_BEHAVIOR,
           other_mode=MODE_BEHAVIOR, disable_token_check=False,
           token_pairs=None, do_skin=True, do_constraints=True, do_clusters=True):
    """리스트업된 오브젝트와 그 자식들을 미러한다.

    objects             : 미러할 최상위 오브젝트 이름 목록(TSL 내용).
    plane               : PLANE_YZ / PLANE_XY / PLANE_XZ
    joint_mode          : 조인트의 MODE_BEHAVIOR / MODE_ORIENTATION
    other_mode          : 커브 등 나머지 트랜스폼의 미러 방식
    disable_token_check : True 면 토큰 없는 이름도 경고만 하고 진행(접미사 '_mir')
    token_pairs         : [(left, right), ...]. None 이면 공용 규칙 파일에서 읽는다.

    반환: (created_roots, warnings, infos)
    예외: MissingTokenError - 토큰 없는 오브젝트가 있고 disable_token_check 가 False 일 때.
          씬은 건드리지 않고(세트 하나만 만든다) 이름 목록과 세트 이름을 실어 던진다.
    """
    warnings = []
    infos = []

    if token_pairs is None:
        token_pairs, message = MirrorTokenStore.load()
        infos.append(message)

    axis = _PLANE_NORMAL.get(plane)
    if axis is None:
        raise ValueError("Unknown mirror plane '{0}'.".format(plane))
    joint_behavior = (joint_mode == MODE_BEHAVIOR)
    other_behavior = (other_mode == MODE_BEHAVIOR)

    roots = _resolve_roots(objects, warnings)
    if not roots:
        raise RuntimeError("Nothing to mirror - list the objects first.")

    # ---- 스코프와 이름을 먼저 정한다 (복제 전에 막을 수 있어야 한다) ----
    scope = []
    for root in roots:
        scope.extend(_hierarchy(root))

    names, missing = _plan_names(scope, token_pairs)
    if missing:
        warnings.append("{0} object(s) have no mirror token:".format(len(missing)))
        warnings.extend(_name_lines(missing))

    if missing and not disable_token_check:
        # 이름만 찍어 두면 씬에서 다시 찾아야 한다. 세트로 묶어 바로 고를 수 있게 한다.
        set_name = _make_missing_token_set(missing, warnings)
        if set_name:
            warnings.append("Collected in the set '{0}'.".format(set_name))
        raise MissingTokenError(
            "{0} object(s) have no mirror token - nothing was mirrored{1}. "
            "Check 'Disable token check' to mirror them anyway.".format(
                len(missing),
                " (see the set '{0}')".format(set_name) if set_name else ""),
            missing, set_name, warnings)

    if missing:
        infos.append("{0} object(s) mirrored with the '{1}' suffix instead of a token.".format(
            len(missing), NO_TOKEN_SUFFIX))

    existing = [names[n] for n in scope if cmds.objExists(names[n])]
    if existing:
        warnings.append("{0} mirrored name(s) already exist - Maya will make them "
                        "unique (e.g. '{1}').".format(len(existing), existing[0]))

    # ---- 복제 + 원본/복제 짝짓기 ----
    pairs = []                      # [(원본 롱네임, 복제 롱네임)] - 부모 -> 자식 순
    root_uuids = []
    for root in roots:
        dup = _duplicate_root(root)
        root_uuids.append(_uuid(dup))   # 리네임하면 경로가 바뀌므로 UUID 로 잡아 둔다
        _pair_hierarchy(root, dup, pairs)

    # 이름을 바꾸면 경로가 전부 흔들리므로 UUID 로 잡아 둔다.
    uuid_pairs = [(_uuid(orig), _uuid(dup)) for orig, dup in pairs]
    for (orig, _dup), (_ou, dup_uuid) in zip(pairs, uuid_pairs):
        _rename_dup(dup_uuid, names[orig], token_pairs, warnings)

    # 리네임 뒤의 현재 경로로 매핑을 다시 세운다. (원본 롱네임 -> 복제 롱네임)
    node_map = {}
    resolved_pairs = []
    for (orig, _dup), (orig_uuid, dup_uuid) in zip(pairs, uuid_pairs):
        orig_path = _by_uuid(orig_uuid) or orig
        dup_path = _by_uuid(dup_uuid)
        if not dup_path:
            continue
        node_map[orig_path] = dup_path
        resolved_pairs.append((orig_path, dup_path))
    created_roots = [path for path in (_by_uuid(u) for u in root_uuids) if path]

    # ---- 트랜스폼 (부모 -> 자식 순서로 놓아야 자식이 안 밀린다) ----
    for orig, dup in resolved_pairs:
        is_joint = (cmds.nodeType(orig) == "joint")
        behavior = joint_behavior if is_joint else other_behavior
        matrix = _mirror_matrix(
            cmds.xform(orig, query=True, worldSpace=True, matrix=True), axis, behavior)
        try:
            _apply_world_matrix(dup, matrix)
        except Exception as e:
            warnings.append("Could not place '{0}' ({1}).".format(_short(dup), e))

    # ---- 메시 지오메트리는 한 번 더 반사한다 (트랜스폼만으로는 안 뒤집힌다) ----
    for orig, dup in resolved_pairs:
        if not _shape_of(dup, "mesh"):
            continue
        matrix = cmds.xform(dup, query=True, worldSpace=True, matrix=True)
        try:
            _reflect_mesh(orig, dup, axis, matrix, warnings)
        except Exception as e:
            warnings.append("Could not mirror the geometry of '{0}' ({1}).".format(
                _short(dup), e))

    # ---- 관계 재구성 ----
    scope_orig = [orig for orig, _dup in resolved_pairs]

    skins = []
    if do_skin:
        for orig, dup in resolved_pairs:
            try:
                new_skin = _copy_skin(orig, dup, node_map, token_pairs, warnings)
            except Exception as e:
                warnings.append("Skin of '{0}' could not be mirrored ({1}).".format(
                    _short(orig), e))
                continue
            if new_skin:
                skins.append(new_skin)

    clusters = []
    if do_clusters:
        clusters = _copy_clusters(scope_orig, node_map, axis, other_behavior,
                                  token_pairs, warnings)

    constraints = []
    if do_constraints:
        for orig, _dup in resolved_pairs:
            for constraint in _constraints_driving(orig):
                try:
                    new_constraint = _mirror_constraint(
                        constraint, orig, node_map, token_pairs, warnings)
                except Exception as e:
                    warnings.append("Constraint '{0}' could not be mirrored ({1}).".format(
                        _short(constraint), e))
                    continue
                if new_constraint:
                    constraints.append(new_constraint)

    infos.append("{0} object(s) mirrored across the {1} plane.".format(
        len(resolved_pairs), plane.upper()))
    if do_skin:
        infos.append("{0} skinCluster(s) rebuilt.".format(len(skins)))
    if do_clusters:
        infos.append("{0} cluster(s) rebuilt.".format(len(clusters)))
    if do_constraints:
        infos.append("{0} constraint(s) rebuilt.".format(len(constraints)))

    return (created_roots, warnings, infos)
