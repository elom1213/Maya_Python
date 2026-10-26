# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00580_FacialBoardBuilder - V04 -> V05 이관표 (maya 비의존)
#
#   python migrate.py            # spec/v04_backward_table.json + 명세 -> spec/migrate_v04.json
#
# V04 표 (mayapy 실측 2026-10-26, M0-2) : attr -> (V04 컨트롤 플러그, 그 플러그가 1 일 때 attr 이 되는 부호)
# 명세 : attr -> (V05 컨트롤, 축, 부호)
# 이관 : v05_plug = v04_plug × multiplier,  multiplier = sign_v05 × sign_v04
# 같은 V04 플러그가 두 attr(± 쌍)을 맡으면 두 multiplier 가 같아야 커브를 그대로 옮길 수 있다 - 다르면 conflicts 에 적는다.
# 쓰는 곳 : A00110 Copy Key / A00145 Connect by Rule 로 옛 키 애니를 V05 로 옮길 때, 또는 verify T7.

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.abspath(os.path.join(HERE, "..", "..")) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from tools.A00580_FacialBoardBuilder import board_spec as bsx

V04_TABLE = os.path.join(bsx.SPEC_DIR, "v04_backward_table.json")
MIGRATE = os.path.join(bsx.SPEC_DIR, "migrate_v04.json")


def make_migrate_table(spec, v04_table):
    """-> {"per_attr": {attr: {...}}, "per_plug": {v04_plug: {"to": v05_plug, "multiplier": m}}, "conflicts": [...],
           "v04_unused_controls": [...]}"""
    mapping = bsx.attr_to_control(spec)
    per_attr = {}
    per_plug = {}
    conflicts = []
    for attr, (v04_plug, v04_sign) in v04_table.items():
        if attr not in mapping:
            conflicts.append("attr {0} not in spec".format(attr))
            continue
        ctl, axis, v05_sign = mapping[attr]
        v05_plug = "{0}.{1}".format(ctl, axis)
        mult = int(v05_sign) * int(v04_sign)
        per_attr[attr] = {"v04": {"plug": v04_plug, "sign": int(v04_sign)},
                          "v05": {"plug": v05_plug, "sign": int(v05_sign)}, "multiplier": mult}
        prev = per_plug.get(v04_plug)
        if prev and (prev["to"] != v05_plug or prev["multiplier"] != mult):
            conflicts.append("{0}: {1} -> {2} x{3} vs {4} x{5}".format(
                v04_plug, attr, v05_plug, mult, prev["to"], prev["multiplier"]))
        per_plug[v04_plug] = {"to": v05_plug, "multiplier": mult}
    # 한 V05 축으로 모이는 V04 플러그 묶음 (예: l_eyelid_Up.ty(blink) + l_eyeWide_Up.ty(wide) -> CTRL_L_eye_blinkWide.ty).
    # 옮길 때는 v05 = Σ v04_k × mult_k. 두 슬라이더가 같은 프레임에 함께 켜져 있던 애니는 합으로만 남는다.
    per_v05 = {}
    for v04_plug, info in per_plug.items():
        per_v05.setdefault(info["to"], []).append([v04_plug, info["multiplier"]])
    merged = {k: sorted(v) for k, v in per_v05.items() if len(v) > 1}
    return {"per_attr": per_attr, "per_plug": per_plug, "per_v05_plug": {k: sorted(v) for k, v in per_v05.items()},
            "merged_v05_plugs": merged, "conflicts": conflicts,
            "v04_unused_controls": ["BS_cheekLeft_innOut_ctl", "BS_cheekRight_innOut_ctl", "BS_eyebrowLeft_mid_ctl",
                                    "BS_eyebrowRight_mid_ctl", "BS_lipTop_frontBack_ctl", "BS_noseLeft_ctl", "BS_noseRight_ctl"]}


def main():
    spec = bsx.load_spec()
    with io.open(V04_TABLE, "r", encoding="utf-8") as fh:
        v04 = json.load(fh)
    table = make_migrate_table(spec, v04)
    table["_about"] = ("V04 Ctl_Only_V04 control plug -> V05 board plug. v05 = v04 * multiplier. "
                       "Built by migrate.py from v04_backward_table.json (mayapy measurement 2026-10-26) and the board spec.")
    with io.open(MIGRATE, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(table, indent=1, ensure_ascii=False))
        fh.write("\n")
    print("written", MIGRATE, "- attrs", len(table["per_attr"]), "plugs", len(table["per_plug"]),
          "conflicts", len(table["conflicts"]))
    for c in table["conflicts"]:
        print("  CONFLICT", c)
    return 1 if table["conflicts"] else 0


if __name__ == "__main__":
    sys.exit(main())
