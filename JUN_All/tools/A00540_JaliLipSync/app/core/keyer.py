# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00540_JaliLipSync - 리그에 키 걸기 / 지우기 (maya.cmds, UI 비의존)
#
# JUN_JALI/examples/maya_apply_visemenet.py 를 옮긴 것. 원본 VisemeNet maya_animation.py 는 "4줄마다 1프레임"
# (= 25fps 가정)이었지만 여기서는 **씬 fps 로 시간을 샘플**한다(angela = film 24fps).
#   프레임 f  ->  시간 f / fps  ->  모델 줄 round(시간 * 100)
# 같은 구간의 이전 키를 먼저 지우고 건다(다시 Apply 해도 섞이지 않게). 전체가 Undo 한 번.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import mapping as mapping_mod


_FPS = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0, "show": 48.0,
        "palf": 50.0, "ntscf": 60.0}


class KeyingError(Exception):
    """키를 걸 수 없는 상태 (어트리뷰트 없음 · 잠김 · 다른 연결)."""


def scene_fps():
    unit = cmds.currentUnit(q=True, time=True)
    if unit in _FPS:
        return _FPS[unit]
    try:
        return float(unit.replace("fps", ""))
    except ValueError:
        return 24.0


def target_attrs(mapping, namespace=""):
    return [namespace + t["attr"] for t in mapping["targets"]]


def controls(mapping, namespace=""):
    """매핑이 쓰는 컨트롤 노드 (중복 없이, 순서 유지)."""
    seen = []
    for attr in target_attrs(mapping, namespace):
        node = attr.split(".", 1)[0]
        if node not in seen:
            seen.append(node)
    return seen


def check_targets(mapping, namespace=""):
    """키를 걸 수 없는 어트리뷰트를 [(attr, 이유)] 로 돌려준다. 비면 OK."""
    problems = []
    for attr in target_attrs(mapping, namespace):
        if not cmds.objExists(attr):
            problems.append((attr, "not found"))
            continue
        if cmds.getAttr(attr, lock=True):
            problems.append((attr, "locked"))
            continue
        src = cmds.listConnections(attr, source=True, destination=False, plugs=False, skipConversionNodes=True)
        if src and not cmds.ls(src, type="animCurve"):
            problems.append((attr, "driven by {0}".format(src[0])))
    return problems


def sample(data, mapping, fps, viseme_scale=None):
    """{attr(네임스페이스 없음): [프레임별 값]} 과 프레임 수."""
    idx = data.column_index()
    lo, hi = mapping.get("clamp", [0.0, 1.0])
    n_frames = int(len(data.rows) / data.fps * fps)
    out = {}
    for t in mapping["targets"]:
        cols = [idx[c] for c in t["from"]]
        how = t.get("combine", "max")
        scale = float(t.get("scale", 1.0))
        if viseme_scale is not None and t.get("role") != "jali":
            scale = float(viseme_scale)
        values = []
        for f in range(n_frames + 1):
            row = data.rows[min(int(round(f / fps * data.fps)), len(data.rows) - 1)]
            values.append(mapping_mod.combine([min(max(row[c], lo), hi) for c in cols], how) * scale)
        out[t["attr"]] = values
    return out, n_frames


def apply(data, mapping, namespace="", start=1, viseme_scale=None, jali_fixed=None, progress=None):
    """키를 건다.

    Args:
        jali_fixed: None = 데이터대로. (jaw, lip) = role "jali" 대상은 구간 처음과 끝에 그 값으로만 키.
        progress: progress(done, total, message) 또는 None.

    Returns:
        dict(start, end, fps, keys, attrs)
    """
    problems = check_targets(mapping, namespace)
    if problems:
        raise KeyingError("Cannot key {0} attribute(s): {1}".format(
            len(problems), ", ".join("{0} ({1})".format(a, why) for a, why in problems)))

    fps = scene_fps()
    values, n_frames = sample(data, mapping, fps, viseme_scale)
    end = start + n_frames
    total = len(mapping["targets"])
    keys = 0
    jali_iter = iter(jali_fixed) if jali_fixed else None

    with undo_chunk():
        for i, t in enumerate(mapping["targets"]):
            attr = namespace + t["attr"]
            cmds.cutKey(attr, time=(start, end), clear=True)
            if jali_iter is not None and t.get("role") == "jali":
                fixed = float(next(jali_iter, 9.0))
                for frame in (start, end):
                    cmds.setKeyframe(attr, time=frame, value=fixed)
                keys += 2
            else:
                for f, v in enumerate(values[t["attr"]]):
                    cmds.setKeyframe(attr, time=start + f, value=v)
                keys += len(values[t["attr"]])
            if progress:
                progress(i + 1, total, attr)
    return {"start": start, "end": end, "fps": fps, "keys": keys, "attrs": total}


def remove(mapping, namespace="", start=None, end=None):
    """매핑 어트리뷰트의 키를 지운다. start/end 가 None 이면 전부. Returns 지운 어트리뷰트 수."""
    count = 0
    with undo_chunk():
        for attr in target_attrs(mapping, namespace):
            if not cmds.objExists(attr) or not cmds.keyframe(attr, q=True, keyframeCount=True):
                continue
            if start is None:
                cmds.cutKey(attr, clear=True)
            else:
                cmds.cutKey(attr, time=(start, end), clear=True)
            count += 1
    return count
