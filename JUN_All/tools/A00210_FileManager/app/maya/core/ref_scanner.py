# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00210_FileManager / Maya 탭 - 디스크의 마야 파일들이 부르는 레퍼런스를 (중첩까지) 모은다
# (A00480_FileTool 에 먼저 만들었다가 2026-10-12 A00210 으로 옮겼다 - A00210 은 마야 밖 standalone 이라
#  maya.cmds 가 필요한 부분은 mayapy 워커(maya_worker.py)에서 이 모듈을 그대로 돌린다.)
#
# 파일 하나의 **직접** 레퍼런스를 읽는 방법은 확장자로 갈린다 (2026-10-12 mayapy 2024 실측):
#   .ma  : 머리글 텍스트만 파싱(ma_parser) - 씬을 열지 않는다.
#   .mb  : 바이너리라 파싱이 안 된다 - `file -o -loadReferenceDepth none` 으로 **열어서** 레퍼런스 노드를
#          읽는다(언로드 상태라 빠르다. 중첩은 부모가 로드돼야 생기므로 이 방법으로는 안 보인다).
#   그 밖 : (.fbx 등) 레퍼런스를 가질 수 없다 - 잎.
# 중첩은 **재귀**다 - 직접 레퍼런스 파일마다 같은 함수를 다시 부른다. 한 파일은 한 번만 읽고(캐시),
# 조상에 있는 파일이 또 나오면 순환으로 보고 내려가지 않는다.
#
# maya.cmds 는 함수 안에서 lazy import 한다 - .ma 만 스캔할 때와 Maya 밖에서는 maya 가 없어도 돈다.
# `allow_open=False` 로 부르면 .mb 를 만나는 순간 NeedsMayaError 를 내고 결과에 needs_maya=True 를 적는다 -
# A00210(standalone) 은 먼저 이렇게 돌려 보고, 마야가 필요하면 mayapy 워커로 다시 돌린다.
#
# 결과(dict):
#   {
#     "files":  [abs_file, ...],                  # 스캔을 요청한 마야 파일(순서 유지, 존재하는 것만)
#     "roots":  {abs_file: [norm, ...]},          # 마야 파일별 직접 레퍼런스(중복 제거, 순서 유지)
#     "nodes":  {norm: {"path", "name", "exists", "is_scene", "children": [norm...],
#                       "used_by": [abs_file...], "ref_type", "scanned", "cycle", "error"}},
#     "opened_scene": bool,                       # Maya 씬을 열어서 읽었는가
#     "logs":   [str, ...],
#   }
# norm = 대소문자 · 슬래시 차이를 무시한 경로 키(os.path.normcase(normpath(abspath))).

import os

try:
    from . import ma_parser
except ImportError:          # mayapy 워커가 평범한 모듈로 import 할 때
    import ma_parser


class NeedsMayaError(RuntimeError):
    """maya.cmds 없이는 읽을 수 없는 파일(.mb)을 만났다 - mayapy 워커로 다시 돌려야 한다."""

MAYA_SCENE_EXTS = (".ma", ".mb")


def norm_path(path):
    """대소문자/슬래시 차이를 무시한 키."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path))) if path else ""


def is_maya_scene(path):
    return os.path.splitext(path or "")[1].lower() in MAYA_SCENE_EXTS


# ------------------------------------------------------------------ maya helpers

def _cmds():
    import maya.cmds as cmds
    return cmds


def open_scene_no_refs(path):
    """씬을 **레퍼런스를 로드하지 않고** 연다(프롬프트 없음, 스크립트 노드 실행 안 함)."""
    cmds = _cmds()
    kwargs = dict(open=True, force=True, loadReferenceDepth="none", prompt=False,
                  ignoreVersion=True)
    try:
        cmds.file(path, executeScriptNodes=False, **kwargs)
    except TypeError:
        # 오래된 마야에 executeScriptNodes 플래그가 없으면 빼고 연다.
        cmds.file(path, **kwargs)


def open_scene(path):
    """씬을 **저장된 로드 상태 그대로** 연다(프롬프트 없음, 스크립트 노드 실행 안 함).

    임포트 단계는 이걸로 연다 - `loadReferenceDepth none` 으로 열어 저장하면 체크 안 한 레퍼런스가
    **언로드 상태로 굳어** 다음에 열 때 안 보인다(2026-10-12 실측). 기본 열기는 저장된 상태를 지킨다.
    """
    cmds = _cmds()
    kwargs = dict(open=True, force=True, prompt=False, ignoreVersion=True)
    try:
        cmds.file(path, executeScriptNodes=False, **kwargs)
    except TypeError:
        cmds.file(path, **kwargs)


def top_level_reference_nodes():
    """현재 씬의 **최상위** 레퍼런스 노드들(부모가 없는 것). 파일이 없는 shared 노드는 뺀다."""
    cmds = _cmds()
    out = []
    for node in (cmds.ls(references=True) or []):
        try:
            parent = cmds.referenceQuery(node, referenceNode=True, parent=True)
        except (RuntimeError, ValueError):
            parent = None
        if parent:
            continue
        if reference_file(node):
            out.append(node)
    return out


def reference_file(ref_node):
    """레퍼런스 노드의 파일 경로(복사본 번호 `{1}` 없이). 파일이 없는 노드면 ""."""
    cmds = _cmds()
    try:
        return cmds.referenceQuery(ref_node, filename=True, withoutCopyNumber=True) or ""
    except (RuntimeError, ValueError):
        return ""


def scene_direct_references():
    """현재 열린 씬의 직접 레퍼런스 파일 경로들(노드 순서, 중복 포함)."""
    return [reference_file(n) for n in top_level_reference_nodes()]


# ------------------------------------------------------------------ per-file

def direct_references(path, log=None, allow_open=True):
    """path 가 **직접** 부르는 레퍼런스 파일의 절대경로 목록(중복 포함, 순서 유지).

    반환: (paths, opened) - opened 는 Maya 씬을 열어서 읽었는가.
    .ma 는 파싱, .mb 는 열어서. 파싱이 깨진 .ma 는 열어서 읽는 길로 폴백한다(allow_open 이면).
    """
    ext = os.path.splitext(path)[1].lower()
    base_dir = os.path.dirname(os.path.abspath(path))

    if ext == ".ma":
        try:
            refs = ma_parser.direct_references(path)
            return [ma_parser.resolve_path(r.path, base_dir) for r in refs], False
        except Exception as exc:  # noqa: BLE001 - 깨진 머리글 · 인코딩
            if log:
                log("[WARN] Could not parse {0} ({1}) - opening it instead.".format(
                    os.path.basename(path), exc))
            if not allow_open:
                raise
    elif ext != ".mb":
        return [], False

    if not allow_open:
        raise NeedsMayaError(path)
    open_scene_no_refs(path)
    return [ma_parser.resolve_path(p, base_dir) for p in scene_direct_references()], True


# ------------------------------------------------------------------ scan

def _new_node(abs_path):
    return {
        "path": abs_path,
        "name": os.path.basename(abs_path),
        "exists": os.path.isfile(abs_path),
        "is_scene": is_maya_scene(abs_path),
        "children": [],
        "used_by": [],
        "ref_type": os.path.splitext(abs_path)[1].lstrip(".").lower(),
        "scanned": False,
        "cycle": False,
        "error": "",
    }


def scan(files, progress=None, log=None, allow_open=True):
    """마야 파일 목록 -> 레퍼런스 트리(모듈 머리글의 결과 형식).

    progress(done, total, message) 는 요청한 파일 단위로 부른다(중첩 파일은 메시지로만).
    """
    logs = []

    def _log(message):
        logs.append(message)
        if log:
            log(message)

    result = {"files": [], "roots": {}, "nodes": {}, "opened_scene": False, "logs": logs,
              "needs_maya": False}
    nodes = result["nodes"]

    todo = [os.path.abspath(f) for f in (files or []) if f]
    total = len(todo)
    for i, abs_file in enumerate(todo):
        if progress:
            progress(i, total, "Scanning {0}".format(os.path.basename(abs_file)))
        if not os.path.isfile(abs_file):
            _log("[WARN] File not found, skipped : {0}".format(abs_file))
            continue
        if not is_maya_scene(abs_file):
            _log("[WARN] Not a Maya scene (.ma / .mb), skipped : {0}".format(abs_file))
            continue
        if abs_file in result["files"]:
            continue
        result["files"].append(abs_file)

        try:
            refs, opened = direct_references(abs_file, log=_log, allow_open=allow_open)
        except NeedsMayaError:
            result["needs_maya"] = True
            result["roots"][abs_file] = []
            continue
        except Exception as exc:  # noqa: BLE001
            _log("[WARN] Could not read references of {0} : {1}".format(
                os.path.basename(abs_file), exc))
            result["roots"][abs_file] = []
            continue
        result["opened_scene"] = result["opened_scene"] or opened

        direct = []
        for ref_path in refs:
            key = norm_path(ref_path)
            if not key:
                continue
            node = nodes.get(key)
            if node is None:
                node = nodes[key] = _new_node(ref_path)
            if abs_file not in node["used_by"]:
                node["used_by"].append(abs_file)
            if key not in direct:
                direct.append(key)
        result["roots"][abs_file] = direct
        _log("{0} : {1} reference(s){2}".format(
            os.path.basename(abs_file), len(direct), "" if opened else " (header only)"))

        # 중첩 - 직접 레퍼런스 파일마다 재귀. 조상 = 이 마야 파일.
        ancestors = {norm_path(abs_file)}
        for key in direct:
            _scan_nested(key, nodes, ancestors, result, _log, allow_open, progress, i, total)

    if progress:
        progress(total, total, "Scan finished")
    return result


def _scan_nested(key, nodes, ancestors, result, _log, allow_open, progress, i, total):
    """nodes[key] 파일이 부르는 레퍼런스를 읽어 children 에 단다(한 번만). 조상이면 순환."""
    node = nodes[key]
    if key in ancestors:
        node["cycle"] = True
        _log("[WARN] Reference cycle, not followed : {0}".format(node["name"]))
        return
    if node["scanned"]:
        return
    node["scanned"] = True
    if not node["is_scene"] or not node["exists"]:
        return                                  # fbx 등은 잎, 없는 파일은 읽을 수 없다

    if progress:
        progress(i, total, "Scanning nested {0}".format(node["name"]))
    try:
        refs, opened = direct_references(node["path"], log=_log, allow_open=allow_open)
    except NeedsMayaError:
        result["needs_maya"] = True
        node["scanned"] = False
        return
    except Exception as exc:  # noqa: BLE001
        node["error"] = str(exc)
        _log("[WARN] Could not read references of {0} : {1}".format(node["name"], exc))
        return
    result["opened_scene"] = result["opened_scene"] or opened

    for ref_path in refs:
        child_key = norm_path(ref_path)
        if not child_key:
            continue
        child = nodes.get(child_key)
        if child is None:
            child = nodes[child_key] = _new_node(ref_path)
        if child_key not in node["children"]:
            node["children"].append(child_key)

    next_ancestors = ancestors | {key}
    for child_key in node["children"]:
        _scan_nested(child_key, nodes, next_ancestors, result, _log, allow_open, progress, i, total)


def needs_maya(files):
    """목록에 .mb 가 있으면 True - 스캔이 Maya 씬을 열게 된다(.ma 만이면 안 연다)."""
    return any(os.path.splitext(f or "")[1].lower() == ".mb" for f in (files or []))
