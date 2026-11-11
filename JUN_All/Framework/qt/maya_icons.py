# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-11
# Framework.qt - 노드 타입 → 마야 아웃라이너 아이콘 (QIcon)
#
#   from Framework.qt.maya_icons import node_icon
#   item.setIcon(0, node_icon("joint"))
#
# 마야 Qt 리소스의 `:/out_<nodeType>.png`(20x20) 을 쓴다. 실측(mayapy 2024, 2026-11-11):
#   - transform · mesh · joint · nurbsCurve · nurbsSurface · locator · camera · ikHandle · parentConstraint ·
#     objectSet · shadingEngine · lambert · displayLayer · reference · animCurveTL · dagNode · default 는 **있다**.
#   - blendShape · skinCluster · network · geometryFilter · deformer 는 **없다**. svg 판(`:/<type>.svg`)은 전부 없다.
#   - mayapy + QApplication 에서도 읽힌다 → 오프스크린 시험 가능.
# 없는 타입의 대체 순서: out_<type> → 상속 타입을 아래(자기)부터 위로 → DAG 면 out_dagNode → out_default.
# 타입마다 한 번만 찾고 캐시한다(리소스 조회 · nodeType 질의가 행마다 돌지 않게).

from Framework.qt.qt import QIcon, QPixmap

try:
    import maya.cmds as cmds
except ImportError:  # 마야 밖(시험 · 문서 빌드)
    cmds = None

DEFAULT_ICON = "out_default.png"
DAG_ICON = "out_dagNode.png"

_CACHE = {}       # node_type -> QIcon
_NAMES = {}       # node_type -> 리소스 이름


def has_resource(name):
    """`:/name` 리소스가 있는가(png 파일 이름 그대로)."""
    return not QPixmap(":/" + name).isNull()


def _inherited(node_type):
    if cmds is None:
        return []
    try:
        return list(cmds.nodeType(node_type, inherited=True, isTypeName=True) or [])
    except RuntimeError:   # 모르는 타입(플러그인이 안 올라온 노드 등)
        return []


def icon_name(node_type):
    """타입의 아웃라이너 아이콘 리소스 이름(예: 'out_joint.png'). 대체 순서는 머리말."""
    if node_type in _NAMES:
        return _NAMES[node_type]
    name = None
    if node_type and has_resource("out_{0}.png".format(node_type)):
        name = "out_{0}.png".format(node_type)
    else:
        chain = _inherited(node_type)
        for parent in reversed(chain[:-1] if chain and chain[-1] == node_type else chain):
            if has_resource("out_{0}.png".format(parent)):
                name = "out_{0}.png".format(parent)
                break
        if name is None:
            name = DAG_ICON if "dagNode" in chain and has_resource(DAG_ICON) else DEFAULT_ICON
    _NAMES[node_type] = name
    return name


def node_icon(node_type):
    """타입의 QIcon(캐시). 리소스가 하나도 없는 환경이면 빈 QIcon."""
    icon = _CACHE.get(node_type)
    if icon is None:
        icon = QIcon(":/" + icon_name(node_type))
        _CACHE[node_type] = icon
    return icon


def clear_cache():
    _CACHE.clear()
    _NAMES.clear()
