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


# =========================
# 로드
# =========================

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
