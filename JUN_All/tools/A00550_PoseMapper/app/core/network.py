# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - 포즈 라이브러리 -> 씬 노드망 (maya.cmds, UI 비의존, 계획서 §3.6)
#
# 타겟 t 하나마다:
#   <prefix>pm_bw_<t> (blendWeighted)  input[i] <- <source>.<음소>,  weight[i] = 포즈[음소][t] / ref
#   <prefix>pm_cl_<t> (clamp 0~1, 옵션) -> <target>.<t>
# 묶음: <prefix>pm_NET (network 노드) - message 로 source · target 노드와 각 bw 를 잡는다(이름이 바뀌어도 따라간다).
#   pmLibrary(string) · pmRef(double) · pmClamp(bool)
# weight 는 항상 input 과 같이 만든다 (blendWeighted 의 "weight 원소 없음 = 1.0 이지만 안 보임" 문제를 만들지 않는다).
# 이미 다른 것이 연결된 타겟: "skip"(기본) / "replace"(끊고 연결) / "add"(기존 소스를 bw 의 입력으로 넣어 합산).

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import attrs as attrs_mod
from . import blend_weights as bwm
from .library import PoseLibrary, EPS


ON_EXISTING = ("skip", "replace", "add")
A_LIB, A_REF, A_CLAMP = "pmLibrary", "pmRef", "pmClamp"
A_SRC, A_TGT, A_CHAINS = "pmSource", "pmTargetNode", "pmChains"
A_T, A_EXT = "pmTarget", "pmExternal"


# ================================================================== 조회

def find_networks(source=None, target=None):
    """이 툴이 만든 network 노드. source / target 을 주면 그 노드 쌍만."""
    nets = [n for n in cmds.ls(type="network") or [] if cmds.attributeQuery(A_LIB, node=n, exists=True)]
    if source:
        nets = [n for n in nets if _same(net_source(n), source)]
    if target:
        nets = [n for n in nets if _same(net_target(n), target)]
    return nets


def _same(a, b):
    return bool(a) and bool(b) and cmds.ls(a, uuid=True) == cmds.ls(b, uuid=True)


def _msg_src(plug_name):
    src = cmds.listConnections(plug_name, source=True, destination=False) or []
    return src[0] if src else None


def net_source(net):
    return _msg_src(net + "." + A_SRC)


def net_target(net):
    return _msg_src(net + "." + A_TGT)


def net_info(net):
    return {"library": cmds.getAttr(net + "." + A_LIB) or "", "ref": cmds.getAttr(net + "." + A_REF),
            "clamp": bool(cmds.getAttr(net + "." + A_CLAMP)), "source": net_source(net), "target": net_target(net)}


def chains(net):
    """{target_attr: bw}"""
    out = {}
    for bw in cmds.listConnections(net + "." + A_CHAINS, source=True, destination=False) or []:
        if cmds.attributeQuery(A_T, node=bw, exists=True):
            out[cmds.getAttr(bw + "." + A_T)] = bw
    return out


def _clamp_of(bw):
    cl = cmds.listConnections(bw + ".output", source=False, destination=True, type="clamp") or []
    return cl[0] if cl else None


def _phoneme_inputs(bw, source):
    """{phoneme: idx} - source 노드에서 온 input 만 (Add 모드의 외부 입력은 빼고)."""
    out = {}
    for i in cmds.getAttr(bw + ".input", multiIndices=True) or []:
        src = bwm.input_source(bw, i)
        if src and _same(src.split(".", 1)[0], source):
            out[src.split(".", 1)[1]] = i
    return out


def read_library(net, name=None):
    """노드망의 weight x ref 로 라이브러리를 다시 만든다."""
    info = net_info(net)
    lib = PoseLibrary(name=name or info["library"] or "from_scene", ref_value=info["ref"], clamp=info["clamp"])
    for t, bw in chains(net).items():
        for p, i in _phoneme_inputs(bw, info["source"]).items():
            lib.set(p, t, cmds.getAttr("{0}.weight[{1}]".format(bw, i)) * info["ref"])
    return lib


# ================================================================== 만들기

def _add_string(node, name, value):
    if not cmds.attributeQuery(name, node=node, exists=True):
        cmds.addAttr(node, ln=name, dt="string")
    cmds.setAttr(node + "." + name, value or "", type="string")


def create_network(source, target, lib, prefix=""):
    net = cmds.createNode("network", n=prefix + "pm_NET")
    _add_string(net, A_LIB, lib.name)
    cmds.addAttr(net, ln=A_REF, at="double", dv=lib.ref_value)
    cmds.addAttr(net, ln=A_CLAMP, at="bool", dv=lib.clamp)
    cmds.addAttr(net, ln=A_SRC, at="message")
    cmds.addAttr(net, ln=A_TGT, at="message")
    cmds.addAttr(net, ln=A_CHAINS, at="message", multi=True, indexMatters=False)
    cmds.connectAttr(source + ".message", net + "." + A_SRC)
    cmds.connectAttr(target + ".message", net + "." + A_TGT)
    return net


def _make_chain(net, t, on_existing, report):
    """타겟 t 의 체인을 만든다. 막히면 None (report 에 이유)."""
    target = net_target(net)
    dst = attrs_mod.plug(target, t)
    existing = attrs_mod.incoming(dst)
    if existing and on_existing == "skip":
        report["skipped_existing"].append((t, existing))
        return None
    prefix = net[:-len("pm_NET")] if net.endswith("pm_NET") else ""
    bw = cmds.createNode("blendWeighted", n=prefix + "pm_bw_" + t)
    _add_string(bw, A_T, t)
    cmds.connectAttr(bw + ".message", net + "." + A_CHAINS, nextAvailable=True)
    out = bw + ".output"
    if cmds.getAttr(net + "." + A_CLAMP):
        cl = cmds.createNode("clamp", n=prefix + "pm_cl_" + t)
        cmds.setAttr(cl + ".maxR", 1.0)
        cmds.connectAttr(out, cl + ".inputR")
        out = cl + ".outputR"
    if existing:
        cmds.disconnectAttr(existing, dst)
        if on_existing == "add":
            idx = bwm.next_index(bw)
            cmds.connectAttr(existing, "{0}.input[{1}]".format(bw, idx))
            cmds.setAttr("{0}.weight[{1}]".format(bw, idx), 1.0)
            _add_string(bw, A_EXT, existing)
        report["replaced" if on_existing == "replace" else "added"].append((t, existing))
    cmds.connectAttr(out, dst, force=True)
    return bw


def _sync_inputs(bw, source, weights):
    """bw 의 음소 입력을 weights({phoneme: weight}) 와 같게: 바꾸고 · 더하고 · 지운다."""
    have = _phoneme_inputs(bw, source)
    for p, i in have.items():
        if p not in weights:
            bwm.remove(bw, [i])
    for p, w in weights.items():
        if p in have:
            cmds.setAttr("{0}.weight[{1}]".format(bw, have[p]), w)
        else:
            idx = bwm.next_index(bw)
            cmds.connectAttr(attrs_mod.plug(source, p), "{0}.input[{1}]".format(bw, idx))
            cmds.setAttr("{0}.weight[{1}]".format(bw, idx), w)


def _delete_chain(bw):
    cl = _clamp_of(bw)
    cmds.delete([n for n in (cl, bw) if n])


def _new_report():
    return {"built": [], "updated": [], "removed": [], "skipped_existing": [], "replaced": [], "added": [],
            "missing_targets": [], "missing_sources": []}


def sync(net, lib, on_existing="skip", only_targets=None):
    """노드망을 라이브러리와 같게 만든다 (ref · clamp 포함). only_targets 를 주면 그 타겟만 (슬라이더 갱신용)."""
    if on_existing not in ON_EXISTING:
        raise ValueError("on_existing must be one of {0}".format(ON_EXISTING))
    report = _new_report()
    source, target = net_source(net), net_target(net)
    if not source or not target:
        raise RuntimeError("Network {0} lost its source or target node".format(net))
    with undo_chunk():
        if only_targets is None:
            cmds.setAttr(net + "." + A_REF, lib.ref_value)
            cmds.setAttr(net + "." + A_CLAMP, lib.clamp)
            _add_string(net, A_LIB, lib.name)
        src_attrs = set(attrs_mod.numeric_user_attrs(source))
        tgt_attrs = set(attrs_mod.target_attrs(target))
        have = chains(net)
        wanted = lib.targets_used() if only_targets is None else list(only_targets)

        for t in wanted:
            weights = {p: w for p, w in lib.weights_for_target(t).items() if p in src_attrs}
            for p in lib.weights_for_target(t):
                if p not in src_attrs and p not in report["missing_sources"]:
                    report["missing_sources"].append(p)
            if t not in tgt_attrs:
                if weights:
                    report["missing_targets"].append(t)
                continue
            bw = have.get(t)
            if not weights:
                if bw and not cmds.attributeQuery(A_EXT, node=bw, exists=True):
                    _delete_chain(bw)
                    report["removed"].append(t)
                elif bw:
                    _sync_inputs(bw, source, {})
                continue
            if bw is None:
                bw = _make_chain(net, t, on_existing, report)
                if bw is None:
                    continue
                report["built"].append(t)
            else:
                report["updated"].append(t)
            _sync_inputs(bw, source, weights)

        if only_targets is None:                     # 라이브러리에서 빠진 타겟의 체인 정리
            for t, bw in have.items():
                if t not in wanted and not cmds.attributeQuery(A_EXT, node=bw, exists=True):
                    _delete_chain(bw)
                    report["removed"].append(t)
    return report


def build(lib, source, target, prefix="", on_existing="skip"):
    """새 노드망. 같은 source/target 쌍에 이미 있으면 그것을 sync 한다. Returns (net, report)."""
    if not cmds.objExists(source):
        raise ValueError("Source node not found: {0}".format(source))
    if not cmds.objExists(target):
        raise ValueError("Target node not found: {0}".format(target))
    with undo_chunk():
        nets = find_networks(source, target)
        net = nets[0] if nets else create_network(source, target, lib, prefix)
        report = sync(net, lib, on_existing)
        if not chains(net) and not nets:
            cmds.delete(net)                          # 하나도 못 만들었으면 빈 network 를 남기지 않는다
            net = None
    return net, report


def remove(net):
    """이 툴이 만든 노드만 지운다. Replace 로 끊은 원래 연결은 되살리지 않는다(Undo 로는 돌아온다)."""
    with undo_chunk():
        nodes = []
        for bw in chains(net).values():
            cl = _clamp_of(bw)
            nodes += [n for n in (cl, bw) if n]
        cmds.delete(nodes + [net])
    return len(nodes)
