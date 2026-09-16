# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00470_MaterialTool - Name Check 탭 (in-Maya)
#
# 흐름은 한 줄이다 : **메시를 담는다 -> 머티리얼을 모은다 -> 규칙으로 진단한다.**
# 규칙은 `data/profiles/*.json` 에서 고른다(코드가 아니라 데이터).
#
# 리포트는 그대로 클립보드에 들어가므로, 로그창에 찍는 글과 복사되는 글이 같다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QCheckBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QApplication,
    QColor,
    Qt,
)
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01

from tools.A00470_MaterialTool.app.core import maya_materials, profiles, reporter
from tools.A00470_MaterialTool.app.core.name_rules import NameProfile


# 트리 항목에 머티리얼 롱네임을 보관하는 역할(표시 텍스트와 분리).
NODE_ROLE = Qt.UserRole + 1

COLOR_OK = QColor(120, 200, 140)
COLOR_BAD = QColor(226, 120, 110)


class NameCheckTab(QWidget):

    def __init__(self, log_view=None, parent=None):
        super(NameCheckTab, self).__init__(parent)

        self.log_view = log_view

        # 마지막 스캔 결과 : [(머티리얼, [메시...])] 와 이름 -> 리포트
        self.assignments = []
        self.reports = {}

        self.build_ui()
        self.reload_profiles()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        # ---- 메시 리스트 --------------------------------------------
        self.tsl = JUN_mod_tsl_qt_v01(
            title="Meshes",
            select_label="Select Meshes",
            show_reverse=True,
            multi_select=True,
            list_min_height=120,
            log_callback=self.log,
        )
        layout.addWidget(self.tsl)

        self.btn_list = QPushButton("List Materials")
        self.btn_list.setMinimumHeight(28)
        self.btn_list.setToolTip(
            "Collect the materials assigned to the listed meshes.\n"
            "Every non-intermediate shape under a transform is read, so a mesh with\n"
            "several shapes does not hide a material.")
        self.btn_list.clicked.connect(self.on_list_materials)
        layout.addWidget(self.btn_list)

        # ---- 프로파일 ------------------------------------------------
        profile_box = QGroupBox("Rule Profile")
        profile_layout = QVBoxLayout(profile_box)

        row = QHBoxLayout()
        row.addWidget(QLabel("Profile"))
        self.cmb_profile = QComboBox()
        self.cmb_profile.setToolTip(
            "A rule set stored as JSON in the tool's data/profiles folder.")
        self.cmb_profile.currentIndexChanged.connect(self.on_profile_changed)
        row.addWidget(self.cmb_profile, stretch=1)

        self.btn_reload = QPushButton("Reload")
        self.btn_reload.setToolTip("Re-read the profile folder after editing the JSON.")
        self.btn_reload.clicked.connect(self.reload_profiles)
        row.addWidget(self.btn_reload)
        profile_layout.addLayout(row)

        self.lbl_pattern = QLabel("")
        self.lbl_pattern.setWordWrap(True)
        profile_layout.addWidget(self.lbl_pattern)

        layout.addWidget(profile_box)

        # ---- 머티리얼 트리 -------------------------------------------
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Material", "Status", "Meshes"])
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setMinimumHeight(150)
        self.tree.setToolTip(
            "Double-click a material to select its node in the scene.\n"
            "Drag the header edges to resize the columns.")
        # 더블클릭으로만 씬 선택을 바꾼다 - 행을 훑어보는 동안 선택이 따라 바뀌지 않도록.
        self.tree.itemDoubleClicked.connect(self.on_tree_double_clicked)

        header = self.tree.header()
        # ★ Stretch / ResizeToContents 는 **드래그로 폭을 바꿀 수 없다**(스타일이 폭을
        #   계산해 버린다). 세 칸 모두 Interactive 로 두고 초기 폭만 정해 준다.
        header.setSectionResizeMode(QHeaderView.Interactive)
        # 마지막 칸까지 사용자가 정한 폭을 지키도록(켜져 있으면 남는 공간에 맞춰 늘어난다).
        header.setStretchLastSection(False)
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 90)
        self.tree.setColumnWidth(2, 70)

        layout.addWidget(self.tree, stretch=1)

        # ---- 옵션 ----------------------------------------------------
        options_box = QGroupBox("Report")
        options_layout = QVBoxLayout(options_box)

        self.chk_detailed = QCheckBox("Detailed report (why each token is wrong)")
        self.chk_detailed.setToolTip(
            "Adds one line per wrong token : what was expected there, and what to "
            "use instead.")
        options_layout.addWidget(self.chk_detailed)

        self.chk_include_valid = QCheckBox("Include the names that pass")
        self.chk_include_valid.setToolTip(
            "Off by default - the report is about what needs fixing.")
        options_layout.addWidget(self.chk_include_valid)

        self.chk_clipboard = QCheckBox("Copy the report to the clipboard")
        self.chk_clipboard.setChecked(True)
        self.chk_clipboard.setToolTip(
            "The report is meant to be handed to someone else, so it is copied by "
            "default.")
        options_layout.addWidget(self.chk_clipboard)

        layout.addWidget(options_box)

        self.btn_check = QPushButton("Check Names")
        self.btn_check.setMinimumHeight(30)
        self.btn_check.setToolTip(
            "Diagnose every listed material name against the selected profile.\n"
            "Nothing in the scene is changed.")
        self.btn_check.clicked.connect(self.on_check)
        layout.addWidget(self.btn_check)

    # ==================================================================
    # 로그
    # ==================================================================

    def log(self, message):
        if self.log_view is not None:
            self.log_view.appendPlainText(message)
        else:
            print(message)

    # ==================================================================
    # 프로파일
    # ==================================================================

    def reload_profiles(self):
        """프로파일 폴더를 다시 읽어 콤보를 채운다(현재 선택은 최대한 유지)."""
        current = self.cmb_profile.currentText()

        names = profiles.list_profiles()

        self.cmb_profile.blockSignals(True)
        self.cmb_profile.clear()
        self.cmb_profile.addItems(names)
        if current in names:
            self.cmb_profile.setCurrentIndex(names.index(current))
        self.cmb_profile.blockSignals(False)

        if not names:
            self.lbl_pattern.setText("No profile found in : {0}".format(
                profiles.profiles_dir()))
            self.log("No rule profile found in {0}".format(profiles.profiles_dir()))
            return

        self.on_profile_changed()

    def current_profile(self):
        """지금 고른 프로파일. 읽기에 실패하면 None 을 돌려주고 이유를 로그에 적는다."""
        name = self.cmb_profile.currentText()
        if not name:
            return None

        try:
            return NameProfile.from_file(name)
        except Exception as e:
            self.log("[failed] Cannot read profile '{0}' : {1}".format(name, e))
            return None

    def on_profile_changed(self, *_args):
        profile = self.current_profile()
        if profile is None:
            self.lbl_pattern.setText("")
            return

        text = "pattern : {0}".format(profile.pattern)
        if profile.description:
            text += "\n{0}".format(profile.description)
        self.lbl_pattern.setText(text)

        # 규칙이 바뀌면 이전 진단은 더 이상 맞지 않는다.
        self.reports = {}
        self.refresh_tree_status()

    # ==================================================================
    # 머티리얼 수집
    # ==================================================================

    def on_list_materials(self):
        # UUID 로 되찾은 **현재** 경로를 쓴다 - 담아 둔 뒤 리네임돼도 맞는 노드를 잡는다.
        meshes = self.tsl.get_all_nodes()

        self.assignments, warnings = maya_materials.scan(meshes)
        self.reports = {}

        for warning in warnings:
            self.log("[warning] " + warning)

        self.fill_tree()

        self.log("Listed {0} material(s) from {1} mesh(es).".format(
            len(self.assignments), len(meshes)))

        return self.assignments

    def fill_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()

        for material, meshes in self.assignments:
            item = QTreeWidgetItem([material.split("|")[-1], "-", str(len(meshes))])
            item.setData(0, NODE_ROLE, material)
            item.setToolTip(2, "\n".join(m.split("|")[-1] for m in meshes))
            self.tree.addTopLevelItem(item)

        self.tree.blockSignals(False)

    def refresh_tree_status(self):
        """진단 결과를 Status 열에 반영한다(진단 전이면 '-')."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            material = item.data(0, NODE_ROLE)
            report = self.reports.get(material)

            if report is None:
                item.setText(1, "-")
                item.setForeground(1, QColor())
                continue

            if report.ok:
                item.setText(1, "ok")
                item.setForeground(1, COLOR_OK)
            else:
                issues = len(report.bad_tokens) + len(report.missing_roles) + len(report.warnings)
                item.setText(1, "{0} issue(s)".format(issues))
                item.setForeground(1, COLOR_BAD)

    def on_tree_double_clicked(self, item=None, column=0):
        """더블클릭한 머티리얼 노드를 씬에서 선택한다.

        여러 행을 골라 둔 상태라면 **고른 것 전부**를 선택한다(하나만 골랐으면 그것만).
        한 번 클릭으로는 선택이 바뀌지 않는다 - 목록을 훑어보다 씬 선택이 딸려 바뀌는 것을
        막기 위해서다.
        """
        names = [i.data(0, NODE_ROLE) for i in self.tree.selectedItems()]
        names = [n for n in names if n]

        clicked = item.data(0, NODE_ROLE) if item is not None else None
        if clicked and clicked not in names:
            names.append(clicked)

        if not names:
            return

        try:
            selected = maya_materials.select_nodes(names)
        except Exception as e:
            self.log("Failed to select in the scene : {0}".format(e))
            return

        if not selected:
            self.log("Not in the scene anymore : {0}".format(
                ", ".join(n.split("|")[-1] for n in names)))
            return

        self.log("Selected {0} material(s) : {1}".format(
            len(selected), ", ".join(n.split("|")[-1] for n in selected)))

    # ==================================================================
    # 진단
    # ==================================================================

    def on_check(self):
        profile = self.current_profile()
        if profile is None:
            self.log("[failed] No rule profile selected.")
            return

        # 아직 아무것도 모으지 않았으면 먼저 모은다 - 버튼 두 번 누르게 하지 않는다.
        if not self.assignments:
            self.log("No material listed yet - listing them from the mesh list first.")
            self.on_list_materials()

        if not self.assignments:
            return

        names = [material for material, _meshes in self.assignments]
        reports = profile.check_many(names)

        self.reports = {report.name: report for report in reports}
        self.refresh_tree_status()

        text = reporter.format_batch(
            reports,
            profile,
            detailed=self.chk_detailed.isChecked(),
            include_valid=self.chk_include_valid.isChecked(),
            usage=maya_materials.usage_map(self.assignments),
        )

        self.log("")
        self.log(text)

        if self.chk_clipboard.isChecked():
            self.copy_to_clipboard(text)

    def copy_to_clipboard(self, text):
        try:
            QApplication.clipboard().setText(text)
            self.log("(report copied to the clipboard)")
        except Exception as e:
            self.log("Failed to copy to the clipboard : {0}".format(e))
