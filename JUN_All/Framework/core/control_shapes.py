# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# Framework - 컨트롤러 커브 셰이프 라이브러리 (공용). UI 비의존.
#
# 셰이프 데이터 : Framework/rules/control_shapes.json  (**모든 툴이 이 파일 하나를 공유**)
# 같은 자리에 있는 mirror_tokens.json 과 같은 규칙이다 — 데이터는 `Framework/rules/`,
# 읽는 코드는 `Framework/core/`.
#
# 원본은 Brandon Schaal 의 `bs_controls.py`(Control Curves Tool) 가 클래스 변수로 들고 있던
# `controlNames` + `cvTuples` 다. 34종(원 35종 표기) 중 **Circle 만 CV 가 없다** — 그것은
# `cmds.circle` 로 만드는 3차 커브라 CV 좌표가 아니라 명령으로 그린다. 나머지 33종은 **degree 1**
# 커브 하나이고, Gear 만 예외로 원 셰이프 하나를 더 붙인다(원본과 같다).
#
# ── 왜 툴 밖에 두나 ─────────────────────────────────────────────────────────
# 컨트롤러 셰이프는 A00400_CurveTool 만의 것이 아니다. A00460_ControllerTool · A00130 ·
# A00145 처럼 컨트롤러를 만드는 툴이면 같은 라이브러리를 쓰는 게 맞다. `dev/build_release.py`
# 가 **툴 하나 + Framework** 를 복사하므로 여기 두면 어느 툴 릴리스에도 함께 따라간다.
#
# ── maya 없이도 import 된다 ─────────────────────────────────────────────────
# 이름·좌표를 읽는 것(`names()` · `points()`)은 순수 파이썬이다. 커브를 실제로 그리는
# `build()` 에서만 maya.cmds 를 쓴다(그 안에서 import). 그래서 데이터 검사는 마야 없이도 된다.

import json
import os


#: 이름만 있고 CV 좌표가 없는 셰이프 - cmds.circle 로 그린다
CIRCLE = "Circle"

#: Gear 는 degree 1 커브에 원 셰이프 하나를 더 붙인다(원본 bs_controls 와 같다)
GEAR = "Gear"

#: Circle 기본값 (원본: d=3, r=2, nr=[0,1,0])
CIRCLE_RADIUS = 2.0
CIRCLE_NORMAL = (0.0, 1.0, 0.0)

#: Gear 에 덧붙이는 원
GEAR_CIRCLE_RADIUS = 0.9

#: Framework/core/ 기준 -> Framework/rules/control_shapes.json
_JSON_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "rules", "control_shapes.json"))

# 읽은 데이터를 한 번만 담아 둔다(파일은 66KB - 매번 파싱할 이유가 없다).
_CACHE = None


def json_path():
    return _JSON_PATH


def load(reload_data=False):
    """셰이프 데이터를 읽는다. `(names, shapes, message)`.

    names  : 메뉴에 그대로 쓰는 순서 있는 이름 목록
    shapes : {이름: [(x, y, z), ...]} - Circle 은 여기 없다(명령으로 그린다)
    파일이 없거나 깨졌으면 **빈 목록 + 경고 문자열**을 돌려준다(예외를 던지지 않는다).
    """
    global _CACHE
    if _CACHE is not None and not reload_data:
        return _CACHE

    if not os.path.exists(_JSON_PATH):
        return [], {}, "[Warning] control_shapes.json not found: {0}".format(_JSON_PATH)

    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:                                # noqa: BLE001
        return [], {}, "[Warning] Could not read control_shapes.json ({0}).".format(exc)

    names = list(data.get("names") or [])
    shapes = {}
    for name, points in (data.get("shapes") or {}).items():
        shapes[name] = [tuple(float(v) for v in p) for p in points]

    # 이름 목록에만 있고 좌표가 없는 것은 Circle 뿐이어야 한다.
    unknown = [n for n in names if n not in shapes and n != CIRCLE]
    message = "{0} control shape(s) loaded.".format(len(names))
    if unknown:
        message = "[Warning] No CV data for: {0}.".format(", ".join(unknown))

    _CACHE = (names, shapes, message)
    return _CACHE


def names():
    """셰이프 이름 목록(파일 순서 그대로)."""
    return list(load()[0])


def points(name):
    """그 셰이프의 CV 좌표 목록. 없으면 빈 목록(Circle 포함)."""
    return list(load()[1].get(name) or [])


def has(name):
    """이 이름으로 커브를 그릴 수 있나."""
    return name == CIRCLE or bool(load()[1].get(name))


def build(name, thickness=1.0, curve_name=None):
    """셰이프 하나를 씬에 그린다. 만들어진 **트랜스폼 이름**을 돌려준다.

    name      : names() 의 이름 하나
    thickness : 1.0 보다 크면 셰이프의 `lineWidth` 에 넣는다(뷰포트 표시 굵기).
    curve_name: 주면 그 이름으로 rename 한다(마야가 번호를 붙일 수 있다).

    씬을 바꾸므로 호출부가 `undo_chunk()` 안에서 부르는 것을 권한다.
    """
    import maya.cmds as cmds

    if not has(name):
        raise ValueError("Unknown control shape: {0}".format(name))

    if name == CIRCLE:
        # 원본과 같은 3차 원. ch=False 로 makeNurbCircle 히스토리를 남기지 않는다.
        crv = cmds.circle(degree=3, radius=CIRCLE_RADIUS, normal=CIRCLE_NORMAL,
                          constructionHistory=False)[0]
    else:
        crv = cmds.curve(degree=1, point=points(name))

    if name == GEAR:
        # Gear 만 셰이프가 둘이다 - 톱니(degree 1) + 안쪽 원.
        circle = cmds.circle(radius=GEAR_CIRCLE_RADIUS, normal=CIRCLE_NORMAL,
                             constructionHistory=False)[0]
        circle_shape = cmds.listRelatives(circle, shapes=True, fullPath=True)[0]
        circle_shape = cmds.rename(circle_shape, crv + "CircleShape")
        cmds.parent(circle_shape, crv, add=True, shape=True)
        cmds.delete(circle)

    if float(thickness) > 1.0:
        for shape in cmds.listRelatives(crv, shapes=True, fullPath=True) or []:
            try:
                cmds.setAttr(shape + ".lineWidth", float(thickness))
            except Exception:                               # noqa: BLE001
                pass

    if curve_name:
        crv = cmds.rename(crv, curve_name)
    return crv
