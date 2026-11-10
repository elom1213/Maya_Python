# -*- coding: utf-8 -*-
"""Kawaii 와 Physics Asset 을 나란히 보는 데모 씬.

같은 꼬리 조인트 체인 두 개 — 루트가 흔들리고(정지 -> 회전 -> 정지), 자식에는 꼬리를 마는 키가
있다. 왼쪽(KAWAII)은 Kawaii 솔버, 오른쪽(PHYSICS)은 Physics Asset 솔버로 키를 굽는다.

    마야 스크립트 에디터:  import tools.A00410_SecondaryMotion.tests.demo_physics_asset as d; d.build()
    mayapy 로 파일 저장:   mayapy tests/demo_physics_asset.py <저장할 .ma 경로>

보이는 것: 왼쪽은 말린 모양을 유지한 채 출렁이고, 오른쪽은 말린 키를 무시하고 중력으로
늘어진 채 진자처럼 흔들린다.
"""
import os
import sys

N = 8
BONE = 6.0
START, END = 1, 120


def _chain(prefix, x):
    import maya.cmds as cmds
    cmds.select(clear=True)
    js = [cmds.joint(name="{0}_tail{1}".format(prefix, i), p=(x + BONE * i, 100, 0))
          for i in range(N)]
    cmds.joint(js[0], e=True, oj="xyz", sao="yup", ch=True, zso=True)
    for f, v in ((1, 0), (20, 0), (30, 60), (45, -45), (60, 0), (120, 0)):
        cmds.setKeyframe(js[0], at="rotateY", t=f, v=v)
    for j in js[1:]:
        for f, v in ((1, 0), (40, 25), (80, 25), (120, 0)):
            cmds.setKeyframe(j, at="rotateZ", t=f, v=v)
    return [cmds.ls(j, long=True)[0] for j in js]


def build():
    import maya.cmds as cmds
    from tools.A00410_SecondaryMotion.app.core import bake_manager as bm
    from tools.A00410_SecondaryMotion.app.core import chain_solver
    from tools.A00410_SecondaryMotion.app.core import physics_solver as ps
    from tools.A00410_SecondaryMotion.app.core import scene_sampler as ss

    cmds.playbackOptions(minTime=START, maxTime=END)
    for prefix, x, params in (("KAWAII", -60.0, chain_solver.SolverParams()),
                              ("PHYSICS", 20.0, ps.PhysicsParams())):
        js = _chain(prefix, x)
        s = bm.SecondaryMotionSession()
        s.prepare(js, ss.MODE_CHAIN, ss.TARGET_JOINT, START, END)
        s.apply(params, bm.OUTPUT_KEYS)
        label = cmds.textCurves(ch=False, f="Arial", t=prefix)[0]
        cmds.setAttr(label + ".translate", x, 110, 0)
        cmds.setAttr(label + ".scale", 4, 4, 4)
    return True


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join(here, "..", "..", "..")))
    import maya.standalone
    maya.standalone.initialize(name="python")
    import maya.cmds as cmds
    cmds.file(new=True, force=True)
    build()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "demo_physics_asset.ma")
    cmds.file(rename=out)
    cmds.file(save=True, type="mayaAscii")
    print("saved", out)
    maya.standalone.uninitialize()
    os._exit(0)
