# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-30
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
#
# 진행률 콜백
# ----------
# 오래 걸리는 단계(prepare / solve / 기록)는 모두 `progress(done, total, message=None)`
# 콜백을 선택 인자로 받는다. UI 는 여기에 진행률 팝업의 콜백을 꽂고, 프리뷰처럼 빠른
# 경로는 그냥 넘기지 않는다(None 이면 아무 일도 하지 않는다). core 는 위젯을 모른다.

import maya.cmds as cmds
from maya.api import OpenMaya as om, OpenMayaAnim as oma

from tools.A00410_SecondaryMotion.app.core import chain_solver
from tools.A00410_SecondaryMotion.app.core import outputs
from tools.A00410_SecondaryMotion.app.core import pose_builder
from tools.A00410_SecondaryMotion.app.core import scene_sampler


# 프리뷰 전용 레이어 이름(고정). Apply/Reset 시 정리된다.
PREVIEW_LAYER = "SM_preview_LYR"

# 결과를 쓰는 회전 어트리뷰트.
ROT_ATTRS = ("rotateX", "rotateY", "rotateZ")

# 출력 id — 실제 구현은 outputs.py 의 레지스트리에 있다(새 출력은 그쪽에만 추가).
OUTPUT_LAYER = outputs.OUTPUT_LAYER
OUTPUT_KEYS = outputs.OUTPUT_KEYS
OUTPUT_NODE = outputs.OUTPUT_NODE


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
        self.empty_roots = []
        # 마지막 solve() 의 체인별 루프 진단(Loop 가 꺼져 있으면 빈 목록).
        self.loop_infos = []

    # ------------------------------------------------------------ helpers

    def log(self, msg, warn=False):
        if callable(self._log):
            self._log(msg, warn)

    def has_cache(self):
        return bool(self.samples)

    def loop_report(self):
        """마지막 solve() 의 루프 진단을 UI 로그용 [(메시지, warn), ...] 로.

        체인이 여럿이면 **가장 나쁜 값**으로 한 줄에 모은다(체인마다 줄이 늘면 로그가
        읽히지 않는다). Loop 가 꺼져 있었으면 빈 목록.
        """
        infos = [i for i in self.loop_infos if i is not None]
        if not infos:
            return []

        out = []
        worst_in = max(infos, key=lambda i: i.input_gap)
        if not worst_in.input_cyclic:
            out.append((
                "Loop: the first and last frame of the range are NOT the same pose "
                "(off by {0:.4f}). The result can only cycle as well as the source "
                "animation does.".format(worst_in.input_gap), True))

        worst = max(infos, key=lambda i: i.residual)
        cycles = max(i.cycles for i in infos)
        if worst.converged:
            out.append((
                "Loop: cycled after {0} pre-roll pass(es), seam error {1:.6f}.".format(
                    cycles, worst.residual), False))
        else:
            out.append((
                "Loop: still settling after {0} pre-roll pass(es), seam error {1:.6f} "
                "(> {2:.6f}). Raise Damping / Stiffness, or use a longer range.".format(
                    cycles, worst.residual, worst.tolerance), True))
        return out

    def node_count(self):
        return len(self._last_writes) or sum(s.count() for s in self.samples)

    # ------------------------------------------------------------ prepare

    def prepare(self, nodes, mode, target_type, start, end, step=1.0,
                dummy_tip=True, progress=None):
        """체인 해석 + 프레임별 원본 포즈 샘플링(비싼 단계, 한 번만).

        dummy_tip=True 면 체인 끝에 가상 점을 붙여 **마지막 노드도 회전**하게 한다.
        progress(done, total, message=None) 를 주면 체인 x 프레임 단위로 진행을 보고한다.

        반환: (체인 수, 노드 수, 프레임 수). 실패하면 예외를 던진다.
        """
        # 프리뷰 레이어가 살아 있으면 자기 출력을 되먹으므로 먼저 지운다.
        self.clear_preview()

        res = scene_sampler.resolve_chains(nodes, mode, target_type)
        chains = res.chains
        self.missing = res.missing
        self.branched = res.branched
        self.empty_roots = res.empty_roots

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

        # 진행률은 '체인 수 x 프레임 수' 를 전체 작업량으로 본다.
        total_units = max(1, len(chains) * len(frames))
        done_units = 0

        for ci, chain in enumerate(chains):
            chain_progress = None
            if progress:
                label = "chain {0}/{1}  ({2} frames)".format(
                    ci + 1, len(chains), len(frames))

                def chain_progress(done, total, message=None,
                                   _base=done_units, _label=label):
                    progress(_base + done, total_units, _label)

            sample = scene_sampler.sample_chain(
                chain, frames, target_type, dummy_tip=dummy_tip,
                progress=chain_progress)
            done_units += len(frames)
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

    def solve(self, params, progress=None):
        """캐시로 솔브 + 회전 재구성. 반환: {node: [(rx,ry,rz) 프레임별]}"""
        if not self.samples:
            raise RuntimeError("Nothing prepared yet.")

        params = params.copy()
        params.fps = self.fps

        writes = {}
        loop = bool(getattr(params, "loop", False))
        self.loop_infos = []
        total = len(self.samples)
        for ci, (sample, own) in enumerate(zip(self.samples, self.owners)):
            if loop:
                # 사이클 정상상태 — 첫/마지막 프레임의 흔들림이 같아진다.
                sim, info = chain_solver.solve_loop(sample.positions, params)
                self.loop_infos.append(info)
            else:
                sim = chain_solver.solve(sample.positions, params)
            rots = pose_builder.build_rotations(sample, sim)
            # rots 는 팁을 제외한 노드 수 - 1 개
            for i, values in enumerate(rots):
                if not own[i]:
                    continue
                writes[sample.nodes[i]] = values
            if progress:
                progress(ci + 1, total, "chain {0}/{1}".format(ci + 1, total))

        self._last_writes = writes
        return writes

    # ------------------------------------------------------------ preview

    def update_preview(self, params):
        """솔브 결과를 프리뷰 레이어에 기록(빠른 경로). 반환: 기록한 노드 수."""
        writes = self.solve(params)
        if not writes:
            return 0

        layer = self.ensure_layer(PREVIEW_LAYER, writes.keys())
        self.write_curves(layer, writes)
        return len(writes)

    def clear_preview(self):
        """프리뷰 레이어 제거(원본 애니로 복귀)."""
        self._curves = {}
        return delete_layer(PREVIEW_LAYER)

    def has_preview(self):
        """프리뷰 레이어가 살아 있고 우리가 만든 커브를 알고 있는가."""
        return bool(_layer_exists(PREVIEW_LAYER) and self._curves)

    def promote_preview(self, name):
        """프리뷰 레이어를 최종 이름으로 승격(재계산 없음). 반환: 실제 레이어 이름."""
        final = cmds.rename(PREVIEW_LAYER, name)
        self._curves = {}
        return final

    def forget_layer(self):
        """레이어 커브 캐시를 버린다(다음 프리뷰가 레이어를 새로 만든다)."""
        self._curves = {}

    # -------------------------------------------------------------- apply

    def apply(self, params, output_id, progress=None, **kw):
        """결과 확정. 실제 기록은 outputs.py 의 spec 이 담당한다.

        새 출력(예: A00390 처럼 라이브 노드망)을 붙일 때 이 함수는 손댈 필요가 없다 —
        outputs.py 에 spec 을 register() 하면 된다.

        반환: (노드 수, 안내 메시지)
        """
        spec = outputs.get(output_id)

        writes = None
        if spec.needs_solve:
            writes = self._last_writes or self.solve(params)
            if not writes:
                raise RuntimeError("Nothing to apply.")

        return spec.apply(self, params, writes, progress=progress, **kw)

    # ------------------------------------------------------ layer/curves

    def default_layer_name(self):
        if not self.samples:
            return "SM_LYR"
        base = self.samples[0].nodes[0].split("|")[-1].split(":")[-1]
        return "SM_{0}_LYR".format(base)

    def ensure_layer(self, name, nodes, unique=False, progress=None):
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
        node_list = list(nodes)
        for ni, node in enumerate(node_list):
            for at in ROT_ATTRS:
                before = set(cmds.animLayer(layer, q=True, animCurves=True) or [])
                cmds.setKeyframe(node, at=at, t=first,
                                 v=cmds.getAttr("{0}.{1}".format(node, at)),
                                 animLayer=layer)
                after = set(cmds.animLayer(layer, q=True, animCurves=True) or [])
                new = list(after - before)
                if new:
                    self._curves[(node, at)] = new[0]
            if progress:
                progress(ni + 1, len(node_list), "layer curves  {0}/{1}".format(
                    ni + 1, len(node_list)))
        return layer

    def write_curves(self, layer, writes, progress=None):
        """프리뷰/최종 레이어 커브에 값 벌크 기록.

        키 개수가 이미 맞으면 값만 덮어쓰고(가장 빠름), 아니면 전부 다시 만든다.
        """
        times = om.MTimeArray()
        for f in self.frames:
            times.append(om.MTime(f, om.MTime.uiUnit()))
        n = len(self.frames)

        items = list(writes.items())
        for ni, (node, values) in enumerate(items):
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
            if progress:
                progress(ni + 1, len(items), "{0}  ({1}/{2})".format(
                    node.split("|")[-1], ni + 1, len(items)))

    def bake_keys(self, writes, progress=None):
        """base 커브에 직접 키를 굽는다(undo 가능한 cmds 경로).

        노드 x 프레임 만큼 `setKeyframe` 이 돌아 이 툴에서 **가장 오래 걸리는 기록
        경로**다. 그래서 진행률도 프레임 단위로 보고한다.
        """
        start, end = self.frames[0], self.frames[-1]
        items = list(writes.items())
        n_frames = len(self.frames)
        # cut 패스(노드당 1) + set 패스(노드당 프레임 수)
        total = max(1, len(items) * (n_frames + 1))
        done = 0

        for node, values in items:
            for at in ROT_ATTRS:
                try:
                    cmds.cutKey(node, at=at, time=(start, end), clear=True)
                except Exception:
                    pass
            done += 1
            if progress:
                progress(done, total, "clearing keys")

        for ni, (node, values) in enumerate(items):
            short = node.split("|")[-1]
            label = "{0}  ({1}/{2})".format(short, ni + 1, len(items))
            for k, f in enumerate(self.frames):
                v = values[k]
                for ai, at in enumerate(ROT_ATTRS):
                    cmds.setKeyframe(node, at=at, t=f, v=v[ai])
                done += 1
                if progress:
                    progress(done, total, label)


def _rad(deg):
    return deg * 0.017453292519943295
