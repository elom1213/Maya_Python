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
# 델타의 공간 (mayapy 로 실측):
#   inputGeomTarget 이 worldMesh 로 연결돼 있어도 델타는 **오브젝트 공간**이다
#   (delta = 타겟 로컬 좌표 - 베이스 원본 로컬 좌표). base/target 의 transform 이
#   서로 달라도(위치·회전·스케일) 마찬가지다. 따라서 타겟 정점은 **오브젝트 공간에서**
#   (X - 1) * delta 만큼 상대 이동시키면 새 델타가 정확히 X * delta 가 된다.

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
    def _scale_live_item(item_plug, shape, factor):
        """연결된 타겟 메시를 옮겨 델타를 factor 배로 만든다.

        델타는 오브젝트 공간이므로 정점을 (factor - 1) * delta 만큼 상대 이동한다.
        반환: (처리한 포인트 수, 실패 사유 또는 None)
        """
        pts = cmds.getAttr(item_plug + ".inputPointsTarget") or []
        if not pts:
            return 0, None

        comps = cmds.getAttr(item_plug + ".inputComponentsTarget") or []
        indices = _expand_components(comps, len(pts))
        if indices is None:
            return 0, "component list did not match delta count"

        offset = factor - 1.0
        tweaks = BaseShapeManager._read_tweaks(shape)

        values = {}
        for k, vtx in enumerate(indices):
            d = pts[k]
            bx, by, bz = tweaks.get(vtx, (0.0, 0.0, 0.0))
            values[vtx] = (bx + d[0] * offset,
                           by + d[1] * offset,
                           bz + d[2] * offset)

        try:
            BaseShapeManager._write_tweaks(shape, values)
        except Exception as exc:
            return 0, "could not move target mesh '{0}' ({1})".format(shape, exc)

        return len(values), None

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
                    item_plug, shape, factor)
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
