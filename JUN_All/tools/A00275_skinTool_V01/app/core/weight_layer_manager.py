# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-15
# A00275_skinTool_V01 - Weights > Layer
"""
weight_layer_manager - 토폴로지가 같은 메시 N 개의 스킨 웨이트를 **레이어처럼** 합성한다.

리스트의 **위쪽이 우선순위가 높은 레이어**, **맨 아래가 베이스**다. 레이어마다
  - lock  : 이 메시에서 가져올 조인트 (베이스는 lock 이 없으면 조인트 전부)
  - Blend : 가져올 양 (0~1)
을 정해 두고, 버텍스마다 아래 규칙으로 한 행을 만든다.

--------------------------------------------------------------------------
합성 규칙 (계획서 `docs/plans/A00275_skinTool_V01_layer_tab_plan.md` 10장 답)
--------------------------------------------------------------------------
    cap = 1                                   # 아직 남은 몫
    lock 이 있는 레이어마다 **아래에서 위로**:
        c = Blend x (lock 한 조인트의 웨이트)    # 절대값 그대로
        합(c) <= cap 이면 그대로 넣고 cap -= 합(c)
        합(c) >  cap 이면 c 를 cap/합(c) 배로 줄여 넣고 cap = 0   (넘친 레이어만 잘린다)
    베이스에 lock 이 없으면 베이스의 전체 행으로 남은 cap 을 채운다.
    그래도 cap 이 남으면(합 < 1) 결과 행을 **재정규화**해 합을 1 로 만든다.
    아무 레이어도 기여하지 못한 버텍스는 베이스의 **전체 행**을 쓴다(로그로 개수).

- lock 값은 **절대값으로 보존**된다. 합이 1 을 넘는 버텍스에서만 **위 레이어부터** 비율대로
  줄어든다 — 아래 레이어의 lock 이 먼저 지켜진다(Q3 답 "위 레이어에서부터 자르도록").
  v01.22 는 이 방향을 반대로 구현해, 위 레이어가 조인트를 전부 lock 하면 아래 레이어의 lock 이
  통째로 사라졌다(v01.23 수정).
- lock 한 조인트가 0 인 버텍스는 그 레이어가 아무것도 가져가지 않으므로, 아래 레이어의 행이
  **그대로** 옮겨진다(Q1).
- 베이스에도 lock 을 걸 수 있다. 채우지 못한 몫은 재정규화로 메운다(Q2).

--------------------------------------------------------------------------
M_new
--------------------------------------------------------------------------
- 형상은 **베이스 메시의 skinCluster 입력 형상**(rest)이다. 화면에 보이는 변형된 형상을
  복제하면 지금 포즈가 구워진다.
- 인플루언스는 합성 결과가 0 이 아닌 조인트뿐이다.
- `bindPreMatrix` 는 **그 조인트를 가진 가장 위 레이어의 skinCluster** 에서 복사한다. 새로
  바인드하면 마야는 *지금* 조인트 위치를 바인드 포즈로 삼으므로, 리그가 포즈된 상태에서
  Merge 하면 메시가 튄다.

--------------------------------------------------------------------------
웨이트 쓰기 — API 가 아니라 setAttr
--------------------------------------------------------------------------
`MFnSkinCluster.setWeights` 는 **undo 기록에 남지 않는다**(mayapy 실측: 청크 안에서 써도
"There are no more commands to undo"). 새 메시를 만드는 모드는 메시째 지우면 되지만,
"이미 있는 메시 갱신" 모드는 Ctrl+Z 로 이전 웨이트가 돌아와야 한다. 그래서 두 모드 모두
버텍스마다 **구간 `setAttr`**(`weightList[v].weights[lo:hi]`)로 쓴다 — 19,881 버텍스 x 8
인플루언스에 0.57초, undo 0.27초로 값이 정확히 복원된다. `normalizeWeights` 가 켜져 있어도
직접 쓴 값은 건드리지 않는다(실측).

UI 비의존: 위젯에서 읽은 list/str/float 값만 받는다. (app/core <-> app/ui 분리)
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core import maya_shape
from Framework.core import maya_skin
from . import bind_pose_manager as bp_mgr


MODE_CREATE = "create"
MODE_UPDATE = "update"

# 이보다 작은 값은 0 으로 본다.
EPS = 1e-9

# 합이 1 에서 이만큼 모자라면 재정규화한다(부동소수 오차는 건드리지 않는다).
RENORMALIZE_GAP = 1e-7

# 입력 행의 합이 1 에서 이만큼 벗어나면 읽을 때 정규화한다.
INPUT_SUM_TOLERANCE = 1e-6

# bindPreMatrix 비교 허용 오차.
MATRIX_TOLERANCE = 1e-4

DEFAULT_NAME = "M_new"


class LayerError(RuntimeError):
    """합성을 시작할 수 없다(검증 실패). 씬은 건드리지 않았다."""


# ==================================================================
# 노드 헬퍼
# ==================================================================

def _long(node):
    found = cmds.ls(node, long=True) or []
    return found[0] if found else None


def _short(node):
    return (node or "").split("|")[-1]


def _clamp01(value):
    return max(0.0, min(1.0, float(value)))


def resolve_mesh(node):
    """트랜스폼 / 셰이프 / 컴포넌트 이름 -> (트랜스폼 롱네임, 셰이프 롱네임, skinCluster|None)."""
    name = (node or "").split(".")[0].strip()
    if not name:
        raise LayerError("Empty mesh name.")
    path = _long(name)
    if not path:
        raise LayerError("'{0}' does not exist.".format(name))

    if cmds.objectType(path, isAType="shape"):
        parents = cmds.listRelatives(path, parent=True, fullPath=True) or []
        transform = parents[0] if parents else path
    else:
        transform = path

    clusters = bp_mgr.skin_clusters_of(transform)
    skin = clusters[0] if clusters else None
    shape = maya_shape.shape_path(transform, deformer=skin, type_="mesh")
    if not shape:
        raise LayerError("'{0}' is not a polygon mesh.".format(_short(transform)))
    return transform, shape, skin


def read_influences(node):
    """메시에 바인드된 조인트(인플루언스) 롱네임 목록. 조인트 리스트 채우기용."""
    transform, _shape, skin = resolve_mesh(node)
    if not skin:
        raise LayerError("'{0}' has no skinCluster.".format(_short(transform)))
    return maya_skin.influence_paths(maya_skin.skin_fn(skin))


def _all_vertices(count):
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.setCompleteData(count)
    return comp


# ==================================================================
# 합성 (마야 없는 순수 계산)
# ==================================================================

def _pour(entries, cap, row):
    """entries 를 남은 몫 cap 안에 붓는다. 넘치면 비율대로 줄인다.

    반환: (새 cap, 잘렸는지)
    """
    if not entries:
        return cap, False
    total = 0.0
    for _key, value in entries:
        total += value
    if total <= EPS:
        return cap, False
    if cap <= EPS:
        return cap, True            # 이미 꽉 찼다 - 통째로 잘렸다

    scale = 1.0
    if total > cap:
        scale = cap / total
    for key, value in entries:
        row[key] = row.get(key, 0.0) + value * scale
    if scale < 1.0:
        return 0.0, True
    return cap - total, False


def compose_rows(locked_rows, fill_rows, fallback_rows):
    """버텍스마다 레이어 행을 합성한다.

    locked_rows   : 레이어 순서(**위 -> 아래**)의 lock 행 목록. 원소마다 버텍스별 행 목록이고,
                    행은 [(key, value), ...] — lock 으로 거르고 Blend 를 **이미 곱한** 값.
                    베이스에 lock 이 있으면 베이스도 여기(마지막)에 들어간다.
    fill_rows     : 베이스에 lock 이 **없을 때** 베이스의 (Blend 를 곱한) 전체 행. lock 을 전부 넣고
                    **남은 몫**을 채운다. 베이스에 lock 이 있으면 None.
    fallback_rows : 아무것도 못 들어간 버텍스에 쓸 행(베이스의 전체 행).

    **lock 은 아래 레이어부터 붓는다.** 합이 1 을 넘으면 **위 레이어부터 잘린다**(계획서 Q3 답
    "합이 1 넘긴 부위만 위 레이어에서부터 자르도록"). v01.22 는 반대로 위 레이어부터 부어서,
    위 레이어가 조인트를 전부 lock 하면 아래 레이어의 lock 이 통째로 사라졌다(사용자 피드백).

    반환: (rows, stats)
        rows  : 버텍스별 {key: value}
        stats : {"cut": lock 이 잘린 버텍스 수,
                 "renormalized": 재정규화한 버텍스 수,
                 "fallback": 베이스 전체 행을 쓴 버텍스 수}
    """
    count = len(fallback_rows)
    order = list(reversed(locked_rows))
    rows = []
    cut = renormalized = fallback = 0

    for v in range(count):
        cap = 1.0
        row = {}
        was_cut = False

        for layer in order:
            cap, clipped = _pour(layer[v], cap, row)
            was_cut = was_cut or clipped

        # 베이스의 lock 안 된 조인트는 남은 몫을 채우는 것이지 lock 이 아니다 - 잘림으로 세지 않는다.
        if fill_rows is not None:
            cap, _clipped = _pour(fill_rows[v], cap, row)

        if cap > RENORMALIZE_GAP:
            filled = 1.0 - cap
            if filled > EPS:
                inverse = 1.0 / filled
                for key in row:
                    row[key] *= inverse
                renormalized += 1
            else:
                row = dict(fallback_rows[v])
                fallback += 1

        if was_cut:
            cut += 1
        rows.append(row)

    return rows, {"cut": cut, "renormalized": renormalized, "fallback": fallback}


# ==================================================================
# 읽기 / 검증
# ==================================================================

class _Layer(object):
    """한 레이어의 씬 정보와 버텍스별 행."""

    def __init__(self, spec, is_base):
        self.transform, self.shape, self.skin = resolve_mesh(spec.get("mesh"))
        self.is_base = is_base
        self.blend = _clamp01(spec.get("blend", 1.0))
        self.locked_names = [n for n in (spec.get("locked") or []) if n]
        self.fn = None
        self.influences = []
        self.logical = []
        self.count = 0
        self.rows = []
        self.full_rows = []
        self.normalized_inputs = 0
        self.use_all = False

    def read(self, warnings):
        self.fn = maya_skin.skin_fn(self.skin)
        self.influences = maya_skin.influence_paths(self.fn)
        self.logical = maya_skin.logical_indices(self.fn)
        dag = maya_shape.shape_dag(self.transform, deformer=self.skin)
        self.count = maya_shape.vertex_count(self.transform, deformer=self.skin)

        locked = set()
        for name in self.locked_names:
            path = _long(name)
            if not path or path not in self.influences:
                warnings.append("'{0}' is locked on '{1}' but is not bound to it - "
                                "ignored.".format(_short(name), _short(self.transform)))
                continue
            locked.add(path)

        self.use_all = self.is_base and not locked
        columns = [c for c, path in enumerate(self.influences)
                   if self.use_all or path in locked]

        flat = list(self.fn.getWeights(dag, _all_vertices(self.count))[0])
        width = len(self.influences)
        blend = self.blend
        paths = self.influences

        for v in range(self.count):
            start = v * width
            seg = flat[start:start + width]
            total = sum(seg)
            if total > EPS and abs(total - 1.0) > INPUT_SUM_TOLERANCE:
                seg = [value / total for value in seg]
                self.normalized_inputs += 1
            if blend > 0.0:
                self.rows.append([(paths[c], seg[c] * blend) for c in columns
                                  if seg[c] > 0.0])
            else:
                self.rows.append([])
            if self.is_base:
                self.full_rows.append([(paths[c], seg[c]) for c in range(width)
                                       if seg[c] > 0.0])

    def bind_pre_matrix(self, joint):
        """이 레이어 skinCluster 에서 joint 의 bindPreMatrix(16개). 없으면 None."""
        if joint not in self.influences:
            return None
        index = self.logical[self.influences.index(joint)]
        return cmds.getAttr("{0}.bindPreMatrix[{1}]".format(self.skin, index))


def validate(layers, mode=MODE_CREATE, target=None):
    """합성 전에 막을 것을 찾는다. 반환: (errors, warnings). 씬은 건드리지 않는다."""
    errors = []
    warnings = []

    specs = [spec for spec in (layers or []) if spec and spec.get("mesh")]
    if len(specs) < 2:
        errors.append("List at least 2 meshes (the bottom one is the base).")
        return errors, warnings

    seen = {}
    counts = {}
    for index, spec in enumerate(specs):
        try:
            transform, _shape, skin = resolve_mesh(spec["mesh"])
        except LayerError as e:
            errors.append(str(e))
            continue
        if transform in seen:
            errors.append("'{0}' is listed twice.".format(_short(transform)))
            continue
        seen[transform] = index
        if not skin:
            errors.append("'{0}' has no skinCluster.".format(_short(transform)))
            continue
        counts[transform] = maya_shape.vertex_count(transform, deformer=skin)
        is_base = index == len(specs) - 1
        if not is_base and not [n for n in (spec.get("locked") or []) if n]:
            warnings.append("'{0}' has no locked joint - it adds nothing.".format(
                _short(transform)))

    if len(set(counts.values())) > 1:
        errors.append("The meshes must have the same vertex count: {0}.".format(
            ", ".join("{0} ({1})".format(_short(t), n) for t, n in counts.items())))

    if mode == MODE_UPDATE:
        if not target:
            errors.append("Set the mesh to update.")
        else:
            try:
                t_transform, _t_shape, t_skin = resolve_mesh(target)
            except LayerError as e:
                errors.append(str(e))
            else:
                if t_transform in seen:
                    errors.append("'{0}' is one of the layers - pick another mesh to "
                                  "update.".format(_short(t_transform)))
                elif counts:
                    n = maya_shape.vertex_count(t_transform, deformer=t_skin)
                    expected = next(iter(counts.values()))
                    if n != expected:
                        errors.append("'{0}' has {1} vertices, the layers have {2}.".format(
                            _short(t_transform), n, expected))
                if t_skin and len(cmds.skinCluster(t_skin, q=True, geometry=True) or []) > 1:
                    errors.append("'{0}' deforms more than one geometry - not "
                                  "supported.".format(t_skin))
    elif mode != MODE_CREATE:
        errors.append("Unknown mode '{0}'.".format(mode))

    return errors, warnings


# ==================================================================
# M_new 만들기 / 준비
# ==================================================================

def _rest_geometry_plug(skin, shape):
    """skinCluster 가 받는 입력 형상 플러그(rest). 변형 전 형상이다."""
    index = bp_mgr._geometry_index(skin, shape)
    sources = cmds.listConnections("{0}.input[{1}].inputGeometry".format(skin, index),
                                   source=True, destination=False, plugs=True) or []
    if not sources:
        raise LayerError("Could not find the rest shape of '{0}'.".format(_short(shape)))
    return sources[0]


def _face_ranges(faces):
    """연속한 면 번호를 `[(시작, 끝), ...]` 구간으로 묶는다.

    면 하나씩 이름을 만들면 머티리얼이 면 단위로 잘게 섞인 메시에서 문자열이 수만 개가
    된다. `f[0:511]` 처럼 구간으로 주면 `cmds.sets` 호출 한 번으로 끝난다.
    """
    ranges = []
    start = previous = None
    for index in faces:
        if start is None:
            start = previous = index
        elif index == previous + 1:
            previous = index
        else:
            ranges.append((start, previous))
            start = previous = index
    if start is not None:
        ranges.append((start, previous))
    return ranges


def _copy_shading(source, shape, warnings=None):
    """소스 셰이프의 머티리얼 배정을 새 셰이프에 그대로 옮긴다.

    ★ **면 단위 배정까지 옮긴다.** 예전에는 `listConnections(..., type="shadingEngine")`
    의 **첫 번째 하나**를 메시 전체에 걸었다. 머티리얼이 하나인 메시에서는 맞는 답이지만,
    면마다 다른 머티리얼이 붙은 메시(캐릭터는 대개 그렇다)에서는 **나머지가 전부 사라지고
    한 벌만 입혀진다.** 그 목록은 어떤 면에 무엇이 붙었는지를 담고 있지 않다.

    면별 배정은 `MFnMesh.getConnectedShaders` 가 알려 준다 - 셰이딩 엔진 목록과, **면마다
    그중 몇 번인지**(배정이 없으면 -1)를 함께 돌려준다. rest 형상은 skinCluster 의 입력이라
    베이스와 토폴로지가 같아 면 번호가 그대로 맞는다(다르면 손대지 않고 경고만 남긴다).
    """
    try:
        selection = om.MSelectionList()
        selection.add(source)
        dag = selection.getDagPath(0)
        engines, face_index = om.MFnMesh(dag).getConnectedShaders(dag.instanceNumber())
        names = [om.MFnDependencyNode(engine).absoluteName() for engine in engines]
    except Exception:
        engines, face_index, names = [], [], []

    if not names:
        try:
            cmds.sets(shape, edit=True, forceElement="initialShadingGroup")
        except Exception:
            pass
        return

    # 면 개수가 다르면 면 번호를 옮길 수 없다. 통째로 거는 것은 틀린 답이므로 하지 않는다.
    if len(face_index) != (cmds.polyEvaluate(shape, face=True) or 0):
        if warnings is not None:
            warnings.append("Face count differs from '{0}' - materials were not "
                            "copied.".format(_short(source)))
        return

    # 면이 전부 같은 엔진이면 셰이프째 건다(면 단위 멤버를 남기지 않는다).
    used = set(face_index)
    if len(used) == 1 and -1 not in used:
        try:
            cmds.sets(shape, edit=True, forceElement=names[face_index[0]])
        except Exception:
            pass
        return

    by_engine = {}
    for face, index in enumerate(face_index):
        if index < 0:
            continue                      # 아무 머티리얼도 없는 면은 그대로 둔다
        by_engine.setdefault(index, []).append(face)

    for index, faces in sorted(by_engine.items()):
        members = ["{0}.f[{1}:{2}]".format(shape, lo, hi) if lo != hi
                   else "{0}.f[{1}]".format(shape, lo)
                   for lo, hi in _face_ranges(faces)]
        try:
            cmds.sets(members, edit=True, forceElement=names[index])
        except Exception:
            if warnings is not None:
                warnings.append("Could not assign '{0}' to the new mesh."
                                .format(_short(names[index])))


def _create_mesh(base, name, warnings=None):
    """베이스의 rest 형상을 굽은 새 메시. 반환: (트랜스폼 롱네임, 셰이프 롱네임)."""
    source = _rest_geometry_plug(base.skin, base.shape)

    transform = cmds.createNode("transform", name=name or DEFAULT_NAME)
    shape = cmds.createNode("mesh", name=_short(transform) + "Shape", parent=transform)
    transform = _long(transform)
    shape = _long(shape)

    # 연결해 평가한 뒤 끊으면 형상이 메시 안에 남는다(히스토리 없는 메시).
    cmds.connectAttr(source, shape + ".inMesh")
    cmds.dgeval(shape + ".outMesh")
    cmds.disconnectAttr(source, shape + ".inMesh")

    cmds.xform(transform, worldSpace=True,
               matrix=cmds.xform(base.transform, query=True, worldSpace=True, matrix=True))

    _copy_shading(base.shape, shape, warnings)
    return transform, shape


def _new_skin(transform, joints, name):
    skin = cmds.skinCluster(joints, transform, toSelectedBones=True,
                            obeyMaxInfluences=False, normalizeWeights=1,
                            name=name)[0]
    return skin


def _logical_index(skin, joint):
    fn = maya_skin.skin_fn(skin)
    paths = maya_skin.influence_paths(fn)
    return maya_skin.logical_indices(fn)[paths.index(joint)]


def _same_matrix(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) <= MATRIX_TOLERANCE


def _source_bind_matrices(layers, joints, warnings):
    """조인트마다 가장 위 레이어의 bindPreMatrix. 레이어끼리 다르면 경고."""
    matrices = {}
    for joint in joints:
        found = [(layer, layer.bind_pre_matrix(joint)) for layer in layers
                 if joint in layer.influences]
        if not found:
            continue
        top_layer, top = found[0]
        matrices[joint] = top
        for layer, matrix in found[1:]:
            if not _same_matrix(top, matrix):
                warnings.append(
                    "'{0}' has a different bind matrix on '{1}' and '{2}' - the "
                    "upper one ('{1}') is used.".format(
                        _short(joint), _short(top_layer.transform), _short(layer.transform)))
                break
    return matrices


def _set_bind_matrix(skin, joint, matrix, warnings):
    plug = "{0}.bindPreMatrix[{1}]".format(skin, _logical_index(skin, joint))
    try:
        cmds.setAttr(plug, *matrix, type="matrix")
    except Exception as e:
        warnings.append("Could not set the bind matrix of '{0}' ({1}).".format(
            _short(joint), e))


def _at_bind_pose(joints, matrices):
    """모든 조인트가 bindPreMatrix 가 기억하는 자리에 있는가."""
    for joint in joints:
        current = cmds.getAttr(joint + ".worldInverseMatrix")
        if not _same_matrix(current, matrices[joint]):
            return False
    return True


def _drop_bind_pose(skin):
    """skinCluster 생성이 *지금* 포즈로 만든 bindPose 를 떼어 지운다."""
    poses = cmds.listConnections(skin + ".bindPose", source=True, destination=False,
                                 type="dagPose") or []
    for pose in poses:
        try:
            cmds.disconnectAttr(pose + ".message", skin + ".bindPose")
        except Exception:
            pass
        # 다른 skinCluster 도 쓰는 포즈면 남긴다.
        users = cmds.listConnections(pose + ".message", source=False,
                                     destination=True) or []
        if not users:
            cmds.delete(pose)


# ==================================================================
# 웨이트 쓰기
# ==================================================================

def _write_weights(skin, shape, rows):
    """버텍스마다 구간 setAttr 로 쓴다(undo 가능).

    구간은 **새로 쓸 값과 지금 들어 있는 값**의 논리 인덱스를 모두 덮어야 한다 — 안 그러면
    예전 인플루언스 웨이트가 남아 합이 1 을 넘는다. 지금 값은 API 로 한 번에 읽는다.
    """
    fn = maya_skin.skin_fn(skin)
    paths = maya_skin.influence_paths(fn)
    logical = maya_skin.logical_indices(fn)
    slot = dict(zip(paths, logical))
    width = len(paths)

    dag = maya_shape.shape_dag(shape, deformer=skin)
    count = len(rows)
    old = list(fn.getWeights(dag, _all_vertices(count))[0])

    template = "{0}.weightList[{{0}}].weights[{{1}}:{{2}}]".format(skin)
    for v, row in enumerate(rows):
        values = {}
        start = v * width
        for c in range(width):
            if old[start + c] != 0.0:
                values[logical[c]] = 0.0
        for key, value in row.items():
            index = slot[key]
            values[index] = values.get(index, 0.0) + value
        if not values:
            continue
        lo = min(values)
        hi = max(values)
        dense = [0.0] * (hi - lo + 1)
        for index, value in values.items():
            dense[index - lo] = value
        cmds.setAttr(template.format(v, lo, hi), *dense)


# ==================================================================
# 진입점
# ==================================================================

def merge(layers, mode=MODE_CREATE, name=DEFAULT_NAME, target=None):
    """레이어를 합성해 새 메시를 만들거나(create) 기존 메시의 웨이트를 갱신한다(update).

    layers : 위 -> 아래 순서 [{"mesh": 이름, "locked": [조인트, ...], "blend": 0~1}, ...]
             마지막이 베이스다.
    mode   : MODE_CREATE / MODE_UPDATE
    name   : create 모드의 새 메시 이름
    target : update 모드의 대상 메시

    반환: report dict
    예외: LayerError - 검증 실패(씬은 건드리지 않았다)
    """
    errors, warnings = validate(layers, mode=mode, target=target)
    if errors:
        raise LayerError("\n".join(errors))
    infos = []

    specs = [spec for spec in layers if spec and spec.get("mesh")]
    data = [_Layer(spec, index == len(specs) - 1) for index, spec in enumerate(specs)]
    for layer in data:
        layer.read(warnings)
        if layer.normalized_inputs:
            warnings.append("'{0}': {1} vertex row(s) did not sum to 1 and were "
                            "normalized before merging.".format(
                                _short(layer.transform), layer.normalized_inputs))
    base = data[-1]

    # 베이스에 lock 이 없으면 베이스는 lock 이 아니라 **남은 몫을 채우는 쪽**이다.
    if base.use_all:
        locked_rows = [layer.rows for layer in data[:-1]]
        fill_rows = base.rows
    else:
        locked_rows = [layer.rows for layer in data]
        fill_rows = None
    rows, stats = compose_rows(locked_rows, fill_rows, base.full_rows)

    # 조인트 순서: 레이어 위 -> 아래, 각 레이어의 인플루언스 순서.
    used = set()
    for row in rows:
        used.update(key for key, value in row.items() if value > 0.0)
    joints = []
    for layer in data:
        for joint in layer.influences:
            if joint in used and joint not in joints:
                joints.append(joint)
    if not joints:
        raise LayerError("Nothing to merge - no joint got any weight.")

    matrices = _source_bind_matrices(data, joints, warnings)

    created = False
    added = []
    if mode == MODE_CREATE:
        transform, shape = _create_mesh(base, name, warnings)
        skin = _new_skin(transform, joints, _short(transform) + "_skinCluster")
        created = True
        for joint in joints:
            _set_bind_matrix(skin, joint, matrices[joint], warnings)
        cmds.setAttr(skin + ".geomMatrix", *cmds.getAttr(base.skin + ".geomMatrix"),
                     type="matrix")
        if not _at_bind_pose(joints, matrices):
            _drop_bind_pose(skin)
            infos.append("The joints are not at their bind pose, so no bindPose node was "
                         "kept for the new mesh (the copied bind matrices are what "
                         "matter).")
    else:
        transform, shape, skin = resolve_mesh(target)
        if not skin:
            skin = _new_skin(transform, joints, _short(transform) + "_skinCluster")
            created = True
            for joint in joints:
                _set_bind_matrix(skin, joint, matrices[joint], warnings)
            if not _at_bind_pose(joints, matrices):
                _drop_bind_pose(skin)
        else:
            existing = set(maya_skin.influence_paths(maya_skin.skin_fn(skin)))
            for joint in joints:
                if joint in existing:
                    current = cmds.getAttr("{0}.bindPreMatrix[{1}]".format(
                        skin, _logical_index(skin, joint)))
                    if not _same_matrix(current, matrices[joint]):
                        warnings.append(
                            "'{0}' is already bound to '{1}' with a different bind "
                            "matrix - kept as it is.".format(
                                _short(joint), _short(transform)))
                    continue
                cmds.skinCluster(skin, edit=True, addInfluence=joint, weight=0.0)
                _set_bind_matrix(skin, joint, matrices[joint], warnings)
                added.append(joint)
        shape = maya_shape.shape_path(transform, deformer=skin, type_="mesh")

    _write_weights(skin, shape, rows)

    all_influences = maya_skin.influence_paths(maya_skin.skin_fn(skin))
    unused = [j for j in all_influences if j not in used]
    if unused and mode == MODE_UPDATE and not created:
        infos.append("{0} influence(s) already on '{1}' now have no weight: {2}".format(
            len(unused), _short(transform),
            ", ".join(_short(j) for j in unused[:6]) + (" ..." if len(unused) > 6 else "")))

    if stats["cut"]:
        infos.append("{0} vertex(es): the locked weights added up past 1.0, so the upper "
                     "layers were cut there (lower layers keep their locks).".format(
                         stats["cut"]))
    if stats["renormalized"]:
        infos.append("{0} vertex(es) did not reach 1.0 and were renormalized.".format(
            stats["renormalized"]))
    if stats["fallback"]:
        warnings.append("{0} vertex(es) got no weight from any layer and took the base "
                        "mesh's full weights.".format(stats["fallback"]))

    return {
        "mode": mode,
        "mesh": transform,
        "skin_cluster": skin,
        "created_skin": created,
        "vertices": len(rows),
        "layers": [_short(layer.transform) for layer in data],
        "influences": joints,
        "added_influences": added,
        "stats": stats,
        "warnings": warnings,
        "infos": infos,
    }
