# -*- coding: utf-8 -*-
# A00390_WindTool_V03 - Flow 재생 비용 측정 (mayapy, 중앙값). 체인(뼈 12) 1 / 5 / 10 / 30, Tip Follow on / off.
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" perf_flow.py
import os
import sys
import time
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import maya.standalone  # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402
from tools.A00390_WindTool_V03.app.core import flow_manager as fmg  # noqa: E402


def scene(n_chains, follow):
    cmds.file(new=True, force=True)
    cmds.currentUnit(time="film")
    cmds.evaluationManager(mode="parallel")
    roots = []
    for c in range(n_chains):
        cmds.select(clear=True)
        js = [cmds.joint(p=(c * 0.5, 13 - k, 0)) for k in range(13)]
        roots.append(js[0])
    t0 = time.time()
    built, drv, msg = fmg.build_flow(roots, preset="Breeze", tip_follow=follow)
    build_s = time.time() - t0
    ends = [cmds.listRelatives(r, allDescendents=True, type="joint")[0] for r in roots]
    nodes = len(cmds.ls())
    samples = []
    for rep in range(5):
        t0 = time.time()
        for f in range(1, 61):
            cmds.currentTime(f)
            for e in ends:
                cmds.getAttr(e + ".worldMatrix[0]")
        samples.append((time.time() - t0) / 60.0 * 1000.0)
    return build_s, nodes, statistics.median(samples)


print("chains | follow | build s | scene nodes | ms/frame | fps")
for n in (1, 5, 10, 30):
    for follow in (True, False):
        b, nodes, ms = scene(n, follow)
        print("{0:6d} | {1:6} | {2:7.2f} | {3:11d} | {4:8.2f} | {5:6.0f}".format(n, str(follow), b, nodes, ms, 1000.0 / ms))
maya.standalone.uninitialize()
