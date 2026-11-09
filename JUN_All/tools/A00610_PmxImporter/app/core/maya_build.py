# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00610_PmxImporter - 마야 노드 만들기 (메시 · 재질 · 스켈레톤 · 모프 · 스킨)
#
# 함수마다 PmxModel 과 이미 정한 노드 이름을 받아 씬을 만든다. UI 를 모른다.
# 실측 근거는 계획서 §2 · §13:
#   - 트랜스폼을 cmds 로 만들고 그 아래에 MFnMesh.create 로 셰이프를 만들면 undo 청크 하나로 같이 사라진다.
#   - 지오메트리 없는 blendShape 타깃(inputPointsTarget + inputComponentsTarget 직접 입력)은 .mb/.ma 왕복에서 산다.
#   - 웨이트는 MFnSkinCluster.setWeights 한 번, 인덱스는 물리 인덱스(Framework.core.maya_skin.weight_indices).
#   - ★ 문자열 어트리뷰트는 ASCII 로만 쓴다: .ma 는 시스템 코드페이지(cp949)로 저장되어 그 밖의 글자('颜')가
#     '?' 로 깨진다(.mb 는 괜찮다, 2026-11-09 실측). 이름 = FBXASC(decode_name), 글 = JSON 유니코드 이스케이프(json.loads).

import json

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from Framework.core.maya_skin import weight_indices

from . import pmx_convert as cv
from . import pmx_reader as pr


def _mobject(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDependNode(0)


def _dag(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDagPath(0)


def _plug(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getPlug(0)


def add_string(node, attr, value):
    if not cmds.attributeQuery(attr, node=node, exists=True):
        cmds.addAttr(node, longName=attr, dataType="string")
    cmds.setAttr("{0}.{1}".format(node, attr), value or "", type="string")


def add_long(node, attr, value):
    if not cmds.attributeQuery(attr, node=node, exists=True):
        cmds.addAttr(node, longName=attr, attributeType="long")
    cmds.setAttr("{0}.{1}".format(node, attr), int(value))


def ascii_json(obj):
    """JSON 을 ASCII 로(비 ASCII 는 유니코드 이스케이프). json.loads 로 그대로 돌아온다."""
    return json.dumps(obj, ensure_ascii=True, sort_keys=True)


def ascii_text(text):
    """글 하나를 ASCII 로(JSON 문자열 본문). json.loads('"' + 값 + '"') 로 돌아온다."""
    return json.dumps(text or "", ensure_ascii=True)[1:-1]


def tag_item(node, name, name_e, index):
    """원본 이름 - 노드 이름과 같은 FBXASC 규칙(pmx_convert.decode_name 으로 읽는다)."""
    add_string(node, "mmdName", cv.encode_name(name))
    add_string(node, "mmdNameE", cv.encode_name(name_e))
    add_long(node, "mmdIndex", index)


def _round(seq, nd=6):
    return [round(float(x), nd) for x in seq] if seq is not None else None


# ----------------------------------------------------------------------------
# 메시
# ----------------------------------------------------------------------------

def build_mesh(model, transform_name, parent, scale, uv_set_name="map1", import_normals=True,
               progress=None):
    """메시 하나(정점 순서 = PMX). 돌려주는 값: (트랜스폼, 셰이프, 리포트 dict)."""
    report = {}
    tr = cmds.createNode("transform", name=transform_name, parent=parent)
    nv = len(model.vertices)
    pts = om.MPointArray()
    pts.setLength(nv)
    for i, v in enumerate(model.vertices):
        pts[i] = om.MPoint(*cv.to_maya_point(v.position, scale))
    counts = om.MIntArray(len(model.faces), 3)
    connects = om.MIntArray()
    connects.setLength(len(model.faces) * 3)
    k = 0
    for tri in model.faces:
        for vid in cv.to_maya_triangle(tri):
            connects[k] = vid
            k += 1
    fn = om.MFnMesh()
    fn.create(pts, counts, connects, parent=_mobject(tr))
    shape = cmds.listRelatives(tr, shapes=True, fullPath=False)[0]
    shape = cmds.rename(shape, transform_name.split("|")[-1] + "Shape")
    fn = om.MFnMesh(_dag(shape))
    if progress:
        progress(1, 4, "Mesh: UVs")

    # UV - PMX 는 정점당 UV 하나 -> uvId = 정점 번호
    cur = fn.currentUVSetName()
    if uv_set_name and cur != uv_set_name:
        fn.renameUVSet(cur, uv_set_name)
        cur = uv_set_name
    us = om.MFloatArray(nv, 0.0)
    vs = om.MFloatArray(nv, 0.0)
    for i, v in enumerate(model.vertices):
        u, w = cv.to_maya_uv(v.uv)
        us[i] = u
        vs[i] = w
    fn.setUVs(us, vs, cur)
    fn.assignUVs(counts, connects, cur)
    dropped_zw = 0
    for k_uv in range(model.header.additional_uvs):
        set_name = "UV{0}".format(k_uv + 1)
        fn.createUVSet(set_name)
        for i, v in enumerate(model.vertices):
            a = v.add_uvs[k_uv]
            us[i] = a[0]
            vs[i] = 1.0 - a[1]
            if abs(a[2]) > 1e-9 or abs(a[3]) > 1e-9:
                dropped_zw += 1
        fn.setUVs(us, vs, set_name)
        fn.assignUVs(counts, connects, set_name)
    fn.setCurrentUVSetName(cur)
    report["uv_sets"] = [cur] + ["UV{0}".format(k + 1) for k in range(model.header.additional_uvs)]
    report["additional_uv_zw_dropped"] = dropped_zw
    if progress:
        progress(2, 4, "Mesh: normals")

    # 엣지는 전부 부드럽게 - 노멀을 잠그기 전에
    cmds.polySoftEdge(shape, angle=180, constructionHistory=False)
    if import_normals:
        normals = om.MVectorArray()
        normals.setLength(nv)
        for i, v in enumerate(model.vertices):
            normals[i] = om.MVector(*cv.normalized(cv.to_maya_vector(v.normal)))
        fn = om.MFnMesh(_dag(shape))
        fn.setVertexNormals(normals, om.MIntArray(range(nv)), om.MSpace.kObject)
        cmds.dgdirty(shape)
    report["normals_locked"] = bool(import_normals)

    # 엣지(외곽선) 배율 - 1 이 아닌 정점이 있을 때만 컬러 셋 mmdEdgeScale (회색 = 배율)
    edges = [v.edge_scale for v in model.vertices]
    if any(abs(e - 1.0) > 1e-6 for e in edges):
        fn = om.MFnMesh(_dag(shape))
        fn.createColorSet("mmdEdgeScale", False)
        fn.setCurrentColorSetName("mmdEdgeScale")
        cmds.setAttr(shape + ".displayColors", 0)
        colors = om.MColorArray([om.MColor((e, e, e, 1.0)) for e in edges])
        fn.setVertexColors(colors, om.MIntArray(range(nv)))
        report["edge_scale_color_set"] = "mmdEdgeScale"
    if progress:
        progress(4, 4, "Mesh done")
    return tr, shape, report


# ----------------------------------------------------------------------------
# 재질
# ----------------------------------------------------------------------------

_PLACE2D_ATTRS = ("coverage", "translateFrame", "rotateFrame", "mirrorU", "mirrorV", "stagger",
                  "wrapU", "wrapV", "repeatUV", "offset", "rotateUV", "noiseUV",
                  "vertexUvOne", "vertexUvTwo", "vertexUvThree", "vertexCameraOne")


def create_file_node(name, path):
    fnode = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=name)
    place = cmds.shadingNode("place2dTexture", asUtility=True, name=name + "_place2d")
    for a in _PLACE2D_ATTRS:
        cmds.connectAttr("{0}.{1}".format(place, a), "{0}.{1}".format(fnode, a), force=True)
    cmds.connectAttr(place + ".outUV", fnode + ".uv", force=True)
    cmds.connectAttr(place + ".outUvFilterSize", fnode + ".uvFilterSize", force=True)
    # 경로는 API 로 넣는다(cmds.setAttr 은 코드페이지 밖 글자를 '?' 로 바꾼다 - 그런 경로는 이미 복사본이다)
    _plug(fnode + ".fileTextureName").setString(path)
    try:
        cmds.setAttr(fnode + ".colorSpace", "sRGB", type="string")
    except RuntimeError:
        pass
    cmds.setAttr(fnode + ".alphaIsLuminance", 0)
    return fnode, place


def build_materials(model, mesh_shape, mat_names, file_infos, log=None, progress=None):
    """재질마다 lambert + SG, 면 범위 할당.

    file_infos: {텍스처 인덱스: {"node_name", "path", "alpha"}} - 처음 쓰일 때 file 노드를 만든다(재질끼리 공유).
    돌려주는 값: (만든 노드 목록, 리포트)
    """
    created = []
    file_nodes = {}
    report = {"materials": [], "hidden": [], "transparent": []}
    ranges = model.material_face_ranges()
    total = len(model.materials)
    for i, mat in enumerate(model.materials):
        name = mat_names[i]
        shader = cmds.shadingNode("lambert", asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader + "SG")
        cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", force=True)
        created += [shader, sg]
        cmds.setAttr(shader + ".diffuse", 1.0)
        alpha = float(mat.diffuse[3])
        tex_alpha_plug = None
        tex = file_infos.get(mat.texture) if mat.texture >= 0 else None
        if tex:
            fnode = file_nodes.get(mat.texture)
            if fnode is None:
                fnode, place = create_file_node(tex["node_name"], tex["path"])
                file_nodes[mat.texture] = fnode
                created += [fnode, place]
            cmds.connectAttr(fnode + ".outColor", shader + ".color", force=True)
            if tex.get("alpha"):
                tex_alpha_plug = fnode
        else:
            cmds.setAttr(shader + ".color", *[float(c) for c in mat.diffuse[0:3]], type="double3")

        # 투명도 = 1 - (텍스처 알파 x diffuse 알파)
        if tex_alpha_plug and alpha >= 0.999:
            cmds.connectAttr(tex_alpha_plug + ".outTransparency", shader + ".transparency", force=True)
            report["transparent"].append(name)
        elif tex_alpha_plug:
            md = cmds.shadingNode("multiplyDivide", asUtility=True, name=name + "_alpha_mul")
            rv = cmds.shadingNode("reverse", asUtility=True, name=name + "_alpha_rev")
            cmds.connectAttr(tex_alpha_plug + ".outAlpha", md + ".input1X", force=True)
            cmds.setAttr(md + ".input2X", alpha)
            cmds.connectAttr(md + ".outputX", rv + ".inputX", force=True)
            for ch in "RGB":
                cmds.connectAttr(rv + ".outputX", shader + ".transparency" + ch, force=True)
            created += [md, rv]
            report["transparent"].append(name)
        elif alpha < 0.999:
            t = 1.0 - max(0.0, alpha)
            cmds.setAttr(shader + ".transparency", t, t, t, type="double3")
            report["transparent"].append(name)
        if alpha <= 1e-6:
            report["hidden"].append(name)
            if log:
                log("[WARN] Material '{0}' has diffuse alpha 0 - it is fully transparent (hidden in MMD too).".format(name))

        tag_item(shader, mat.name, mat.name_e, i)
        data = {
            "diffuse": _round(mat.diffuse), "specular": _round(mat.specular),
            "specularPower": round(mat.specular_power, 6), "ambient": _round(mat.ambient),
            "flags": mat.flags, "doubleSided": bool(mat.flags & pr.MAT_DOUBLE_SIDED),
            "edge": bool(mat.flags & pr.MAT_EDGE), "edgeColor": _round(mat.edge_color),
            "edgeSize": round(mat.edge_size, 6),
            "texture": model.textures[mat.texture] if 0 <= mat.texture < len(model.textures) else "",
            "sphere": model.textures[mat.sphere] if 0 <= mat.sphere < len(model.textures) else "",
            "sphereMode": pr.SPHERE_MODES[mat.sphere_mode] if mat.sphere_mode < 4 else mat.sphere_mode,
            "toon": ("toon{0:02d}.bmp".format(mat.toon + 1) if mat.shared_toon
                     else (model.textures[mat.toon] if 0 <= mat.toon < len(model.textures) else "")),
            "toonShared": mat.shared_toon, "memo": mat.memo,
        }
        add_string(shader, "mmdData", ascii_json(data))

        start, count = ranges[i]
        if count > 0:
            cmds.sets("{0}.f[{1}:{2}]".format(mesh_shape, start, start + count - 1), edit=True, forceElement=sg)
        report["materials"].append({"name": name, "faces": count})
        if progress:
            progress(i + 1, total, "Material {0}/{1}".format(i + 1, total))
    return created, report


# ----------------------------------------------------------------------------
# 스켈레톤
# ----------------------------------------------------------------------------

_IDENTITY = om.MMatrix()


def _rows(x, y, z):
    return om.MMatrix([x.x, x.y, x.z, 0.0, y.x, y.y, y.z, 0.0, z.x, z.y, z.z, 0.0, 0.0, 0.0, 0.0, 1.0])


def bone_rest_frames(model, use_local_axes=True):
    """본마다 레스트 월드 방향(회전 행렬, 행 = X/Y/Z 축, 마야 좌표).

    - 로컬축(0x800): X = localX, Z 는 localZ 를 X 에 직교화, Y = Z x X  (MMD 가 화면에 그리는 축 그대로)
    - 고정축(0x400)만: X = 고정축, Z = X x 월드 위(평행이면 월드 Z), Y = Z x X
    - 나머지 · use_local_axes=False: 월드 정렬(항등) - MMD 본은 원래 방향이 없다
    """
    frames = []
    for b in model.bones:
        frame = _IDENTITY
        if use_local_axes and b.local_x and b.local_z:
            x = om.MVector(*cv.to_maya_vector(b.local_x))
            zt = om.MVector(*cv.to_maya_vector(b.local_z))
            if x.length() > 1e-6 and zt.length() > 1e-6 and (zt ^ x).length() > 1e-6:
                x.normalize()
                y = (zt ^ x).normal()
                frame = _rows(x, y, (x ^ y).normal())
        elif use_local_axes and b.fixed_axis:
            x = om.MVector(*cv.to_maya_vector(b.fixed_axis))
            if x.length() > 1e-6:
                x.normalize()
                up = om.MVector(0, 1, 0) if abs(x.y) < 0.95 else om.MVector(0, 0, 1)
                z = (x ^ up).normal()
                frame = _rows(x, (z ^ x).normal(), z)
        frames.append(frame)
    return frames


def build_skeleton(model, bone_names, parent_grp, scale, hide_invisible=True, radius=None, progress=None,
                   use_local_axes=True):
    """본마다 조인트, 계층 = PMX 부모. 돌려주는 값: ([조인트 (본 인덱스 순)], [레스트 월드 방향 MMatrix]).

    use_local_axes: 로컬축 · 고정축이 있는 본은 그 축으로 jointOrient(월드 위치는 그대로), 나머지는 월드 정렬.
    """
    bones = model.bones
    order, parents = cv.bone_creation_order(bones)
    world = [cv.to_maya_point(b.position, scale) for b in bones]
    frames = bone_rest_frames(model, use_local_axes)
    if radius is None:
        ys = [p[1] for p in world] or [0.0]
        radius = max(0.05, (max(ys) - min(ys)) * 0.004)
    joints = [None] * len(bones)
    total = len(order)
    for n, i in enumerate(order):
        b = bones[i]
        p = parents[i]
        parent = joints[p] if p >= 0 else parent_grp
        j = cmds.createNode("joint", name=bone_names[i], parent=parent)
        joints[i] = cmds.ls(j, long=True)[0]
        base = world[p] if p >= 0 else (0.0, 0.0, 0.0)
        p_frame = frames[p] if p >= 0 else _IDENTITY
        p_inv = p_frame.inverse()
        # 로컬 위치 = 부모 레스트 방향으로 본 오프셋, jointOrient = 내 방향 x 부모 방향^-1 (행벡터 규약)
        off = om.MVector(world[i][0] - base[0], world[i][1] - base[1], world[i][2] - base[2]) * p_inv
        cmds.setAttr(joints[i] + ".translate", off.x, off.y, off.z, type="double3")
        if not frames[i].isEquivalent(p_frame, 1e-12):
            e = om.MTransformationMatrix(frames[i] * p_inv).rotation()
            cmds.setAttr(joints[i] + ".jointOrient", *[om.MAngle(a).asDegrees() for a in (e.x, e.y, e.z)],
                         type="double3")
        cmds.setAttr(joints[i] + ".radius", radius)
        if hide_invisible and not (b.flags & pr.BONE_VISIBLE):
            cmds.setAttr(joints[i] + ".drawStyle", 2)
        if progress and n % 20 == 0:
            progress(n, total, "Joint {0}/{1}".format(n, total))
    # 이름 · 원본 데이터 (부모를 다 만든 뒤 - 경로가 바뀌지 않는다)
    for i, b in enumerate(bones):
        j = joints[i]
        tag_item(j, b.name, b.name_e, i)
        data = {
            "flags": b.flags, "layer": b.layer, "parent": b.parent,
            "tailBone": b.tail_bone if b.flags & pr.BONE_TAIL_IS_BONE else None,
            "tailOffset": _round(cv.to_maya_point(b.tail_offset, scale)) if b.tail_offset else None,
            "appendParent": b.append_parent if b.append_parent >= 0 else None,
            "appendRatio": round(b.append_ratio, 6) if b.append_parent >= 0 else None,
            "appendRotate": bool(b.flags & pr.BONE_APPEND_ROTATE),
            "appendMove": bool(b.flags & pr.BONE_APPEND_MOVE),
            "appendLocal": bool(b.flags & pr.BONE_APPEND_LOCAL),
            "fixedAxis": _round(cv.to_maya_vector(b.fixed_axis)) if b.fixed_axis else None,
            "localX": _round(cv.to_maya_vector(b.local_x)) if b.local_x else None,
            "localZ": _round(cv.to_maya_vector(b.local_z)) if b.local_z else None,
            "externalParentKey": b.external_parent_key,
        }
        if b.ik:
            data["ik"] = {
                "target": b.ik.target, "loop": b.ik.loop, "limitAngle": round(b.ik.limit_angle, 6),
                "links": [{"bone": l.bone,
                           "min": _round(l.limit_min) if l.limit_min else None,
                           "max": _round(l.limit_max) if l.limit_max else None} for l in b.ik.links],
            }
        add_string(j, "mmdData", ascii_json(dict((k, v) for k, v in data.items() if v is not None)))
    return joints, frames


# ----------------------------------------------------------------------------
# 부여(付与) - quatNodes 망
# ----------------------------------------------------------------------------
#
# MMD 본은 레스트 방향이 없다(월드 정렬). 본 i 의 "MMD 로컬 회전" Rm 과 마야 rotate R 은
#     Rm = W_i^-1 * R * W_i            (W_i = 조인트 레스트 월드 방향, 행벡터 · quatProd(a, b) = a 먼저)
# 부여 본 c (부여 부모 a, 비율 r):  Append = slerp(I, Rm_a, r)   (r < 0 이면 Rm_a^-1 를 |r| 만큼)
#     ★ 순서: MMD 는 q_c = own * Append (열벡터) = 부여가 먼저, 자기 회전이 나중
#       (three.js MMD GrantSolver · saba 와 같다. Blender mmd_tools 는 오일러 TRANSFORM 근사라 판정 기준이 못 된다 - 계획서 §15).
#     마야 조인트 행렬은 [rotateAxis][rotate][jointOrient][T] 라 rotateAxis 가 rotate 보다 먼저 -> 거기에 넣는다:
#       RA = W_c * Append * W_c^-1   (rotate · translate 는 그대로 = 직접 조작 가능)
# 부여 부모가 또 부여 본이면(補助 <- 足D <- 足) 그 본의 '총 MMD 회전'(부여 다음 자기 rotate)을 쓴다.
# IK 가 돌린 본(足 · ひざ · 足首)은 rotate 에 IK 결과가 들어 있으므로 그대로 부여된다.
# 마야 2023 에도 있는 quatNodes(eulerToQuat · quatProd · quatInvert · quatSlerp · quatToEuler)만 쓴다.

def _quat_const(m):
    q = om.MTransformationMatrix(m).rotation(asQuaternion=True)
    return (q.x, q.y, q.z, q.w)


def _quat_prod(name, a, b):
    """a, b = 플러그 이름(str) 또는 상수 쿼터니언(tuple). 돌려주는 값: outputQuat 플러그."""
    n = cmds.createNode("quatProd", name=name)
    for slot, src in (("input1Quat", a), ("input2Quat", b)):
        if isinstance(src, tuple):
            cmds.setAttr("{0}.{1}".format(n, slot), *src)
        else:
            cmds.connectAttr(src, "{0}.{1}".format(n, slot))
    return n + ".outputQuat"


def build_append(model, joints, frames, log=None):
    """회전 부여를 노드 망으로. 돌려주는 값: 리포트 dict. 이동 부여 · 로컬 부여는 아직(리포트 · 경고)."""
    if not cmds.pluginInfo("quatNodes", q=True, loaded=True):
        cmds.loadPlugin("quatNodes", quiet=True)
    bones = model.bones
    n = len(bones)
    order, parents = cv.bone_creation_order(bones)
    total_quat = {}       # 본 -> 그 본의 총 MMD 회전 플러그
    report = {"built": [], "skipped": []}
    visiting = set()

    def short(i):
        return joints[i].split("|")[-1].split(":")[-1]

    def own_mmd(i):
        """본 i 의 자기 rotate -> MMD 로컬 회전 플러그."""
        e = cmds.createNode("eulerToQuat", name="mmd_{0}_rotQ".format(short(i)))
        cmds.connectAttr(joints[i] + ".rotate", e + ".inputRotate")
        cmds.connectAttr(joints[i] + ".rotateOrder", e + ".inputRotateOrder")
        q = e + ".outputQuat"
        if frames[i].isEquivalent(_IDENTITY, 1e-12):
            return q
        w = _quat_const(frames[i])
        w_inv = (-w[0], -w[1], -w[2], w[3])
        return _quat_prod("mmd_{0}_localQ".format(short(i)), _quat_prod("mmd_{0}_localQ0".format(short(i)), w_inv, q), w)

    def mmd_total(i):
        if i in total_quat:
            return total_quat[i]
        b = bones[i]
        if not (0 <= b.append_parent < n) or not (b.flags & pr.BONE_APPEND_ROTATE) or i in visiting:
            total_quat[i] = own_mmd(i)
            return total_quat[i]
        visiting.add(i)
        src = mmd_total(b.append_parent)
        visiting.discard(i)
        tag = short(i)
        ratio = float(b.append_ratio)
        if ratio < 0:
            inv = cmds.createNode("quatInvert", name="mmd_{0}_appendInv".format(tag))
            cmds.connectAttr(src, inv + ".inputQuat")
            src = inv + ".outputQuat"
        sl = cmds.createNode("quatSlerp", name="mmd_{0}_append".format(tag))
        cmds.setAttr(sl + ".input1Quat", 0.0, 0.0, 0.0, 1.0)
        cmds.connectAttr(src, sl + ".input2Quat")
        cmds.setAttr(sl + ".inputT", abs(ratio))
        add_long(joints[i], "mmdAppendBuilt", 1)
        appended = sl + ".outputQuat"
        # 마야: rotateAxis = W_c * Append * W_c^-1  (rotate 보다 먼저 = 부여 먼저, 자기 회전 나중)
        a_quat = appended
        if not frames[i].isEquivalent(_IDENTITY, 1e-12):
            w = _quat_const(frames[i])
            w_inv = (-w[0], -w[1], -w[2], w[3])
            a_quat = _quat_prod("mmd_{0}_appendW".format(tag), _quat_prod("mmd_{0}_appendW0".format(tag), w, appended),
                                w_inv)
        qe = cmds.createNode("quatToEuler", name="mmd_{0}_appendE".format(tag))
        cmds.connectAttr(a_quat, qe + ".inputQuat")
        cmds.setAttr(qe + ".inputRotateOrder", 0)            # rotateAxis 는 항상 XYZ
        cmds.connectAttr(qe + ".outputRotate", joints[i] + ".rotateAxis", force=True)
        # 사슬용 총 회전 = 부여 다음 자기 회전 (행벡터: quatProd(append, own))
        total_quat[i] = _quat_prod("mmd_{0}_totalQ".format(tag), appended, own_mmd(i))
        report["built"].append(b.name)
        return total_quat[i]

    for i in order:
        b = bones[i]
        if b.append_parent < 0:
            continue
        if not (0 <= b.append_parent < n):
            report["skipped"].append((b.name, "bad append parent"))
            continue
        if b.flags & pr.BONE_APPEND_ROTATE:
            mmd_total(i)
        if b.flags & pr.BONE_APPEND_MOVE:
            report["skipped"].append((b.name, "append move"))
        if b.flags & pr.BONE_APPEND_LOCAL:
            report["skipped"].append((b.name, "append local"))
    if log and report["skipped"]:
        log("[WARN] Append not built (not supported yet): {0}".format(
            ", ".join("{0} ({1})".format(cv.encode_name(nm), why) for nm, why in report["skipped"][:10])))
    return report


# ----------------------------------------------------------------------------
# IK - ikHandle (근사)
# ----------------------------------------------------------------------------
#
# MMD IK 는 CCD(반복 · 1회 각도 제한 · 링크별 회전 제한). 마야는 링크 2개 이상 = ikRPsolver, 1개 = ikSCsolver 로 근사한다.
# 핸들은 IK 본(足ＩＫ) 아래에 둔다 -> IK 본을 움직이면 발이 따라간다. 회전 제한 · 반복 수는 mmdData 에만 있다.
# 사슬은 타깃 본에서 부모를 따라 올라가 링크 본들을 만나야 한다(아니면 건너뛰고 리포트).

def build_ik(model, joints, log=None):
    bones = model.bones
    n = len(bones)
    report = {"built": [], "skipped": []}
    for k, b in enumerate(bones):
        ik = b.ik
        if ik is None:
            continue
        links = [l.bone for l in ik.links if 0 <= l.bone < n]
        if not (0 <= ik.target < n) or not links:
            report["skipped"].append((b.name, "no target or links"))
            continue
        # 타깃 -> 위로 링크 수만큼: 정확히 링크 본들이어야 한다
        chain = []
        cur = bones[ik.target].parent
        while 0 <= cur < n and len(chain) < len(links):
            chain.append(cur)
            cur = bones[cur].parent
        if sorted(chain) != sorted(links):
            report["skipped"].append((b.name, "links are not a parent chain of the target"))
            continue
        root = chain[-1]
        solver = "ikRPsolver" if len(links) >= 2 else "ikSCsolver"
        tag = joints[k].split("|")[-1].split(":")[-1]
        handle, effector = cmds.ikHandle(startJoint=joints[root], endEffector=joints[ik.target], solver=solver,
                                         name="{0}_ikHandle".format(tag))
        cmds.rename(effector, "{0}_effector".format(tag))
        handle = cmds.parent(handle, joints[k])[0]
        handle = cmds.ls(handle, long=True)[0]
        cmds.setAttr(handle + ".visibility", 0)
        add_long(handle, "mmdIKBone", k)
        report["built"].append(b.name)
    if log and report["skipped"]:
        log("[WARN] IK not built: {0}".format(
            ", ".join("{0} ({1})".format(cv.encode_name(nm), why) for nm, why in report["skipped"])))
    return report


# ----------------------------------------------------------------------------
# 표시 프레임 -> 셀렉션 셋 · Shape Editor 그룹
# ----------------------------------------------------------------------------

def _set_int_array(plug_name, values):
    data = om.MFnIntArrayData()
    _plug(plug_name).setMObject(data.create(om.MIntArray(values)))


def build_display_frames(model, joints, set_names, parent_set_name):
    """본 항목이 있는 표시 프레임마다 objectSet(조인트), 전부를 parent set 하나에. 돌려주는 값: [셋 이름]."""
    made = []
    for fi, fr in enumerate(model.display_frames):
        members = [joints[i] for kind, i in fr.items if kind == 0 and 0 <= i < len(joints) and joints[i]]
        if not members:
            continue
        s = cmds.sets(members, name=set_names[fi])
        add_string(s, "mmdName", cv.encode_name(fr.name))
        made.append(s)
    if not made:
        return []
    parent = cmds.sets(made, name=parent_set_name)
    return [parent] + made


def build_morph_groups(model, bs, aliases):
    """blendShape 타깃을 모프 패널(눈썹 · 눈 · 입 · 기타)별 Shape Editor 그룹으로. 돌려주는 값: {그룹 이름: 타깃 수}."""
    if not bs or not aliases:
        return {}
    # 별칭 -> 타깃(weight) 인덱스
    alias_index = {}
    pairs = cmds.aliasAttr(bs, q=True) or []
    for a, w in zip(pairs[0::2], pairs[1::2]):
        alias_index[a] = int(w[w.index("[") + 1:w.index("]")])
    groups = {}
    for alias, mi in aliases.items():
        panel = model.morphs[mi].panel
        name = pr.MORPH_PANELS[panel] if panel < len(pr.MORPH_PANELS) else "other"
        groups.setdefault(name, []).append(alias_index[alias])
    order = [p for p in pr.MORPH_PANELS if p in groups]
    root_children = []
    for d, name in enumerate(order, start=1):
        targets = sorted(groups[name])
        base = "{0}.targetDirectory[{1}]".format(bs, d)
        cmds.setAttr(base + ".directoryName", name, type="string")
        cmds.setAttr(base + ".parentIndex", 0)
        _set_int_array(base + ".childIndices", targets)
        for t in targets:
            cmds.setAttr("{0}.parentDirectory[{1}]".format(bs, t), d)
        root_children.append(-d)
    _set_int_array("{0}.targetDirectory[0].childIndices".format(bs), root_children)
    return dict((name, len(groups[name])) for name in order)


# ----------------------------------------------------------------------------
# 모프 -> blendShape
# ----------------------------------------------------------------------------

def build_morphs(model, mesh_shape, bs_name, morph_names, scale, progress=None):
    """버텍스 모프만 지오메트리 없는 타깃으로. 돌려주는 값: (blendShape 이름 | None, {alias: 모프 인덱스})."""
    vertex_morphs = [(i, m) for i, m in enumerate(model.morphs) if m.type == 1]
    if not vertex_morphs:
        return None, {}
    bs = cmds.blendShape(mesh_shape, name=bs_name, origin="local")[0]
    aliases = {}
    nv = len(model.vertices)
    total = len(vertex_morphs)
    for t, (mi, morph) in enumerate(vertex_morphs):
        acc = {}
        for vid, off in morph.offsets:
            if 0 <= vid < nv:
                d = cv.to_maya_point(off, scale)
                if vid in acc:
                    a = acc[vid]
                    acc[vid] = (a[0] + d[0], a[1] + d[1], a[2] + d[2])
                else:
                    acc[vid] = d
        ids = sorted(acc)
        base = "{0}.inputTarget[0].inputTargetGroup[{1}].inputTargetItem[6000]".format(bs, t)
        pa = om.MFnPointArrayData()
        _plug(base + ".inputPointsTarget").setMObject(
            pa.create(om.MPointArray([om.MPoint(*acc[v]) for v in ids])))
        sic = om.MFnSingleIndexedComponent()
        comp = sic.create(om.MFn.kMeshVertComponent)
        sic.addElements(ids)
        cl = om.MFnComponentListData()
        cobj = cl.create()
        cl.add(comp)
        _plug(base + ".inputComponentsTarget").setMObject(cobj)
        cmds.setAttr("{0}.weight[{1}]".format(bs, t), 0.0)
        alias = morph_names[mi]
        n = 1
        while cmds.attributeQuery(alias, node=bs, exists=True):
            alias = "{0}_{1}".format(morph_names[mi], n)
            n += 1
        cmds.aliasAttr(alias, "{0}.weight[{1}]".format(bs, t))
        aliases[alias] = mi
        if progress:
            progress(t + 1, total, "Morph {0}/{1}".format(t + 1, total))
    info = dict((alias, {"index": mi, "name": model.morphs[mi].name, "nameE": model.morphs[mi].name_e,
                         "panel": pr.MORPH_PANELS[model.morphs[mi].panel]
                         if model.morphs[mi].panel < len(pr.MORPH_PANELS) else model.morphs[mi].panel})
                for alias, mi in aliases.items())
    add_string(bs, "mmdMorphs", ascii_json(info))
    return bs, aliases


# ----------------------------------------------------------------------------
# 스킨
# ----------------------------------------------------------------------------

def build_skin(model, mesh_shape, joints, skin_name, dq_for_sdef=True, progress=None):
    """skinCluster + 웨이트 한 번에. 돌려주는 값: (skinCluster 이름, 리포트)."""
    bone_count = len(model.bones)
    per_vertex = []
    used = set()
    normalized = 0
    for v in model.vertices:
        w, fixed = cv.vertex_weights(v, bone_count)
        normalized += int(fixed)
        per_vertex.append(w)
        used.update(w.keys())
    report = {"normalized_vertices": normalized,
              "unweighted_vertices": sum(1 for w in per_vertex if not w),
              "sdef": sum(1 for v in model.vertices if v.weight_type == 3),
              "qdef": sum(1 for v in model.vertices if v.weight_type == 4)}
    if not used:
        return None, report
    infl_bones = sorted(used)
    if progress:
        progress(0, 3, "Binding skin")
    skin = cmds.skinCluster([joints[b] for b in infl_bones] + [mesh_shape], name=skin_name,
                            toSelectedBones=True, bindMethod=0, maximumInfluences=4,
                            obeyMaxInfluences=False, normalizeWeights=1, removeUnusedInfluence=False)[0]
    fn = oma.MFnSkinCluster(_mobject(skin))
    paths = [d.fullPathName() for d in fn.influenceObjects()]
    col_of = {}
    for b in infl_bones:
        col_of[b] = paths.index(cmds.ls(joints[b], long=True)[0])
    n_inf = len(paths)
    nv = len(model.vertices)
    weights = om.MDoubleArray(nv * n_inf, 0.0)
    for vid, w in enumerate(per_vertex):
        row = vid * n_inf
        for b, val in w.items():
            weights[row + col_of[b]] = val
    if progress:
        progress(1, 3, "Writing weights")
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.setCompleteData(nv)
    dag = _dag(mesh_shape)
    fn.setWeights(dag, comp, weight_indices(n_inf), weights, False)
    report["influences"] = n_inf

    # SDEF / QDEF -> 그 정점만 듀얼 쿼터니언 (weight blended)
    special = [i for i, v in enumerate(model.vertices) if v.weight_type in (3, 4)]
    if special and dq_for_sdef:
        cmds.setAttr(skin + ".skinningMethod", 2)
        sc = om.MFnSingleIndexedComponent()
        c2 = sc.create(om.MFn.kMeshVertComponent)
        sc.addElements(special)
        fn.setBlendWeights(dag, c2, om.MDoubleArray(len(special), 1.0))
        report["dual_quaternion_vertices"] = len(special)
    if progress:
        progress(3, 3, "Skin done")
    return skin, report
