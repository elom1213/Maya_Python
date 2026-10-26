# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00580_FacialBoardBuilder - 보드 명세(json) 읽기 · 좌우 전개 · 축/attr 해석 (maya 비의존)
#
# 명세 하나(spec/arkit52_board_v05.json)가 Maya 빌더 · 베이크 · 검증 · 미리보기 · (2단계) UE 빌더의
# 단일 소스다. 이 모듈은 json 을 읽어 "실제로 만들 컨트롤 목록" 으로 펼친다:
#   - "mirror": true 인 L 컨트롤은 R 컨트롤을 자동 생성 (x 반전 · Left->Right · tx 부호 거울)
#   - 축 키 "ty+" / "ty-" / "tx+" / "tx-" 를 (축, 부호, attr) 로 해석
# maya.cmds 를 import 하지 않으므로 시스템 python 으로도 돈다 (preview.py).

import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_DIR = os.path.join(HERE, "spec")
DEFAULT_SPEC = os.path.join(SPEC_DIR, "arkit52_board_v05.json")

AXES = ("tx", "ty")


def load_spec(path=None):
    """json -> dict. 경로가 없으면 기본 명세."""
    path = path or DEFAULT_SPEC
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def spec_to_json(spec):
    """씬에 심을 때 쓰는 직렬화 (들여쓰기 없이, 한글 유지)."""
    return json.dumps(spec, ensure_ascii=False, separators=(",", ":"))


def mirror_name(name):
    """CTRL_L_x -> CTRL_R_x. L/R 토큰이 없으면 그대로."""
    parts = name.split("_")
    out = []
    for p in parts:
        if p == "L":
            out.append("R")
        elif p == "R":
            out.append("L")
        else:
            out.append(p)
    return "_".join(out)


def mirror_attr(attr):
    """ARKit attr 이름의 Left <-> Right."""
    if attr.endswith("Left"):
        return attr[:-4] + "Right"
    if attr.endswith("Right"):
        return attr[:-5] + "Left"
    return attr


def mirror_control(ctl):
    """L 컨트롤 dict -> R 컨트롤 dict.

    - x 를 반전한다.
    - 이름 · attr 의 Left/Right 를 바꾼다.
    - tx 의 + 와 - 를 **바꾼다**: L 패드에서 +tx(보드 오른쪽 = 캐릭터 왼쪽 바깥) 가 Out 이면
      R 패드에서는 Out 이 -tx(보드 왼쪽) 가 되어야 "바깥쪽으로 끌면 Out" 이 양쪽에서 같다.
    - 색 L -> R (unused 는 그대로).
    """
    out = dict(ctl)
    out["name"] = mirror_name(ctl["name"])
    out["pos"] = [-ctl["pos"][0], ctl["pos"][1]]
    out["mirror"] = False
    out["mirror_of"] = ctl["name"]
    axes = {}
    for key, attr in (ctl.get("axes") or {}).items():
        if key.startswith("tx"):
            key = "tx-" if key.endswith("+") else "tx+"
        axes[key] = mirror_attr(attr)
    out["axes"] = axes
    if ctl.get("color") == "L":
        out["color"] = "R"
    return out


def expand_controls(spec):
    """명세의 controls 를 실제 컨트롤 목록으로 펼친다 (L 뒤에 바로 그 R)."""
    out = []
    for ctl in spec["controls"]:
        out.append(ctl)
        if ctl.get("mirror"):
            out.append(mirror_control(ctl))
    return out


def axis_entries(ctl):
    """컨트롤의 axes -> [(axis, sign, attr), ...]  sign 은 +1 / -1."""
    entries = []
    for key, attr in (ctl.get("axes") or {}).items():
        axis, sign = key[:2], (1 if key.endswith("+") else -1)
        if axis not in AXES:
            raise ValueError("bad axis key {0!r} on {1}".format(key, ctl["name"]))
        entries.append((axis, sign, attr))
    return entries


def axis_map(ctl):
    """{axis: [(sign, attr), ...]} - 한 축에 표현이 1개(0~1) 또는 2개(±)."""
    out = {}
    for axis, sign, attr in axis_entries(ctl):
        out.setdefault(axis, []).append((sign, attr))
    return out


def attr_to_control(spec):
    """{attr: (control name, axis, sign)} - 52 attr 전부가 정확히 한 번 나와야 한다."""
    out = {}
    for ctl in expand_controls(spec):
        for axis, sign, attr in axis_entries(ctl):
            if attr in out:
                raise ValueError("attr {0} mapped twice: {1} and {2}".format(attr, out[attr][0], ctl["name"]))
            out[attr] = (ctl["name"], axis, sign)
    return out


def check_spec(spec):
    """명세 자체의 정합성. 문제 목록을 돌려준다(비면 OK)."""
    problems = []
    arkit = list(spec["arkit52"])
    if len(arkit) != 52 or len(set(arkit)) != 52:
        problems.append("arkit52 must list 52 unique names")
    alias = list(spec["csv_alias_order"])
    if sorted(alias) != sorted(arkit):
        problems.append("csv_alias_order must be a permutation of arkit52")
    try:
        mapping = attr_to_control(spec)
    except ValueError as e:
        problems.append(str(e))
        mapping = {}
    missing = [a for a in arkit if a not in mapping]
    extra = [a for a in mapping if a not in arkit]
    if missing:
        problems.append("attrs without control: {0}".format(", ".join(missing)))
    if extra:
        problems.append("controls drive unknown attrs: {0}".format(", ".join(extra)))
    names = [c["name"] for c in expand_controls(spec)]
    dups = sorted(set(n for n in names if names.count(n) > 1))
    if dups:
        problems.append("duplicate control names: {0}".format(", ".join(dups)))
    for ctl in expand_controls(spec):
        lim = ctl.get("limits") or {}
        for axis, sign, attr in axis_entries(ctl):
            lo, hi = lim.get(axis, [0, 0])
            if sign > 0 and hi <= 0:
                problems.append("{0}: {1}+ -> {2} but limit max is {3}".format(ctl["name"], axis, attr, hi))
            if sign < 0 and lo >= 0:
                problems.append("{0}: {1}- -> {2} but limit min is {3}".format(ctl["name"], axis, attr, lo))
    return problems
