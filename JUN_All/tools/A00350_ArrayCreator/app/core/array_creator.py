# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00350_ArrayCreator - 생성 오케스트레이터
#
# TSL 오브젝트 이름 목록 + 옵션 -> UE Control Rig Item Array 노드 텍스트 파일 생성.
# 템플릿 처리 흐름은 A00080_KWI_creator / A00260_ConstraintConverter (PathManager +
# 0010_src/0020_out) 를 따른다.

from Framework.core.path_manager import PathManager

from .tool_path import CreatorPaths
from .node_builder import NodeBuilder, ArrayOptions


class ArrayCreator:

    def __init__(self):

        self._set_path()

        self.builder = NodeBuilder(
            node_tmpl      = self._read(self.paths.read_node_tmpl),
            elem_decl_tmpl = self._read(self.paths.read_elem_decl),
            elem_def_tmpl  = self._read(self.paths.read_elem_def),
        )

    # ------------------------------------------------------------------

    def _set_path(self):
        self.pm = PathManager(
            __file__,
            read_dir  = "0010_src",
            write_dir = "0020_out",
        )

        ext = "py"
        self.paths = CreatorPaths(
            read_node_tmpl = self.pm.path("read",  "A0001_Src_array_node.{0}".format(ext)),
            read_elem_decl = self.pm.path("read",  "A0002_Src_element_decl.{0}".format(ext)),
            read_elem_def  = self.pm.path("read",  "A0003_Src_element_def.{0}".format(ext)),
            write_out      = self.pm.path("write", "A001_array_node_out.{0}".format(ext)),
        )

    @staticmethod
    def _read(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write(self, path, text):
        self.pm.ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    @staticmethod
    def _element_name(raw):
        """TSL 항목(마야 이름) -> UE 요소 이름. DAG 경로는 leaf 이름만 쓴다."""
        return raw.split("|")[-1].strip()

    # ------------------------------------------------------------------
    # 공개 API

    def build_text(self, names, options):
        """이름 목록을 UE array 노드 텍스트로 변환해 반환한다.

        반환: (text, element_names)  element_names = 실제 노드에 들어간 요소 이름 순서.
        """
        clean = [self._element_name(nm) for nm in names]
        clean = [c for c in clean if c]
        if not clean:
            return "", []
        return self.builder.build_node(clean, options), clean

    def create(self, names, options):
        """변환 후 0020_out 에 파일을 쓴다.

        반환: (text, element_names, out_path)
        """
        text, clean = self.build_text(names, options)

        if text:
            self._write(self.paths.write_out, text)

        return text, clean, self.paths.write_out
