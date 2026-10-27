# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# Framework.core.maya_fbx_exact - 모캡 FBX 를 회전까지 정확하게 임포트 (maya.cmds lazy, Maya 밖에서 import 가능)
#
# 왜 (계획서 docs/plans/A00480_FileTool_fbx_exact_import_plan.md, mayapy 2024 실측):
#   마야 FBX 임포터는 회전 키를 이전 키에 가까운 동치 오일러로 바꿀 때 rotateOrder 를 무시하고 XYZ 꼴
#   (x+180, 180-y, z+180) 을 쓴다. 비 XYZ 조인트(Vicon 모캡의 XZY Hips 등)가 ±180 근처를 넘나들면 **자세가 틀린다.**
#   FBXImportQuaternion 세 모드 다 틀리고 끄는 옵션이 없다.
#
# 어떻게:
#   1) 마야 임포터로 평소처럼 임포트 (euler 모드 = 재샘플 없음, 이동 커브는 파일 키 그대로)
#   2) 같은 FBX 를 Framework.core.fbx_binary 로 읽어 LimbNode 회전 커브를 **파일 값으로 다시 쓴다**
#   3) 회전 순서를 고려한 언랩 (euler_math) / Normalize joints = jointOrient 0 · rotateOrder xyz 로 다시 굽기
#   4) 샘플 프레임에서 파일 수식과 비교해 검증
#
# 반환 규약은 maya_fbx 와 같다 - (성공, 로그 리스트[, report]). 로그 표식은 Framework_log_levels.
# undo 는 기록하지 않는다 (키 수백만 개, 사용자 결정 2026-10-27). 대신 이름 충돌이면 [FAIL] 로 멈춰 기존 씬을 보호한다.

import math
import time

from Framework.core import fbx_binary
from Framework.core import euler_math as em
from Framework.core import maya_fbx

#: FBX 회전 순서 문자열 <-> 마야 rotateOrder 인덱스
MAYA_ORDER_INDEX = {"XYZ": 0, "YZX": 1, "ZXY": 2, "XZY": 3, "YXZ": 4, "ZYX": 5}
MAYA_ORDER_NAME = {v: k for k, v in MAYA_ORDER_INDEX.items()}

ROTATE_ATTRS = (("X", "rotateX"), ("Y", "rotateY"), ("Z", "rotateZ"))
TRANSLATE_ATTRS = (("X", "translateX"), ("Y", "translateY"), ("Z", "translateZ"))

#: "잘못된 회전" 판정 - ① 마야 값이 파일 값에 XYZ 동치 (x+180, 180-y, z+180) 를 적용한 값과 FLIP_SIGNATURE_DEG 안에서
#: 같으면(임포터 버그의 지문 - 이 경우 자세 차이가 1° 미만인 프레임도 있다) ② 또는 자세가 WRONG_DEG 보다 다르면.
#: 그 밖의 차이(임포터의 키 감소 · 탄젠트, 사용자 씬에서 최대 0.022°)는 미세 차이로 따로 센다.
FLIP_SIGNATURE_DEG = 1e-3
WRONG_DEG = 1.0

#: 검증 허용치
VERIFY_DEG = 1e-3
VERIFY_CM = 1e-3
#: 커브 수준 검증에서 조인트당 샘플 프레임 수 (대략)
VERIFY_SAMPLES = 200


def _cmds():
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


def _mel():
    try:
        import maya.mel as mel
        return mel
    except Exception:
        return None


# ================================================================
# 스캔 (씬을 건드리지 않는다)
# ================================================================

def scan(path):
    """FBX 를 읽어 요약. 반환 (info dict | None, 로그). info: version · settings · skeletons[(이름, 조인트 수)] · counts."""
    try:
        doc = fbx_binary.read(path)
    except (IOError, OSError) as exc:
        return None, ["[FAIL] Cannot read the file : {0}".format(exc)]
    except fbx_binary.FbxError as exc:
        return None, ["[FAIL] {0}".format(exc)]
    info = {
        "path": path,
        "version": doc.version,
        "settings": dict(doc.settings),
        "skeletons": [(name, n) for _mid, name, n in doc.skeleton_roots()],
        "counts": dict(doc.counts),
        "stacks": len(doc.stacks),
        "layers": doc.n_layers,
    }
    logs = ["[Info] " + describe(info)]
    if not info["skeletons"]:
        logs.append("[WARN] No skeleton (LimbNode) in this file.")
    if info["stacks"] > 1 or info["layers"] > 1:
        logs.append("[WARN] {0} animation stacks / {1} layers - only the first is used.".format(
            info["stacks"], info["layers"]))
    return info, logs


def describe(info):
    """한 줄 요약 - 'FBX 7700, Z-up, cm, 60 fps, frames 1-6285, 5 skeletons, 365 joints, ...' (로그는 ASCII 만)."""
    s = info["settings"]
    unit = "cm" if abs(s["unit_cm"] - 1.0) < 1e-9 else "{0:g} cm/unit".format(s["unit_cm"])
    counts = info["counts"]
    parts = [
        "FBX {0}".format(info["version"]),
        "{0}-up".format(s["up_axis"]),
        unit,
        "{0:g} fps".format(s["fps"]),
        "frames {0:g}-{1:g}".format(s["start"], s["stop"]),
        "{0} skeleton{1}".format(len(info["skeletons"]), "" if len(info["skeletons"]) == 1 else "s"),
        "{0} joints".format(counts.get("LimbNode", 0)),
    ]
    for kind, label in (("Marker", "markers"), ("Camera", "cameras"), ("Mesh", "meshes")):
        if counts.get(kind):
            parts.append("{0} {1}".format(counts[kind], label))
    return ", ".join(parts)


# ================================================================
# 매핑 - FBX 모델 -> 마야 노드
# ================================================================

def _match_child(cmds, maya_parent, name):
    """maya_parent 의 자식 중 (네임스페이스를 뗀) 이름이 name 인 것."""
    for child in cmds.listRelatives(maya_parent, children=True, fullPath=True, type="transform") or []:
        if child.split("|")[-1].split(":")[-1] == name:
            return child
    return None


def map_skeleton(doc, root_id, maya_root):
    """root 아래 모든 모델 -> 마야 경로. 반환 ({model id: fullPath}, [못 찾은 FBX 경로])."""
    cmds = _cmds()
    mapping = {root_id: maya_root}
    missing = []
    stack = [(root_id, maya_root)]
    while stack:
        mid, maya_node = stack.pop()
        for child in doc.children.get(mid, []):
            name = fbx_binary.maya_node_name(doc.models[child].short)
            found = _match_child(cmds, maya_node, name) if maya_node else None
            if found:
                mapping[child] = found
            elif doc.models[child].kind == "LimbNode" or any(
                    doc.models[d].kind == "LimbNode" for d in doc.descendants(child)):
                missing.append("|".join([doc.models[root_id].short] + doc.path_from(root_id, child)))
            stack.append((child, found))
    return mapping, missing


def _non_skeleton_branches(doc, root_id):
    """root 아래에서 LimbNode 가 하나도 없는 가지의 맨 위 모델들 (마커 · 카메라 등)."""
    out = []
    stack = list(doc.children.get(root_id, []))
    while stack:
        mid = stack.pop()
        if doc.models[mid].kind == "LimbNode":
            stack.extend(doc.children.get(mid, []))
            continue
        if any(doc.models[d].kind == "LimbNode" for d in doc.descendants(mid)):
            stack.extend(doc.children.get(mid, []))
        else:
            out.append(mid)
    return out


# ================================================================
# 마야 커브 읽기 · 쓰기
# ================================================================

def _input_curve(cmds, plug):
    """plug 에 직접 물린 animCurve 이름. animCurve 가 아닌 입력이면 False, 입력이 없으면 None."""
    src = cmds.listConnections(plug, source=True, destination=False, skipConversionNodes=True) or []
    if not src:
        return None
    node = src[0]
    if cmds.nodeType(node).startswith("animCurve"):
        return node
    return False


def _curve_track(cmds, curve):
    frames = cmds.keyframe(curve, query=True, timeChange=True) or []
    values = cmds.keyframe(curve, query=True, valueChange=True) or []
    return fbx_binary.Track(list(frames), list(values), "linear")


def _values_on(track, frames):
    if track.frames == frames:
        return list(track.values)
    return [track.value_at(f) for f in frames]


def _write_curve(cmds, plug_name, frames, values, interp, angular=True):
    """plug 의 기존 animCurve 를 지우고 새 커브 (MFnAnimCurve.addKeys 한 번).

    angular=True 면 values 는 도(-> 라디안), False 면 cm (마야 내부 거리 단위).
    """
    from maya.api import OpenMaya as om, OpenMayaAnim as oma
    old = _input_curve(cmds, plug_name)
    if old:
        cmds.delete(old)
    sel = om.MSelectionList()
    sel.add(plug_name)
    plug = sel.getPlug(0)
    fn = oma.MFnAnimCurve()
    fn.create(plug, oma.MFnAnimCurve.kAnimCurveTA if angular else oma.MFnAnimCurve.kAnimCurveTL)
    unit = om.MTime.uiUnit()
    times = om.MTimeArray([om.MTime(f, unit) for f in frames])
    scale = math.pi / 180.0 if angular else 1.0
    vals = om.MDoubleArray([v * scale for v in values])
    tangent = {
        "constant": oma.MFnAnimCurve.kTangentStep,
        "cubic": oma.MFnAnimCurve.kTangentAuto,
    }.get(interp, oma.MFnAnimCurve.kTangentLinear)
    fn.addKeys(times, vals, tangent, tangent)
    return len(frames)


def _evaluator(cmds, plug_name, angular=True):
    """frame -> 도 (angular) / cm. 커브가 있으면 MFnAnimCurve.evaluate, 없으면 정적 값."""
    from maya.api import OpenMaya as om, OpenMayaAnim as oma
    curve = _input_curve(cmds, plug_name)
    if not curve:
        value = cmds.getAttr(plug_name)
        return lambda frame: value
    sel = om.MSelectionList()
    sel.add(curve)
    fn = oma.MFnAnimCurve(sel.getDependNode(0))
    unit = om.MTime.uiUnit()
    scale = 180.0 / math.pi if angular else 1.0
    return lambda frame: fn.evaluate(om.MTime(frame, unit)) * scale


# ================================================================
# 핵심 - 회전 커브 복원
# ================================================================

class _Job(object):
    __slots__ = ("mid", "node", "name", "order", "pre", "post", "tracks", "jo", "ra", "frames", "t_tracks")


def _runs(bad_frames):
    """[1, 2, 3, 7, 8] -> [(1, 3), (7, 8)]"""
    runs = []
    for f in bad_frames:
        if runs and f - runs[-1][1] <= 1.0 + 1e-9:
            runs[-1][1] = f
        else:
            runs.append([f, f])
    return [(a, b) for a, b in runs]


def _fmt_runs(runs, limit=3):
    text = ", ".join("{0:g}-{1:g}".format(a, b) if a != b else "{0:g}".format(a) for a, b in runs[:limit])
    if len(runs) > limit:
        text += ", +{0} more".format(len(runs) - limit)
    return text


def _collect_jobs(cmds, doc, root_id, mapping, mode, logs):
    """복원할 조인트 목록. 파일과 맞지 않는 조인트는 [SKIP] 로그."""
    jobs, skipped = [], []
    for mid in [root_id] + doc.descendants(root_id):
        model = doc.models[mid]
        node = mapping.get(mid)
        if model.kind != "LimbNode" or not node:
            continue
        if cmds.nodeType(node) != "joint":
            skipped.append((node, "not a joint"))
            continue
        order = doc.rotation_order(mid)
        ro = cmds.getAttr(node + ".rotateOrder")
        jo = tuple(cmds.getAttr(node + ".jointOrient")[0])
        ra = tuple(cmds.getAttr(node + ".rotateAxis")[0])
        pre, post = doc.pre_rotation(mid), doc.post_rotation(mid)
        if any(abs(v) > 1e-6 for v in post):
            skipped.append((node, "PostRotation is not supported yet"))
            continue
        if ro != MAYA_ORDER_INDEX[order]:
            skipped.append((node, "rotateOrder {0} differs from the file ({1})".format(MAYA_ORDER_NAME.get(ro, ro), order)))
            continue
        if any(abs(a - b) > 1e-3 for a, b in zip(jo, pre)) or any(abs(v) > 1e-6 for v in ra):
            skipped.append((node, "jointOrient / rotateAxis differ from the file PreRotation"))
            continue
        blocked = [attr for _axis, attr in ROTATE_ATTRS + TRANSLATE_ATTRS
                   if _input_curve(cmds, node + "." + attr) is False]
        if blocked:
            skipped.append((node, "rotate / translate is driven by a non-curve input"))
            continue
        job = _Job()
        job.mid, job.node, job.name = mid, node, model.short
        job.order, job.pre, job.post, job.jo, job.ra = order, pre, post, jo, ra
        job.tracks = doc.channel(mid, "Lcl Rotation")
        job.t_tracks = doc.channel(mid, "Lcl Translation")
        frames = set()
        for track in job.tracks.values():
            frames.update(track.frames)
        job.frames = sorted(frames)
        jobs.append(job)
    for node, reason in skipped[:10]:
        logs.append("[SKIP] {0} : {1}".format(node.split("|")[-1], reason))
    if len(skipped) > 10:
        logs.append("[SKIP] ... {0} more joints skipped.".format(len(skipped) - 10))
    return jobs, skipped


def _file_triples(doc, job):
    """job.frames 위의 파일 회전 (xs, ys, zs) - 커브 없는 축은 정적 값."""
    static = doc.static(job.mid, "Lcl Rotation")
    out = []
    for i, axis in enumerate(("X", "Y", "Z")):
        track = job.tracks.get(axis)
        out.append(_values_on(track, job.frames) if track else [static[i]] * len(job.frames))
    return out


def _diagnose(cmds, doc, job, file_xyz):
    """마야에 지금 들어 있는 회전이 파일과 다른 프레임들 (자세 기준). 반환 [(프레임, 각도, 잘못된 회전 여부)]."""
    maya_xyz = []
    for i, (axis, attr) in enumerate(ROTATE_ATTRS):
        curve = _input_curve(cmds, job.node + "." + attr)
        if curve:
            track = _curve_track(cmds, curve)
            if track.frames == job.frames:
                maya_xyz.append(track.values)
            else:  # 키가 줄어 있으면 마야 탄젠트 그대로 평가
                evaluate = _evaluator(cmds, job.node + "." + attr)
                maya_xyz.append([evaluate(f) for f in job.frames])
        else:
            maya_xyz.append([cmds.getAttr(job.node + "." + attr)] * len(job.frames))
    bad = []
    pre_m = em.matrix(job.pre, "XYZ")
    jo_m = em.matrix(job.jo, "XYZ")
    maya_order = MAYA_ORDER_NAME[cmds.getAttr(job.node + ".rotateOrder")]
    fx, fy, fz = file_xyz
    mx, my, mz = maya_xyz
    for i, frame in enumerate(job.frames):
        a = (fx[i], fy[i], fz[i])
        b = (mx[i], my[i], mz[i])
        if em.same_angles(a, b) and em.same_angles(job.pre, job.jo):
            continue
        want = em.mat_mul(pre_m, em.matrix(a, job.order))
        have = em.mat_mul(jo_m, em.matrix(b, maya_order))
        deg = em.angle_between(want, have)
        if deg > VERIFY_DEG:
            wrong = deg > WRONG_DEG or em.same_angles(b, em.alternate(a, "XYZ"), FLIP_SIGNATURE_DEG)
            bad.append((frame, deg, wrong))
    return bad


def _translation_diff(cmds, job):
    """파일 이동 커브 vs 마야 translate - 최대 차이(cm)."""
    worst = 0.0
    for axis, attr in TRANSLATE_ATTRS:
        track = job.t_tracks.get(axis)
        if track is None:
            continue
        evaluate = _evaluator(cmds, job.node + "." + attr, angular=False)
        for frame, value in zip(track.frames, track.values):
            worst = max(worst, abs(evaluate(frame) - value))
    return worst


def _rebuild_translation(cmds, job):
    """파일에 이동 커브가 있는 축만 파일 키로 다시 쓴다 (cm). 반환 쓴 키 수."""
    keys = 0
    for axis, attr in TRANSLATE_ATTRS:
        track = job.t_tracks.get(axis)
        if track is None:
            continue
        kind = track.interp_kind()
        keys += _write_curve(cmds, job.node + "." + attr, track.frames, track.values,
                             kind if kind in ("linear", "constant", "cubic") else "linear", angular=False)
    return keys


def _rebuild(cmds, doc, job, file_xyz, unwrap, normalize, report):
    """job 의 회전 커브를 파일 값으로 다시 쓴다 (+ 언랩 / 정규화). 반환 쓴 키 수."""
    if not job.frames:
        if normalize:
            # 애니 없는 조인트 - 정적 값만 XYZ 로
            static = doc.static(job.mid, "Lcl Rotation")
            nx, ny, nz = em.normalize_xyz([static[0]], [static[1]], [static[2]], job.order, job.jo, job.ra)
            for value, (_axis, attr) in zip((nx[0], ny[0], nz[0]), ROTATE_ATTRS):
                cmds.setAttr(job.node + "." + attr, value)
            _set_normalized(cmds, job.node)
        return 0
    kinds = {t.interp_kind() for t in job.tracks.values()}
    interp = kinds.pop() if len(kinds) == 1 else "linear"
    if interp in ("cubic", "mixed"):
        report["cubic"] += 1
    keys = 0
    if normalize:
        xs, ys, zs = file_xyz
        nx, ny, nz = em.normalize_xyz(xs, ys, zs, job.order, job.jo, job.ra)
        for values, (_axis, attr) in zip((nx, ny, nz), ROTATE_ATTRS):
            keys += _write_curve(cmds, job.node + "." + attr, job.frames, values, interp)
        _set_normalized(cmds, job.node)
        return keys
    full = len(job.tracks) == 3 and all(t.frames == job.frames for t in job.tracks.values())
    if unwrap and full:
        before = sum(em.count_jumps(t.values) for t in job.tracks.values())
        xs, ys, zs = em.unwrap_triples(file_xyz[0], file_xyz[1], file_xyz[2], job.order)
        report["jumps"] += before
        channels = {"X": xs, "Y": ys, "Z": zs}
    else:
        channels = {}
        for axis, track in job.tracks.items():
            values = list(track.values)
            if unwrap:
                report["jumps"] += em.count_jumps(values)
                values = em.unwrap_single(values)
            channels[axis] = values
    for axis, attr in ROTATE_ATTRS:
        track = job.tracks.get(axis)
        if track is None:
            continue
        keys += _write_curve(cmds, job.node + "." + attr, track.frames, channels[axis], interp)
    return keys


def _set_normalized(cmds, node):
    cmds.setAttr(node + ".jointOrient", 0.0, 0.0, 0.0)
    cmds.setAttr(node + ".rotateAxis", 0.0, 0.0, 0.0)
    cmds.setAttr(node + ".rotateOrder", 0)


def _verify_curves(cmds, doc, jobs):
    """커브 수준 검증 - 샘플 프레임마다 파일 Rpre·R(order)·Rpost⁻¹ vs 마야 JO·R(ro)·RA. 반환 (최대 각도, [(각도, 조인트, 프레임)])."""
    worst = []
    max_deg = 0.0
    for job in jobs:
        frames = job.frames or [doc.settings["start"]]
        step = max(1, len(frames) // VERIFY_SAMPLES)
        sample = frames[::step]
        if frames[-1] not in sample:
            sample.append(frames[-1])
        evals = [_evaluator(cmds, job.node + "." + attr) for _axis, attr in ROTATE_ATTRS]
        jo = cmds.getAttr(job.node + ".jointOrient")[0]
        ra = cmds.getAttr(job.node + ".rotateAxis")[0]
        order = MAYA_ORDER_NAME[cmds.getAttr(job.node + ".rotateOrder")]
        jo_m, ra_m = em.matrix(jo, "XYZ"), em.matrix(ra, "XYZ")
        pre_m = em.matrix(job.pre, "XYZ")
        post_t = em.transpose(em.matrix(job.post, "XYZ"))
        for frame in sample:
            v = doc.value_at(job.mid, "Lcl Rotation", frame, channel=job.tracks)
            want = em.mat_mul(em.mat_mul(pre_m, em.matrix(v, job.order)), post_t)
            have = em.mat_mul(em.mat_mul(jo_m, em.matrix([e(frame) for e in evals], order)), ra_m)
            deg = em.angle_between(want, have)
            if deg > max_deg:
                max_deg = deg
            if deg > VERIFY_DEG:
                worst.append((deg, job.node.split("|")[-1], frame))
    worst.sort(reverse=True)
    return max_deg, worst[:5]


def _local4(doc, mid, frame, cache):
    """FBX 로컬 4x4 (열 벡터, 행 리스트) - T · Rpre · R · Rpost⁻¹ · S."""
    tracks = cache.get(mid)
    if tracks is None:
        tracks = cache[mid] = (doc.channel(mid, "Lcl Translation"), doc.channel(mid, "Lcl Rotation"),
                               doc.channel(mid, "Lcl Scaling"))
    t = doc.value_at(mid, "Lcl Translation", frame, channel=tracks[0])
    r = doc.value_at(mid, "Lcl Rotation", frame, channel=tracks[1])
    s = doc.value_at(mid, "Lcl Scaling", frame, default=(1.0, 1.0, 1.0), channel=tracks[2])
    m = em.mat_mul(em.mat_mul(em.matrix(doc.pre_rotation(mid), "XYZ"), em.matrix(r, doc.rotation_order(mid))),
                   em.transpose(em.matrix(doc.post_rotation(mid), "XYZ")))
    return [[m[0][0] * s[0], m[0][1] * s[1], m[0][2] * s[2], t[0]],
            [m[1][0] * s[0], m[1][1] * s[1], m[1][2] * s[2], t[1]],
            [m[2][0] * s[0], m[2][1] * s[1], m[2][2] * s[2], t[2]],
            [0.0, 0.0, 0.0, 1.0]]


def _mul4(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _verify_world(cmds, doc, root_id, mapping, frames):
    """DG 수준 스모크 - 루트 기준 조인트 위치를 파일 계산값과 비교. 반환 최대 cm."""
    from maya.api import OpenMaya as om
    maya_root = mapping[root_id]
    limbs = [mid for mid in doc.descendants(root_id) if doc.models[mid].kind == "LimbNode" and mid in mapping]
    worst = 0.0
    cache = {}
    current = cmds.currentTime(query=True)
    try:
        for frame in frames:
            cmds.currentTime(frame, edit=True)
            root_inv = om.MMatrix(cmds.xform(maya_root, query=True, worldSpace=True, matrix=True)).inverse()
            world = {root_id: None}     # 루트 기준이라 루트 자신은 단위 행렬로 본다

            def rel_world(mid):
                if mid not in world:
                    parent = doc.parent.get(mid, 0)
                    local = _local4(doc, mid, frame, cache)
                    up = rel_world(parent) if parent in doc.models else None
                    world[mid] = _mul4(up, local) if up is not None else local
                return world[mid]

            for mid in limbs:
                rel_world(mid)
                rel = om.MMatrix(cmds.xform(mapping[mid], query=True, worldSpace=True, matrix=True)) * root_inv
                have = (rel[12], rel[13], rel[14])
                want = (world[mid][0][3], world[mid][1][3], world[mid][2][3])
                worst = max(worst, math.sqrt(sum((a - b) ** 2 for a, b in zip(have, want))))
    finally:
        cmds.currentTime(current, edit=True)
    return worst


def _repair(cmds, doc, targets, unwrap, normalize, verify, mode, logs, progress):
    """targets = [(root_id, maya_root)]. 회전 커브 진단 · 복원 · 검증. 반환 report."""
    report = {"flipped": {}, "curves": 0, "keys": 0, "jumps": 0, "cubic": 0, "joints": 0, "skipped": 0,
              "minor": 0, "minor_deg": 0.0, "t_curves": 0, "t_diff_cm": 0.0,
              "verify_deg": None, "verify_cm": None}
    doc.build_channel_index()
    # 이동은 파일 cm · 씬 cm 일 때만 다시 쓴다 (단위 변환을 추측하지 않는다)
    do_translation = abs(doc.settings["unit_cm"] - 1.0) < 1e-9 and cmds.currentUnit(query=True, linear=True) == "cm"
    if not do_translation:
        logs.append("[Info] Translation curves are left as imported (file or scene unit is not cm).")
    all_jobs = []
    t0 = time.time()
    for root_id, maya_root in targets:
        root_name = doc.models[root_id].short
        mapping, missing = map_skeleton(doc, root_id, maya_root)
        if missing:
            logs.append("[WARN] {0} : {1} joints not found in the scene (e.g. {2}).".format(
                root_name, len(missing), missing[0]))
        jobs, skipped = _collect_jobs(cmds, doc, root_id, mapping, mode, logs)
        report["skipped"] += len(skipped)
        if progress:
            progress("[Info] {0} : checking {1} joints ...".format(root_name, len(jobs)))
        flipped = []
        for job in jobs:
            file_xyz = _file_triples(doc, job)
            if job.tracks:
                bad = _diagnose(cmds, doc, job, file_xyz)
                flips = [frame for frame, _deg, wrong in bad if wrong]
                minor = [deg for _frame, deg, wrong in bad if not wrong]
                if flips:
                    flipped.append((job.name, _runs(flips)))
                if minor:
                    report["minor"] += 1
                    report["minor_deg"] = max(report["minor_deg"], max(minor))
            if do_translation and job.t_tracks:
                report["t_diff_cm"] = max(report["t_diff_cm"], _translation_diff(cmds, job))
                report["keys"] += _rebuild_translation(cmds, job)
                report["t_curves"] += len(job.t_tracks)
            keys = _rebuild(cmds, doc, job, file_xyz, unwrap, normalize, report)
            if keys:
                report["curves"] += 3 if normalize else len(job.tracks)
                report["keys"] += keys
        report["joints"] += len(jobs)
        report["flipped"][root_name] = flipped
        if flipped:
            text = ", ".join("{0} ({1})".format(name, _fmt_runs(runs)) for name, runs in flipped[:6])
            if len(flipped) > 6:
                text += ", +{0} more".format(len(flipped) - 6)
            logs.append("[WARN] {0} : Maya had wrong rotations on {1} joint{2} - {3}. Rebuilt from the file.".format(
                root_name, len(flipped), "" if len(flipped) == 1 else "s", text))
        else:
            logs.append("[Info] {0} : no wrong rotations found.".format(root_name))
        all_jobs.append((root_id, mapping, jobs))
    if report["minor"]:
        logs.append("[Info] {0} joints differed slightly from the file (max {1:.3f} deg, reduced keys / tangents)"
                    " - rebuilt too.".format(report["minor"], report["minor_deg"]))
    if report["t_diff_cm"] > VERIFY_CM:
        logs.append("[Info] Translation differed from the file by up to {0:.4f} cm - rebuilt too.".format(
            report["t_diff_cm"]))
    logs.append("[OK] Curves rebuilt from the file : {0} joints, {1} rotation + {2} translation curves, {3:,} keys"
                " ({4:.1f}s).".format(report["joints"], report["curves"], report["t_curves"], report["keys"],
                                      time.time() - t0))
    if normalize:
        logs.append("[OK] Normalized joints : jointOrient 0, rotateOrder xyz.")
    elif unwrap and report["jumps"]:
        logs.append("[OK] Unwrapped {0} jumps over 180 deg (rotate order aware).".format(report["jumps"]))
    if report["cubic"]:
        logs.append("[WARN] {0} joints have cubic keys - written with auto tangents (approximate).".format(report["cubic"]))

    if verify:
        t1 = time.time()
        if progress:
            progress("[Info] Verifying against the file ...")
        max_deg, worst = 0.0, []
        max_cm = 0.0
        s = doc.settings
        frames = sorted({s["start"], s["stop"], float(round((s["start"] + s["stop"]) / 2.0))})
        for root_id, mapping, jobs in all_jobs:
            d, w = _verify_curves(cmds, doc, jobs)
            max_deg = max(max_deg, d)
            worst.extend(w)
            max_cm = max(max_cm, _verify_world(cmds, doc, root_id, mapping, frames))
        report["verify_deg"], report["verify_cm"] = max_deg, max_cm
        if max_deg <= VERIFY_DEG and max_cm <= VERIFY_CM:
            logs.append("[OK] Verify : max {0:.4f} deg rotation, {1:.4f} cm position ({2:.1f}s).".format(
                max_deg, max_cm, time.time() - t1))
        else:
            worst.sort(reverse=True)
            logs.append("[FAIL] Verify : max {0:.4f} deg rotation, {1:.4f} cm position.".format(max_deg, max_cm))
            for deg, name, frame in worst[:5]:
                logs.append("[FAIL]   {0} frame {1:g} : {2:.4f} deg".format(name, frame, deg))
    return report


# ================================================================
# 공개 API
# ================================================================

class _undo_off(object):
    """undo 를 기록하지 않는다 (기존 큐는 그대로 - stateWithoutFlush)."""

    def __enter__(self):
        cmds = _cmds()
        self._was = cmds.undoInfo(query=True, state=True)
        if self._was:
            cmds.undoInfo(stateWithoutFlush=False)
        return self

    def __exit__(self, *args):
        if self._was:
            _cmds().undoInfo(stateWithoutFlush=True)
        return False


def import_exact(path, skeletons=None, skeletons_only=True, unwrap=True, normalize=True, verify=True, progress=None):
    """FBX 를 임포트하고 LimbNode 회전 커브를 파일 값으로 다시 쓴다.

    skeletons : 임포트할 스켈레톤 루트 이름 목록 (None = 전부). 나머지 스켈레톤은 임포트 뒤 지운다.
    skeletons_only : 스켈레톤 밖의 루트(카메라 · System)와 스켈레톤 루트 아래 조인트 없는 가지(마커)를 지운다.
    progress : 긴 작업 중 부를 콜백(로그 한 줄) - UI 가 로그창에 쌓고 이벤트를 돌린다.
    반환 (ok, logs, report).
    """
    cmds, mel = _cmds(), _mel()
    if cmds is None:
        return False, ["[FAIL] Maya not available."], {}
    t_start = time.time()
    info, logs = scan(path)
    if info is None:
        return False, logs, {}
    doc = fbx_binary.read(path)
    roots = doc.skeleton_roots()
    wanted = set(skeletons) if skeletons is not None else {name for _mid, name, _n in roots}
    chosen = [(mid, name) for mid, name, _n in roots if name in wanted]
    if not chosen:
        logs.append("[FAIL] No skeleton selected.")
        return False, logs, {}

    # 사전 검사 - 같은 이름이 이미 씬 최상위에 있으면 매핑이 꼬인다
    clash = [name for _mid, name in chosen if cmds.objExists("|" + fbx_binary.maya_node_name(name))]
    if clash:
        logs.append("[FAIL] The scene already has {0}. Import into a new scene, or rename / delete it first.".format(
            ", ".join("'{0}'".format(n) for n in clash)))
        return False, logs, {}

    ok, plugin_logs = maya_fbx.ensure_fbx_plugin()
    logs.extend(plugin_logs)
    if not ok:
        return False, logs, {}

    with _undo_off():
        logs.append("[Info] Undo is not recorded for this import.")
        before_asm = set(cmds.ls(assemblies=True, long=True) or [])
        before_ns = set(cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True) or [])
        fps_before = cmds.currentUnit(query=True, time=True)
        if progress:
            progress("[Info] Importing with the Maya FBX importer ...")
        t0 = time.time()
        with maya_fbx.import_options(quaternion="euler", mode="add"):
            try:
                mel.eval('FBXImport -f "{0}"'.format(path.replace("\\", "/")))
            except RuntimeError as exc:
                logs.append("[FAIL] FBX import failed : {0}".format(exc))
                return False, logs, {}
        new_asm = [a for a in (cmds.ls(assemblies=True, long=True) or []) if a not in before_asm]
        fps_after = cmds.currentUnit(query=True, time=True)
        logs.append("[Info] Imported in {0:.1f}s.{1}".format(
            time.time() - t0, "" if fps_after == fps_before else
            " Scene time unit {0} -> {1} (from the file).".format(fps_before, fps_after)))

        # 새 루트 <-> FBX 최상위 모델
        by_name = {a.split("|")[-1]: a for a in new_asm}
        targets, removed = [], {"skeletons": 0, "roots": 0, "branches": 0}
        to_delete = []
        for mid in doc.children.get(0, []):
            node = by_name.get(fbx_binary.maya_node_name(doc.models[mid].short))
            if node is None:
                continue
            is_skeleton = any(mid == r[0] for r in roots)
            if is_skeleton and doc.models[mid].short in wanted:
                targets.append((mid, node))
            elif is_skeleton:
                to_delete.append(node)
                removed["skeletons"] += 1
            elif skeletons_only:
                to_delete.append(node)
                removed["roots"] += 1
        if skeletons_only:
            for mid, node in targets:
                mapping, _missing = map_skeleton(doc, mid, node)
                for branch in _non_skeleton_branches(doc, mid):
                    if branch in mapping:
                        to_delete.append(mapping[branch])
                        removed["branches"] += 1
        if to_delete:
            cmds.delete([n for n in to_delete if cmds.objExists(n)])
        removed["namespaces"] = _remove_new_empty_namespaces(cmds, before_ns)
        parts = []
        for key, label in (("skeletons", "unselected skeletons"), ("branches", "marker / non-joint branches"),
                           ("roots", "other top nodes (cameras ...)"), ("namespaces", "empty namespaces")):
            if removed[key]:
                parts.append("{0} {1}".format(removed[key], label))
        if parts:
            logs.append("[Info] Removed : " + ", ".join(parts) + ".")

        report = _repair(cmds, doc, targets, unwrap, normalize, verify, "import", logs, progress)

        s = doc.settings
        cmds.playbackOptions(minTime=s["start"], maxTime=s["stop"], animationStartTime=s["start"],
                             animationEndTime=s["stop"])
    ok = not any(line.startswith("[FAIL]") for line in logs)
    logs.append("[{0}] Done in {1:.1f}s - {2}.".format(
        "OK" if ok else "WARN", time.time() - t_start, ", ".join(n for _m, n in chosen)))
    report["roots"] = [node for _mid, node in targets]
    return ok, logs, report


def _remove_new_empty_namespaces(cmds, before):
    """이번 임포트가 만든 빈 네임스페이스를 지운다 (깊은 것부터). 반환 지운 수."""
    now = cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True) or []
    new = [ns for ns in now if ns not in before and ns not in ("UI", "shared")]
    new.sort(key=lambda ns: ns.count(":"), reverse=True)
    count = 0
    for ns in new:
        try:
            if cmds.namespaceInfo(ns, listNamespace=True):
                continue
            cmds.namespace(removeNamespace=ns)
            count += 1
        except RuntimeError:
            pass
    return count


def fix_scene_from_fbx(path, roots=None, unwrap=True, normalize=True, verify=True, progress=None):
    """이미 마야로 임포트해 둔 씬의 회전 커브를 FBX 원본으로 고친다.

    roots : 고칠 씬 노드 (선택한 루트). None 이면 FBX 스켈레톤 이름과 같은 최상위 노드.
    rotateOrder / jointOrient 가 파일과 다른 조인트(이미 정규화한 씬 등)는 [SKIP].
    반환 (ok, logs, report).
    """
    cmds = _cmds()
    if cmds is None:
        return False, ["[FAIL] Maya not available."], {}
    t_start = time.time()
    info, logs = scan(path)
    if info is None:
        return False, logs, {}
    doc = fbx_binary.read(path)
    file_roots = {fbx_binary.maya_node_name(name): mid for mid, name, _n in doc.skeleton_roots()}
    targets = []
    if roots:
        for node in roots:
            long_name = (cmds.ls(node, long=True) or [node])[0]
            short = long_name.split("|")[-1].split(":")[-1]
            if short in file_roots:
                targets.append((file_roots[short], long_name))
            else:
                logs.append("[SKIP] {0} : no skeleton named '{1}' in the file.".format(long_name, short))
    else:
        for top in cmds.ls(assemblies=True, long=True) or []:
            short = top.split("|")[-1].split(":")[-1]
            if short in file_roots:
                targets.append((file_roots[short], top))
    if not targets:
        logs.append("[FAIL] No matching skeleton in the scene. Select the root (e.g. '{0}').".format(
            next(iter(file_roots), "root")))
        return False, logs, {}

    # 키 시간이 파일과 다르면(리타임 · 오프셋) 고치지 않는다 - 조인트 단위로 _collect_jobs 뒤에 검사
    with _undo_off():
        logs.append("[Info] Undo is not recorded for this fix.")
        _check_timing(cmds, doc, targets, logs)
        if any(line.startswith("[FAIL]") for line in logs):
            return False, logs, {}
        report = _repair(cmds, doc, targets, unwrap, normalize, verify, "fix", logs, progress)
    ok = not any(line.startswith("[FAIL]") for line in logs)
    logs.append("[{0}] Done in {1:.1f}s - {2}.".format(
        "OK" if ok else "WARN", time.time() - t_start, ", ".join(t[1].split("|")[-1] for t in targets)))
    return ok, logs, report


def _check_timing(cmds, doc, targets, logs):
    """씬 커브의 키 시간이 파일 키 시간의 부분집합이 아니면 [FAIL] - 리타임 · 오프셋한 씬을 파일 키로 덮으면 작업이 밀린다.

    부분집합은 괜찮다 - 마야 임포터가 같은 값이 이어지는 키를 줄인다(사용자 씬 Hips rx 6276/6285 키, 2026-10-27 실측).
    """
    doc.build_channel_index()
    for root_id, maya_root in targets:
        mapping, _missing = map_skeleton(doc, root_id, maya_root)
        for mid in [root_id] + doc.descendants(root_id):
            if doc.models[mid].kind != "LimbNode" or mid not in mapping:
                continue
            rot, trans = doc.channel(mid, "Lcl Rotation"), doc.channel(mid, "Lcl Translation")
            for tracks, axis, attr in [(rot, a, n) for a, n in ROTATE_ATTRS] + [(trans, a, n) for a, n in TRANSLATE_ATTRS]:
                track = tracks.get(axis)
                curve = _input_curve(cmds, mapping[mid] + "." + attr) if track else None
                if not curve:
                    continue
                frames = cmds.keyframe(curve, query=True, timeChange=True) or []
                file_frames = {round(f, 4) for f in track.frames}
                if any(round(f, 4) not in file_frames for f in frames):
                    logs.append("[FAIL] {0} : key times differ from the file (retimed or offset?) - not fixed.".format(
                        mapping[mid].split("|")[-1]))
                    return
