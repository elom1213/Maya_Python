# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00130_ControlRig_V02 - 템플릿 조인트 <-> 케이지 세트 매핑 데이터.
#
# 계획서 7-10 의 스키마. 초판은 `.ref/ref_01.txt` 에서 뽑았다.
#
# ── 왜 `조인트 -> 세트 목록` 인가 ────────────────────────────────────────────
#
# 원본 표에서 한 조인트가 세트 둘을 갖는 모양이 **두 가지**로 들어 있었다.
#
#     helper_foot_l : B01_Leg_L_03, B01_Leg_L_ik_01_foot    <- 한 줄에 둘
#     helper_ball_l : B01_Leg_L_04                           <- 줄이 둘로 나뉘어 있다
#     helper_ball_l : B01_Leg_L_ik_07_Ball
#
# `{조인트: 세트}` 로 만들면 **`helper_ball_l/r` 의 한쪽이 조용히 사라진다.**
# 그래서 값은 언제나 목록이고, 로드할 때 같은 이름이 또 나오면 합친다.

import json
import os


#: 매칭 모드 기본값 — 위치 + 회전
DEFAULT_MATCH = ("t", "r")

#: 이 폴더 아래 버전 폴더가 들어간다 (app/data/mapping/<version>/template_map.json)
MAPPING_DIRNAME = os.path.join("data", "mapping")
MAPPING_FILENAME = "template_map.json"
LENGTH_FILENAME = "length_map.json"
ORIENT_FILENAME = "orient_map.json"
PAIR_FILENAME = "pair_map.json"
CONSTRAIN_FILENAME = "constrain_map.json"
IK_AXIS_FILENAME = "ik_axis_map.json"

#: `total` 을 어떻게 잴지 (계획서 3-1)
TOTAL_STRAIGHT = "straight"   # 첫 조인트 -> 마지막 조인트 직선 거리 (V01 과 동일)
TOTAL_SUM = "sum"             # 마디 길이의 합 (완전히 폈을 때)
TOTAL_MODES = (TOTAL_STRAIGHT, TOTAL_SUM)


def _app_dir():
    # .../app/core/mapping_data.py -> .../app
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mapping_root():
    return os.path.join(_app_dir(), MAPPING_DIRNAME)


def list_versions():
    """`app/data/mapping/` 아래 버전 폴더 이름들. 최신이 뒤."""
    root = mapping_root()
    if not os.path.isdir(root):
        return []
    out = []
    for name in sorted(os.listdir(root)):
        if os.path.isfile(os.path.join(root, name, MAPPING_FILENAME)):
            out.append(name)
    return out


def default_version():
    versions = list_versions()
    return versions[-1] if versions else None


def mapping_path(version=None):
    version = version or default_version()
    if not version:
        return None
    return os.path.join(mapping_root(), version, MAPPING_FILENAME)


def _version_path(version, filename):
    version = version or default_version()
    if not version:
        return None
    return os.path.join(mapping_root(), version, filename)


def pair_path(version=None):
    return _version_path(version, PAIR_FILENAME)


def constrain_path(version=None):
    return _version_path(version, CONSTRAIN_FILENAME)


def ik_axis_path(version=None):
    return _version_path(version, IK_AXIS_FILENAME)


def _read_json(path, label, messages):
    if not path or not os.path.isfile(path):
        messages.append("[ERR] {0} file not found: {1}".format(label, path))
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messages.append("[ERR] Could not read {0} ({1}).".format(path, e))
        return None


def load_pairs(version=None):
    """`pair_map.json` -> `(doc, messages)`.

    `doc["pairs"]` 는 `{"from": A, "to": B}` 목록. **같은 세트가 두 번 나오면 알린다** —
    한 세트를 두 짝이 서로 다른 곳으로 옮기려 들면 뒤에 오는 것이 이긴다.
    """
    messages = []
    empty = {"match": ["t", "r"], "pairs": []}
    doc = _read_json(pair_path(version), "Pair", messages)
    if doc is None:
        return empty, messages

    pairs = [p for p in (doc.get("pairs") or [])
             if p.get("from") and p.get("to")]
    dropped = len(doc.get("pairs") or []) - len(pairs)
    if dropped:
        messages.append("[Warning] {0} pair(s) have no 'from'/'to' - skipped.".format(
            dropped))

    for key in ("from", "to"):
        seen = {}
        for p in pairs:
            seen.setdefault(p[key], 0)
            seen[p[key]] += 1
        dup = sorted(n for n, c in seen.items() if c > 1)
        if dup:
            messages.append("[Warning] '{0}' set(s) used more than once: {1}".format(
                key, ", ".join(dup)))

    messages.append("[OK] Loaded {0} pair(s).".format(len(pairs)))
    return {"match": doc.get("match") or ["t", "r"], "pairs": pairs}, messages


def load_ik_axis(version=None):
    """`ik_axis_map.json` -> `(doc, messages)`.

    `doc["sets"]` 는 `{"set": 이름, "axis": "+Z"}` 목록. **목록인 이유는 세트가 늘어날
    수 있어서**다 — 지금은 하나뿐이지만 코드는 개수를 모른다.
    """
    messages = []
    empty = {"sets": []}
    doc = _read_json(ik_axis_path(version), "IK axis", messages)
    if doc is None:
        return empty, messages

    sets = []
    for e in (doc.get("sets") or []):
        name, axis = e.get("set"), (e.get("axis") or "").strip()
        if not name:
            messages.append("[Warning] an ik-axis rule has no 'set' - skipped.")
            continue
        if not axis or axis[-1].upper() not in ("X", "Y", "Z"):
            messages.append("[Warning] {0}: '{1}' is not an axis - skipped.".format(
                name, axis))
            continue
        sets.append({"set": name, "axis": axis})

    if sets:
        messages.append("[OK] Loaded {0} ik-axis rule(s): {1}.".format(
            len(sets), ", ".join("{0} -> {1}".format(e["set"], e["axis"])
                                 for e in sets)))
    return {"sets": sets}, messages


def load_constrain(version=None):
    """`constrain_map.json` -> `(doc, messages)`."""
    messages = []
    empty = {"set": "", "attribute": "Con", "maintain_offset": False}
    doc = _read_json(constrain_path(version), "Constrain", messages)
    if doc is None:
        return empty, messages

    if not doc.get("set"):
        messages.append("[ERR] 'set' is missing - there are no pose objects to read.")
    messages.append("[OK] Loaded constrain rule - set '{0}', attribute '{1}', "
                    "maintain offset {2}.".format(
                        doc.get("set"), doc.get("attribute") or "Con",
                        "on" if doc.get("maintain_offset") else "off"))
    return {"set": doc.get("set") or "",
            "attribute": doc.get("attribute") or "Con",
            "maintain_offset": bool(doc.get("maintain_offset", False))}, messages


def orient_path(version=None):
    version = version or default_version()
    if not version:
        return None
    return os.path.join(mapping_root(), version, ORIENT_FILENAME)


def length_path(version=None):
    version = version or default_version()
    if not version:
        return None
    return os.path.join(mapping_root(), version, LENGTH_FILENAME)


# =========================
# 로드
# =========================

def load_orient(version=None, joints=None):
    """`orient_map.json` 을 읽어 `(doc, messages)`.

    `joints`(template_map 로드 결과)를 주면 **규칙에 적힌 조인트 이름이 거기 있는지**
    검사하고, `doc["_all_joints"]` 에 전체 목록을 실어 준다 —
    `orient_manager.plan()` 이 **규칙이 없는 조인트를 세는 데** 쓴다(계획서 3장).
    """
    messages = []
    empty = {"world_zero_default": True, "aim_groups": [], "pole_chains": [],
             "mirror": {}, "_all_joints": []}
    path = orient_path(version)

    if not path or not os.path.isfile(path):
        messages.append("[ERR] Orient file not found: {0}".format(path))
        return empty, messages

    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        messages.append("[ERR] Could not read {0} ({1}).".format(path, e))
        return empty, messages

    known = {j["name"] for j in (joints or [])}
    doc["_all_joints"] = [j["name"] for j in (joints or [])]

    named = []
    for group in (doc.get("aim_groups") or []):
        named.extend(group.get("joints") or [])
    for chain in (doc.get("pole_chains") or []):
        named.extend(chain.get("joints") or [])
        if chain.get("pole"):
            named.append(chain["pole"])
        tail = chain.get("tail")
        if isinstance(tail, dict):
            named.extend(tail.get("joints") or [])
            # tail 은 반드시 체인의 끝 조인트에서 시작해야 한다 (계획서 5-1)
            if (tail.get("joints") or [None])[0] != (chain.get("joints") or [None])[-1]:
                messages.append(
                    "[Warning] {0}: the tail should start at the last chain joint "
                    "({1}) but starts at {2}.".format(
                        chain.get("name"), (chain.get("joints") or [""])[-1],
                        (tail.get("joints") or [""])[0]))
    mirror = doc.get("mirror") or {}
    for key in ("behavior", "position_pairs", "position_only"):
        for entry in (mirror.get(key) or []):
            named.extend([entry.get("source"), entry.get("target")])

    if known:
        unknown = sorted({n for n in named if n and n not in known})
        if unknown:
            messages.append("[Warning] not in template_map.json: {0}".format(
                ", ".join(unknown)))

    preserve = sum(1 for c in (doc.get("pole_chains") or [])
                   if c.get("tail") == "preserve")
    messages.append(
        "[OK] Loaded orient rules - {0} aim group(s), {1} pole chain(s) "
        "({2} preserve), {3} mirror entry set(s).".format(
            len(doc.get("aim_groups") or []), len(doc.get("pole_chains") or []),
            preserve, len([k for k in ("behavior", "position_pairs", "position_only")
                           if mirror.get(k)])))
    return doc, messages


def load_ik_set(version=None):
    """`template_map.json` 의 `ik_handle_set` — ikHandle 을 모아 둔 케이지 세트 이름.

    없으면 `None`. 그러면 Match 는 **IK 세션 없이** 돈다(예전과 같은 동작).
    """
    path = mapping_path(version)
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception:
        return None
    return doc.get("ik_handle_set") or None


def load(version=None):
    """매핑 파일을 읽어 `(joints, messages)` 로 돌려준다.

    `joints` 는 dict 목록 — `name` · `parent` · `targets`(`set` / `match`).
    **파일이 잘못돼 있으면 예외를 던지지 않고 messages 로 알린다** — 툴이 안 뜨는 것보다
    "무엇이 잘못됐는지" 를 보여 주는 편이 낫다.
    """
    messages = []
    path = mapping_path(version)

    if not path or not os.path.isfile(path):
        messages.append("[ERR] Mapping file not found: {0}".format(path))
        return [], messages

    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        messages.append("[ERR] Could not read {0} ({1}).".format(path, e))
        return [], messages

    raw = doc.get("joints") or []
    merged = []
    index = {}

    for item in raw:
        name = (item or {}).get("name")
        if not name:
            messages.append("[Warning] An entry has no 'name' - skipped.")
            continue

        targets = []
        for t in (item.get("targets") or []):
            set_name = (t or {}).get("set")
            if not set_name:
                messages.append(
                    "[Warning] {0}: a target has no 'set' - skipped.".format(name))
                continue
            match = tuple(t.get("match") or DEFAULT_MATCH)
            bad = [m for m in match if m not in ("t", "r")]
            if bad:
                messages.append(
                    "[Warning] {0} -> {1}: unknown match flag(s) {2} - using {3}.".format(
                        name, set_name, bad, list(DEFAULT_MATCH)))
                match = DEFAULT_MATCH
            targets.append({"set": set_name, "match": match})

        if name in index:
            # 같은 조인트가 또 나오면 합친다 (위 주석 참고)
            entry = index[name]
            known = {t["set"] for t in entry["targets"]}
            for t in targets:
                if t["set"] not in known:
                    entry["targets"].append(t)
            messages.append(
                "[Info] {0} appears more than once - targets were merged.".format(name))
            continue

        entry = {
            "name": name,
            "parent": item.get("parent"),
            "targets": targets,
            # 나중 단계용으로 자리만 남긴다. 지금은 아무도 읽지 않는다.
            "orient": item.get("orient"),
        }
        index[name] = entry
        merged.append(entry)

    messages.append("[OK] Loaded {0} joint(s) from {1}.".format(
        len(merged), os.path.basename(os.path.dirname(path))))
    return merged, messages


# =========================
# 파일만 보고 할 수 있는 점검 (씬 없이)
# =========================

def check(joints):
    """씬을 보지 않고 데이터 자체만 점검한다. 문제 메시지 목록."""
    messages = []
    names = {j["name"] for j in joints}

    roots = [j["name"] for j in joints if not j["parent"]]
    if len(roots) != 1:
        messages.append("[Warning] Expected exactly one root, found {0}: {1}".format(
            len(roots), roots))

    for j in joints:
        parent = j["parent"]
        if parent and parent not in names:
            messages.append("[Warning] {0}: parent '{1}' is not in the file.".format(
                j["name"], parent))

    used = {}
    for j in joints:
        for t in j["targets"]:
            used.setdefault(t["set"], []).append(j["name"])
    for set_name, owners in used.items():
        if len(owners) > 1:
            messages.append("[Warning] set '{0}' is claimed by {1}.".format(
                set_name, owners))

    no_target = [j["name"] for j in joints if not j["targets"]]
    if no_target:
        # 정상이다 — 배치·계층용 조인트. 문제로 보지 않고 알려만 준다.
        messages.append("[Info] {0} joint(s) have no target set (structure only).".format(
            len(no_target)))

    return messages


# =========================
# 길이 수치 (계획서: A00130_ControlRig_V02_length_plan.md)
# =========================

def load_length(version=None, joints=None):
    """`length_map.json` 을 읽어 `(doc, messages)` 로 돌려준다.

    `doc` = `{"option_ctl": str, "total_mode": str, "measures": [...]}`.
    `measures` 의 한 항목: `part` · `chain`(조인트 이름 목록) · `attrs`.

    `joints`(template_map 로드 결과)를 주면 **`chain` 의 조인트 이름이 거기에 실제로
    있는지 검사**한다. 오타는 씬에서 조용히 0 이 되는 대신 **여기서 잡힌다**(계획서 4-1).

    `load()` 와 같은 태도로 **예외를 던지지 않는다** — 무엇이 잘못됐는지 messages 로 알린다.
    """
    messages = []
    empty = {"option_ctl": "", "total_mode": TOTAL_STRAIGHT, "measures": []}
    path = length_path(version)

    if not path or not os.path.isfile(path):
        messages.append("[ERR] Length file not found: {0}".format(path))
        return empty, messages

    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        messages.append("[ERR] Could not read {0} ({1}).".format(path, e))
        return empty, messages

    option_ctl = doc.get("option_ctl") or ""
    if not option_ctl:
        messages.append("[ERR] 'option_ctl' is missing - there is nowhere to write.")

    total_mode = doc.get("total_mode") or TOTAL_STRAIGHT
    if total_mode not in TOTAL_MODES:
        messages.append("[Warning] Unknown total_mode '{0}' - using '{1}'.".format(
            total_mode, TOTAL_STRAIGHT))
        total_mode = TOTAL_STRAIGHT

    known = {j["name"] for j in (joints or [])}
    measures = []
    attr_count = 0

    for item in (doc.get("measures") or []):
        part = (item or {}).get("part")
        if not part:
            messages.append("[Warning] A measure has no 'part' - skipped.")
            continue

        chain = list(item.get("chain") or [])
        if len(chain) < 2:
            messages.append(
                "[Warning] {0}: 'chain' needs at least 2 joints - skipped.".format(part))
            continue

        # 조인트 이름 오타를 여기서 잡는다 (씬을 보기 전에)
        if known:
            unknown = [j for j in chain if j not in known]
            if unknown:
                messages.append(
                    "[Warning] {0}: {1} is not in template_map.json.".format(
                        part, ", ".join(unknown)))

        attrs = dict(item.get("attrs") or {})
        attrs = {k: v for k, v in attrs.items() if v}
        if not attrs:
            messages.append("[Warning] {0}: no 'attrs' to write - skipped.".format(part))
            continue

        unknown_keys = [k for k in attrs if k not in ("total", "upper", "lower")]
        if unknown_keys:
            messages.append("[Warning] {0}: unknown attr key(s) {1} - ignored.".format(
                part, unknown_keys))
            for k in unknown_keys:
                attrs.pop(k, None)

        # upper/lower 는 마디가 정확히 둘일 때만 뜻이 있다
        if len(chain) != 3 and ("upper" in attrs or "lower" in attrs):
            messages.append(
                "[Warning] {0}: 'upper'/'lower' assume 3 joints but the chain has {1} "
                "- only 'total' will be written.".format(part, len(chain)))
            attrs.pop("upper", None)
            attrs.pop("lower", None)

        measures.append({"part": part, "chain": chain, "attrs": attrs})
        attr_count += len(attrs)

    messages.append("[OK] Loaded {0} measure(s), {1} attribute(s) from {2}.".format(
        len(measures), attr_count, os.path.basename(os.path.dirname(path))))

    return {"option_ctl": option_ctl,
            "total_mode": total_mode,
            "measures": measures}, messages


def check_length(doc):
    """길이 데이터 자체만 점검한다 (씬 없이). 문제 메시지 목록."""
    messages = []
    measures = doc.get("measures") or []

    if not measures:
        messages.append("[Warning] No measure in the length file.")
        return messages

    # 같은 어트리뷰트를 두 부위가 쓰면 나중 것이 앞 것을 덮는다
    owners = {}
    for m in measures:
        for role, attr in m["attrs"].items():
            owners.setdefault(attr, []).append("{0}.{1}".format(m["part"], role))
    for attr, who in sorted(owners.items()):
        if len(who) > 1:
            messages.append("[Warning] attribute '{0}' is written by {1}.".format(
                attr, ", ".join(who)))

    total = sum(len(m["attrs"]) for m in measures)
    messages.append("[Info] {0} part(s), {1} attribute(s) will be written.".format(
        len(measures), total))
    return messages
