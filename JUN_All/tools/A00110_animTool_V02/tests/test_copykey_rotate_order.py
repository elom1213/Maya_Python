# -*- coding: utf-8 -*-
"""Copy Key rotate order 경고 - core 판정 시험 (mayapy).

    "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe" tests/test_copykey_rotate_order.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if JUN_ALL not in sys.path:
    sys.path.insert(0, JUN_ALL)

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

from tools.A00110_animTool_V02.app.core.copykey_manager import CopyKeyManager as CKM

passed = 0
failed = 0


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", label)
    else:
        failed += 1
        print("FAIL", label)


try:
    cmds.file(new=True, force=True)
    a = cmds.createNode("transform", name="A")
    b = cmds.createNode("transform", name="B")
    c = cmds.createNode("transform", name="C")
    j = cmds.createNode("joint", name="J")
    cmds.setAttr(b + ".rotateOrder", 5)   # zyx
    cmds.setAttr(j + ".rotateOrder", 0)   # xyz (A 와 같음)

    check("same order -> none", CKM.rotate_order_mismatches([a], [c]) == [])
    check("diff order -> one",
          CKM.rotate_order_mismatches([a], [b]) == [(a, b, "xyz", "zyx")])
    check("joint vs transform same", CKM.rotate_order_mismatches([a], [j]) == [])

    # 1->n : A 하나를 B, C, J 에
    res = CKM.rotate_order_mismatches([a], [b, c, j], one_to_many=True)
    check("1->n only B", [r[1] for r in res] == [b])
    # n->n 짝: (A,C) (B,J) -> B(zyx) vs J(xyz)
    res = CKM.rotate_order_mismatches([a, b], [c, j, b], one_to_many=True)
    check("n->n pairs by index", res == [(b, j, "zyx", "xyz")])
    # 1->n 꺼짐 + Base 1개 -> 첫 짝만
    res = CKM.rotate_order_mismatches([a], [c, b], one_to_many=False)
    check("one_to_many off -> first pair only", res == [])

    # 없는 노드 / rotateOrder 없는 노드는 비교 안 함
    m = cmds.createNode("multiplyDivide", name="MD")
    check("missing node skipped", CKM.rotate_order_mismatches(["nope"], [b]) == [])
    check("non-transform skipped", CKM.rotate_order_mismatches([m], [b]) == [])

    # 회전 채널 포함 여부
    allon = {k: True for k, _ in CKM.COPY_ATTRS}
    check("all axes -> rotation", CKM.copies_rotation(CKM.resolve_attrs(allon)))
    tonly = {k: k.startswith("t") for k, _ in CKM.COPY_ATTRS}
    check("translate only -> no rotation",
          not CKM.copies_rotation(CKM.resolve_attrs(tonly)))
    ronly = dict(tonly, ry=True)
    check("ry -> rotation", CKM.copies_rotation(CKM.resolve_attrs(ronly)))
    check("custom only -> no rotation",
          not CKM.copies_rotation(CKM.resolve_attrs(
              {k: False for k, _ in CKM.COPY_ATTRS}, ["ikBlend"])))

    # build_pairs 는 copy_keys 와 같은 짝
    fan, pairs = CKM.build_pairs([a], [b, c], True)
    check("build_pairs 1->n", fan and pairs == [(a, b), (a, c)])
    fan, pairs = CKM.build_pairs([a, b], [c], True)
    check("build_pairs n->n short", (not fan) and pairs == [(a, c)])

    # copy_keys 가 리팩터 뒤에도 그대로 복사하는지
    cmds.setKeyframe(a, attribute="rotateX", time=1, value=10)
    cmds.setKeyframe(a, attribute="rotateX", time=5, value=50)
    n, msg = CKM.copy_keys([a], [b, c], 1, 5, {}, "replace", one_to_many=True,
                           attr_flags=allon)
    check("copy_keys 1->n still works", n == 2
          and cmds.keyframe(c + ".rotateX", q=True, valueChange=True) == [10.0, 50.0])
finally:
    print("\n{0}/{1} passed".format(passed, passed + failed))
    maya.standalone.uninitialize()
    sys.exit(1 if failed else 0)
