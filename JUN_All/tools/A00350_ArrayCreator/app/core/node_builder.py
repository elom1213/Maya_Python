# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00350_ArrayCreator - 오브젝트 이름 목록 + 타입 -> UE Control Rig Item Array 노드 텍스트
#
# 참고: A0010_Src_Array_node_v01.py(정식 구조, N개 요소 단일 노드),
#       A0010_Src_Array_node_v02.py(타입 카탈로그). 요소마다 바뀌는 것은 Type/Name 의
#       DefaultValue 뿐이라, 선언(decl)/정의(def)/SubPins 조각을 요소 수만큼 반복해 조립한다.

from dataclasses import dataclass

from .template_engine import TemplateEngine


# UE 에 붙여넣으면 엔진이 현재 그래프로 경로를 다시 매핑하므로 asset 경로 값 자체는
# 중요하지 않다(노드 이름만 있으면 된다). 참고 파일 v01 의 값을 그대로 기본값으로 쓴다.
DEFAULT_ASSET = (
    "/Game/MANU/Character/CHN/Set007/Rig/V01/"
    "CTR_MANU_CH_CHN_Set007_Bottom_Driven_V01."
    "CTR_MANU_CH_CHN_Set007_Bottom_Driven_V01"
)
DEFAULT_NODE_NAME = "ItemArray_7"
DEFAULT_NODE_TITLE = "Test_array"
DEFAULT_POS_X = -492.0
DEFAULT_POS_Y = 1607.0

# ERigElementType 값 (v02 의 타입 예시). 툴의 Type 콤보 항목.
ELEMENT_TYPES = ("None", "Bone", "Null", "Control", "Curve",
                 "Reference", "Connector", "Socket")
DEFAULT_TYPE = "Bone"


@dataclass
class ArrayOptions:
    """array 노드 생성 옵션(모든 요소 공통)."""
    elem_type  : str   = DEFAULT_TYPE
    node_title : str   = DEFAULT_NODE_TITLE
    node_name  : str   = DEFAULT_NODE_NAME
    asset      : str   = DEFAULT_ASSET
    pos_x      : float = DEFAULT_POS_X
    pos_y      : float = DEFAULT_POS_Y


class NodeBuilder:
    """세 조각 템플릿(node / element decl / element def)으로 array 노드 텍스트를 만든다."""

    def __init__(self, node_tmpl, elem_decl_tmpl, elem_def_tmpl):
        self.node_tmpl = node_tmpl
        self.elem_decl_tmpl = elem_decl_tmpl
        self.elem_def_tmpl = elem_def_tmpl

    def build_node(self, names, options):
        """이름 목록(요소 순서) + 옵션 -> 단일 array 노드 텍스트."""
        n = len(names)
        return TemplateEngine.apply(self.node_tmpl, {
            "NODE"       : options.node_name,
            "ASSET"      : options.asset,
            "NODE_TITLE" : options.node_title,
            "POS_X"      : "{0:.6f}".format(options.pos_x),
            "POS_Y"      : "{0:.6f}".format(options.pos_y),
            "VALUE_DECL" : self._build_decl(options, n),
            "VALUE_DEF"  : self._build_def(options, names),
            "SUBPINS"    : self._build_subpins(n),
        })

    def _build_decl(self, options, count):
        parts = []
        for idx in range(count):
            parts.append(TemplateEngine.apply(self.elem_decl_tmpl, {
                "ASSET": options.asset,
                "NODE" : options.node_name,
                "IDX"  : idx,
            }))
        return "".join(parts)

    def _build_def(self, options, names):
        parts = []
        for idx, name in enumerate(names):
            parts.append(TemplateEngine.apply(self.elem_def_tmpl, {
                "ASSET": options.asset,
                "NODE" : options.node_name,
                "IDX"  : idx,
                "TYPE" : options.elem_type,
                "NAME" : name,
            }))
        return "".join(parts)

    @staticmethod
    def _build_subpins(count):
        return "".join(
            "      SubPins({0})=\"/Script/RigVMDeveloper.RigVMPin'{0}'\"\n".format(idx)
            for idx in range(count)
        )
