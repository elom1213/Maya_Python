# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - 포즈 라이브러리 -> 씬 노드망 (maya.cmds, UI 비의존, 계획서 §3.6 · §11)
#
# 타겟 t 하나마다:
#   <prefix>pm_bw_<t> (blendWeighted)  input[i] <- <source>.<음소>,  weight[i] = 포즈[음소][t] / ref
#   [JaLi 축이 있으면, v01.05]
#   <prefix>pm_jb_<t> (blendTwoAttr)     input[0] = 1, input[1] <- pm_ratio_<Jaw|Lip>.output, attributesBlender = strength
#   <prefix>pm_jm_<t> (multDoubleLinear) bw.output x jb.output
#   <prefix>pm_cl_<t> (clamp 0~1, 옵션) -> <target>.<t>
# 노드망당 공용: <prefix>pm_ratio_Jaw / _Lip (multDoubleLinear) <JaLi 노드>.<축 attr> x (1 / neutral)
#   -> factor = 1 + strength * (축값 / neutral - 1)
# 묶음: <prefix>pm_NET (network 노드) - message 로 source · target · JaLi 노드와 각 bw · ratio 를 잡는다.
#   pmLibrary(string) · pmRef(double) · pmClamp(bool) · pmJawAttr / pmLipAttr(string) · pmNeutral(double)
# 체인의 clamp · jm · jb 는 bw 의 message 어트리뷰트(pmClampNode · pmAxisMul · pmAxisBlend)로 찾는다.
# weight 는 항상 input 과 같이 만든다 (blendWeighted 의 "weight 원소 없음 = 1.0 이지만 안 보임" 문제를 만들지 않는다).
# 이미 다른 것이 연결된 타겟: "skip"(기본) / "replace"(끊고 연결) / "add"(기존 소스를 bw 의 입력으로 넣어 합산).

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import attrs as attrs_mod
from . import blend_weights as bwm
from .library import PoseLibrary, EPS, AXES, DEFAULT_NEUTRAL


ON_EXISTING = ("skip", "replace", "add")
A_LIB, A_REF, A_CLAMP = "pmLibrary", "pmRef", "pmClamp"
A_SRC, A_TGT, A_CHAINS = "pmSource", "pmTargetNode", "pmChains"
A_T, A_EXT = "pmTarget", "pmExternal"
# v01.05 JaLi
A_JALI, A_JAW_ATTR, A_LIP_ATTR, A_NEUTRAL = "pmJaliNode", "pmJawAttr", "pmLipAttr", "pmNeutral"
A_RATIO = {"jaw": "pmRatioJaw", "lip": "pmRatioLip"}
A_CL_NODE, A_JM, A_JB = "pmClampNode", "pmAxisMul", "pmAxisBlend"


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


def _has(node, attr):
    return bool(node) and cmds.attributeQuery(attr, node=node, exists=True)


def _msg_src(plug_name):
    node, attr = plug_name.split(".", 1)
    if not _has(node, attr):
        return None
    src = cmds.listConnections(plug_name, source=True, destination=False) or []
    return src[0] if src else None


def _link(node, attr, other):
    """other.message -> node.attr (message 어트리뷰트가 없으면 만든다)."""
    if not _has(node, attr):
        cmds.addAttr(node, ln=attr, at="message")
    cmds.connectAttr(other + ".message", "{0}.{1}".format(node, attr), force=True)


def net_source(net):
    return _msg_src(net + "." + A_SRC)


def net_target(net):
    return _msg_src(net + "." + A_TGT)


def net_jali(net):
    """(JaLi 노드, jaw_attr, lip_attr, neutral). v01.04 노드망은 (None, "Jaw", "Lip", 9.0)."""
    node = _msg_src(net + "." + A_JALI)
    jaw = cmds.getAttr(net + "." + A_JAW_ATTR) if _has(net, A_JAW_ATTR) else "Jaw"
    lip = cmds.getAttr(net + "." + A_LIP_ATTR) if _has(net, A_LIP_ATTR) else "Lip"
    neutral = cmds.getAttr(net + "." + A_NEUTRAL) if _has(net, A_NEUTRAL) else DEFAULT_NEUTRAL
    return node, jaw or "Jaw", lip or "Lip", neutral


def net_info(net):
    jali, jaw, lip, neutral = net_jali(net)
    return {"library": cmds.getAttr(net + "." + A_LIB) or "", "ref": cmds.getAttr(net + "." + A_REF),
            "clamp": bool(cmds.getAttr(net + "." + A_CLAMP)), "source": net_source(net), "target": net_target(net),
            "jali": jali, "jaw_attr": jaw, "lip_attr": lip, "neutral": neutral}


def chains(net):
    """{target_attr: bw}"""
    out = {}
    for bw in cmds.listConnections(net + "." + A_CHAINS, source=True, destination=False) or []:
        if cmds.attributeQuery(A_T, node=bw, exists=True):
            out[cmds.getAttr(bw + "." + A_T)] = bw
    return out


def _axis_nodes(bw):
    """(jm, jb) - 축이 없으면 (None, None)."""
    return _msg_src(bw + "." + A_JM), _msg_src(bw + "." + A_JB)


def _clamp_of(bw):
    cl = _msg_src(bw + "." + A_CL_NODE)
    if cl:
        return cl
    # v01.04 노드망: message 가 없다 - bw (또는 jm) 출력 쪽의 clamp
    jm, _jb = _axis_nodes(bw)
    for out in ((jm + ".output") if jm else None, bw + ".output"):
        if out:
            found = cmds.listConnections(out, source=False, destination=True, type="clamp") or []
            if found:
                return found[0]
    return None


def _pre_clamp_output(bw):
    """clamp(또는 clamp 가 없으면 타겟) 로 들어가는 plug - 축이 있으면 jm.output."""
    jm, _jb = _axis_nodes(bw)
    return jm + ".output" if jm else bw + ".output"


def chain_output(bw):
    """체인의 마지막 출력 plug (clamp 가 있으면 clamp.outputR)."""
    cl = _clamp_of(bw)
    return cl + ".outputR" if cl else _pre_clamp_output(bw)


def chain_axis(net, bw):
    """(axis, strength) - 축이 없으면 (None, 1.0)."""
    jm, jb = _axis_nodes(bw)
    if not jb:
        return None, 1.0
    src = _msg_src_plug(jb + ".input[1]")
    for axis in AXES:
        ratio = _msg_src(net + "." + A_RATIO[axis])
        if ratio and src and src.split(".", 1)[0] == ratio:
            return axis, cmds.getAttr(jb + ".attributesBlender")
    return None, 1.0


def _msg_src_plug(plug_name):
    src = cmds.listConnections(plug_name, source=True, destination=False, plugs=True) or []
    return src[0] if src else None


def _phoneme_inputs(bw, source):
    """{phoneme: idx} - source 노드에서 온 input 만 (Add 모드의 외부 입력은 빼고)."""
    out = {}
    for i in cmds.getAttr(bw + ".input", multiIndices=True) or []:
        src = bwm.input_source(bw, i)
        if src and _same(src.split(".", 1)[0], source):
            out[src.split(".", 1)[1]] = i
    return out


def detached(net):
    """타겟을 더 이상 구동하지 않는 체인의 타겟 이름 (v01.04).

    같은 타겟에 다른 노드망을 Replace 로 연결하면 이 노드망의 체인은 남아 있지만 출력이 타겟에 닿지 않는다
    -> 이 노드망의 슬라이더를 움직여도 얼굴이 안 바뀐다. 그걸 알려 주려고 쓴다.
    """
    target = net_target(net)
    out = []
    for t, bw in chains(net).items():
        dst = attrs_mod.plug(target, t)
        if not cmds.objExists(dst):
            continue
        src = attrs_mod.incoming(dst)
        if src is None or src.split(".", 1)[0] != chain_output(bw).split(".", 1)[0]:
            out.append(t)
    return out


def read_library(net, name=None):
    """노드망의 weight x ref 로 라이브러리를 다시 만든다 (JaLi 축 · 세기 · neutral 포함)."""
    info = net_info(net)
    lib = PoseLibrary(name=name or info["library"] or "from_scene", ref_value=info["ref"], clamp=info["clamp"],
                      jaw_attr=info["jaw_attr"], lip_attr=info["lip_attr"], jali_neutral=info["neutral"])
    for t, bw in chains(net).items():
        for p, i in _phoneme_inputs(bw, info["source"]).items():
            lib.set(p, t, cmds.getAttr("{0}.weight[{1}]".format(bw, i)) * info["ref"])
        axis, strength = chain_axis(net, bw)
        if axis:
            lib.set_axis(t, axis, strength)
    return lib


# ================================================================== 만들기

def _add_string(node, name, value):
    if not cmds.attributeQuery(name, node=node, exists=True):
        cmds.addAttr(node, ln=name, dt="string")
    cmds.setAttr(node + "." + name, value or "", type="string")


def _prefix(net):
    return net[:-len("pm_NET")] if net.endswith("pm_NET") else ""


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


# ------------------------------------------------------------------ JaLi

def jali_ready(net):
    """JaLi 노드와 두 축 어트리뷰트가 다 있으면 True."""
    node, jaw, lip, _n = net_jali(net)
    return bool(node) and cmds.objExists(node) and _has(node, jaw) and _has(node, lip)


def set_jali(net, jali_node, jaw_attr, lip_attr, neutral):
    """JaLi 입력을 정한다 (노드가 None 이면 연결을 풀고 축 효과 없음 = factor 1). ratio 노드는 필요할 때 만든다."""
    with undo_chunk():
        _add_string(net, A_JAW_ATTR, jaw_attr)
        _add_string(net, A_LIP_ATTR, lip_attr)
        if not _has(net, A_NEUTRAL):
            cmds.addAttr(net, ln=A_NEUTRAL, at="double", dv=DEFAULT_NEUTRAL)
        cmds.setAttr(net + "." + A_NEUTRAL, float(neutral))
        if jali_node and cmds.objExists(jali_node):
            _link(net, A_JALI, jali_node)
        elif _has(net, A_JALI):
            src = _msg_src_plug(net + "." + A_JALI)
            if src:
                cmds.disconnectAttr(src, net + "." + A_JALI)
        for axis in AXES:
            if _msg_src(net + "." + A_RATIO[axis]):
                _wire_ratio(net, axis)


def _ratio(net, axis):
    """축의 ratio 노드 (없으면 만든다)."""
    ratio = _msg_src(net + "." + A_RATIO[axis])
    if not ratio:
        ratio = cmds.createNode("multDoubleLinear", n=_prefix(net) + "pm_ratio_" + axis.capitalize())
        _link(net, A_RATIO[axis], ratio)
        _wire_ratio(net, axis)
    return ratio


def _wire_ratio(net, axis):
    """ratio.input1 <- JaLi.<attr>, input2 = 1/neutral. JaLi 가 없으면 input1 = neutral (factor 1)."""
    ratio = _msg_src(net + "." + A_RATIO[axis])
    node, jaw, lip, neutral = net_jali(net)
    neutral = neutral if abs(neutral) > EPS else DEFAULT_NEUTRAL
    attr = jaw if axis == "jaw" else lip
    src = _msg_src_plug(ratio + ".input1")
    if node and cmds.objExists(node) and _has(node, attr):
        plug = "{0}.{1}".format(node, attr)
        if src != plug:
            cmds.connectAttr(plug, ratio + ".input1", force=True)
    else:
        if src:
            cmds.disconnectAttr(src, ratio + ".input1")
        cmds.setAttr(ratio + ".input1", neutral)
    cmds.setAttr(ratio + ".input2", 1.0 / neutral)


def _apply_axis(net, bw, t, axis, strength, report):
    """체인 t 에 축 노드를 맞춘다: 없음 -> jb · jm 삭제 / 있음 -> 만들거나 축 · 세기만 바꾼다."""
    jm, jb = _axis_nodes(bw)
    if not axis:
        if jm:
            dests = cmds.listConnections(jm + ".output", source=False, destination=True, plugs=True) or []
            for d in dests:
                cmds.connectAttr(bw + ".output", d, force=True)
            cmds.delete([n for n in (jm, jb) if n])
        return
    if not jali_ready(net) and t not in report["jali_missing"]:
        report["jali_missing"].append(t)
    ratio = _ratio(net, axis)
    if not jm:
        prefix = _prefix(net)
        jb = cmds.createNode("blendTwoAttr", n=prefix + "pm_jb_" + t)
        cmds.setAttr(jb + ".input[0]", 1.0)
        cmds.connectAttr(ratio + ".output", jb + ".input[1]")
        jm = cmds.createNode("multDoubleLinear", n=prefix + "pm_jm_" + t)
        dests = cmds.listConnections(bw + ".output", source=False, destination=True, plugs=True) or []
        cmds.connectAttr(bw + ".output", jm + ".input1")
        cmds.connectAttr(jb + ".output", jm + ".input2")
        for d in dests:                               # bw 가 가던 곳(clamp 또는 타겟)을 jm 이 이어받는다
            cmds.connectAttr(jm + ".output", d, force=True)
        _link(bw, A_JM, jm)
        _link(bw, A_JB, jb)
    elif _msg_src_plug(jb + ".input[1]") != ratio + ".output":
        cmds.connectAttr(ratio + ".output", jb + ".input[1]", force=True)
    cmds.setAttr(jb + ".attributesBlender", max(0.0, min(1.0, float(strength))))


def _make_chain(net, t, on_existing, report):
    """타겟 t 의 체인을 만든다. 막히면 None (report 에 이유)."""
    target = net_target(net)
    dst = attrs_mod.plug(target, t)
    existing = attrs_mod.incoming(dst)
    if existing and on_existing == "skip":
        report["skipped_existing"].append((t, existing))
        return None
    prefix = _prefix(net)
    bw = cmds.createNode("blendWeighted", n=prefix + "pm_bw_" + t)
    _add_string(bw, A_T, t)
    cmds.connectAttr(bw + ".message", net + "." + A_CHAINS, nextAvailable=True)
    out = bw + ".output"
    if cmds.getAttr(net + "." + A_CLAMP):
        cl = cmds.createNode("clamp", n=prefix + "pm_cl_" + t)
        cmds.setAttr(cl + ".maxR", 1.0)
        cmds.connectAttr(out, cl + ".inputR")
        _link(bw, A_CL_NODE, cl)
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


def _chain_nodes(bw):
    jm, jb = _axis_nodes(bw)
    return [n for n in (_clamp_of(bw), jm, jb, bw) if n]


def _delete_chain(bw):
    cmds.delete(_chain_nodes(bw))


def _new_report():
    return {"built": [], "updated": [], "removed": [], "skipped_existing": [], "replaced": [], "added": [],
            "missing_targets": [], "missing_sources": [], "jali_missing": []}


def sync(net, lib, on_existing="skip", only_targets=None):
    """노드망을 라이브러리와 같게 만든다 (ref · clamp · JaLi 포함). only_targets 를 주면 그 타겟만 (슬라이더 갱신용)."""
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
            set_jali(net, net_jali(net)[0], lib.jaw_attr, lib.lip_attr, lib.jali_neutral)
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
            _apply_axis(net, bw, t, lib.axis(t), lib.strength(t), report)

        if only_targets is None:                     # 라이브러리에서 빠진 타겟의 체인 정리
            for t, bw in have.items():
                if t not in wanted and not cmds.attributeQuery(A_EXT, node=bw, exists=True):
                    _delete_chain(bw)
                    report["removed"].append(t)
    return report


def build(lib, source, target, prefix="", on_existing="skip", jali_node=None):
    """새 노드망. 같은 source/target 쌍에 이미 있으면 그것을 sync 한다. Returns (net, report).

    jali_node: JaLi 축 어트리뷰트(lib.jaw_attr / lip_attr)를 가진 노드. None 이면 기존 값을 두고,
    처음 만드는 노드망이면 source 에 그 어트리뷰트가 있을 때 source 를 쓴다.
    """
    if not cmds.objExists(source):
        raise ValueError("Source node not found: {0}".format(source))
    if not cmds.objExists(target):
        raise ValueError("Target node not found: {0}".format(target))
    with undo_chunk():
        nets = find_networks(source, target)
        net = nets[0] if nets else create_network(source, target, lib, prefix)
        node = jali_node or net_jali(net)[0]
        if not node and _has(source, lib.jaw_attr) and _has(source, lib.lip_attr):
            node = source
        set_jali(net, node, lib.jaw_attr, lib.lip_attr, lib.jali_neutral)
        report = sync(net, lib, on_existing)
        if not chains(net) and not nets:
            remove(net)                               # 하나도 못 만들었으면 빈 network 를 남기지 않는다
            net = None
    return net, report


def remove(net):
    """이 툴이 만든 노드만 지운다. Replace 로 끊은 원래 연결은 되살리지 않는다(Undo 로는 돌아온다)."""
    with undo_chunk():
        nodes = []
        for bw in chains(net).values():
            nodes += _chain_nodes(bw)
        for axis in AXES:
            ratio = _msg_src(net + "." + A_RATIO[axis])
            if ratio:
                nodes.append(ratio)
        cmds.delete(nodes + [net])
    return len(nodes)
