# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-10
# A00260_ConstraintConverter - ConstraintData + 옵션 -> UE Control Rig Constraint 노드 텍스트
#
# v01.05 : Parent 외에 Position / Rotation 컨스트레인트 노드 지원 + 축(X/Y/Z)별 필터

from dataclasses import dataclass

from .template_engine import TemplateEngine


# 샘플(ref_/smaple.py)의 그래프 경로. UE 에 붙여넣을 때 엔진이 현재 그래프로 다시
# 매핑하므로 실제 값은 중요하지 않다(노드 이름만 고유하면 된다).
DEFAULT_GRAPH_PATH = (
    "/Game/AV_test_02_CHN/test_06_CtrlRig.test_06_CtrlRig:RigVMModel"
)

# UE Control Rig 의 EConstraintInterpType 값
INTERP_TYPES = ("Average", "Shortest")

# 생성할 UE 노드 종류.
#   channels : 이 노드가 실제로 필터링하는 채널 ("trans"/"rot"/"scale").
#              UI 는 여기 없는 채널의 축 체크박스를 비활성화한다.
#   interp   : AdvancedSettings(InterpolationType) 핀 유무.
#              Position 노드에는 AdvancedSettings 자체가 없다.
#   prefix   : 생성되는 노드 이름 접두사.
NODE_TYPES = {
    "Parent": {
        "channels" : ("trans", "rot", "scale"),
        "interp"   : True,
        "prefix"   : "ParentConstraint_",
    },
    "Position": {
        "channels" : ("trans",),
        "interp"   : False,
        "prefix"   : "PositionConstraint_",
    },
    "Rotation": {
        "channels" : ("rot",),
        "interp"   : True,
        "prefix"   : "RotationConstraint_",
    },
}

# UI 표시 순서(dict 순서에 의존하지 않기 위해 명시)
NODE_TYPE_ORDER = ("Parent", "Position", "Rotation")

# 채널 key -> UI 라벨
CHANNELS = (
    ("trans", "Translate"),
    ("rot",   "Rotate"),
    ("scale", "Scale"),
)

AXES = ("x", "y", "z")


@dataclass
class ConvertOptions:
    """변환 시 모든 컨스트레인트에 공통 적용되는 UI 옵션."""
    constraint_type : str = "Parent"      # NODE_TYPES 의 key

    # 축별 필터. Position 은 trans_*, Rotation 은 rot_* 만 사용한다.
    trans_x : bool = True
    trans_y : bool = True
    trans_z : bool = True
    rot_x   : bool = False
    rot_y   : bool = False
    rot_z   : bool = False
    scale_x : bool = False
    scale_y : bool = False
    scale_z : bool = False

    maintain_offset : bool = True
    interp_type     : str  = "Shortest"
    weight          : float = 1.0
    graph_path      : str  = DEFAULT_GRAPH_PATH

    def axes(self, channel):
        """채널("trans"/"rot"/"scale")의 (x, y, z) 체크 상태 튜플."""
        return tuple(
            getattr(self, "{0}_{1}".format(channel, axis)) for axis in AXES
        )


def node_spec(constraint_type):
    """알 수 없는 타입이면 Parent 로 폴백한 NODE_TYPES 항목."""
    return NODE_TYPES.get(constraint_type, NODE_TYPES["Parent"])


def _ue_bool(value):
    # 샘플의 표기 규칙: 참은 "True", 거짓은 "false"
    return "True" if value else "false"


class NodeBuilder:
    """템플릿 문자열들로 노드 텍스트를 만든다.

    node_tmpls: {"Parent": text, "Position": text, "Rotation": text}
    """

    def __init__(self, node_tmpls, parent_decl_tmpl, parent_def_tmpl, link_tmpl):
        self.node_tmpls = node_tmpls
        self.parent_decl_tmpl = parent_decl_tmpl
        self.parent_def_tmpl = parent_def_tmpl
        self.link_tmpl = link_tmpl

    # ------------------------------------------------------------------

    def build_links(self, graph, node_names):
        """노드들을 생성 순서대로 ExecutePin -> ExecutePin 으로 잇는 RigVMLink 블록 리스트.

        node_names[i].ExecutePin -> node_names[i+1].ExecutePin 으로 체인을 만든다.
        노드가 2개 미만이면 연결할 게 없으므로 빈 리스트를 반환한다.
        """
        links = []
        for idx in range(len(node_names) - 1):
            links.append(TemplateEngine.apply(self.link_tmpl, {
                "GRAPH"       : graph,
                "IDX"         : idx,
                "SOURCE_NODE" : node_names[idx],
                "TARGET_NODE" : node_names[idx + 1],
            }))
        return links

    # ------------------------------------------------------------------

    def build_node(self, data, options, node_name, pos_x, pos_y):
        """ConstraintData 하나를 UE 노드 텍스트로 변환."""

        graph = options.graph_path
        ctype = options.constraint_type
        if ctype not in self.node_tmpls:
            ctype = "Parent"
        spec = NODE_TYPES[ctype]
        n = len(data.targets)

        replacements = {
            "GRAPH"            : graph,
            "NODE"             : node_name,
            "CHILD"            : data.child,
            "WEIGHT"           : "{0:.6f}".format(options.weight),
            "MAINTAIN_OFFSET"  : _ue_bool(options.maintain_offset),
            "POS_X"            : "{0:.6f}".format(pos_x),
            "POS_Y"            : "{0:.6f}".format(pos_y),
            "PARENTS_DECL"     : self._build_parents_decl(graph, node_name, n),
            "PARENTS_DEF"      : self._build_parents_def(graph, node_name, data.targets),
            "PARENTS_SUBPINS"  : self._build_parents_subpins(n),
        }

        if spec["interp"]:
            replacements["INTERP_TYPE"] = options.interp_type

        # Parent 는 채널별(Translation/Rotation/Scale) 필터 3벌을,
        # Position/Rotation 은 단일 필터 1벌(FILTER_X/Y/Z)을 갖는다.
        if ctype == "Parent":
            for channel, key in (("trans", "TRANS"), ("rot", "ROT"), ("scale", "SCALE")):
                for axis, flag in zip(AXES, options.axes(channel)):
                    replacements["{0}_{1}".format(key, axis.upper())] = _ue_bool(flag)
        else:
            channel = spec["channels"][0]
            for axis, flag in zip(AXES, options.axes(channel)):
                replacements["FILTER_{0}".format(axis.upper())] = _ue_bool(flag)

        return TemplateEngine.apply(self.node_tmpls[ctype], replacements)

    # ------------------------------------------------------------------
    # parent 배열 조립
    #
    # 샘플은 선언/정의 모두 인덱스를 내림차순(N-1 .. 0)으로 나열하고,
    # 정의 섹션에서 '첫 번째로 나열된' parent 만 bIsDynamicArray=True 를 갖는다.
    # SubPins 는 오름차순(0 .. N-1)이다. UE 직렬화 형태를 그대로 재현한다.

    def _build_parents_decl(self, graph, node_name, count):
        parts = []
        for idx in range(count - 1, -1, -1):
            parts.append(TemplateEngine.apply(self.parent_decl_tmpl, {
                "GRAPH" : graph,
                "NODE"  : node_name,
                "IDX"   : idx,
            }))
        return "".join(parts)

    def _build_parents_def(self, graph, node_name, targets):
        parts = []
        count = len(targets)
        first = True
        for idx in range(count - 1, -1, -1):
            bone, weight = targets[idx]
            dyn_line = "         bIsDynamicArray=True\n" if first else ""
            first = False
            parts.append(TemplateEngine.apply(self.parent_def_tmpl, {
                "GRAPH"         : graph,
                "NODE"          : node_name,
                "IDX"           : idx,
                "WEIGHT"        : "{0:.6f}".format(weight),
                "BONE"          : bone,
                "DYN_ARRAY_LINE": dyn_line,
            }))
        return "".join(parts)

    def _build_parents_subpins(self, count):
        lines = []
        for idx in range(count):
            lines.append(
                "      SubPins({0})=\"/Script/RigVMDeveloper.RigVMPin'{0}'\"\n".format(idx)
            )
        return "".join(lines)
