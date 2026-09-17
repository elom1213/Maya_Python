# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00470_MaterialTool - Copy Material 탭 (in-Maya)
#
# 흐름 : **소스 메시 M 을 기억한다(UUID) -> 대상 메시 M_i 를 담는다 -> Copy Material.**
# M 의 면마다 붙은 머티리얼이 M_i 의 같은 면에 똑같이 붙는다. 로직은 core/material_copy.py.

import maya.cmds as cmds

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
)
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01
from Framework.core.maya_undo import undo_chunk

from tools.A00470_MaterialTool.app.core import material_copy


class CopyMaterialTab(QWidget):

    def __init__(self, log_view=None, parent=None):
        super(CopyMaterialTab, self).__init__(parent)

        self.log_view = log_view

        # 소스 메시 M 은 **UUID** 로만 기억한다. 표시 이름은 필요할 때 UUID 로 다시 읽는다.
        self.source_uuid = None

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        desc = QLabel(
            "Give the target meshes the same per-face materials as the source mesh.\n"
            "The targets are assumed to be the same mesh (same face order).")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ---- 소스 메시 ------------------------------------------------
        source_box = QGroupBox("Source Mesh")
        source_layout = QHBoxLayout(source_box)

        self.le_source = QLineEdit()
        self.le_source.setReadOnly(True)
        self.le_source.setPlaceholderText("select one mesh and click Set Source")
        self.le_source.setToolTip(
            "The source is remembered by its UUID, so renaming or reparenting it\n"
            "later still finds the same mesh.")
        source_layout.addWidget(self.le_source, stretch=1)

        self.btn_set_source = QPushButton("Set Source")
        self.btn_set_source.setToolTip("Remember the first selected mesh as the source.")
        self.btn_set_source.clicked.connect(self.on_set_source)
        source_layout.addWidget(self.btn_set_source)

        self.btn_select_source = QPushButton("Select")
        self.btn_select_source.setToolTip("Select the remembered source mesh in the scene.")
        self.btn_select_source.clicked.connect(self.on_select_source)
        source_layout.addWidget(self.btn_select_source)

        layout.addWidget(source_box)

        # ---- 대상 메시 ------------------------------------------------
        self.tsl = JUN_mod_tsl_qt_v01(
            title="Target Meshes",
            select_label="Select Targets",
            multi_select=True,
            list_min_height=160,
            log_callback=self.log,
        )
        layout.addWidget(self.tsl, stretch=1)

        self.btn_copy = QPushButton("Copy Material")
        self.btn_copy.setMinimumHeight(32)
        self.btn_copy.setToolTip(
            "Assign the source's material to the same faces on every target mesh.\n"
            "A target with a different face count is skipped, not guessed.\n"
            "One undo step.")
        self.btn_copy.clicked.connect(self.on_copy_material)
        layout.addWidget(self.btn_copy)

    # ==================================================================
    # 로그
    # ==================================================================

    def log(self, message):
        if self.log_view is not None:
            self.log_view.appendPlainText(message)
        else:
            print(message)

    # ==================================================================
    # 소스
    # ==================================================================

    def source_node(self):
        """기억한 UUID 의 현재 롱네임(없으면 None). 표시 이름도 함께 맞춘다."""
        node = material_copy.node_from_uuid(self.source_uuid)
        if self.source_uuid:
            self.le_source.setText(material_copy.short(node) if node
                                   else "(deleted from the scene)")
        return node

    def on_set_source(self):
        selection = cmds.ls(selection=True, long=True) or []
        uuid, node = material_copy.remember_source(selection)
        if not uuid:
            self.log("[warning] Select one mesh to use as the source.")
            return

        self.source_uuid = uuid
        self.le_source.setText(material_copy.short(node))

        shapes = material_copy.mesh_shapes(node)
        engines = []
        for shape in shapes:
            names, _faces = material_copy.face_assignment(shape)
            engines.extend(n for n in names if n not in engines)
        materials = [material_copy.material_of(e) for e in engines]
        self.log("Source set : {0} ({1} material(s){2}).".format(
            material_copy.short(node), len(materials),
            ": " + ", ".join(materials) if materials else ""))
        if len(selection) > 1:
            self.log("[info] Several nodes were selected - the first mesh was used.")

    def on_select_source(self):
        node = self.source_node()
        if not node:
            self.log("[warning] No source mesh is set, or it was deleted.")
            return
        cmds.select(node, replace=True)

    # ==================================================================
    # 복사
    # ==================================================================

    def on_copy_material(self):
        if not self.source_uuid:
            self.log("[warning] Set the source mesh first.")
            return
        self.source_node()      # 표시 이름을 현재 이름으로

        targets = self.tsl.get_all_nodes() or self.tsl.get_all_items()
        if not targets:
            self.log("[warning] The target list is empty. Select the meshes and "
                     "click Select Targets.")
            return

        with undo_chunk():
            result = material_copy.copy_material(self.source_uuid, targets)

        for target, why in result["skipped"]:
            self.log("[skipped] {0} : {1}".format(material_copy.short(target), why))
        for warning in result["warnings"]:
            self.log("[warning] " + warning)

        if not result["ok"]:
            self.log("[failed] " + result["message"])
            return

        self.log(result["message"])
        self.log("  materials : " + ", ".join(result["materials"]))
