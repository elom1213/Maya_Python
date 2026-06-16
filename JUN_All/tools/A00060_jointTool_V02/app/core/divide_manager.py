# -*- coding: utf-8 -*-
# Divide 탭 로직 - MEL JointTool V05.03 "Divide" 포팅.
#   JUN_get_curve / JUN_get_curves_strEnd / JUN_rebuild_crv /
#   JUN_rebuildCurves_spans / JUN_cmd_makeJnt_divide
#   (+ Select/Add Start End 헬퍼 pairs_from_selection)

import maya.cmds as cmds

from .curve_joint_manager import cv_indices_of_curve, joints_along_curve, POINT_TYPE_EP


def _curve_between(pos_a, pos_b):
    """MEL JUN_get_curve - 두 점 사이 degree1 커브."""
    return cmds.curve(d=1, p=[pos_a, pos_b], k=[0, 1])


def curves_from_pairs(starts, ends):
    """MEL JUN_get_curves_strEnd - 시작/끝 쌍마다 커브 생성.
    원본과 동일하게 object-space translation(xform -q -translation)을 사용한다."""
    curves = []
    n = max(len(starts), len(ends))
    for i in range(n):
        pos_a = cmds.xform(starts[i], q=True, translation=True)
        pos_b = cmds.xform(ends[i], q=True, translation=True)
        curves.append(_curve_between(pos_a, pos_b))
    return curves


def rebuild_span(curve, num_span):
    """MEL JUN_rebuild_crv - degree3 으로 span 재구성."""
    result = cmds.rebuildCurve(curve, ch=0, rpo=1, end=1, kr=0,
                               s=num_span, d=3, rt=0)
    return result[0]


def make_joints_divided(starts, ends, num_div):
    """MEL JUN_cmd_makeJnt_divide - 시작/끝 사이를 num_div 개로 나눠 joint 생성."""
    if len(starts) != len(ends):
        raise ValueError("size of Start, End is not same")
    if num_div <= 0:
        raise ValueError("must type a number greater than 0")

    curves = curves_from_pairs(starts, ends)
    curves = [rebuild_span(c, num_div - 1) for c in curves]

    indices = cv_indices_of_curve(curves[0])
    indices = indices[:-2]  # 끝 2개 제거 (ep 개수)

    for crv in curves:
        joints_along_curve(crv, POINT_TYPE_EP, indices)


def pairs_from_selection(selection):
    """MEL JUN_cmd_selStrEnd - 선택 순서로 (start, end) 쌍 리스트 구성.
    n 개 선택 -> start = sel[0..n-2], end = sel[1..n-1]."""
    starts = []
    ends = []
    for i in range(len(selection) - 1):
        starts.append(selection[i])
        ends.append(selection[i + 1])
    return starts, ends
