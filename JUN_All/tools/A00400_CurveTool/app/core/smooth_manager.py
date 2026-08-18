# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00400_CurveTool core - 선택한 CV 의 Smooth / Rough (소프트 셀렉션 폴오프 반영). UI 비의존.
#
# 마야 기본 `Curves > Smooth`(= `cmds.smoothCurve`)의 **결과를 그대로 쓰되**, 그 명령이
# 못 하는 세 가지를 얹는다.
#
#   1) Rough        : `smoothCurve` 는 **음수 smoothness 를 조용히 무시한다**(실측 - 값이
#                     그대로다). 그래서 "스무딩 결과에서 멀어지는" 방향으로 직접 보간한다.
#   2) 폴오프       : `smoothCurve` 는 고른 CV 를 전부 똑같이 민다. 소프트 셀렉션 가중치를
#                     읽어 CV 마다 다르게 섞는다.
#   3) 실시간 조절  : 원본 스냅샷에서 **매번 다시 계산**하므로 드래그해도 누적되지 않는다.
#
# ── 계산 ───────────────────────────────────────────────────────────────────
#   target[i] = 마야 smoothCurve(smoothness = |amount|) 를 적용한 위치
#   result[i] = origin[i] + sign(amount) * weight[i] * (target[i] - origin[i])
#
# amount = 1, 가중치 1 이면 **마야 기본 Smooth 와 정확히 같은 결과**가 된다.
# amount 를 키우면 `smoothCurve` 에 더 큰 smoothness 를 넘긴다(마야가 하는 것과 같은 방식).
# 스무딩 결과를 넘겨 외삽하지 않으므로 값이 커져도 형태가 튀지 않는다.
#
# ── mayapy 로 확인한 사실 ──────────────────────────────────────────────────
#  * `smoothCurve` 는 **실수 smoothness** 를 받는다(0.5 와 1 의 결과가 다르다).
#  * **음수는 무시**한다(s=-1 이면 그대로).
#  * 히스토리 노드를 만들지 않는다(일회성 편집).
#  * **활성 선택을 지운다**(다른 커브에 걸어도 그렇다). 슬라이더를 잡고 드래그하는 동안
#    사용자의 CV 선택이 풀려 버리므로, 이 명령 앞뒤로 선택을 보관했다 되돌린다.
#  * **주기(periodic) 커브**와 **degree 1(직선) 커브에서는 실패**한다 → 미리 걸러 이유를 알린다.
#  * **커브 양 끝 CV 는 절대 움직이지 않는다** — degree 3 이면 앞뒤 2개씩, degree 5 면 3개씩.
#    끝쪽만 고르면 명령은 성공하는데 아무 것도 안 변한다. 그래서 "실제로 움직인 CV 수" 를
#    세어 돌려주고, 0 이면 호출부가 그 이유를 알려 줄 수 있게 한다.
#  * 소프트 셀렉션 가중치는 `MGlobal.getRichSelection()` 으로 읽힌다.
#    소프트가 꺼져 있어도 고른 CV 가 가중치 1.0 으로 나오므로 같은 코드로 처리된다.
#    다만 이 호출은 **빈 선택에서 예외를 던지고**, 마야 버전/상태에 따라 다른 이유로도
#    실패할 수 있다. 실패를 조용히 삼키면 "선택한 게 없다"로 오해되므로,
#    평범한 선택 목록으로 되돌아가고 사유를 로그에 남긴다(아래 `cv_selection`).

import re

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from Framework.core.maya_undo import undo_chunk

TEMP_PREFIX = "JUN_smoothTemp"

# `...cv[12]` 만 잡는다. NURBS **서페이스**는 `cv[0][0]` 이라 여기 걸리지 않는다.
_CV_PATTERN = re.compile(r"\.cv\[(\d+)\]$")


# ==========================================================================
# 선택 읽기
# ==========================================================================
#
# 선택을 읽는 경로가 **두 개**다. 소프트 셀렉션 폴오프까지 얻으려면 리치 셀렉션이
# 필요하지만, `MGlobal.getRichSelection()` 은 환경에 따라 예외를 던진다(빈 선택일 때는
# 확실히 던지고, 그 밖에도 마야 버전/상태에 따라 실패할 수 있다).
# 그 예외를 조용히 삼키면 **"선택한 게 없다"** 로 오해되어 툴이 아무 것도 못 하게 된다.
# 그래서 리치가 실패하거나 비어 있으면 **평범한 선택 목록으로 되돌아가고**, 어느 경로를
# 썼는지(그리고 왜 실패했는지)를 호출부에 알려 준다.

def _curve_shape(node):
    """트랜스폼이든 셰이프든 nurbsCurve 셰이프의 롱네임. 아니면 None."""
    if not node or not cmds.objExists(node):
        return None

    if cmds.nodeType(node) == "nurbsCurve":
        return (cmds.ls(node, long=True) or [None])[0]

    shapes = cmds.listRelatives(node, shapes=True, fullPath=True, noIntermediate=True,
                                type="nurbsCurve") or []

    return shapes[0] if shapes else None


def _rich_selection():
    """리치 셀렉션에서 {셰이프: {인덱스: 가중치}}. (결과, 실패사유) 를 돌려준다."""
    result = {}

    try:
        selection = om2.MGlobal.getRichSelection()
    except Exception as exc:
        # 빈 선택이면 "Object does not exist" 로 예외가 난다(실측). 그 밖의 실패도 있으므로
        # 삼키지 말고 사유를 돌려준다.
        return result, "{0}: {1}".format(type(exc).__name__, exc)

    items = selection.getSelection()

    for i in range(items.length()):
        dag, component = items.getComponent(i)

        if component.isNull():
            continue

        shape = _curve_shape(dag.fullPathName())

        # 컴포넌트 타입 enum 대신 **노드가 nurbsCurve 인지**로 거른다.
        # 서페이스 CV 등은 여기서 걸러지고, 커브라면 타입 표기가 달라도 통과한다.
        if not shape:
            continue

        try:
            fn = om2.MFnSingleIndexedComponent(component)
        except Exception:
            # 서페이스 CV 처럼 인덱스가 2개인 컴포넌트는 여기서 걸린다.
            continue

        weights = {}

        for element in range(fn.elementCount):
            weight = fn.weight(element).influence if fn.hasWeights else 1.0

            if weight > 0.0:
                weights[fn.element(element)] = weight

        if weights:
            result.setdefault(shape, {}).update(weights)

    return result, None


def plain_cv_selection():
    """평범한 선택 목록에서 {셰이프: {인덱스: 1.0}}. 폴오프는 없다."""
    result = {}

    for item in (cmds.ls(selection=True, flatten=True, long=True) or []):
        match = _CV_PATTERN.search(item)

        if not match:
            continue

        shape = _curve_shape(item.split(".")[0])

        if not shape:
            continue

        result.setdefault(shape, {})[int(match.group(1))] = 1.0

    return result


def cv_selection():
    """선택된 커브 CV. (선택, 어느 경로였는지, 알림) 을 돌려준다.

    선택은 {셰이프 롱네임: {CV 인덱스: 가중치}}.
    """
    rich, error = _rich_selection()

    if rich:
        return rich, "soft selection" if _has_falloff(rich) else "selection", None

    plain = plain_cv_selection()

    if not plain:
        return {}, "none", error

    note = None

    if error:
        note = ("Could not read the soft selection ({0}) - "
                "falling back to the plain selection, without falloff.".format(error))
    elif cmds.softSelect(query=True, softSelectEnabled=True):
        note = ("Soft selection is on but no falloff weights came back - "
                "using the plain selection instead.")

    return plain, "plain selection", note


def pinned_indices(cv_count, degree):
    """마야 smoothCurve 가 절대 건드리지 않는 CV 인덱스.

    실측(CV 12개): degree 2 -> 앞 2 / 뒤 1, degree 3 -> 앞뒤 2, degree 5 -> 앞뒤 3.
    `(degree + 1) // 2` 가 이 값과 맞는다(degree 2 는 뒤쪽 기준으로 잡아 보수적).

    이 값은 **안내 문구를 만들기 위한 것**이지 실제 연산에 쓰이지 않으므로, 실제로 고정되는
    것보다 더 많이 말하지 않도록(= 실제 집합의 부분집합이 되도록) 보수적으로 잡는다.
    """
    edge = max(1, (int(degree) + 1) // 2)
    edge = min(edge, cv_count)

    return sorted(set(range(edge)) | set(range(max(0, cv_count - edge), cv_count)))


def has_falloff(selection):
    """가중치가 1 이 아닌 CV 가 하나라도 있으면 폴오프가 섞인 것."""
    return _has_falloff(selection)


def _has_falloff(selection):
    """가중치가 1 이 아닌 CV 가 하나라도 있으면 폴오프가 섞인 것."""
    return any(weight < 1.0 for weights in selection.values() for weight in weights.values())


def rich_cv_selection():
    """{셰이프: {인덱스: 가중치}} 만 필요할 때(호환용)."""
    return cv_selection()[0]


def summarize_indices(indices):
    """[5,7,8,9,12] -> "5, 7-9, 12" — 로그가 CV 하나씩 도배되지 않게."""
    values = sorted(indices)

    if not values:
        return ""

    parts = []
    start = previous = values[0]

    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        parts.append(str(start) if start == previous else "{0}-{1}".format(start, previous))
        start = previous = value

    parts.append(str(start) if start == previous else "{0}-{1}".format(start, previous))

    return ", ".join(parts)


def soft_select_state():
    """(켜짐, 반경) — 로그에 상태를 적어 주기 위한 것."""
    enabled = bool(cmds.softSelect(query=True, softSelectEnabled=True))
    distance = cmds.softSelect(query=True, softSelectDistance=True)

    return enabled, distance


# ==========================================================================
# 커브 하나에 대한 작업 단위
# ==========================================================================

class CurveTarget(object):
    """커브 하나의 원본 스냅샷 + 가중치 + 계산용 임시 커브."""

    def __init__(self, shape, weights):
        self.shape = shape
        self.weights = weights                       # {cv index: weight}
        self.origin = self._read(shape)
        self.count = len(self.origin)
        self.temp = None
        self.temp_shape = None

    # ------------------------------------------------------------------
    # CV 읽기/쓰기는 **한 번에** 한다.
    #
    # CV 하나씩 `cmds.xform` 을 부르면 드래그 한 틱에 수십~수백 번의 명령이 나가고,
    # 그동안 마야가 화면을 다시 그릴 틈을 못 얻어 **드래그 중에는 커브가 안 움직이는 것처럼
    # 보인다**(놓는 순간에야 한꺼번에 그려진다).
    #
    # 읽기는 API 배열 접근(`cvPositions`), 쓰기는 **`cmds.curve(replace=True)`** 를 쓴다.
    # API 의 `setCVPositions` 가 더 빠르지만 **undo 큐에 남지 않는다**(실측 - undo 해도
    # 커브가 안 돌아온다). `cmds.curve -r` 은 한 번의 호출로 CV 전체를 바꾸면서 **undo 가
    # 되고**(0.16 ms/call), degree/CV 수/히스토리를 보존하며 숨긴 커브에도 통한다.
    # 한 undo 청크 안에서 여러 번 불러도 Ctrl+Z 한 번에 전부 되돌아간다(실측).
    # ------------------------------------------------------------------

    @staticmethod
    def _fn(shape):
        selection = om2.MSelectionList()
        selection.add(shape)
        return om2.MFnNurbsCurve(selection.getDagPath(0))

    @classmethod
    def _read(cls, shape):
        """오브젝트 공간 CV 전체를 튜플 리스트로."""
        return [(point.x, point.y, point.z)
                for point in cls._fn(shape).cvPositions(om2.MSpace.kObject)]

    @staticmethod
    def _write(shape, positions):
        """오브젝트 공간 CV 전체를 한 번에, **undo 가 되게** 쓴다."""
        cmds.curve(shape, replace=True, point=[tuple(p) for p in positions])

    def open_temp(self):
        """마야의 smoothCurve 를 돌릴 임시 사본. 드래그 한 번에 하나만 만든다."""
        transform = cmds.listRelatives(self.shape, parent=True, fullPath=True)[0]

        self.temp = cmds.duplicate(transform, name=TEMP_PREFIX + "#",
                                   upstreamNodes=False)[0]
        cmds.delete(self.temp, constructionHistory=True)
        cmds.setAttr(self.temp + ".visibility", False)

        self.temp_shape = cmds.listRelatives(self.temp, shapes=True, fullPath=True)[0]

    def close_temp(self):
        if self.temp and cmds.objExists(self.temp):
            cmds.delete(self.temp)

        self.temp = None
        self.temp_shape = None

    def smoothed(self, smoothness):
        """임시 사본에 마야 smoothCurve 를 걸어 나온 위치들. 실패하면 None."""
        # 매번 원본으로 되돌린 뒤 계산한다 → 드래그해도 누적되지 않는다.
        self._write(self.temp_shape, self.origin)

        components = ["{0}.cv[{1}]".format(self.temp_shape, i) for i in sorted(self.weights)]

        # ⚠️ `cmds.smoothCurve` 는 **활성 선택을 지운다**(실측 - 다른 커브에 걸어도 그렇다).
        # 그대로 두면 슬라이더를 처음 움직이는 순간 사용자가 골라 둔 CV 가 전부 풀리고,
        # 그 다음 틱부터는 적용할 대상이 없어 **드래그해도 아무 반응이 없다.**
        # 그래서 이 명령 앞뒤로 선택을 그대로 보관했다 되돌린다.
        stored = om2.MGlobal.getActiveSelectionList()

        try:
            cmds.smoothCurve(components, smoothness=float(smoothness))
        except Exception:
            return None
        finally:
            om2.MGlobal.setActiveSelectionList(stored)

        return self._read(self.temp_shape)

    def apply(self, amount):
        """origin + sign * weight * (smoothed - origin) 을 실제 커브에 쓴다.

        (성공했는가, 실제로 움직인 CV 수) 를 돌려준다. 움직인 수를 세는 이유는
        **마야가 커브 양 끝 CV 를 고정**하기 때문이다 - 끝쪽만 고른 경우 명령은
        성공하지만 아무 것도 변하지 않는다. 그걸 조용히 넘기면 "툴이 동작을 안 한다"
        로만 보인다.
        """
        if abs(amount) < 1e-6:
            self._write(self.shape, self.origin)
            return True, 0

        target = self.smoothed(abs(amount))

        if target is None:
            return False, 0

        sign = 1.0 if amount > 0 else -1.0
        moved = 0

        # 고르지 않은 CV 는 원본 그대로 둔 배열을 만들어 **한 번에** 쓴다.
        positions = list(self.origin)

        for index, weight in self.weights.items():
            origin = self.origin[index]
            smoothed = target[index]

            position = tuple(origin[axis] + sign * weight * (smoothed[axis] - origin[axis])
                             for axis in range(3))

            if any(abs(position[axis] - origin[axis]) > 1e-9 for axis in range(3)):
                moved += 1

            positions[index] = position

        self._write(self.shape, positions)

        return True, moved

    def restore(self):
        self._write(self.shape, self.origin)


# ==========================================================================
# 세션 (드래그 한 번)
# ==========================================================================

class SmoothSession(object):
    """드래그가 시작될 때 만들어져 끝날 때 정리되는 상태.

    원본을 붙잡아 두고 **매번 원본에서 다시 계산**하므로 드래그해도 값이 누적되지 않는다.
    """

    def __init__(self, targets, skipped, source="selection", note=None):
        self.targets = targets
        self.skipped = skipped
        self.source = source        # 선택을 어느 경로로 읽었는지 (로그용)
        self.note = note            # 폴오프를 못 읽었을 때의 안내

        for target in self.targets:
            target.open_temp()

    @property
    def cv_count(self):
        return sum(len(t.weights) for t in self.targets)

    def apply(self, amount):
        """(적용된 커브 수, 실패한 커브 이름들, 실제로 움직인 CV 수)"""
        failed = []
        moved = 0

        for target in self.targets:
            ok, count = target.apply(amount)

            if ok:
                moved += count
            else:
                failed.append(target.shape)

        return len(self.targets) - len(failed), failed, moved

    def restore(self):
        for target in self.targets:
            target.restore()

    def close(self):
        for target in self.targets:
            target.close_temp()


def capture():
    """지금 선택에서 세션을 만든다. (세션, 에러) — 못 만들면 세션이 None."""
    selection, source, note = cv_selection()

    if not selection:
        message = ("Select some curve CVs first "
                   "(component mode on a NURBS curve, soft selection optional).")

        # 리치 셀렉션이 예외를 냈다면 그 사유까지 보여 준다 - 그래야 "선택했는데도 안 된다"
        # 는 상황에서 원인을 알 수 있다.
        if note:
            message += "  [{0}]".format(note)

        return None, message

    targets = []
    skipped = []

    for shape, weights in selection.items():
        # 마야 smoothCurve 가 실패하는 두 경우는 미리 걸러 이유를 알린다(실측).
        if cmds.getAttr(shape + ".form") == 2:
            skipped.append((shape, "periodic curve - Maya's smoothCurve cannot handle it"))
            continue

        if cmds.getAttr(shape + ".degree") < 2:
            skipped.append((shape, "degree 1 (linear) curve - Maya's smoothCurve "
                                   "cannot handle it"))
            continue

        targets.append(CurveTarget(shape, weights))

    if not targets:
        return None, "No usable curve in the selection. " + "; ".join(
            "{0} ({1})".format(shape.split("|")[-1], why) for shape, why in skipped)

    return SmoothSession(targets, skipped, source=source, note=note), None


# ==========================================================================
# 한 번에 적용 (드래그가 아니라 버튼/키보드로 값이 들어올 때)
# ==========================================================================

def apply_once(amount):
    """세션을 만들고 한 번 적용한 뒤 정리한다. undo 한 스텝."""
    # 임시 커브를 만드는 capture() 와 지우는 close() 까지 **전부 한 청크 안**이어야 한다.
    # 밖에 두면 Ctrl+Z 가 CV 가 아니라 "임시 커브 삭제"를 되돌려, 커브는 그대로인데
    # 임시 노드만 되살아난다(실측).
    with undo_chunk():
        session, error = capture()

        if session is None:
            return {"ok": False, "message": error}

        try:
            applied, failed, moved = session.apply(amount)
        finally:
            session.close()

    return {
        "ok": True,
        "message": "{0} {1:.3f} -> {2} curve(s), {3} of {4} CV(s) moved".format(
            "Smooth" if amount >= 0 else "Rough", abs(amount), applied,
            moved, session.cv_count),
        "applied": applied,
        "failed": failed,
        "moved": moved,
        "skipped": session.skipped,
        "note": session.note,
    }
