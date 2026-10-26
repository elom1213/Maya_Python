# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 마야 파일을 열어 버전 · fps · 재생 범위 · 규칙에 맞는 세트를 읽는다 (maya.cmds, 워커 안)  (v01.41)
#
# probe(files, rule) -> {"files": [항목...], "mayapy_version": "2024"}   항목 = 계획서 §3.2
#   - 파일마다 ref_scanner.open_scene (저장된 레퍼런스 로드 상태 그대로, 스크립트 노드 X). 레퍼런스 안의 세트도 로드돼 있으면 보인다.
#   - version  = cmds.fileInfo("version", q=True) (저장한 마야, 실측 ['2024'])   fps = Framework.jali.time_units.fps_of_unit(currentUnit)
#   - playback = [min, max] (타임라인)   anim = [ast, aet]
#   - sets     = [{"name", "members", "nodes"}]  nodes = 멤버 + 자손 트랜스폼 수(가지치기 전)
#   - 실패한 파일은 ok=False + error 로 적고 다음 파일 계속. 취소 플래그는 파일 경계에서.

import os
import re
import time

try:
    from . import ref_scanner
    from . import set_match
except ImportError:          # mayapy 워커가 평범한 모듈로 import 할 때
    import ref_scanner
    import set_match

from Framework.jali import time_units


def _cmds():
    import maya.cmds as cmds
    return cmds


_PLAYBACK_RE = re.compile(r"-(min|max|ast|aet)\s+(-?[0-9.]+)")


def playback_from_script_node():
    """파일에 저장된 재생 범위 - `sceneConfigurationScriptNode` 의 `playbackOptions -min .. -max .. -ast .. -aet ..` 문장을 **읽기만** 한다.

    씬은 `executeScriptNodes=False` 로 열므로(스크립트 노드를 실행하지 않는다 - Reference 하위탭과 같은 안전 규칙) 그 노드가 돌지 않아
    `playbackOptions -q` 는 이전 씬 값(단위 환산까지 된)을 돌려준다(2026-10-26 실측: 2-120 이 1.25-150 으로). 그래서 문장을 파싱한다.
    반환 {"min","max","ast","aet"} (없는 키는 빠진다) 또는 {}.
    """
    cmds = _cmds()
    out = {}
    for node in cmds.ls(type="script") or []:
        if "sceneConfigurationScriptNode" not in node:
            continue
        try:
            text = cmds.getAttr(node + ".before") or ""
        except (RuntimeError, ValueError):
            continue
        if "playbackOptions" not in text:
            continue
        for key, value in _PLAYBACK_RE.findall(text):
            try:
                out[key] = float(value)
            except ValueError:
                pass
        if out:
            break
    return out


def scene_info():
    """현재 씬의 version · fps · unit · playback · anim · references."""
    cmds = _cmds()
    version = cmds.fileInfo("version", q=True) or [""]
    unit = cmds.currentUnit(q=True, time=True)
    saved = playback_from_script_node()
    loaded = unloaded = 0
    for node in ref_scanner.top_level_reference_nodes():
        try:
            if cmds.referenceQuery(node, isLoaded=True):
                loaded += 1
            else:
                unloaded += 1
        except RuntimeError:
            pass
    return {
        "version": str(version[0]) if version else "",
        "unit": unit,
        "fps": time_units.fps_of_unit(unit),
        "playback": [saved.get("min", cmds.playbackOptions(q=True, min=True)), saved.get("max", cmds.playbackOptions(q=True, max=True))],
        "anim": [saved.get("ast", cmds.playbackOptions(q=True, ast=True)), saved.get("aet", cmds.playbackOptions(q=True, aet=True))],
        "playback_source": "file" if saved else "session",
        "references": {"loaded": loaded, "unloaded": unloaded},
    }


def probe_sets(rule):
    cmds = _cmds()
    out = []
    for set_name in set_match.find_sets(rule):
        members = cmds.sets(set_name, q=True) or []
        kept, pruned = set_match.collect_targets([set_name], joints_only=False)
        out.append({"name": set_name, "members": len(members), "nodes": len(kept)})
    return out


def probe_file(path, rule, log=None):
    t0 = time.time()
    item = {"file": path, "ok": False, "error": "", "version": "", "fps": None, "unit": "",
            "playback": [None, None], "anim": [None, None], "sets": [], "references": {"loaded": 0, "unloaded": 0},
            "seconds": 0.0}
    if not os.path.isfile(path):
        item["error"] = "file not found"
        return item
    try:
        ref_scanner.open_scene(path)
    except Exception as exc:  # noqa: BLE001
        item["error"] = "open failed : {0}".format(str(exc).strip())
        item["seconds"] = round(time.time() - t0, 2)
        return item
    try:
        item.update(scene_info())
        item["sets"] = probe_sets(rule)
        item["ok"] = True
    except Exception as exc:  # noqa: BLE001
        item["error"] = "probe failed : {0}".format(str(exc).strip())
    item["seconds"] = round(time.time() - t0, 2)
    if log:
        name = os.path.basename(path)
        if item["ok"]:
            sets = ", ".join("{0} ({1} -> {2})".format(s["name"], s["members"], s["nodes"]) for s in item["sets"]) or "no matching set"
            log("{0} : {1} | {2} - {3} @ {4} fps | Maya {5}".format(
                name, sets, _fmt(item["playback"][0]), _fmt(item["playback"][1]), _fmt(item["fps"]), item["version"] or "?"))
        else:
            log("[WARN] {0} : {1}".format(name, item["error"]))
    return item


def _fmt(value):
    if value is None:
        return "?"
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return "{0:g}".format(value)


def probe(files, rule, log=None, progress=None, should_cancel=None):
    cmds = _cmds()
    files = [f for f in (files or []) if f]
    total = len(files)
    result = {"files": [], "mayapy_version": str(cmds.about(version=True)), "cancelled": False}
    for i, path in enumerate(files):
        if should_cancel and should_cancel():
            result["cancelled"] = True
            if log:
                log("[WARN] Cancelled - {0} of {1} file(s) checked.".format(i, total))
            break
        if progress:
            progress(i, total, "{0} : opening ({1}/{2})".format(os.path.basename(path), i + 1, total))
        result["files"].append(probe_file(path, rule, log=log))
    if progress:
        progress(total, total, "Done")
    return result
