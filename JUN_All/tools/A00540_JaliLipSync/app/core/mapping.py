# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00540_JaliLipSync - 매핑 json (모델 열 -> 리그 어트리뷰트). Maya 비의존.
#
# app/mappings/<이름>.json 하나 = 매핑 하나. 새 리그 · ARKit 아바타는 json 만 추가하면 된다(코드 수정 없음).
#   targets[] : {"attr": "CNT_PHONEMES.OHH", "from": ["Oh", "Uh"], "combine": "max", "scale": 10,
#                "role": "jali"(선택 - JaLi Fixed 일 때 키 대신 고정값)}
#   clamp     : 모델 값을 먼저 이 범위로 자른다 (원본 maya_animation.py 와 같은 0~1)

import json
import os


MAPPINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mappings")
COMBINES = ("max", "sum", "avg")


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

    columns = data.get("model_columns") or []
    targets = data.get("targets") or []
    if not targets:
        raise ValueError("Mapping {0} has no targets".format(name))
    for t in targets:
        if not t.get("attr") or "." not in t["attr"]:
            raise ValueError("Mapping {0}: bad attr {1!r}".format(name, t.get("attr")))
        unknown = [c for c in t.get("from", []) if c not in columns]
        if not t.get("from") or unknown:
            raise ValueError("Mapping {0}: {1} uses unknown column(s) {2}".format(name, t["attr"], unknown))
        if t.get("combine", "max") not in COMBINES:
            raise ValueError("Mapping {0}: {1} combine must be one of {2}".format(name, t["attr"], COMBINES))
    data.setdefault("clamp", [0.0, 1.0])
    data["name"] = data.get("name") or name
    return data


def combine(values, how):
    if how == "sum":
        return sum(values)
    if how == "avg":
        return sum(values) / float(len(values))
    return max(values)
