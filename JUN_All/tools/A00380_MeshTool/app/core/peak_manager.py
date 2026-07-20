# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-20
# A00380_MeshTool - Peak(노말 방향 팽창/수축) 코어 로직
#
# 후디니 peak 노드처럼 버텍스를 자기 노말 방향으로 밀어내거나 당긴다.
# 마야 기본 방식(컴포넌트 선택 후 Move 툴 axis=normal)은 버텍스마다 명령이 돌아
# 19k 버텍스 기준 7 초가 걸린다. 여기서는 이동을 전부 shape.pnts(= 입력 메시에
# 더해지는 offset, tweak) 에 "구간(range) setAttr" 한 방으로 쓴다 → 같은 메시 0.10 초.
#
#   preview : undo 를 잠시 끈 채로 쓴다. 슬라이더를 끄는 동안 undo 기록이 쌓이지
#             않으므로 Ctrl+Z 가 미리보기 단계마다 걸리지 않는다.
#   commit  : 스냅샷 값으로 되돌린 뒤(undo off) 같은 값을 undo 켠 상태로 쓴다.
#             그래야 setAttr 이 "미리보기 이전" 값을 undo 기준으로 잡아,
#             Ctrl+Z 한 번에 Apply 직전 상태로 정확히 돌아간다.
#
# mayapy 로 확인한 함정 두 가지:
#  - MFnMesh.setPoints 로 메시 데이터(vrts)를 직접 쓰면 미리보기는 0.02 초로 더
#    빠르지만 기존 tweak 이 쓸려 나가, Apply 두 번 뒤 Ctrl+Z 가 첫 Apply 까지 푼다.
#  - MPlug.setFloat 로 pnts 를 써도 tweak 이 한 번도 없던 메시에서는 반영이 안 된다
#    (cmds.setAttr 이 한 번 들어가야 평가가 트리거된다). 그래서 setAttr 로 통일했다.
#
# 기존 tweak 값을 읽어 거기에 누적하므로 이전 편집이 날아가지 않는다.
# 히스토리/스킨이 걸린 메시에서도 동작한다.

import re
import contextlib

import maya.cmds as cmds
import maya.api.OpenMaya as om


@contextlib.contextmanager
def _undo_disabled():
    """블록 안의 cmds 호출을 undo 큐에 남기지 않는다 (미리보기용).

    stateWithoutFlush 는 "큐를 비우지 않고" undo 기록만 잠시 끈다. state=False 를
    쓰면 지금까지 쌓인 undo 히스토리가 통째로 날아가므로 반드시 이쪽을 쓴다.
    예외가 나도 finally 에서 다시 켜, undo 가 꺼진 채 남는 사고를 막는다.
    """

    cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


# =========================
# 선택 파싱
# =========================

_COMP_RE = re.compile(r"^(?P<node>.+?)\.(?P<attr>vtx|e|f|map|pt)\[(?P<idx>[\d:]+)\]$")


def _shape_of(node):
    """transform/shape 이름을 받아 non-intermediate 메시 shape 의 풀 패스를 돌려준다."""

    if cmds.nodeType(node) == "mesh":
        shapes = [node]
    else:
        shapes = cmds.listRelatives(node, s=True, f=True, type="mesh") or []

    for s in shapes:
        if not cmds.getAttr("{0}.intermediateObject".format(s)):
            return cmds.ls(s, l=True)[0]

    return None


def _parse_indices(comp_strings):
    """'obj.vtx[3]' / 'obj.vtx[3:9]' 문자열 목록 → 인덱스 set.

    ls(flatten=True) 로 펼치면 큰 선택에서 느려지므로 구간 표기를 그대로 파싱한다.
    """

    ids = set()

    for name in comp_strings:
        m = _COMP_RE.match(name)
        if not m:
            continue

        idx = m.group("idx")

        if ":" in idx:
            start, end = idx.split(":")
            ids.update(range(int(start), int(end) + 1))
        else:
            ids.add(int(idx))

    return ids


def _selection_map():
    """현재 선택을 {shape_full_path: set(vertex ids) or None} 로 정리한다.

    None 은 "메시 전체"를 뜻한다. 엣지/페이스/UV 선택은 버텍스로 변환한다.
    """

    sel = cmds.ls(sl=True, l=True) or []
    if not sel:
        return {}

    result = {}
    comps = []

    for item in sel:
        if "." in item:
            comps.append(item)
            continue

        shape = _shape_of(item)
        if shape:
            result[shape] = None  # 오브젝트 통째 선택 → 전체 버텍스

    if comps:
        # 엣지/페이스/UV 는 버텍스로 변환 (선택 자체는 건드리지 않는다)
        verts = cmds.polyListComponentConversion(comps, tv=True) or []

        by_shape = {}
        for name in verts:
            node = name.split(".")[0]
            by_shape.setdefault(node, []).append(name)

        for node, names in by_shape.items():
            shape = _shape_of(node)
            if not shape:
                continue

            if shape in result and result[shape] is None:
                continue  # 이미 전체 선택

            ids = result.get(shape) or set()
            ids |= _parse_indices(names)
            result[shape] = ids

    return result


def _dag_path(shape):
    sel = om.MSelectionList()
    sel.add(shape)
    return sel.getDagPath(0)


def _soft_weights(shape, count):
    """소프트 셀렉션이 켜져 있으면 {vtx id: weight} 를, 아니면 None 을 돌려준다."""

    if not cmds.softSelect(q=True, softSelectEnabled=True):
        return None

    try:
        rich = om.MGlobal.getRichSelection()
        rich_sel = rich.getSelection()
    except Exception:
        return None

    weights = {}
    short = shape.split("|")[-1]

    for i in range(rich_sel.length()):
        try:
            dag, comp = rich_sel.getComponent(i)
        except Exception:
            continue

        if dag.fullPathName().split("|")[-1] != short:
            continue

        if comp.isNull() or not comp.hasFn(om.MFn.kMeshVertComponent):
            continue

        fn_comp = om.MFnSingleIndexedComponent(comp)

        for e in range(fn_comp.elementCount):
            idx = fn_comp.element(e)
            if idx >= count:
                continue
            weights[idx] = fn_comp.weight(e).influence if fn_comp.hasWeights else 1.0

    return weights or None


def _contiguous_runs(sorted_ids):
    """정렬된 인덱스 목록 → [(start, end), ...] 연속 구간. 구간 setAttr 용."""

    runs = []
    start = prev = sorted_ids[0]

    for i in sorted_ids[1:]:
        if i == prev + 1:
            prev = i
            continue
        runs.append((start, prev))
        start = prev = i

    runs.append((start, prev))

    return runs


# =========================
# 대상 메시 1개
# =========================

class PeakTarget(object):
    """peak 대상 메시 하나의 스냅샷.

    세션 시작 시점의 노말과 기존 tweak 을 얼려둔다. 슬라이더를 끄는 동안 노말을
    다시 계산하면 결과가 스스로에게 먹여져(feedback) 형태가 뭉개지므로, 노말은
    반드시 스냅샷 시점 값을 쓴다.

    이동은 미리보기든 확정이든 전부 shape.pnts(tweak) 에만 쓴다. 메시 데이터(vrts)
    를 건드리지 않으므로 undo/redo 스택이 정확히 맞는다 (모듈 상단 주석 참고).
    """

    def __init__(self, shape, vtx_ids=None, angle_weighted=True, soft_select=True):

        self.shape = shape
        self.dag = _dag_path(shape)
        self.fn = om.MFnMesh(self.dag)

        self.normals = self.fn.getVertexNormals(angle_weighted, om.MSpace.kObject)

        count = self.fn.numVertices

        if vtx_ids is None:
            self.ids = list(range(count))
        else:
            self.ids = sorted(i for i in vtx_ids if 0 <= i < count)

        # 소프트 셀렉션 가중치 (없으면 전부 1.0)
        self.weights = None
        if soft_select:
            w = _soft_weights(shape, count)
            if w:
                self.weights = w
                self.ids = sorted(w.keys())

        self.plug = om.MFnDependencyNode(self.dag.node()).findPlug("pnts", False)
        self.base_tweaks = self._read_tweaks()

    # ---- tweak 읽기 -------------------------------------------------

    def _read_tweaks(self):
        """기존 shape.pnts 값을 {idx: (x, y, z)} 로 읽는다.

        getAttr(".pnts") 통짜 조회는 "compound with mixed type elements" 로 실패하고
        버텍스마다 getAttr 을 돌리면 느리다. MPlug 로 "실제 존재하는 element" 만
        읽으면 19k 메시에서도 0.02 초.
        """

        tweaks = {}

        try:
            for i in self.plug.getExistingArrayAttributeIndices():
                ep = self.plug.elementByLogicalIndex(i)
                tweaks[i] = (ep.child(0).asFloat(),
                             ep.child(1).asFloat(),
                             ep.child(2).asFloat())
        except Exception:
            pass

        return tweaks

    # ---- 적용 -------------------------------------------------------

    def _weight(self, idx):
        return self.weights.get(idx, 0.0) if self.weights is not None else 1.0

    def _offsets(self, amount):
        """이번 이동 결과 tweak 값 {idx: (x, y, z)} 을 만든다 (기존 tweak 누적)."""

        out = {}

        for i in self.ids:
            n = self.normals[i]
            d = amount * self._weight(i)
            bx, by, bz = self.base_tweaks.get(i, (0.0, 0.0, 0.0))
            out[i] = (bx + n.x * d, by + n.y * d, bz + n.z * d)

        return out

    def _write(self, values):
        """{idx: (x,y,z)} 를 pnts 에 쓴다. 연속 인덱스는 구간 setAttr 로 묶는다.

        버텍스마다 setAttr 을 돌리면 19k 메시가 6.8 초, 구간으로 묶으면 0.10 초다.
        """

        for start, end in _contiguous_runs(sorted(values.keys())):

            flat = []
            for i in range(start, end + 1):
                flat.extend(values[i])

            if start == end:
                cmds.setAttr("{0}.pnts[{1}]".format(self.shape, start),
                             flat[0], flat[1], flat[2], type="double3")
            else:
                cmds.setAttr("{0}.pnts[{1}:{2}]".format(self.shape, start, end),
                             *flat, type="double3")

    def preview(self, amount):
        """즉시 보여준다. undo 큐에는 안 올라간다.

        스냅샷 시점의 tweak 에서 매번 다시 계산하므로 슬라이더를 왕복해도 값이
        누적되지 않는다.
        """

        with _undo_disabled():
            self._write(self._offsets(amount))

    def restore(self):
        """미리보기를 세션 시작 상태로 되돌린다 (undo 큐에 안 올라감)."""

        with _undo_disabled():
            self._write({i: self.base_tweaks.get(i, (0.0, 0.0, 0.0))
                         for i in self.ids})

    def commit(self, amount):
        """확정 기록한다. undo 가능.

        기존 tweak 에 이번 이동량을 더해 쓰므로 이전 편집이 보존된다.
        """

        if not self.ids or abs(amount) < 1e-9:
            return 0

        # setAttr 은 "실행 시점의 값"을 undo 기준으로 기억한다. 미리보기 값이 남아
        # 있으면 그게 기준이 되어 Ctrl+Z 가 미리보기 상태로 되돌아간다.
        # 반드시 스냅샷 값으로 되돌린 뒤에 확정 기록해야 한다.
        self.restore()

        applied = self._offsets(amount)
        self._write(applied)

        # 방금 쓴 값을 그대로 스냅샷에 반영한다. 여기서 플러그를 다시 읽으면 DG
        # 평가 시점에 따라 예전 값이 잡힐 수 있어 연속 Apply 가 어긋난다.
        self.base_tweaks.update(applied)

        return len(self.ids)


# =========================
# 세션
# =========================

class PeakSession(object):
    """선택된 메시들의 스냅샷 묶음."""

    def __init__(self, targets):
        self.targets = targets

    # ---- 생성 -------------------------------------------------------

    @classmethod
    def from_selection(cls, angle_weighted=True, soft_select=True):
        """현재 마야 선택으로 세션을 만든다. 선택이 없으면 None."""

        sel_map = _selection_map()
        if not sel_map:
            return None

        targets = []

        for shape, ids in sel_map.items():
            try:
                t = PeakTarget(shape, ids,
                               angle_weighted=angle_weighted,
                               soft_select=soft_select)
            except Exception:
                continue

            if t.ids:
                targets.append(t)

        return cls(targets) if targets else None

    # ---- 정보 -------------------------------------------------------

    @property
    def mesh_count(self):
        return len(self.targets)

    @property
    def vertex_count(self):
        return sum(len(t.ids) for t in self.targets)

    @property
    def is_soft(self):
        return any(t.weights is not None for t in self.targets)

    def mesh_names(self):
        return [t.shape.split("|")[-1] for t in self.targets]

    # ---- 동작 -------------------------------------------------------

    def preview(self, amount):
        for t in self.targets:
            t.preview(amount)

    def restore(self):
        for t in self.targets:
            t.restore()

    def commit(self, amount):
        """확정. 각 타깃이 스냅샷을 갱신하므로 이어서 계속 작업할 수 있다.

        노말은 스냅샷 시점 값으로 유지된다. 형상이 크게 변한 뒤 새 노말로
        작업하려면 Load Selection 으로 세션을 다시 만든다.
        """

        moved = 0
        for t in self.targets:
            moved += t.commit(amount)

        return moved
