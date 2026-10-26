# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 파일마다 열기 -> (레퍼런스 임포트 · 네임스페이스 제거) -> 세트 -> 노드 수집 -> 베이크 -> FBX
# (maya.cmds, mayapy 워커 안)  (v01.41)   설계: docs/plans/A00210_FileManager_maya_export_plan.md §5.4 · D7 · D9 · D9b · D10
#
# 파일 하나 (export_one):
#   1 open      ref_scanner.open_scene (저장된 로드 상태 그대로, 스크립트 노드 X) · fbx 플러그인
#   2 import    job.import_references 면 ref_importer.import_loaded_references + remove_all_namespaces   (실측: FBX 는 `CHN:root` 를 남긴다)
#   3 sets      set_match.find_sets(rule) - 없으면 skipped
#   4 targets   set_match.collect_targets(sets, joints_only) -> kept(베이크 · 내보낼 노드), pruned ; roots = 조상이 kept 에 없는 것
#   5 range     playbackOptions min/max/ast/aet = start/end   (FBX 타임스팬 = 언리얼 "Exported Time", 실측)
#   6 bake      bakeResults 한 호출 (simulation · sampleBy 1 · disableImplicitControl · preserveOutsideKeys False) + euler filter 옵션
#   7 roots     부모가 있는 루트를 **마야 최상위로** (사용자 결정 Q4, D9b):
#                 bake 일 때 - 6 전에 월드 로케이터 TMP_<root>_world 를 루트에 parent+scaleConstraint 로 붙여 (루트는 빼고) 함께 베이크,
#                 6 뒤에 루트 parent -w → 루트 T/R/S 의 키 · 입력 연결을 비우고 로케이터에 constraint → 루트만 재베이크 → 임시 삭제.
#                 (실측 2026-10-26: 애니된 그룹 · jointOrient · rotateOrder 가 달라도 월드 행렬 1e-13 동치. 단순 unparent 는 50 cm 틀림)
#                 Export Only 일 때 - parent -w 만 (현재 프레임 월드 유지) + 부모 체인에 애니 · 입력 연결이 있으면 [WARN]
#   8 export    kept 를 명시 선택 + IncludeChildren(가지친 게 있을 때 false) · InputConnections false · BakeComplexAnimation false
#               -> `<stem>__part.fbx` 로 쓰고 끝나면 os.replace (취소로 죽어도 반쪽 FBX 가 남지 않게)
# **원본 마야 파일은 저장하지 않는다.** 다음 파일 open 이 씬을 덮는다. 실패한 파일은 failed 로 적고 다음 파일 계속.

import os
import time

try:
    from . import ref_scanner
    from . import ref_importer
    from . import set_match
except ImportError:          # mayapy 워커가 평범한 모듈로 import 할 때
    import ref_scanner
    import ref_importer
    import set_match

from Framework.core import maya_fbx
from Framework.jali import time_units

CHANNEL_ATTRS = {"translate": ("tx", "ty", "tz"), "rotate": ("rx", "ry", "rz"), "scale": ("sx", "sy", "sz")}
ALL_ATTRS = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")
TMP_PREFIX = "TMP_A00210_"

# 파일 안 단계 비중 (설계 D15) - 진행률 팝업의 파일 한 칸 안에서
STEP_OPEN, STEP_IMPORT, STEP_BAKE, STEP_EXPORT, STEP_DONE = 0.0, 0.10, 0.25, 0.85, 1.0

STATUS_EXPORTED, STATUS_SKIPPED, STATUS_FAILED = "exported", "skipped", "failed"


def _cmds():
    import maya.cmds as cmds
    return cmds


def _attrs(channels):
    out = []
    for ch in channels or []:
        out.extend(CHANNEL_ATTRS.get(ch, ()))
    return out


def bake_nodes(nodes, start, end, attrs):
    """bakeResults 한 호출 (설계 D9). 실측: 78 조인트 x 6000 프레임 41 s, simulation=True 가 False 보다 빠르다."""
    cmds = _cmds()
    if not nodes or not attrs:
        return
    cmds.bakeResults(nodes, time=(start, end), attribute=list(attrs), simulation=True, sampleBy=1,
                     disableImplicitControl=True, preserveOutsideKeys=False, minimizeRotation=True,
                     sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, bakeOnOverrideLayer=False,
                     controlPoints=False, shape=False)


def euler_filter(nodes):
    cmds = _cmds()
    curves = []
    for node in nodes:
        for attr in ("rx", "ry", "rz"):
            curves.extend(cmds.listConnections("{0}.{1}".format(node, attr), s=True, d=False, type="animCurve") or [])
    if curves:
        cmds.filterCurve(curves)
    return len(curves)


def _clear_inputs(node, attrs):
    """node 의 T/R/S 키와 입력 연결을 비운다 (루트 재베이크 전 - 키가 있는 채널엔 scaleConstraint 가 붙지 않는다, 실측)."""
    cmds = _cmds()
    cmds.cutKey(node, at=list(attrs), clear=True)
    for a in list(attrs) + ["translate", "rotate", "scale"]:
        plug = node + "." + a
        for src in cmds.listConnections(plug, s=True, d=False, p=True) or []:
            try:
                cmds.disconnectAttr(src, plug)
            except RuntimeError:
                pass


def _parent_chain_has_motion(node):
    """node 의 조상 중 애니 커브 · 입력 연결(컨스트레인트 등)이 T/R/S 에 걸린 것이 있나 (Export Only 의 [WARN] 근거)."""
    cmds = _cmds()
    parent = set_match.parent_of(node)
    while parent:
        for a in ALL_ATTRS + ("translate", "rotate", "scale"):
            if cmds.listConnections(parent + "." + a, s=True, d=False):
                return True
        parent = set_match.parent_of(parent)
    return False


def relocate_roots_prepare(roots):
    """bake 모드: 부모가 있는 루트마다 월드 로케이터 + constraint. 반환 [(root, loc, [constraints])]."""
    cmds = _cmds()
    out = []
    for root in roots:
        if not set_match.parent_of(root):
            continue
        loc = cmds.spaceLocator(n=TMP_PREFIX + maya_fbx.short_name(root) + "_world")[0]
        cons = [cmds.parentConstraint(root, loc, mo=False)[0], cmds.scaleConstraint(root, loc, mo=False)[0]]
        out.append((root, loc, cons))
    return out


def relocate_roots_finish(prepared, start, end, attrs, log=None):
    """bake 모드: 로케이터 베이크가 끝난 뒤 - 루트 parent -w → 키 · 입력 비우기 → 로케이터에 constraint → 루트 재베이크 → 임시 삭제.
    반환 {old long name: new long name}."""
    cmds = _cmds()
    renamed = {}
    for root, loc, cons in prepared:
        cmds.delete(cons)
        new_root = cmds.parent(root, world=True)[0]
        new_root = (cmds.ls(new_root, long=True) or [new_root])[0]
        _clear_inputs(new_root, ALL_ATTRS)
        cons2 = [cmds.parentConstraint(loc, new_root, mo=False)[0], cmds.scaleConstraint(loc, new_root, mo=False)[0]]
        bake_nodes([new_root], start, end, attrs or ALL_ATTRS)
        cmds.delete(cons2 + [loc])
        renamed[root] = new_root
        if log:
            log("  root {0} moved to the top level (world motion baked)".format(maya_fbx.short_name(root)))
    return renamed


def relocate_roots_unparent(roots, log=None):
    """Export Only: parent -w 만. 반환 {old: new}."""
    cmds = _cmds()
    renamed = {}
    for root in roots:
        if not set_match.parent_of(root):
            continue
        warn = _parent_chain_has_motion(root)
        new_root = cmds.parent(root, world=True)[0]
        new_root = (cmds.ls(new_root, long=True) or [new_root])[0]
        renamed[root] = new_root
        if log:
            log("  root {0} moved to the top level{1}".format(
                maya_fbx.short_name(root),
                " - [WARN] its former parent is animated/driven; without Bake that motion is NOT in the FBX" if warn else ""))
    return renamed


def _part_path(out_fbx):
    """임시 출력 이름 `<stem>__part.fbx` - FBX 익스포터는 .fbx 가 아닌 이름에 .fbx 를 덧붙이므로(실측) 확장자는 .fbx 로 둔다."""
    stem, ext = os.path.splitext(out_fbx)
    return stem + "__part" + (ext or ".fbx")


def _rename_paths(nodes, renamed):
    """루트 이동으로 바뀐 long name 을 자손 경로에도 반영."""
    out = []
    for node in nodes:
        for old, new in renamed.items():
            if node == old or node.startswith(old + "|"):
                node = new + node[len(old):]
                break
        out.append(node)
    return out


def export_one(item, job, log=None, step=None):
    """파일 하나. 반환 dict (계획서 §3.3 results 항목). 예외는 안에서 잡아 failed."""
    cmds = _cmds()
    path, start, end, out_fbx = item["file"], int(item["start"]), int(item["end"]), item["out_fbx"]
    name = os.path.basename(path)
    rule = job["rule"]
    do_bake = bool(job.get("bake", True))
    channels = job.get("channels") or list(CHANNEL_ATTRS)
    attrs = _attrs(channels)
    res = {"file": path, "status": STATUS_FAILED, "out_fbx": out_fbx, "sets": [], "nodes": 0, "pruned": 0,
           "roots_moved": 0, "frames": end - start + 1, "fps": None, "imported_references": 0, "namespaces_removed": 0,
           "seconds": {}, "error": ""}
    times = {}

    def _log(msg):
        if log:
            log(msg)

    def _step(frac, msg):
        if step:
            step(frac, "{0} : {1}".format(name, msg))

    def _tick(key, t0):
        times[key] = round(time.time() - t0, 1)

    if not os.path.isfile(path):
        res["error"] = "file not found"
        return res

    # 1. open
    _step(STEP_OPEN, "opening")
    t0 = time.time()
    try:
        ref_scanner.open_scene(path)
        maya_fbx.ensure_fbx_plugin()
    except Exception as exc:  # noqa: BLE001
        res["error"] = "open failed : {0}".format(str(exc).strip())
        _tick("open", t0); res["seconds"] = times
        return res
    _tick("open", t0)
    res["fps"] = time_units.fps_of_unit(cmds.currentUnit(q=True, time=True))

    # 2. import references + namespaces
    t0 = time.time()
    if job.get("import_references", True):
        _step(STEP_IMPORT, "importing references")
        try:
            imported = ref_importer.import_loaded_references(log=_log)
            res["imported_references"] = len(imported)
            removed, failed = ref_importer.remove_all_namespaces(log=_log)
            res["namespaces_removed"] = removed
        except Exception as exc:  # noqa: BLE001
            res["error"] = "import references failed : {0}".format(str(exc).strip())
            _tick("import", t0); res["seconds"] = times
            return res
    _tick("import", t0)

    # 3. sets  4. targets
    sets = set_match.find_sets(rule)
    res["sets"] = sets
    if not sets:
        res["status"] = STATUS_SKIPPED
        res["error"] = "no set matches the rule"
        _log("  [SKIP] {0} : no set matches the rule - skipped".format(name))
        res["seconds"] = times
        return res
    kept, pruned = set_match.collect_targets(sets, joints_only=bool(job.get("joints_only", True)))
    if not kept:
        res["error"] = "nothing to export (set members have no transforms)"
        res["seconds"] = times
        return res
    roots = set_match.roots_of(kept)
    res["nodes"], res["pruned"] = len(kept), len(pruned)
    _log("  sets {0} -> {1} node(s), {2} pruned, {3} root(s)".format(", ".join(sets), len(kept), len(pruned), len(roots)))

    # 5. range
    cmds.playbackOptions(min=start, max=end, ast=start, aet=end)

    try:
        # 6. bake (+ 7 prepare)
        t0 = time.time()
        renamed = {}
        if do_bake:
            prepared = relocate_roots_prepare(roots)
            prepared_roots = {r for r, _l, _c in prepared}
            bake_list = [n for n in kept if n not in prepared_roots] + [loc for _r, loc, _c in prepared]
            _step(STEP_BAKE, "baking {0} frames x {1} nodes ({2})...".format(end - start + 1, len(kept), ", ".join(channels)))
            bake_nodes(bake_list, start, end, attrs)
            if job.get("euler_filter"):
                n = euler_filter([n for n in kept if n not in prepared_roots])
                _log("  euler filter on {0} curve(s)".format(n))
            renamed = relocate_roots_finish(prepared, start, end, attrs, log=_log)
            if job.get("euler_filter") and renamed:
                euler_filter(list(renamed.values()))
        else:
            renamed = relocate_roots_unparent(roots, log=_log)
        res["roots_moved"] = len(renamed)
        kept = _rename_paths(kept, renamed)          # 루트 이동으로 바뀐 long name 을 먼저 반영한 뒤 노드를 다시 만진다
        pruned = _rename_paths(pruned, renamed)
        if not do_bake:
            curves = set(cmds.listConnections(kept, type="animCurve") or [])
            if not curves:
                _log("  [WARN] {0} : no animation curve on the exported nodes - the FBX will have no animation (use Bake & Export?)".format(name))
        _tick("bake", t0)

        # 8. export
        _step(STEP_EXPORT, "exporting {0}".format(os.path.basename(out_fbx)))
        t0 = time.time()
        folder = os.path.dirname(out_fbx)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        part = _part_path(out_fbx)
        maya_fbx.export_selected(kept, part, include_children=False if pruned else None,
                                 input_connections=False, bake_complex_animation=False)
        if os.path.isfile(out_fbx):
            os.remove(out_fbx)
        os.replace(part, out_fbx)
        _tick("export", t0)
    except Exception as exc:  # noqa: BLE001
        res["error"] = "{0} failed : {1}".format("bake/export" if do_bake else "export", str(exc).strip())
        res["seconds"] = times
        try:
            if os.path.isfile(_part_path(out_fbx)):
                os.remove(_part_path(out_fbx))
        except OSError:
            pass
        return res

    res["status"] = STATUS_EXPORTED
    res["seconds"] = times
    _log("  [OK] {0} -> {1}  ({2} nodes, {3} frames, {4})".format(
        name, out_fbx, len(kept), end - start + 1,
        ", ".join("{0} {1}s".format(k, v) for k, v in times.items())))
    return res


def export_all(job, log=None, progress=None, should_cancel=None):
    """job["items"] 마다 export_one. progress 는 파일 단위(done, total, message), 파일 안은 STEP_* 비중. 취소는 파일 경계."""
    import json
    items = job.get("items") or []
    total = len(items)
    result = {"results": [], "exported": 0, "skipped": 0, "failed": 0, "cancelled": False}

    def _log(msg):
        if log:
            log(msg)

    for i, item in enumerate(items):
        if should_cancel and should_cancel():
            result["cancelled"] = True
            _log("[WARN] Cancelled - {0} of {1} file(s) done.".format(i, total))
            break
        name = os.path.basename(item["file"])
        _log("{0} ({1}/{2}) : {3} - {4}  [{5}]".format(name, i + 1, total, item["start"], item["end"],
                                                      "Bake & Export" if job.get("bake", True) else "Export Only"))

        def _step(frac, msg, _i=i):
            if progress:
                progress(_i + frac, total, msg)

        try:
            res = export_one(item, job, log=_log, step=_step)
        except Exception as exc:  # noqa: BLE001 - export_one 이 못 잡은 것
            res = {"file": item["file"], "status": STATUS_FAILED, "out_fbx": item.get("out_fbx", ""),
                   "error": "unexpected : {0}".format(str(exc).strip()), "seconds": {}}
        if res["status"] == STATUS_FAILED:
            _log("  [FAIL] {0} : {1}".format(name, res["error"]))
        result["results"].append(res)
        result[res["status"]] += 1
        _write_report(job, result)

    if progress:
        progress(total, total, "Done")
    _log("Export : {0} file(s) - {1} exported, {2} skipped, {3} failed{4}".format(
        total, result["exported"], result["skipped"], result["failed"], " (cancelled)" if result["cancelled"] else ""))
    _write_report(job, result)
    return result


def _write_report(job, result):
    """보고서 json (설계 D16) - 파일마다 갱신해 중간에 죽어도 남는다."""
    import json
    path = job.get("report")
    if not path:
        return
    try:
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        data = {"tool": "A00210_FileManager", "job": {k: v for k, v in job.items() if k not in ("result", "cancel_flag")},
                "updated": time.strftime("%Y-%m-%d %H:%M:%S"), "result": result}
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except OSError:
        pass
