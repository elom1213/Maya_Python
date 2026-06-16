# -*- coding: utf-8 -*-
# Aim 탭 로직 - MEL JointTool V05.03 "Aim" 포팅.
#   JUN_cmd_make_jntAim (ikHandle + poleVectorConstraint)

import maya.cmds as cmds


def make_joint_aim(starts, ends, pole_targets):
    """MEL JUN_cmd_make_jntAim - 시작/끝 joint 쌍에 ikHandle 생성 후 pole vector 구속."""
    n = min(len(starts), len(ends))
    for i in range(n):
        ik = cmds.ikHandle(sj=starts[i], ee=ends[i])
        if i < len(pole_targets):
            cmds.poleVectorConstraint(pole_targets[i], ik[0])
