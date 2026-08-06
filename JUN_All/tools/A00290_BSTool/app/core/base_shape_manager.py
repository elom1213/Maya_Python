# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-03
# A00290_BSTool - Base Shape 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# 목적: 선택한 blendShape 타겟의 "기본(weight=1.0) 모양"을 다시 정의한다.
#
# 아이디어:
#   blendShape 결과 = base + weight * delta  (delta = 타겟의 포인트 오프셋)
#   weight = X (예: 0.5 또는 1.3) 에서 보이던 모양을 weight = 1.0 의 모양으로 만들려면
#   delta 를 X 배 하면 된다.
#       new_delta = delta * X
#       => weight 1.0 일 때: base + 1.0 * (delta*X) = base + X*delta = 예전 weight X 모양
#
#   따라서 "값 X 의 모양을 1.0 의 기본 모양으로" == 타겟 포인트 델타를 X 배 스케일.
#
# 델타를 X 배 하는 방법은 타겟이 어떻게 저장돼 있느냐에 따라 **두 가지**다.
#
#   (A) baked 타겟 — 타겟 메시가 씬에 없고 델타만 노드에 굽혀 있다.
#       inputTarget[g].inputTargetGroup[w].inputTargetItem[i].inputPointsTarget 를
#       직접 X 배로 setAttr 한다.
#
#   (B) live 타겟 — 타겟 메시가 씬에 남아 inputGeomTarget 에 연결돼 있다.
#       이때 inputPointsTarget 은 **연결된 메시에서 매번 다시 계산되는 값**이라,
#       setAttr 로 써도 다음 평가에서 조용히 되돌아간다(에러도 안 난다).
#       -> v01.11 이전에는 이 경우 "적용됐다"고 보고만 하고 실제로는 아무 일도 없었고,
#          씬 저장이나 Shape Editor 의 Edit 진입처럼 재평가를 유발하는 순간
#          원래 모양으로 돌아온 것처럼 보였다.
#       -> 그래서 이제 **타겟 메시의 정점을 직접 옮긴다**. 델타가 곧 타겟 메시이므로
#          타겟을 옮기는 것이 "기본 모양을 바꾸는" 유일한 정공법이다.
#
# 델타의 공간 (mayapy 로 실측, v01.16 에서 정정):
#   델타가 어느 공간에 있느냐는 blendShape 의 **origin** 어트리뷰트가 정한다.
#
#     origin = 1 (local, cmds.blendShape 기본) — 델타 = 타겟 로컬 좌표 - 베이스 로컬 좌표.
#         두 오브젝트의 transform 이 달라도 순수 오브젝트 공간이다.
#     origin = 0 (world) — 델타 = (타겟 로컬 * 타겟 worldMatrix * 베이스 worldInverse)
#         - 베이스 로컬. 즉 **베이스 오브젝트 공간**이라, 타겟과 베이스의 transform 이
#         다르면(회전 · 마이너스 스케일 · 비균등 스케일) 델타는 타겟 오브젝트 공간이 아니다.
#
#   타겟 정점은 (당연히) 자기 오브젝트 공간에서만 옮길 수 있으므로, world origin 이고
#   transform 이 다르면 델타를 **타겟 오브젝트 공간으로 되돌린 뒤** 옮겨야 한다.
#       local_offset = delta * (base.worldMatrix * target.worldMatrix^-1)   ← 3x3 부분만
#   v01.15 까지는 이 변환 없이 델타를 그대로 썼다. 그래서 예컨대 타겟이 X 로 미러(scale -1)
#   되어 있으면 X 성분만 반대로 움직여, 값 0.5 를 넣어도 그 정점들만 1.5 를 넣은 것처럼 보였다
#   (= 정점마다 되기도 하고 반대로 되기도 하는 증상).
#
#   그래도 못 잡는 배치가 있을 수 있어(디포머가 낀 타겟 등), 적용 후 **델타가 정말 X 배가
#   됐는지 검증**하고, 아니면 되돌린 뒤 타겟 정점을 실제로 흔들어 응답 행렬을 **직접 재서**
#   다시 시도한다. 그래도 안 되면 원상복구하고 이유를 보고한다.

import re

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_undo import undo_chunk

from . import blendshape_utils as bsu


_COMPONENT_RE = re.compile(r"\[(\d+)(?::(\d+))?\]")


def _expand_components(comps, count):
    """inputComponentsTarget(['vtx[0]', 'vtx[3:7]', ...]) 을 정점 인덱스 목록으로 편다.

    comps 가 비어 있으면(가끔 그렇다) 0..count-1 로 본다 — Maya 가 델타를 그 순서로
    담기 때문이다. 편 개수가 델타 개수와 맞지 않으면 None 을 돌려 호출부가 건너뛴다.
    """
    if not comps:
        return list(range(count))

    out = []
    for c in comps:
        match = _COMPONENT_RE.search(c)
        if not match:
            return None
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        out.extend(range(start, end + 1))

    return out if len(out) == count else None


def _contiguous_runs(indices):
    """정렬된 인덱스를 연속 구간 [(start, end), ...] 으로 묶는다."""
    runs = []
    start = prev = None
    for i in indices:
        if start is None:
            start = prev = i
        elif i == prev + 1:
            prev = i
        else:
            runs.append((start, prev))
            start = prev = i
    if start is not None:
        runs.append((start, prev))
    return runs


class BaseShapeManager:

    # ==================================================
    # 조회
    # ==================================================

    @staticmethod
    def list_targets(bs_node):
        """blendShape 타겟 이름 목록(weight 인덱스 순)."""
        return bsu.get_blendshape_targets(bs_node)

    # ==================================================
    # 내부 헬퍼
    # ==================================================

    @staticmethod
    def _group_plug(bs_node, geo_idx, grp_idx):
        return "{0}.inputTarget[{1}].inputTargetGroup[{2}]".format(
            bs_node, geo_idx, grp_idx)

    @staticmethod
    def _live_target_shape(item_plug):
        """inputGeomTarget 에 연결된 타겟 셰이프. 연결이 없으면 None(= baked)."""
        srcs = cmds.listConnections(item_plug + ".inputGeomTarget",
                                    source=True, destination=False,
                                    shapes=True) or []
        return srcs[0] if srcs else None

    @staticmethod
    def _read_tweaks(shape):
        """shape.pnts 의 **실제로 존재하는 element** 만 {idx: (x, y, z)} 로 읽는다.

        getAttr(".pnts") 통짜 조회는 "compound with mixed type elements" 로 실패하고
        정점마다 getAttr 을 돌리면 느리다(A00380 peak_manager 와 같은 방식).
        """
        tweaks = {}
        try:
            sel = om.MSelectionList()
            sel.add(shape)
            node = sel.getDependNode(0)
            plug = om.MFnDependencyNode(node).findPlug("pnts", False)
            for i in plug.getExistingArrayAttributeIndices():
                ep = plug.elementByLogicalIndex(i)
                tweaks[i] = (ep.child(0).asFloat(),
                             ep.child(1).asFloat(),
                             ep.child(2).asFloat())
        except Exception:
            pass
        return tweaks

    @staticmethod
    def _write_tweaks(shape, values):
        """{idx: (x, y, z)} 를 shape.pnts 에 쓴다. 연속 인덱스는 구간 setAttr 로 묶는다.

        정점마다 setAttr/xform 을 돌리면 19k 메시에서 6 초대, 구간으로 묶으면 0.1 초대다.
        메시 데이터(vrts)가 아니라 tweak 에만 쓰므로 undo 도 정확히 맞는다.
        """
        for start, end in _contiguous_runs(sorted(values.keys())):
            flat = []
            for i in range(start, end + 1):
                flat.extend(values[i])
            if start == end:
                cmds.setAttr("{0}.pnts[{1}]".format(shape, start),
                             flat[0], flat[1], flat[2], type="double3")
            else:
                cmds.setAttr("{0}.pnts[{1}:{2}]".format(shape, start, end),
                             *flat, type="double3")

    # ==================================================
    # (A) baked 타겟 — 노드에 굽힌 델타를 직접 스케일
    # ==================================================

    @staticmethod
    def _scale_baked_item(item_plug, factor):
        """inputPointsTarget 을 factor 배. 반환: 처리한 포인트 수."""
        pts = cmds.getAttr(item_plug + ".inputPointsTarget") or []
        if not pts:
            return 0

        new_pts = []
        for p in pts:
            w = p[3] if len(p) > 3 else 1.0
            new_pts.append((p[0] * factor, p[1] * factor, p[2] * factor, w))

        cmds.setAttr(item_plug + ".inputPointsTarget",
                     len(new_pts), *new_pts, type="pointArray")
        return len(new_pts)

    # ==================================================
    # (B) live 타겟 — 타겟 메시 정점을 직접 옮긴다
    # ==================================================

    @staticmethod
    def _read_item_deltas(item_plug):
        """델타를 {정점: (dx, dy, dz)} 로 읽는다.

        컴포넌트 목록을 델타 개수만큼 펴지 못하면 None(호출부가 건너뛴다).
        """
        pts = cmds.getAttr(item_plug + ".inputPointsTarget") or []
        if not pts:
            return {}

        comps = cmds.getAttr(item_plug + ".inputComponentsTarget") or []
        indices = _expand_components(comps, len(pts))
        if indices is None:
            return None

        return {vtx: (pts[k][0], pts[k][1], pts[k][2])
                for k, vtx in enumerate(indices)}

    @staticmethod
    def _base_shape_for_geo(bs_node, geo_idx):
        """이 inputTarget 인덱스가 디포밍하는 베이스 셰이프 이름."""
        geos = cmds.blendShape(bs_node, query=True, geometry=True) or []
        idxs = cmds.blendShape(bs_node, query=True, geometryIndices=True) or []
        for geo, idx in zip(geos, idxs):
            if idx == geo_idx:
                return geo
        return geos[0] if len(geos) == 1 else None

    @staticmethod
    def _delta_to_local_matrix(bs_node, geo_idx, shape):
        """델타 공간의 변위를 **타겟 오브젝트 공간** 변위로 바꾸는 행렬(없으면 None).

        origin=local 이면 델타가 이미 타겟 오브젝트 공간이라 변환이 필요 없다.
        origin=world 면 델타가 베이스 오브젝트 공간이므로 base.world * target.world^-1 로
        되돌린다. 두 transform 이 같으면(대개 그렇다) 항등이라 None 을 준다.
        """
        try:
            if cmds.getAttr(bs_node + ".origin") != 0:      # 0 = world, 1 = local
                return None
        except Exception:
            return None

        base_shape = BaseShapeManager._base_shape_for_geo(bs_node, geo_idx)
        if not base_shape:
            return None

        try:
            base_m = om.MMatrix(cmds.getAttr(base_shape + ".worldMatrix[0]"))
            tgt_m = om.MMatrix(cmds.getAttr(shape + ".worldMatrix[0]"))
        except Exception:
            return None

        mat = base_m * tgt_m.inverse()
        return None if mat.isEquivalent(om.MMatrix.kIdentity, 1e-6) else mat

    @staticmethod
    def _measure_local_matrix(item_plug, shape, deltas, saved):
        """타겟 정점을 실제로 흔들어 '로컬 변위 -> 델타 변위' 응답을 재고, 그 역행렬을 준다.

        계산으로 못 맞추는 배치(타겟에 디포머가 끼어 있는 등)를 위한 폴백이다.
        변환은 선형이라 정점 하나를 x/y/z 로 한 번씩 밀어 보면 3x3 이 그대로 나온다.
        """
        probe = max(deltas, key=lambda v: sum(c * c for c in deltas[v]))
        origin = saved.get(probe, (0.0, 0.0, 0.0))
        step = 1.0
        rows = []

        try:
            for axis in range(3):
                moved = list(origin)
                moved[axis] += step
                BaseShapeManager._write_tweaks(shape, {probe: tuple(moved)})

                after = BaseShapeManager._read_item_deltas(item_plug)
                if not after or probe not in after:
                    return None
                d0, d1 = deltas[probe], after[probe]
                rows.append([(d1[i] - d0[i]) / step for i in range(3)])
        finally:
            BaseShapeManager._write_tweaks(shape, {probe: origin})

        mat = om.MMatrix([rows[0][0], rows[0][1], rows[0][2], 0.0,
                          rows[1][0], rows[1][1], rows[1][2], 0.0,
                          rows[2][0], rows[2][1], rows[2][2], 0.0,
                          0.0, 0.0, 0.0, 1.0])
        if abs(mat.det3x3()) < 1e-9:
            return None
        return mat.inverse()

    @staticmethod
    def _offset_target_mesh(shape, deltas, saved, factor, mat):
        """타겟 정점을 (factor - 1) * delta 만큼(필요하면 mat 로 공간을 되돌려) 옮긴다."""
        offset = factor - 1.0
        values = {}
        for vtx, d in deltas.items():
            vec = om.MVector(d[0], d[1], d[2])
            if mat is not None:
                vec = vec * mat
            bx, by, bz = saved.get(vtx, (0.0, 0.0, 0.0))
            values[vtx] = (bx + vec.x * offset,
                           by + vec.y * offset,
                           bz + vec.z * offset)
        BaseShapeManager._write_tweaks(shape, values)

    @staticmethod
    def _deltas_scaled_ok(item_plug, before, factor):
        """델타가 정말 factor 배가 됐는지 확인한다(정점 단위로 대조).

        스케일 뒤 아주 작아진 델타는 마야가 목록에서 걷어낼 수 있으므로 위치가 아니라
        **정점 번호로** 대조하고, 없는 정점은 0 으로 본다.
        """
        after = BaseShapeManager._read_item_deltas(item_plug)
        if after is None:
            return False

        for vtx, d in before.items():
            got = after.get(vtx, (0.0, 0.0, 0.0))
            for i in range(3):
                expected = d[i] * factor
                if abs(got[i] - expected) > 1e-4 * max(1.0, abs(expected)):
                    return False
        return True

    @staticmethod
    def _scale_live_item(bs_node, geo_idx, item_plug, shape, factor):
        """연결된 타겟 메시를 옮겨 델타를 factor 배로 만든다.

        델타 공간(= blendShape 의 origin 과 두 오브젝트의 worldMatrix)을 되돌려 옮기고,
        정말 factor 배가 됐는지 확인한다. 아니면 되돌린 뒤 응답 행렬을 직접 재서 한 번 더
        시도하고, 그래도 아니면 원상복구한다.

        반환: (처리한 포인트 수, 실패 사유 또는 None)
        """
        deltas = BaseShapeManager._read_item_deltas(item_plug)
        if deltas is None:
            return 0, "component list did not match delta count"
        if not deltas:
            return 0, None

        tweaks = BaseShapeManager._read_tweaks(shape)
        saved = {vtx: tweaks.get(vtx, (0.0, 0.0, 0.0)) for vtx in deltas}

        try:
            mat = BaseShapeManager._delta_to_local_matrix(bs_node, geo_idx, shape)
            BaseShapeManager._offset_target_mesh(shape, deltas, saved, factor, mat)
            if BaseShapeManager._deltas_scaled_ok(item_plug, deltas, factor):
                return len(deltas), None

            # 공간 가정이 틀렸다. 되돌리고 응답을 직접 재서 다시.
            BaseShapeManager._write_tweaks(shape, saved)
            measured = BaseShapeManager._measure_local_matrix(
                item_plug, shape, deltas, saved)
            if measured is not None:
                BaseShapeManager._offset_target_mesh(
                    shape, deltas, saved, factor, measured)
                if BaseShapeManager._deltas_scaled_ok(item_plug, deltas, factor):
                    return len(deltas), None

            BaseShapeManager._write_tweaks(shape, saved)
        except Exception as exc:
            return 0, "could not move target mesh '{0}' ({1})".format(shape, exc)

        return 0, ("'{0}' left unchanged - moving its vertices does not scale the"
                   " deltas as expected (target mesh may be deformed or"
                   " constrained)".format(shape))

    # ==================================================
    # 델타 스케일 (그룹 단위)
    # ==================================================

    @staticmethod
    def _scale_group_deltas(bs_node, geo_idx, grp_idx, factor):
        """inputTargetGroup 의 모든 inputTargetItem 델타를 factor 배.

        item 마다 live(타겟 메시 연결) / baked(델타만) 를 따로 판정한다. in-between
        타겟은 item 이 여러 개이고 각자 다른 메시에 연결돼 있을 수 있다.

        반환: (포인트 수, live item 수, 실패 사유 목록)
        """
        group_plug = BaseShapeManager._group_plug(bs_node, geo_idx, grp_idx)

        item_indices = cmds.getAttr(group_plug + ".inputTargetItem",
                                    multiIndices=True) or []
        points_done = 0
        live_items = 0
        problems = []

        for it in item_indices:
            item_plug = "{0}.inputTargetItem[{1}]".format(group_plug, it)
            shape = BaseShapeManager._live_target_shape(item_plug)

            if shape:
                pts, problem = BaseShapeManager._scale_live_item(
                    bs_node, geo_idx, item_plug, shape, factor)
                points_done += pts
                if pts:
                    live_items += 1
                if problem:
                    problems.append(problem)
            else:
                points_done += BaseShapeManager._scale_baked_item(item_plug, factor)

        return points_done, live_items, problems

    @staticmethod
    def apply_value_as_default(bs_node, target_names, value):
        """선택 타겟들의 weight=value 모양을 weight=1.0 의 기본 모양으로 만든다.

        타겟이 baked 면 노드의 델타를, live(타겟 메시가 연결됨)면 **타겟 메시 자체**를
        고쳐서 그 순간 기본 모양이 바뀌게 한다. 어느 쪽이든 씬을 저장하거나 Shape Editor
        의 Edit 로 들어가도 되돌아오지 않는다.

        Args:
            bs_node      : blendShape 노드 이름
            target_names : 대상 타겟 이름 리스트
            value        : 기준 값 X (0 이 아니어야 함)

        반환: (처리한 타겟 수, 메시지)
        """
        if not bsu.is_blendshape(bs_node):
            return 0, "[Warning] '{0}' is not a valid blendShape node.".format(bs_node)

        if not target_names:
            return 0, "[Warning] No target selected."

        if value is None or abs(value) < 1e-6:
            return 0, "[Warning] Value must be non-zero."

        name_to_idx = bsu.target_index_map(bs_node)
        geo_indices = cmds.getAttr(bs_node + ".inputTarget", multiIndices=True) or [0]

        done = 0
        live_targets = 0
        skipped = []
        problems = []

        with undo_chunk():
            for name in target_names:
                grp_idx = name_to_idx.get(name)
                if grp_idx is None:
                    skipped.append(name)
                    continue

                touched_pts = 0
                touched_live = 0
                for geo_idx in geo_indices:
                    pts, live, probs = BaseShapeManager._scale_group_deltas(
                        bs_node, geo_idx, grp_idx, value)
                    touched_pts += pts
                    touched_live += live
                    problems.extend("{0}: {1}".format(name, p) for p in probs)

                if touched_pts == 0:
                    skipped.append(name)
                    continue

                done += 1
                if touched_live:
                    live_targets += 1

        msg = "[Base Shape] '{0}' : {1} target(s) rescaled by x{2} (value {2} -> 1.0).".format(
            bs_node, done, value)
        if live_targets:
            msg += (" {0} of them are live targets - their target mesh was moved"
                    " so the change sticks.".format(live_targets))
        if skipped:
            msg += " Skipped (no stored deltas / unknown): {0}".format(", ".join(skipped))
        if problems:
            msg += " Problems: {0}".format("; ".join(problems))

        return done, msg
