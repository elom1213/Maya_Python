# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00540_JaliLipSync - 씬 도우미: JALI 리그 찾기 · 오디오 노드 (maya.cmds, UI 비의존)

import maya.cmds as cmds
import maya.mel as mel


RIG_MARKER = "CNT_PHONEMES"
SOUND_NODE = "jali_lipsync_audio"


def find_rigs():
    """CNT_PHONEMES 가 있는 네임스페이스 목록 ("" = 루트, "angela:" 처럼 콜론까지)."""
    names = cmds.ls("*" + RIG_MARKER, "*:" + RIG_MARKER, recursive=True, type="transform") or []
    found = []
    for name in names:
        short = name.split("|")[-1]
        ns = short.rsplit(":", 1)[0] + ":" if ":" in short else ""
        if ns not in found:
            found.append(ns)
    return found


def attach_sound(wav, start):
    """사운드 노드를 (다시) 만들고 GUI 면 타임슬라이더에 붙인다. Returns 노드 이름."""
    if cmds.objExists(SOUND_NODE):
        cmds.delete(SOUND_NODE)
    node = cmds.sound(file=wav, offset=start, name=SOUND_NODE)
    if not cmds.about(batch=True):
        try:
            slider = mel.eval("$tmp = $gPlayBackSlider")
            cmds.timeControl(slider, edit=True, sound=node, displaySound=True)
        except RuntimeError:
            pass
    return node
