# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00580_FacialBoardBuilder - ARKit 52 페이셜 컨트롤 보드 빌더 (mayapy / in-Maya 공용)
#
#   mayapy build.py [spec.json] <out.ma> [--mb]      # 새 씬에 보드를 만들어 .ma (와 .mb) 로 저장
#
# 명세(spec/arkit52_board_v05.json)에서 만든다 - 손으로 만들지 않는다. 자리 · 이름 · 범위를 바꾸려면 json 을
# 고치고 다시 돈다. 계획 · 결정은 docs/plans/Facial_ARKit52_Ctl_V05_plan.md.
#
# 만드는 것
#   GRP_faceGUI_follow / FOLLOW_<Head|Global|World>_loc     # 보드가 따라갈 자리 3개 (사용자가 머리 · 루트 본에 붙인다)
#   GRP_faceGUI  (parentConstraint <- 3 locator, 가중치 <- CTRL_faceGUI.Head/Global/World)
#   └── CTRL_faceGUI          # 루트 컨트롤 : 보드 이동 · 따라가기 가중치 · boardSpec(명세 json 전체)
#       ├── FRM_faceGUI       # 테두리 · 부위 라벨 (Reference)
#       ├── GRP_<region>GUI   # brow · eye · cheek · nose · mouth · jaw · tongue
#       │   └── FRM_<ctl> (scale = unit) > CTRL_<ctl>   # 트랙/패드 테두리 + 라벨 + 컨트롤(원)
#       └── BS_Face_Connect_01        # 출력 더미 (attr 52, V04 와 같은 이름 · 순서)
#   BS_Face_CSV               # 입력 더미 blendShape (타겟 별칭 52, V04 와 같은 순서, 지오메트리 없음 - M0 실측 OK)
#   FWD_<attr>_neg / FWD_<attr>_clamp         # 앞으로 : 컨트롤 -> Connect_01
#   BWD_<ctl>_<axis>                          # 뒤로   : BS_Face_CSV -> 컨트롤 (plusMinusAverage, 없으면 직결)
#
# 컨트롤 값은 늘 -1..1 / 0..1 (transformLimits 가 손 조작 · 연결값 둘 다 자른다 - M0 실측). FRM 의 scale 이
# 값 1 을 보드 위 몇 cm 로 보일지(unit) 정하므로 UE 로 갈 때도 값 범위는 같다.

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", ".."))
if JUN_ALL not in sys.path:
    sys.path.insert(0, JUN_ALL)

import maya.cmds as cmds

from tools.A00580_FacialBoardBuilder import board_spec as bsx

REFERENCE = 2
FONT = "Arial"


# ---------------------------------------------------------------- small helpers

def _lock(node, channels):
    for ch in channels:
        cmds.setAttr("{0}.{1}".format(node, ch), lock=True, keyable=False, channelBox=False)


def _reference(node):
    cmds.setAttr(node + ".overrideEnabled", 1)
    cmds.setAttr(node + ".overrideDisplayType", REFERENCE)


def _color(shape, rgb):
    cmds.setAttr(shape + ".overrideEnabled", 1)
    cmds.setAttr(shape + ".overrideDisplayType", 0)
    cmds.setAttr(shape + ".overrideRGBColors", 1)
    cmds.setAttr(shape + ".overrideColorRGB", rgb[0], rgb[1], rgb[2])


def _line(name, points, parent, closed=False):
    pts = list(points) + ([points[0]] if closed else [])
    crv = cmds.curve(d=1, p=pts, n=name)
    shp = cmds.listRelatives(crv, s=True)[0]
    cmds.rename(shp, name + "Shape")
    cmds.parent(crv, parent, r=True)
    _reference(crv)
    return crv


def _circle(name, radius, parent, rgb):
    crv = cmds.circle(n=name, nr=(0, 0, 1), r=radius, ch=False)[0]
    shp = cmds.listRelatives(crv, s=True)[0]
    shp = cmds.rename(shp, name + "Shape")
    cmds.parent(crv, parent, r=True)
    _color(shp, rgb)
    return crv


def _text(name, text, parent, scale, pos, center=True):
    """textCurves 라벨 (Reference). 가로 중앙 정렬. mayapy 에서도 된다 (폰트 경고만)."""
    node = cmds.textCurves(ch=False, f=FONT, t=text)[0]
    node = cmds.rename(node, name)
    bb = cmds.exactWorldBoundingBox(node)
    width = bb[3] - bb[0]
    cmds.parent(node, parent, r=True)
    off = -width * scale * 0.5 if center else 0.0
    cmds.setAttr(node + ".t", pos[0] + off, pos[1], 0.0)
    cmds.setAttr(node + ".s", scale, scale, scale)
    _reference(node)
    # 글자 트랜스폼들은 선택되지 않게 잠근다
    for ch in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        cmds.setAttr("{0}.{1}".format(node, ch), lock=True)
    return node


def _add_float(node, attr, default=0.0, lo=None, hi=None, keyable=True):
    kw = {"ln": attr, "at": "double", "dv": default, "k": keyable}
    if lo is not None:
        kw["min"] = lo
    if hi is not None:
        kw["max"] = hi
    cmds.addAttr(node, **kw)


# ---------------------------------------------------------------- dummies

def build_csv_dummy(spec, parent):
    """BS_Face_CSV - weight 별칭 52 (V04 와 같은 인덱스) 를 가진 blendShape. A00480 FileTool 이 aliasAttr 로 찾는다.

    ★ 지오메트리 **없는** blendShape 는 쓸 수 없다 (mayapy 실측 2026-10-26): 연결된 animCurve 나 pma 노드를
    delete 하거나 `cutKey -clear` 만 해도 Maya 가 "쓰이지 않는 디포머" 로 보고 노드째 지우고, 값 0 · 미연결
    weight 원소는 저장 때 빠져 별칭이 허공을 가리킨다. 숨긴 4점 평면(BS_Face_CSV_geo)에 붙이면 전부 살아남고
    미연결 원소도 저장 왕복에서 남는다. V04 의 글자 메시가 하던 역할을 이 평면이 한다 (FileTool 은 메시를 안 본다).
    """
    name = spec["names"]["csv_node"]
    geo = cmds.polyPlane(name=name + "_geo", w=0.1, h=0.1, sx=1, sy=1, ch=False)[0]
    cmds.parent(geo, parent)
    bs = cmds.blendShape(geo, name=name)[0]
    for i, alias in enumerate(spec["csv_alias_order"]):
        plug = "{0}.weight[{1}]".format(bs, i)
        cmds.setAttr(plug, 0.0)                     # 원소를 만든다
        cmds.aliasAttr(alias, plug)
    cmds.setAttr(geo + ".v", 0)
    _lock(geo, ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"))
    return bs


def ensure_csv_elements(spec, csv_node=None):
    """BS_Face_CSV 의 weight 원소 52 개가 전부 있는지 보고, 빠진 것은 다시 만든다(값 0). 돌려주는 것: 만든 수."""
    csv_node = csv_node or spec["names"]["csv_node"]
    existing = set(cmds.getAttr(csv_node + ".weight", multiIndices=True) or [])
    made = 0
    for i, alias in enumerate(spec["csv_alias_order"]):
        if i not in existing:
            cmds.setAttr("{0}.weight[{1}]".format(csv_node, i), 0.0)
            made += 1
    return made


def build_out_dummy(spec, parent):
    """BS_Face_Connect_01 - attr 52 (V04 순서) 를 가진 transform."""
    name = spec["names"]["out_node"]
    node = cmds.createNode("transform", name=name, parent=parent)
    for attr in spec["arkit52"]:
        _add_float(node, attr, 0.0)
    _lock(node, ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"))
    return node


# ---------------------------------------------------------------- one control

def build_control(ctl, spec, parent):
    """FRM_<ctl>(scale unit) > CTRL_<ctl>. 트랙/패드 테두리 · 라벨 · 리밋 · 색. 돌려주는 것: CTRL 이름."""
    board = spec["board"]
    unit = float(board["unit"])
    rad = float(board["ctl_radius"]) / unit
    name = ctl["name"]
    frm = cmds.createNode("transform", name="FRM_" + name[5:] if name.startswith("CTRL_") else "FRM_" + name,
                          parent=parent)
    cmds.setAttr(frm + ".t", ctl["pos"][0], ctl["pos"][1], 0.0)
    cmds.setAttr(frm + ".s", unit, unit, unit)
    _reference(frm)

    lim = ctl.get("limits") or {}
    tx = lim.get("tx", [0, 0])
    ty = lim.get("ty", [0, 0])
    kind = ctl["type"]

    # 테두리 : 슬라이더는 트랙 선 + 눈금, 패드는 리밋 범위에 여백(pad_margin)을 두른 사각
    m = float(board.get("pad_margin", 0.3))
    if kind == "pad":
        x0, x1, y0, y1 = tx[0] - m, tx[1] + m, ty[0] - m, ty[1] + m
        _line(frm + "_pad", [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], frm, closed=True)
        _line(frm + "_zeroX", [(x0, 0, 0), (x1, 0, 0)], frm)
        _line(frm + "_zeroY", [(0, y0, 0), (0, y1, 0)], frm)
        bottom = y0
    elif kind == "slider_x":
        _line(frm + "_track", [(tx[0], 0, 0), (tx[1], 0, 0)], frm)
        for v in sorted(set([tx[0], 0, tx[1]])):
            _line(frm + "_tick{0}".format(int(v) + 1), [(v, -0.25, 0), (v, 0.25, 0)], frm)
        bottom = -m
    else:  # slider (ty)
        _line(frm + "_track", [(0, ty[0], 0), (0, ty[1], 0)], frm)
        for v in sorted(set([ty[0], 0, ty[1]])):
            _line(frm + "_tick{0}".format(int(v) + 1), [(-0.25, v, 0), (0.25, v, 0)], frm)
        bottom = min(ty[0], 0.0) - m

    # 라벨 : 아래쪽
    if board.get("labels", True) and ctl.get("label"):
        _text(frm + "_label", ctl["label"], frm, float(board["label_scale"]) / unit, (0.0, bottom - 0.7))

    # 컨트롤
    rgb = spec["colors"][ctl.get("color", "C")]
    c = _circle(name, rad, frm, rgb)
    cmds.transformLimits(c, tx=(tx[0], tx[1]), etx=(True, True),
                         ty=(ty[0], ty[1]), ety=(True, True),
                         tz=(0, 0), etz=(True, True))
    locked = ["tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
    if tx[0] == 0 and tx[1] == 0:
        locked.append("tx")
    if ty[0] == 0 and ty[1] == 0:
        locked.append("ty")
    _lock(c, locked)
    if ctl.get("unused"):
        cmds.addAttr(c, ln="notConnected", at="bool", dv=True)
        cmds.setAttr(c + ".notConnected", lock=True)
    return c


# ---------------------------------------------------------------- connections

def connect_forward(spec, out_node=None):
    """컨트롤 -> BS_Face_Connect_01. 0~1 단일 + 축은 직결, - 축은 ×-1, 한 축에 둘이면 clamp(0,1)."""
    out_node = out_node or spec["names"]["out_node"]
    made = []
    for ctl in bsx.expand_controls(spec):
        for axis, pairs in bsx.axis_map(ctl).items():
            src = "{0}.{1}".format(ctl["name"], axis)
            paired = len(pairs) > 1
            for sign, attr in pairs:
                plug = src
                if sign < 0:
                    neg = cmds.createNode("multiplyDivide", name="FWD_{0}_neg".format(attr))
                    cmds.setAttr(neg + ".input2X", -1.0)
                    cmds.connectAttr(plug, neg + ".input1X")
                    plug = neg + ".outputX"
                    made.append(neg)
                if paired:
                    cl = cmds.createNode("clamp", name="FWD_{0}_clamp".format(attr))
                    cmds.setAttr(cl + ".minR", 0.0)
                    cmds.setAttr(cl + ".maxR", 1.0)
                    cmds.connectAttr(plug, cl + ".inputR")
                    plug = cl + ".outputR"
                    made.append(cl)
                cmds.connectAttr(plug, "{0}.{1}".format(out_node, attr), force=True)
    return made


def connect_backward(spec, csv_node=None, prefix="", skip_plugs=None):
    """BS_Face_CSV -> 컨트롤. 0~1 단일 + 축은 직결, 그 밖은 plusMinusAverage(a+ - a-).

    이미 입력이 있는 축 · skip_plugs 에 든 축은 건너뛴다. prefix 는 네임스페이스("ns:").
    돌려주는 것: 새로 건 축의 수.
    """
    csv_node = csv_node or (prefix + spec["names"]["csv_node"])
    skip_plugs = skip_plugs or set()
    ensure_csv_elements(spec, csv_node)
    made = 0
    for ctl in bsx.expand_controls(spec):
        name = prefix + ctl["name"]
        for axis, pairs in bsx.axis_map(ctl).items():
            dst = "{0}.{1}".format(name, axis)
            if dst in skip_plugs or cmds.listConnections(dst, s=True, d=False):
                continue
            plus = [a for s, a in pairs if s > 0]
            minus = [a for s, a in pairs if s < 0]
            if len(plus) == 1 and not minus:
                cmds.connectAttr("{0}.{1}".format(csv_node, plus[0]), dst)
                made += 1
                continue
            pma = cmds.createNode("plusMinusAverage", name="BWD_{0}_{1}".format(ctl["name"], axis))
            cmds.setAttr(pma + ".operation", 2)       # subtract : [0] - [1]
            cmds.setAttr(pma + ".input1D[0]", 0.0)
            cmds.setAttr(pma + ".input1D[1]", 0.0)
            if plus:
                cmds.connectAttr("{0}.{1}".format(csv_node, plus[0]), pma + ".input1D[0]")
            if minus:
                cmds.connectAttr("{0}.{1}".format(csv_node, minus[0]), pma + ".input1D[1]")
            cmds.connectAttr(pma + ".output1D", dst)
            made += 1
    return made


def disconnect_backward_plug(dst):
    """컨트롤 플러그 하나의 뒤로 입력을 뗀다 (animCurve 는 둔다, BWD_ 노드는 지운다). 뗐으면 True."""
    freed = False
    for src in cmds.listConnections(dst, s=True, d=False, plugs=True) or []:
        node = src.split(".")[0]
        if cmds.nodeType(node).startswith("animCurve"):
            continue                                   # 베이크된 키는 둔다
        cmds.disconnectAttr(src, dst)
        freed = True
        if node.split(":")[-1].startswith("BWD_"):
            # ★ 입력을 먼저 뗀다. 입력이 걸린 채 pma 를 delete 하면 Maya 가 상류의 BS_Face_CSV(지오메트리 없는
            #   blendShape)와 keepAlive 까지 "쓰이지 않는 노드" 로 보고 함께 지운다 (mayapy 실측 2026-10-26).
            conns = cmds.listConnections(node, s=True, d=False, plugs=True, connections=True) or []
            for i in range(0, len(conns), 2):
                cmds.disconnectAttr(conns[i + 1], conns[i])
            cmds.delete(node)
    return freed


def disconnect_backward(spec, prefix=""):
    """뒤로 경로를 전부 뗀다. 돌려주는 것: 뗀 컨트롤 플러그 목록."""
    freed = []
    for ctl in bsx.expand_controls(spec):
        for axis in bsx.axis_map(ctl):
            dst = "{0}.{1}".format(prefix + ctl["name"], axis)
            if disconnect_backward_plug(dst):
                freed.append(dst)
    return freed


# ---------------------------------------------------------------- board

def build(spec):
    """현재 씬에 보드를 만든다. 돌려주는 것: {root_grp, root_ctl, csv, out, controls[...]}."""
    problems = bsx.check_spec(spec)
    if problems:
        raise ValueError("spec problems:\n  " + "\n  ".join(problems))

    names = spec["names"]
    board = spec["board"]
    colors = spec["colors"]

    # 따라가기 자리 3개
    follow_grp = cmds.createNode("transform", name=names["follow_grp"])
    locs = []
    for tag in names["follow_targets"]:
        loc = cmds.spaceLocator(name="FOLLOW_{0}_loc".format(tag))[0]
        cmds.parent(loc, follow_grp)
        locs.append(loc)
    _lock(follow_grp, ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"))

    # 루트
    root_grp = cmds.createNode("transform", name=names["root_grp"])
    root_ctl = cmds.createNode("transform", name=names["root_ctl"], parent=root_grp)
    fr = board["frame"]
    pad = 0.4
    crv = cmds.curve(d=1, n=root_ctl + "_shapeSrc",
                     p=[(fr[0] - pad, fr[1] - pad, 0), (fr[2] + pad, fr[1] - pad, 0),
                        (fr[2] + pad, fr[3] + pad, 0), (fr[0] - pad, fr[3] + pad, 0), (fr[0] - pad, fr[1] - pad, 0)])
    shp = cmds.listRelatives(crv, s=True)[0]
    cmds.parent(shp, root_ctl, r=True, s=True)
    cmds.delete(crv)
    shp = cmds.rename(shp, root_ctl + "Shape")
    _color(shp, colors["root"])
    t = board.get("default_root_translate", [0, 0, 0])
    cmds.setAttr(root_ctl + ".t", t[0], t[1], t[2])

    cmds.addAttr(root_ctl, ln="follow", at="enum", en="----", k=False)
    cmds.setAttr(root_ctl + ".follow", channelBox=True, lock=True)
    for tag in names["follow_targets"]:
        _add_float(root_ctl, tag, float(names["follow_default"].get(tag, 0.0)), 0.0, 1.0)
    cmds.addAttr(root_ctl, ln="boardVersion", dt="string")
    cmds.setAttr(root_ctl + ".boardVersion", str(spec["version"]), type="string", lock=True)
    cmds.addAttr(root_ctl, ln=names["spec_attr"], dt="string")
    cmds.setAttr("{0}.{1}".format(root_ctl, names["spec_attr"]), bsx.spec_to_json(spec), type="string", lock=True)
    _lock(root_ctl, ("sx", "sy", "sz", "v"))

    con = cmds.parentConstraint(locs, root_grp, mo=False)[0]
    con = cmds.rename(con, root_grp + "_follow_parentConstraint")
    weights = cmds.parentConstraint(con, q=True, weightAliasList=True)
    for tag, w in zip(names["follow_targets"], weights):
        cmds.connectAttr("{0}.{1}".format(root_ctl, tag), "{0}.{1}".format(con, w), force=True)
    _lock(root_grp, ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"))

    # 테두리 + 부위 라벨
    frm = cmds.createNode("transform", name=names["frame_grp"], parent=root_ctl)
    _line(frm + "_border", [(fr[0], fr[1], 0), (fr[2], fr[1], 0), (fr[2], fr[3], 0), (fr[0], fr[3], 0)], frm, closed=True)
    if board.get("labels", True):
        for text, pos in (board.get("region_labels") or {}).items():
            _text(frm + "_" + text.lower(), text, frm, float(board["label_scale"]) * 1.5, (pos[0], pos[1]))
    _reference(frm)
    _lock(frm, ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"))

    # 부위 그룹 + 컨트롤
    region_grp = {}
    for region in spec["regions"]:
        g = cmds.createNode("transform", name="GRP_{0}GUI".format(region), parent=root_ctl)
        _lock(g, ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"))
        region_grp[region] = g
    controls = []
    for ctl in bsx.expand_controls(spec):
        controls.append(build_control(ctl, spec, region_grp[ctl["region"]]))

    # 더미 + 연결
    csv = build_csv_dummy(spec, root_grp)
    out = build_out_dummy(spec, root_grp)
    connect_forward(spec, out)
    connect_backward(spec, csv)

    cmds.fileInfo("jun_face_board", "ARKit52 board v{0} built by A00580_FacialBoardBuilder".format(spec["version"]))
    return {"root_grp": root_grp, "root_ctl": root_ctl, "csv": csv, "out": out,
            "controls": controls, "follow_locs": locs, "constraint": con}


def build_file(out_path, spec_path=None, also_mb=False):
    """새 씬 -> build -> .ma 저장 (also_mb 면 같은 이름의 .mb 도). 돌려주는 것: 저장한 경로 목록."""
    spec = bsx.load_spec(spec_path)
    cmds.file(new=True, force=True)
    cmds.currentUnit(linear="cm")
    build(spec)
    saved = []
    out_path = os.path.abspath(out_path)
    folder = os.path.dirname(out_path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    base, ext = os.path.splitext(out_path)
    ma = base + ".ma"
    cmds.file(rename=ma)
    cmds.file(save=True, type="mayaAscii", force=True)
    saved.append(ma)
    if also_mb or ext.lower() == ".mb":
        mb = base + ".mb"
        cmds.file(rename=mb)
        cmds.file(save=True, type="mayaBinary", force=True)
        saved.append(mb)
    return saved


def _main(argv):
    args = [a for a in argv if not a.startswith("--")]
    also_mb = "--mb" in argv
    if not args:
        print("usage: mayapy build.py [spec.json] <out.ma> [--mb]")
        return 2
    spec_path = args[0] if len(args) > 1 else None
    out_path = args[-1]
    import maya.standalone
    maya.standalone.initialize(name="python")
    try:
        for p in build_file(out_path, spec_path, also_mb):
            print("saved", p)
    finally:
        maya.standalone.uninitialize()
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
