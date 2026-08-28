# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00130_ControlRig_V02 - Length : 템플릿 조인트 사이 거리를 옵션 컨트롤러에 써 넣는다.
#
# 계획서: docs/plans/A00130_ControlRig_V02_length_plan.md
#
# ── V01 과 무엇이 다른가 ────────────────────────────────────────────────────
#
# V01(`rig_matcher.py:255` 외 3곳)은 **아바타 본**을 쟀고, 그 본은 사용자가 TSL 에
# **손으로 순서대로 담은 것**이었다. 여기서는 **템플릿 조인트**를 재고 짝은 json 이 갖는다.
# 값은 같지만 **아바타의 조인트 이름에 의존하지 않게 된다.**
#
# 또 V01 은 부위 매칭 함수 안에서 `setAttr` 을 바로 불렀다. 없는 어트리뷰트에 쓰면
# `RuntimeError` 가 나는데 그 자리를 **감싸지 않아서** 예외가 `on_match` 밖으로 올라가
# **Match 전체가 멈췄다**(실측, 계획서 3-2). 여기서는 쓰기 전에 다 보고 **건너뛰고 계속**한다.
#
# ── 쓰기 전에 보는 것 (전부 실측으로 확인) ──────────────────────────────────
#
#   없는 어트리뷰트  RuntimeError: setAttr: No object matches name: opt.Arm_r
#   범위 밖          RuntimeError: ... past its maximum value of 10   ← 자르지 않는다
#   잠김/연결        RuntimeError: ... is locked or connected and cannot be set
#
# 범위를 넘으면 **잘라서 쓰지 않고 거부**한다 — 잘린 길이는 틀린 리그를 조용히 만든다.

import math

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import mapping_data
from . import scene_utils as su


#: 결과 코드
ST_OK = "ok"
ST_NO_JOINT = "joint missing"
ST_NO_ATTR = "attr missing"
ST_BLOCKED = "blocked"
ST_RANGE = "out of range"
ST_ERROR = "error"

#: 직선 거리와 마디 합이 이보다 더 벌어지면 "굽었다" 고 알린다 (비율)
BEND_TOLERANCE = 0.005          # 0.5 %


# =========================
# 재기
# =========================

def distance(a, b):
    """두 노드의 월드 위치 사이 거리.

    `xform -ws -t` 는 **씬의 선형 단위**를 탄다(실측: 같은 두 점이 cm 10 / m 0.1 / mm 100).
    툴은 단위를 바꾸지 않고 `linear_unit()` 으로 **무슨 단위였는지 알린다**.
    """
    p = cmds.xform(a, query=True, worldSpace=True, translation=True)
    q = cmds.xform(b, query=True, worldSpace=True, translation=True)
    return math.sqrt((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2)


def linear_unit():
    """씬의 현재 선형 단위 (`cm` · `m` · `mm` ...)."""
    try:
        return cmds.currentUnit(query=True, linear=True)
    except Exception:
        return "?"


def chain_lengths(nodes):
    """`(segments, straight)`.

    - `segments` : 이웃한 두 노드 사이 거리 목록 (마디 길이)
    - `straight` : **처음 -> 마지막 직선 거리**

    ★ 이 둘은 같지 않다. 체인이 굽어 있으면 `straight < sum(segments)` 다
      (실측: 30° 굽으면 3.4 % 짧다). 어느 쪽을 `total` 로 쓸지는 `total_mode` 가 정한다.
    """
    segments = [distance(nodes[i], nodes[i + 1]) for i in range(len(nodes) - 1)]
    straight = distance(nodes[0], nodes[-1])
    return segments, straight


# =========================
# 옵션 컨트롤러 찾기
# =========================

def token_search(name, namespace=None):
    """이름을 **부분 문자열**로 갖는 transform 을 찾는다. 후보 목록(우선순위 순).

    V01 은 옵션 컨트롤러를 `"OptionAll_xx_ctl" in obj` 로 찾았다 — **토큰**이지 전체
    이름이 아니었다(실제 이름은 `CH_n_OptionAll_xx_ctl`). 그래서 정확한 이름으로 못 찾으면
    여기로 온다.

    ── 실측한 함정 둘 (2026-08-28) ─────────────────────────────────────────
    1. **`ls("*tok*")` 는 네임스페이스를 넘지 않는다.** 루트만 본다 —
       노드가 `CAGE:CH_n_OptionAll_xx_ctl` 이면 **빈 목록**이 온다.
       → `recursive=True` 라야 네임스페이스 안까지 본다.
    2. **셰이프까지 잡힌다.** 컨트롤러는 nurbsCurve 라 `...ctlShape` 가 따라오고,
       그러면 후보가 2개로 보여 **"여럿이면 멈춘다" 규칙에 잘못 걸린다.**
       → `type="transform"`.

    이 둘이 겹쳐서 레퍼런스한 케이지에서 컨트롤러를 못 찾았다.
    """
    if not name:
        return []
    try:
        found = cmds.ls("*" + name + "*", recursive=True, type="transform") or []
    except Exception:
        return []

    found = sorted(set(found))
    if not namespace or namespace == su.NO_NAMESPACE:
        return found

    # 고른 네임스페이스 안의 것을 앞으로 (su.resolve 와 같은 우선순위)
    prefix = namespace.rstrip(":") + ":"
    inside = [n for n in found if n.startswith(prefix)]
    return inside + [n for n in found if n not in inside]


def find_option_ctl(name, namespace, override=None):
    """옵션 컨트롤러를 찾는다. `(노드 또는 None, messages, how)`.

    `how` 는 `"manual"` · `"exact"` · `"token"` · `None`.

    1. **`override`** — UI 에서 손으로 지정한 것. 있으면 **그것이 이긴다**(존재만 확인).
    2. `su.resolve()` — 고른 네임스페이스를 붙인 쪽 먼저, 없으면 이름 그대로.
       **케이지를 레퍼런스하면 `CAGE:CH_n_OptionAll_xx_ctl` 이 된다.**
    3. `token_search()` — 이름을 부분 문자열로 갖는 transform.
       - 하나면 쓰되 **토큰으로 찾았다고 알린다**
       - **여럿이면 고르지 않는다.** 후보를 보여 주고 **`Get Selected` 로 지정하라**고 한다.
         V01 은 `rnm_optionCtl[0]` 으로 첫 개를 골랐다 — 남의 노드에 조용히 쓰는 게 최악이다.
    """
    messages = []

    if override:
        if cmds.objExists(override):
            return override, messages, "manual"
        messages.append(
            "[Warning] The option controller was set to '{0}' by hand but that node "
            "is gone - looking it up again.".format(override))

    if not name:
        messages.append("[ERR] No option controller name in the length file.")
        return None, messages, None

    node, found = su.resolve(name, namespace)
    if node:
        if len(found) > 1:
            messages.append(
                "[Warning] Ambiguous option controller - using {0} (also found {1}).".format(
                    node, ", ".join(found[1:])))
        return node, messages, "exact"

    loose = token_search(name, namespace)

    if len(loose) == 1:
        messages.append(
            "[Warning] No node is called exactly '{0}' - using '{1}', matched by "
            "name. Use Get Selected if that is the wrong node.".format(name, loose[0]))
        return loose[0], messages, "token"

    if len(loose) > 1:
        messages.append(
            "[ERR] '{0}' matches {1} nodes - refusing to guess. Pick one and press "
            "Get Selected: {2}".format(name, len(loose), ", ".join(loose[:8])))
        return None, messages, None

    messages.append(
        "[ERR] Option controller not found. Looked for {0}, then for any transform "
        "whose name contains '{1}'. Select it and press Get Selected.".format(
            " and ".join(su.candidates(name, namespace)), name))
    return None, messages, None


def selected_option_ctl():
    """선택에서 옵션 컨트롤러 하나를 집는다. `(노드 또는 None, message)`.

    셰이프를 골랐어도 트랜스폼으로 올려 준다 — 컨트롤러는 커브라 셰이프가 잡히기 쉽다.
    """
    selection = cmds.ls(selection=True, long=False) or []
    if not selection:
        return None, "[Warning] Nothing is selected."

    node = selection[0]
    if cmds.objectType(node, isAType="shape"):
        parents = cmds.listRelatives(node, parent=True, fullPath=False) or []
        if parents:
            node = parents[0]

    if not cmds.objExists(node):
        return None, "[Warning] '{0}' does not exist.".format(node)

    extra = ""
    if len(selection) > 1:
        extra = " ({0} were selected - used the first)".format(len(selection))
    return node, "[OK] Option controller set to '{0}'{1}.".format(node, extra)


# =========================
# 계획 (씬을 바꾸지 않는다)
# =========================

def _attr_status(plug, value):
    """이 플러그에 `value` 를 쓸 수 있나. `(status, note)`.

    쓰기 전에 **전부 미리 본다** — `setAttr` 을 던지고 예외를 받는 것보다,
    무엇이 왜 안 되는지 표에 보여 주는 편이 낫다.
    """
    if not cmds.objExists(plug):
        return ST_NO_ATTR, "no attribute '{0}'".format(plug.split(".")[-1])

    if not su.plug_writable(plug):
        return ST_BLOCKED, "locked or connected"

    node, attr = plug.split(".", 1)
    try:
        if cmds.attributeQuery(attr, node=node, minExists=True):
            low = cmds.attributeQuery(attr, node=node, minimum=True)[0]
            if value < low:
                return ST_RANGE, "{0:.4g} is below the minimum {1:.4g}".format(value, low)
        if cmds.attributeQuery(attr, node=node, maxExists=True):
            high = cmds.attributeQuery(attr, node=node, maximum=True)[0]
            if value > high:
                return ST_RANGE, "{0:.4g} is past the maximum {1:.4g}".format(value, high)
    except Exception:
        pass        # 범위 조회가 안 되는 타입이면 그냥 넘어간다

    return ST_OK, ""


def plan(doc, namespace, total_mode=None, option_ctl_node=None, override=None):
    """무엇을 어디에 얼마로 쓸지 계산한다. 씬은 **바꾸지 않는다**.

    `(rows, messages)` — 각 행은
        part · chain · values{role: 값} · attrs{role: 이름} · plugs{role: 플러그} ·
        status · note · bent
    """
    messages = []
    rows = []

    mode = total_mode or doc.get("total_mode") or mapping_data.TOTAL_STRAIGHT

    ctl = option_ctl_node
    if ctl is None:
        ctl, ctl_msgs, _how = find_option_ctl(
            doc.get("option_ctl"), namespace, override)
        messages.extend(ctl_msgs)

    for measure in (doc.get("measures") or []):
        row = {
            "part": measure["part"],
            "chain": list(measure["chain"]),
            "resolved": [],
            "values": {},
            "attrs": dict(measure["attrs"]),
            "plugs": {},
            "status": ST_OK,
            "note": "",
            "bent": 0.0,
        }

        # --- 조인트를 푼다 (Match 와 같은 이름 해석) ---
        nodes, missing = [], []
        for jname in measure["chain"]:
            node, _found = su.resolve(jname, namespace)
            if node:
                nodes.append(node)
            else:
                missing.append(jname)

        if missing:
            row["status"] = ST_NO_JOINT
            row["note"] = "missing " + ", ".join(missing)
            rows.append(row)
            continue

        row["resolved"] = nodes

        # --- 잰다 ---
        segments, straight = chain_lengths(nodes)
        total_sum = sum(segments)
        row["values"]["total"] = (
            straight if mode == mapping_data.TOTAL_STRAIGHT else total_sum)
        if len(nodes) == 3:
            row["values"]["upper"] = segments[0]
            row["values"]["lower"] = segments[1]

        # 직선과 합이 벌어지면 알린다 — 어느 쪽을 쓸지는 사용자가 정한다 (계획서 3-1)
        if total_sum > 1e-9:
            row["bent"] = (total_sum - straight) / total_sum
            if row["bent"] > BEND_TOLERANCE:
                row["note"] = "bent - straight {0:.4g} vs sum {1:.4g}".format(
                    straight, total_sum)

        # --- 쓸 수 있는지 본다 ---
        if not ctl:
            row["status"] = ST_ERROR
            row["note"] = "no option controller"
            rows.append(row)
            continue

        worst = ST_OK
        notes = []
        for role, attr in row["attrs"].items():
            if role not in row["values"]:
                continue
            plug = "{0}.{1}".format(ctl, attr)
            row["plugs"][role] = plug
            status, note = _attr_status(plug, row["values"][role])
            if status != ST_OK:
                worst = status
                notes.append("{0}: {1}".format(attr, note))

        if notes:
            row["status"] = worst
            row["note"] = ("; ".join(notes) if not row["note"]
                           else row["note"] + " | " + "; ".join(notes))

        rows.append(row)

    # 조인트를 아직 안 놓았을 때 (계획서 4-6)
    measured = [r for r in rows if r["values"]]
    if measured and all(
            all(v < 1e-6 for v in r["values"].values()) for r in measured):
        messages.append(
            "[Warning] Every length is 0 - the template joints look like they are "
            "still at the origin. Place them first.")

    return rows, messages


# =========================
# 쓰기
# =========================

def apply(rows):
    """계산된 값을 실제로 쓴다. `(results, messages)`. 전체가 **undo 한 스텝**."""
    messages = []
    results = {"written": 0, "skipped": 0, "parts": 0}

    with undo_chunk():
        for row in rows:
            if row["status"] == ST_NO_JOINT:
                results["skipped"] += len(row["attrs"])
                messages.append("[Warning] {0}: {1} - skipped.".format(
                    row["part"], row["note"]))
                continue

            wrote = 0
            for role, plug in row["plugs"].items():
                value = row["values"][role]
                status, note = _attr_status(plug, value)
                if status != ST_OK:
                    results["skipped"] += 1
                    messages.append("[Warning] {0}: {1} - {2}.".format(
                        row["part"], plug.split(".")[-1], note))
                    continue
                try:
                    cmds.setAttr(plug, value)
                except Exception as e:
                    results["skipped"] += 1
                    messages.append("[ERR] {0}: {1} - {2}".format(
                        row["part"], plug.split(".")[-1], e))
                    continue
                results["written"] += 1
                wrote += 1

            # attrs 는 있는데 values 가 없어 아예 시도조차 못한 것
            not_tried = len(row["attrs"]) - len(row["plugs"])
            if not_tried > 0:
                results["skipped"] += not_tried

            if wrote:
                results["parts"] += 1
                messages.append("[OK] {0}: {1}.".format(
                    row["part"],
                    ", ".join("{0} = {1:.4f}".format(row["attrs"][r], row["values"][r])
                              for r in sorted(row["plugs"]) if r in row["values"])))

    messages.append(
        "[OK] Length done - {0} attribute(s) on {1} part(s), {2} skipped. "
        "Measured in {3}.".format(
            results["written"], results["parts"], results["skipped"], linear_unit()))
    return results, messages


def summarize(rows):
    """상태별 개수 (UI 요약용)."""
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


def attribute_count(rows):
    """`(쓸 수 있는 개수, 데이터가 요구하는 개수)` — 12개가 다 써지는지 세는 데 쓴다."""
    wanted = sum(len(r["attrs"]) for r in rows)
    ready = sum(1 for r in rows if r["status"] == ST_OK for _ in r["plugs"])
    return ready, wanted
