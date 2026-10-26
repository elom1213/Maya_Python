# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00580_FacialBoardBuilder - CSV 더미 -> 컨트롤 베이크 / 뒤로 경로 떼기 · 다시 걸기 (in-Maya · mayapy 공용)
#
# 흐름 (사용자 설명, V04 와 같다)
#   A00480 FileTool 이 CSV 를 BS_Face_CSV 별칭 52 에 키로 넣는다 -> 컨트롤러가 뒤로 경로로 따라온다
#   -> bake_csv_to_ctl() : 그 움직임을 컨트롤러 tx/ty 의 키로 옮기고 뒤로 경로를 뗀다 (컨트롤러에 키가 남는다)
#   -> 손 애니 · 클린업 -> BS_Face_Connect_01 은 늘 컨트롤러를 따라간다
#   다음 CSV 를 받기 전에 reconnect_csv() 로 뒤로 경로를 다시 건다 (명세는 CTRL_faceGUI.boardSpec 에 심겨 있어
#   json 파일이 없어도 씬만으로 된다).
#
#   from tools.A00580_FacialBoardBuilder import bake
#   bake.bake_csv_to_ctl()            # 선택 무관, 보드 전체
#   bake.reconnect_csv()  /  bake.disconnect_csv()  /  bake.csv_connected()
#
# 베이크 방식 : 한 축에 표현이 하나(0~1 직결)면 BS_Face_CSV 쪽 animCurve 를 **통째로 복사**(키 수 · 탄젠트 그대로,
# JALI bake_ctl_keys 의 copy 모드). 둘(±, a+ - a-)이거나 - 단일이면 두 커브 키 시각의 합집합마다 값을 계산해 키를
# 찍는다(auto 탄젠트). 커브가 없는 채널은 지금 값만 키 하나로 남긴다(정적).

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", ".."))
if JUN_ALL not in sys.path:
    sys.path.insert(0, JUN_ALL)

import maya.cmds as cmds

from tools.A00580_FacialBoardBuilder import board_spec as bsx
from tools.A00580_FacialBoardBuilder import build as fb

SPEC_ATTR = "boardSpec"


def find_root_ctl():
    """boardSpec 어트리뷰트를 가진 루트 컨트롤 (없으면 None)."""
    for node in cmds.ls("*.{0}".format(SPEC_ATTR), objectsOnly=True, recursive=True) or []:
        return node
    return None


def read_spec(root=None):
    """씬에 심긴 명세 json -> dict."""
    root = root or find_root_ctl()
    if not root:
        raise RuntimeError("No ARKit face board in the scene (CTRL_faceGUI.boardSpec not found).")
    return json.loads(cmds.getAttr("{0}.{1}".format(root, SPEC_ATTR)))


def _ns(root, name):
    """루트와 같은 네임스페이스로 이름을 맞춘다 (레퍼런스로 들어왔을 때)."""
    if ":" in root:
        return root.rsplit(":", 1)[0] + ":" + name
    return name


def csv_connected(spec=None, root=None):
    """뒤로 경로가 하나라도 걸려 있으면 True."""
    root = root or find_root_ctl()
    spec = spec or read_spec(root)
    for ctl in bsx.expand_controls(spec):
        for axis in bsx.axis_map(ctl):
            srcs = cmds.listConnections("{0}.{1}".format(_ns(root, ctl["name"]), axis), s=True, d=False) or []
            if any(cmds.nodeType(s) not in ("animCurveTL", "animCurveTU", "animCurveTA") for s in srcs):
                return True
    return False


def _curve_of(plug):
    crv = cmds.listConnections(plug, s=True, d=False, type="animCurve") or []
    return crv[0] if crv else None


def bake_csv_to_ctl(start=None, end=None, root=None):
    """BS_Face_CSV 의 키를 컨트롤러 tx/ty 로 옮기고 뒤로 경로를 뗀다. 돌려주는 것: 요약 dict."""
    root = root or find_root_ctl()
    spec = read_spec(root)
    csv = _ns(root, spec["names"]["csv_node"])
    fb.ensure_csv_elements(spec, csv)
    copied, computed, static, skipped = [], [], [], []

    for ctl in bsx.expand_controls(spec):
        name = _ns(root, ctl["name"])
        for axis, pairs in bsx.axis_map(ctl).items():
            dst = "{0}.{1}".format(name, axis)
            srcs = cmds.listConnections(dst, s=True, d=False) or []
            if not srcs or all(cmds.nodeType(s).startswith("animCurve") for s in srcs):
                skipped.append(dst)                  # 이미 베이크됐거나 연결이 없다
                continue
            # 기여하는 (부호, 커브) 모으기
            contrib = []
            for sign, attr in pairs:
                plug = "{0}.{1}".format(csv, attr)
                contrib.append((sign, attr, plug, _curve_of(plug)))
            curves = [c for _, _, _, c in contrib if c]
            value_now = cmds.getAttr(dst)
            fb.disconnect_backward_plug(dst)          # 먼저 뗀다 - 연결된 플러그엔 키를 못 찍는다
            if len(contrib) == 1 and contrib[0][0] > 0 and curves:
                # 0~1 직결 : 커브 통째 복사
                _, attr, plug, crv = contrib[0]
                cmds.copyKey(csv, attribute=attr, option="curve")
                cmds.pasteKey(name, attribute=axis, option="replaceCompletely")
                copied.append(dst)
            elif curves:
                times = set()
                for c in curves:
                    times.update(cmds.keyframe(c, q=True, timeChange=True) or [])
                for t in sorted(times):
                    v = 0.0
                    for sign, attr, plug, crv in contrib:
                        v += sign * cmds.getAttr(plug, time=t)
                    cmds.setKeyframe(dst, time=t, value=v)
                computed.append(dst)
            else:
                cmds.setAttr(dst, value_now)
                static.append(dst)
    # 남은 BWD_ 노드 정리
    for node in cmds.ls("BWD_*", type="plusMinusAverage") or []:
        if not cmds.listConnections(node + ".output1D", s=False, d=True):
            cmds.delete(node)
    summary = {"copied": copied, "computed": computed, "static": static, "skipped": skipped,
               "start": start, "end": end}
    print("bake_csv_to_ctl: {0} copied, {1} computed, {2} static, {3} skipped".format(
        len(copied), len(computed), len(static), len(skipped)))
    return summary


def disconnect_csv(root=None):
    """뒤로 경로를 전부 뗀다 (키는 두지 않는다 - 그냥 분리). 돌려주는 것: 뗀 플러그 목록."""
    root = root or find_root_ctl()
    spec = read_spec(root)
    return fb.disconnect_backward(spec, prefix=_ns(root, ""))


def reconnect_csv(root=None):
    """뒤로 경로를 명세대로 다시 건다. 컨트롤러에 animCurve 가 붙어 있으면 그 축은 건너뛴다(키를 지우지 않는다).

    돌려주는 것: (새로 건 축 수, 키가 있어 건너뛴 플러그 목록).
    """
    root = root or find_root_ctl()
    spec = read_spec(root)
    kept = []
    for ctl in bsx.expand_controls(spec):
        name = _ns(root, ctl["name"])
        for axis in bsx.axis_map(ctl):
            dst = "{0}.{1}".format(name, axis)
            if _curve_of(dst):
                kept.append(dst)
    made = fb.connect_backward(spec, csv_node=_ns(root, spec["names"]["csv_node"]), prefix=_ns(root, ""),
                               skip_plugs=set(kept))
    print("reconnect_csv: {0} axis reconnected, {1} kept their keys".format(made, len(kept)))
    return made, kept


def clear_ctl_keys(root=None):
    """컨트롤러 tx/ty 의 animCurve 를 지운다 (다시 CSV 를 받기 전에). 돌려주는 것: 지운 수."""
    root = root or find_root_ctl()
    spec = read_spec(root)
    n = 0
    for ctl in bsx.expand_controls(spec):
        name = _ns(root, ctl["name"])
        for axis in bsx.axis_map(ctl):
            crv = _curve_of("{0}.{1}".format(name, axis))
            if crv:
                cmds.delete(crv)
                n += 1
    return n
