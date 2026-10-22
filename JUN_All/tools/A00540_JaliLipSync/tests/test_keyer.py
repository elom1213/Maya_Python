# -*- coding: utf-8 -*-
# A00540_JaliLipSync - 코어 시험 (T-K, mayapy 2024, 합성 리그)
#   mayapy test_keyer.py
import os
import sys

import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00540_JaliLipSync.app.core import mapping as mapping_mod, keyer, scene, lipsync_data, sequence   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def attrs_of(mapping, role):
    return [t["attr"].split(".", 1)[1] for t in mapping["targets"] if t["role"] == role]


def make_node(name, attrs, parent_ns=""):
    node = cmds.createNode("transform", n=parent_ns + name)
    for a in attrs:
        cmds.addAttr(node, ln=a, at="double", min=0.0, max=1.0, k=True)
    return node


def key_count(attr):
    return cmds.keyframe(attr, q=True, keyframeCount=True) or 0


def value_at(attr, frame):
    return cmds.keyframe(attr, q=True, eval=True, t=(frame, frame))[0]


new = mapping_mod.load_mapping("jali_slider_dummy_in")
cmds.file(new=True, force=True)
cmds.currentUnit(time="film")

# 합성 데이터: 50줄(0.5초) — Jaw 0.9, Lip 0.3, Aa 0.7, W 0.2, 나머지 0
idx = {c: i for i, c in enumerate(lipsync_data.MODEL_COLUMNS)}
row = [0.0] * 22
row[idx["Jaw"]], row[idx["Lip"]], row[idx["Aa"]], row[idx["W"]] = 0.9, 0.3, 0.7, 0.2
data = lipsync_data.LipsyncData("synthetic.txt", [list(row) for _ in range(50)], list(lipsync_data.MODEL_COLUMNS), 100.0)

# Manual 용 노드 (아무 이름)
A = make_node("A", attrs_of(new, "phonemes"))
B = make_node("B", attrs_of(new, "coartic"))
C = make_node("C", attrs_of(new, "jali"))
# Auto 용: 네임스페이스 rigA 안에 json 이름 그대로
cmds.namespace(add="rigA")
for role, name in new["nodes"].items():
    make_node(name, attrs_of(new, role), "rigA:")

# K1 Auto 해석
targets, skipped = keyer.resolve_targets(new, "rigA:")
check("K1 auto 23 targets, all prefixed", len(targets) == 23 and all(t["attr"].startswith("rigA:") for t in targets) and skipped == [])
check("K1 find_rigs by marker", scene.find_rigs(scene.marker_of(new)) == ["rigA:"])
check("K1 find_rigs other marker -> none", scene.find_rigs("CNT_PHONEMES") == [])

# K2 Manual 해석
targets, skipped = keyer.resolve_targets(new, "ignored:", {"phonemes": "A", "coartic": None, "jali": "C"})
check("K2 manual 18 targets (coartic 5 skipped)", len(targets) == 18 and skipped == ["coartic"])
check("K2 manual nodes substituted", {t["attr"].split(".")[0] for t in targets} == {"A", "C"})

# K3 전부 None
try:
    keyer.apply(data, new, node_map={"phonemes": None, "coartic": None, "jali": None})
    check("K3 all None -> KeyingError", False)
except keyer.KeyingError as e:
    check("K3 all None -> KeyingError", "No target node" in str(e))

# K4 sample 배율
vals, n = keyer.sample(data, new, 24.0)
check("K4 new mapping default: AAA = 0.7 (scale 1), Jaw = 0.9", abs(max(vals["DUMMY_IN_PHONEMES.AAA"]) - 0.7) < 1e-9
      and abs(max(vals["DUMMY_IN_JALI.Jaw"]) - 0.9) < 1e-9 and n == 12)
vals, _ = keyer.sample(data, new, 24.0, viseme_scale=10, jali_scale=15)
check("K4 viseme_scale 10 / jali_scale 15", abs(max(vals["DUMMY_IN_PHONEMES.AAA"]) - 7.0) < 1e-9
      and abs(max(vals["DUMMY_IN_JALI.Jaw"]) - 13.5) < 1e-9)
check("K4 WA_PEDAL <- W column 0.2", abs(max(vals["DUMMY_IN_COARTIC.WA_PEDAL"]) - 2.0) < 1e-9)

# K5 apply Manual
res = keyer.apply(data, new, start=1, node_map={"phonemes": "A", "coartic": None, "jali": "C"})
check("K5 manual: A and C keyed, B not", key_count("A.AAA") == 13 and key_count("C.Jaw") == 13 and key_count("B.MMM") == 0)
check("K5 skipped == [coartic]", res["skipped"] == ["coartic"] and res["attrs"] == 18)
check("K5 key value AAA 0.7, Jaw 0.9", abs(value_at("A.AAA", 5) - 0.7) < 1e-6 and abs(value_at("C.Jaw", 5) - 0.9) < 1e-6)
check("K5 apply() reports one clip", res["clips"] == [("synthetic.txt", 1, 13)] and res["start"] == 1 and res["end"] == 13)
keyer.remove(new, node_map={"phonemes": "A", "coartic": "B", "jali": "C"})
res = keyer.apply(data, new, start=1, node_map={"phonemes": "A", "coartic": None, "jali": None})
check("K5 jali None too -> skipped [coartic, jali], C has no keys", res["skipped"] == ["coartic", "jali"] and key_count("C.Jaw") == 0)

# K6 remove / controls 가 node_map 을 따른다
check("K6 controls manual", keyer.controls(new, node_map={"phonemes": "A", "coartic": None, "jali": "C"}) == ["C", "A"])
check("K6 controls auto", keyer.controls(new, "rigA:") == ["rigA:DUMMY_IN_JALI", "rigA:DUMMY_IN_PHONEMES", "rigA:DUMMY_IN_COARTIC"])
n_removed = keyer.remove(new, node_map={"phonemes": "A", "coartic": None, "jali": None})
check("K6 remove manual phonemes only -> 16 attrs", n_removed == 16 and key_count("A.AAA") == 0)

# K7 scale_warnings
targets, _ = keyer.resolve_targets(new, node_map={"phonemes": "A", "coartic": "B", "jali": "C"})
warn = keyer.scale_warnings(targets, new, viseme_scale=10, jali_scale=1)
check("K7 scale 10 on max-1 attrs -> 21 warnings, none for jali", len(warn) == 21 and all(not a.startswith("C.") for a, _, _ in warn))
check("K7 scale 1 -> no warnings", keyer.scale_warnings(targets, new, viseme_scale=1, jali_scale=1) == [])

# K8 jali_fixed (리그 단위) + Auto 적용
res = keyer.apply(data, new, "rigA:", start=10, jali_fixed=(0.6, 0.6))
check("K8 auto apply: 23 attrs, skipped []", res["attrs"] == 23 and res["skipped"] == [])
jaw = cmds.keyframe("rigA:DUMMY_IN_JALI.Jaw", q=True, valueChange=True)
check("K8 fixed Jaw keyed at both ends = 0.6", jaw == [0.6, 0.6] and cmds.keyframe("rigA:DUMMY_IN_JALI.Jaw", q=True, tc=True) == [10.0, 22.0])
check("K8 phonemes keyed from data", key_count("rigA:DUMMY_IN_PHONEMES.AAA") == 13)

# K9 check_targets: 잠긴 어트리뷰트 거부 (Manual)
cmds.setAttr("A.Eh", lock=True)
try:
    keyer.apply(data, new, node_map={"phonemes": "A", "coartic": None, "jali": None})
    check("K9 locked attr -> KeyingError", False)
except keyer.KeyingError as e:
    check("K9 locked attr -> KeyingError names it", "A.Eh (locked)" in str(e))
cmds.setAttr("A.Eh", lock=False)

# ---------------------------------------------------------------- v01.02 여러 클립
# 클립 b: 30줄(0.3초) — Aa 0.2, Jaw 0.1
row_b = [0.0] * 22
row_b[idx["Aa"]], row_b[idx["Jaw"]] = 0.2, 0.1
data_b = lipsync_data.LipsyncData("b.txt", [list(row_b) for _ in range(30)], list(lipsync_data.MODEL_COLUMNS), 100.0)
clips = [sequence.Clip("synthetic.txt", data), sequence.Clip("b.txt", data_b)]
AAA, JAW = "rigA:DUMMY_IN_PHONEMES.AAA", "rigA:DUMMY_IN_JALI.Jaw"

# K10 hold 5: a = 1-13 (키 13개), hold 키 18, b = 19-26 (키 8개). 전체가 Undo 한 번
keyer.remove(new, "rigA:")
cmds.undoInfo(state=True, infinity=True)
segs = sequence.layout(clips, 1, 5, 24.0)
res = keyer.apply_sequence(segs, new, "rigA:", hold=5)
check("K10 clips placed with hold 5", res["clips"] == [("synthetic.txt", 1, 13), ("b.txt", 19, 26)]
      and res["start"] == 1 and res["end"] == 26 and res["attrs"] == 23)
check("K10 keys: 13 + hold 1 + 8 = 22 on AAA", key_count(AAA) == 22 and 18.0 in cmds.keyframe(AAA, q=True, tc=True))
check("K10 held value through the gap (frames 13, 16, 18 = 0.7), b starts at 19 = 0.2",
      abs(value_at(AAA, 13) - 0.7) < 1e-6 and abs(value_at(AAA, 16) - 0.7) < 1e-6
      and abs(value_at(AAA, 18) - 0.7) < 1e-6 and abs(value_at(AAA, 19) - 0.2) < 1e-6)
check("K10 Jaw from data per clip (0.9 then 0.1)", abs(value_at(JAW, 5) - 0.9) < 1e-6 and abs(value_at(JAW, 22) - 0.1) < 1e-6)
cmds.undo()
check("K10 one undo removes the whole sequence", key_count(AAA) == 0 and key_count(JAW) == 0)

# K11 hold 0: b 가 바로 이어진다 (14-21), hold 키 없음
segs = sequence.layout(clips, 1, 0, 24.0)
res = keyer.apply_sequence(segs, new, "rigA:", hold=0)
check("K11 hold 0 -> b at 14-21, 21 keys on AAA", res["clips"][1] == ("b.txt", 14, 21) and key_count(AAA) == 21
      and abs(value_at(AAA, 14) - 0.2) < 1e-6)

# K12 jali_fixed 로 여러 클립: Jaw 는 클립마다 처음 · 끝 + hold 키
segs = sequence.layout(clips, 1, 5, 24.0)
res = keyer.apply_sequence(segs, new, "rigA:", jali_fixed=(0.6, 0.6), hold=5)
check("K12 fixed Jaw: keys at 1, 13, 18, 19, 26 all 0.6", cmds.keyframe(JAW, q=True, tc=True) == [1.0, 13.0, 18.0, 19.0, 26.0]
      and cmds.keyframe(JAW, q=True, valueChange=True) == [0.6] * 5)
check("K12 re-apply cleared the hold-0 layout first (no key at 14 from K11 with b's value)", abs(value_at(AAA, 14) - 0.7) < 1e-6)

# K13 빈 목록 · 음수 hold
try:
    keyer.apply_sequence([], new, "rigA:")
    check("K13 empty -> KeyingError", False)
except keyer.KeyingError as e:
    check("K13 empty -> KeyingError", "No clip" in str(e))
try:
    keyer.apply_sequence(segs, new, "rigA:", hold=-1)
    check("K13 hold -1 -> KeyingError", False)
except keyer.KeyingError:
    check("K13 hold -1 -> KeyingError", True)

print("RESULT", "OK" if all(R) else "%d FAILED" % R.count(False))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
