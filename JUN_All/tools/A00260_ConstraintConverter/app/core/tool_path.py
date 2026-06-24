# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# A00260_ConstraintConverter - 읽기/쓰기 경로 묶음 (A00080_KWI_creator_V02 의 tool_path 패턴)

from dataclasses import dataclass


@dataclass
class ConverterPaths:
    read_node_tmpl      : str   # 전체 노드 템플릿
    read_parent_decl    : str   # parent 선언(stub) 조각
    read_parent_def     : str   # parent 정의 조각

    write_out           : str   # 변환 결과 출력 파일
