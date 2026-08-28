# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00130_ControlRig_V02 - Qt UI
#
# 계획서: docs/plans/A00130_ControlRig_V02_plan.md
#
# **Phase 1 (최소 기능)** — 템플릿 조인트에 케이지 세트를 맞춘다.
# 상위 탭 = 단계. 지금은 `Match` 하나뿐이고, 다음 단계(Orient / Mirror / IK / Validate)는
# 아래 STEPS 표에 줄을 넣으면 붙는다.
#
#   Match : 매핑 표(json)대로 세트의 원소를 짝인 조인트에 맞춘다
#
# v02.00 : 신규. Match + 템플릿 조인트 생성.
#          **orient 규칙은 아직 안 정해졌다** — 매핑 json 의 `orient` 필드는 자리만
#          잡아 두고 아무도 읽지 않는다. 규칙이 오면 `Orient` 단계를 STEPS 에 더한다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00130_ControlRig_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00130_ControlRig_V02.app.core import mapping_data
from tools.A00130_ControlRig_V02.app.core import match_manager
from tools.A00130_ControlRig_V02.app.core import scene_utils as su


WINDOW_OBJECT_NAME = "JUN_A00130_ControlRig_V02_window"


# (탭 라벨, 툴팁, 빌더 메서드 이름) — 단계가 늘면 여기에 줄만 넣는다
STEPS = (
    ("Match",
     "Match - move each cage set's members onto the template joint it is paired with.",
     "_build_match_tab"),
)


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 620
        self.win_height = 700
        self.win_title = "Control Rig Tool v{0}".format(VERSION)

        self.resize(self.win_width, self.win_height)

        self.joints = []
        self.messages_seen = 0

        self.build_ui()
        self.reload_mapping()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        # 로그창 (탭 빌더가 self.log 를 부를 수 있어 탭보다 먼저)
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(140)

        root.addWidget(self._build_source_group())

        self.tabs = QTabWidget()
        self.tabs.tabBar().setElideMode(Qt.ElideRight)
        for label, tip, builder in STEPS:
            index = self.tabs.addTab(self._scrolled(getattr(self, builder)()), label)
            self.tabs.setTabToolTip(index, tip)
        root.addWidget(self.tabs, 1)

        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.te_log)
        root.addWidget(log_group)

        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignRight)
        root.addWidget(footer)

    def _scrolled(self, widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    # --------------------------------------------------------------
    # 공통 : 매핑 버전 + 네임스페이스
    # --------------------------------------------------------------

    def _build_source_group(self):
        group = QGroupBox("Source")
        layout = QGridLayout(group)

        layout.addWidget(QLabel("Mapping"), 0, 0)
        self.cmb_version = QComboBox()
        self.cmb_version.setToolTip(
            "Which template_map.json to use.\n"
            "Add a folder under app/data/mapping/ to keep a second cage version.")
        self.cmb_version.currentIndexChanged.connect(lambda *_: self.reload_mapping())
        layout.addWidget(self.cmb_version, 0, 1)

        self.btn_reload = QPushButton("Reload")
        self.btn_reload.setToolTip("Read the mapping file again after editing it.")
        self.btn_reload.clicked.connect(self.reload_mapping)
        layout.addWidget(self.btn_reload, 0, 2)

        layout.addWidget(QLabel("Cage namespace"), 1, 0)
        self.cmb_namespace = QComboBox()
        self.cmb_namespace.setToolTip(
            "The namespace the cage was referenced under.\n"
            "Both the cage SETS and the TEMPLATE JOINTS are looked up inside it first,\n"
            "then without it - so an imported cage, a referenced cage and joints you\n"
            "made locally all work.")
        layout.addWidget(self.cmb_namespace, 1, 1)

        self.btn_ns_refresh = QPushButton("Refresh")
        self.btn_ns_refresh.setToolTip("List the namespaces in the scene again.")
        self.btn_ns_refresh.clicked.connect(self.refresh_namespaces)
        layout.addWidget(self.btn_ns_refresh, 1, 2)

        self.lbl_mapping = QLabel("")
        self.lbl_mapping.setWordWrap(True)
        layout.addWidget(self.lbl_mapping, 2, 0, 1, 3)

        return group

    # --------------------------------------------------------------
    # Step : Match
    # --------------------------------------------------------------

    def _build_match_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        note = QLabel(
            "Each cage set's members are moved onto the template joint it is paired "
            "with, using the mapping file. Names are looked up inside the chosen "
            "namespace first, then without it. Anything missing is reported and "
            "skipped - the rest still run.")
        note.setWordWrap(True)
        layout.addWidget(note)

        # ---- 템플릿 조인트 ----
        grp_tpl = QGroupBox("Template joints")
        tpl_layout = QVBoxLayout(grp_tpl)

        tpl_note = QLabel(
            "Create builds the joints with the names and parenting from the mapping "
            "file, all at the origin. Placing them is your job.")
        tpl_note.setWordWrap(True)
        tpl_layout.addWidget(tpl_note)

        tpl_row = QHBoxLayout()
        self.btn_create_template = QPushButton("Create Template Joints")
        self.btn_create_template.setToolTip(
            "Create any joint from the mapping file that is not in the scene yet,\n"
            "with the parenting the file describes. Joints that already exist -\n"
            "including ones that came in with a referenced cage - are left alone.\n"
            "One undo step.")
        self.btn_create_template.clicked.connect(self.on_create_template)
        tpl_row.addWidget(self.btn_create_template)

        self.btn_check_template = QPushButton("Check")
        self.btn_check_template.setToolTip(
            "Report which template joints and cage sets are missing. Changes nothing.")
        self.btn_check_template.clicked.connect(self.on_check)
        tpl_row.addWidget(self.btn_check_template)
        tpl_layout.addLayout(tpl_row)

        layout.addWidget(grp_tpl)

        # ---- 미리보기 ----
        self.tree_plan = QTreeWidget()
        self.tree_plan.setColumnCount(5)
        self.tree_plan.setHeaderLabels(
            ["Template joint", "Cage set", "Match", "Members", "Status"])
        self.tree_plan.setRootIsDecorated(False)
        self.tree_plan.setAlternatingRowColors(True)
        self.tree_plan.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.tree_plan, 1)

        self.btn_match = QPushButton("Match")
        self.btn_match.setMinimumHeight(34)
        self.btn_match.setToolTip(
            "Move the members of every listed cage set onto its template joint.\n"
            "Sub-sets inside a set are ignored. Locked or driven objects are skipped\n"
            "and reported rather than half-moved.\n"
            "Everything is one undo step.")
        self.btn_match.clicked.connect(self.on_match)
        layout.addWidget(self.btn_match)

        return tab

    # ==============================================================
    # 데이터
    # ==============================================================

    def reload_mapping(self):
        """매핑 파일을 읽고 버전 콤보 · 네임스페이스 콤보를 채운다."""
        if self.cmb_version.count() == 0:
            versions = mapping_data.list_versions()
            self.cmb_version.blockSignals(True)
            self.cmb_version.addItems(versions or ["(none)"])
            self.cmb_version.setCurrentIndex(max(0, self.cmb_version.count() - 1))
            self.cmb_version.blockSignals(False)
            self.refresh_namespaces()

        version = self.cmb_version.currentText()
        self.joints, messages = mapping_data.load(
            None if version == "(none)" else version)
        self._log_all(messages)
        self._log_all(mapping_data.check(self.joints))

        pairs = sum(len(j["targets"]) for j in self.joints)
        structure = len([j for j in self.joints if not j["targets"]])
        self.lbl_mapping.setText(
            "{0} joint(s), {1} joint-to-set pair(s), {2} structure-only joint(s)."
            .format(len(self.joints), pairs, structure))

        self._refresh_plan()

    def refresh_namespaces(self):
        current = self.cmb_namespace.currentText()
        self.cmb_namespace.blockSignals(True)
        self.cmb_namespace.clear()
        self.cmb_namespace.addItem(su.NO_NAMESPACE)
        self.cmb_namespace.addItems(su.list_namespaces())
        if current:
            index = self.cmb_namespace.findText(current)
            if index >= 0:
                self.cmb_namespace.setCurrentIndex(index)
        self.cmb_namespace.blockSignals(False)

    def _namespace(self):
        return self.cmb_namespace.currentText()

    # ==============================================================
    # 슬롯
    # ==============================================================

    def _current_plan(self):
        return match_manager.plan(self.joints, self._namespace())

    def _refresh_plan(self):
        if not hasattr(self, "tree_plan"):
            return
        rows = self._current_plan()
        self.tree_plan.clear()
        for row in rows:
            item = QTreeWidgetItem([
                row["joint"],
                su.short_name(row["set"]),
                "t" if "r" not in row["match"] else "t + r",
                str(len(row["members"])),
                row["status"] if not row["note"]
                else "{0} - {1}".format(row["status"], row["note"]),
            ])
            self.tree_plan.addTopLevelItem(item)
        for col in range(5):
            self.tree_plan.resizeColumnToContents(col)
        return rows

    def on_check(self):
        rows = self._refresh_plan()
        counts = match_manager.summarize(rows)
        self.log("Check : " + ", ".join(
            "{0} {1}".format(v, k) for k, v in sorted(counts.items())))
        missing_j = sorted({r["joint"] for r in rows
                            if r["status"] == match_manager.ST_NO_JOINT})
        missing_s = sorted({su.short_name(r["set"]) for r in rows
                            if r["status"] == match_manager.ST_NO_SET})
        if missing_j:
            self.log("[Warning] missing template joint(s): " + ", ".join(missing_j))
        if missing_s:
            self.log("[Warning] missing cage set(s): " + ", ".join(missing_s))
        if not missing_j and not missing_s:
            self.log("[OK] Every template joint and cage set was found.")

    def on_create_template(self):
        if not self.joints:
            self.log("[WARN] No mapping loaded.")
            return
        _created, messages = match_manager.create_template(
            self.joints, self._namespace())
        self._log_all(messages)
        self._refresh_plan()

    def on_match(self):
        if not self.joints:
            self.log("[WARN] No mapping loaded.")
            return
        rows = self._refresh_plan()
        if not rows:
            self.log("[WARN] Nothing to match.")
            return
        _results, messages = match_manager.apply(rows)
        self._log_all(messages)
        self._refresh_plan()

    # ==============================================================
    # helpers
    # ==============================================================

    def log(self, text):
        self.te_log.append(text)

    def _log_all(self, messages):
        for m in (messages or []):
            self.log(m)

    def show_about(self, *args):
        QMessageBox.information(
            self, "About",
            "Control Rig Tool v{0}\nWritten by Ji Hun Park\nUpdate date : {1}".format(
                VERSION, LAST_UPDATE))
