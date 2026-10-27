# -*- coding: utf-8 -*-
# A00275_skinTool_V01 - Weights > Smooth 회귀 시험 (mayapy)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_weight_smooth_regression.py          비교
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_weight_smooth_regression.py --save   기준 다시 쓰기
#
# v01.37 에서 Smooth 의 공용 함수를 skin_weights_common.py 로 옮기면서(Move 탭과 공유) 만들었다.
# 옮기기 **전의** 코드로 고정 씬 결과를 data/smooth_baseline.json 에 저장해 두고, 지금 코드가 같은지 본다.
import json
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00275_skinTool_V01.app.core import weight_smooth_manager as sm   # noqa: E402

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "smooth_baseline.json")


def build_scene():
    """10x10 평면 + 조인트 3 개, 버텍스마다 정해진 (결정적) 웨이트."""
    cmds.file(new=True, force=True)
    cmds.polyPlane(name="pl", w=10, h=10, sx=10, sy=10)
    joints = []
    for i, x in enumerate((-4.0, 0.0, 4.0)):
        cmds.select(clear=True)
        joints.append(cmds.joint(name="j{0}".format(i), position=(x, 0, 0)))
    skin = cmds.skinCluster(joints, "pl", toSelectedBones=True)[0]
    count = cmds.polyEvaluate("pl", vertex=True)
    for v in range(count):
        a = ((v * 37) % 11) / 10.0
        b = ((v * 17) % 7) / 6.0 * (1.0 - a)
        cmds.skinPercent(skin, "pl.vtx[{0}]".format(v), transformValue=[
            (joints[0], a), (joints[1], b), (joints[2], max(0.0, 1.0 - a - b))])
    return skin, count


CASES = [
    ("default", dict()),
    ("iter8_blend05", dict(iterations=8, blend=0.5)),
    ("rigid", dict(iterations=3, rigid=0.7)),
    ("keep_one", dict(iterations=4, keep_value_one=True)),
    ("lock_keep", dict(iterations=4, joint_locks=sm.LOCKS_KEEP, _lock="j1")),
    ("lock_add", dict(iterations=4, joint_locks=sm.LOCKS_ONLY_ADD, _lock="j1")),
    ("border_ignore", dict(iterations=4, border_edges=sm.BORDER_IGNORE, border_mask_steps=2)),
    ("border_only", dict(iterations=4, border_edges=sm.BORDER_ONLY, border_mask_steps=1)),
    ("partial", dict(iterations=5, _ids=list(range(20, 70)))),
]


def run_case(kwargs):
    skin, count = build_scene()
    kwargs = dict(kwargs)
    lock = kwargs.pop("_lock", None)
    ids = kwargs.pop("_ids", None)
    if lock:
        cmds.setAttr(lock + ".liw", 1)
    targets = [{"mesh": cmds.ls("pl", long=True)[0], "ids": ids, "softs": None}]
    sm.smooth(targets=targets, **kwargs)
    return [[round(x, 9) for x in cmds.skinPercent(skin, "pl.vtx[{0}]".format(v), q=True, v=True)]
            for v in range(count)]


results = dict((name, run_case(kw)) for name, kw in CASES)

if "--save" in sys.argv:
    if not os.path.isdir(os.path.dirname(BASELINE)):
        os.makedirs(os.path.dirname(BASELINE))
    with open(BASELINE, "w") as handle:
        json.dump(results, handle)
    print("saved", BASELINE)
    ok = True
else:
    with open(BASELINE) as handle:
        baseline = json.load(handle)
    ok = True
    for name, _kw in CASES:
        worst = max(abs(a - b) for ra, rb in zip(results[name], baseline[name]) for a, b in zip(ra, rb))
        good = worst < 1e-8
        ok = ok and good
        print(("PASS " if good else "FAIL ") + "smooth regression : " + name + "  | max diff {0:.2e}".format(worst))
    print("\n{0}".format("all passed" if ok else "FAILED"))

maya.standalone.uninitialize()
os._exit(0 if ok else 1)
