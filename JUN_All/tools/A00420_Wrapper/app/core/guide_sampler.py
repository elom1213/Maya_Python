# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-10
# A00420_Wrapper core - 가이드(커브 쌍 / 포인트 쌍) -> 대응 컨트롤 포인트 샘플링.
#
# Wrap3D 의 `SelectPointPairs` 는 두 메시에서 **점**을 하나씩 집어 대응을 만든다.
# 이 툴은 그 대응을 **커브 쌍**으로 만든다. 소스 메시에 그린 커브와 타깃 메시에 그린
# 커브를 짝지어 두면, 두 커브를 같은 개수로 등간격(호 길이) 샘플링해 i 번째 샘플끼리
# 대응시킨다. 커브 하나가 곧 수십 개의 포인트 페어가 되는 셈이라, 입술·눈·코 라인처럼
# "선"으로 잡히는 특징을 훨씬 적은 손질로 맞출 수 있다.
#
# 커브 쌍에서 실수하기 쉬운 두 가지를 자동으로 해결한다.
#   1) 방향  : 두 커브의 cv 진행 방향이 반대면 대응이 꼬여 메시가 뒤집힌다.
#   2) 시작점: 닫힌 커브(눈/입 루프)는 방향이 같아도 **시작 위치(seam)** 가 다르면 돌아간다.
# 두 커브를 각자 중심/크기로 정규화한 뒤(메시 크기·위치가 달라도 비교 가능) 후보
# 조합(열린 커브 = 정/역 2가지, 닫힌 커브 = 정/역 x 시작점 N가지) 중 오차가 가장 작은
# 것을 고른다.

import maya.cmds as cmds
import maya.api.OpenMaya as om

import numpy as np

from .mesh_utils import (
    curve_shape_of,
    dag_path,
    world_position,
)


# 가이드 종류
KIND_CURVE = "curve"
KIND_POINT = "point"


# ============================================================ 커브 샘플링

def is_closed_curve(curve_shape):
    """커브가 닫힌(closed/periodic) 커브인지."""
    fn = om.MFnNurbsCurve(dag_path(curve_shape))
    return fn.form in (om.MFnNurbsCurve.kClosed, om.MFnNurbsCurve.kPeriodic)


def sample_curve(curve_shape, count):
    """커브를 호 길이 등간격으로 count 개 샘플링해 월드 좌표 (count, 3) 로 돌려준다.

    닫힌 커브는 시작점이 두 번 나오지 않도록 마지막 샘플을 빼고 한 바퀴를 count 등분한다.
    """
    fn = om.MFnNurbsCurve(dag_path(curve_shape))

    total = fn.length()
    if total <= 0.0:
        raise ValueError("Curve has zero length: {0}".format(curve_shape))

    closed = fn.form in (om.MFnNurbsCurve.kClosed, om.MFnNurbsCurve.kPeriodic)
    divisor = float(count) if closed else float(max(count - 1, 1))

    pts = np.empty((count, 3), dtype=np.float64)

    for i in range(count):
        length = total * (i / divisor)
        # 부동소수 오차로 끝을 넘지 않게 살짝 당긴다.
        length = min(length, total * (1.0 - 1e-9))
        param = fn.findParamFromLength(length)
        p = fn.getPointAtParam(param, om.MSpace.kWorld)
        pts[i] = (p.x, p.y, p.z)

    return pts


# ============================================================ 방향 / 시작점 맞추기

def _normalized(pts):
    """중심을 0 으로, 평균 반지름을 1 로 정규화. 위치/스케일이 달라도 형태만 비교하려고."""
    c = pts.mean(axis=0)
    d = pts - c
    r = np.sqrt((d * d).sum(axis=1)).mean()
    if r < 1e-12:
        r = 1.0
    return d / r


def align_samples(src_pts, tgt_pts, closed, auto=True, flip=False, offset=0):
    """타깃 샘플을 소스 샘플과 대응이 맞도록 재배열한다.

    auto=True  : 정/역(+ 닫힌 커브면 시작점 회전)을 모두 시도해 오차가 가장 작은 조합 선택.
    auto=False : flip/offset 을 그대로 적용.
    반환: (재배열된 tgt_pts, flip_used, offset_used)
    """
    n = len(src_pts)

    if not auto:
        out = tgt_pts[::-1] if flip else tgt_pts
        if closed and offset:
            out = np.roll(out, -int(offset) % n, axis=0)
        return out, bool(flip), int(offset) % n if closed else 0

    a = _normalized(src_pts)

    best = None
    for f in (False, True):
        b = _normalized(tgt_pts[::-1] if f else tgt_pts)
        shifts = range(n) if closed else (0,)
        for s in shifts:
            rolled = np.roll(b, -s, axis=0)
            err = float(((a - rolled) ** 2).sum())
            if best is None or err < best[0]:
                best = (err, f, s)

    _, flip_used, offset_used = best

    out = tgt_pts[::-1] if flip_used else tgt_pts
    if offset_used:
        out = np.roll(out, -offset_used, axis=0)

    return out, flip_used, offset_used


# ============================================================ 표면 스냅

def snap_to_surface(points, finder):
    """샘플 점들을 메시 표면 위로 당긴다(최근접점).

    커브를 눈대중으로 그렸어도 컨트롤 포인트가 정확히 표면에 앉게 해, 워프가
    '표면 -> 표면' 대응이 되도록 한다.
    """
    snapped, _, _ = finder.query(points)
    return snapped


# ============================================================ 가이드 -> 컨트롤 포인트

class GuidePair(object):
    """가이드 한 쌍. 커브 쌍이거나 포인트 쌍이다.

    노드는 UUID 로 보관한다(리네임/동명 노드에도 안전, repo 공통 규칙).
    """

    def __init__(self, kind, source, target, flip=False, samples=0, enabled=True):

        self.kind = kind
        self.flip = bool(flip)
        self.samples = int(samples)      # 0 이면 전역 설정을 따른다
        self.enabled = bool(enabled)

        self.source = source
        self.target = target
        self.source_uuid = self._uuid_of(source)
        self.target_uuid = self._uuid_of(target)

        # 마지막 샘플링에서 실제로 쓰인 값(UI 표시용)
        self.resolved = ""

    # ---- UUID 보관 --------------------------------------------------

    @staticmethod
    def _uuid_of(name):
        node = name.split(".")[0] if name else ""
        if not node or not cmds.objExists(node):
            return ""
        try:
            return cmds.ls(node, uuid=True)[0]
        except Exception:
            return ""

    @staticmethod
    def _resolve(name, uuid):
        """UUID 로 현재 이름을 되찾는다. 컴포넌트(.vtx[3]) 부분은 유지."""
        if not uuid:
            return name

        found = cmds.ls(uuid, long=True) or []
        if not found:
            return name

        if "." in name:
            return "{0}.{1}".format(found[0], name.split(".", 1)[1])
        return found[0]

    def source_name(self):
        return self._resolve(self.source, self.source_uuid)

    def target_name(self):
        return self._resolve(self.target, self.target_uuid)

    def is_valid(self):
        s, t = self.source_name(), self.target_name()
        return bool(s and t and cmds.objExists(s.split(".")[0])
                    and cmds.objExists(t.split(".")[0]))


def sample_pair(pair, default_samples, auto_align=True,
                src_finder=None, tgt_finder=None):
    """가이드 쌍 하나를 대응 컨트롤 포인트로 만든다.

    src_finder / tgt_finder 를 주면 샘플을 각 메시 표면으로 스냅한다.
    반환: (src_pts (n,3), tgt_pts (n,3), note)
    """
    src_name = pair.source_name()
    tgt_name = pair.target_name()

    if pair.kind == KIND_POINT:
        src = world_position(src_name).reshape(1, 3)
        tgt = world_position(tgt_name).reshape(1, 3)

        if src_finder is not None:
            src = snap_to_surface(src, src_finder)
        if tgt_finder is not None:
            tgt = snap_to_surface(tgt, tgt_finder)

        return src, tgt, "point"

    src_shape = curve_shape_of(src_name)
    tgt_shape = curve_shape_of(tgt_name)

    if not src_shape or not tgt_shape:
        raise ValueError("Not a NURBS curve pair: {0} / {1}".format(src_name, tgt_name))

    count = pair.samples if pair.samples > 0 else default_samples
    count = max(int(count), 2)

    src = sample_curve(src_shape, count)
    tgt = sample_curve(tgt_shape, count)

    src_closed = is_closed_curve(src_shape)
    tgt_closed = is_closed_curve(tgt_shape)

    # 한쪽만 닫혀 있으면 샘플 간격 규칙이 서로 달라 대응이 조금씩 어긋난다. 열린 커브
    # 규칙으로 처리하되(시작점 회전 없음) 노트에 남겨 사용자가 알아채게 한다.
    closed = src_closed and tgt_closed
    mixed = src_closed != tgt_closed

    tgt, flip_used, offset_used = align_samples(
        src, tgt, closed, auto=auto_align, flip=pair.flip, offset=0)

    if src_finder is not None:
        src = snap_to_surface(src, src_finder)
    if tgt_finder is not None:
        tgt = snap_to_surface(tgt, tgt_finder)

    note = "{0} samples{1}{2}{3}{4}".format(
        count,
        ", closed" if closed else "",
        ", OPEN/CLOSED mismatch" if mixed else "",
        ", flipped" if flip_used else "",
        ", offset {0}".format(offset_used) if offset_used else "")

    return src, tgt, note


def build_control_points(pairs, default_samples, auto_align=True,
                         src_finder=None, tgt_finder=None, log=None):
    """가이드 쌍 목록 -> 컨트롤 포인트 (src (N,3), tgt (N,3)).

    실패한 쌍은 건너뛰고 로그만 남긴다.
    """
    src_all = []
    tgt_all = []
    used = 0

    for pair in pairs:
        if not pair.enabled:
            continue

        try:
            s, t, note = sample_pair(pair, default_samples, auto_align,
                                     src_finder, tgt_finder)
        except Exception as e:
            pair.resolved = "failed"
            if log:
                log("Guide skipped ({0} / {1}): {2}".format(
                    pair.source, pair.target, e), warn=True)
            continue

        pair.resolved = note
        src_all.append(s)
        tgt_all.append(t)
        used += 1

    if not src_all:
        raise ValueError("No usable guide pairs.")

    return np.vstack(src_all), np.vstack(tgt_all), used


def merge_duplicates(src, tgt, tolerance):
    """소스 쪽에서 tolerance 안에 겹치는 컨트롤 포인트를 하나로 합친다.

    커브 끝이 서로 만나거나 두 가이드가 교차하면 같은 자리에 컨트롤 포인트가 겹치고,
    그러면 TPS 행렬이 특이(singular)해져 워프가 폭발한다. 격자 반올림으로 묶어
    소스/타깃 좌표를 각각 평균한다.
    """
    if tolerance <= 0.0 or len(src) < 2:
        return src, tgt

    key = np.round(src / tolerance).astype(np.int64)
    _, inverse = np.unique(key, axis=0, return_inverse=True)
    inverse = np.asarray(inverse).ravel()

    groups = int(inverse.max()) + 1
    if groups == len(src):
        return src, tgt

    counts = np.bincount(inverse, minlength=groups).astype(np.float64)

    s_out = np.empty((groups, 3), dtype=np.float64)
    t_out = np.empty((groups, 3), dtype=np.float64)
    for c in range(3):
        s_out[:, c] = np.bincount(inverse, weights=src[:, c], minlength=groups)
        t_out[:, c] = np.bincount(inverse, weights=tgt[:, c], minlength=groups)

    return s_out / counts[:, None], t_out / counts[:, None]
