# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00400_CurveTool core - 컨트롤러 커브 만들기 · 색 지정 · 셰이프 교체 (UI 비의존)
#
# Brandon Schaal 의 `bs_controls.py` / `bs_controlsUI.py`(Control Curves Tool)를 이 툴로
# 옮긴 것이다. 원본은 마야 셸프에서
#       import bs_controlsUI; bs_controlsUI.BSControlsUI().bsControlsUI()
# 로 띄우던 `maya.cmds` 창이었다.
#
# ── 옮기면서 바꾼 것 ────────────────────────────────────────────────────────
# 동작(무엇을 만들고 어디에 붙이는지)은 그대로 두고, 이 저장소의 규칙에 맞췄다.
#
#   1) **셰이프 데이터는 Framework 로 올렸다** — `Framework/rules/control_shapes.json` +
#      `Framework.core.control_shapes`. 컨트롤러 셰이프는 이 툴만의 것이 아니다.
#   2) **`cmds.error` 를 쓰지 않는다** — 원본은 선택이 비면 예외를 던져 멈췄다. 여기서는
#      **로그 문자열 목록**을 돌려주고 나머지 일은 계속한다(다른 탭과 같은 규칙).
#   3) **씬 변경은 `undo_chunk()` 한 스텝** — 원본은 오브젝트마다 undo 가 쪼개졌다.
#   4) **선택을 지우지 않는다** — 원본 `bsSetIndex` / `bsResetColor` 는 끝에서
#      `cmds.select(d=True)` 로 선택을 날렸다. 색을 여러 번 바꿔 보는 흐름이 깨져서
#      **선택을 그대로 둔다**(색만 바꾸고 고른 것은 유지).
#   5) **`parentConstraint` 대신 `matchTransform`** — 원본은 constraint 를 걸었다 지웠다.
#      `matchTransform` 이 피벗 · `rotateOrder` · `jointOrient` 를 마야가 처리해 더 안전하다.
#   6) 원본 `bsResetColor` 는 셰이프가 없는 노드에서 `shapes` 가 정의되지 않아 죽었다
#      (transform 도 shape 도 아닌 노드를 고르면 `UnboundLocalError`). 여기서는 건너뛰고 알린다.

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from Framework.core.maya_undo import undo_chunk
from Framework.core import control_shapes
from tools.A00400_CurveTool.app.core.curve_manager import curve_shapes


#: 만들 위치 (원본 버튼 4개)
MODE_PARENT = "parent"      # 컨트롤을 선택 오브젝트의 **부모**로
MODE_CHILD = "child"        # 선택 오브젝트의 **자식**으로 (그 자식들은 컨트롤 밑으로)
MODE_WORLD = "world"        # 자리만 맞추고 월드에 둔다
MODE_ORIGIN = "origin"      # 선택과 무관하게 원점에 하나
MODES = (MODE_PARENT, MODE_CHILD, MODE_WORLD, MODE_ORIGIN)

#: 이름을 비워 두었을 때 붙는 접미사 (원본과 같다)
DEFAULT_SUFFIX = "_ANIM"

#: 이름에서 떼어 내는 흔한 접미사들 (원본 목록 그대로)
SUFFIXES = ("_JNT", "_Jnt", "_jnt", "_Bnd", "_BND", "_bnd", "_JT", "_Jt", "_jt",
            "_DRV", "Drv", "_drv", "_CON", "_Con", "_con", "_CTRL", "_Ctrl", "ctrl",
            "_anim", "_ANIM", "_Anim", "_LOC", "_Loc", "_loc", "_GRP", "_Grp", "_grp")

#: 색 그리드에 쓰는 마야 오버라이드 인덱스와 화면 색 (원본 UI 와 같은 순서 · 같은 값)
COLOR_SWATCHES = (
    (0, (0.0, 0.016, 0.373)), (1, (0.0, 0.0, 0.0)), (2, (0.247, 0.247, 0.247)),
    (3, (0.498, 0.498, 0.498)), (4, (0.608, 0.0, 0.157)), (6, (0.0, 0.0, 1.0)),
    (7, (0.0, 0.275, 0.094)), (8, (0.145, 0.0, 0.263)), (9, (0.78, 0.0, 0.78)),
    (10, (0.537, 0.278, 0.2)), (11, (0.243, 0.133, 0.122)), (12, (0.6, 0.145, 0.0)),
    (13, (1.0, 0.0, 0.0)), (14, (0.0, 1.0, 0.0)), (15, (0.0, 0.255, 0.6)),
    (16, (1.0, 1.0, 1.0)), (17, (1.0, 1.0, 0.0)), (18, (0.388, 0.863, 1.0)),
    (19, (0.263, 1.0, 0.635)), (20, (1.0, 0.686, 0.686)), (21, (0.89, 0.675, 0.475)),
    (22, (1.0, 1.0, 0.384)), (23, (0.0, 0.6, 0.325)), (24, (0.627, 0.412, 0.188)),
    (25, (0.62, 0.627, 0.188)), (26, (0.408, 0.627, 0.188)), (27, (0.188, 0.627, 0.365)),
    (28, (0.188, 0.627, 0.627)), (29, (0.188, 0.404, 0.627)), (30, (0.435, 0.188, 0.627)),
)

#: overrideDisplayType (원본 그리드의 T / R 버튼)
DISPLAY_NORMAL = 0
DISPLAY_TEMPLATE = 1
DISPLAY_REFERENCE = 2


def shape_names():
    """만들 수 있는 셰이프 이름 목록 (Framework 공용 라이브러리에서)."""
    return control_shapes.names()


# --------------------------------------------------------------- 이름

def control_name(node, typed):
    """컨트롤에 붙일 이름. 원본 `bsNameCurve` 와 같은 규칙이다.

    typed 가 비었으면          -> `<노드><DEFAULT_SUFFIX>`
    typed 에 `_`(또는 공백)이 있으면 -> 그 이름을 그대로 쓴다(공백은 `_` 로)
    typed 가 한 단어면         -> 노드 이름에서 흔한 접미사를 떼고 `_<typed>` 를 붙인다
                                 (`spine_jnt` + `ctl` -> `spine_ctl`)
    """
    base = (node or "").split("|")[-1]
    typed = (typed or "").strip()

    if not typed:
        return base + DEFAULT_SUFFIX

    typed = typed.replace(" ", "_")
    if "_" in typed:
        return typed

    name = base
    for suffix in SUFFIXES:
        name = name.replace(suffix, "")
    return "{0}_{1}".format(name, typed)


# --------------------------------------------------------------- 만들기

def _make_curve(shape, thickness, name, result):
    crv = control_shapes.build(shape, thickness=thickness, curve_name=name)
    if name and crv.split("|")[-1] != name:
        result["renamed"].append((name, crv.split("|")[-1]))
    return crv


def create_controls(shape, mode=MODE_WORLD, name="", thickness=1.0):
    """선택한 오브젝트마다(또는 원점에) 컨트롤 커브를 만든다. `(result, messages)`.

    shape     : `shape_names()` 의 이름 하나
    mode      : MODE_PARENT / MODE_CHILD / MODE_WORLD / MODE_ORIGIN
    name      : 이름 또는 접미사(위 control_name 규칙). 비우면 `<오브젝트>_ANIM`.
    thickness : 1.0 초과면 셰이프 `lineWidth`.

    전체가 **undo 한 스텝**이고, 만든 컨트롤이 선택된 채로 끝난다.
    """
    result = {"controls": [], "renamed": [], "skipped": []}
    messages = []

    if mode not in MODES:
        raise ValueError("Unknown mode: {0}".format(mode))
    if not control_shapes.has(shape):
        raise ValueError("Unknown control shape: {0}".format(shape))

    selection = cmds.ls(selection=True, long=True) or []
    if mode != MODE_ORIGIN and not selection:
        return result, ["[WARN] Select at least one object, or use Origin."]

    with undo_chunk():
        if mode == MODE_ORIGIN:
            # 원점 모드는 선택을 보지 않는다. 이름을 비우면 셰이프 이름을 소문자로.
            wanted = (name or shape).strip().replace(" ", "_").lower() \
                if not name else name.replace(" ", "_")
            result["controls"].append(_make_curve(shape, thickness, wanted, result))
        else:
            for node in selection:
                if not cmds.objExists(node):
                    result["skipped"].append((node, "gone from the scene"))
                    continue

                crv = _make_curve(shape, thickness, control_name(node, name), result)
                # 원본은 parentConstraint 를 걸었다 지웠다 - matchTransform 이 피벗과
                # rotateOrder/jointOrient 까지 마야에게 맡기므로 더 안전하다.
                cmds.matchTransform(crv, node, position=True, rotation=True, scale=False)

                if mode == MODE_PARENT:
                    # 컨트롤이 오브젝트의 자리에 들어간다 - 오브젝트의 부모 밑으로 먼저.
                    parents = cmds.listRelatives(node, parent=True, type="transform",
                                                 fullPath=True) or []
                    if parents:
                        crv = cmds.parent(crv, parents[0])[0]
                    cmds.parent(node, crv)
                elif mode == MODE_CHILD:
                    # 오브젝트의 자식들을 컨트롤 밑으로 옮기고, 컨트롤을 오브젝트 밑에.
                    children = cmds.listRelatives(node, children=True, type="transform",
                                                  fullPath=True) or []
                    if children:
                        cmds.parent(children, crv)
                    crv = cmds.parent(crv, node)[0]

                result["controls"].append(cmds.ls(crv, long=True)[0])

        if result["controls"]:
            cmds.select(result["controls"], replace=True)

    for wanted, actual in result["renamed"]:
        messages.append("[Warning] Name '{0}' was taken - Maya used '{1}'.".format(
            wanted, actual))
    for node, why in result["skipped"]:
        messages.append("[Warning] Skipped {0}: {1}.".format(node.split("|")[-1], why))
    if result["controls"]:
        messages.append("Created {0} '{1}' control(s): {2}".format(
            len(result["controls"]), shape,
            ", ".join(c.split("|")[-1] for c in result["controls"])))
    else:
        messages.append("[WARN] Nothing was created.")
    return result, messages


# --------------------------------------------------------------- 색

def _shapes_of(node):
    """색을 입힐 셰이프들. 트랜스폼이면 자식 셰이프, 셰이프면 자기 자신."""
    if not cmds.objExists(node):
        return []
    if cmds.objectType(node, isAType="shape"):
        return [node]
    return cmds.listRelatives(node, shapes=True, fullPath=True,
                              noIntermediate=True) or []


def _set_override(shapes, color=None, display=None, rgb=None):
    """셰이프들의 drawing override 를 켜고 값을 쓴다. 건드린 셰이프 수.

    color 는 마야 **인덱스 색**, rgb 는 **임의 색**(0~1 세 값)이다. 둘은 `overrideRGBColors`
    스위치 하나로 갈린다 - 인덱스를 쓰려면 0, RGB 를 쓰려면 1 이어야 해서 **쓸 때마다 맞춰 준다**
    (ref_01.mel 도 같다). 안 맞추면 색을 넣어도 화면은 이전 모드의 색 그대로다.
    """
    touched = 0
    for shape in shapes:
        try:
            if not cmds.getAttr(shape + ".overrideEnabled"):
                cmds.setAttr(shape + ".overrideEnabled", 1)
            if display is not None:
                cmds.setAttr(shape + ".overrideDisplayType", display)
            if color is not None or rgb is not None:
                # 색을 지정하면서 template/reference 로 두면 색이 안 보인다 - 원본과 같이 0 으로.
                if cmds.getAttr(shape + ".overrideDisplayType") != DISPLAY_NORMAL:
                    cmds.setAttr(shape + ".overrideDisplayType", DISPLAY_NORMAL)
            if color is not None:
                cmds.setAttr(shape + ".overrideRGBColors", 0)
                cmds.setAttr(shape + ".overrideColor", int(color))
            if rgb is not None:
                cmds.setAttr(shape + ".overrideRGBColors", 1)
                cmds.setAttr(shape + ".overrideColorRGB",
                             float(rgb[0]), float(rgb[1]), float(rgb[2]))
            touched += 1
        except Exception as exc:                            # noqa: BLE001
            raise RuntimeError("{0}: {1}".format(shape.split("|")[-1], exc))
    return touched


def _apply_to_selection(color=None, display=None, rgb=None, what="color"):
    """선택한 것들의 셰이프에 override 를 적용한다. `(touched, messages)`.

    **선택은 그대로 둔다** - 원본은 끝에서 선택을 지웠는데, 색을 몇 번 바꿔 보는 흐름이
    그때마다 끊겼다.
    """
    selection = cmds.ls(selection=True, long=True) or []
    if not selection:
        return 0, ["[WARN] Select control curve(s) first."]

    messages = []
    touched = 0
    with undo_chunk():
        for node in selection:
            shapes = _shapes_of(node)
            if not shapes:
                messages.append("[Warning] {0} has no shape to change.".format(
                    node.split("|")[-1]))
                continue
            try:
                touched += _set_override(shapes, color=color, display=display, rgb=rgb)
            except RuntimeError as exc:
                messages.append("[Warning] Could not set the {0} on {1}.".format(
                    what, exc))

    if touched:
        messages.append("{0} changed on {1} shape(s).".format(what.capitalize(), touched))
    elif not messages:
        messages.append("[WARN] Nothing was changed.")
    return touched, messages


def set_color(index):
    """선택한 컨트롤의 셰이프 색을 마야 오버라이드 **인덱스**로 바꾼다."""
    return _apply_to_selection(color=int(index), what="color")


def set_color_rgb(rgb):
    """선택한 컨트롤의 셰이프 색을 **임의 색(RGB)** 으로 바꾼다. 값은 0~1 세 개.

    인덱스 32색에 없는 색을 쓰려는 경우다(ref_01.mel 의 `Color Palettes` 와 같은 방식) —
    `overrideRGBColors` 를 켜고 `overrideColorRGB` 에 쓴다.
    """
    values = [min(max(float(v), 0.0), 1.0) for v in rgb]
    if len(values) != 3:
        raise ValueError("RGB needs three values.")
    return _apply_to_selection(rgb=values, what="color")


def set_display_type(display):
    """선택한 컨트롤 셰이프를 normal / template(1) / reference(2) 로."""
    return _apply_to_selection(display=int(display), what="display type")


def reset_color():
    """선택한 컨트롤의 override 를 트랜스폼과 셰이프 양쪽에서 끈다. `(touched, messages)`."""
    selection = cmds.ls(selection=True, long=True) or []
    if not selection:
        return 0, ["[WARN] Select control curve(s) first."]

    messages = []
    touched = 0
    with undo_chunk():
        for node in selection:
            # DAG 가 아닌 노드(유틸리티 등)에는 override 자체가 없다 - 건너뛰고 알린다.
            # (원본 `bsResetColor` 는 여기서 UnboundLocalError 로 죽었다.)
            if not cmds.objExists(node) or not cmds.objectType(node, isAType="dagNode"):
                messages.append("[Warning] {0} is not a shape or transform.".format(
                    node.split("|")[-1]))
                continue

            targets = list(_shapes_of(node))
            # 트랜스폼에 걸린 override 도 끈다 - 안 그러면 셰이프만 꺼도 자식들이 물려받는다.
            if not cmds.objectType(node, isAType="shape"):
                targets.append(node)
            if not targets:
                messages.append("[Warning] {0} has no shape to reset.".format(
                    node.split("|")[-1]))
                continue
            for target in targets:
                try:
                    cmds.setAttr(target + ".overrideEnabled", 0)
                    cmds.setAttr(target + ".overrideColor", 0)
                    cmds.setAttr(target + ".overrideDisplayType", DISPLAY_NORMAL)
                    # 임의 색(RGB)으로 칠했던 것도 되돌린다 - 스위치만 남으면 다음에 인덱스
                    # 색을 넣었을 때 "왜 색이 안 바뀌지" 가 된다.
                    if cmds.attributeQuery("overrideRGBColors", node=target, exists=True):
                        cmds.setAttr(target + ".overrideRGBColors", 0)
                        cmds.setAttr(target + ".overrideColorRGB", 0.0, 0.0, 0.0)
                    touched += 1
                except Exception as exc:                    # noqa: BLE001
                    messages.append("[Warning] Could not reset {0} ({1}).".format(
                        target.split("|")[-1], exc))

    if touched:
        messages.append("Reset the overrides on {0} node(s).".format(touched))
    return touched, messages


# --------------------------------------------------------------- 셰이프 교체

def _unlock_transform(node):
    for attr in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        plug = "{0}.{1}".format(node, attr)
        try:
            if cmds.getAttr(plug, lock=True):
                cmds.setAttr(plug, lock=False)
        except Exception:                                   # noqa: BLE001
            pass


# --------------------------------------------------------------- 레퍼런스 대상 (v01.22)
#
# 레퍼런스로 들어온 컨트롤은 **셰이프 노드를 지울 수 없다.** 위의 `replace_shape` 는
# "기존 셰이프 삭제 -> 새 셰이프 붙이기" 라서 레퍼런스 대상에서는 `cmds.delete` 가
# "Cannot delete ... as it has locked or read-only children" 로 실패하고, 이어지는
# `parent -add -shape` 도 레퍼런스 트랜스폼에는 붙지 않는다.
#
# 대신 **셰이프는 그대로 두고 CV 위치만 옮긴다.** `crv_to_replace.cv[i]` 를
# `crv_replacement.cv[i]` 에 하나씩 맞추는 것이라, 두 커브의 모양이 원래 같고 CV 개수가
# 같을 때(= 미러 쌍) 의도한 모양이 된다. CV 만 바뀌므로 레퍼런스 edit 로 저장되고
# (`setAttr ....controlPoints[i]`) 트랜스폼 · 이름 · 연결은 전부 그대로다.
#
#   mirror=True   대응 CV 의 **월드** 위치를 X 만 뒤집어(-x, y, z) 가져온다.
#                 셰이프 교체 경로의 mirror 와 같은 결과다 - 대상의 자리는 맞추지 않는다.
#   mirror=False  대응 CV 의 **오브젝트** 위치를 그대로 가져온다.
#                 셰이프 교체 경로의 non-mirror(matchTransform 후 freeze)와 같은 결과다.
#
# ── 쓰기는 왜 `xform` 인가 (mayapy 2024 로 확인) ──────────────────────────────
#  * `cmds.curve -replace`(Shape Edit 탭이 쓰는 방법)는 레퍼런스 커브에서 **그 세션에만**
#    먹는다. 레퍼런스 edit 로 기록되지 않아 **씬을 저장했다 다시 열면 원래 모양으로 돌아간다.**
#  * `setAttr .controlPoints[i]` 는 저장은 되지만 히스토리(예: `makeNurbCircle`)가 살아 있는
#    커브에서 절대 위치가 아니라 **트윅(델타)** 로 들어가 값이 두 배가 된다.
#  * `cmds.xform(cv, objectSpace=True, translation=...)` 만 **절대 위치 + 레퍼런스 edit 로
#    저장 + undo 한 스텝** 세 가지를 다 만족한다. 그래서 CV 하나씩 이걸로 쓴다.
#  * 주기(닫힌) 커브는 컴포넌트 `cv[i]` 가 **spans 개까지만** 유효하다. MFn 은 CV 를
#    `spans + degree` 개로 세지만(뒤의 degree 개는 앞의 복사본) 그 인덱스로 `xform` 을 쓰면
#    **조용히 마지막 CV 로 클램프돼 엉뚱한 CV 가 덮어써진다**(원 11개에 cv[8..10] → cv[7] 이
#    망가진다). 앞의 spans 개만 쓰면 이음매는 마야가 알아서 따라온다.


def is_referenced(node):
    """레퍼런스에서 들어온 노드인가. 대상 트랜스폼이나 그 셰이프 하나라도 걸리면 True."""
    candidates = [node] + list(curve_shapes(node))
    for candidate in candidates:
        try:
            if cmds.referenceQuery(candidate, isNodeReferenced=True):
                return True
        except Exception:                                   # noqa: BLE001
            continue

    return False


def _dag_path(shape):
    selection = om2.MSelectionList()
    selection.add(shape)

    return selection.getDagPath(0)


def _writable_cv_count(shape):
    """컴포넌트 `cv[i]` 로 **쓸 수 있는** CV 개수 - 주기 커브는 spans 까지뿐이다(위 주석)."""
    return len(cmds.ls(shape + ".cv[*]", flatten=True) or [])


def _cv_points(shape, world=False):
    """셰이프의 CV 위치 - **plain tuple 로 즉시 복사**해서 돌려준다.

    `cvPositions()` 가 준 `MPoint` 를 그대로 들고 나오면 `MFnNurbsCurve` 가 사라진 뒤
    값이 원래 자리로 되돌아가 있는 일이 있었다(씬을 저장했다 다시 연 다음 돌리면 CV 가
    하나도 안 움직이던 버그 - mayapy 로 재현). `MPlug.asMObject` 와 같은 수명 함정이다.
    """
    space = om2.MSpace.kWorld if world else om2.MSpace.kObject
    positions = om2.MFnNurbsCurve(_dag_path(shape)).cvPositions(space)

    return [(point.x, point.y, point.z) for point in positions]


def match_cv_positions(target, replacement, mirror=False):
    """`target` 의 CV 를 `replacement` 의 대응 CV 에 맞춘다. `(shapes, reason)`.

    셰이프 노드는 건드리지 않는다 - 레퍼런스 대상용 경로다(위 주석 참고).
    reason 이 None 이 아니면 아무 것도 쓰지 않고 그 사유로 건너뛴 것이다.
    """
    target_shapes = curve_shapes(target)
    source_shapes = curve_shapes(replacement)

    if not target_shapes:
        return 0, "it has no NURBS curve shape"
    if not source_shapes:
        return 0, "the replacement has no NURBS curve shape"
    if len(target_shapes) != len(source_shapes):
        return 0, "shape counts differ ({0} vs {1})".format(
            len(target_shapes), len(source_shapes))

    # 하나라도 안 맞으면 **아무 것도 쓰지 않는다** - 반쪽만 옮겨 어긋나지 않게.
    plans = []
    for index, target_shape in enumerate(target_shapes):
        source_shape = source_shapes[index]

        if mirror:
            # 월드에서 X 만 뒤집고(= scaleX -1) 대상의 오브젝트 공간으로 되돌린다.
            inverse = _dag_path(target_shape).inclusiveMatrixInverse()
            points = []
            for x, y, z in _cv_points(source_shape, world=True):
                mirrored = om2.MPoint(-x, y, z) * inverse
                points.append((mirrored.x, mirrored.y, mirrored.z))
        else:
            points = _cv_points(source_shape)

        # CV 개수와 **쓸 수 있는** 개수(주기 커브면 spans)가 둘 다 같아야 i <-> i 가 성립한다.
        # 뒤엣것까지 보는 이유 - 하나는 열린 커브, 하나는 닫힌 커브인데 CV 총수만 우연히
        # 같은 경우를 걸러 낸다.
        if (len(points) != len(_cv_points(target_shape))
                or _writable_cv_count(source_shape) != _writable_cv_count(target_shape)):
            return 0, "CV counts differ ({0} vs {1}) on {2}".format(
                len(_cv_points(target_shape)), len(points),
                target_shape.split("|")[-1])

        plans.append((target_shape, points))

    for shape, points in plans:
        for index, point in enumerate(points[:_writable_cv_count(shape)]):
            cmds.xform("{0}.cv[{1}]".format(shape, index),
                       objectSpace=True, translation=point)

    return len(plans), None


def replace_shape(target, replacement, mirror=False):
    """`target` 의 커브 셰이프를 `replacement` 의 모양으로 바꾼다(트랜스폼은 그대로).

    원본 `bsReplaceShape` 와 같은 순서다 - 복제 -> 잠금 해제 -> 자식 정리 -> 자리 맞추기
    -> target 밑으로 -> freeze -> 기존 셰이프 삭제 -> 셰이프를 target 에 붙이고 이름 정리.
    mirror 면 자리를 맞추는 대신 `scaleX = -1` 인 그룹에 넣었다 빼 **반대 모양**으로 만든다.
    """
    duplicate = cmds.duplicate(replacement, returnRootsOnly=True,
                               renameChildren=True, name="temp_CRV")[0]
    _unlock_transform(duplicate)

    if cmds.listRelatives(duplicate, parent=True):
        duplicate = cmds.parent(duplicate, world=True)[0]

    # 셰이프가 아닌 자식(그룹 · 조인트 등)은 떼어 낸다 - 셰이프만 옮길 것이다.
    for child in cmds.listRelatives(duplicate, children=True, fullPath=True) or []:
        if not cmds.objectType(child, isAType="shape"):
            cmds.delete(child)

    if mirror:
        group = cmds.group(empty=True, world=True, name="mirror_GRP")
        duplicate = cmds.parent(duplicate, group)[0]
        cmds.setAttr(group + ".scaleX", -1.0)
        duplicate = cmds.parent(duplicate, world=True)[0]
        cmds.delete(group)
    else:
        cmds.matchTransform(duplicate, target, position=True, rotation=True, scale=True)

    duplicate = cmds.parent(duplicate, target, relative=False)[0]
    cmds.makeIdentity(duplicate, apply=True, t=1, r=1, s=1)

    new_shapes = cmds.listRelatives(duplicate, shapes=True, fullPath=True) or []
    old_shapes = cmds.listRelatives(target, shapes=True, fullPath=True) or []
    if old_shapes:
        cmds.delete(old_shapes)

    nice = target.split("|")[-1] + "Shape"
    moved = 0
    for shape in new_shapes:
        shape = cmds.rename(shape, nice)
        cmds.parent(shape, target, add=True, shape=True)
        moved += 1

    cmds.delete(duplicate)
    return moved


def replace_shapes(targets, replacements, mirror=False):
    """여러 타깃의 셰이프를 한 번에 바꾼다. `(replaced, messages)`.

    ── 짝 짓는 규칙 (v01.16) ──────────────────────────────────────────────
    - replacement 가 **하나**면 모든 타깃이 그 모양이 된다(원본과 같다).
    - 여럿이면 **리스트 순서대로 1:1**. 개수가 다르면 **적은 쪽만큼만** 하고 남는 것은
      건드리지 않는다 - 그 사실을 로그에 적는다.
      (v01.15 까지는 개수가 다르면 아예 거절했다. 사용자 요청으로 바꿨다 - 리스트에
      담아 둔 것 중 짝이 맞는 데까지 돌리는 편이 실제 작업 흐름에 맞다.)

    ── 레퍼런스 대상 (v01.22) ─────────────────────────────────────────────
    타깃이 **레퍼런스**면 셰이프를 지울 수 없으므로 셰이프 교체 대신
    `match_cv_positions` 로 **CV 만 대응 CV 에 맞춘다**(mirror 여부는 그대로 따른다).
    타깃마다 따로 판단하므로 레퍼런스와 로컬이 섞인 리스트도 한 번에 돌아간다.
    """
    targets = [t for t in (targets or [])]
    replacements = [r for r in (replacements or [])]
    messages = []

    if not targets:
        return 0, ["[WARN] Load the target shape(s) first."]
    if not replacements:
        return 0, ["[WARN] Load the replacement shape(s) first."]

    if len(replacements) > 1:
        pairs = min(len(targets), len(replacements))
        if len(targets) != len(replacements):
            messages.append(
                "[Info] {0} target(s) and {1} replacement(s) - the first {2} pair(s) "
                "are used, the rest are left alone.".format(
                    len(targets), len(replacements), pairs))
        targets = targets[:pairs]

    replaced = 0
    matched = 0
    with undo_chunk():
        for index, target in enumerate(targets):
            source = replacements[index] if len(replacements) > 1 else replacements[0]
            short = target.split("|")[-1]
            if not cmds.objExists(target):
                messages.append("[Warning] Target is gone: {0}.".format(target))
                continue
            if not cmds.objExists(source):
                messages.append("[Warning] Replacement is gone: {0}.".format(source))
                continue

            # 레퍼런스 대상은 셰이프를 지울 수 없다 -> CV 만 맞춘다.
            if is_referenced(target):
                try:
                    shapes, reason = match_cv_positions(target, source, mirror=mirror)
                except Exception as exc:                    # noqa: BLE001
                    messages.append(
                        "[Warning] {0} is referenced and its CVs could not be "
                        "moved: {1}".format(short, exc))
                    continue
                if reason:
                    messages.append(
                        "[Warning] {0} is referenced, so only its CVs can move - "
                        "skipped because {1}.".format(short, reason))
                    continue
                messages.append(
                    "[Info] {0} is referenced - matched {1} CV(s) to {2} instead of "
                    "swapping the shape node.".format(
                        short, sum(len(_cv_points(s)) for s in curve_shapes(target)),
                        source.split("|")[-1]))
                matched += 1
                continue

            try:
                moved = replace_shape(target, source, mirror=mirror)
            except Exception as exc:                        # noqa: BLE001
                messages.append("[Warning] Could not replace {0}: {1}".format(
                    short, exc))
                continue
            if moved:
                replaced += 1

    suffix = " (mirrored)" if mirror else ""
    if replaced:
        messages.append("Replaced the shape on {0} control(s){1}.".format(
            replaced, suffix))
    if matched:
        messages.append("Matched the CVs on {0} referenced control(s){1}.".format(
            matched, suffix))
    if not replaced and not matched and not messages:
        messages.append("[WARN] Nothing was replaced.")
    return replaced + matched, messages
