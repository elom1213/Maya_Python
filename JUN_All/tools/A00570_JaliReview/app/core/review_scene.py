# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00570_JaliReview - 검수 씬 코어: 클립 · 아바타 레퍼런스, 교체, 편집 조회 · 저장 · 폐기 (maya.cmds, UI 비의존)
#
# 검수 씬 = 빈 씬 + 아바타 레퍼런스 + 클립 .mb 레퍼런스(ns CLIP, 고정). 클립 안에는 JALI 컨트롤러가 중첩 레퍼런스(CLIP:JALI:).
# M0 실측 (2026-10-26, mayapy 2024, 계획서 §6 · §10):
#   - 레퍼런스된 animCurve 의 키 편집은 `relationship "fcurve" ... -relationshipData "add <t> <v> ..." / "cut <t>"` 편집으로
#     **CLIP 레퍼런스 노드에 저장**된다. 켜야 한다: animDisplay -e -refAnimCurvesEditable 1 (optionVar refAnimCurvesEditable).
#     꺼져 있으면 keyframe -e 가 조용히 무시된다.
#   - `referenceQuery <CLIPRN> -editStrings` 는 클립 파일 자체의 중첩 편집(JALI 컨트롤러에 커브를 붙인 23건)까지 보여 준다.
#     검수 씬에서 한 편집만 세려면 **-onReferenceNode <CLIPRN>** 로 "그 노드에 저장된 것" 만 본다 (pending_edits).
#   - ARKIT_OUT → 블렌드셰이프 connectAttr 편집은 **아바타 레퍼런스 노드**에 저장된다(순서 무관). 교체 뒤에도 연결이 산다.
#   - 저장 = `cmds.file(<클립 경로>, saveReference=True)` → 클립 .mb 에 써지고 저장된 편집은 목록에서 빠진다.
#   - **교체 · 재로드 전에 반드시 저장하거나 버려야 한다**: 편집을 남긴 채 loadReference 하면 마야가 fcurve 편집의 시각을
#     24fps 기준으로 다시 환산한다(30fps 씬에서 10 → 12.5, 5000 → 6250 - 마야 버그). 그 상태로 저장하면 엉뚱한 프레임에 키가 생긴다.
#     그래서 Swap 은 pending 0 일 때만, Discard 는 unload → referenceEdit -removeEdits → load (로드 상태에서는 지워지지 않는다).
#   - 레퍼런스된 클립의 fileInfo 도장은 검수 씬에서 안 보인다 → start · end 는 매니페스트에서. 사운드 노드는 CLIP:jali_lipsync_audio 로 보인다.

import os
import re

import maya.cmds as cmds
import maya.mel as mel

CLIP_NS = "CLIP"
SOUND_NODE = "jali_lipsync_audio"
TEMP_AVATAR_NS = "REVIEW_AVATAR"
_FCURVE_EDIT = re.compile(r'^relationship\s+"fcurve"')


class ReviewError(Exception):
    """검수 씬 상태가 요구와 다를 때 (클립 없음 · 편집 남음 · 저장 실패)."""


# ---------------------------------------------------------------------------
# 레퍼런스 찾기
# ---------------------------------------------------------------------------
def _top_reference_nodes():
    out = []
    for rn in cmds.ls(type="reference") or []:
        if rn.endswith("sharedReferenceNode") or ":" in rn:
            continue
        try:
            if cmds.referenceQuery(rn, parent=True, referenceNode=True):
                continue
        except RuntimeError:
            continue
        out.append(rn)
    return out


def _namespace_of(rn):
    try:
        return cmds.referenceQuery(rn, namespace=True, shortName=True)
    except RuntimeError:
        return ""


def find_clip_ref():
    """네임스페이스 CLIP 인 최상위 레퍼런스 노드. 없으면 ""."""
    for rn in _top_reference_nodes():
        if _namespace_of(rn) == CLIP_NS:
            return rn
    return ""


def other_references():
    """클립이 아닌 최상위 레퍼런스 [(노드, 네임스페이스, 파일)] - 아바타 후보."""
    out = []
    for rn in _top_reference_nodes():
        ns = _namespace_of(rn)
        if ns == CLIP_NS or ns == TEMP_AVATAR_NS:
            continue
        out.append((rn, ns, clip_path(rn)))
    return out


def clip_path(rn):
    try:
        return cmds.referenceQuery(rn, filename=True, withoutCopyNumber=True)
    except RuntimeError:
        return ""


def is_loaded(rn):
    try:
        return bool(cmds.referenceQuery(rn, isLoaded=True))
    except RuntimeError:
        return False


# ---------------------------------------------------------------------------
# 만들기 · 교체
# ---------------------------------------------------------------------------
def reference_avatar(path, namespace=None):
    """아바타를 레퍼런스한다. namespace 가 없으면 파일 이름. Returns 레퍼런스 노드."""
    if not path or not os.path.isfile(path):
        raise ReviewError("Avatar file not found: {0}".format(path))
    ns = namespace or re.sub(r"[^A-Za-z0-9_]", "_", os.path.splitext(os.path.basename(path))[0])
    ref = cmds.file(path, reference=True, namespace=ns, prompt=False)
    return cmds.referenceQuery(ref, referenceNode=True, topReference=True)


def reference_clip(path):
    """클립을 ns CLIP 으로 레퍼런스한다(이미 CLIP 이 있으면 ReviewError - swap_clip 을 쓸 것). Returns 레퍼런스 노드."""
    if not path or not os.path.isfile(path):
        raise ReviewError("Clip file not found: {0}".format(path))
    if find_clip_ref():
        raise ReviewError("A CLIP reference already exists - use Swap")
    ref = cmds.file(path, reference=True, namespace=CLIP_NS, prompt=False)
    return cmds.referenceQuery(ref, referenceNode=True, topReference=True)


def swap_clip(rn, path):
    """클립 레퍼런스를 다른 파일로 바꾼다. 편집이 남아 있으면 ReviewError (저장 또는 폐기 먼저 - 시각 환산 버그 때문)."""
    if not path or not os.path.isfile(path):
        raise ReviewError("Clip file not found: {0}".format(path))
    pending = pending_edits(rn)
    if pending:
        raise ReviewError("{0} unsaved edit(s) on the current clip - Save Clip Edits or Discard first".format(len(pending)))
    cmds.file(path, loadReference=rn, prompt=False)
    return clip_path(rn)


# ---------------------------------------------------------------------------
# 편집
# ---------------------------------------------------------------------------
def anim_curve_edits_enabled():
    return bool(cmds.animDisplay(q=True, refAnimCurvesEditable=True))


def set_anim_curve_edits(enabled):
    cmds.animDisplay(e=True, refAnimCurvesEditable=bool(enabled))
    cmds.optionVar(iv=("refAnimCurvesEditable", 1 if enabled else 0))
    return anim_curve_edits_enabled()


def pending_edits(rn, failed=False):
    """검수 씬에서 이 클립에 한 편집 (CLIP 레퍼런스 노드에 **저장된** 것만 - 클립 자체의 중첩 편집은 제외)."""
    if not rn or not cmds.objExists(rn):
        return []
    try:
        return cmds.referenceQuery(rn, editStrings=True, onReferenceNode=rn, successfulEdits=not failed, failedEdits=failed) or []
    except RuntimeError:
        return []


def classify_edits(edits):
    """{"keys": [fcurve 편집], "other": [그 밖]} - 표시용."""
    keys = [e for e in edits if _FCURVE_EDIT.match(e)]
    return {"keys": keys, "other": [e for e in edits if e not in keys]}


def describe_edit(edit, max_len=120):
    """편집 문장을 사람이 읽을 한 줄로. fcurve 면 커브 이름 + add/cut 수."""
    m = re.match(r'^relationship\s+"fcurve"\s+"([^"]+)"(.*)$', edit)
    if m:
        curve, rest = m.group(1), m.group(2)
        adds = sum(len(re.findall(r"\badd\b", d)) for d in re.findall(r'-relationshipData\s+"([^"]*)"', rest))
        cuts = sum(len(re.findall(r"\bcut\b", d)) for d in re.findall(r'-relationshipData\s+"([^"]*)"', rest))
        return "{0}: {1} key change(s), {2} removal(s)".format(curve.split(":")[-1], adds, cuts)
    return edit if len(edit) <= max_len else edit[:max_len - 3] + "..."


def save_clip_edits(rn):
    """편집을 클립 .mb 에 쓴다 (file -saveReference). Returns (클립 경로, 남은 편집 수). 남으면 ReviewError."""
    path = clip_path(rn)
    if not path:
        raise ReviewError("No clip reference")
    if not is_loaded(rn):
        raise ReviewError("Clip reference is not loaded")
    cmds.file(path, saveReference=True)
    left = pending_edits(rn)
    if left:
        raise ReviewError("{0} edit(s) could not be saved into the clip".format(len(left)))
    return path, 0


def discard_edits(rn):
    """검수 씬에서 한 편집을 버린다: unload -> removeEdits -> load (로드 상태에서는 지워지지 않는다, M0 실측). Returns 지운 수."""
    before = len(pending_edits(rn)) + len(pending_edits(rn, failed=True))
    if not before:
        return 0
    cmds.file(unloadReference=rn)
    try:
        cmds.referenceEdit(rn, removeEdits=True, successfulEdits=True, failedEdits=True, onReferenceNode=rn)
    finally:
        cmds.file(loadReference=rn)
    return before - len(pending_edits(rn)) - len(pending_edits(rn, failed=True))


# ---------------------------------------------------------------------------
# 재생 범위 · 소리 · 단위
# ---------------------------------------------------------------------------
def apply_range(start, end):
    cmds.playbackOptions(min=start, max=end, ast=start, aet=end)
    cmds.currentTime(start)


def clip_sound_node():
    nodes = cmds.ls(CLIP_NS + ":" + SOUND_NODE, type="audio") or []
    return nodes[0] if nodes else ""


def attach_clip_sound():
    """레퍼런스된 클립의 사운드 노드를 타임슬라이더에 (GUI 에서만). Returns 노드 또는 ""."""
    node = clip_sound_node()
    if node and not cmds.about(batch=True):
        try:
            slider = mel.eval("$tmp = $gPlayBackSlider")
            cmds.timeControl(slider, edit=True, sound=node, displaySound=True)
        except RuntimeError:
            pass
    return node


def scene_unit():
    return cmds.currentUnit(q=True, time=True)


def set_scene_fps(fps):
    from Framework.jali import time_units
    cmds.currentUnit(time=time_units.unit_name(fps))
    return scene_unit()


def scene_modified():
    return bool(cmds.file(q=True, modified=True))


def new_scene():
    cmds.file(new=True, force=True)


# ---------------------------------------------------------------------------
# Open Clip (클립을 직접 열어 깊은 수정) - 아바타는 임시 레퍼런스
# ---------------------------------------------------------------------------
def open_clip(path):
    if not path or not os.path.isfile(path):
        raise ReviewError("Clip file not found: {0}".format(path))
    cmds.file(path, open=True, force=True, prompt=False)
    return path


def temp_avatar_ref():
    for rn in _top_reference_nodes():
        if _namespace_of(rn) == TEMP_AVATAR_NS:
            return rn
    return ""


def reference_temp_avatar(path):
    rn = temp_avatar_ref()
    if rn:
        return rn
    return reference_avatar(path, TEMP_AVATAR_NS)


def remove_temp_avatar():
    rn = temp_avatar_ref()
    if not rn:
        return False
    cmds.file(removeReference=True, referenceNode=rn)
    return True


def save_open_clip():
    """열린 클립을 제자리 저장 (임시 아바타는 먼저 뗀다). Returns 경로."""
    path = cmds.file(q=True, sceneName=True)
    if not path:
        raise ReviewError("The current scene is not a saved clip file")
    remove_temp_avatar()
    cmds.file(save=True, type="mayaBinary" if path.lower().endswith(".mb") else "mayaAscii", force=True)
    return path


def arkit_out_node():
    """검수 씬(CLIP:JALI:ARKIT_OUT) 또는 열린 클립(JALI:ARKIT_OUT) 의 ARKIT_OUT. 없으면 ""."""
    for name in (CLIP_NS + ":JALI:ARKIT_OUT", "JALI:ARKIT_OUT"):
        if cmds.objExists(name):
            return name
    found = cmds.ls("*:ARKIT_OUT", "ARKIT_OUT", recursive=True, type="transform") or []
    return found[0] if found else ""
