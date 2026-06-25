# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-25
# A00300_meshDoctor - 읽기 전용 메시 진단 (maya.cmds + maya.api.OpenMaya 2.0)
#
# 메시를 절대 수정하지 않는다. 선택 메시의 토폴로지/정점 무결성을 검사해
# {check, severity, count, samples, message} 리스트로 결과를 모은다.
#
# 두 가지 대표 증상에 맞춘 진단:
#   증상 1 (빈 공간 클릭해도 선택됨)  -> bounding box 팽창: NaN/Inf 정점, 떠돌이 정점,
#                                       intermediate(orig) shape.
#   증상 2 (weight Transfer 부분 실패/일그러짐) -> 토폴로지 손상: non-manifold, lamina,
#                                       zero-area face, zero-length edge, 겹친 정점.

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om


# ----------------------------------------------------------------------
# severity
# ----------------------------------------------------------------------

PASS = "PASS"
INFO = "INFO"
WARN = "WARN"
FAIL = "FAIL"

_RANK = {PASS: 0, INFO: 1, WARN: 2, FAIL: 3}

# 진단 임계값
STRAY_FACTOR = 50.0     # 정점 거리가 median 의 N 배를 넘으면 떠돌이 후보
ABS_HUGE = 1.0e6        # 절대좌표가 이보다 크면 무조건 떠돌이
BBOX_INFLATE = 3.0      # 실제 bbox 대각이 robust bbox 대각의 N 배 이상이면 팽창
AREA_DEGEN = 1.0e-10    # 면적이 이보다 작으면 무조건 퇴화(구조적 zero-area)
AREA_TINY = 1.0e-5      # 이보다 작으면 '작은 면' 후보 (polyCleanup zeroGeom 허용치와 정렬)
QUALITY_EPS = 1.0e-2    # 형상품질 q(등주지수)가 이보다 작으면 슬라이버(퇴화)로 본다
EDGE_EPS = 1.0e-7       # 길이가 이보다 작으면 zero-length edge
MERGE_TOL = 1.0e-4      # 이 거리 안에서 떨어진(미병합) 정점쌍 후보
SAMPLE_CAP = 30         # 로그에 남길 컴포넌트 인덱스 최대 개수


def worst_of(checks):
    """체크 리스트에서 가장 높은 severity 를 반환."""
    w = PASS
    for c in checks:
        if _RANK[c["severity"]] > _RANK[w]:
            w = c["severity"]
    return w


def _check(name, severity, message, count=0, samples=None):
    return {
        "check": name,
        "severity": severity,
        "count": int(count),
        "samples": list(samples or [])[:SAMPLE_CAP],
        "message": message,
    }


# ----------------------------------------------------------------------
# DAG / 포인트 헬퍼 (mesh_fix 와 공유)
# ----------------------------------------------------------------------

def shape_of(node):
    """transform/shape 이름 -> 비-intermediate mesh shape (fullPath). 없으면 None."""
    if cmds.nodeType(node) == "mesh":
        return node
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True, type="mesh") or []
    for s in shapes:
        if not cmds.getAttr(s + ".intermediateObject"):
            return s
    return shapes[0] if shapes else None


def _shape_dag(node):
    sel = om.MSelectionList()
    sel.add(node)
    dag = sel.getDagPath(0)
    if dag.apiType() == om.MFn.kTransform:
        dag.extendToShape()
    return dag


def get_object_points(node):
    """object 공간 정점 좌표 [(x, y, z), ...] (API 호출 1회)."""
    fn = om.MFnMesh(_shape_dag(node))
    pts = fn.getPoints(om.MSpace.kObject)
    return [(p.x, p.y, p.z) for p in pts]


def _finite(p):
    return math.isfinite(p[0]) and math.isfinite(p[1]) and math.isfinite(p[2])


def find_nan_indices(points):
    """NaN/Inf 좌표를 가진 정점 인덱스 목록."""
    return [i for i, p in enumerate(points) if not _finite(p)]


def _median(values):
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else 0.5 * (s[mid - 1] + s[mid])


def centroid_of(points):
    """유한한 정점만으로 축별 median centroid 를 계산(이상치에 강함)."""
    fin = [p for p in points if _finite(p)]
    if not fin:
        return (0.0, 0.0, 0.0)
    return (
        _median([p[0] for p in fin]),
        _median([p[1] for p in fin]),
        _median([p[2] for p in fin]),
    )


def find_stray_indices(points, centroid=None):
    """본체에서 비정상적으로 멀리 떨어진 떠돌이 정점 인덱스 목록.

    median centroid 로부터의 거리가 median 거리의 STRAY_FACTOR 배를 넘거나,
    절대좌표가 ABS_HUGE 를 넘으면 떠돌이로 본다. NaN 은 제외(별도 처리).
    """
    if centroid is None:
        centroid = centroid_of(points)
    cx, cy, cz = centroid
    dists = []
    for p in points:
        if _finite(p):
            dists.append(math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2 + (p[2] - cz) ** 2))
        else:
            dists.append(None)
    finite_d = [d for d in dists if d is not None]
    med = _median(finite_d)
    thr = max(med * STRAY_FACTOR, 1e-9)
    stray = []
    for i, p in enumerate(points):
        if not _finite(p):
            continue
        d = dists[i]
        if d > thr or abs(p[0]) > ABS_HUGE or abs(p[1]) > ABS_HUGE or abs(p[2]) > ABS_HUGE:
            stray.append(i)
    return stray


def _bbox_diag(points, skip=None):
    skip = set(skip or [])
    xs = [p[0] for i, p in enumerate(points) if _finite(p) and i not in skip]
    ys = [p[1] for i, p in enumerate(points) if _finite(p) and i not in skip]
    zs = [p[2] for i, p in enumerate(points) if _finite(p) and i not in skip]
    if not xs:
        return 0.0, None
    bb = (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
    diag = math.sqrt((bb[3] - bb[0]) ** 2 + (bb[4] - bb[1]) ** 2 + (bb[5] - bb[2]) ** 2)
    return diag, bb


# ----------------------------------------------------------------------
# 개별 진단 체크
# ----------------------------------------------------------------------

def _check_vertex_sanity(shape, points):
    """NaN/Inf 정점, 떠돌이 정점, bbox 팽창 (증상 1)."""
    out = []

    nan_idx = find_nan_indices(points)
    if nan_idx:
        out.append(_check(
            "nan_inf_vertices", FAIL,
            "NaN/Inf coordinates found. This corrupts the bounding box and "
            "breaks weight transfer (barycentric -> 0). Fix: Snap NaN/Stray Verts.",
            len(nan_idx), nan_idx))
    else:
        out.append(_check("nan_inf_vertices", PASS, "No NaN/Inf vertices.", 0))

    centroid = centroid_of(points)
    stray_idx = find_stray_indices(points, centroid)
    if stray_idx:
        out.append(_check(
            "stray_vertices", FAIL,
            "Vertices far from the mesh body (stray). These inflate the bounding "
            "box, so empty space around the mesh becomes clickable. "
            "Fix: Snap NaN/Stray Verts (or inspect with Select Stray/NaN Verts).",
            len(stray_idx), stray_idx))
    else:
        out.append(_check("stray_vertices", PASS, "No stray vertices.", 0))

    # bbox 팽창 비교
    bad = set(nan_idx) | set(stray_idx)
    full_diag, full_bb = _bbox_diag(points, skip=nan_idx)   # NaN 은 bbox 계산 불가라 제외
    robust_diag, _rb = _bbox_diag(points, skip=bad)
    if robust_diag > 1e-9 and full_diag > robust_diag * BBOX_INFLATE:
        out.append(_check(
            "bbox_inflation", FAIL,
            "Bounding box is much larger than the mesh body "
            "(actual diag={0:.3g} vs body diag={1:.3g}). This is why clicking empty "
            "space selects the mesh. Caused by NaN/stray vertices above.".format(
                full_diag, robust_diag),
            0))
    else:
        out.append(_check(
            "bbox_inflation", PASS,
            "Bounding box matches the mesh body (diag={0:.3g}).".format(full_diag), 0))

    return out


def _check_shapes_history(transform, shape):
    """intermediate(orig) shape, 잔여 construction history (증상 1 보조 / 일반 건강)."""
    out = []

    all_shapes = cmds.listRelatives(transform, shapes=True, fullPath=True, type="mesh") or [] \
        if cmds.nodeType(transform) == "transform" else []
    inter = [s for s in all_shapes if cmds.getAttr(s + ".intermediateObject")]
    if len(inter) > 1:
        out.append(_check(
            "intermediate_shapes", WARN,
            "Multiple intermediate(orig) shapes. A broken orig shape can inflate the "
            "selection bounding box. Consider Delete History (deformer-safe).",
            len(inter), [s.split("|")[-1] for s in inter]))
    elif inter:
        out.append(_check(
            "intermediate_shapes", INFO,
            "One intermediate(orig) shape (normal for deformed meshes).",
            1, [s.split("|")[-1] for s in inter]))
    else:
        out.append(_check("intermediate_shapes", PASS, "No intermediate shapes.", 0))

    # 잔여 poly construction history (deformer 제외)
    hist = cmds.listHistory(shape, pruneDagObjects=True) or []
    deformer_types = ("skinCluster", "blendShape", "cluster", "ffd", "wrap",
                      "deltaMush", "tension", "nonLinear", "softMod", "wire",
                      "sculpt", "jiggle", "shrinkWrap", "proximityWrap")
    leftover = []
    for n in hist:
        nt = cmds.nodeType(n)
        if nt in ("mesh", "groupId", "groupParts", "shadingEngine"):
            continue
        if nt in deformer_types:
            continue
        leftover.append("{0}({1})".format(n.split("|")[-1], nt))
    if leftover:
        out.append(_check(
            "construction_history", WARN,
            "Leftover construction history (non-deformer). Stale history can cause "
            "odd selection/transfer behaviour. Fix: Delete History (deformer-safe).",
            len(leftover), leftover))
    else:
        out.append(_check("construction_history", PASS, "No leftover construction history.", 0))

    return out


def face_quality(points, area):
    """면 형상 품질(등주지수) q = (4*pi*area) / perimeter^2.

    원=1, 정사각형≈0.785, 정삼각형≈0.60, 슬라이버(정점 일직선/겹침)→0. **스케일 무관**.
    절대 면적과 달리, 면이 균일하게 작아도(케이스 B) q 는 정상값을 유지하고,
    얇은 슬라이버(케이스 A)만 0 으로 떨어진다 -> Transfer barycentric 의 안정성 지표.

    points: 해당 면의 정점들(MPointArray, 루프 순서). area: getArea 결과.
    """
    n = len(points)
    if n < 3 or area <= 0.0:
        return 0.0
    perim = 0.0
    for i in range(n):
        a = points[i]
        b = points[(i + 1) % n]
        dx, dy, dz = a.x - b.x, a.y - b.y, a.z - b.z
        perim += math.sqrt(dx * dx + dy * dy + dz * dz)
    if perim <= 1e-12:
        return 0.0
    return (4.0 * math.pi * area) / (perim * perim)


def _check_topology(shape):
    """non-manifold, lamina/holed/concave/zero-area face, zero-length edge,
    floating vertex (증상 2)."""
    out = []
    dag = _shape_dag(shape)

    # --- non-manifold (polyInfo) ---
    try:
        nme = cmds.polyInfo(shape, nonManifoldEdges=True) or []
    except Exception:
        nme = []
    try:
        nmv = cmds.polyInfo(shape, nonManifoldVertices=True) or []
    except Exception:
        nmv = []
    if nme or nmv:
        out.append(_check(
            "non_manifold", FAIL,
            "Non-manifold geometry (edges shared by >2 faces or bowtie vertices). "
            "Closest-point transfer maps to the wrong face here -> distortion/partial "
            "transfer. Fix: polyCleanup.",
            len(nme) + len(nmv),
            [s.split(":")[0] for s in (list(nme) + list(nmv))]))
    else:
        out.append(_check("non_manifold", PASS, "Manifold (no non-manifold components).", 0))

    # --- lamina (polyInfo) ---
    try:
        lam = cmds.polyInfo(shape, laminaFaces=True) or []
    except Exception:
        lam = []
    if lam:
        out.append(_check(
            "lamina_faces", FAIL,
            "Lamina faces (faces sharing all their edges / doubled faces). "
            "Fix: polyCleanup.",
            len(lam), [s.split(":")[0] for s in lam]))
    else:
        out.append(_check("lamina_faces", PASS, "No lamina faces.", 0))

    # --- per-face: sliver(zero-area)/tiny/holed/concave (MItMeshPolygon) ---
    # zero-area 판정은 절대 면적이 아니라 형상품질 q(face_quality)로 한다.
    #   후보 = it.zeroArea() 또는 area < AREA_TINY
    #   후보 중 area<AREA_DEGEN 또는 q<QUALITY_EPS -> 슬라이버/퇴화(FAIL, Transfer 깨짐)
    #   그 외(작지만 형상 정상) -> tiny(INFO 강등; barycentric 비율은 정상이라 오탐 방지)
    # 샘플은 "f<idx> a=<area> q=<quality>" 문자열로 남겨 로그에서 A/B 를 눈으로 구분.
    sliver, tiny, holed, concave = [], [], [], []
    try:
        it = om.MItMeshPolygon(dag)
        while not it.isDone():
            idx = it.index()
            try:
                area = it.getArea(om.MSpace.kObject)
                candidate = area < AREA_TINY
                try:
                    candidate = candidate or it.zeroArea()
                except Exception:
                    pass
                if candidate:
                    q = face_quality(it.getPoints(om.MSpace.kObject), area)
                    label = "f{0} a={1:.2e} q={2:.3f}".format(idx, area, q)
                    if area < AREA_DEGEN or q < QUALITY_EPS:
                        sliver.append(label)
                    else:
                        tiny.append(label)
            except Exception:
                pass
            try:
                if it.isHoled():
                    holed.append(idx)
            except Exception:
                pass
            try:
                if not it.isConvex():
                    concave.append(idx)
            except Exception:
                pass
            it.next()
    except Exception as e:
        out.append(_check("face_iteration", INFO,
                          "Face iteration skipped: {0}".format(e), 0))

    if sliver:
        out.append(_check(
            "zero_area_faces", FAIL,
            "Degenerate / sliver faces (area ~0 or very thin -> low shape quality q). "
            "Barycentric transfer breaks here -> faces collapse/distort. If the face is "
            "NEEDED geometry, transfer with closestVertex mode instead of deleting it; "
            "use polyCleanup only on junk faces.",
            len(sliver), sliver))
    else:
        out.append(_check("zero_area_faces", PASS, "No degenerate/sliver faces.", 0))

    if tiny:
        out.append(_check(
            "tiny_faces", INFO,
            "Small but well-shaped faces (area < {0:g}, shape quality ok). Barycentric "
            "ratios stay valid, so weight transfer is fine here -- not a defect.".format(
                AREA_TINY),
            len(tiny), tiny))

    if holed:
        out.append(_check(
            "holed_faces", WARN,
            "Faces with holes. Fix: polyCleanup.", len(holed), holed))
    if concave:
        out.append(_check(
            "concave_faces", INFO,
            "Concave faces (usually harmless, but can affect closest-point mapping).",
            len(concave), concave))

    # --- zero-length / border edges (MItMeshEdge) ---
    zero_edge, border = [], 0
    try:
        ie = om.MItMeshEdge(dag)
        while not ie.isDone():
            try:
                if ie.length(om.MSpace.kObject) < EDGE_EPS:
                    zero_edge.append(ie.index())
            except Exception:
                pass
            try:
                if ie.onBoundary():
                    border += 1
            except Exception:
                pass
            ie.next()
    except Exception:
        pass

    if zero_edge:
        out.append(_check(
            "zero_length_edges", FAIL,
            "Zero-length edges (collapsed/coincident edge vertices). Fix: polyCleanup "
            "or Merge Vertices.", len(zero_edge), zero_edge))
    else:
        out.append(_check("zero_length_edges", PASS, "No zero-length edges.", 0))

    out.append(_check(
        "border_edges",
        INFO if border else PASS,
        "Border (open) edges: {0}. Open meshes are fine, but holes from cleanup "
        "show up here.".format(border),
        border))

    # --- floating vertices (연결 페이스 0) ---
    floating = []
    try:
        iv = om.MItMeshVertex(dag)
        while not iv.isDone():
            try:
                if iv.numConnectedFaces() == 0:
                    floating.append(iv.index())
            except Exception:
                pass
            iv.next()
    except Exception:
        pass
    if floating:
        out.append(_check(
            "floating_vertices", WARN,
            "Vertices with no connected faces (floating). Often paired with stray "
            "vertices / inflated bbox.", len(floating), floating))

    return out


def _check_coincident_vertices(points):
    """merge_tol 안에서 떨어져 있는(미병합 의심) 정점쌍 후보 — 작은 spatial hash."""
    finite_idx = [i for i, p in enumerate(points) if _finite(p)]
    if len(finite_idx) < 2:
        return _check("coincident_vertices", PASS, "Not enough vertices.", 0)

    cell = MERGE_TOL
    grid = {}

    def key(p):
        return (int(math.floor(p[0] / cell)),
                int(math.floor(p[1] / cell)),
                int(math.floor(p[2] / cell)))

    pairs = set()
    tol2 = MERGE_TOL * MERGE_TOL
    for i in finite_idx:
        p = points[i]
        kx, ky, kz = key(p)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    bucket = grid.get((kx + dx, ky + dy, kz + dz))
                    if not bucket:
                        continue
                    for j in bucket:
                        q = points[j]
                        d2 = (p[0]-q[0])**2 + (p[1]-q[1])**2 + (p[2]-q[2])**2
                        if d2 <= tol2:
                            pairs.add((j, i))
        grid.setdefault((kx, ky, kz), []).append(i)

    if pairs:
        flat = sorted({v for pair in pairs for v in pair})
        return _check(
            "coincident_vertices", WARN,
            "Coincident (unmerged) vertex pairs within {0:g}. These create invisible "
            "splits that break transfer. Fix: Merge Vertices.".format(MERGE_TOL),
            len(pairs), flat)
    return _check("coincident_vertices", PASS, "No coincident/unmerged vertices.", 0)


def _check_transform_uv_skin(transform, shape):
    out = []

    # 음수 스케일(노멀 뒤집힘 -> 전이 시 일그러짐)
    try:
        m = cmds.xform(transform, q=True, ws=True, matrix=True)
        # 3x3 determinant
        det = (m[0]*(m[5]*m[10]-m[6]*m[9])
               - m[1]*(m[4]*m[10]-m[6]*m[8])
               + m[2]*(m[4]*m[9]-m[5]*m[8]))
        if det < 0:
            out.append(_check(
                "negative_scale", WARN,
                "Negative scale (mirrored transform, det<0). Normals read flipped, "
                "which distorts weight transfer. Consider Freeze Transformations.", 0))
        else:
            out.append(_check("negative_scale", PASS, "No negative scale.", 0))
    except Exception:
        pass

    # UV 셋 / 누락 UV
    try:
        uv_sets = cmds.polyUVSet(shape, q=True, allUVSets=True) or []
    except Exception:
        uv_sets = []
    missing_uv = []
    try:
        it = om.MItMeshPolygon(_shape_dag(shape))
        while not it.isDone():
            try:
                if not it.hasUVs():
                    missing_uv.append(it.index())
            except Exception:
                pass
            it.next()
    except Exception:
        pass
    if not uv_sets:
        out.append(_check("uv_sets", WARN,
                          "No UV sets. UV-based transfer modes will fail.", 0))
    elif missing_uv:
        out.append(_check(
            "missing_uvs", WARN,
            "Faces without UVs ({0} sets present). UV-based transfer modes will be "
            "wrong here.".format(len(uv_sets)), len(missing_uv), missing_uv))
    else:
        out.append(_check("uv_sets", PASS,
                          "{0} UV set(s), all faces have UVs.".format(len(uv_sets)), 0))

    # skinCluster
    skin = [n for n in (cmds.listHistory(shape) or [])
            if cmds.nodeType(n) == "skinCluster"]
    if skin:
        sc = skin[0]
        try:
            infs = cmds.skinCluster(sc, q=True, influence=True) or []
            mx = cmds.getAttr(sc + ".maxInfluences")
            out.append(_check(
                "skin_cluster", INFO,
                "skinCluster '{0}': {1} influences, maxInfluences={2}.".format(
                    sc, len(infs), mx), len(infs)))
        except Exception:
            out.append(_check("skin_cluster", INFO,
                              "skinCluster '{0}'.".format(sc), 0))
    else:
        out.append(_check("skin_cluster", INFO, "No skinCluster on this mesh.", 0))

    return out


# ----------------------------------------------------------------------
# 메인 스캐너
# ----------------------------------------------------------------------

class MeshScanner:
    """선택 메시 진단. 메시를 절대 수정하지 않는다."""

    def scan_selection(self):
        sel = cmds.ls(selection=True, long=True) or []
        meshes = []
        seen = set()
        for node in sel:
            shp = shape_of(node)
            if shp and shp not in seen:
                seen.add(shp)
                # transform 이름 확보
                if cmds.nodeType(node) == "mesh":
                    tr = (cmds.listRelatives(node, parent=True, fullPath=True) or [node])[0]
                else:
                    tr = node
                meshes.append((tr, shp))
        return [self.scan_one(tr, shp) for tr, shp in meshes]

    def scan_one(self, transform, shape):
        checks = []
        counts = {}
        try:
            fn = om.MFnMesh(_shape_dag(shape))
            points = get_object_points(shape)
            counts = {
                "vertices": fn.numVertices,
                "edges": fn.numEdges,
                "faces": fn.numPolygons,
            }
            try:
                counts["shells"] = cmds.polyEvaluate(shape, shell=True)
            except Exception:
                pass

            checks += _check_vertex_sanity(shape, points)
            checks += _check_shapes_history(transform, shape)
            checks += _check_topology(shape)
            checks.append(_check_coincident_vertices(points))
            checks += _check_transform_uv_skin(transform, shape)
        except Exception as e:
            checks.append(_check("scan_error", FAIL,
                                 "Scan failed: {0}".format(e), 0))

        worst = worst_of(checks)
        return {
            "transform": transform.split("|")[-1],
            "shape": shape.split("|")[-1],
            "transform_full": transform,
            "shape_full": shape,
            "counts": counts,
            "checks": checks,
            "worst": worst,
            "suspected_root_causes": self._root_causes(checks),
        }

    @staticmethod
    def _root_causes(checks):
        by = {c["check"]: c for c in checks}
        causes = []

        def fired(name):
            c = by.get(name)
            return c and c["severity"] in (WARN, FAIL) and c["count"] >= 0 \
                and c["severity"] != PASS and (c["count"] > 0 or c["severity"] == FAIL)

        s1 = [n for n in ("nan_inf_vertices", "stray_vertices", "bbox_inflation",
                          "intermediate_shapes") if fired(n)]
        if s1:
            causes.append(
                "Symptom 1 (empty-space click selects mesh): inflated bounding box "
                "from " + ", ".join(s1) + ".")

        s2 = [n for n in ("non_manifold", "lamina_faces", "zero_area_faces",
                          "zero_length_edges", "coincident_vertices",
                          "negative_scale") if fired(n)]
        if s2:
            causes.append(
                "Symptom 2 (weight transfer partial/distorted): topology damage from "
                + ", ".join(s2) + ".")

        if not causes:
            causes.append("No blocking issues detected.")
        return causes
