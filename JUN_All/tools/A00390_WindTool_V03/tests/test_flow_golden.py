# -*- coding: utf-8 -*-
# A00390_WindTool_V03 - Flow 순수 모델(flow_model) vs 블렌더 Waves Gen 기준 데이터(골든) 대조. Maya 불필요.
#   python test_flow_golden.py [golden.json]
# 골든: docs/plans/A00390_wavesgen_blender_probe.py 로 뽑은 json (기본 tests/data/wavesgen_golden.json)
import os
import sys
import json
import math

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, JUN_ALL)
from tools.A00390_WindTool_V03.app.core import flow_model as fm  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data", "wavesgen_golden.json")
G = json.load(open(path))
NB = G["bones"]
names = ["CF_%02d" % i for i in range(NB)]


def rot3(m):
    return [row[:3] for row in m[:3]]


def pos(m):
    return [m[0][3], m[1][3], m[2][3]]


root = G["rest"]["CF_Root"]["matrix"]
rest = []
prev_r, prev_p = rot3(root), pos(root)
for nm in names:
    m = G["rest"][nm]["matrix"]
    r, p = rot3(m), pos(m)
    rt = fm.transpose(prev_r)
    rest.append((fm.mat_mul(rt, r), fm.mat_vec(rt, [p[k] - prev_p[k] for k in range(3)])))
    prev_r, prev_p = r, p
tip = G["rest"]["CF_Tip"]["head"]
bone_len = math.dist(G["rest"]["CF_00"]["head"], G["rest"]["CF_00"]["tail"])
chain_len = bone_len * NB


def params_of(v):
    return {"lean": v["cf_wind"], "direction": math.degrees(v["cf_dir"]), "flutter": v["cf_flutter"],
            "cross": v["cf_cross"], "speed": v["cf_speed"], "wavelength": v["cf_length"],
            "stiffness": v["cf_stiff"], "random": v["cf_random"], "follow": v["cf_influence"]}


worst_all = 0.0
for case, data in G["cases"].items():
    p = params_of(data["values"])
    follow_on = p["follow"] > 0.0
    worst_pos, worst_ang = 0.0, 0.0
    for fi, frame in enumerate(G["frames"]):
        phi = frame * p["speed"]
        ours = fm.evaluate_chain(rot3(root), pos(root), rest, p, phi, tip, follow_on=follow_on)
        gold = data["frames"][fi]
        for i, nm in enumerate(names):
            gm = gold[nm]["matrix"]
            gr, gp = rot3(gm), pos(gm)
            orot, ohead = ours[i]
            worst_pos = max(worst_pos, math.dist(gp, ohead))
            # 축 각도 차 (Y 축)
            # 세 축 모두, 정규화해서(블렌더 행렬 보간이 축 길이를 1 에서 아주 조금 벗어나게 한다)
            for ax in range(3):
                gv = fm.norm([gr[0][ax], gr[1][ax], gr[2][ax]])
                ov = fm.norm([orot[0][ax], orot[1][ax], orot[2][ax]])
                worst_ang = max(worst_ang, math.degrees(math.acos(max(-1, min(1, fm.dot(gv, ov))))))
    rel = worst_pos / chain_len
    worst_all = max(worst_all, rel)
    check("golden {0}: head error < 0.1% of chain, axes < 0.2 deg".format(case), rel < 1e-3 and worst_ang < 0.2,
          "pos {0:.2e} ({1:.4%}) ang {2:.4f} deg".format(worst_pos, rel, worst_ang))

print("\nworst head error {0:.4%} of chain length".format(worst_all))
print("{0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
