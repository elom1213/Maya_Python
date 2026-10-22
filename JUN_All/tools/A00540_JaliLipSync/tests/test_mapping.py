# -*- coding: utf-8 -*-
# A00540_JaliLipSync - 매핑 json v2 시험 (T-M, Maya 비의존 - mayapy 로 돌려도 된다)
#   mayapy test_mapping.py
import copy
import os
import sys

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00540_JaliLipSync.app.core import mapping as mapping_mod   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def raises(fn, text):
    try:
        fn()
    except ValueError as e:
        return text in str(e)
    return False


angela = mapping_mod.load_mapping("angela_jali_visemenet")
new = mapping_mod.load_mapping("jali_slider_dummy_in")

# 1. angela json
check("M1 angela nodes", angela["nodes"] == {"phonemes": "CNT_PHONEMES", "coartic": "CNT_COARTIC", "jali": "CNT_JaLi"})
check("M1 angela viseme_scale 10", angela["viseme_scale"] == 10.0)
check("M1 angela jali", angela["jali"] == {"scale": 10.0, "range": [0.0, 15.0], "fixed_default": [9.0, 9.0]})
check("M1 angela 23 targets", len(angela["targets"]) == 23)
check("M1 angela roles set", all(t["role"] in mapping_mod.ROLES for t in angela["targets"]))
check("M1 angela jali targets", [t["attr"] for t in angela["targets"] if t["role"] == "jali"] ==
      ["CNT_JaLi.translateX", "CNT_JaLi.translateY"])
check("M1 angela coartic targets 5", sum(1 for t in angela["targets"] if t["role"] == "coartic") == 5)

# 2. 새 json
check("M2 new nodes", new["nodes"] == {"phonemes": "DUMMY_IN_PHONEMES", "coartic": "DUMMY_IN_COARTIC", "jali": "DUMMY_IN_JALI"})
check("M2 new viseme_scale 1", new["viseme_scale"] == 1.0)
check("M2 new jali", new["jali"] == {"scale": 1.0, "range": [0.0, 1.0], "fixed_default": [0.6, 0.6]})
check("M2 new 23 targets", len(new["targets"]) == 23)
rename = {"translateX": "Jaw", "translateY": "Lip"}


def key(t):
    attr = t["attr"].split(".", 1)[1]
    return (t["role"], rename.get(attr, attr))


a_map = {key(t): (t["from"], t.get("combine", "max")) for t in angela["targets"]}
n_map = {key(t): (t["from"], t.get("combine", "max")) for t in new["targets"]}
check("M2 same column mapping as angela (role, attr, from, combine)", a_map == n_map)

# 3. 오류
base = copy.deepcopy(new)
no_nodes = copy.deepcopy(base); del no_nodes["nodes"]
check("M3 no nodes -> ValueError", raises(lambda: mapping_mod.validate(no_nodes, "x"), "nodes"))
bad_node = copy.deepcopy(base); bad_node["targets"][2]["attr"] = "OTHER_NODE.AAA"
check("M3 target node not in nodes -> ValueError names attr",
      raises(lambda: mapping_mod.validate(bad_node, "x"), "OTHER_NODE.AAA"))
dot = copy.deepcopy(base); dot["nodes"]["phonemes"] = "a.b"
check("M3 nodes value with '.' -> ValueError", raises(lambda: mapping_mod.validate(dot, "x"), "without '.'"))
bad_role = copy.deepcopy(base); bad_role["nodes"]["tongue"] = "T"
check("M3 unknown role -> ValueError", raises(lambda: mapping_mod.validate(bad_role, "x"), "unknown role"))
bad_range = copy.deepcopy(base); bad_range["jali"]["range"] = [1, 0]
check("M3 jali.range min >= max -> ValueError", raises(lambda: mapping_mod.validate(bad_range, "x"), "jali.range"))

# 4. 하위 호환: viseme_scale / jali 없이 targets[].scale 만
old = copy.deepcopy(angela)
for k in ("viseme_scale", "jali"):
    del old[k]
for t in old["targets"]:
    t.pop("role", None)
old = mapping_mod.validate(old, "old")
check("M4 viseme_scale from targets[].scale", old["viseme_scale"] == 10.0)
check("M4 jali.scale from jali target scale", old["jali"]["scale"] == 10.0)
check("M4 jali defaults", old["jali"]["range"] == [0.0, 15.0] and old["jali"]["fixed_default"] == [9.0, 9.0])
check("M4 role from node", [t["role"] for t in old["targets"][:3]] == ["jali", "jali", "phonemes"])

print("RESULT", "OK" if all(R) else "%d FAILED" % R.count(False))
sys.exit(0 if all(R) else 1)
