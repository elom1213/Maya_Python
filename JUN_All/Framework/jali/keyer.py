# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.jali.keyer - JALI 리그에 키 걸기 / 지우기 (maya.cmds, UI 비의존)
#
# 2026-10-26 A00540_JaliLipSync/app/core/keyer.py 를 공용(Framework/jali)으로 올렸다 - A00560_JaliBatch 워커 ·
# A00570_JaliReview 가 같은 코드를 쓴다(릴리즈본은 툴 간 import 금지, Framework 는 모든 릴리즈에 동봉). A00540 은 재노출.
#
# JUN_JALI/examples/maya_apply_visemenet.py 를 옮긴 것. 원본 VisemeNet maya_animation.py 는 "4줄마다 1프레임"
# (= 25fps 가정)이었지만 여기서는 **씬 fps 로 시간을 샘플**한다(angela = film 24fps).
#   프레임 f  ->  시간 f / fps  ->  모델 줄 round(시간 * 100)
# 같은 구간의 이전 키를 먼저 지우고 건다(다시 Apply 해도 섞이지 않게). 전체가 Undo 한 번.
#
# v01.01 타겟 해석은 resolve_targets() 한 곳에서:
#   Auto   : namespace 를 매핑 json 의 노드 이름 앞에 붙인다 ("angela:CNT_PHONEMES.AAA")
#   Manual : node_map {"phonemes": 노드, "coartic": None, "jali": 노드} 로 json 의 노드 이름을 치환한다.
#            None 인 역할의 타겟은 건너뛴다(skipped).
# v01.02 여러 클립은 apply_sequence() - sequence.layout() 이 놓은 Segment 들을 한 Undo 로 건다. 클립 사이 hold 프레임은
#   클립 끝 값을 다음 클립 직전까지 키로 붙들어 정지 구간으로 만든다(안 붙들면 마야가 두 클립 사이를 천천히 보간한다).
#   apply() 는 클립 하나짜리 apply_sequence().

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import mapping as mapping_mod
from . import sequence


_FPS = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0, "show": 48.0,
        "palf": 50.0, "ntscf": 60.0}


class KeyingError(Exception):
    """키를 걸 수 없는 상태 (어트리뷰트 없음 · 잠김 · 다른 연결 · 타겟 없음)."""


def scene_fps():
    unit = cmds.currentUnit(q=True, time=True)
    if unit in _FPS:
        return _FPS[unit]
    try:
        return float(unit.replace("fps", ""))
    except ValueError:
        return 24.0


# ---------------------------------------------------------------------------
# 타겟 해석
# ---------------------------------------------------------------------------
def resolve_targets(mapping, namespace="", node_map=None):
    """키를 걸 타겟과 건너뛴 역할.

    Returns:
        (targets, skipped) — targets = [{"attr": 최종 plug, "key": json 의 attr, "role", "from", "combine"}],
        skipped = node_map 에서 None 인 역할 목록 (Auto 면 []).
    node_map 이 주어지면 namespace 는 무시한다.
    """
    nodes = mapping["nodes"]
    targets, skipped = [], []
    if node_map is not None:
        skipped = [role for role in mapping_mod.ROLES if role in nodes and not node_map.get(role)]
    for t in mapping["targets"]:
        node, attr = t["attr"].split(".", 1)
        role = t["role"]
        if node_map is not None:
            new_node = node_map.get(role)
            if not new_node:
                continue
            plug = "{0}.{1}".format(new_node, attr)
        else:
            plug = namespace + t["attr"]
        targets.append({"attr": plug, "key": t["attr"], "role": role,
                        "from": t["from"], "combine": t.get("combine", "max")})
    return targets, skipped


def target_attrs(mapping, namespace="", node_map=None):
    return [t["attr"] for t in resolve_targets(mapping, namespace, node_map)[0]]


def controls(mapping, namespace="", node_map=None):
    """매핑이 쓰는 컨트롤 노드 (중복 없이, 순서 유지)."""
    seen = []
    for attr in target_attrs(mapping, namespace, node_map):
        node = attr.split(".", 1)[0]
        if node not in seen:
            seen.append(node)
    return seen


def check_targets(mapping, namespace="", node_map=None):
    """키를 걸 수 없는 어트리뷰트를 [(attr, 이유)] 로 돌려준다. 비면 OK."""
    problems = []
    for attr in target_attrs(mapping, namespace, node_map):
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


def _scales(mapping, viseme_scale, jali_scale):
    v = mapping["viseme_scale"] if viseme_scale is None else float(viseme_scale)
    j = mapping["jali"]["scale"] if jali_scale is None else float(jali_scale)
    return v, j


def scale_warnings(targets, mapping, viseme_scale=None, jali_scale=None):
    """[(attr, scale, attr_max)] — 어트리뷰트에 max 가 있고 적용 배율이 그보다 크면. 막지 않고 알리는 용도."""
    v, j = _scales(mapping, viseme_scale, jali_scale)
    out = []
    for t in targets:
        if not cmds.objExists(t["attr"]):
            continue
        node, attr = t["attr"].split(".", 1)
        try:
            if not cmds.attributeQuery(attr, node=node, maxExists=True):
                continue
            mx = cmds.attributeQuery(attr, node=node, maximum=True)[0]
        except RuntimeError:
            continue
        scale = j if t["role"] == mapping_mod.JALI_ROLE else v
        if scale > mx + 1e-9:
            out.append((t["attr"], scale, mx))
    return out


# ---------------------------------------------------------------------------
# 샘플 · 적용 · 지우기
# ---------------------------------------------------------------------------
def sample(data, mapping, fps, viseme_scale=None, jali_scale=None, targets=None):
    """{타겟 attr(최종 plug): [프레임별 값]} 과 프레임 수. targets 가 None 이면 Auto(네임스페이스 없음)."""
    if targets is None:
        targets = resolve_targets(mapping)[0]
    idx = data.column_index()
    lo, hi = mapping.get("clamp", [0.0, 1.0])
    v_scale, j_scale = _scales(mapping, viseme_scale, jali_scale)
    n_frames = sequence.key_frames(data, fps)
    out = {}
    for t in targets:
        cols = [idx[c] for c in t["from"]]
        how = t["combine"]
        scale = j_scale if t["role"] == mapping_mod.JALI_ROLE else v_scale
        values = []
        for f in range(n_frames + 1):
            row = data.rows[min(int(round(f / fps * data.fps)), len(data.rows) - 1)]
            values.append(mapping_mod.combine([min(max(row[c], lo), hi) for c in cols], how) * scale)
        out[t["attr"]] = values
    return out, n_frames


def apply_sequence(segments, mapping, namespace="", viseme_scale=None, jali_scale=None, jali_fixed=None,
                   node_map=None, hold=0, progress=None):
    """여러 클립(sequence.layout 의 Segment 목록)을 순서대로 건다. 전체가 Undo 한 번.

    Args:
        viseme_scale / jali_scale: None = 매핑 json 의 기본값.
        jali_fixed: None = 데이터대로. (jaw, lip) = role "jali" 대상은 클립마다 처음과 끝에 그 값으로만 키 (리그 단위).
        node_map: Manual 모드 역할 -> 노드. None = Auto (namespace 사용).
        hold: 클립 사이 정지 프레임 수. 0 보다 크면 클립 끝 값을 end + hold 프레임에 한 번 더 키로 붙든다(마지막 클립 제외).
        progress: progress(done, total, message) 또는 None.

    Returns:
        dict(start, end, fps, keys, attrs, skipped, clips=[(label, start, end)])
    """
    if not segments:
        raise KeyingError("No clip - add at least one TXT")
    hold = int(hold)
    if hold < 0:
        raise KeyingError("Hold must be 0 or more frames")
    targets, skipped = resolve_targets(mapping, namespace, node_map)
    if not targets:
        raise KeyingError("No target node - fill at least one of Phonemes / Coartic / JaLi")
    problems = check_targets(mapping, namespace, node_map)
    if problems:
        raise KeyingError("Cannot key {0} attribute(s): {1}".format(
            len(problems), ", ".join("{0} ({1})".format(a, why) for a, why in problems)))

    fps = scene_fps()
    first, last = segments[0].start, segments[-1].end
    fixed_default = mapping["jali"]["fixed_default"]
    total = len(targets) * len(segments)
    done = 0
    keys = 0
    clips = []

    with undo_chunk():
        for t in targets:
            cmds.cutKey(t["attr"], time=(first, last), clear=True)
        for si, seg in enumerate(segments):
            values, n_frames = sample(seg.data, mapping, fps, viseme_scale, jali_scale, targets)
            hold_frame = seg.end + hold if (hold > 0 and si < len(segments) - 1) else None
            jali_iter = iter(jali_fixed) if jali_fixed else None
            for t in targets:
                attr = t["attr"]
                if jali_iter is not None and t["role"] == mapping_mod.JALI_ROLE:
                    last_value = float(next(jali_iter, fixed_default[0]))
                    for frame in (seg.start, seg.start + n_frames):
                        cmds.setKeyframe(attr, time=frame, value=last_value)
                    keys += 2
                else:
                    for f, v in enumerate(values[attr]):
                        cmds.setKeyframe(attr, time=seg.start + f, value=v)
                    keys += len(values[attr])
                    last_value = values[attr][-1]
                if hold_frame is not None:
                    cmds.setKeyframe(attr, time=hold_frame, value=last_value)
                    keys += 1
                done += 1
                if progress:
                    progress(done, total, "{0}: {1}".format(seg.label, attr))
            clips.append((seg.label, seg.start, seg.end))
    return {"start": first, "end": last, "fps": fps, "keys": keys, "attrs": len(targets), "skipped": skipped,
            "clips": clips}


def apply(data, mapping, namespace="", start=1, viseme_scale=None, jali_scale=None, jali_fixed=None,
          node_map=None, progress=None):
    """클립 하나를 start 부터 건다 (apply_sequence 의 단일 클립 형태). Returns apply_sequence 와 같은 dict."""
    seg = sequence.layout([sequence.Clip(getattr(data, "txt_path", ""), data)], start, 0, scene_fps())
    return apply_sequence(seg, mapping, namespace, viseme_scale, jali_scale, jali_fixed, node_map, 0, progress)


def remove(mapping, namespace="", start=None, end=None, node_map=None):
    """매핑 어트리뷰트의 키를 지운다. start/end 가 None 이면 전부. Returns 지운 어트리뷰트 수."""
    count = 0
    with undo_chunk():
        for attr in target_attrs(mapping, namespace, node_map):
            if not cmds.objExists(attr) or not cmds.keyframe(attr, q=True, keyframeCount=True):
                continue
            if start is None:
                cmds.cutKey(attr, clear=True)
            else:
                cmds.cutKey(attr, time=(start, end), clear=True)
            count += 1
    return count
