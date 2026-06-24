# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00260_ConstraintConverter - ConstraintData + 옵션 -> UE Control Rig Parent Constraint 노드 텍스트

from dataclasses import dataclass

from .template_engine import TemplateEngine


# 샘플(ref_/smaple.py)의 그래프 경로. UE 에 붙여넣을 때 엔진이 현재 그래프로 다시
# 매핑하므로 실제 값은 중요하지 않다(노드 이름만 고유하면 된다).
DEFAULT_GRAPH_PATH = (
    "/Game/AV_test_02_CHN/test_06_CtrlRig.test_06_CtrlRig:RigVMModel"
)

# UE Control Rig 의 EConstraintInterpType 값
INTERP_TYPES = ("Average", "Shortest")


@dataclass
class ConvertOptions:
    """변환 시 모든 컨스트레인트에 공통 적용되는 UI 옵션."""
    trans_filter    : bool = True
    rot_filter      : bool = False
    scale_filter    : bool = False
    maintain_offset : bool = True
    interp_type     : str  = "Shortest"
    weight          : float = 1.0
    graph_path      : str  = DEFAULT_GRAPH_PATH


def _ue_bool(value):
    # 샘플의 표기 규칙: 참은 "True", 거짓은 "false"
    return "True" if value else "false"


class NodeBuilder:
    """세 개의 템플릿 문자열로 노드 텍스트를 만든다."""

    def __init__(self, node_tmpl, parent_decl_tmpl, parent_def_tmpl):
        self.node_tmpl = node_tmpl
        self.parent_decl_tmpl = parent_decl_tmpl
        self.parent_def_tmpl = parent_def_tmpl

    # ------------------------------------------------------------------

    def build_node(self, data, options, node_name, pos_x, pos_y):
        """ConstraintData 하나를 UE 노드 텍스트로 변환."""

        graph = options.graph_path
        n = len(data.targets)

        parents_decl   = self._build_parents_decl(graph, node_name, n)
        parents_def    = self._build_parents_def(graph, node_name, data.targets)
        parents_subpins = self._build_parents_subpins(n)

        replacements = {
            "GRAPH"            : graph,
            "NODE"             : node_name,
            "CHILD"            : data.child,
            "WEIGHT"           : "{0:.6f}".format(options.weight),
            "INTERP_TYPE"      : options.interp_type,
            "MAINTAIN_OFFSET"  : _ue_bool(options.maintain_offset),
            "TRANS_FILTER"     : _ue_bool(options.trans_filter),
            "ROT_FILTER"       : _ue_bool(options.rot_filter),
            "SCALE_FILTER"     : _ue_bool(options.scale_filter),
            "POS_X"            : "{0:.6f}".format(pos_x),
            "POS_Y"            : "{0:.6f}".format(pos_y),
            "PARENTS_DECL"     : parents_decl,
            "PARENTS_DEF"      : parents_def,
            "PARENTS_SUBPINS"  : parents_subpins,
        }

        return TemplateEngine.apply(self.node_tmpl, replacements)

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
