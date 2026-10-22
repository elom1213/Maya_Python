# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# A00540_JaliLipSync - 매핑 json (모델 열 -> 리그 어트리뷰트). Maya 비의존.
#
# app/mappings/<이름>.json 하나 = 매핑(규칙) 하나. 새 리그 · ARKit 아바타는 json 만 추가하면 된다(코드 수정 없음).
#   nodes        : 역할 -> 노드 이름 {"phonemes": "CNT_PHONEMES", "coartic": "CNT_COARTIC", "jali": "CNT_JaLi"}
#                  Auto 모드는 phonemes 노드를 표식으로 리그(네임스페이스)를 찾고, Manual 모드는 이 이름을 사용자가
#                  고른 노드로 치환한다. 모든 targets 의 노드는 여기 있어야 한다.
#   viseme_scale : 비짐 타겟의 기본 배율 (UI 스핀박스 기본값). 없으면 targets[].scale 의 첫 값, 그것도 없으면 1
#   jali         : {"scale": JaLi 타겟 배율, "range": Fixed 스핀박스 범위, "fixed_default": Fixed 기본 [jaw, lip]}
#   targets[]    : {"attr": "CNT_PHONEMES.OHH", "from": ["Oh", "Uh"], "combine": "max"}
#                  role 은 노드로 판정한다(명시 "role": "jali" 가 있으면 그것이 우선). scale 은 하위 호환으로만 읽는다.
#   clamp        : 모델 값을 먼저 이 범위로 자른다 (원본 maya_animation.py 와 같은 0~1)

import json
import os


MAPPINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mappings")
COMBINES = ("max", "sum", "avg")
ROLES = ("phonemes", "coartic", "jali")
JALI_ROLE = "jali"


def list_mappings():
    if not os.path.isdir(MAPPINGS_DIR):
        return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(MAPPINGS_DIR) if f.lower().endswith(".json"))


def load_mapping(name):
    """매핑을 읽고 검사한다. 틀리면 ValueError (영어 메시지)."""
    path = os.path.join(MAPPINGS_DIR, name + ".json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise ValueError("Cannot read mapping {0}: {1}".format(name, e))
    return validate(data, name)


def validate(data, name="mapping"):
    """dict 를 검사하고 기본값(nodes 역할 · viseme_scale · jali)을 채워 돌려준다. 틀리면 ValueError."""
    columns = data.get("model_columns") or []
    targets = data.get("targets") or []
    if not targets:
        raise ValueError("Mapping {0} has no targets".format(name))

    nodes = data.get("nodes")
    if not isinstance(nodes, dict) or not nodes:
        raise ValueError("Mapping {0} has no 'nodes' (role -> node name table)".format(name))
    for role, node in nodes.items():
        if role not in ROLES:
            raise ValueError("Mapping {0}: unknown role {1!r} in nodes (use {2})".format(name, role, ", ".join(ROLES)))
        if not isinstance(node, str) or not node or "." in node:
            raise ValueError("Mapping {0}: nodes[{1}] must be a node name without '.'".format(name, role))
    node_role = {node: role for role, node in nodes.items()}

    for t in targets:
        if not t.get("attr") or "." not in t["attr"]:
            raise ValueError("Mapping {0}: bad attr {1!r}".format(name, t.get("attr")))
        unknown = [c for c in t.get("from", []) if c not in columns]
        if not t.get("from") or unknown:
            raise ValueError("Mapping {0}: {1} uses unknown column(s) {2}".format(name, t["attr"], unknown))
        if t.get("combine", "max") not in COMBINES:
            raise ValueError("Mapping {0}: {1} combine must be one of {2}".format(name, t["attr"], COMBINES))
        node = t["attr"].split(".", 1)[0]
        if node not in node_role:
            raise ValueError("Mapping {0}: {1} uses node {2} not listed in nodes".format(name, t["attr"], node))
        t["role"] = t.get("role") or node_role[node]
        if t["role"] not in ROLES:
            raise ValueError("Mapping {0}: {1} has unknown role {2!r}".format(name, t["attr"], t["role"]))

    if "viseme_scale" not in data:
        scales = [t["scale"] for t in targets if t["role"] != JALI_ROLE and "scale" in t]
        data["viseme_scale"] = float(scales[0]) if scales else 1.0
    data["viseme_scale"] = float(data["viseme_scale"])

    jali = dict(data.get("jali") or {})
    if "scale" not in jali:
        scales = [t["scale"] for t in targets if t["role"] == JALI_ROLE and "scale" in t]
        jali["scale"] = float(scales[0]) if scales else 1.0
    jali["scale"] = float(jali["scale"])
    jali.setdefault("range", [0.0, 15.0])
    jali.setdefault("fixed_default", [9.0, 9.0])
    for key in ("range", "fixed_default"):
        if not isinstance(jali[key], (list, tuple)) or len(jali[key]) != 2:
            raise ValueError("Mapping {0}: jali.{1} must be [a, b]".format(name, key))
        jali[key] = [float(v) for v in jali[key]]
    if jali["range"][0] >= jali["range"][1]:
        raise ValueError("Mapping {0}: jali.range must be [min, max] with min < max".format(name))
    data["jali"] = jali

    data.setdefault("clamp", [0.0, 1.0])
    data["name"] = data.get("name") or name
    return data


def combine(values, how):
    if how == "sum":
        return sum(values)
    if how == "avg":
        return sum(values) / float(len(values))
    return max(values)
