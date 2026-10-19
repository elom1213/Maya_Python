# -*- coding: utf-8 -*-
# A00550_PoseMapper - JaLi 조절 코어 시험 (v01.05, mayapy 2024)  계획서 §11.6 J1 ~ J6
#   mayapy test_jali.py [테스트 씬 .mb]   (테스트 씬은 열기만, 저장하지 않는다)
import json
import os
import sys
import tempfile

import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools.A00550_PoseMapper.app.core import library, network   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def near(a, b, tol=1e-3):
    return abs(a - b) < tol


cmds.file(new=True, force=True)
src = cmds.createNode("transform", n="JALI_IN")
for a in ("Jaw", "Lip", "AHH", "UUU"):
    cmds.addAttr(src, ln=a, at="double", k=True)
cmds.setAttr(src + ".Jaw", 9)
cmds.setAttr(src + ".Lip", 9)
tgt = cmds.createNode("transform", n="ARKIT")
for a in ("jawOpen", "mouthFunnel"):
    cmds.addAttr(tgt, ln=a, at="double", k=True)

lib = library.PoseLibrary(name="j")
lib.set("AHH", "jawOpen", 0.67)
lib.set("UUU", "mouthFunnel", 0.26)
lib.set_axis("jawOpen", "jaw", 1.0)
net, rep = network.build(lib, src, tgt)
check("source with Jaw/Lip is used as JaLi node", network.net_jali(net)[0] == src and network.jali_ready(net))
cmds.setAttr(src + ".AHH", 10)
check("J1 Jaw 9 -> 0.67", near(cmds.getAttr(tgt + ".jawOpen"), 0.67))
cmds.setAttr(src + ".Jaw", 4.5)
check("J1 Jaw 4.5, s=1 -> 0.335", near(cmds.getAttr(tgt + ".jawOpen"), 0.335))
lib.set_strength("jawOpen", 0.5)
network.sync(net, lib, only_targets=["jawOpen"])
check("J1 s=0.5 -> 0.5025", near(cmds.getAttr(tgt + ".jawOpen"), 0.5025))
lib.set_strength("jawOpen", 0.0)
network.sync(net, lib, only_targets=["jawOpen"])
check("J1 s=0 -> 0.67", near(cmds.getAttr(tgt + ".jawOpen"), 0.67))
cmds.setAttr(src + ".Jaw", 15)
lib.set_strength("jawOpen", 1.0)
network.sync(net, lib, only_targets=["jawOpen"])
check("J1 Jaw 15 -> clamp 1.0 (0.67 x 15/9 = 1.117)", near(cmds.getAttr(tgt + ".jawOpen"), 1.0))

bw = network.chains(net)["jawOpen"]
jm, jb = network._axis_nodes(bw)
check("J2 axis nodes exist + clamp fed by jm", jm and jb and cmds.isConnected(jm + ".output", network._clamp_of(bw) + ".inputR"))
cmds.setAttr(src + ".Jaw", 9)
cmds.setAttr(src + ".Lip", 4.5)
lib.set_axis("jawOpen", "lip", 1.0)
network.sync(net, lib, only_targets=["jawOpen"])
check("J2 Jaw -> Lip: follows Lip 4.5 -> 0.335", near(cmds.getAttr(tgt + ".jawOpen"), 0.335) and network.chain_axis(net, bw)[0] == "lip")
lib.set_axis("jawOpen", None)
network.sync(net, lib, only_targets=["jawOpen"])
check("J2 axis none -> jm/jb deleted, bw -> clamp, 0.67", not cmds.objExists(jm) and not cmds.objExists(jb)
      and cmds.isConnected(bw + ".output", network._clamp_of(bw) + ".inputR") and near(cmds.getAttr(tgt + ".jawOpen"), 0.67))

lib.set_axis("jawOpen", "jaw", 1.0)
lib.jali_neutral = 6.0
network.sync(net, lib)
ratio = network._msg_src(net + ".pmRatioJaw")
cmds.setAttr(src + ".Jaw", 6)
check("J3 neutral 6 -> ratio input2 1/6, Jaw 6 -> 0.67", near(cmds.getAttr(ratio + ".input2"), 1 / 6.0) and near(cmds.getAttr(tgt + ".jawOpen"), 0.67))
other = cmds.createNode("transform", n="CNT_JaLi")
cmds.setAttr(other + ".tx", 3)
network.set_jali(net, other, "translateX", "translateY", 6.0)
check("J3 JaLi node -> CNT_JaLi.translateX: 3/6 -> 0.335", cmds.isConnected(other + ".translateX", ratio + ".input1")
      and near(cmds.getAttr(tgt + ".jawOpen"), 0.335))
network.set_jali(net, None, "translateX", "translateY", 6.0)
check("J3 no JaLi node -> factor 1 (0.67)", near(cmds.getAttr(tgt + ".jawOpen"), 0.67))
network.set_jali(net, src, "Jaw", "Lip", 6.0)

lib.set_strength("jawOpen", 0.25)
network.sync(net, lib, only_targets=["jawOpen"])
back = network.read_library(net)
check("J4 read_library axis / strength / neutral", back.axis("jawOpen") == "jaw" and near(back.strength("jawOpen"), 0.25)
      and near(back.jali_neutral, 6.0) and back.axis("mouthFunnel") is None)
path = os.path.join(tempfile.mkdtemp(), "j.json")
library.save(back, path)
again = library.load(path)
check("J4 save/load", again.target_axis == {"jawOpen": "jaw"} and near(again.strength("jawOpen"), 0.25) and near(again.jali_neutral, 6.0))
old = {"format": "jun.posemap/1", "name": "old", "ref_value": 10, "poses": {"AHH": {"jawOpen": 1.0}}}
oldp = os.path.join(tempfile.mkdtemp(), "old.json")
json.dump(old, open(oldp, "w"))
o = library.load(oldp)
check("J4 v01.04 json loads (no axis, neutral 9)", o.target_axis == {} and near(o.jali_neutral, 9.0))
lib2 = library.PoseLibrary()
for t in ("jawOpen", "mouthFunnel", "cheekPuff"):
    lib2.set("AHH", t, 0.5)
lib2.jali_defaults()
check("JALI Defaults: jawOpen jaw, others lip, strength 1", lib2.target_axis == {"jawOpen": "jaw", "mouthFunnel": "lip", "cheekPuff": "lip"}
      and lib2.strength("mouthFunnel") == 1.0)

n_before = len(cmds.ls(type=("blendWeighted", "blendTwoAttr", "multDoubleLinear", "clamp")))
network.remove(net)
check("J5 remove deletes jb / jm / ratio too", len(cmds.ls(type=("blendWeighted", "blendTwoAttr", "multDoubleLinear", "clamp"))) == 0 and n_before > 0)
cmds.undo()
check("J5 undo restores", cmds.objExists(net) and network.chain_axis(net, network.chains(net)["jawOpen"])[0] == "jaw")
cmds.addAttr(other, ln="UUU", at="double", k=True)             # 다른 노드망이 같은 타겟을 Replace 로 가져가게
lib3 = library.PoseLibrary(name="x")
lib3.set("UUU", "jawOpen", 0.5)
net3, _r = network.build(lib3, other, tgt, prefix="b_", on_existing="replace")
check("J5 detached() through the jm path", network.detached(net) == ["jawOpen"])

# J6 테스트 씬: 원래 노드망과 같은 값
if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    try:
        cmds.file(sys.argv[1], o=True, force=True, executeScriptNodes=False, ignoreVersion=True)
    except RuntimeError:
        pass
    import scene_fixture
    scene_fixture.reset_to_original_wiring()
    from tools.A00550_PoseMapper.app.core import capture, attrs
    BS = "CHN_n_Face_xx_bs"
    PH = ["AHH", "AAA", "Eh", "IEE", "OHH", "UUU", "WWW", "RRR", "SSS", "SSH", "FFF", "TTH", "MBP", "Schwa", "LNTD", "GK"]
    cmds.setAttr("JALI1:CNT_JaLi.tx", 9)
    cmds.setAttr("JALI1:CNT_JaLi.ty", 9)
    cap, _info = capture.capture("JALI1:CNT_PHONEMES", PH, BS, attrs.target_attrs(BS), 10.0)
    cap.jaw_attr, cap.lip_attr = "translateX", "translateY"
    cap.jali_defaults()
    ref = {}
    for tx, ty in ((2, 9), (9, 4), (12, 6)):
        cmds.setAttr("JALI1:CNT_JaLi.tx", tx)
        cmds.setAttr("JALI1:CNT_JaLi.ty", ty)
        cmds.setAttr("JALI1:CNT_PHONEMES.AHH", 10)
        a = cmds.getAttr(BS + ".jawOpen")
        cmds.setAttr("JALI1:CNT_PHONEMES.AHH", 0)
        cmds.setAttr("JALI1:CNT_PHONEMES.UUU", 10)
        b = cmds.getAttr(BS + ".mouthFunnel")
        cmds.setAttr("JALI1:CNT_PHONEMES.UUU", 0)
        ref[(tx, ty)] = (a, b)
    net6, rep6 = network.build(cap, "JALI1:CNT_PHONEMES", BS, prefix="j6_", on_existing="replace", jali_node="JALI1:CNT_JaLi")
    for (tx, ty), (a, b) in sorted(ref.items()):
        cmds.setAttr("JALI1:CNT_JaLi.tx", tx)
        cmds.setAttr("JALI1:CNT_JaLi.ty", ty)
        cmds.setAttr("JALI1:CNT_PHONEMES.AHH", 10)
        a2 = cmds.getAttr(BS + ".jawOpen")
        cmds.setAttr("JALI1:CNT_PHONEMES.AHH", 0)
        cmds.setAttr("JALI1:CNT_PHONEMES.UUU", 10)
        b2 = cmds.getAttr(BS + ".mouthFunnel")
        cmds.setAttr("JALI1:CNT_PHONEMES.UUU", 0)
        check("J6 JaLi ({0},{1}): jawOpen {2:.3f}={3:.3f}, mouthFunnel {4:.3f}={5:.3f} (original network)".format(
            tx, ty, a2, a, b2, b), near(a, a2, 2e-3) and near(b, b2, 2e-3))
    check("J6 no jali_missing", rep6["jali_missing"] == [])

print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
