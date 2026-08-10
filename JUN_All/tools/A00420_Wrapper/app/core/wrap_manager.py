# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-10
# A00420_Wrapper core - 커브 가이드 래핑 파이프라인 (Wrap3D 의 Wrapping 노드에 해당).
#
# 토폴로지가 다른 두 메시 A(소스) / B(타깃) 에 대해, A 의 **토폴로지는 그대로 두고**
# 형태만 B 와 같아지도록 A 의 정점을 옮긴다. 2 단계다.
#
#   1) Warp     - 커브 가이드에서 뽑은 대응 포인트로 TPS 공간 워프를 만들어 A 전체를
#                 통째로 B 쪽으로 휜다. 입술/눈/코 같은 **특징 대응**은 여기서 맞는다.
#                 이 단계만으로도 큰 형태 차이(비율/각도)가 거의 사라진다.
#   2) Project  - 워프된 A 의 정점을 B 표면의 최근접점으로 당긴다(비강체 ICP). 매 반복마다
#                 변위를 라플라시안으로 스무딩해, 표면에 붙이면서도 삼각형이 뒤집히거나
#                 스파이크가 생기지 않게 한다. 여기서 **세부 형태**가 맞는다.
#
# 왜 1) 없이 2) 만 하면 안 되나: 최근접점만으로는 "입술 위 정점"이 옆의 다른 부위로
# 끌려갈 수 있다. 가이드 워프로 특징을 먼저 맞춰 두어야 최근접점이 올바른 대응이 된다.
#
# 왜 2) 가 필요한가: TPS 는 컨트롤 포인트 사이를 부드럽게 보간할 뿐이라, 가이드가 없는
# 영역(볼·이마·뒤통수)은 B 표면에 정확히 붙지 않는다. 투영이 그 나머지를 메운다.

import maya.cmds as cmds

import numpy as np

from .mesh_utils import (
    MeshData,
    ClosestPointFinder,
    smooth_field,
)
from .guide_sampler import build_control_points, merge_duplicates
from .rbf_warp import ThinPlateSpline


# 출력 모드
OUTPUT_NEW = "new"        # 소스를 복제해 결과를 만든다 (원본 보존)
OUTPUT_IN_PLACE = "in_place"


class WrapOptions(object):
    """래핑 설정 한 묶음. UI 값이 그대로 들어온다."""

    def __init__(self):

        # 가이드
        self.samples = 24            # 커브 1개당 샘플 개수
        self.auto_align = True       # 커브 방향/시작점 자동 정렬
        self.snap_guides = True      # 샘플을 각 메시 표면으로 스냅

        # 워프
        self.smoothness = 0.0        # TPS 정규화 (0 = 컨트롤 포인트를 정확히 통과)

        # 투영
        self.iterations = 5          # 0 이면 투영 단계를 건너뛴다
        self.strength = 1.0          # 반복 1회당 최근접점 쪽으로 가는 비율
        self.relax = 0.3             # 변위 스무딩 세기
        self.relax_steps = 2         # 변위 스무딩 반복
        self.max_distance = 0.0      # 0 = 제한 없음. 이보다 멀면 그 정점은 안 옮긴다
        self.angle_limit = 90.0      # 노멀 각도 차가 이보다 크면 반대편으로 본다 (0 = 끔)

        # 출력
        self.output = OUTPUT_NEW
        self.suffix = "_wrap"
        self.amount = 1.0            # 원본 <-> 결과 블렌드 (1 = 완전 래핑)


class WrapResult(object):

    def __init__(self):
        self.node = ""
        self.vertex_count = 0
        self.control_count = 0
        self.guide_count = 0
        self.residual_mean = 0.0
        self.residual_max = 0.0
        self.projected = 0
        self.skipped = 0
        self.mean_distance = 0.0


# ============================================================ 투영 단계

def project_to_surface(points, source_normals, finder, adjacency, options,
                       progress=None):
    """워프된 정점을 타깃 표면으로 반복 투영한다.

    points         : (N, 3) 월드 좌표 (워프 결과)
    source_normals : (N, 3) 소스 정점 노멀 (월드). 뒷면 판정에만 쓴다.
    반환: (points, moved_count, skipped_count, mean_distance)
    """
    pts = np.array(points, dtype=np.float64, copy=True)

    cos_limit = None
    if options.angle_limit > 0.0:
        cos_limit = float(np.cos(np.radians(min(options.angle_limit, 179.0))))

    moved = 0
    skipped = 0
    mean_distance = 0.0

    for step in range(int(options.iterations)):

        closest, normals, dist = finder.query(pts)

        valid = np.ones(len(pts), dtype=bool)

        if options.max_distance > 0.0:
            valid &= dist <= options.max_distance

        if cos_limit is not None:
            valid &= (normals * source_normals).sum(axis=1) >= cos_limit

        delta = (closest - pts) * float(options.strength)
        delta[~valid] = 0.0

        delta = smooth_field(delta, adjacency, options.relax, options.relax_steps)

        pts += delta

        moved = int(valid.sum())
        skipped = int((~valid).sum())
        mean_distance = float(dist[valid].mean()) if moved else 0.0

        if progress:
            progress(step + 1, int(options.iterations), mean_distance)

    return pts, moved, skipped, mean_distance


# ============================================================ 출력

def _duplicate_source(source_node, suffix):
    """소스 메시를 복제하고 히스토리를 지운다. 결과 transform 이름을 돌려준다."""
    transform = source_node
    if cmds.nodeType(source_node) == "mesh":
        parents = cmds.listRelatives(source_node, parent=True, fullPath=True) or []
        transform = parents[0] if parents else source_node

    short = transform.split("|")[-1]
    dup = cmds.duplicate(transform, name="{0}{1}".format(short, suffix),
                         returnRootsOnly=True)[0]

    cmds.delete(dup, constructionHistory=True)

    # 복제본은 편집 대상이므로 잠금/표시 상태를 안전하게 풀어 둔다.
    for attr in ("translate", "rotate", "scale"):
        for axis in ("X", "Y", "Z"):
            plug = "{0}.{1}{2}".format(dup, attr, axis)
            if cmds.getAttr(plug, lock=True):
                cmds.setAttr(plug, lock=False)

    return cmds.ls(dup, long=True)[0]


# ============================================================ 파이프라인

def wrap(source_node, target_node, pairs, options, log=None, progress=None):
    """가이드 커브 쌍으로 소스 메시를 타깃 메시에 래핑한다.

    source_node / target_node : 메시 transform 또는 shape 이름
    pairs                     : guide_sampler.GuidePair 리스트
    options                   : WrapOptions
    반환: WrapResult
    """
    def _log(text, warn=False):
        if log:
            log(text, warn=warn)

    result = WrapResult()

    src_mesh = MeshData(source_node)
    tgt_mesh = MeshData(target_node)

    if src_mesh.shape == tgt_mesh.shape:
        raise ValueError("Source and Target are the same mesh.")

    tgt_finder = ClosestPointFinder(tgt_mesh)
    src_finder = ClosestPointFinder(src_mesh) if options.snap_guides else None

    # ---- 1) 가이드 -> 컨트롤 포인트 --------------------------------

    ctrl_src, ctrl_dst, used = build_control_points(
        pairs, options.samples, options.auto_align,
        src_finder if options.snap_guides else None,
        tgt_finder if options.snap_guides else None,
        log=log)

    # 겹친 컨트롤 포인트는 합친다(TPS 행렬이 특이해지는 것을 막는다).
    bbox = ctrl_src.max(axis=0) - ctrl_src.min(axis=0)
    tolerance = float(np.linalg.norm(bbox)) * 1e-4
    before = len(ctrl_src)
    ctrl_src, ctrl_dst = merge_duplicates(ctrl_src, ctrl_dst, tolerance)

    if len(ctrl_src) != before:
        _log("Merged {0} overlapping control point(s).".format(before - len(ctrl_src)))

    result.guide_count = used
    result.control_count = len(ctrl_src)

    # ---- 2) TPS 워프 -----------------------------------------------

    tps = ThinPlateSpline(ctrl_src, ctrl_dst, options.smoothness)

    original = src_mesh.world_points()
    warped = tps.apply(original)

    result.residual_mean, result.residual_max = tps.residual()

    _log("Warp done. {0} guide(s) -> {1} control point(s), "
         "fit error avg {2:.5f} / max {3:.5f}.".format(
             used, result.control_count,
             result.residual_mean, result.residual_max))

    # ---- 3) 표면 투영 ----------------------------------------------

    if options.iterations > 0:

        normals = src_mesh.world_normals()
        adjacency = src_mesh.adjacency()

        warped, moved, skipped, mean_distance = project_to_surface(
            warped, normals, tgt_finder, adjacency, options, progress=progress)

        result.projected = moved
        result.skipped = skipped
        result.mean_distance = mean_distance

        _log("Projection done. {0} iteration(s), {1} vertex(es) snapped, "
             "{2} skipped, mean gap {3:.5f}.".format(
                 int(options.iterations), moved, skipped, mean_distance))

    # ---- 4) 블렌드 + 쓰기 ------------------------------------------

    amount = float(options.amount)
    if amount < 1.0:
        warped = original + (warped - original) * amount

    if options.output == OUTPUT_NEW:
        out_node = _duplicate_source(src_mesh.node, options.suffix)
        out_mesh = MeshData(out_node)
    else:
        out_mesh = src_mesh
        out_node = src_mesh.shape

    out_mesh.set_world_points(warped)

    result.node = out_node
    result.vertex_count = out_mesh.count

    return result


# ============================================================ 가이드 미리보기

PREVIEW_GROUP = "A00420_guidePreview_grp"


def clear_preview():
    """기존 가이드 미리보기 그룹을 지운다."""
    if cmds.objExists(PREVIEW_GROUP):
        cmds.delete(PREVIEW_GROUP)
        return True
    return False


def build_preview(source_node, target_node, pairs, options, every=1, log=None):
    """가이드 대응을 눈으로 확인하는 선을 만든다.

    소스 샘플 i 와 타깃 샘플 i 를 잇는 짧은 직선을 쌍마다 그룹으로 만든다. 선이 서로
    꼬여 있으면 커브 방향/시작점 대응이 틀린 것이므로, 래핑 전에 여기서 잡을 수 있다.
    반환: (생성된 선 개수, 그룹 이름)
    """
    src_mesh = MeshData(source_node)
    tgt_mesh = MeshData(target_node)

    src_finder = ClosestPointFinder(src_mesh) if options.snap_guides else None
    tgt_finder = ClosestPointFinder(tgt_mesh) if options.snap_guides else None

    clear_preview()
    group = cmds.group(empty=True, name=PREVIEW_GROUP)

    made = 0
    step = max(int(every), 1)

    from .guide_sampler import sample_pair

    for index, pair in enumerate(pairs):
        if not pair.enabled:
            continue

        missing = pair.missing_side()
        if missing:
            pair.resolved = "no {0}".format(missing)
            if log:
                log("Guide row {0} has no {1} - skipped.".format(index + 1, missing),
                    warn=True)
            continue

        try:
            src, tgt, note = sample_pair(pair, options.samples, options.auto_align,
                                         src_finder, tgt_finder)
        except Exception as e:
            if log:
                log("Preview skipped ({0}): {1}".format(pair.source, e), warn=True)
            continue

        pair.resolved = note

        lines = []
        for k in range(0, len(src), step):
            crv = cmds.curve(degree=1,
                             point=[tuple(src[k]), tuple(tgt[k])],
                             name="A00420_link_{0:02d}_{1:03d}".format(index + 1, k))
            lines.append(crv)
            made += 1

        if lines:
            sub = cmds.group(lines, name="A00420_guide_{0:02d}".format(index + 1))
            cmds.parent(sub, group)

            # 첫 대응선만 색을 달리해 시작점을 눈에 띄게 한다.
            shapes = cmds.listRelatives(lines[0], shapes=True, fullPath=True) or []
            for shape in shapes:
                cmds.setAttr(shape + ".overrideEnabled", 1)
                cmds.setAttr(shape + ".overrideColor", 13)   # red = start

    return made, group
