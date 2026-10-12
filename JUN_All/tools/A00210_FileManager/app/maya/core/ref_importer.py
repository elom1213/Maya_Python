# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00210_FileManager / Maya 탭 - 체크한 레퍼런스를 마야 파일마다 임포트하고 같은 파일에 저장 (maya.cmds)
# (A00210 은 standalone 이라 이 모듈은 mayapy 워커(maya_worker.py) 안에서 돈다.)
#
# 입력은 ref_scanner.scan() 결과 + 체크된 레퍼런스 키(norm) 집합. **마야 파일마다**:
#   1. 백업 (backup.py, 옵션)           5. 중첩이 올라오면 그것도 load -> import (요청: 중첩까지)
#   2. file -o (저장된 로드 상태 그대로)  6. Remove All Namespace (옵션) - 씬의 모든 네임스페이스를 루트로 병합
#   3. 체크된 직접 레퍼런스가 언로드면 load   (남는 레퍼런스의 네임스페이스는 지울 수 없으니 건너뛴다)
#   4. importReference                   7. 원래 타입(mayaAscii / mayaBinary)으로 제자리 저장
#
# 실측(2026-10-12, mayapy 2024)에 기댄 것:
#   - 언로드 레퍼런스는 importReference 가 에러 -> 먼저 loadReference.
#   - 부모를 임포트하면 그 중첩 레퍼런스가 **씬 최상위**로 올라온다 -> 다시 (load ->) import.
#   - **`loadReferenceDepth none` 으로 열어 저장하면 체크 안 한 레퍼런스가 언로드로 굳는다**(다음에 열면
#     안 보인다). 그래서 임포트는 기본 열기 - 저장된 로드 상태가 그대로 저장된다. (스캔만 none 으로 연다.)
#   - 네임스페이스는 깊은 것부터 `-mergeNamespaceWithRoot`. 로드된 레퍼런스의 네임스페이스는 지울 수 없다 -
#     남는 레퍼런스 것은 건너뛰고 개수만 알린다. 그 밖에 못 지운 것은 [WARN].
#   - 실패한 파일은 **저장하지 않고** 다음 파일로(반쯤 임포트된 채 저장 금지).
#
# mayapy 워커 안에서 도니 현재 씬 걱정은 없다.

import os

try:
    from . import backup as backup_mod
    from . import ref_scanner
except ImportError:          # mayapy 워커가 평범한 모듈로 import 할 때
    import backup as backup_mod
    import ref_scanner

# 지우지 않는 네임스페이스(마야 내부).
_PROTECTED_NS = ("UI", "shared")


def _cmds():
    import maya.cmds as cmds
    return cmds


# ------------------------------------------------------------------ plan

def plan(scan_result, checked_keys):
    """[(maya_file, [checked norm ...]), ...] - 체크된 직접 레퍼런스가 하나라도 있는 마야 파일만, 스캔 순서."""
    checked = set(checked_keys or ())
    out = []
    for maya_file in scan_result.get("files", []):
        keys = [k for k in scan_result["roots"].get(maya_file, []) if k in checked]
        if keys:
            out.append((maya_file, keys))
    return out


# ------------------------------------------------------------------ maya helpers

def _ensure_fbx_plugin():
    """FBX 레퍼런스를 load/import 하려면 fbxmaya 가 필요하다. 없어도 죽지 않는다."""
    cmds = _cmds()
    try:
        if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
            cmds.loadPlugin("fbxmaya", quiet=True)
    except Exception:  # noqa: BLE001
        pass


def _is_loaded(ref_node):
    cmds = _cmds()
    try:
        return bool(cmds.referenceQuery(ref_node, isLoaded=True))
    except (RuntimeError, ValueError):
        return False


def _scene_type():
    cmds = _cmds()
    types = cmds.file(q=True, type=True) or []
    return types[0] if types else ""


def _all_namespaces():
    """씬의 모든 네임스페이스(절대 이름 `:a:b`, 깊은 것 먼저). 내부 네임스페이스는 뺀다."""
    cmds = _cmds()
    names = cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True, absoluteName=True) or []
    out = []
    for ns in names:
        leaf = ns.split(":")[-1]
        if leaf in _PROTECTED_NS and ns.count(":") == 1:
            continue
        out.append(ns)
    out.sort(key=lambda n: (-n.count(":"), n))
    return out


def _reference_namespaces():
    """씬에 남아 있는 레퍼런스들의 네임스페이스(절대 이름). 언로드라 네임스페이스가 없는 것은 뺀다."""
    cmds = _cmds()
    out = set()
    for node in (cmds.ls(references=True) or []):
        try:
            ns = cmds.referenceQuery(node, namespace=True)
        except (RuntimeError, ValueError):
            continue
        if ns and ns != ":":
            out.add(ns if ns.startswith(":") else ":" + ns)
    return out


def remove_all_namespaces(log=None):
    """씬의 모든 네임스페이스를 루트로 병합한다. 반환: (지운 개수, 못 지운 이름들).

    남아 있는 레퍼런스의 네임스페이스(와 그 아래)는 지울 수 없으므로 건너뛴다(개수만 로그).
    """
    cmds = _cmds()
    removed = 0
    failed = []
    kept_ref = _reference_namespaces()
    skipped = 0
    for ns in _all_namespaces():
        if ns in kept_ref or any(ns.startswith(k + ":") for k in kept_ref):
            skipped += 1
            continue
        try:
            cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
            removed += 1
        except RuntimeError as exc:
            failed.append(ns)
            if log:
                log("    [WARN] Could not remove namespace {0} : {1}".format(ns, str(exc).strip()))
    if skipped and log:
        log("    kept {0} namespace(s) of references that stay referenced".format(skipped))
    return removed, failed


# ------------------------------------------------------------------ import one file

def import_into_file(maya_file, checked_keys, remove_namespaces=True, make_backup=True,
                     log=None, progress=None):
    """마야 파일 하나에 체크된 레퍼런스(+ 그 중첩)를 임포트하고 제자리 저장한다.

    반환 dict: {"file", "status": "saved" | "skipped" | "failed", "imported": [파일명...],
                "backup": 경로 또는 "", "namespaces_removed": int, "error": str}
    """
    cmds = _cmds()
    name = os.path.basename(maya_file)
    result = {"file": maya_file, "status": "failed", "imported": [], "backup": "",
              "namespaces_removed": 0, "error": ""}
    checked = set(checked_keys or ())

    def _log(message):
        if log:
            log(message)

    def _step(k, n, message):
        if progress:
            progress(k, n, message)

    # 1. 백업
    if make_backup:
        _step(0, 4, "{0} : backup".format(name))
        try:
            result["backup"] = backup_mod.backup_file(maya_file)
            _log("  backup -> {0}".format(result["backup"]))
        except Exception as exc:  # noqa: BLE001
            result["error"] = "backup failed : {0}".format(exc)
            _log("  [WARN] {0} - file skipped.".format(result["error"]))
            return result

    # 2. 열기 - 저장된 로드 상태 그대로(none 으로 열면 체크 안 한 레퍼런스가 언로드로 저장된다)
    _step(1, 4, "{0} : open".format(name))
    _ensure_fbx_plugin()
    try:
        ref_scanner.open_scene(maya_file)
    except Exception as exc:  # noqa: BLE001
        result["error"] = "open failed : {0}".format(exc)
        _log("  [WARN] {0} - file skipped.".format(result["error"]))
        return result
    scene_type = _scene_type()

    # 3. 체크된 직접 레퍼런스 노드 (체크 안 한 것은 건드리지 않는다 - 로드 상태도 그대로)
    queue = []
    for node in ref_scanner.top_level_reference_nodes():
        key = ref_scanner.norm_path(ref_scanner.reference_file(node))
        if key in checked:
            queue.append(node)
    if not queue:
        result["status"] = "skipped"
        result["error"] = "none of the checked references is in this file"
        _log("  (no checked reference in this file - skipped)")
        return result

    # 4~5. load -> import, 올라온 중첩도 같은 길
    _step(2, 4, "{0} : import".format(name))
    try:
        while queue:
            node = queue.pop(0)
            ref_file = ref_scanner.reference_file(node)
            if not _is_loaded(node):
                cmds.file(loadReference=node)
            before = set(ref_scanner.top_level_reference_nodes())
            cmds.file(referenceNode=node, importReference=True)
            after = set(ref_scanner.top_level_reference_nodes())
            surfaced = [n for n in after - before]
            result["imported"].append(os.path.basename(ref_file))
            _log("  imported {0}{1}".format(
                os.path.basename(ref_file),
                " (+{0} nested)".format(len(surfaced)) if surfaced else ""))
            # 올라온 중첩 레퍼런스는 노드 이름순으로 이어서(결정적 순서)
            queue.extend(sorted(surfaced))
    except Exception as exc:  # noqa: BLE001
        result["error"] = "import failed : {0}".format(str(exc).strip())
        _log("  [WARN] {0} - file NOT saved.".format(result["error"]))
        return result

    # 6. 네임스페이스
    if remove_namespaces:
        _step(3, 4, "{0} : namespaces".format(name))
        removed, failed = remove_all_namespaces(log=_log)
        result["namespaces_removed"] = removed
        _log("  namespaces removed : {0}{1}".format(
            removed, "" if not failed else " ({0} kept)".format(len(failed))))

    # 7. 저장 (원래 타입)
    _step(4, 4, "{0} : save".format(name))
    try:
        if scene_type:
            cmds.file(save=True, force=True, type=scene_type)
        else:
            cmds.file(save=True, force=True)
    except Exception as exc:  # noqa: BLE001
        result["error"] = "save failed : {0}".format(str(exc).strip())
        _log("  [WARN] {0}".format(result["error"]))
        return result

    result["status"] = "saved"
    _log("  [OK] saved {0} ({1})".format(name, scene_type or "?"))
    return result


# ------------------------------------------------------------------ batch

def import_references(scan_result, checked_keys, remove_namespaces=True, make_backup=True,
                      log=None, progress=None, should_cancel=None):
    """plan() 의 파일마다 import_into_file. progress 는 파일 단위(done, total, message).

    should_cancel() 이 True 를 돌려주면 **파일 경계에서** 멈춘다(저장 중간에 끊지 않는다).
    반환: {"results": [dict...], "saved": n, "skipped": n, "failed": n, "cancelled": bool}
    """
    jobs = plan(scan_result, checked_keys)
    total = len(jobs)
    summary = {"results": [], "saved": 0, "skipped": 0, "failed": 0, "cancelled": False}

    def _log(message):
        if log:
            log(message)

    for i, (maya_file, keys) in enumerate(jobs):
        if should_cancel and should_cancel():
            summary["cancelled"] = True
            _log("[WARN] Cancelled - {0} of {1} file(s) done.".format(i, total))
            break
        if progress:
            progress(i, total, "{0} ({1}/{2})".format(os.path.basename(maya_file), i + 1, total))
        _log("{0} : {1} checked reference(s)".format(os.path.basename(maya_file), len(keys)))

        def _sub(k, n, message, _i=i):
            # 파일 안의 4 단계를 파일 단위 진행률 안에 끼워 넣는다
            if progress:
                progress(_i + (float(k) / n if n else 1.0), total, message)

        res = import_into_file(maya_file, keys, remove_namespaces=remove_namespaces,
                               make_backup=make_backup, log=_log, progress=_sub)
        summary["results"].append(res)
        summary[res["status"]] += 1

    if progress:
        progress(total, total, "Done")
    _log("Import Reference : {0} file(s) - {1} saved, {2} skipped, {3} failed".format(
        total, summary["saved"], summary["skipped"], summary["failed"]))
    return summary
