# -*- coding: utf-8 -*-
# A00630 시험 공용: 경로 설정 · check · 월드 피벗 읽기
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
for p in (JUN_ALL, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    tail = str(extra) if extra is not None else ""
    print(("PASS " if cond else "FAIL ") + name + ("  | " + tail if tail else ""))


def world_pivot(node, frame):
    """그 시간의 회전 피벗 월드 위치 = 마야 `xform -q -ws -rp` 실측 (비교 기준).

    getAttr -time worldMatrix 는 쓰지 않는다 - 마야가 시간 문맥 값을 캐시해 두고 커브가 바뀌어도 옛 값을 주는 일이 있었다.
    시간을 옮겨 읽고 되돌린다. 그동안 undo 기록을 꺼서 시험의 undo 순서를 흐리지 않는다.
    """
    import maya.cmds as cmds
    keep_time = cmds.currentTime(q=True)
    keep_undo = cmds.undoInfo(q=True, state=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        cmds.currentTime(frame, update=True)
        p = cmds.xform(node, q=True, worldSpace=True, rotatePivot=True)
        cmds.currentTime(keep_time, update=True)
    finally:
        cmds.undoInfo(stateWithoutFlush=keep_undo)
    return tuple(p)


def finish():
    import maya.standalone
    print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
    sys.stdout.flush()           # os._exit 는 버퍼를 비우지 않는다 - 파이프로 받을 때 출력이 사라졌다
    maya.standalone.uninitialize()
    os._exit(0 if all(R) else 1)
