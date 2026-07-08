# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# A00350_ArrayCreator - 읽기/쓰기 경로 묶음 (A00260_ConstraintConverter 의 tool_path 패턴)

from dataclasses import dataclass


@dataclass
class CreatorPaths:
    read_node_tmpl : str   # 전체 array 노드 템플릿
    read_elem_decl : str   # 배열 요소 선언(stub) 조각
    read_elem_def  : str   # 배열 요소 정의(Type/Name) 조각

    write_out      : str   # 생성 결과 출력 파일
