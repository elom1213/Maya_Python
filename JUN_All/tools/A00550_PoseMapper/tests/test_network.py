# -*- coding: utf-8 -*-
# A00550_PoseMapper - attrs / library / network 코어 시험 (mayapy 2024, 합성 씬)
import json
import os
import sys
import tempfile

import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00550_PoseMapper.app.core import attrs, library, network   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def near(a, b):
    return abs(a - b) < 1e-4


def scene(ns=""):
    if ns:
        cmds.namespace(add=ns.rstrip(":"))
    src = cmds.createNode("transform", n=ns + "JALI_IN")
    for a in ("AAA", "Eh", "MBP", "OHH"):
        cmds.addAttr(src, ln=a, at="double", min=0, max=12, k=True)
    base = cmds.polyCube(n=ns + "face")[0]
    tg = [cmds.polyCube(n=ns + n)[0] for n in ("jawOpen", "mouthClose", "mouthPucker")]
    bs = cmds.blendShape(tg + [base], n=ns + "BS_arkit")[0]
    return src, bs


cmds.file(new=True, force=True)
src, bs = scene()
check("attrs: source attrs", attrs.numeric_user_attrs(src) == ["AAA", "Eh", "MBP", "OHH"])
check("attrs: bs targets", attrs.target_attrs(bs) == ["jawOpen", "mouthClose", "mouthPucker"])

lib = library.PoseLibrary(name="t", ref_value=10.0)
lib.set("AAA", "jawOpen", 0.67)
lib.set("MBP", "jawOpen", 0.43)
lib.set("MBP", "mouthClose", 0.62)
lib.set("Eh", "jawOpen", 0.0)                         # 0 은 저장 안 됨
check("library sparse", lib.poses == {"AAA": {"jawOpen": 0.67}, "MBP": {"jawOpen": 0.43, "mouthClose": 0.62}})

net, rep = network.build(lib, src, bs)
check("P2 built 2 chains", sorted(rep["built"]) == ["jawOpen", "mouthClose"] and len(network.chains(net)) == 2)
cmds.setAttr(src + ".AAA", 10)
check("P2 AAA=10 -> jawOpen 0.67", near(cmds.getAttr(bs + ".jawOpen"), 0.67))
cmds.setAttr(src + ".MBP", 10)
check("P2 sum + clamp (0.67+0.43 -> 1.0)", near(cmds.getAttr(bs + ".jawOpen"), 1.0))
cmds.setAttr(src + ".AAA", 0)
check("P2 MBP=10 -> mouthClose 0.62", near(cmds.getAttr(bs + ".mouthClose"), 0.62))
bw = network.chains(net)["jawOpen"]
check("weights always have elements", (cmds.getAttr(bw + ".input", mi=True) or []) == (cmds.getAttr(bw + ".weight", mi=True) or []))

# P3 슬라이더 = 한 타겟만 sync, 노드 재생성 없음
nodes_before = set(cmds.ls(type="blendWeighted"))
lib.set("MBP", "mouthClose", 0.8)
network.sync(net, lib, only_targets=["mouthClose"])
check("P3 live update, same nodes", near(cmds.getAttr(bs + ".mouthClose"), 0.8) and set(cmds.ls(type="blendWeighted")) == nodes_before)
lib.set("OHH", "mouthPucker", 0.5)
r3 = network.sync(net, lib, only_targets=["mouthPucker"])
cmds.setAttr(src + ".MBP", 0); cmds.setAttr(src + ".OHH", 10)
check("P3 new target chain on demand", r3["built"] == ["mouthPucker"] and near(cmds.getAttr(bs + ".mouthPucker"), 0.5))

# ref 를 임의 실수로
lib.ref_value = 2.5
network.sync(net, lib)
cmds.setAttr(src + ".OHH", 2.5)
check("ref 2.5: OHH=2.5 -> mouthPucker 0.5", near(cmds.getAttr(bs + ".mouthPucker"), 0.5) and near(cmds.getAttr(net + ".pmRef"), 2.5))
cmds.setAttr(src + ".OHH", 0)
_rl = network.read_library(net).poses   # weight 는 float32 - 되읽은 값은 소수 4자리까지만 같다
check("read_library roundtrip", {p: {t: round(v, 4) for t, v in tv.items()} for p, tv in _rl.items()} ==
      {p: {t: round(v, 4) for t, v in tv.items()} for p, tv in lib.poses.items()})

# 라이브러리에서 타겟을 빼면 체인 정리
lib.set("OHH", "mouthPucker", 0)
r4 = network.sync(net, lib)
check("removed target chain", "mouthPucker" in r4["removed"] and "mouthPucker" not in network.chains(net))

# 저장 / 불러오기
path = os.path.join(tempfile.mkdtemp(), "t.json")
library.save(lib, path)
lib2 = library.load(path)
check("save/load", lib2.poses == lib.poses and near(lib2.ref_value, 2.5))

# P7 remove + undo
n_before = len(cmds.ls(type="blendWeighted"))
network.remove(net)
check("P7 remove deletes tool nodes", not cmds.objExists(net) and len(cmds.ls(type="blendWeighted")) == n_before - 2)
cmds.undo()
check("P7 undo restores", cmds.objExists(net) and len(network.chains(net)) == 2)

# P4 다른 노드 쌍에 연결 (네임스페이스, 타겟 하나 없음)
src2, bs2 = scene("avatar:")
cmds.aliasAttr("avatar:BS_arkit.mouthClose", rm=True)     # 이 아바타에는 mouthClose 가 없다고 치자
lib2.ref_value = 10.0
net2, rep2 = network.build(lib2, src2, bs2, prefix="avatar_")
cmds.setAttr(src2 + ".MBP", 10)
check("P4 other pair: jawOpen 0.43, missing mouthClose reported",
      near(cmds.getAttr(bs2 + ".jawOpen"), 0.43) and rep2["missing_targets"] == ["mouthClose"] and net2.startswith("avatar_"))

# P5 이미 연결된 타겟: skip / replace / add
cmds.file(new=True, force=True)
src, bs = scene()
drv = cmds.createNode("transform", n="OLD")
cmds.addAttr(drv, ln="v", at="double", dv=0.2, k=True) if False else cmds.addAttr(drv, ln="val", at="double", dv=0.2, k=True)
cmds.connectAttr(drv + ".val", bs + ".jawOpen")
lib = library.PoseLibrary(name="t")
lib.set("AAA", "jawOpen", 0.5)
lib.set("AAA", "mouthPucker", 0.3)
net, rep = network.build(lib, src, bs)                       # skip (기본)
check("P5 skip keeps old driver", rep["skipped_existing"] == [("jawOpen", "OLD.val")] and attrs.incoming(bs + ".jawOpen") == "OLD.val")
r = network.sync(net, lib, on_existing="add")
cmds.setAttr(src + ".AAA", 10)
check("P5 add: old 0.2 + 0.5 = 0.7", r["added"] == [("jawOpen", "OLD.val")] and near(cmds.getAttr(bs + ".jawOpen"), 0.7))
network.remove(net)
cmds.connectAttr(drv + ".val", bs + ".jawOpen", force=True)
net, rep = network.build(lib, src, bs, on_existing="replace")
check("P5 replace: 0.5, old disconnected", near(cmds.getAttr(bs + ".jawOpen"), 0.5) and rep["replaced"] == [("jawOpen", "OLD.val")])

print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
