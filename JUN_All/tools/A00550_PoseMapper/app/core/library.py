# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - 포즈 라이브러리 (Maya 비의존, 계획서 §3.4)
#
# 포즈 = "음소 하나를 기준값(ref)으로 올렸을 때 각 타겟이 가질 값". 노드 이름은 저장하지 않는다(어트리뷰트 이름만)
# -> 같은 이름의 어트리뷰트를 가진 임의의 노드 쌍에 연결할 수 있다. 0 인 값은 저장하지 않는다(희소).

import json
import os


FORMAT_ID = "jun.posemap/1"
LIB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "libraries")
DEFAULT_REF = 10.0
EPS = 1e-6


class PoseLibrary(object):

    def __init__(self, name="untitled", ref_value=DEFAULT_REF, clamp=True, source_attrs=None,
                 poses=None, description=""):
        self.name = name
        self.description = description
        self.ref_value = float(ref_value)
        self.clamp = bool(clamp)
        self.source_attrs = list(source_attrs or [])
        self.poses = {p: dict(t) for p, t in (poses or {}).items()}

    # ------------------------------------------------------------ 값

    def get(self, phoneme, target):
        return self.poses.get(phoneme, {}).get(target, 0.0)

    def set(self, phoneme, target, value):
        value = float(value)
        if abs(value) < EPS:
            self.poses.get(phoneme, {}).pop(target, None)
            if phoneme in self.poses and not self.poses[phoneme]:
                del self.poses[phoneme]
        else:
            self.poses.setdefault(phoneme, {})[target] = value
        if phoneme not in self.source_attrs:
            self.source_attrs.append(phoneme)

    def pose(self, phoneme):
        return dict(self.poses.get(phoneme, {}))

    def clear_pose(self, phoneme):
        self.poses.pop(phoneme, None)

    def targets_used(self):
        seen = []
        for p in self.source_attrs + [p for p in self.poses if p not in self.source_attrs]:
            for t in self.poses.get(p, {}):
                if t not in seen:
                    seen.append(t)
        return seen

    def weights_for_target(self, target):
        """{phoneme: weight}  weight = pose / ref  (blendWeighted.weight 에 들어가는 값)."""
        return {p: t[target] / self.ref_value for p, t in self.poses.items() if target in t}

    # ------------------------------------------------------------ 파일

    def to_dict(self):
        return {"format": FORMAT_ID, "name": self.name, "description": self.description,
                "ref_value": self.ref_value, "clamp": self.clamp, "source_attrs": self.source_attrs,
                "poses": {p: {t: round(v, 6) for t, v in tv.items()} for p, tv in self.poses.items() if tv}}

    @classmethod
    def from_dict(cls, data):
        if data.get("format") not in (None, FORMAT_ID):
            raise ValueError("Unknown library format: {0}".format(data.get("format")))
        ref = float(data.get("ref_value", DEFAULT_REF))
        if ref <= 0:
            raise ValueError("ref_value must be > 0")
        return cls(name=data.get("name", "untitled"), ref_value=ref, clamp=data.get("clamp", True),
                   source_attrs=data.get("source_attrs", []), poses=data.get("poses", {}),
                   description=data.get("description", ""))


def list_libraries():
    if not os.path.isdir(LIB_DIR):
        return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(LIB_DIR) if f.lower().endswith(".json"))


def library_path(name):
    return os.path.join(LIB_DIR, name + ".json")


def load(name_or_path):
    path = name_or_path if name_or_path.lower().endswith(".json") else library_path(name_or_path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return PoseLibrary.from_dict(json.load(f))
    except (OSError, ValueError) as e:
        raise ValueError("Cannot read library {0}: {1}".format(os.path.basename(path), e))


def save(lib, path=None):
    path = path or library_path(lib.name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lib.to_dict(), f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path
