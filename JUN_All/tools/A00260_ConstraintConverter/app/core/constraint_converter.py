# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00260_ConstraintConverter - 변환 오케스트레이터
#
# 마야 컨스트레인트 노드 목록 + 옵션 -> UE Control Rig 노드 텍스트 파일 생성.
# 템플릿 처리 흐름은 A00080_KWI_creator_V02 (PathManager + 0010_src/0020_out) 를 따른다.

from Framework.core.path_manager import PathManager

from .tool_path import ConverterPaths
from .node_builder import NodeBuilder, ConvertOptions, node_spec
from . import constraint_reader as reader


class ConstraintConverter:

    def __init__(self):

        self._set_path()

        # 노드 배치 시작점/간격.
        # 여러 컨스트레인트를 가로로 나열하고, nodes_per_row(4) 개를 넘으면 줄을 바꿔 아래로 내린다.
        # 간격은 ref_/sample_03.py 의 두 노드 가로 간격(X 약 307)을 참고해 닫힘 노드가 겹치지 않게 잡음.
        self.node_pos_start_x = 336.0
        self.node_pos_start_y = 16.0
        self.node_pos_offset_x = 340.0
        self.node_pos_offset_y = 280.0
        self.nodes_per_row = 4

        # UE 에서 붙여넣을 노드 이름 접두사는 노드 종류(NODE_TYPES)에서 가져온다.

        self.builder = NodeBuilder(
            node_tmpls = {
                "Parent"   : self._read(self.paths.read_node_tmpl),
                "Position" : self._read(self.paths.read_position_tmpl),
                "Rotation" : self._read(self.paths.read_rotation_tmpl),
            },
            parent_decl_tmpl = self._read(self.paths.read_parent_decl),
            parent_def_tmpl  = self._read(self.paths.read_parent_def),
            link_tmpl        = self._read(self.paths.read_link_tmpl),
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
            read_node_tmpl     = self.pm.path("read",  "A0001_Src_constraint_node.{0}".format(ext)),
            read_parent_decl   = self.pm.path("read",  "A0002_Src_parent_decl.{0}".format(ext)),
            read_parent_def    = self.pm.path("read",  "A0003_Src_parent_def.{0}".format(ext)),
            read_link_tmpl     = self.pm.path("read",  "A0004_Src_link.{0}".format(ext)),
            read_position_tmpl = self.pm.path("read",  "A0005_Src_position_node.{0}".format(ext)),
            read_rotation_tmpl = self.pm.path("read",  "A0006_Src_rotation_node.{0}".format(ext)),
            write_out          = self.pm.path("write", "A001_constraint_nodes_out.{0}".format(ext)),
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
        node_names = []

        prefix = node_spec(options.constraint_type)["prefix"]

        idx = 0
        for cn in constraint_nodes:
            data = reader.read_constraint(cn)
            if data is None or not data.targets:
                continue

            node_name = "{0}{1}".format(prefix, idx + 1)
            node_names.append(node_name)

            # 가로로 나열 -> nodes_per_row 마다 다음 줄(아래)로 이동
            col = idx % self.nodes_per_row
            row = idx // self.nodes_per_row
            pos_x = self.node_pos_start_x + self.node_pos_offset_x * col
            pos_y = self.node_pos_start_y + self.node_pos_offset_y * row

            block = self.builder.build_node(
                data,
                options,
                node_name = node_name,
                pos_x = pos_x,
                pos_y = pos_y,
            )
            blocks.append(block)
            infos.append((data.name, data.child, len(data.targets)))
            idx += 1

        # 생성된 노드들을 생성 순서대로 ExecutePin -> ExecutePin 으로 연결한다.
        # (sample_04.py 의 RigVMLink 참고. 노드가 2개 미만이면 링크 없음.)
        links = self.builder.build_links(options.graph_path, node_names)

        combined = "\n".join(blocks + links)
        return combined, infos

    def convert(self, constraint_nodes, options):
        """변환 후 0020_out 에 파일을 쓴다.

        반환: (combined_text, infos, out_path)
        """
        combined, infos = self.build_text(constraint_nodes, options)

        if combined:
            self._write(self.paths.write_out, combined)

        return combined, infos, self.paths.write_out
