# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00610_PmxImporter - 임포트 순서 · 이름 정하기 · 텍스처 준비 · 리포트 (UI 를 모른다)
#
#   options = ImportOptions(...)
#   result = run_import("C:/.../Miyabi.pmx", options, log=print, progress=None)
#
# progress 는 단계 이름을 받는 begin(label) 와 (done, total, message) 콜백 두 가지를 쓴다 -
# UI 는 공용 진행 팝업에 그대로 이어 준다. 둘 다 None 이면 아무 것도 안 한다.

import json
import os
import time

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import maya_build as mb
from . import pmx_convert as cv
from . import pmx_reader as pr
from . import texture_resolver as tr
from ..config.version import VERSION

PHASES = [("Reading PMX", 5), ("Mesh", 15), ("Materials", 10), ("Skeleton", 15), ("Morphs", 15),
          ("Skin", 35), ("Finish", 5)]


class ImportOptions(object):
    def __init__(self, scale=cv.DEFAULT_SCALE, mesh=True, materials=True, skeleton=True, skin=True,
                 morphs=True, import_normals=True, hide_invisible_bones=True, dq_for_sdef=True,
                 copy_unsafe_textures=True, uv_set_name="map1", namespace=""):
        self.scale = float(scale)
        self.mesh = mesh
        self.materials = materials
        self.skeleton = skeleton
        self.skin = skin
        self.morphs = morphs
        self.import_normals = import_normals
        self.hide_invisible_bones = hide_invisible_bones
        self.dq_for_sdef = dq_for_sdef
        self.copy_unsafe_textures = copy_unsafe_textures
        self.uv_set_name = uv_set_name or "map1"
        self.namespace = namespace or ""


class ImportResult(object):
    def __init__(self):
        self.group = None
        self.mesh = None
        self.joints = []
        self.blendshape = None
        self.skin = None
        self.materials = []
        self.report = {}
        self.seconds = 0.0


def maya_codepage():
    """마야가 파일 경로에 쓰는 코드페이지 (예: '949' -> 'cp949')."""
    try:
        cs = str(cmds.about(codeset=True))
    except Exception:
        return ""
    if cs.isdigit():
        return "cp" + cs
    return cs


def plan_textures(model, pmx_dir, book, codepage, copy_unsafe=True, log=None):
    """재질 텍스처(색에 쓰는 것)마다 경로 · 알파 · file 노드 이름. 돌려주는 값: ({인덱스: info}, 리포트 목록)."""
    used = sorted(set(m.texture for m in model.materials if m.texture >= 0))
    infos = {}
    rows = []
    for t in used:
        if t >= len(model.textures):
            continue
        rel = model.textures[t]
        path, status = tr.resolve(pmx_dir, rel)
        row = {"index": t, "pmx": rel, "path": path, "status": status, "copied": False}
        if status == "missing":
            if log:
                log("[WARN] Missing texture: {0}".format(rel))
        elif not tr.codepage_safe(path, codepage):
            if copy_unsafe:
                dst = tr.ascii_copy_path(pmx_dir, rel)
                copied = tr.copy_if_needed(path, dst)
                row["copied"] = True
                row["path"] = dst
                if log:
                    log("Texture copied for Maya ({0} cannot read this path): {1} -> {2}".format(
                        codepage, rel, os.path.relpath(dst, pmx_dir).replace("\\", "/"))
                        + ("" if copied else "  (up to date)"))
            elif log:
                log("[WARN] Maya ({0}) cannot read this texture path: {1}".format(codepage, rel))
        alpha = tr.has_alpha(row["path"]) if os.path.isfile(row["path"]) else None
        row["alpha"] = bool(alpha)
        stem = os.path.splitext(tr.normalize_rel(rel).split("/")[-1])[0]
        infos[t] = {"node_name": book.unique((cv.encode_name(stem) or "tex_{0:02d}".format(t)) + "_file"),
                    "path": row["path"].replace("\\", "/"), "alpha": row["alpha"]}
        rows.append(row)
    return infos, rows


def run_import(pmx_path, options=None, log=None, progress=None, begin=None):
    options = options or ImportOptions()
    log = log or (lambda msg: None)
    t0 = time.time()

    def phase(label):
        if begin:
            begin(label)

    phase("Reading PMX")
    model = pr.read_pmx(pmx_path)
    pmx_dir = os.path.dirname(os.path.abspath(pmx_path))
    log("Read {0}: '{1}' ({2}) PMX {3}  vertices {4:,}  triangles {5:,}  materials {6}  bones {7}  morphs {8}".format(
        os.path.basename(pmx_path), model.name, model.name_e, model.header.version, len(model.vertices),
        len(model.faces), len(model.materials), len(model.bones), len(model.morphs)))

    result = ImportResult()
    with undo_chunk():
        ns = options.namespace.strip(":")
        prev_ns = cmds.namespaceInfo(currentNamespace=True, absoluteName=True)
        if ns:
            if not cmds.namespace(exists=":" + ns):
                cmds.namespace(add=ns, parent=":")
            cmds.namespace(setNamespace=":" + ns)
        try:
            _build(model, pmx_path, pmx_dir, options, log, progress, phase, result, ns)
        finally:
            if ns:
                cmds.namespace(setNamespace=prev_ns)
        result.seconds = time.time() - t0
        result.report["seconds"] = round(result.seconds, 2)
        cmds.setAttr(result.group + ".mmdImportReport", mb.ascii_json(result.report),
                     type="string")
    log("Done in {0:.1f}s - {1}".format(result.seconds, result.group))
    return result


def _build(model, pmx_path, pmx_dir, options, log, progress, phase, result, ns=""):
    S = options.scale
    # 겹침 검사는 만들 자리(네임스페이스) 기준
    book = cv.NameBook(taken=lambda n: cmds.objExists("{0}:{1}".format(ns, n) if ns else ":" + n))
    model_base = cv.encode_name(model.name.strip() or model.name_e.strip()) or \
        cv.encode_name(os.path.splitext(os.path.basename(pmx_path))[0]) or "pmx_model"
    grp = cmds.createNode("transform", name=book.unique(model_base + "_grp"))
    result.group = cmds.ls(grp, long=True)[0]
    geo_grp = cmds.createNode("transform", name=book.unique(model_base + "_geo_grp"), parent=grp)
    skel_grp = cmds.createNode("transform", name=book.unique(model_base + "_skel_grp"), parent=grp)
    # 문자열은 ASCII 로만 (maya_build 머리말 - .ma 의 코드페이지 손실)
    mb.add_string(grp, "mmdModelName", cv.encode_name(model.name))
    mb.add_string(grp, "mmdModelNameE", cv.encode_name(model.name_e))
    mb.add_string(grp, "mmdComment", mb.ascii_text(model.comment))
    mb.add_string(grp, "mmdSourceFile", mb.ascii_text(os.path.abspath(pmx_path).replace("\\", "/")))
    mb.add_string(grp, "mmdImporterVersion", VERSION)
    mb.add_string(grp, "mmdImportReport", "")

    rep = result.report
    rep["source"] = os.path.abspath(pmx_path).replace("\\", "/")
    rep["counts"] = {
        "vertices": len(model.vertices), "triangles": len(model.faces), "textures": len(model.textures),
        "materials": len(model.materials), "bones": len(model.bones), "morphs": len(model.morphs),
        "display_frames": len(model.display_frames), "rigid_bodies": len(model.rigids),
        "joints": len(model.joints), "soft_bodies": model.soft_body_count,
    }
    rep["weight_types"] = model.weight_type_counts()
    rep["morph_types"] = model.morph_type_counts()
    rep["not_imported"] = {
        "rigid_bodies": len(model.rigids), "joints": len(model.joints),
        "display_frames": len(model.display_frames),
        "non_vertex_morphs": sum(1 for m in model.morphs if m.type != 1),
        "ik_bones": sum(1 for b in model.bones if b.ik),
        "append_bones": sum(1 for b in model.bones if b.append_parent >= 0),
    }

    # -- 메시 -----------------------------------------------------------------
    phase("Mesh")
    mesh_tr = shape = None
    if options.mesh:
        mesh_tr, shape, mrep = mb.build_mesh(model, book.unique(model_base + "_mesh"), geo_grp, S,
                                             options.uv_set_name, options.import_normals, progress)
        result.mesh = cmds.ls(mesh_tr, long=True)[0]
        rep["mesh"] = mrep
        log("Mesh: {0}  UV sets {1}".format(mesh_tr, ", ".join(mrep["uv_sets"])))
        if mrep["additional_uv_zw_dropped"]:
            log("[WARN] Additional UV z/w values dropped on {0} vertices (Maya UVs are 2D).".format(
                mrep["additional_uv_zw_dropped"]))

    # -- 재질 -----------------------------------------------------------------
    phase("Materials")
    if options.mesh and options.materials and model.materials:
        infos, rows = plan_textures(model, pmx_dir, book, maya_codepage(), options.copy_unsafe_textures, log)
        mat_names = [book.item_name(m.name, m.name_e, "mat_{0:02d}".format(i)) for i, m in enumerate(model.materials)]
        created, mrep = mb.build_materials(model, shape, mat_names, infos, log, progress)
        result.materials = created
        mrep["textures"] = rows
        rep["materials"] = mrep
        log("Materials: {0} lambert  textures {1} (missing {2}, copied {3}, with alpha {4})".format(
            len(model.materials), len(rows), sum(1 for r in rows if r["status"] == "missing"),
            sum(1 for r in rows if r["copied"]), sum(1 for r in rows if r["alpha"])))
    elif options.mesh:
        cmds.sets(shape, edit=True, forceElement="initialShadingGroup")

    # -- 스켈레톤 --------------------------------------------------------------
    phase("Skeleton")
    if options.skeleton and model.bones:
        bone_names = [book.item_name(b.name, b.name_e, "bone_{0:03d}".format(i)) for i, b in enumerate(model.bones)]
        result.joints = mb.build_skeleton(model, bone_names, skel_grp, S, options.hide_invisible_bones,
                                          progress=progress)
        log("Skeleton: {0} joints".format(len(result.joints)))

    # -- 모프 (스킨보다 먼저 - 디포머 순서 blendShape -> skinCluster) --------------------
    phase("Morphs")
    if options.mesh and options.morphs:
        morph_names = [book_name for book_name in _morph_names(model)]
        bs, aliases = mb.build_morphs(model, shape, book.unique(model_base + "_morphs"), morph_names, S, progress)
        result.blendshape = bs
        rep["blendshape_targets"] = len(aliases)
        if bs:
            log("Morphs: {0} vertex morphs -> blendShape {1}".format(len(aliases), bs))
        skipped = model.morph_type_counts()
        skipped.pop("vertex", None)
        if skipped:
            log("[WARN] Morphs not imported (not vertex morphs): {0}".format(
                ", ".join("{0} {1}".format(k, v) for k, v in sorted(skipped.items()))))

    # -- 스킨 -----------------------------------------------------------------
    phase("Skin")
    if options.mesh and options.skin and result.joints:
        skin, srep = mb.build_skin(model, shape, result.joints, book.unique(model_base + "_skinCluster"),
                                   options.dq_for_sdef, progress)
        result.skin = skin
        rep["skin"] = srep
        if skin:
            log("Skin: {0}  influences {1}".format(skin, srep.get("influences")))
        if srep["normalized_vertices"]:
            log("[WARN] Weights normalized on {0} vertices (sum was not 1).".format(srep["normalized_vertices"]))
        if srep["unweighted_vertices"]:
            log("[WARN] {0} vertices have no weight.".format(srep["unweighted_vertices"]))
        if srep["sdef"] or srep["qdef"]:
            log("SDEF {0} / QDEF {1} vertices -> {2}.".format(
                srep["sdef"], srep["qdef"], "dual quaternion blend" if options.dq_for_sdef else "linear"))

    # -- 마무리 ---------------------------------------------------------------
    phase("Finish")
    ni = rep["not_imported"]
    if ni["rigid_bodies"] or ni["joints"] or ni["ik_bones"] or ni["append_bones"]:
        log("Kept as data only (not built): rigid bodies {0}, physics joints {1}, IK bones {2}, append bones {3}."
            .format(ni["rigid_bodies"], ni["joints"], ni["ik_bones"], ni["append_bones"]))
    cmds.select(result.group, replace=True)


def _morph_names(model):
    """모프 별칭 이름 (같은 blendShape 안에서만 겹치지 않으면 된다 - 씬 전체 이름과 무관)."""
    book = cv.NameBook()
    return [book.item_name(m.name, m.name_e, "morph_{0:02d}".format(i)) for i, m in enumerate(model.morphs)]
