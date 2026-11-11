# -*- coding: utf-8 -*-
"""Copy Key - 잠긴 채널이 섞여도 안 잠긴 채널끼리는 복사되는지 시험 (mayapy).

    "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe" tests/test_copykey_locked.py
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


AT = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
ALL_ON = {k: True for k in AT}


def scene(lock_src=(), lock_dst=(), dst_keys=False):
    cmds.file(new=True, force=True)
    a = cmds.createNode("transform", n="A")
    b = cmds.createNode("transform", n="B")
    for i, at in enumerate(AT):
        cmds.setKeyframe(a, at=at, t=1, v=i + 1)
        cmds.setKeyframe(a, at=at, t=10, v=(i + 1) * 10)
        if dst_keys:
            cmds.setKeyframe(b, at=at, t=5, v=-1)
    for at in lock_src:
        cmds.setAttr(a + "." + at, lock=True)
    for at in lock_dst:
        cmds.setAttr(b + "." + at, lock=True)
    return a, b


def values(node, at):
    """잠긴 채널은 keyframe -q 가 None 이라 잠깐 풀어서 읽는다."""
    plug = node + "." + at
    was = cmds.getAttr(plug, lock=True)
    parent = (cmds.attributeQuery(at, node=node, listParent=True) or [None])[0]
    plock = parent and cmds.getAttr(node + "." + parent, lock=True)
    if plock:
        cmds.setAttr(node + "." + parent, lock=False)
    cmds.setAttr(plug, lock=False)
    v = cmds.keyframe(plug, q=True, vc=True)
    cmds.setAttr(plug, lock=was)
    if plock:
        cmds.setAttr(node + "." + parent, lock=True)
    return v


# 1) 필터 없는 경로(9축 전부 ON) - Target ty 잠김
a, b = scene(lock_dst=("ty",))
n, msg = CKM.copy_keys([a], [b], 1, 10, {}, attr_flags=ALL_ON)
print(msg)
check("all: pair counted", n == 1)
check("all: tx copied", values(b, "tx") == [1.0, 10.0])
check("all: sz copied", values(b, "sz") == [9.0, 90.0])
check("all: locked ty untouched", values(b, "ty") is None)
check("all: log names locked ty", "Locked on Target" in msg and "translateY" in msg)

# 2) 필터 없는 경로 - Target 에 원래 키 + 잠김 -> 잠긴 쪽 기존 커브 보존
a, b = scene(lock_dst=("ty",), dst_keys=True)
CKM.copy_keys([a], [b], 1, 10, {}, attr_flags=ALL_ON)
check("all+keys: locked ty keeps own curve", values(b, "ty") == [-1.0])
# insert 는 붙이는 구간(1~10)만큼 뒤 키를 민다 - 원래 5 의 키는 14 로.
check("all+keys: tx inserted", values(b, "tx") == [1.0, 10.0, -1.0])
check("all+keys: locked ty keeps time 5", cmds.keyframe(b + ".ty", q=True, tc=True)
      in (None, [5.0]))

# 3) 명시 경로(일부 축) - Target tx, ry 잠김
flags = dict(ALL_ON, sz=False)
a, b = scene(lock_dst=("tx", "ry"))
n, msg = CKM.copy_keys([a], [b], 1, 10, {}, attr_flags=flags)
print(msg)
check("attrs: pair counted", n == 1)
check("attrs: ty copied", values(b, "ty") == [2.0, 20.0])
check("attrs: rz copied", values(b, "rz") is not None)
check("attrs: tx skipped", values(b, "tx") is None)
check("attrs: ry skipped", values(b, "ry") is None)
check("attrs: sz not copied (unchecked)", values(b, "sz") is None)
check("attrs: log lists locked", "translateX" in msg and "rotateY" in msg
      and "Locked on Target" in msg)

# 4) Base 쪽 잠김 - 키는 그대로 복사된다
a, b = scene(lock_src=("tx", "rz"))
n, msg = CKM.copy_keys([a], [b], 1, 10, {}, attr_flags=flags)
check("src locked: tx still copied", values(b, "tx") == [1.0, 10.0])
check("src locked: rz still copied", values(b, "rz") is not None)
check("src locked: no locked warning", "Locked on Target" not in msg)

# 5) compound 잠금(translate) + Reverse tx 체크 - 나머지 채널 복사, 잠긴 쪽 반전 안 됨
a, b = scene(lock_dst=("translate",))
n, msg = CKM.copy_keys([a], [b], 1, 10, {"tx": True, "rx": True}, attr_flags=ALL_ON)
print(msg)
check("compound: rx copied", values(b, "rx") is not None)
check("compound: tx skipped", values(b, "tx") is None)

# 6) Target 채널이 전부 잠김 - 에러 없이 skipped
a, b = scene(lock_dst=AT)
n, msg = CKM.copy_keys([a], [b], 1, 10, {}, attr_flags=ALL_ON)
print(msg)
check("all locked: 0 pairs, no exception", n == 0 and "skipped" in msg)

# 7) rotate order 경고 - Target 회전이 전부 잠겨 있으면 묻지 않는다
a, b = scene(lock_dst=("rx", "ry", "rz"))
cmds.setAttr(a + ".rotateOrder", 5)
check("rotate order: skipped when target rotate locked",
      CKM.rotate_order_mismatches([a], [b]) == [])
a, b = scene(lock_dst=("rx",))
cmds.setAttr(a + ".rotateOrder", 5)
check("rotate order: still warns when partly locked",
      len(CKM.rotate_order_mismatches([a], [b])) == 1)

print("\n{0} passed, {1} failed".format(passed, failed))
maya.standalone.uninitialize()
sys.exit(1 if failed else 0)
