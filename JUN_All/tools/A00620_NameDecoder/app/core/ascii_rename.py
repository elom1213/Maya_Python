# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00620_NameDecoder - Rename to ASCII: 번역표로 FBXASC 이름을 ASCII 이름으로 바꾸고, 원래 이름으로 되돌린다 (maya.cmds)
#
# ★ FBXASC 이름은 FBX 로 내보낼 때 원래 글자로 돌아간다(Model::あ, 2026-11-09 실측). ASCII 로 바꾸면 그 원래 이름이
#   사라진다 - 그래서 이 기능은 선택 기능이고, 바꾼 이름은 씬의 network 노드 하나에 기억해 Restore 로 되돌린다.
#   (노드마다 어트리뷰트를 붙이지 않는다 - 조인트 · 메시에 붙인 문자열 어트리뷰트는 FBX 사용자 속성으로 따라 나간다)
#
# 번역표 = {원래 글자 조각: ASCII}. 이름 안의 FBXASC 구간(조각)마다 가장 긴 키부터 바꾼다.
#   {"まばたき": "blink", "口": "mouth", "左": "L", " ": "_"}
#   まばたき -> blink,  口左Shape -> mouthLShape,  Left ankle -> Left_ankle
# 값이 빈 칸("")인 키는 아직 번역 안 한 것으로 본다(템플릿을 그대로 넣어도 아무것도 지우지 않게).
# 자동 번역 · 로마자 변환은 하지 않는다 - 바꾸지 못한 글자가 남으면 그 이름은 건너뛴다(Not mapped).

import io
import json

import maya.cmds as cmds

from Framework.core import fbx_name
from Framework.core import maya_fbx_names as MFN
from Framework.core.maya_undo import undo_chunk

STORE_ATTR = "a00610Originals"
STORE_NAME = "A00620_originalNames"

ST_READY = "Ready"
ST_NO_CHANGE = "No change"
ST_NOT_MAPPED = "Not mapped"
ST_INVALID = "Invalid name"
ST_BROKEN = "Broken FBXASC"
ST_REFERENCED = "Referenced"
ST_LOCKED = "Locked"
ST_MISSING = "Missing"
ST_NOT_SUPPORTED = "Not supported"
ST_IN_USE = "Name in use"
ST_RENAMED = "Renamed"
ST_FAILED = "Failed"


# ================================================================
# 번역표
# ================================================================

def load_map(path):
    """json {조각: ASCII} 를 읽는다. 문자열 쌍만 남긴다."""
    with io.open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Map file must be a JSON object: {\"original\": \"ascii\", ...}")
    return {str(k): str(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def save_map(mapping, path):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(mapping, ensure_ascii=False, indent=2))


def _replace(text, keys, mapping):
    out = []
    i = 0
    while i < len(text):
        for k in keys:
            if text.startswith(k, i):
                out.append(mapping[k])
                i += len(k)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _unmapped_chars(text):
    out = []
    for ch in text:
        if not (ch.isascii() and (ch.isalnum() or ch == "_")) and ch not in out:
            out.append(ch)
    return out


def translate(raw, mapping):
    """raw(FBXASC 이름) -> (새 이름, 상태, 설명).

    상태: Ready / No change / Not mapped(남은 글자) / Invalid name / Broken FBXASC
    """
    keys = sorted((k for k, v in mapping.items() if k and v), key=len, reverse=True)
    out = []
    for raw_part, text, kind in fbx_name.decode_parts(raw):
        if kind == "invalid":
            return raw, ST_BROKEN, raw_part
        out.append(_replace(text, keys, mapping) if kind == "decoded" else text)
    new = "".join(out)
    left = _unmapped_chars(new)
    if left:
        return new, ST_NOT_MAPPED, " ".join(repr(c) for c in left)
    if not fbx_name.is_valid_maya_name(new):
        return new, ST_INVALID, "Maya names cannot start with a digit" if new[:1].isdigit() else ""
    if new == raw:
        return new, ST_NO_CHANGE, ""
    return new, ST_READY, ""


class RenamePlan(object):
    __slots__ = ("entry", "new", "status", "note")

    def __init__(self, entry, new, status, note=""):
        self.entry = entry
        self.new = new
        self.status = status
        self.note = note

    @property
    def ready(self):
        return self.status == ST_READY


def _node_block(node):
    """이름을 바꿀 수 없는 노드면 상태, 아니면 None."""
    if node is None:
        return ST_MISSING
    if cmds.referenceQuery(node, isNodeReferenced=True):
        return ST_REFERENCED
    if (cmds.lockNode(node, query=True, lock=True) or [False])[0]:
        return ST_LOCKED
    return None


def preview(entries, mapping):
    """[RenamePlan] - 씬은 바꾸지 않는다. node · bs_target 만 다룬다(어트리뷰트 이름 · enum 은 Not supported)."""
    plans = []
    for e in entries:
        if e.kind not in (MFN.KIND_NODE, MFN.KIND_BS_TARGET):
            plans.append(RenamePlan(e, e.raw, ST_NOT_SUPPORTED, "only node names and blendShape targets"))
            continue
        new, status, note = translate(e.raw, mapping)
        if status == ST_READY:
            node = MFN.node_of(e)
            block = _node_block(node)
            if block:
                status, note = block, ""
            elif e.kind == MFN.KIND_BS_TARGET and cmds.attributeQuery(new, node=node, exists=True):
                status, note = ST_IN_USE, "the blendShape already has this attribute"
        plans.append(RenamePlan(e, new, status, note))
    return plans


# ================================================================
# 원래 이름 저장소 (씬의 network 노드 하나)
# ================================================================

def _store_node(create=False):
    for n in cmds.ls(type="network") or []:
        if cmds.attributeQuery(STORE_ATTR, node=n, exists=True):
            return n
    if not create:
        return None
    n = cmds.createNode("network", name=STORE_NAME, skipSelect=True)
    cmds.addAttr(n, longName=STORE_ATTR, dataType="string")
    cmds.setAttr("{0}.{1}".format(n, STORE_ATTR), json.dumps({"nodes": {}, "targets": {}}), type="string")
    return n


def read_store():
    n = _store_node()
    if not n:
        return {"nodes": {}, "targets": {}}
    try:
        data = json.loads(cmds.getAttr("{0}.{1}".format(n, STORE_ATTR)) or "{}")
    except ValueError:
        data = {}
    data.setdefault("nodes", {})
    data.setdefault("targets", {})
    return data


def _write_store(data):
    n = _store_node(create=True)
    cmds.setAttr("{0}.{1}".format(n, STORE_ATTR), json.dumps(data, ensure_ascii=True), type="string")


def stored_count():
    data = read_store()
    return len(data["nodes"]) + sum(len(v) for v in data["targets"].values())


# ================================================================
# 실행
# ================================================================

def apply(plans, log=None):
    """Ready 인 계획만 바꾼다. undo 한 번. [(plan, 결과 상태, 실제 이름)]."""
    log = log or (lambda m: None)
    results = []
    with undo_chunk():
        store = read_store()
        for p in plans:
            if not p.ready:
                continue
            e = p.entry
            node = MFN.node_of(e)
            try:
                if e.kind == MFN.KIND_NODE:
                    actual = cmds.rename(node, p.new).split("|")[-1]
                    store["nodes"].setdefault(e.uuid, e.raw)
                else:
                    cmds.aliasAttr(p.new, "{0}.weight[{1}]".format(node, e.index))
                    actual = p.new
                    store["targets"].setdefault(e.uuid, {}).setdefault(str(e.index), e.raw)
                results.append((p, ST_RENAMED, actual))
                if actual != p.new:
                    log("[WARN] {0} -> {1} (name taken, Maya used {2})".format(e.decoded, p.new, actual))
            except RuntimeError as exc:
                results.append((p, ST_FAILED, str(exc).strip()))
                log("[ERROR] {0}: {1}".format(e.decoded, str(exc).strip()))
        if results:
            _write_store(store)
    return results


def restore(log=None):
    """기억해 둔 원래(FBXASC) 이름으로 되돌리고 저장소 노드를 지운다. undo 한 번. (되돌린 수, 실패 수)."""
    log = log or (lambda m: None)
    data = read_store()
    done = failed = 0
    with undo_chunk():
        for uuid, raw in data["nodes"].items():
            found = cmds.ls(uuid, long=True)
            if not found:
                failed += 1
                log("[WARN] Node for {0} is gone - skipped.".format(fbx_name.decode(raw)))
                continue
            try:
                actual = cmds.rename(found[0], raw).split("|")[-1]
                done += 1
                if actual != raw:
                    log("[WARN] {0} restored as {1} (name taken).".format(fbx_name.decode(raw), actual))
            except RuntimeError as exc:
                failed += 1
                log("[ERROR] {0}: {1}".format(fbx_name.decode(raw), str(exc).strip()))
        for uuid, by_index in data["targets"].items():
            found = cmds.ls(uuid, long=True)
            for index, raw in by_index.items():
                if not found:
                    failed += 1
                    log("[WARN] blendShape for {0} is gone - skipped.".format(fbx_name.decode(raw)))
                    continue
                try:
                    cmds.aliasAttr(raw, "{0}.weight[{1}]".format(found[0], index))
                    done += 1
                except RuntimeError as exc:
                    failed += 1
                    log("[ERROR] {0}: {1}".format(fbx_name.decode(raw), str(exc).strip()))
        n = _store_node()
        if n and not failed:
            cmds.delete(n)
        elif n:
            log("[WARN] {0} name(s) could not be restored - {1} is kept.".format(failed, n))
    return done, failed
