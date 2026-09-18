# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00380_MeshTool - Match > By Weight 코어 로직
#
# 스킨 웨이트를 **마스크**로 써서 메시를 타깃 쪽으로 옮긴다. 블렌드셰이프에서 타깃마다
# 웨이트 맵(마스크)을 칠해 "이 타깃이 원본을 얼마나 바꿀지" 를 정하는 것과 결과가 같다.
#
#   M_w   : 조인트에 바인드된 메시. 웨이트(마스크)만 읽는다.
#   jnt_i : M_w 를 바인드한 조인트 중 체크한 것.
#   M_tgt : 목표 모양. 버텍스 인덱스로 대응한다.
#   M_j   : 옮길 메시들 (M_w · M_tgt 와 토폴로지가 같다).
#
#   new_local[v] = cur_local[v] + mask[v] * strength * (tgt_local[v] - cur_local[v])
#   mask[v]      = sum( weight(jnt, v) for jnt in M_j 에 짝지은 조인트 ), 1 로 자른다
#
# 좌표는 블렌드셰이프처럼 **오브젝트(로컬) 공간**이다. 델타 = M_tgt 로컬 - M_j 로컬.
#
# 짝짓는 방법 (어느 조인트의 웨이트를 어느 M_j 에 쓸까):
#   PAIR_ORDER : 체크한 조인트 k 번째 -> M_j 리스트 k 번째 (jnt_01 -> M_01, jnt_02 -> M_02 ...).
#                조인트별로 영역을 쪼갠 코렉티브를 만드는 흐름.
#   PAIR_SUM   : 체크한 조인트 웨이트의 합을 **모든 M_j** 에 같은 마스크로.
#
# 이동은 Match(Default) 와 같은 `MatchTarget` 을 쓴다 — shape.pnts 구간 setAttr 라
# Ctrl+Z 한 번에 되돌아가고 히스토리/스킨이 걸린 M_j 에서도 동작한다.
# 단 M_j 의 blendShape 타겟 Edit(sculpt) 가 켜져 있으면 pnts 가 타겟으로 우회돼 쓰기가
# 실패한다 → 그 타겟 아이템의 델타에 직접 더한다(`sculpt_target`, v01.12~).

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from .peak_manager import _dag_path, _shape_of
from .match_manager import MatchTarget
from . import sculpt_target


PAIR_ORDER = "order"
PAIR_SUM = "sum"


# =========================
# 스킨
# =========================

def skin_cluster_of(mesh):
    """mesh 를 변형하는 skinCluster 이름. 없으면 None."""
    shape = _shape_of(mesh)
    if not shape:
        return None
    hist = cmds.listHistory(shape, pruneDagObjects=True) or []
    skins = cmds.ls(hist, type="skinCluster") or []
    return skins[0] if skins else None


def _skin_fn(skin):
    sel = om.MSelectionList()
    sel.add(skin)
    return oma.MFnSkinCluster(sel.getDependNode(0))


class SkinWeights(object):
    """M_w 의 스킨 웨이트 스냅샷. 조인트 이름 -> 버텍스별 웨이트."""

    def __init__(self, mesh):
        self.mesh = mesh
        self.shape = _shape_of(mesh) if cmds.objExists(mesh) else None
        if not self.shape:
            raise ValueError("Not a mesh: {0}".format(mesh))
        self.skin = skin_cluster_of(mesh)
        if not self.skin:
            raise ValueError("{0} is not bound to joints (no skinCluster)".format(
                mesh.split("|")[-1]))

        fn = _skin_fn(self.skin)
        paths = fn.influenceObjects()
        self.joints = [p.partialPathName() for p in paths]

        dag = _dag_path(self.shape)
        self.vertex_count = om.MFnMesh(dag).numVertices
        comp = om.MFnSingleIndexedComponent()
        comp_obj = comp.create(om.MFn.kMeshVertComponent)
        comp.setCompleteData(self.vertex_count)
        flat, n_inf = fn.getWeights(dag, comp_obj)
        self._flat = flat
        self._n = n_inf

    def weights_of(self, joint):
        """joint 의 버텍스별 웨이트 리스트(길이 = 버텍스 수)."""
        col = self.joints.index(joint)
        n = self._n
        return [self._flat[v * n + col] for v in range(self.vertex_count)]

    def bound_joints(self):
        """웨이트가 하나라도 0 보다 큰 인플루언스. (웨이트 0 인 인플루언스도 목록엔 남긴다.)"""
        n = self._n
        used = set()
        for v in range(self.vertex_count):
            base = v * n
            for c in range(n):
                if self._flat[base + c] > 1e-6:
                    used.add(c)
        return [j for c, j in enumerate(self.joints) if c in used]

    def mask(self, joints):
        """joints 웨이트의 합(1 로 자름). {v: w} - 0 인 버텍스는 뺀다."""
        cols = [self.joints.index(j) for j in joints if j in self.joints]
        n = self._n
        out = {}
        for v in range(self.vertex_count):
            base = v * n
            w = sum(self._flat[base + c] for c in cols)
            if w > 1e-6:
                out[v] = min(w, 1.0)
        return out


# =========================
# 짝짓기
# =========================

def make_pairs(meshes, joints, mode=PAIR_ORDER):
    """[(mesh, [joint, ...]), ...] 와 짝이 안 맞아 남은 것(meshes, joints) 을 돌려준다."""
    if mode == PAIR_SUM:
        if not joints:
            return [], list(meshes), []
        return [(m, list(joints)) for m in meshes], [], []
    n = min(len(meshes), len(joints))
    pairs = [(meshes[k], [joints[k]]) for k in range(n)]
    return pairs, list(meshes[n:]), list(joints[n:])


# =========================
# 적용
# =========================

def apply(weight_mesh, target_mesh, pairs, strength=1.0):
    """짝마다 M_j 를 M_tgt 쪽으로 마스크만큼 옮긴다. 호출부가 undo_chunk 로 감싼다.

    Returns:
        (done, skipped)
        done    = [(mesh, joints, moved_vertex_count, max_mask, sculpt_label)]
                  sculpt_label = Edit 중이라 델타를 넣은 타겟("bs.target") 또는 None
        skipped = [(mesh, reason)]
    """
    sw = SkinWeights(weight_mesh)

    tgt_shape = _shape_of(target_mesh) if cmds.objExists(target_mesh) else None
    if not tgt_shape:
        raise ValueError("Target is not a mesh: {0}".format(target_mesh))
    tgt_points = om.MFnMesh(_dag_path(tgt_shape)).getPoints(om.MSpace.kObject)
    if len(tgt_points) != sw.vertex_count:
        raise ValueError(
            "Target has {0} vertices, the weight mesh has {1} - they must be the "
            "same mesh".format(len(tgt_points), sw.vertex_count))

    done, skipped = [], []
    for mesh, joints in pairs:
        shape = _shape_of(mesh) if cmds.objExists(mesh) else None
        if not shape:
            skipped.append((mesh, "not a mesh"))
            continue
        if shape == tgt_shape:
            skipped.append((mesh, "is the target mesh"))
            continue
        count = om.MFnMesh(_dag_path(shape)).numVertices
        if count != sw.vertex_count:
            skipped.append((mesh, "{0} vertices, expected {1}".format(
                count, sw.vertex_count)))
            continue

        mask = sw.mask(joints)
        if not mask:
            skipped.append((mesh, "zero weight on {0}".format(", ".join(joints))))
            continue

        # 대응 버텍스 = 마스크가 있는 것만. 마스크가 곧 MatchTarget 의 버텍스별 가중치다.
        t = MatchTarget(shape, tgt_points, world=False,
                        vtx_ids=sorted(mask.keys()), soft_select=False)
        t.weights = mask

        # blendShape 타겟 Edit 가 켜져 있으면 pnts 쓰기가 타겟으로 새어 에러가 난다
        # (sculpt_target 상단 주석). 그 타겟의 델타에 직접 더한다.
        st = sculpt_target.find_sculpt_target(shape)
        if st is not None:
            offsets = {}
            for i in t.ids:
                k = strength * mask[i]
                dx, dy, dz = t.delta[i]
                offsets[i] = (dx * k, dy * k, dz * k)
            moved = sculpt_target.add_offsets(shape, st, offsets)
        else:
            moved = t.commit(strength)
        done.append((mesh, list(joints), moved, max(mask.values()),
                     st.label if st is not None else None))
    return done, skipped
