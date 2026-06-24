# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00260_ConstraintConverter - 변환 오케스트레이터
#
# 마야 컨스트레인트 노드 목록 + 옵션 -> UE Control Rig 노드 텍스트 파일 생성.
# 템플릿 처리 흐름은 A00080_KWI_creator_V02 (PathManager + 0010_src/0020_out) 를 따른다.

from Framework.core.path_manager import PathManager

from .tool_path import ConverterPaths
from .node_builder import NodeBuilder, ConvertOptions
from . import constraint_reader as reader


class ConstraintConverter:

    def __init__(self):

        self._set_path()

        # 노드 배치 시작점/간격 (여러 컨스트레인트를 세로로 쌓는다)
        self.node_pos_start_x = 336.0
        self.node_pos_start_y = 16.0
        self.node_pos_offset_y = 420.0

        # UE 에서 붙여넣을 노드 이름 접두사
        self.node_name_prefix = "ParentConstraint_"

        self.builder = NodeBuilder(
            node_tmpl        = self._read(self.paths.read_node_tmpl),
            parent_decl_tmpl = self._read(self.paths.read_parent_decl),
            parent_def_tmpl  = self._read(self.paths.read_parent_def),
        )

    # ------------------------------------------------------------------

    def _set_path(self):
        self.pm = PathManager(
            __file__,
            read_dir  = "0010_src",
            write_dir = "0020_out",
        )

        ext = "py"
        self.paths = ConverterPaths(
            read_node_tmpl   = self.pm.path("read",  "A0001_Src_constraint_node.{0}".format(ext)),
            read_parent_decl = self.pm.path("read",  "A0002_Src_parent_decl.{0}".format(ext)),
            read_parent_def  = self.pm.path("read",  "A0003_Src_parent_def.{0}".format(ext)),
            write_out        = self.pm.path("write", "A001_constraint_nodes_out.{0}".format(ext)),
        )

    @staticmethod
    def _read(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write(self, path, text):
        self.pm.ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    # ------------------------------------------------------------------
    # 공개 API

    def build_text(self, constraint_nodes, options):
        """컨스트레인트 노드 이름 목록을 UE 텍스트로 변환해 반환한다.

        반환: (combined_text, infos)
            infos = [(constraint_name, child, target_count), ...]  변환된 항목 요약
        """
        blocks = []
        infos = []

        idx = 0
        for cn in constraint_nodes:
            data = reader.read_constraint(cn)
            if data is None or not data.targets:
                continue

            node_name = "{0}{1}".format(self.node_name_prefix, idx + 1)
            pos_y = self.node_pos_start_y + self.node_pos_offset_y * idx

            block = self.builder.build_node(
                data,
                options,
                node_name = node_name,
                pos_x = self.node_pos_start_x,
                pos_y = pos_y,
            )
            blocks.append(block)
            infos.append((data.name, data.child, len(data.targets)))
            idx += 1

        combined = "\n".join(blocks)
        return combined, infos

    def convert(self, constraint_nodes, options):
        """변환 후 0020_out 에 파일을 쓴다.

        반환: (combined_text, infos, out_path)
        """
        combined, infos = self.build_text(constraint_nodes, options)

        if combined:
            self._write(self.paths.write_out, combined)

        return combined, infos, self.paths.write_out
