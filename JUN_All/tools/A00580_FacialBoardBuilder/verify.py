# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00580_FacialBoardBuilder - 빌드 결과 검증 (mayapy)  — 계획서 §8 T1 ~ T8
#
#   mayapy verify.py <board.ma> [--v04 <Ctl_Only_V04.mb>] [--spec spec.json]
#
# .ma 를 열어 T1~T7 을 돌리고, 같은 이름의 .mb 가 있으면 그것도 열어 T8(왕복) 로 T1~T5 를 다시 돈다.
# --v04 를 주면 V04 의 별칭 순서 · attr 순서를 직접 읽어 비교하고(T1), 이관표로 V04 키 -> V05 동치(T7b)를 본다.

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", ".."))
if JUN_ALL not in sys.path:
    sys.path.insert(0, JUN_ALL)

import maya.cmds as cmds

from tools.A00580_FacialBoardBuilder import board_spec as bsx
from tools.A00580_FacialBoardBuilder import bake as fbake
from tools.A00580_FacialBoardBuilder import migrate as fmig

EPS = 1e-4


class Checker(object):
    def __init__(self):
        self.n = 0
        self.fails = []

    def ok(self, cond, msg):
        self.n += 1
        if not cond:
            self.fails.append(msg)
            print("FAIL", msg)
        return bool(cond)


def _out_values(spec):
    out = spec["names"]["out_node"]
    return {a: cmds.getAttr("{0}.{1}".format(out, a)) for a in spec["arkit52"]}


def _nonzero(d):
    return {k: round(v, 4) for k, v in d.items() if abs(v) > EPS}


def _ctl_axis_values(spec):
    vals = {}
    for ctl in bsx.expand_controls(spec):
        for axis in ("tx", "ty"):
            plug = "{0}.{1}".format(ctl["name"], axis)
            if not cmds.getAttr(plug, lock=True):
                vals[plug] = cmds.getAttr(plug)
    return vals


def t1_structure(ck, spec, v04_alias=None, v04_attrs=None):
    names = spec["names"]
    ctls = bsx.expand_controls(spec)
    for ctl in ctls:
        ck.ok(cmds.objExists(ctl["name"]), "T1 control missing: " + ctl["name"])
        frm = "FRM_" + ctl["name"][5:]
        ck.ok(cmds.objExists(frm) and cmds.listRelatives(ctl["name"], parent=True)[0] == frm,
              "T1 {0} not under {1}".format(ctl["name"], frm))
    ck.ok(len(ctls) == 35, "T1 control count {0} != 35".format(len(ctls)))
    for n in (names["root_grp"], names["root_ctl"], names["frame_grp"], names["follow_grp"], names["csv_node"], names["out_node"]):
        ck.ok(cmds.objExists(n), "T1 node missing: " + n)
    for region in spec["regions"]:
        ck.ok(cmds.objExists("GRP_{0}GUI".format(region)), "T1 region group missing: " + region)
    ck.ok(cmds.nodeType(names["csv_node"]) == "blendShape", "T1 csv node is not a blendShape")
    # aliasAttr -q 의 순서는 저장 뒤 plug 문자열 순("weight[0]", "weight[10]" …)으로 바뀐다 - 순서가 아니라
    # 별칭 -> weight 인덱스 **대응**을 비교한다 (FileTool 도 별칭 이름으로만 찾는다).
    aliases = cmds.aliasAttr(names["csv_node"], q=True) or []
    alias_map = {aliases[i]: aliases[i + 1] for i in range(0, len(aliases), 2) if aliases[i + 1].startswith("weight")}
    expect = {a: "weight[{0}]".format(i) for i, a in enumerate(spec["csv_alias_order"])}
    ck.ok(alias_map == expect, "T1 csv alias->weight map differs from spec")
    if v04_alias is not None:
        ck.ok(alias_map == v04_alias, "T1 csv alias->weight map differs from V04")
    idx = cmds.getAttr(names["csv_node"] + ".weight", multiIndices=True) or []
    ck.ok(idx == list(range(52)), "T1 csv weight elements missing: {0}".format(sorted(set(range(52)) - set(idx))))
    for a in spec["arkit52"]:
        ck.ok(cmds.objExists("{0}.{1}".format(names["csv_node"], a)), "T1 csv alias plug missing: " + a)
    attrs = cmds.listAttr(names["out_node"], userDefined=True) or []
    ck.ok(attrs == spec["arkit52"], "T1 out attr order differs from spec")
    if v04_attrs is not None:
        ck.ok(attrs == v04_attrs, "T1 out attr order differs from V04")
    # 메시는 csv 더미를 살려 두는 숨김 평면 하나뿐
    meshes = [cmds.listRelatives(m, parent=True)[0] for m in cmds.ls(type="mesh", noIntermediate=True)]
    ck.ok(meshes == [names["csv_node"] + "_geo"], "T1 meshes {0} (expected only the csv plane)".format(meshes))
    ck.ok(not cmds.getAttr(names["csv_node"] + "_geo.v"), "T1 csv plane should be hidden")
    ck.ok(cmds.blendShape(names["csv_node"], q=True, geometry=True) == [names["csv_node"] + "_geoShape"],
          "T1 csv blendShape is not attached to its plane")
    # 명세 심김
    ck.ok(cmds.objExists("{0}.{1}".format(names["root_ctl"], names["spec_attr"])), "T1 boardSpec attr missing")
    emb = json.loads(cmds.getAttr("{0}.{1}".format(names["root_ctl"], names["spec_attr"])))
    ck.ok(emb["version"] == spec["version"] and len(emb["controls"]) == len(spec["controls"]), "T1 embedded spec differs")
    # 연결 없는 컨트롤
    for ctl in ctls:
        if ctl.get("unused"):
            outs = cmds.listConnections(ctl["name"], s=False, d=True, plugs=True) or []
            outs = [o for o in outs if "message" not in o and "dagSetMembers" not in o]
            ck.ok(not outs, "T1 unused control {0} has connections: {1}".format(ctl["name"], outs))
            ck.ok(cmds.objExists(ctl["name"] + ".notConnected"), "T1 unused control lacks notConnected flag")


def t2_limits(ck, spec):
    for ctl in bsx.expand_controls(spec):
        c = ctl["name"]
        lim = ctl.get("limits") or {}
        for axis, flag in (("tx", "etx"), ("ty", "ety")):
            lo, hi = lim.get(axis, [0, 0])
            en = cmds.transformLimits(c, q=True, **{flag: True})
            val = cmds.transformLimits(c, q=True, **{axis: True})
            ck.ok(all(en) and abs(val[0] - lo) < EPS and abs(val[1] - hi) < EPS,
                  "T2 {0}.{1} limits {2} != {3}".format(c, axis, val, [lo, hi]))
            locked = cmds.getAttr("{0}.{1}".format(c, axis), lock=True)
            ck.ok(locked == (lo == 0 and hi == 0), "T2 {0}.{1} lock state wrong".format(c, axis))
        for ch in ("tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"):
            ck.ok(cmds.getAttr("{0}.{1}".format(c, ch), lock=True), "T2 {0}.{1} not locked".format(c, ch))
        keyable = cmds.listAttr(c, keyable=True) or []
        ck.ok(set(keyable) <= {"translateX", "translateY"}, "T2 {0} keyable {1}".format(c, keyable))
        # 리밋이 setAttr 를 자른다
        for axis in ("tx", "ty"):
            lo, hi = lim.get(axis, [0, 0])
            if lo == 0 and hi == 0:
                continue
            plug = "{0}.{1}".format(c, axis)
            srcs = cmds.listConnections(plug, s=True, d=False, plugs=True) or []
            if srcs:
                continue
            cmds.setAttr(plug, hi + 5)
            ck.ok(abs(cmds.getAttr(plug) - hi) < EPS, "T2 {0} not clamped to max".format(plug))
            cmds.setAttr(plug, 0)


def _disconnect_all_backward(spec):
    from tools.A00580_FacialBoardBuilder import build as fb
    return fb.disconnect_backward(spec)


def t3_forward(ck, spec):
    """컨트롤 축 ±1 -> 그 attr 만 1. 뒤로 경로를 떼고 본다(연결된 플러그는 setAttr 불가)."""
    _disconnect_all_backward(spec)
    for ctl in bsx.expand_controls(spec):
        for axis, pairs in bsx.axis_map(ctl).items():
            plug = "{0}.{1}".format(ctl["name"], axis)
            for sign, attr in pairs:
                cmds.setAttr(plug, float(sign))
                nz = _nonzero(_out_values(spec))
                ck.ok(nz == {attr: 1.0}, "T3 {0}={1:+d} -> {2} (expected only {3}=1)".format(plug, sign, nz, attr))
                cmds.setAttr(plug, 0.0)
    # 중간값 선형
    ctl = "CTRL_C_jaw.ty"
    cmds.setAttr(ctl, -0.4)
    ck.ok(abs(_out_values(spec)["jawOpen"] - 0.4) < EPS, "T3 jawOpen linear mid value")
    cmds.setAttr(ctl, 0.0)
    for c in bsx.expand_controls(spec):
        if c.get("unused"):
            cmds.setAttr(c["name"] + ".ty", 1.0)
            ck.ok(not _nonzero(_out_values(spec)), "T3 unused control {0} changed an output".format(c["name"]))
            cmds.setAttr(c["name"] + ".ty", 0.0)


def t4_backward(ck, spec):
    """다시 걸고 : csv attr = 1 -> 그 컨트롤 축이 ±1, 다른 컨트롤 0. 왕복 Connect_01 == 1."""
    from tools.A00580_FacialBoardBuilder import build as fb
    fb.connect_backward(spec)
    csv = spec["names"]["csv_node"]
    mapping = bsx.attr_to_control(spec)
    for attr in spec["arkit52"]:
        cmds.setAttr("{0}.{1}".format(csv, attr), 1.0)
        moved = _nonzero(_ctl_axis_values(spec))
        ctl, axis, sign = mapping[attr]
        expect = {"{0}.{1}".format(ctl, axis): float(sign)}
        ck.ok(moved == expect, "T4 csv.{0}=1 moved {1} (expected {2})".format(attr, moved, expect))
        outs = _nonzero(_out_values(spec))
        ck.ok(outs == {attr: 1.0}, "T5 roundtrip csv.{0}=1 -> out {1}".format(attr, outs))
        cmds.setAttr("{0}.{1}".format(csv, attr), 0.0)
    ck.ok(not _nonzero(_ctl_axis_values(spec)), "T4 controls not back to zero")
    # ± 쌍 동시 0.5 -> 둘 다 0 (pma 가 뺀다)
    cmds.setAttr(csv + ".eyeBlinkLeft", 0.5)
    cmds.setAttr(csv + ".eyeWideLeft", 0.5)
    ck.ok(not _nonzero(_out_values(spec)), "T5 blink+wide both 0.5 should cancel to 0")
    cmds.setAttr(csv + ".eyeBlinkLeft", 0.0)
    cmds.setAttr(csv + ".eyeWideLeft", 0.0)
    # 범위 밖 입력은 리밋이 자른다
    cmds.setAttr(csv + ".jawOpen", 1.5)
    ck.ok(abs(cmds.getAttr("CTRL_C_jaw.ty") + 1.0) < EPS and abs(_out_values(spec)["jawOpen"] - 1.0) < EPS,
          "T5 csv.jawOpen 1.5 should be clamped by the limit")
    cmds.setAttr(csv + ".jawOpen", 0.0)


def t6_bake(ck, spec):
    """csv 에 키 -> bake -> 뒤로 연결 0, 프레임마다 out 값 동일 -> reconnect 복구."""
    csv = spec["names"]["csv_node"]
    frames = range(1, 25)
    keyed = {"jawOpen": lambda f: 0.5 + 0.5 * ((f % 8) / 8.0),
             "eyeBlinkLeft": lambda f: (f % 6) / 6.0, "eyeWideLeft": lambda f: 0.3 if f % 4 == 0 else 0.0,
             "mouthSmileLeft": lambda f: (f % 10) / 10.0, "browInnerUp": lambda f: 1.0 - (f % 12) / 12.0,
             "eyeLookInRight": lambda f: 0.8 if f % 3 == 0 else 0.1, "mouthLeft": lambda f: 0.2 * (f % 5),
             "mouthRight": lambda f: 0.1 * (f % 3)}
    for attr, fn in keyed.items():
        for f in frames:
            cmds.setKeyframe("{0}.{1}".format(csv, attr), time=f, value=fn(f))
    before = {}
    for f in frames:
        cmds.currentTime(f)
        before[f] = _out_values(spec)
    summary = fbake.bake_csv_to_ctl()
    ck.ok(not fbake.csv_connected(spec), "T6 backward still connected after bake")
    ck.ok(not cmds.ls("BWD_*"), "T6 BWD_ nodes left: {0}".format(cmds.ls("BWD_*")))
    ck.ok("CTRL_C_brow_raiseIn.ty" in summary["copied"], "T6 browInnerUp should be a copied curve")
    ck.ok("CTRL_L_eye_blinkWide.ty" in summary["computed"], "T6 blink/wide should be computed")
    bad = []
    for f in frames:
        cmds.currentTime(f)
        after = _out_values(spec)
        for a in spec["arkit52"]:
            if abs(after[a] - before[f][a]) > 1e-3:
                bad.append((f, a, round(before[f][a], 4), round(after[a], 4)))
    ck.ok(not bad, "T6 out values differ after bake: {0}".format(bad[:6]))
    # 복사된 커브는 키 수가 같다
    n_src = len(cmds.keyframe(csv + ".browInnerUp", q=True) or [])
    n_dst = len(cmds.keyframe("CTRL_C_brow_raiseIn.ty", q=True) or [])
    ck.ok(n_src == n_dst == len(frames), "T6 copied key count {0} vs {1}".format(n_src, n_dst))
    # 키 있는 축은 reconnect 가 건너뛴다, 키 지우면 다시 걸린다
    made, kept = fbake.reconnect_csv()
    ck.ok(len(kept) >= 6 and not fbake._curve_of("CTRL_L_brow_down.ty"), "T6 reconnect kept keyed axes")
    removed = fbake.clear_ctl_keys()
    made2, kept2 = fbake.reconnect_csv()
    ck.ok(removed >= 6 and not kept2 and fbake.csv_connected(spec), "T6 reconnect after clearing keys")
    # csv 키 정리
    for attr in keyed:
        crv = fbake._curve_of("{0}.{1}".format(csv, attr))
        if crv:
            cmds.delete(crv)
        cmds.setAttr("{0}.{1}".format(csv, attr), 0.0)
    cmds.currentTime(1)


def t7_mirror_follow(ck, spec):
    for ctl in spec["controls"]:
        if not ctl.get("mirror"):
            continue
        r = bsx.mirror_control(ctl)
        pl = cmds.getAttr("FRM_" + ctl["name"][5:] + ".t")[0]
        pr = cmds.getAttr("FRM_" + r["name"][5:] + ".t")[0]
        ck.ok(abs(pl[0] + pr[0]) < EPS and abs(pl[1] - pr[1]) < EPS, "T7 mirror position " + r["name"])
        sl = cmds.listRelatives(ctl["name"], s=True)[0]
        sr = cmds.listRelatives(r["name"], s=True)[0]
        cl = cmds.getAttr(sl + ".overrideColorRGB")[0]
        cr = cmds.getAttr(sr + ".overrideColorRGB")[0]
        if ctl.get("unused"):
            ck.ok(cl == cr, "T7 unused colors differ")
        else:
            ck.ok(cl != cr, "T7 L/R colors should differ: " + r["name"])
    # 따라가기 : Head=1 일 때 Head 로케이터를 옮기면 보드가 따라간다
    names = spec["names"]
    root = names["root_ctl"]
    base = cmds.xform(root, q=True, ws=True, t=True)
    cmds.setAttr("FOLLOW_Head_loc.tx", 10.0)
    moved = cmds.xform(root, q=True, ws=True, t=True)
    ck.ok(abs(moved[0] - base[0] - 10.0) < EPS, "T7 board does not follow Head locator")
    cmds.setAttr(root + ".Head", 0.0)
    cmds.setAttr(root + ".World", 1.0)
    world = cmds.xform(root, q=True, ws=True, t=True)
    ck.ok(abs(world[0] - base[0]) < EPS, "T7 World weight should ignore Head locator")
    cmds.setAttr(root + ".World", 0.0)
    cmds.setAttr(root + ".Head", 1.0)
    cmds.setAttr("FOLLOW_Head_loc.tx", 0.0)


def t7b_migrate(ck, spec, v04_path):
    """V04 에서 컨트롤에 키 → 이관표로 V05 에 옮겼을 때 Connect_01 52 값이 프레임마다 같은가."""
    with io.open(fmig.V04_TABLE, "r", encoding="utf-8") as fh:
        table = fmig.make_migrate_table(spec, json.load(fh))
    ck.ok(not table["conflicts"], "T7b migrate conflicts: {0}".format(table["conflicts"]))
    # V04 를 열어 모든 뒤로 입력을 떼고 각 V04 플러그에 키
    cmds.file(v04_path, open=True, force=True)
    v04_vals = {}
    plugs = sorted(table["per_plug"])
    # 한 V05 축으로 모이는 V04 플러그 묶음은 프레임마다 하나만 켠다 - 둘이 동시에 켜진 값은 V05 에 합으로만 남는다.
    group_pos = {}
    for v05, members in table["per_v05_plug"].items():
        for k, (v04, _m) in enumerate(members):
            group_pos[v04] = (k, len(members))
    # V04 단일 슬라이더는 clamp 가 없어 "반대쪽" 값이 음수 가중치가 됐다(의미 없는 쪽). 그쪽은 V05 에선 다른
    # 표현(blink 의 반대쪽 = wide)이 되므로 시험 키는 **의미 있는 쪽 부호만** 쓴다. 두 표현을 가진 축(jaw.tx 등)은 양쪽.
    plug_signs = {}
    for attr, info in table["per_attr"].items():
        plug_signs.setdefault(info["v04"]["plug"], set()).add(info["v04"]["sign"])
    for i, plug in enumerate(plugs):
        for src in cmds.listConnections(plug, s=True, d=False, plugs=True) or []:
            cmds.disconnectAttr(src, plug)
        k, n = group_pos[plug]
        signs = plug_signs[plug]
        for f in range(1, 6):
            v = ((f + i) % 5) / 4.0 * (1 if (f + i) % 2 else -1)
            if len(signs) == 1:
                v = abs(v) * list(signs)[0]
            if n > 1 and f % n != k:
                v = 0.0
            cmds.setKeyframe(plug, time=f, value=v)
    out = spec["names"]["out_node"]
    for f in range(1, 6):
        cmds.currentTime(f)
        v04_vals[f] = {a: cmds.getAttr("{0}.{1}".format(out, a)) for a in spec["arkit52"]}
    keys = {plug: [(t, cmds.getAttr(plug, time=t)) for t in range(1, 6)] for plug in plugs}
    return table, keys, v04_vals


def t7b_apply(ck, spec, table, keys, v04_vals):
    from tools.A00580_FacialBoardBuilder import build as fb
    fb.disconnect_backward(spec)
    # v05 = Σ v04_k × mult_k (묶음은 합) - 이관 도구가 할 일과 같은 계산
    for v05, members in table["per_v05_plug"].items():
        for t in range(1, 6):
            v = 0.0
            for v04, mult in members:
                v += dict(keys[v04])[t] * mult
            cmds.setKeyframe(v05, time=t, value=v)
    bad = []
    for f in range(1, 6):
        cmds.currentTime(f)
        after = _out_values(spec)
        for a in spec["arkit52"]:
            # V04 는 단일 슬라이더를 clamp 하지 않아 음수가 나올 수 있다 - V05 는 리밋으로 0 에 묶인다.
            exp = v04_vals[f][a]
            exp = min(max(exp, 0.0), 1.0)
            if abs(after[a] - exp) > 1e-3:
                bad.append((f, a, round(v04_vals[f][a], 3), round(after[a], 3)))
    ck.ok(not bad, "T7b migrated keys give different outputs: {0}".format(bad[:8]))
    fbake.clear_ctl_keys()
    fb.connect_backward(spec)


def t8_file_health(ck, label):
    ck.ok(not cmds.ls(type="unknown"), "T8 {0} has unknown nodes".format(label))
    ck.ok(not cmds.ls(type="renderLayer") or cmds.ls(type="renderLayer") == ["defaultRenderLayer"],
          "T8 {0} has extra render layers".format(label))
    ck.ok(cmds.fileInfo("jun_face_board", q=True), "T8 {0} fileInfo stamp missing".format(label))


def run(path, spec_path=None, v04_path=None):
    spec = bsx.load_spec(spec_path)
    ck = Checker()
    v04_alias = v04_attrs = None
    if v04_path and os.path.isfile(v04_path):
        cmds.file(v04_path, open=True, force=True)
        al = cmds.aliasAttr("BS_Face_CSV", q=True) or []
        v04_alias = {al[i]: al[i + 1] for i in range(0, len(al), 2) if al[i + 1].startswith("weight")}
        v04_attrs = cmds.listAttr("BS_Face_Connect_01", userDefined=True)
    base, ext = os.path.splitext(path)
    files = [base + ".ma"] + ([base + ".mb"] if os.path.isfile(base + ".mb") else [])
    for i, f in enumerate(files):
        cmds.file(f, open=True, force=True)
        label = os.path.basename(f)
        print("---", label)
        t1_structure(ck, spec, v04_alias, v04_attrs)
        t2_limits(ck, spec)
        t3_forward(ck, spec)
        t4_backward(ck, spec)
        if i == 0:
            t6_bake(ck, spec)
            t7_mirror_follow(ck, spec)
        t8_file_health(ck, label)
    if v04_path and os.path.isfile(v04_path):
        table, keys, v04_vals = t7b_migrate(ck, spec, v04_path)
        cmds.file(files[0], open=True, force=True)
        t7b_apply(ck, spec, table, keys, v04_vals)
    print("\n{0} checks, {1} failure(s)".format(ck.n, len(ck.fails)))
    for f in ck.fails:
        print("  -", f)
    return ck


def _main(argv):
    args = [a for a in argv if not a.startswith("--")]
    spec_path = argv[argv.index("--spec") + 1] if "--spec" in argv else None
    v04 = argv[argv.index("--v04") + 1] if "--v04" in argv else None
    args = [a for a in args if a not in (spec_path, v04)]
    if not args:
        print("usage: mayapy verify.py <board.ma> [--v04 <Ctl_Only_V04.mb>] [--spec spec.json]")
        return 2
    import maya.standalone
    maya.standalone.initialize(name="python")
    try:
        ck = run(args[0], spec_path, v04)
    finally:
        maya.standalone.uninitialize()
    return 1 if ck.fails else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
