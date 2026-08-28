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
#   Orient & Place : 규칙(A1 · A2 · A3)대로 방향을 잡고, 폴 타깃 4개는 위치까지 놓는다
#                    <- Match 보다 먼저
#   Length         : 템플릿 조인트 사이 거리를 옵션 컨트롤러 어트리뷰트에 써 넣는다
#   Match          : 매핑 표(json)대로 세트의 원소를 짝인 조인트에 맞춘다
#
# v02.07 : 폴 타깃 4개 추가 + **Place** 규칙(자기 축 +Z 로 10) —
#          방향만이 아니라 위치도 다루므로 탭·버튼을 **Orient & Place** 로.
#          탭 순서도 Orient & Place / Length / Match 로.
# v02.06 : Match 가 **세트에 없는 관련 ikHandle 도 찾아** 함께 끈다.
# v02.05 : 탭 순서를 실제 작업 순서대로 — **Orient** 를 맨 앞으로.
# v02.04 : **Orient** 단계 — A1(척추) · A2(팔·다리 + tail/preserve) · A3(미러).
#          계획서: docs/plans/A00130_ControlRig_V02_orient_plan.md
# v02.03 : Match 앞뒤로 **IK 편집 세션** — D01_IK_handle 의 핸들을 끄고 매칭한 뒤
#          핸들 스냅 + 폴 벡터 역산으로 되켠다 (계획서 Phase 4).
# v02.02 : 막힌 채널을 그룹 단위로 갈라, 일부만 막혀도 나머지는 매칭한다.
# v02.01 : Length 단계 — 템플릿 조인트 사이 거리를 옵션 컨트롤러에 쓴다.
#          계획서: docs/plans/A00130_ControlRig_V02_length_plan.md
# v02.00 : 신규. Match + 템플릿 조인트 생성.
#          **orient 규칙은 아직 안 정해졌다** — 매핑 json 의 `orient` 필드는 자리만
#          잡아 두고 아무도 읽지 않는다. 규칙이 오면 `Orient` 단계를 STEPS 에 더한다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00130_ControlRig_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00130_ControlRig_V02.app.core import mapping_data
from tools.A00130_ControlRig_V02.app.core import ik_session
from tools.A00130_ControlRig_V02.app.core import length_manager
from tools.A00130_ControlRig_V02.app.core import match_manager
from tools.A00130_ControlRig_V02.app.core import orient_manager
from tools.A00130_ControlRig_V02.app.core import scene_utils as su


WINDOW_OBJECT_NAME = "JUN_A00130_ControlRig_V02_window"


# (탭 라벨, 툴팁, 빌더 메서드 이름) — 단계가 늘면 여기에 줄만 넣는다
# 탭 순서 = 실제로 누르는 순서다. `Orient & Place` 가 먼저인 이유는 Match 가 케이지를
# 조인트 자리로 옮기기 때문 - 조인트가 다 잡힌 뒤에 맞춰야 한다.
#
# 이름이 `Orient` 가 아닌 이유: 폴 타깃 4개는 **위치까지** 놓는다(orient_map 의 `place`).
# 방향만 다루지 않으므로 탭도 버튼도 `Orient & Place` 다.
STEPS = (
    ("Orient & Place",
     "Orient & Place - mirror the left side to the right, set every template joint's "
     "rotation from the rules, then place the foot and toe pole targets. "
     "Run this before Match.",
     "_build_orient_tab"),
    ("Length",
     "Length - measure the template joints and write the distances onto the "
     "option controller.",
     "_build_length_tab"),
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
        self.length_doc = {}
        self.ik_set_name = None
        self.orient_doc = {}
        self.option_ctl_override = ""      # 손으로 지정하면 그것이 이긴다
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

        # ---- IK 핸들 ----
        grp_ik = QGroupBox("IK handles")
        ik_layout = QVBoxLayout(grp_ik)

        self.chk_ik_session = QCheckBox("Turn IK off while matching, then snap the handles back")
        self.chk_ik_session.setChecked(True)
        self.chk_ik_session.setToolTip(
            "Joints driven by an ikHandle cannot be matched while IK is solving -\n"
            "matchTransform succeeds and the solver takes the value straight back,\n"
            "so the log would say OK while nothing changed.\n"
            "\n"
            "With this on, Match does:\n"
            "  turn IK off  ->  match  ->  snap handle + rebuild pole vector  ->  IK on\n"
            "\n"
            "The snap and the pole vector maths come from A00060 Joint Tool.\n"
            "If the match fails half way the chains are put back and IK is turned on.\n"
            "\n"
            "Handles that drive the joints being matched but are missing from the set\n"
            "are found and turned off as well - a nested chain left solving would fight\n"
            "the match and leave its joints rotated. You are told which ones.")
        ik_layout.addWidget(self.chk_ik_session)

        self.lbl_ik_set = QLabel("")
        self.lbl_ik_set.setWordWrap(True)
        ik_layout.addWidget(self.lbl_ik_set)

        layout.addWidget(grp_ik)

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

    # --------------------------------------------------------------
    # Step : Length
    # --------------------------------------------------------------

    def _build_length_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        note = QLabel(
            "The distance between template joints is written onto the option "
            "controller. Place the template joints first - Match does not have to "
            "have been run. Measure changes nothing; Write Values is one undo step.")
        note.setWordWrap(True)
        layout.addWidget(note)

        # ---- 대상 / 옵션 ----
        grp = QGroupBox("Target")
        grid = QGridLayout(grp)

        grid.addWidget(QLabel("Option controller"), 0, 0)
        self.le_option_ctl = QLineEdit()
        self.le_option_ctl.setPlaceholderText("not found - select it and press Get Selected")
        self.le_option_ctl.setToolTip(
            "Where the values are written.\n"
            "\n"
            "Found automatically from the name in length_map.json: the chosen namespace\n"
            "first, then the bare name, then any transform whose name contains it\n"
            "(a referenced cage brings it in as CAGE:CH_n_OptionAll_xx_ctl).\n"
            "\n"
            "You can also type a name here or select the controller in the scene and\n"
            "press Get Selected. A name you set by hand wins until you press Auto.")
        self.le_option_ctl.editingFinished.connect(self.on_option_ctl_typed)
        grid.addWidget(self.le_option_ctl, 0, 1)

        ctl_row = QHBoxLayout()
        self.btn_get_option_ctl = QPushButton("Get Selected")
        self.btn_get_option_ctl.setToolTip(
            "Use the selected object as the option controller.\n"
            "Select a shape and its transform is used.")
        self.btn_get_option_ctl.clicked.connect(self.on_get_option_ctl)
        ctl_row.addWidget(self.btn_get_option_ctl)

        self.btn_auto_option_ctl = QPushButton("Auto")
        self.btn_auto_option_ctl.setToolTip(
            "Drop the name you set by hand and look it up from length_map.json again.")
        self.btn_auto_option_ctl.clicked.connect(self.on_auto_option_ctl)
        ctl_row.addWidget(self.btn_auto_option_ctl)
        grid.addLayout(ctl_row, 0, 2)

        self.lbl_ctl_how = QLabel("")
        self.lbl_ctl_how.setWordWrap(True)
        grid.addWidget(self.lbl_ctl_how, 1, 1, 1, 2)

        grid.addWidget(QLabel("Total"), 2, 0)
        self.cmb_total_mode = QComboBox()
        self.cmb_total_mode.addItems([mapping_data.TOTAL_STRAIGHT,
                                      mapping_data.TOTAL_SUM])
        self.cmb_total_mode.setToolTip(
            "How the whole-limb length is measured.\n"
            "  straight : first joint to last joint, ignoring the bend (what V01 did)\n"
            "  sum      : the two segments added up, i.e. fully extended\n"
            "They differ by about 3.4% at a 30 degree bend. If the value drives IK\n"
            "stretch, 'sum' is usually what you want.")
        self.cmb_total_mode.currentIndexChanged.connect(lambda *_: self._refresh_length())
        grid.addWidget(self.cmb_total_mode, 2, 1)

        self.lbl_unit = QLabel("")
        self.lbl_unit.setToolTip(
            "Distances follow the scene's linear unit. The tool never changes it.")
        grid.addWidget(self.lbl_unit, 2, 2)

        layout.addWidget(grp)

        # ---- 미리보기 ----
        self.tree_length = QTreeWidget()
        self.tree_length.setColumnCount(6)
        self.tree_length.setHeaderLabels(
            ["Part", "Total", "Upper", "Lower", "Attributes", "Status"])
        self.tree_length.setRootIsDecorated(False)
        self.tree_length.setAlternatingRowColors(True)
        self.tree_length.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.tree_length, 1)

        row = QHBoxLayout()
        self.btn_measure = QPushButton("Measure")
        self.btn_measure.setToolTip(
            "Measure the template joints and show what would be written.\n"
            "Changes nothing.")
        self.btn_measure.clicked.connect(self.on_measure)
        row.addWidget(self.btn_measure)

        self.btn_write_length = QPushButton("Write Values")
        self.btn_write_length.setMinimumHeight(34)
        self.btn_write_length.setToolTip(
            "Write the measured distances onto the option controller.\n"
            "Attributes that are missing, locked, driven or out of range are skipped\n"
            "and reported - the rest are still written.\n"
            "One undo step.")
        self.btn_write_length.clicked.connect(self.on_write_length)
        row.addWidget(self.btn_write_length, 1)
        layout.addLayout(row)

        return tab

    # --------------------------------------------------------------
    # Step : Orient
    # --------------------------------------------------------------

    def _build_orient_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        note = QLabel(
            "Place the template joints by hand first, then press Orient & Place. The "
            "left side is mirrored onto the right, the spine is squared up, and the "
            "arms and legs are aimed down the chain with the pole target deciding the "
            "roll. Finally the foot and toe pole targets are moved out along their own "
            "+Z - that last step is why this is not called Orient.")
        note.setWordWrap(True)
        layout.addWidget(note)

        grp = QGroupBox("Rules")
        opt = QVBoxLayout(grp)

        self.chk_spine_zero = QCheckBox(
            "Spine joints get world rotation 0, 0, 0 (uncheck to aim +X along the chain)")
        self.chk_spine_zero.setChecked(True)
        self.chk_spine_zero.setToolTip(
            "On  : pelvis, spine, neck and head are squared up to the world axes.\n"
            "Off : the forward axis aims at the next joint and +Z leans toward world +Z.\n"
            "The head has no child, so it copies the joint before it.")
        self.chk_spine_zero.stateChanged.connect(lambda *_: self._refresh_orient())
        opt.addWidget(self.chk_spine_zero)

        self.chk_mirror = QCheckBox("Mirror the left side onto the right first")
        self.chk_mirror.setChecked(True)
        self.chk_mirror.setToolTip(
            "The arm is mirrored with Maya's behaviour rule (the right arm's forward\n"
            "axis ends up being -X). The leg is mirrored by position only and then\n"
            "aimed, because its forward axis stays +X.\n"
            "\n"
            "This has to run BEFORE the arms and legs are aimed: aiming reads the pole\n"
            "targets, and mirroring is what puts the right-hand ones in place.")
        self.chk_mirror.stateChanged.connect(lambda *_: self._refresh_orient())
        opt.addWidget(self.chk_mirror)

        layout.addWidget(grp)

        self.tree_orient = QTreeWidget()
        self.tree_orient.setColumnCount(5)
        self.tree_orient.setHeaderLabels(
            ["Joint", "Rule", "Up dev", "Status", "Note"])
        self.tree_orient.setRootIsDecorated(False)
        self.tree_orient.setAlternatingRowColors(True)
        self.tree_orient.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.tree_orient, 1)

        row = QHBoxLayout()
        self.btn_check_orient = QPushButton("Check")
        self.btn_check_orient.setToolTip(
            "Show which rule covers which joint, and which ones get placed.\n"
            "Changes nothing.\n"
            "'Up dev' is measured from the scene as it is now - the number that\n"
            "matters is the one after Orient has run.")
        self.btn_check_orient.clicked.connect(self.on_check_orient)
        row.addWidget(self.btn_check_orient)

        self.btn_orient = QPushButton("Orient && Place")
        self.btn_orient.setMinimumHeight(34)
        self.btn_orient.setToolTip(
            "Mirror, set the rotations, then place the foot and toe pole targets.\n"
            "One undo step.\n"
            "Joints with no rule are left untouched and listed as 'no rule'.")
        self.btn_orient.clicked.connect(self.on_orient)
        row.addWidget(self.btn_orient, 1)
        layout.addLayout(row)

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

        self.ik_set_name = mapping_data.load_ik_set(
            None if version == "(none)" else version)

        # 길이 데이터도 같은 버전 폴더에서 읽는다. 조인트 이름 오타를 여기서 잡는다.
        self.length_doc, length_messages = mapping_data.load_length(
            None if version == "(none)" else version, joints=self.joints)
        self._log_all(length_messages)
        self._log_all(mapping_data.check_length(self.length_doc))
        self._sync_total_mode()

        self.orient_doc, orient_messages = mapping_data.load_orient(
            None if version == "(none)" else version, joints=self.joints)
        self._log_all(orient_messages)

        pairs = sum(len(j["targets"]) for j in self.joints)
        structure = len([j for j in self.joints if not j["targets"]])
        self.lbl_mapping.setText(
            "{0} joint(s), {1} joint-to-set pair(s), {2} structure-only joint(s)."
            .format(len(self.joints), pairs, structure))

        self._refresh_plan()
        self._refresh_length()
        self._refresh_orient()

    def _sync_total_mode(self):
        """콤보를 json 의 total_mode 로 맞춘다 (사용자가 바꾸면 그 뒤로는 콤보가 이긴다)."""
        if not hasattr(self, "cmb_total_mode"):
            return
        mode = self.length_doc.get("total_mode")
        index = self.cmb_total_mode.findText(mode or "")
        if index >= 0 and self.cmb_total_mode.currentIndex() != index:
            self.cmb_total_mode.blockSignals(True)
            self.cmb_total_mode.setCurrentIndex(index)
            self.cmb_total_mode.blockSignals(False)

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
        self._refresh_ik_label()
        return rows

    # --------------------------------------------------------------
    # IK 세션
    # --------------------------------------------------------------

    def _ik_handles(self, log_messages=False):
        """`D01_IK_handle` 세트에서 ikHandle 을 모은다. `(handles, set_node)`."""
        if not self.ik_set_name:
            return [], None
        set_node, messages = ik_session.resolve_set(self.ik_set_name, self._namespace())
        handles, more = ik_session.handles_in_set(set_node)
        if log_messages:
            self._log_all(messages + more)
        return handles, set_node

    def _refresh_ik_label(self):
        if not hasattr(self, "lbl_ik_set"):
            return
        handles, set_node = self._ik_handles()
        text = ik_session.describe(set_node, handles)
        stranded = ik_session.stranded_handles(handles)
        if stranded:
            text += "  -  {0} still in edit mode from an earlier run".format(len(stranded))
        self.lbl_ik_set.setText(text)

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

        # 체크박스는 "매칭 중 IK 를 다룬다" 는 뜻이다 - 세트에서 온 것도,
        # 툴이 찾아낸 것도 함께 끈다/안 끈다.
        use_ik = self.chk_ik_session.isChecked()
        ik_handles = []
        if use_ik:
            ik_handles, _set_node = self._ik_handles(log_messages=True)

        _results, messages = match_manager.apply(
            rows, ik_handles=ik_handles, auto_ik=use_ik)
        self._log_all(messages)
        self._refresh_plan()

    # --------------------------------------------------------------
    # Length
    # --------------------------------------------------------------

    def _current_length_plan(self):
        return length_manager.plan(
            self.length_doc, self._namespace(), self.cmb_total_mode.currentText(),
            override=self.option_ctl_override)

    def _refresh_length(self, log_messages=False):
        if not hasattr(self, "tree_length"):
            return [], []

        rows, messages = self._current_length_plan()
        if log_messages:
            self._log_all(messages)

        node, _msgs, how = length_manager.find_option_ctl(
            self.length_doc.get("option_ctl"), self._namespace(),
            self.option_ctl_override)
        if self.le_option_ctl.text() != (node or ""):
            self.le_option_ctl.setText(node or "")
        self.lbl_ctl_how.setText({
            "manual": "set by hand",
            "exact": "found by name",
            "token": "matched by name - check it is the right node",
        }.get(how, "not found - select it and press Get Selected"))
        self.lbl_unit.setText("Measured in " + length_manager.linear_unit())

        self.tree_length.clear()
        for row in rows:
            values = row["values"]
            item = QTreeWidgetItem([
                row["part"],
                "{0:.4f}".format(values["total"]) if "total" in values else "-",
                "{0:.4f}".format(values["upper"]) if "upper" in values else "-",
                "{0:.4f}".format(values["lower"]) if "lower" in values else "-",
                ", ".join(row["attrs"][r] for r in ("total", "upper", "lower")
                          if r in row["attrs"]),
                row["status"] if not row["note"]
                else "{0} - {1}".format(row["status"], row["note"]),
            ])
            self.tree_length.addTopLevelItem(item)
        for col in range(6):
            self.tree_length.resizeColumnToContents(col)
        return rows, messages

    def on_get_option_ctl(self):
        """선택한 오브젝트를 옵션 컨트롤러로 삼는다."""
        node, message = length_manager.selected_option_ctl()
        self.log(message)
        if node:
            self.option_ctl_override = node
            self._refresh_length()

    def on_auto_option_ctl(self):
        """손으로 지정한 것을 버리고 다시 자동으로 찾는다."""
        self.option_ctl_override = ""
        _rows, messages = self._refresh_length()
        self._log_all(messages)

    def on_option_ctl_typed(self):
        """필드에 직접 친 이름을 받는다 (빈 칸이면 자동으로 돌아간다)."""
        text = self.le_option_ctl.text().strip()
        if not text:
            self.option_ctl_override = ""
            self._refresh_length()
            return
        if text == self.option_ctl_override:
            return
        if not cmds.objExists(text):
            self.log("[Warning] '{0}' does not exist.".format(text))
            return
        self.option_ctl_override = text
        self.log("[OK] Option controller set to '{0}'.".format(text))
        self._refresh_length()

    def on_measure(self):
        if not self.length_doc.get("measures"):
            self.log("[WARN] No length data loaded.")
            return
        rows, _messages = self._refresh_length(log_messages=True)
        counts = length_manager.summarize(rows)
        self.log("Measure : " + ", ".join(
            "{0} {1}".format(v, k) for k, v in sorted(counts.items())))
        ready, wanted = length_manager.attribute_count(rows)
        self.log("[{0}] {1} of {2} attribute(s) can be written.".format(
            "OK" if ready == wanted else "Warning", ready, wanted))

    def on_write_length(self):
        if not self.length_doc.get("measures"):
            self.log("[WARN] No length data loaded.")
            return
        rows, messages = self._refresh_length()
        self._log_all(messages)
        if not rows:
            self.log("[WARN] Nothing to write.")
            return
        _results, write_messages = length_manager.apply(rows)
        self._log_all(write_messages)
        self._refresh_length()

    # --------------------------------------------------------------
    # Orient
    # --------------------------------------------------------------

    def _refresh_orient(self, log_messages=False):
        if not hasattr(self, "tree_orient"):
            return [], []

        rows, messages = orient_manager.plan(
            self.orient_doc, self._namespace(),
            world_zero_spine=self.chk_spine_zero.isChecked(),
            mirror_enabled=self.chk_mirror.isChecked())
        if log_messages:
            self._log_all(messages)

        self.tree_orient.clear()
        for row in rows:
            item = QTreeWidgetItem([
                su.short_name(row["joint"]),
                row["rule"],
                "" if row["up_dev"] is None else "{0:.2f} deg".format(row["up_dev"]),
                row["status"],
                row["note"],
            ])
            self.tree_orient.addTopLevelItem(item)
        for col in range(5):
            self.tree_orient.resizeColumnToContents(col)
        return rows, messages

    def on_check_orient(self):
        if not self.orient_doc.get("pole_chains"):
            self.log("[WARN] No orient rules loaded.")
            return
        rows, _messages = self._refresh_orient(log_messages=True)
        counts = orient_manager.summarize(rows)
        placed = [r for r in rows if r["status"] == orient_manager.ST_PLACED]
        if placed:
            self.log("[Info] {0} joint(s) will be MOVED, not just rotated: {1}.".format(
                len(placed), ", ".join(su.short_name(r["joint"]) for r in placed)))
        self.log("Check : " + ", ".join(
            "{0} {1}".format(v, k) for k, v in sorted(counts.items())))
        no_rule = [r for r in rows if r["status"] == orient_manager.ST_NO_RULE]
        if no_rule:
            self.log("[Info] {0} joint(s) have no rule yet and are left alone - "
                     "this is different from the ones marked 'preserved', which are "
                     "deliberately kept.".format(len(no_rule)))

    def on_orient(self):
        if not self.orient_doc.get("pole_chains"):
            self.log("[WARN] No orient rules loaded.")
            return
        _results, messages = orient_manager.apply(
            self.orient_doc, self._namespace(),
            world_zero_spine=self.chk_spine_zero.isChecked(),
            mirror_enabled=self.chk_mirror.isChecked())
        self._log_all(messages)
        self._refresh_orient()

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
