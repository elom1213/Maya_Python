# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00640_AttrSlider core - 선택 → 섹션(노드) · 행(어트리뷰트) / 값 읽기 · 쓰기 (maya.cmds)
#
# 계획서 docs/plans/A00640_AttrSlider_plan.md §1 · §3 · §4.
# UI 비의존: 위젯을 모른다. 행(AttrRow)에 "무엇을 어떻게 그릴지" 재료만 담는다.
#
# 채널박스 판정 · 종류 표 · enum 파싱은 A00145 attr_value_manager / connect_manager 와 같은 규칙이다
# (툴 간 import 금지라 여기 따로 둔다 - Framework 로 합치는 것은 계획서 §6 3단계).

import maya.cmds as cmds

from Framework.core import fbx_name
from Framework.core import maya_fbx_names

KIND_FLOAT = "float"
KIND_INT = "int"
KIND_BOOL = "bool"
KIND_ENUM = "enum"

_TYPE_KIND = {
    "double": KIND_FLOAT, "float": KIND_FLOAT,
    "doubleLinear": KIND_FLOAT, "doubleAngle": KIND_FLOAT,
    "floatLinear": KIND_FLOAT, "floatAngle": KIND_FLOAT, "time": KIND_FLOAT,
    "long": KIND_INT, "short": KIND_INT, "byte": KIND_INT, "char": KIND_INT,
    "bool": KIND_BOOL,
    "enum": KIND_ENUM,
}
_ANGLE_TYPES = ("doubleAngle", "floatAngle")

# 행 상태 - 마야 채널박스 색과 같은 뜻
ST_FREE = "free"          # 그냥 값
ST_KEYED = "keyed"        # 시간 커브 키 / 애님 레이어 - setAttr 는 되지만 시간을 옮기면 커브 값으로 돌아간다
ST_DRIVEN = "driven"      # 연결 · 드리븐 키 · 표현식 - 못 바꾼다(드리븐 키는 setAttr 가 되지만 곧 덮어쓰인다)
ST_LOCKED = "locked"      # 잠김
EDITABLE_STATES = (ST_FREE, ST_KEYED)

SEC_NODE = "node"
SEC_SHAPE = "shape"
SEC_BLENDSHAPE = "blendShape"

MAX_NODES = 30

NAMES_NICE = "nice"
NAMES_LONG = "long"


# ------------------------------------------------------------------ 이름

def decode(name):
    """FBXASC 를 푼 글자. 못 풀면 원래 이름."""
    try:
        return fbx_name.decode(name)
    except Exception:  # noqa: BLE001
        return name


def short_name(node):
    return node.split("|")[-1]


def node_label(node):
    return decode(short_name(node))


# ------------------------------------------------------------------ 종류 · 상태

def attr_kind(node, attr):
    """node.attr 의 종류(KIND_*) 또는 None(다루지 않는 타입 / 멀티 / compound 부모)."""
    try:
        if not cmds.attributeQuery(attr, node=node, exists=True):
            return None
        if cmds.attributeQuery(attr, node=node, multi=True):
            return None
        if cmds.attributeQuery(attr, node=node, numberOfChildren=True):
            return None
        at = cmds.attributeQuery(attr, node=node, attributeType=True)
    except Exception:  # noqa: BLE001
        return None
    return _TYPE_KIND.get(at)


def enum_items(node, attr):
    """enum 항목 [(이름, 값)]. `A:B=5:C` -> A=0, B=5, C=6 (마야 규칙)."""
    try:
        raw = cmds.attributeQuery(attr, node=node, listEnum=True) or []
    except Exception:  # noqa: BLE001
        return []
    items = []
    value = 0
    for token in (raw[0].split(":") if raw else []):
        if not token:
            continue
        name = token
        if "=" in token:
            head, num = token.rsplit("=", 1)
            try:
                value = int(num)
                name = head
            except ValueError:
                pass
        items.append((name, value))
        value += 1
    return items


def plug_state(plug):
    """(상태, 소스 노드 또는 None).

    실측(2026-11-20): animCurveT* · animBlendNode* 소스는 setAttr 가 되지만 시간을 옮기면 돌아간다 = Keyed.
    animCurveU*(드리븐 키)는 setAttr 가 에러 없이 되지만 곧 드라이버가 덮어쓴다 = Driven. 그 밖의 연결 · 잠금은 에러.
    """
    try:
        if cmds.getAttr(plug, lock=True):
            return ST_LOCKED, None
    except Exception:  # noqa: BLE001
        return ST_LOCKED, None
    src = cmds.listConnections(plug, source=True, destination=False, skipConversionNodes=True) or []
    if not src:
        return ST_FREE, None
    node = src[0]
    node_type = cmds.nodeType(node)
    if node_type.startswith("animCurveT") or node_type.startswith("animBlendNode"):
        return ST_KEYED, node
    return ST_DRIVEN, node


def channel_box_attrs(node):
    """채널박스에 보이는 어트리뷰트(listAttr 순서). 키어블 + 비키어블 표시, hidden · 중첩 이름 제외."""
    raw = (cmds.listAttr(node, keyable=True) or []) + (cmds.listAttr(node, channelBox=True) or [])
    out = []
    seen = set()
    for attr in raw:
        if "." in attr or attr in seen:
            continue
        seen.add(attr)
        try:
            if cmds.attributeQuery(attr, node=node, hidden=True):
                continue
        except Exception:  # noqa: BLE001
            continue
        out.append(attr)
    return out


# ------------------------------------------------------------------ 행 · 섹션

class AttrRow(object):
    """어트리뷰트 한 줄의 재료."""

    def __init__(self, node, attr, kind, raw_name, nice_name, long_name, attr_type="",
                 hard_min=None, hard_max=None, soft_min=None, soft_max=None, items=None,
                 target_index=None):
        self.node = node
        self.attr = attr                    # setAttr 에 쓰는 이름 (타겟은 weight[i])
        self.plug = "{0}.{1}".format(node, attr)
        self.kind = kind
        self.attr_type = attr_type
        self.raw_name = raw_name            # 마야 이름(툴팁 · Filter)
        self.nice_name = nice_name          # 풀린 nice 이름
        self.long_name = long_name          # 풀린 long 이름
        self.hard_min = hard_min
        self.hard_max = hard_max
        self.soft_min = soft_min
        self.soft_max = soft_max
        self.items = items or []            # enum [(풀린 이름, 값)]
        self.raw_items = []                 # enum [(마야 이름, 값)]
        self.target_index = target_index    # blendShape 타겟이면 인덱스
        self.state = ST_FREE
        self.source = None
        self.refresh_state()

    @property
    def is_angle(self):
        return self.attr_type in _ANGLE_TYPES

    @property
    def editable(self):
        return self.state in EDITABLE_STATES

    @property
    def encoded(self):
        return fbx_name.is_encoded(self.raw_name)

    def label(self, mode=NAMES_NICE):
        return self.long_name if mode == NAMES_LONG else self.nice_name

    def refresh_state(self):
        self.state, self.source = plug_state(self.plug)
        return self.state

    def range_key(self):
        """사용자 범위 저장 키 = 마야 어트리뷰트 이름(타겟은 별칭)."""
        return self.raw_name


class Section(object):
    def __init__(self, node, kind, rows):
        self.node = node
        self.kind = kind
        self.rows = rows
        self.node_type = cmds.nodeType(node)

    @property
    def label(self):
        return node_label(self.node)

    @property
    def raw_label(self):
        return short_name(self.node)


def _query(attr, node, **flag):
    try:
        return cmds.attributeQuery(attr, node=node, **flag)
    except Exception:  # noqa: BLE001
        return None


def _range_of(node, attr):
    out = {}
    for key, exists, value in (("hard_min", "minExists", "minimum"), ("hard_max", "maxExists", "maximum"),
                               ("soft_min", "softMinExists", "softMin"), ("soft_max", "softMaxExists", "softMax")):
        if _query(attr, node, **{exists: True}):
            got = _query(attr, node, **{value: True})
            out[key] = got[0] if got else None
        else:
            out[key] = None
    return out


def make_row(node, attr):
    """node.attr 의 행. 다루지 않는 어트리뷰트면 None."""
    kind = attr_kind(node, attr)
    if kind is None:
        return None
    long_raw = _query(attr, node, longName=True) or attr
    nice_raw = _query(attr, node, niceName=True) or long_raw
    long_name = decode(long_raw)
    # FBXASC 이름은 niceName 도 FBXASC 그대로다(실측) - 풀린 long 이름을 쓴다
    nice_name = long_name if fbx_name.is_encoded(long_raw) else nice_raw
    kw = {}
    if kind in (KIND_FLOAT, KIND_INT):
        kw = _range_of(node, attr)
    row = AttrRow(node, long_raw, kind, long_raw, nice_name, long_name,
                  attr_type=_query(attr, node, attributeType=True) or "", **kw)
    if kind == KIND_ENUM:
        row.raw_items = enum_items(node, attr)
        row.items = [(decode(n), v) for n, v in row.raw_items]
    return row


def blendshape_rows(bs):
    """envelope + 타겟 웨이트(별칭을 풀어서)."""
    rows = []
    env = make_row(bs, "envelope")
    if env:
        rows.append(env)
    weight_range = _range_of(bs, "weight")
    for index, alias in maya_fbx_names.blendshape_targets(bs):
        name = decode(alias)
        rows.append(AttrRow(bs, "weight[{0}]".format(index), KIND_FLOAT, alias, name, name,
                            attr_type="double", target_index=index, **weight_range))
    return rows


def node_rows(node):
    rows = []
    for attr in channel_box_attrs(node):
        row = make_row(node, attr)
        if row:
            rows.append(row)
    return rows


def _long(node):
    return (cmds.ls(node, long=True) or [node])[0]


def _shapes_of(node):
    if not cmds.objectType(node, isAType="transform"):
        return []
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True, noIntermediate=True) or []
    return shapes


def _blendshapes_of(node):
    shapes = [node] if cmds.objectType(node, isAType="shape") else \
        (cmds.listRelatives(node, shapes=True, fullPath=True) or [])
    if not shapes:
        return []
    return cmds.ls(cmds.listHistory(shapes, pruneDagObjects=True) or [], type="blendShape") or []


def build_sections(nodes, include_shapes=True, include_blendshapes=True, max_nodes=MAX_NODES):
    """선택(노드 이름 목록) -> ([Section], 잘린 노드 수).

    노드마다 그 노드 섹션, 켜면 셰이프 섹션(채널박스 SHAPES 처럼) · 히스토리의 blendShape 섹션(INPUTS 처럼).
    같은 노드는 한 번만. 행이 없는 섹션은 뺀다. 고른 노드가 max_nodes 를 넘으면 앞에서 자른다.
    """
    picked = []
    for n in nodes:
        if cmds.objExists(n):
            ln = _long(n)
            if ln not in picked:
                picked.append(ln)
    dropped = max(0, len(picked) - max_nodes)
    picked = picked[:max_nodes]

    order = []        # (node, kind)
    seen = set()

    def add(node, kind):
        ln = _long(node)
        if ln in seen:
            return
        seen.add(ln)
        order.append((ln, kind))

    for node in picked:
        if cmds.nodeType(node) == "blendShape":
            add(node, SEC_BLENDSHAPE)
            continue
        add(node, SEC_NODE)
        if include_shapes:
            for shape in _shapes_of(node):
                add(shape, SEC_SHAPE)
        if include_blendshapes:
            for bs in _blendshapes_of(node):
                add(bs, SEC_BLENDSHAPE)

    sections = []
    for node, kind in order:
        rows = blendshape_rows(node) if kind == SEC_BLENDSHAPE else node_rows(node)
        if rows:
            sections.append(Section(node, kind, rows))
    return sections, dropped


def selected_nodes():
    return cmds.ls(selection=True, long=True, objectsOnly=True) or []


# ------------------------------------------------------------------ 값

def get_value(row):
    try:
        value = cmds.getAttr(row.plug)
    except Exception:  # noqa: BLE001
        return None
    if row.kind == KIND_BOOL:
        return bool(value)
    if row.kind in (KIND_INT, KIND_ENUM):
        return int(value)
    return float(value)


def clamp(row, value):
    """하드 범위로 자르고 종류에 맞게(int 반올림 · bool) 바꾼다 - setAttr 가 거부할 값을 넣지 않는다."""
    if row.kind == KIND_BOOL:
        return bool(value)
    value = float(value)
    if row.hard_min is not None:
        value = max(value, float(row.hard_min))
    if row.hard_max is not None:
        value = min(value, float(row.hard_max))
    if row.kind in (KIND_INT, KIND_ENUM):
        return int(round(value))
    return value


def set_value(row, value, key=False):
    """값을 쓴다. 반환 = 실제로 쓴 값. 못 바꾸는 행(Driven · Locked)이면 RuntimeError."""
    row.refresh_state()
    if not row.editable:
        raise RuntimeError("{0} is {1}{2} - not changed.".format(
            row.plug, row.state, " by " + row.source if row.source else ""))
    value = clamp(row, value)
    cmds.setAttr(row.plug, value)
    if key:
        cmds.setKeyframe(row.plug)
        row.refresh_state()
    return value


def set_key(row):
    if not row.editable:
        raise RuntimeError("{0} is {1} - no key set.".format(row.plug, row.state))
    cmds.setKeyframe(row.plug)
    row.refresh_state()
