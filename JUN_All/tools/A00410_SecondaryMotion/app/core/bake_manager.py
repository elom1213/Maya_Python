# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-29
# A00410_SecondaryMotion core - 샘플링 캐시 / 솔브 / 기록(프리뷰 레이어 · 확정) 오케스트레이션.
#
# 흐름
# ----
#   prepare()  씬에서 체인을 찾고 프레임별 원본 포즈를 **한 번** 샘플링해 캐시에 담는다.
#              (유일하게 비싼 단계 — 20본 x 300프레임 기준 약 0.37s)
#   update()   캐시로 솔브 + 회전 재구성 + 프리뷰 레이어에 벌크 기록. 약 13ms 이라
#              슬라이더를 드래그하는 동안 매번 다시 돌려도 실시간이다.
#   apply()    결과를 확정한다. 프리뷰 레이어를 최종 이름으로 바꾸거나(Layer 모드),
#              컨트롤러/조인트의 커브에 직접 굽는다(Keys 모드).
#
# 왜 override 레이어인가 (mayapy 검증)
#   override 애님 레이어에 **절대 회전값**을 넣으면 weight 로 base 와 선형 블렌드된다
#   (base=50, layer=90 -> weight 0.5 에서 70). 원본 애니를 보존한 채 강도를 조절할 수
#   있고, 레이어만 지우면 원상복구다. additive 레이어의 회전 합성(쿼터니언) 규칙을
#   추측할 필요도 없다.
#
# 프리뷰 갱신은 MFnAnimCurve(API) 로 값만 덮어써서 **undo 큐를 건드리지 않는다**.
# 레이어 자체는 cmds 로 만들어 undo 가 가능하므로, Ctrl+Z 하면 레이어째 사라진다.

import maya.cmds as cmds
from maya.api import OpenMaya as om, OpenMayaAnim as oma

from tools.A00410_SecondaryMotion.app.core import chain_solver
from tools.A00410_SecondaryMotion.app.core import pose_builder
from tools.A00410_SecondaryMotion.app.core import scene_sampler


# 프리뷰 전용 레이어 이름(고정). Apply/Reset 시 정리된다.
PREVIEW_LAYER = "SM_preview_LYR"

# 결과를 쓰는 회전 어트리뷰트.
ROT_ATTRS = ("rotateX", "rotateY", "rotateZ")

# 출력 모드
OUTPUT_LAYER = "layer"     # override 애님 레이어(기본) — 원본 보존 + weight 로 강도 조절
OUTPUT_KEYS = "keys"       # 컨트롤러/조인트 커브에 직접 굽기


def _layer_exists(name):
    return bool(cmds.ls(name, type="animLayer"))


def delete_layer(name):
    if _layer_exists(name):
        try:
            cmds.delete(name)
            return True
        except Exception:
            return False
    return False


class SecondaryMotionSession(object):
    """샘플링 캐시 + 프리뷰 상태를 들고 있는 작업 세션."""

    def __init__(self, log=None):
        self._log = log
        self.samples = []          # [ChainSample, ...]
        self.owners = []           # [i in chain -> 이 체인이 그 노드를 쓰는가]
        self.frames = []
        self.target_type = scene_sampler.TARGET_CTRL
        self.fps = chain_solver.REF_FPS
        self._curves = {}          # (node, attr) -> 프리뷰 레이어 커브 이름
        self._last_writes = {}     # node -> [(rx,ry,rz), ...]
        self.branched = []
        self.missing = []

    # ------------------------------------------------------------ helpers

    def log(self, msg, warn=False):
        if callable(self._log):
            self._log(msg, warn)

    def has_cache(self):
        return bool(self.samples)

    def node_count(self):
        return len(self._last_writes) or sum(s.count() for s in self.samples)

    # ------------------------------------------------------------ prepare

    def prepare(self, nodes, mode, target_type, start, end, step=1.0,
                dummy_tip=True):
        """체인 해석 + 프레임별 원본 포즈 샘플링(비싼 단계, 한 번만).

        dummy_tip=True 면 체인 끝에 가상 점을 붙여 **마지막 노드도 회전**하게 한다.

        반환: (체인 수, 노드 수, 프레임 수). 실패하면 예외를 던진다.
        """
        # 프리뷰 레이어가 살아 있으면 자기 출력을 되먹으므로 먼저 지운다.
        self.clear_preview()

        chains, missing, branched = scene_sampler.resolve_chains(
            nodes, mode, target_type)
        self.missing = missing
        self.branched = branched

        if not chains:
            raise RuntimeError(
                "No chain resolved. A chain needs at least 2 nodes "
                "(root + one child).")

        if start > end:
            start, end = end, start
        step = max(0.01, float(step))

        frames = []
        f = float(start)
        while f <= float(end) + 1e-6:
            frames.append(round(f, 5))
            f += step
        if len(frames) < 2:
            raise RuntimeError("Frame range is too short (need 2+ frames).")

        self.frames = frames
        self.target_type = target_type
        self.fps = scene_sampler.scene_fps()

        # 분기로 체인이 쪼개졌을 때 같은 노드가 여러 체인에 들어간다.
        # 먼저 나온(더 긴) 체인이 그 노드의 회전을 소유한다.
        self.samples = []
        self.owners = []
        claimed = set()
        for chain in chains:
            sample = scene_sampler.sample_chain(
                chain, frames, target_type, dummy_tip=dummy_tip)
            own = []
            for node in chain:
                own.append(node not in claimed)
                claimed.add(node)
            self.samples.append(sample)
            self.owners.append(own)

        self._curves = {}
        self._last_writes = {}
        return len(chains), len(claimed), len(frames)

    # -------------------------------------------------------------- solve

    def solve(self, params):
        """캐시로 솔브 + 회전 재구성. 반환: {node: [(rx,ry,rz) 프레임별]}"""
        if not self.samples:
            raise RuntimeError("Nothing prepared yet.")

        params = params.copy()
        params.fps = self.fps

        writes = {}
        for sample, own in zip(self.samples, self.owners):
            sim = chain_solver.solve(sample.positions, params)
            rots = pose_builder.build_rotations(sample, sim)
            # rots 는 팁을 제외한 노드 수 - 1 개
            for i, values in enumerate(rots):
                if not own[i]:
                    continue
                writes[sample.nodes[i]] = values

        self._last_writes = writes
        return writes

    # ------------------------------------------------------------ preview

    def update_preview(self, params):
        """솔브 결과를 프리뷰 레이어에 기록(빠른 경로). 반환: 기록한 노드 수."""
        writes = self.solve(params)
        if not writes:
            return 0

        layer = self._ensure_layer(PREVIEW_LAYER, writes.keys())
        self._write_curves(layer, writes)
        return len(writes)

    def clear_preview(self):
        """프리뷰 레이어 제거(원본 애니로 복귀)."""
        self._curves = {}
        return delete_layer(PREVIEW_LAYER)

    # -------------------------------------------------------------- apply

    def apply(self, params, output_mode, layer_name=None):
        """결과 확정. 반환: (노드 수, 안내 메시지)"""
        writes = self._last_writes or self.solve(params)
        if not writes:
            raise RuntimeError("Nothing to apply.")

        if output_mode == OUTPUT_LAYER:
            name = layer_name or self._default_layer_name()
            if _layer_exists(PREVIEW_LAYER) and self._curves:
                # 프리뷰 레이어를 그대로 최종 레이어로 승격(다시 계산하지 않는다).
                final = cmds.rename(PREVIEW_LAYER, name)
                self._curves = {}
                return len(writes), (
                    "Applied to override anim layer '{0}' ({1} nodes). "
                    "Use the layer weight to dial the amount.".format(final, len(writes)))

            final = self._ensure_layer(name, writes.keys(), unique=True)
            self._write_curves(final, writes)
            self._curves = {}
            return len(writes), (
                "Applied to override anim layer '{0}' ({1} nodes). "
                "Use the layer weight to dial the amount.".format(final, len(writes)))

        # keys: 컨트롤러/조인트 커브에 직접 굽는다.
        self.clear_preview()
        self._bake_keys(writes)
        return len(writes), (
            "Baked keys onto {0} nodes, frames {1}~{2}.".format(
                len(writes), self.frames[0], self.frames[-1]))

    # ------------------------------------------------------ layer/curves

    def _default_layer_name(self):
        if not self.samples:
            return "SM_LYR"
        base = self.samples[0].nodes[0].split("|")[-1].split(":")[-1]
        return "SM_{0}_LYR".format(base)

    def _ensure_layer(self, name, nodes, unique=False):
        """override 애님 레이어를 만들고 대상 회전 어트리뷰트를 등록한다.

        레이어 커브는 만들자마자 이름을 캐시해 둔다(이후 갱신은 값만 덮어쓴다).
        레이어 안의 커브 이름은 규칙에 의존하지 말고 **추가 전/후 차집합**으로 찾는다.
        """
        if _layer_exists(name) and self._curves and not unique:
            return name

        # 이름이 이미 있으면 Maya 가 알아서 유니크한 이름을 만들어 돌려준다.
        layer = cmds.animLayer(name, override=True)

        plugs = []
        for node in nodes:
            for at in ROT_ATTRS:
                plugs.append("{0}.{1}".format(node, at))
        cmds.animLayer(layer, edit=True, attribute=plugs)

        # 레이어 커브를 하나씩 만들면서 이름을 잡아둔다.
        first = self.frames[0]
        self._curves = {}
        for node in nodes:
            for at in ROT_ATTRS:
                before = set(cmds.animLayer(layer, q=True, animCurves=True) or [])
                cmds.setKeyframe(node, at=at, t=first,
                                 v=cmds.getAttr("{0}.{1}".format(node, at)),
                                 animLayer=layer)
                after = set(cmds.animLayer(layer, q=True, animCurves=True) or [])
                new = list(after - before)
                if new:
                    self._curves[(node, at)] = new[0]
        return layer

    def _write_curves(self, layer, writes):
        """프리뷰/최종 레이어 커브에 값 벌크 기록.

        키 개수가 이미 맞으면 값만 덮어쓰고(가장 빠름), 아니면 전부 다시 만든다.
        """
        times = om.MTimeArray()
        for f in self.frames:
            times.append(om.MTime(f, om.MTime.uiUnit()))
        n = len(self.frames)

        for node, values in writes.items():
            for ai, at in enumerate(ROT_ATTRS):
                crv = self._curves.get((node, at))
                if not crv or not cmds.objExists(crv):
                    continue
                sel = om.MSelectionList()
                sel.add(crv)
                fn = oma.MFnAnimCurve(sel.getDependNode(0))

                if fn.numKeys == n:
                    for k in range(n):
                        fn.setValue(k, _rad(values[k][ai]))
                else:
                    while fn.numKeys:
                        fn.remove(fn.numKeys - 1)
                    va = om.MDoubleArray()
                    for k in range(n):
                        va.append(_rad(values[k][ai]))
                    fn.addKeys(times, va)

    def _bake_keys(self, writes):
        """base 커브에 직접 키를 굽는다(undo 가능한 cmds 경로)."""
        start, end = self.frames[0], self.frames[-1]
        for node, values in writes.items():
            for at in ROT_ATTRS:
                try:
                    cmds.cutKey(node, at=at, time=(start, end), clear=True)
                except Exception:
                    pass
        for node, values in writes.items():
            for k, f in enumerate(self.frames):
                v = values[k]
                for ai, at in enumerate(ROT_ATTRS):
                    cmds.setKeyframe(node, at=at, t=f, v=v[ai])


def _rad(deg):
    return deg * 0.017453292519943295
