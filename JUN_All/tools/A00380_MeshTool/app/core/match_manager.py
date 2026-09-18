# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00380_MeshTool - Match(From 메시 버텍스 위치로 스냅) 코어 로직
#
# v01.10~ Default 탭은 `MatchSession.from_pairs` 를 쓴다 — 좌(source) / 우(target) 리스트를
# 짝지어 target 메시 전체를 source 모양으로. 옛 `from_selection`(From 1개 + 씬 선택)은 남겨 둔다.
#
# Kangaroo 의 Geometry > Match 기능을 Kangaroo 없이 재현한다.
# 리스트업한 From 메시의 "같은 인덱스" 버텍스 위치로, 현재 선택한 메시의 버텍스를
# 이동시킨다. 소프트 셀렉션이 켜져 있으면 그 falloff 가중치를 반영한다. 대응은
# closest-point 가 아니라 "버텍스 인덱스" 기준이라, 두 메시는 토폴로지(버텍스
# 순서/개수)가 같아야 정확히 맞는다. (Kangaroo setModelVerts 와 동일한 규칙.)
#
#   final_local = orig_local + softw * weight * (from_local - orig_local)
#
#   weight (0~1) = 전체 블렌드 세기. 0 이면 원본, 1 이면 완전히 From 에 스냅.
#   softw        = 버텍스별 소프트 셀렉션 가중치(없으면 1.0).
#   from_local   = From 버텍스를 "대상 메시의 오브젝트 공간" 으로 옮긴 좌표.
#                  World 모드면 From 을 월드로 읽어 대상의 inclusiveMatrixInverse 로
#                  역변환하므로, 결과적으로 대상 버텍스가 From 의 '월드' 위치에 앉는다.
#                  Object 모드면 두 메시의 로컬 좌표를 그대로 맞춘다.
#
# 이동은 Peak 과 똑같이 shape.pnts(tweak) 에 "구간 setAttr" 로만 쓴다. 그래서
# undo/redo 스택이 정확히 맞고, 히스토리/스킨이 걸린 메시에서도 동작한다(모듈
# peak_manager 상단 주석의 함정 정리 참고). undo/preview/commit 모델과 공용 헬퍼는
# peak_manager 의 것을 그대로 재사용한다(중복 구현 없이).

import maya.cmds as cmds
import maya.api.OpenMaya as om

from .peak_manager import (
    _undo_disabled,
    _selection_map,
    _dag_path,
    _soft_weights,
    _contiguous_runs,
    _shape_of,
)


# =========================
# 짝짓기 (마야 비의존)
# =========================

MODE_ONE_TO_MANY = "1<=n"
MODE_PAIRWISE = "n<=n"


def pair_meshes(sources, targets):
    """좌(source) / 우(target) 리스트를 짝짓는다.

    - source 가 **1개**면 1 <= n : 모든 target 이 그 하나의 모양이 된다.
    - 아니면 n <= n : 리스트 순서대로 k 번째끼리. 개수가 다르면 **작은 쪽 수만큼**만 짝짓고
      남는 쪽은 unmatched 로 돌려준다(호출부가 로그에 적는다).

    반환: (mode, [(source, target), ...], 남은 source 들, 남은 target 들)
    """
    sources, targets = list(sources), list(targets)
    if len(sources) == 1:
        return MODE_ONE_TO_MANY, [(sources[0], t) for t in targets], [], []
    count = min(len(sources), len(targets))
    return (MODE_PAIRWISE, list(zip(sources[:count], targets[:count])),
            sources[count:], targets[count:])


# =========================
# 대상 메시 1개
# =========================

class MatchTarget(object):
    """Match 대상 메시 하나의 스냅샷.

    로드 시점에 "가중치 1일 때의 이동 벡터"(from_local - orig_local)를 버텍스별로
    미리 계산해 얼려둔다. 슬라이더(weight)를 끄는 동안은 이 벡터에 weight 만 곱하므로
    빠르고, 값이 스스로에게 먹여지는(feedback) 문제도 없다.
    """

    def __init__(self, shape, from_points, world=True, vtx_ids=None, soft_select=True):

        self.shape = shape
        self.dag = _dag_path(shape)
        self.fn = om.MFnMesh(self.dag)

        count = self.fn.numVertices

        if vtx_ids is None:
            ids = list(range(count))
        else:
            ids = sorted(i for i in vtx_ids if 0 <= i < count)

        # 소프트 셀렉션 가중치 (없으면 전부 1.0). 있으면 대상 id 도 그쪽을 따른다.
        self.weights = None
        if soft_select:
            w = _soft_weights(shape, count)
            if w:
                self.weights = w
                ids = sorted(w.keys())

        # 대상의 현재 오브젝트 공간 좌표(base + 기존 tweak 의 출력값).
        orig = self.fn.getPoints(om.MSpace.kObject)
        from_count = len(from_points)

        # World 모드: From(월드) 을 대상 오브젝트 공간으로 역변환할 행렬.
        inv = self.dag.inclusiveMatrixInverse() if world else None

        # id 별 "weight=1, softw=1 일 때의 이동 벡터" = from_local - orig_local
        self.delta = {}
        self.skipped = []          # From 에 대응 인덱스가 없어 건너뛴 대상 id
        kept = []
        for i in ids:
            if i >= from_count:
                self.skipped.append(i)
                continue
            fp = from_points[i]
            if world:
                fp = fp * inv       # From 월드 좌표 -> 대상 오브젝트 공간
            o = orig[i]
            self.delta[i] = (fp.x - o.x, fp.y - o.y, fp.z - o.z)
            kept.append(i)

        self.ids = kept

        self.plug = om.MFnDependencyNode(self.dag.node()).findPlug("pnts", False)
        self.base_tweaks = self._read_tweaks()

    # ---- tweak 읽기 -------------------------------------------------

    def _read_tweaks(self):
        """기존 shape.pnts 값을 {idx: (x, y, z)} 로 읽는다 (peak_manager 와 동일 방식)."""

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

    def _offsets(self, weight):
        """이번 blend 결과 tweak 값 {idx: (x, y, z)} 을 만든다 (기존 tweak 누적)."""

        out = {}
        for i in self.ids:
            k = weight * self._weight(i)
            dx, dy, dz = self.delta[i]
            bx, by, bz = self.base_tweaks.get(i, (0.0, 0.0, 0.0))
            out[i] = (bx + dx * k, by + dy * k, bz + dz * k)
        return out

    def _write(self, values):
        """{idx: (x,y,z)} 를 pnts 에 쓴다. 연속 인덱스는 구간 setAttr 로 묶는다."""

        if not values:
            return

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

    def preview(self, weight):
        """즉시 보여준다. undo 큐에는 안 올라간다."""

        with _undo_disabled():
            self._write(self._offsets(weight))

    def restore(self):
        """미리보기를 세션 시작 상태로 되돌린다 (undo 큐에 안 올라감)."""

        with _undo_disabled():
            self._write({i: self.base_tweaks.get(i, (0.0, 0.0, 0.0))
                         for i in self.ids})

    def commit(self, weight):
        """확정 기록한다. undo 가능. 미리보기 값을 스냅샷으로 되돌린 뒤 확정한다."""

        if not self.ids:
            return 0

        self.restore()

        applied = self._offsets(weight)
        self._write(applied)
        self.base_tweaks.update(applied)

        return len(self.ids)


# =========================
# 세션
# =========================

class MatchSession(object):
    """From 메시 1개 + 선택된 대상 메시들의 스냅샷 묶음."""

    def __init__(self, targets, from_name, world, from_count, mismatch):
        self.targets = targets
        self.from_name = from_name
        self.world = world
        self.from_count = from_count
        # 토폴로지가 다른(버텍스 수가 From 과 다른) 대상 [(name, count), ...]
        self.mismatch = mismatch

    # ---- 생성 -------------------------------------------------------

    @classmethod
    def from_selection(cls, from_node, world=True, soft_select=True):
        """From 메시(노드 이름) + 현재 선택으로 세션을 만든다.

        From 이 메시가 아니면 ValueError. 대상 선택이 없으면 None.
        From 자신이 선택돼 있어도 대상에서는 제외한다(자기 자신 매칭 방지).
        """

        from_shape = _shape_of(from_node)
        if not from_shape:
            raise ValueError("'From' is not a mesh: {0}".format(from_node))

        from_dag = _dag_path(from_shape)
        from_fn = om.MFnMesh(from_dag)
        space = om.MSpace.kWorld if world else om.MSpace.kObject
        from_points = from_fn.getPoints(space)
        from_count = len(from_points)
        from_name = from_shape.split("|")[-1]

        sel_map = _selection_map()
        sel_map.pop(from_shape, None)   # From 은 대상에서 제외
        if not sel_map:
            return None

        targets = []
        mismatch = []

        for shape, ids in sel_map.items():
            try:
                t = MatchTarget(shape, from_points,
                                world=world, vtx_ids=ids, soft_select=soft_select)
            except Exception:
                continue

            if t.ids:
                targets.append(t)
                if t.fn.numVertices != from_count:
                    mismatch.append((shape.split("|")[-1], t.fn.numVertices))

        if not targets:
            return None

        return cls(targets, from_name, world, from_count, mismatch)

    @classmethod
    def from_pairs(cls, pairs, world=True, soft_select=True, progress=None):
        """[(source, target), ...] 짝마다 target 메시 **전체**를 source 모양으로 (v01.10~).

        Default 탭의 좌/우 리스트가 만든 짝을 받는다(1 <= n 이면 source 가 전부 같다).
        soft_select 가 켜져 있고 target 의 버텍스를 소프트 셀렉션으로 골라 두었으면 그
        버텍스만 falloff 대로 움직인다(없으면 메시 전체).

        progress : `progress(done, total, message)` 콜백(없으면 무시) - 짝 하나 읽을 때마다.
                   UI 가 공용 진행률 팝업의 `callback()` 을 넘긴다. 코어는 위젯을 모른다.

        반환: (세션 또는 None, 건너뛴 짝 [(source, target, 이유), ...])
        """

        points = {}          # source shape -> getPoints (같은 source 는 한 번만 읽는다)
        targets, mismatch, skipped = [], [], []
        space = om.MSpace.kWorld if world else om.MSpace.kObject

        total = len(pairs)
        for k, (src, tgt) in enumerate(pairs):
            if progress:
                progress(k, total, "Reading {0}".format(tgt.split("|")[-1]))
            src_shape = _shape_of(src) if cmds.objExists(src) else None
            tgt_shape = _shape_of(tgt) if cmds.objExists(tgt) else None
            if not src_shape:
                skipped.append((src, tgt, "source is not a mesh"))
                continue
            if not tgt_shape:
                skipped.append((src, tgt, "target is not a mesh"))
                continue
            if src_shape == tgt_shape:
                skipped.append((src, tgt, "same mesh on both sides"))
                continue

            if src_shape not in points:
                points[src_shape] = om.MFnMesh(_dag_path(src_shape)).getPoints(space)
            src_points = points[src_shape]

            t = MatchTarget(tgt_shape, src_points, world=world, soft_select=soft_select)
            # 로그용 이름은 셰이프가 아니라 리스트에 보이는 트랜스폼 이름.
            t.from_name = src.split("|")[-1]
            t.target_name = tgt.split("|")[-1]
            if not t.ids:
                skipped.append((src, tgt, "no vertex to move"))
                continue
            targets.append(t)
            if t.fn.numVertices != len(src_points):
                mismatch.append((t.target_name, t.fn.numVertices,
                                 t.from_name, len(src_points)))

        if progress:
            progress(total, total, "Read {0} pair(s)".format(total))

        if not targets:
            return None, skipped

        names = sorted(set(t.from_name for t in targets))
        session = cls(targets, ", ".join(names), world, None, mismatch)
        return session, skipped

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

    @property
    def skipped_count(self):
        return sum(len(t.skipped) for t in self.targets)

    def mesh_names(self):
        return [t.shape.split("|")[-1] for t in self.targets]

    # ---- 동작 -------------------------------------------------------

    def preview(self, weight):
        for t in self.targets:
            t.preview(weight)

    def restore(self):
        for t in self.targets:
            t.restore()

    def commit(self, weight, progress=None):
        """전 대상을 확정한다. progress(done, total, message) 는 메시 하나마다(없으면 무시)."""
        moved = 0
        total = len(self.targets)
        for k, t in enumerate(self.targets):
            if progress:
                name = getattr(t, "target_name", None) or t.shape.split("|")[-1]
                progress(k, total, "Writing {0}".format(name))
            moved += t.commit(weight)
        if progress:
            progress(total, total, "Wrote {0} mesh(es)".format(total))
        return moved
