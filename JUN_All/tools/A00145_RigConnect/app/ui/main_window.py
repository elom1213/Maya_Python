# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00145_RigConnect - Qt UI
#
# MEL ConnectionTool V04.02 의 3탭(Constrain / Connect / List Connected)을 PySide 로
# 포팅하고, A00140 ConnectClosest 기능과 Match / Attribute 를 더한 것이다.
#
# 최상위 탭은 4개이고, 기능이 여럿인 탭은 **중첩 탭**으로 나눈다:
#   Match
#   Constrain : Constraint / Skin Weight / Group Create / Transfer / Target Edit /
#               Update
#   Connect   : Connect / List Connected / Pair
#   Attribute : Edit / Create / Set Value
#
# 로직은 app/core 에 위임하고 이 모듈은 위젯 구성/시그널 연결/로그 출력만 담당한다.
# 모든 UI 문자열(버튼/라벨/로그)은 영어. (한국어는 주석/독스트링만)

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_filter_qt
from Framework.qt import JUN_mod_checkList_qt

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.core.mirror_tokens import MirrorTokenStore
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from tools.A00145_RigConnect.app.config.version import VERSION, LAST_UPDATE
from tools.A00145_RigConnect.app.core import match_manager as mch_mgr
from tools.A00145_RigConnect.app.core import constrain_manager as con_mgr
from tools.A00145_RigConnect.app.core import matrix_constraint_manager as mtx_mgr
from tools.A00145_RigConnect.app.core import connect_manager as cnt_mgr
from tools.A00145_RigConnect.app.core import attribute_manager as att_mgr
from tools.A00145_RigConnect.app.core import stream_manager as stm_mgr
from tools.A00145_RigConnect.app.core import skin_constraint_manager as skn_mgr
from tools.A00145_RigConnect.app.core import group_create_manager as grp_mgr
from tools.A00145_RigConnect.app.core import constraint_transfer_manager as cxfer_mgr
from tools.A00145_RigConnect.app.core import constraint_target_manager as ctgt_mgr
from tools.A00145_RigConnect.app.core import constraint_update_manager as cupd_mgr
from tools.A00145_RigConnect.app.core import attr_match
from tools.A00145_RigConnect.app.core import object_match as obj_match
from tools.A00145_RigConnect.app.core import snapshot_manager as snap_mgr
from tools.A00145_RigConnect.app.core import attr_profile_prefs as aprefs
from tools.A00145_RigConnect.app.core import attr_create_manager as acreate_mgr
from tools.A00145_RigConnect.app.core import attr_display as adisp
from tools.A00145_RigConnect.app.core import attr_delete_manager as adel_mgr
from tools.A00145_RigConnect.app.core import attr_order_manager as aord_mgr
from tools.A00145_RigConnect.app.core import attr_value_manager as aval_mgr
from tools.A00145_RigConnect.app.core import mirror_manager as mir_mgr
from tools.A00145_RigConnect.app.core import (
    CONSTRAINT_TYPES, PAIRING_CLOSEST, PAIRING_ORDER,
    connect_closest, find_closest_for_drivers)
from tools.A00145_RigConnect.app.ui.collapsible import CollapsibleBox
from tools.A00145_RigConnect.app.ui.attr_spec_dialog import AttrSpecDialog


# 재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00145_RigConnect_window"

# Match 탭 리스트의 요약 전환 기준. Targets/Followers 는 버텍스를 통째로 담는 일이 잦아
# 수천 개가 올라오는데, 그때 리스트를 채우는 비용(항목마다 UUID 조회)이 매칭 자체보다 크다.
# 이 수 **이상**이면 리스트에 펼치지 않고 개수 요약만 보여준다(공용 TSL 위젯의 list_limit).
# 다 보고 싶으면 리스트 아래 'List All' 버튼을 누른다.
MATCH_LIST_LIMIT = 500


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 560
        # Match 탭이 스크롤 없이 다 보이는 높이. 오프스크린(teal_dark)에서 900 이면
        # 39px 모자랐다(필요 939). 마야 폰트 차이를 감안해 여유를 둔다.
        self.win_height = 980
        self.win_title = "RigConnect v{0}".format(VERSION)

        # Connect 탭 src/dst 위젯 보관용. List Connected 의 stream 방향 상태.
        self._connect_widgets = {}
        self._stream_upstream = True

        # Match 탭의 추상 캐시(스냅샷). 로케이터 없이 월드 T/R/S 만 기억한다.
        # 창이 들고 있는 세션 데이터라 창을 닫거나 reload 하면 사라진다.
        self.snapshots = snap_mgr.SnapshotCache()

        # Attribute > Create 탭의 프로파일 상태. 프로파일은 JSON 으로 남으므로
        # 창을 닫아도 살아 있다(세션 데이터인 snapshots 와 다르다).
        # _acr_updating 은 리스트를 코드로 채우는 동안 itemChanged 를 무시하는 빗장.
        self._acr_profile = ""
        self._acr_data = {"attributes": []}
        self._acr_updating = False

        self.resize(self.win_width, self.win_height)
        # 창이 의도치 않게 너무 작게 줄어들지 않도록 최소 크기를 보장한다.
        # (리스트/로그가 쓸만한 높이를 유지하도록 콘텐츠보다 약간 낮은 바닥값)
        self.setMinimumSize(480, 560)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 공유 로그창 (탭 빌더가 self.log 를 호출할 수 있어 탭보다 먼저 생성)
        self.te_log = JUN_mod_log_qt_v01(
            window_title="RigConnect - Log",
            object_name="JUN_A00145_RigConnect_log_window")
        self.te_log.setMaximumHeight(120)

        # 탭
        self.tabs = QTabWidget()
        # Match 만 스크롤에 안 담겨 있어, 창이 모자라면 TSL 리스트와 Add/Del/Up/Down
        # 버튼이 겹쳐 보였다(하위 탭들은 _nested_tabs 에서 이미 _scrolled 로 담긴다).
        self.tabs.addTab(self._scrolled(self._build_match_tab()), "Match")
        self.tabs.addTab(self._build_constrain_tab(), "Constrain")
        self.tabs.addTab(self._build_connect_tab(), "Connect")
        self.tabs.addTab(self._build_attribute_tab(), "Attribute")
        self.tabs.addTab(self._scrolled(self._build_mirror_tab()), "Mirror")
        main_layout.addWidget(self.tabs)

        main_layout.addWidget(self.te_log)

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------------------
    # Tab : Match  (MEL Match Tool V05.04 이식)
    # --------------------------------------------------------------

    def _build_match_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Targets / Followers (TSL 위젯이 cmds.ls(fl=True) 로 버텍스를 개별 항목으로 펼친다)
        # list_limit : MATCH_LIST_LIMIT 이상이면 항목을 펼치지 않고 개수만 요약한다.
        #              담긴 항목은 그대로 쓰이고(Match/Create/Swap 동일), 'List All' 로 펼친다.
        self.tsl_match_tgt = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select",
            list_min_height=200, list_limit=MATCH_LIST_LIMIT,
            log_callback=self.log)
        self.tsl_match_flw = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=200, list_limit=MATCH_LIST_LIMIT,
            log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_match_tgt)
        list_row.addWidget(self.tsl_match_flw)
        layout.addLayout(list_row)

        # Create : 타겟 수만큼 컨트롤을 만들어 타겟 위치/방향에 즉시 매칭(+ Followers 목록 채움).
        create_box = QGroupBox("Create (at target positions)")
        create_row = QHBoxLayout(create_box)
        for label, ctl_type in (("Locators", "locator"),
                                ("Sphere", "sphere"),
                                ("Cube", "cube")):
            btn = QPushButton(label)
            btn.clicked.connect(
                lambda _checked=False, t=ctl_type: self.on_match_create(t))
            create_row.addWidget(btn)
        layout.addWidget(create_box)

        # Cache : 노드를 만들지 않고 타겟의 월드 T/R/S 만 값으로 기억한다.
        # "잠깐 옮겼다 되돌리려고" 로케이터를 수천 개 만들던 자리를 대신한다.
        cache_box = QGroupBox("Cache (remember without creating nodes)")
        cache_layout = QVBoxLayout(cache_box)

        cache_row = QHBoxLayout()
        btn_cache = QPushButton("Cache Targets")
        btn_cache.setToolTip(
            "Remember the world position / rotation / scale of every target and "
            "put the cached items in the Followers list -\n"
            "like the Create buttons, but nothing is added to the scene.\n\n"
            "Use it to put objects back where they were:\n"
            "  Targets = the objects -> Cache Targets -> Swap -> (move them "
            "around) -> Match\n\n"
            "Components work too (a vertex keeps its position and normal).\n"
            "Cached items are listed as '@cache <name>'. They are not scene "
            "objects, so they cost nothing\n"
            "and survive even if the original object is deleted - but they are "
            "lost when this window closes.")
        btn_cache.clicked.connect(self.on_match_cache)
        cache_row.addWidget(btn_cache)

        btn_cache_clear = QPushButton("Clear Cache")
        btn_cache_clear.setToolTip(
            "Throw away every cached transform and remove the cached items from "
            "the two lists above.")
        btn_cache_clear.clicked.connect(self.on_match_cache_clear)
        cache_row.addWidget(btn_cache_clear)

        self.lbl_match_cache = QLabel("")
        self.lbl_match_cache.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cache_row.addWidget(self.lbl_match_cache)
        cache_layout.addLayout(cache_row)
        layout.addWidget(cache_box)

        # Match Options (DOOTOOL_PY_TOOL_Match 의 체크박스 이식).
        # Rotate Order / Rotate Axis 는 이 툴이 월드 행렬 기반 매칭이라 의미가 없어 제외.
        # 기본 체크 상태는 DOOTOOL 을 따른다: Translation/Rotation ON, Scale/Parent OFF.
        opt_box = QGroupBox("Match Options")
        opt_layout = QVBoxLayout(opt_box)

        tr_row = QHBoxLayout()
        self.cb_mt_translate = QCheckBox("Translation")
        self.cb_mt_translate.setChecked(True)
        self.cb_mt_translate.setToolTip(
            "Match the follower's world position to the target.\n"
            "A component follower (a mesh vertex, a CV) can only take this - "
            "the point is moved to the target's world position.")
        self.cb_mt_rotate = QCheckBox("Rotation")
        self.cb_mt_rotate.setChecked(True)
        self.cb_mt_rotate.setToolTip(
            "Match the follower's world rotation to the target (rotateOrder "
            "safe). For a vertex target, aligns the follower to the vertex "
            "normal instead.\n"
            "Ignored for a component follower (a vertex has no rotation).")
        tr_row.addWidget(self.cb_mt_translate)
        tr_row.addWidget(self.cb_mt_rotate)
        tr_row.addStretch(1)
        opt_layout.addLayout(tr_row)

        self.cb_mt_scale = QCheckBox("Scale (world space)")
        self.cb_mt_scale.setChecked(False)
        self.cb_mt_scale.setToolTip(
            "Match the follower's world scale to the target. Only meaningful "
            "for transform/joint targets (ignored for mesh/cluster/component/"
            "vertex targets, and for a component follower).")
        opt_layout.addWidget(self.cb_mt_scale)

        self.cb_mt_parent = QCheckBox("Parent Followers to Targets")
        self.cb_mt_parent.setChecked(False)
        self.cb_mt_parent.setToolTip(
            "After matching, parent each follower under its target (under the "
            "owning object for a component target). Keeps the matched world "
            "position.\n"
            "Skipped for a component follower - a vertex or CV cannot be "
            "parented.")
        opt_layout.addWidget(self.cb_mt_parent)

        # 자식 보존 : 팔로워를 옮겨도 그 아래 오브젝트는 있던 월드 자리에 둔다.
        # Mirror 탭의 같은 이름 체크박스와 **같은 코어**(app/core/keep_children.py)를 쓴다.
        # 기본은 꺼짐 - 평소에는 자식이 부모를 따라가는 것이 맞다(사용자 지정, v01.53).
        self.cb_mt_keep_children = QCheckBox("Keep Children in Place")
        self.cb_mt_keep_children.setChecked(False)
        self.cb_mt_keep_children.setToolTip(
            "On : every child under a follower keeps the world position, "
            "rotation and scale it had\n"
            "     before the Match - only the follower itself moves. A child "
            "that is itself listed in\n"
            "     Followers still goes to its own target (followers are then "
            "matched parent first).\n"
            "     A child with locked or driven channels cannot be held and "
            "follows its parent (logged).\n"
            "Off (default): children move with their follower (their local "
            "values stay the same).")
        opt_layout.addWidget(self.cb_mt_keep_children)

        # 1 <- n : 타겟이 하나면 팔로워 전부를 그 하나에. 타겟이 여럿이면 켜져 있어도
        #          평소대로 n <- n (인덱스 1:1) 이라 늘 켜 둬도 된다.
        self.cb_mt_one_to_many = QCheckBox("1 <- n")
        self.cb_mt_one_to_many.setChecked(True)
        self.cb_mt_one_to_many.setToolTip(
            "On (default): when Targets holds exactly ONE object, EVERY follower "
            "is matched to it (1 <- n).\n"
            "With 2 or more targets this does nothing - the match stays "
            "index-paired, Targets[i] <- Followers[i] (n <- n),\n"
            "so it is safe to leave on.")
        opt_layout.addWidget(self.cb_mt_one_to_many)

        layout.addWidget(opt_box)

        # Match / Swap
        btn_row = QHBoxLayout()
        btn_match = QPushButton("Match")
        btn_match.setMinimumHeight(32)
        btn_match.clicked.connect(self.on_match)
        btn_swap = QPushButton("Swap")
        btn_swap.clicked.connect(self.on_match_swap)
        btn_row.addWidget(btn_match)
        btn_row.addWidget(btn_swap)
        layout.addLayout(btn_row)

        layout.addStretch(1)
        self._update_cache_label()
        return tab

    # --------------------------------------------------------------
    # Tab : Mirror
    # --------------------------------------------------------------

    def _build_mirror_tab(self):
        """리스트업된 오브젝트(와 자식들)를 반대쪽으로 통째로 미러하는 탭."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # --- 모드 : 새로 만들기(Objects) / 이미 있는 반대쪽을 옮기기(Source -> Target) ---
        # 아래 Mirror Plane / Mirror Type 은 두 모드가 같이 쓴다. 모드가 바꾸는 것은
        # 리스트(1개 / 2개)와 옵션 박스, 버튼 이름뿐이다.
        source_box = QGroupBox("Mode")
        source_row = QHBoxLayout(source_box)
        self.rb_mirror_create = QRadioButton("Create (Objects)")
        self.rb_mirror_create.setToolTip(
            "Duplicate the listed objects and everything under them onto the other "
            "side,\nwith L/R names, skin weights, constraints, clusters and node "
            "networks rebuilt.")
        self.rb_mirror_apply = QRadioButton("Apply (Source -> Target)")
        self.rb_mirror_apply.setToolTip(
            "Nothing is created. Each Target object is moved to where the Create "
            "mode would have\nput the mirror of the Source object in the same row "
            "(translation / rotation only).")
        self.rb_mirror_create.setChecked(True)
        self.rb_mirror_source = QButtonGroup(self)
        self.rb_mirror_source.addButton(self.rb_mirror_create, 0)
        self.rb_mirror_source.addButton(self.rb_mirror_apply, 1)
        source_row.addWidget(self.rb_mirror_create)
        source_row.addWidget(self.rb_mirror_apply)
        source_row.addStretch(1)
        layout.addWidget(source_box)

        # Create : Objects 하나
        self.tsl_mirror = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=200, list_limit=MATCH_LIST_LIMIT,
            log_callback=self.log)
        self.tsl_mirror.setToolTip(
            "Top objects to mirror. Every child under them is mirrored too.\n\n"
            "Only what is listed here gets copied - a mesh that is skinned to a\n"
            "listed joint is NOT copied unless the mesh itself is listed.\n"
            "Anything outside the list is reused as-is (a centre joint stays the\n"
            "driver of the mirrored constraint).")
        layout.addWidget(self.tsl_mirror)

        # Apply : Source / Target 두 개 (같은 줄끼리 짝)
        # 이름을 Left / Right 로 두지 않는다 - 스왑(Source=[a_l, a_r], Target=[a_r, a_l])처럼
        # 오른쪽 오브젝트가 원본일 수 있어 좌우 이름은 틀린 설명이 된다.
        self.w_mirror_pair = QWidget()
        pair_row = QHBoxLayout(self.w_mirror_pair)
        pair_row.setContentsMargins(0, 0, 0, 0)
        self.tsl_mirror_source = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Source", select_label="Select",
            list_min_height=200, list_limit=MATCH_LIST_LIMIT,
            log_callback=self.log)
        self.tsl_mirror_source.setToolTip(
            "Objects to mirror from. They are only read, never changed.\n"
            "Children are NOT included - list every object you want to mirror.")
        self.tsl_mirror_target = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select",
            list_min_height=200, list_limit=MATCH_LIST_LIMIT,
            log_callback=self.log)
        self.tsl_mirror_target.setToolTip(
            "Objects to move. Target[i] gets the mirror of Source[i] - keep both "
            "lists in the same order.\n\n"
            "All Source transforms are read before anything moves, so listing\n"
            "Source = [a, b] and Target = [b, a] swaps the two sides in one go.")
        pair_row.addWidget(self.tsl_mirror_source)
        pair_row.addWidget(self.tsl_mirror_target)
        layout.addWidget(self.w_mirror_pair)

        # --- 반사 평면 ---
        plane_box = QGroupBox("Mirror Plane")
        plane_row = QHBoxLayout(plane_box)
        self.rb_mirror_plane = QButtonGroup(self)
        for index, (label, key) in enumerate(mir_mgr.MIRROR_PLANES):
            rb = QRadioButton(label)
            rb.setProperty("mirror_key", key)
            if key == mir_mgr.PLANE_YZ:
                rb.setChecked(True)
            self.rb_mirror_plane.addButton(rb, index)
            plane_row.addWidget(rb)
        plane_row.addStretch(1)
        layout.addWidget(plane_box)

        # --- 미러 방식 (조인트 / 컨트롤러) ---
        mode_box = QGroupBox("Mirror Type")
        mode_layout = QGridLayout(mode_box)
        mode_box.setToolTip(
            "Behavior    : same rotation values give mirrored motion - the local "
            "axes are flipped\n"
            "              (matches Maya's mirrorJoint with Mirror function "
            "'Behavior').\n"
            "Orientation : the local axes keep pointing the same way as the "
            "original.\n"
            "Reflect     : a true mirror image - the same state you get by putting "
            "the object under\n"
            "              a group and setting world scaleX to -1 (YZ plane). The "
            "local axes point\n"
            "              the reflected way, so moving the mirrored control along "
            "its own +X / +Y / +Z\n"
            "              moves it exactly opposite across the plane. This leaves "
            "a negative scale\n"
            "              on one axis, which is what that mirror is.\n\n"
            "Behavior mirrors rotation, not translation: moving a control +Y on "
            "both sides moves\n"
            "them in opposite directions. Pick Orientation for translate driven "
            "objects (cluster handles).\n\n"
            "Meshes always fall back to Orientation - their geometry is reflected, "
            "so Reflect would\n"
            "only add a negative scale on top.")

        self.rb_mirror_joint = self._mirror_mode_row(
            mode_layout, 0, "Joints", mir_mgr.MIRROR_MODES, mir_mgr.MODE_BEHAVIOR)
        self.rb_mirror_other = self._mirror_mode_row(
            mode_layout, 1, "Curves / Others", mir_mgr.CONTROL_MIRROR_MODES,
            mir_mgr.MODE_REFLECT)
        layout.addWidget(mode_box)

        # --- 옵션 (Create 전용) ---
        opt_box = QGroupBox("Options")
        self.gb_mirror_options = opt_box
        opt_layout = QVBoxLayout(opt_box)

        self.cb_mirror_no_token = QCheckBox("Disable token check")
        self.cb_mirror_no_token.setChecked(False)
        self.cb_mirror_no_token.setToolTip(
            "Off : an object whose name has no L/R token is reported and NOTHING "
            "is mirrored.\n"
            "      Their names are logged and they are collected in the "
            "'{0}' set,\n"
            "      which is then selected - fix the names and run Mirror again.\n"
            "On  : the warning is still logged, but those objects are mirrored "
            "with the '{1}'\n"
            "      suffix instead of a swapped token (no set is made).\n\n"
            "Tokens come from the shared rule file:\n{2}".format(
                mir_mgr.MISSING_TOKEN_SET, mir_mgr.NO_TOKEN_SUFFIX,
                MirrorTokenStore.json_path()))
        opt_layout.addWidget(self.cb_mirror_no_token)

        keep_row = QHBoxLayout()
        self.cb_mirror_skin = QCheckBox("Skin Weights")
        self.cb_mirror_constraints = QCheckBox("Constraints")
        self.cb_mirror_clusters = QCheckBox("Clusters")
        self.cb_mirror_networks = QCheckBox("Node Networks")
        for cb, tip in ((self.cb_mirror_skin,
                         "Rebuild each skinCluster on the mirrored mesh with the "
                         "mirrored influences and the same weights."),
                        (self.cb_mirror_constraints,
                         "Rebuild the constraints that drive the mirrored objects, "
                         "with mirrored drivers."),
                        (self.cb_mirror_clusters,
                         "Rebuild the clusters that deform the mirrored geometry, "
                         "with a mirrored handle and the same weights."),
                        (self.cb_mirror_networks,
                         "Rebuild the utility node networks that drive the mirrored "
                         "objects - any chain of\n"
                         "nodes, not just constraints (pointOnCurveInfo, "
                         "fourByFourMatrix, multMatrix,\n"
                         "decomposeMatrix, ...). The nodes are duplicated and "
                         "rewired to the mirrored side;\n"
                         "drivers outside the mirror stay shared.\n\n"
                         "Values that are not connected are copied as-is, so check "
                         "any baked offsets.\n"
                         "Animation curves, expressions and deformers are left "
                         "out on purpose.")):
            cb.setChecked(True)
            cb.setToolTip(tip)
            keep_row.addWidget(cb)
        keep_row.addStretch(1)
        opt_layout.addLayout(keep_row)

        layout.addWidget(opt_box)

        # --- 적용할 값 (Apply 전용) ---
        # 스킨 / 컨스트레인트 등은 만드는 모드에서만 의미가 있어 Options 대신 이 박스를 보인다.
        apply_box = QGroupBox("Apply")
        self.gb_mirror_apply = apply_box
        apply_row = QHBoxLayout(apply_box)
        self.cb_mirror_translate = QCheckBox("Translation")
        self.cb_mirror_translate.setChecked(True)
        self.cb_mirror_translate.setToolTip(
            "Move each Target object to the mirrored world position of its Source "
            "partner.")
        self.cb_mirror_rotate = QCheckBox("Rotation")
        self.cb_mirror_rotate.setChecked(True)
        self.cb_mirror_rotate.setToolTip(
            "Turn each Target object to the mirrored world rotation of its Source "
            "partner.\n"
            "The scale size of the Target object is kept. A joint takes it in rotate "
            "(jointOrient is kept).\n"
            "Reflect is a true mirror image, so an object that was not reflected "
            "before ends up with\na negative scale on one axis - the same state the "
            "Create mode makes.")
        # 자식 보존 : Target 을 옮겨도 그 아래 오브젝트는 옮기기 전 월드 자리에 둔다.
        self.cb_mirror_keep_children = QCheckBox("Keep Children in Place")
        self.cb_mirror_keep_children.setChecked(True)
        self.cb_mirror_keep_children.setToolTip(
            "On : every child under a Target object keeps the world position, "
            "rotation and scale it had\n"
            "     before the Apply - only the Target itself moves. A child that is "
            "itself listed in Target\n"
            "     still goes to its own mirrored place.\n"
            "     A child with locked or driven channels cannot be held and follows "
            "its parent (logged).\n"
            "Off: children move with their parent (their local values stay the same).")
        apply_row.addWidget(self.cb_mirror_translate)
        apply_row.addWidget(self.cb_mirror_rotate)
        apply_row.addWidget(self.cb_mirror_keep_children)
        apply_row.addStretch(1)
        layout.addWidget(apply_box)

        self.btn_mirror = QPushButton("Mirror")
        self.btn_mirror.setMinimumHeight(32)
        self.btn_mirror.clicked.connect(self.on_mirror)
        layout.addWidget(self.btn_mirror)

        self.rb_mirror_source.buttonToggled.connect(self._on_mirror_source_changed)
        self._on_mirror_source_changed()

        layout.addStretch(1)
        return tab

    def _on_mirror_source_changed(self, *_args):
        """모드에 맞는 리스트 / 옵션 박스만 보이고 버튼 이름을 바꾼다.

        buttonToggled 는 한 번 바꿀 때 두 번(꺼짐 / 켜짐) 온다 - 상태만 다시 읽으므로 무해하다.
        """
        apply = self.rb_mirror_apply.isChecked()
        self.tsl_mirror.setVisible(not apply)
        self.gb_mirror_options.setVisible(not apply)
        self.w_mirror_pair.setVisible(apply)
        self.gb_mirror_apply.setVisible(apply)
        self.btn_mirror.setText("Mirror to Target" if apply else "Mirror")

    def _mirror_mode_row(self, grid, row, label, modes, default_key):
        """미러 방식 라디오 한 줄. 반환: QButtonGroup.

        조인트와 컨트롤러가 고를 수 있는 방식이 다르다 - 조인트에는 음수 스케일을 남기는
        `Reflect` 를 주지 않는다.
        """
        grid.addWidget(QLabel(label + " :"), row, 0)
        group = QButtonGroup(self)
        for index, (text, key) in enumerate(modes):
            rb = QRadioButton(text)
            rb.setProperty("mirror_key", key)
            if key == default_key:
                rb.setChecked(True)
            group.addButton(rb, index)
            grid.addWidget(rb, row, index + 1)
        return group

    @staticmethod
    def _mirror_key(group):
        """라디오 그룹에서 고른 항목의 식별자(mirror_key 프로퍼티)."""
        button = group.checkedButton()
        return button.property("mirror_key") if button else None

    # --------------------------------------------------------------
    # Tab : Constrain
    # --------------------------------------------------------------

    # Constrain 하위 탭: (탭 라벨, 툴팁 = 전체 이름/설명, 빌더 메서드 이름).
    # 라벨을 짧게 두는 이유는 탭 바가 창 폭(기본 560)을 넘기지 않게 하기 위해서다.
    # 전체 이름은 툴팁에 싣는다.
    CONSTRAIN_PAGES = (
        ("Constraint", "Multi target -> follower constraints (+ Matrix Constraint)",
         "_build_constraint_page"),
        ("Skin Weight", "Skin Weight to Constraint - constrain by the skin weights "
         "of the selected vertices", "_build_skin_constraint_page"),
        ("Group Create", "Insert zero-out offset nodes above / below each object",
         "_build_group_create_page"),
        ("Transfer", "Constraint Transfer - move an existing constraint onto "
         "another object", "_build_constraint_transfer_page"),
        ("Target Edit", "Replace / add / remove the targets (drivers) of existing "
         "constraints", "_build_target_edit_page"),
        ("Update", "Update Offset - re-bake the maintain offset of existing "
         "constraints from their current pose (the Attribute Editor's Update "
         "button, for the whole list at once)", "_build_constraint_update_page"),
    )

    def _build_constrain_tab(self):
        """Constrain 탭 — 기능별 **중첩 탭**.

        예전에는 접이식 박스(CollapsibleBox)를 위에서 아래로 쌓았는데, 기능이 5개로
        늘면서 원하는 것을 찾으려면 접었다 폈다 해야 했다. 이제 탭 하나에 기능 하나만
        보인다. 각 페이지는 따로 스크롤되므로 창을 줄여도 위젯이 겹치지 않는다.
        """
        self.constrain_tabs = self._build_sub_tabs(self.CONSTRAIN_PAGES)
        return self.constrain_tabs

    def _build_sub_tabs(self, pages):
        """(라벨, 툴팁, 빌더 메서드 이름) 목록을 중첩 탭 위젯으로 만든다.

        상위 탭 하나가 여러 기능을 품을 때 쓰는 공통 골격(Constrain / Connect).
        """
        tabs = QTabWidget()
        # 폭이 모자라면 라벨을 자른다(스크롤 화살표만 뜨는 것보다 읽기 쉽다).
        tabs.tabBar().setElideMode(Qt.ElideRight)

        for label, tip, builder in pages:
            index = tabs.addTab(self._scrolled(getattr(self, builder)()), label)
            tabs.setTabToolTip(index, tip)

        return tabs

    def _scrolled(self, widget):
        """위젯을 스크롤 영역에 담아 돌려준다 (창이 작아도 겹치지 않도록)."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    def _build_constraint_page(self):
        """기존 multi target -> follower constraint UI (Constrain 하위 탭)."""
        page = QWidget()
        layout = QVBoxLayout(page)

        self.tsl_targets = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select",
            list_min_height=200, log_callback=self.log)
        self.tsl_followers = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=200, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_targets)
        list_row.addWidget(self.tsl_followers)
        layout.addLayout(list_row)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # 대부분의 리깅 작업이 오프셋 유지를 전제로 해 기본 체크 상태로 둔다.
        self.cb_con_maintain = QCheckBox("Maintain Offset")
        self.cb_con_maintain.setChecked(True)
        opt_layout.addWidget(self.cb_con_maintain)

        # 종류는 체크박스 (v01.47, 예전엔 라디오) - 채널이 겹치지 않으면 여러 개를 함께 건다.
        # Parent + Scale / Point · Orient · Scale 중 2~3개. 겹치는 것(Parent 와 Point 등)을 체크하면
        # 먼저 체크돼 있던 쪽을 끈다 - 마야가 둘째를 `already connected` 로 거절하기 때문이다.
        self.cb_con_types = {}
        type_row = QHBoxLayout()
        for i, (key, label) in enumerate(con_mgr.CONSTRAIN_TYPES):
            cb = QCheckBox(label)
            cb.setChecked(i == 0)
            cb.setToolTip(self._con_type_tip(key))
            cb.toggled.connect(lambda checked, k=key: self._on_con_type_toggled(k, checked))
            self.cb_con_types[key] = cb
            type_row.addWidget(cb)
        opt_layout.addLayout(type_row)

        # --- Matrix Constraint 모드 ---
        # 체크 시 *Constraint 노드 대신 multMatrix/decomposeMatrix 네트워크로 구속한다.
        self.cb_con_matrix = QCheckBox("Matrix Constraint")
        self.cb_con_matrix.setChecked(False)
        opt_layout.addWidget(self.cb_con_matrix)

        # Matrix 모드 전용 채널 토글(기본 전부 on). 일반 모드에선 비활성.
        mtx_row = QHBoxLayout()
        self.cb_mtx_t = QCheckBox("Translate")
        self.cb_mtx_r = QCheckBox("Rotate")
        self.cb_mtx_s = QCheckBox("Scale")
        for cb in (self.cb_mtx_t, self.cb_mtx_r, self.cb_mtx_s):
            cb.setChecked(True)
            mtx_row.addWidget(cb)
        opt_layout.addLayout(mtx_row)

        self.cb_con_matrix.toggled.connect(self._on_matrix_mode_toggled)
        self._on_matrix_mode_toggled(False)

        layout.addWidget(opt_box)

        btn = QPushButton("Constrain")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self.on_constrain)
        layout.addWidget(btn)

        return page

    def _on_matrix_mode_toggled(self, enabled):
        """Matrix Constraint 모드 토글.

        Matrix on  : 채널(T/R/S) 체크박스 활성, 컨스트레인트 타입 라디오 비활성.
        Matrix off : 반대.
        """
        for cb in (self.cb_mtx_t, self.cb_mtx_r, self.cb_mtx_s):
            cb.setEnabled(enabled)
        for cb in self.cb_con_types.values():
            cb.setEnabled(not enabled)

    _CHANNEL_WORDS = {"t": "translate", "r": "rotate", "s": "scale"}

    def _con_type_tip(self, key):
        """체크박스 툴팁 - 무엇을 구동하고 무엇과 함께 못 거는지."""
        channels = con_mgr.CONSTRAIN_CHANNELS[key]
        labels = dict(con_mgr.CONSTRAIN_TYPES)
        if key == "pointOnPoly":
            return ("Drives translate + rotate from a mesh component.\n"
                    "Used alone - checking it unchecks the others.")
        clash = [labels[k] for k, _l in con_mgr.CONSTRAIN_TYPES
                 if k != key and con_mgr.types_conflict(key, k)]
        return "Drives {0}.\nCannot be combined with {1} (same channels).".format(
            " + ".join(self._CHANNEL_WORDS[c] for c in channels), ", ".join(clash))

    def _on_con_type_toggled(self, key, checked):
        """체크한 종류와 채널이 겹치는 종류를 끈다 (함께 걸 수 없다)."""
        if not checked:
            return
        for other, cb in self.cb_con_types.items():
            if other != key and cb.isChecked() and con_mgr.types_conflict(key, other):
                cb.setChecked(False)

    def _checked_con_types(self):
        return [key for key, _label in con_mgr.CONSTRAIN_TYPES
                if self.cb_con_types[key].isChecked()]

    def _build_skin_constraint_page(self):
        """Skin Weight to Constraint UI (Constrain 하위 탭).

        선택 버텍스의 스킨 웨이트로 영향 joint 들을 그 비율의 weight 로
        follower 에 constraint 한다. constraint 타입은 라디오로 고른다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # 어떤 버텍스를 선택했는지 리스트업하는 TSL + follower 리스트.
        self.tsl_skin_verts = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Vertices", select_label="Select",
            list_min_height=180, log_callback=self.log)
        self.tsl_skin_followers = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=180, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_skin_verts)
        list_row.addWidget(self.tsl_skin_followers)
        layout.addLayout(list_row)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # Max Influence : 사용할 최대 joint 개수 (0 = 제한 없음).
        mi_row = QHBoxLayout()
        mi_row.addWidget(QLabel("Max Influence"))
        self.sb_skin_max_inf = QSpinBox()
        self.sb_skin_max_inf.setRange(0, 100)
        self.sb_skin_max_inf.setValue(4)
        self.sb_skin_max_inf.setToolTip("Max number of influences to use (0 = no limit)")
        mi_row.addWidget(self.sb_skin_max_inf)
        mi_row.addStretch(1)
        opt_layout.addLayout(mi_row)

        self.cb_skin_maintain = QCheckBox("Maintain Offset")
        self.cb_skin_maintain.setChecked(True)
        opt_layout.addWidget(self.cb_skin_maintain)

        # 체크 시: vertices[i] 웨이트 -> followers[i] 1:1.
        # 해제 시: 모든 버텍스 웨이트 평균 -> 모든 follower 에 동일 적용.
        self.cb_skin_per_vertex = QCheckBox(
            "Per-vertex (vertex[i] -> follower[i], 1:1)")
        self.cb_skin_per_vertex.setChecked(False)
        opt_layout.addWidget(self.cb_skin_per_vertex)

        # 생성할 constraint 타입. 위 Constraint 박스와 같은 라디오 패턴.
        # (pointOnPoly 는 joint 가중 방식에 쓸 수 없어 목록에서 빠진다)
        self.rb_skin_con_group = QButtonGroup(self)
        rb_row = QHBoxLayout()
        for i, (key, label) in enumerate(skn_mgr.SKIN_CONSTRAIN_TYPES):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_skin_con_group.addButton(rb, i)
            rb_row.addWidget(rb)
        rb_row.addStretch(1)
        opt_layout.addLayout(rb_row)

        layout.addWidget(opt_box)

        btn_row = QHBoxLayout()

        btn = QPushButton("Skin Weight to Constraint")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Constrain the objects in the Followers list with the skin "
            "weights of the selected vertices.\n"
            "The constraint type is taken from the radio buttons above.")
        btn.clicked.connect(self.on_skin_weight_to_constraint)
        btn_row.addWidget(btn)

        # Locators : follower 를 직접 만들 필요 없이, 로케이터를 자동 생성하고
        # 동일한 스킨 웨이트 constraint 를 그 로케이터에 건다.
        btn_loc = QPushButton("Locators")
        btn_loc.setMinimumHeight(32)
        btn_loc.setToolTip(
            "Auto-create locators and run Skin Weight to Constraint on them "
            "(no Followers needed).\n"
            "Per-vertex: one locator per vertex at its position.\n"
            "Average: one locator at the centroid of selected vertices.")
        btn_loc.clicked.connect(self.on_skin_weight_to_locators)
        btn_row.addWidget(btn_loc)

        layout.addLayout(btn_row)

        return page

    def _build_group_create_page(self):
        """Group Create UI (Constrain 하위 탭).

        리스트업된 각 오브젝트에, 그 오브젝트와 위치·회전이 같은 오프셋 노드를
        부모 쪽/자식 쪽 계층에 삽입한다(zero-out). 노드명은 <obj>_<suffix>_01.
        Suffix / Count / Padding / 노드 타입(Group·오브젝트 타입) / 방향(Parent·Child)
        을 사용자가 지정한다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        self.tsl_group_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=180, log_callback=self.log)
        layout.addWidget(self.tsl_group_objs)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # Suffix / Count / Padding (한 줄).
        row = QHBoxLayout()
        row.addWidget(QLabel("Suffix"))
        self.le_group_suffix = QLineEdit("zro")
        self.le_group_suffix.setMaximumWidth(80)
        self.le_group_suffix.setToolTip(
            "Name suffix for created nodes. Node name = <object>_<suffix>_01.")
        row.addWidget(self.le_group_suffix)

        row.addWidget(QLabel("Count"))
        self.sb_group_count = QSpinBox()
        self.sb_group_count.setRange(1, 50)
        self.sb_group_count.setValue(1)
        self.sb_group_count.setToolTip(
            "How many nested nodes to create per object (per side).\n"
            "_01 is the object's immediate parent (Parent) / child (Child).")
        row.addWidget(self.sb_group_count)

        row.addWidget(QLabel("Padding"))
        self.sb_group_padding = QSpinBox()
        self.sb_group_padding.setRange(1, 6)
        self.sb_group_padding.setValue(2)
        self.sb_group_padding.setToolTip(
            "Zero-padding width of the number (2 -> 01, 02; 3 -> 001, 002).")
        row.addWidget(self.sb_group_padding)
        row.addStretch(1)
        opt_layout.addLayout(row)

        # Type : Group(기본) 또는 오브젝트와 동일 타입.
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type"))
        self.rb_group_type = QButtonGroup(self)
        rb_grp = QRadioButton("Group")
        rb_grp.setChecked(True)
        rb_grp.setToolTip("Created nodes are empty groups (transforms).")
        rb_match = QRadioButton("Match object type")
        rb_match.setToolTip(
            "Created nodes use the object's own node type\n"
            "(e.g. a joint object -> joint offset nodes).")
        self.rb_group_type.addButton(rb_grp, 0)
        self.rb_group_type.addButton(rb_match, 1)
        type_row.addWidget(rb_grp)
        type_row.addWidget(rb_match)
        type_row.addStretch(1)
        opt_layout.addLayout(type_row)

        # Side : Parent(기본 on) / Child. 둘 다 켜면 양쪽 모두 삽입.
        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("Side"))
        self.cb_group_parent = QCheckBox("Parent")
        self.cb_group_parent.setChecked(True)
        self.cb_group_parent.setToolTip(
            "Insert nodes between the object and its parent (object moves down).")
        self.cb_group_child = QCheckBox("Child")
        self.cb_group_child.setToolTip(
            "Insert nodes between the object and its children\n"
            "(existing children move down; none -> nodes hang under the object).")
        side_row.addWidget(self.cb_group_parent)
        side_row.addWidget(self.cb_group_child)
        side_row.addStretch(1)
        opt_layout.addLayout(side_row)

        layout.addWidget(opt_box)

        btn = QPushButton("Create Groups")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Insert offset node(s) (same world position/rotation) on the parent\n"
            "and/or child side of each listed object. Name = <object>_<suffix>_01.")
        btn.clicked.connect(self.on_group_create)
        layout.addWidget(btn)

        return page

    def _build_constraint_transfer_page(self):
        """Constraint Transfer UI (Constrain 하위 탭).

        왼쪽 목록의 constraint 를 오른쪽 목록의 오브젝트로 옮긴다(원본 삭제 + 동일
        세팅 재생성, maintainOffset 유지로 양쪽 모두 위치/회전 불변). UUID 기반.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # 왼쪽: 옮길 constraint(또는 constraint 가 걸린 트랜스폼).
        self.tsl_cxfer_cons = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Constraints", select_label="Select",
            list_min_height=180, log_callback=self.log)
        # 오른쪽: 새로 constraint 를 받을(driven) 오브젝트.
        self.tsl_cxfer_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Apply To", select_label="Select",
            list_min_height=180, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_cxfer_cons)
        list_row.addWidget(self.tsl_cxfer_objs)
        layout.addLayout(list_row)

        btn = QPushButton("Transfer Constraint")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Delete each listed constraint and re-create the same constraint\n"
            "(type, targets, weights, maintain offset) on the right-side object.\n"
            "Both the old and the new object keep their world position/rotation.\n"
            "Left items may be constraint nodes or objects that carry constraints.\n"
            "Mapping: 1 object -> all constraints go to it; equal counts -> 1:1.")
        btn.clicked.connect(self.on_transfer_constraint)
        layout.addWidget(btn)

        return page

    def _build_target_edit_page(self):
        """Target Edit UI (Constrain 하위 탭) - 타깃 교체 / 추가 / 삭제.

        리스트업한 constraint 들이 쓰고 있는 타깃(드라이버)을 모아 보여 주고, 고른
        타깃을 씬의 다른 오브젝트로 갈아끼우거나(Replace), 지우거나(Remove), New
        Target 리스트의 오브젝트를 새 타깃으로 붙인다(Add). 그 타깃을 쓰지 않는
        constraint 는 건드리지 않는다.

        세 동작 모두 **Constraints 리스트에서 고른 항목만** 대상으로 한다(아무것도
        고르지 않으면 리스트 전체). 한 페이지에 모은 이유는 셋 다 같은 입력
        (constraint 목록 + 타깃 목록 + 새 타깃 목록)을 쓰기 때문이다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # 왼쪽: 대상 constraint(또는 constraint 가 걸린 트랜스폼).
        self.tsl_tedit_cons = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Constraints", select_label="Select",
            list_min_height=160, log_callback=self.log)
        self.tsl_tedit_cons.setToolTip(
            "Constraint nodes, or objects that carry constraints (expanded to "
            "their constraint children).\n"
            "Pick rows to work on a subset - with nothing picked the whole list "
            "is used.")

        # 오른쪽: 위 constraint 들이 쓰고 있는 타깃 목록.
        targets_col = QVBoxLayout()
        head = QHBoxLayout()
        lbl = QLabel("Targets")
        font = lbl.font()
        font.setBold(True)
        lbl.setFont(font)
        head.addWidget(lbl)
        head.addStretch(1)
        self.lbl_tedit_number = QLabel("Number: 0")
        head.addWidget(self.lbl_tedit_number)
        targets_col.addLayout(head)

        self.lw_tedit_targets = QListWidget()
        self.lw_tedit_targets.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_tedit_targets.setMinimumHeight(160)
        self.lw_tedit_targets.setToolTip(
            "Targets used by the constraints on the left.\n"
            "[n/m] = used by n of the m constraints (hover for the list).\n"
            "Pick rows here to replace or remove those targets.")
        targets_col.addWidget(self.lw_tedit_targets)

        self.flt_tedit = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.lw_tedit_targets, placeholder="Type any part of a target name",
            number_label=self.lbl_tedit_number)
        targets_col.addWidget(self.flt_tedit)

        btn_row = QHBoxLayout()
        btn_list = QPushButton("List Targets")
        btn_list.setToolTip(
            "Collect every target used by the constraints on the left.")
        btn_list.clicked.connect(self.on_tedit_list)
        btn_row.addWidget(btn_list)
        btn_pick = QPushButton("Select")
        btn_pick.setToolTip("Select the picked targets in the scene.")
        btn_pick.clicked.connect(self.on_tedit_select)
        btn_row.addWidget(btn_pick)
        targets_col.addLayout(btn_row)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_tedit_cons)
        list_row.addLayout(targets_col)
        layout.addLayout(list_row)

        # 아래: 대신 들어갈 / 새로 붙일 오브젝트 (Replace 와 Add 가 공유).
        self.tsl_tedit_new = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="New Target (used by Replace / Add)", select_label="Select",
            list_min_height=110, log_callback=self.log)
        self.tsl_tedit_new.setToolTip(
            "Replace : the object(s) that take the picked target's place.\n"
            "Add     : the object(s) added as extra targets.")
        layout.addWidget(self.tsl_tedit_new)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        self.cb_tedit_keep = QCheckBox("Keep driven objects in place")
        self.cb_tedit_keep.setChecked(True)
        self.cb_tedit_keep.setToolTip(
            "On  : recompute the constraint offset so nothing moves when the "
            "targets change.\n"
            "Off : keep the original offset, so the driven object follows the "
            "new target set the same way it did before (it will jump).")
        opt_layout.addWidget(self.cb_tedit_keep)

        self.cb_tedit_rename = QCheckBox("Rename the weight attribute to the new target")
        self.cb_tedit_rename.setChecked(False)
        self.cb_tedit_rename.setToolTip(
            "Replace only. Rename the target weight attribute "
            "(tgt_A_02W0 -> tgt_B_02W0).\n"
            "Only auto-generated names are touched. Leave off if scripts refer "
            "to the weight by name.")
        opt_layout.addWidget(self.cb_tedit_rename)

        self.cb_tedit_delete_empty = QCheckBox(
            "Delete the constraint when its last target is removed")
        self.cb_tedit_delete_empty.setChecked(False)
        self.cb_tedit_delete_empty.setToolTip(
            "Remove only. Maya deletes a constraint node once its last target "
            "goes away\n"
            "(the driven object keeps the values it had).\n"
            "Off : such a constraint is skipped with a warning instead.")
        opt_layout.addWidget(self.cb_tedit_delete_empty)

        weight_row = QHBoxLayout()
        lbl_weight = QLabel("Added target weight")
        self.sb_tedit_weight = QDoubleSpinBox()
        self.sb_tedit_weight.setRange(0.0, 100.0)
        self.sb_tedit_weight.setSingleStep(0.1)
        self.sb_tedit_weight.setDecimals(3)
        self.sb_tedit_weight.setValue(1.0)
        self.sb_tedit_weight.setKeyboardTracking(False)
        self.sb_tedit_weight.setToolTip(
            "Add only. Constraint weight given to each added target.")
        weight_row.addWidget(lbl_weight)
        weight_row.addWidget(self.sb_tedit_weight)
        weight_row.addStretch(1)
        opt_layout.addLayout(weight_row)

        layout.addWidget(opt_box)

        btn_replace = QPushButton("Replace Target")
        btn_replace.setMinimumHeight(32)
        btn_replace.setToolTip(
            "Swap the picked target for the New Target on every constraint that "
            "uses it.\n"
            "Constraints without that target are left untouched.\n"
            "Weights, weight connections and the constraint node itself are kept.\n"
            "Mapping: 1 new target -> used for every picked target; equal counts "
            "-> 1:1.")
        btn_replace.clicked.connect(self.on_replace_target)
        layout.addWidget(btn_replace)

        edit_row = QHBoxLayout()

        btn_add = QPushButton("Add Target")
        btn_add.setMinimumHeight(32)
        btn_add.setToolTip(
            "Add every object in the New Target list as an extra target of every "
            "listed constraint.\n"
            "Targets a constraint already has are skipped.\n"
            "Weight aliases are created by Maya, so existing targets and their "
            "weights are kept.")
        btn_add.clicked.connect(self.on_add_target)
        edit_row.addWidget(btn_add)

        btn_remove = QPushButton("Remove Target")
        btn_remove.setMinimumHeight(32)
        btn_remove.setToolTip(
            "Remove the targets picked in the Targets list from the listed "
            "constraints.\n"
            "Constraints without those targets are left untouched.\n"
            "Removing a constraint's last target deletes the constraint - see "
            "the option above.")
        btn_remove.clicked.connect(self.on_remove_target)
        edit_row.addWidget(btn_remove)

        layout.addLayout(edit_row)

        return page

    def _build_constraint_update_page(self):
        """Update Offset UI (Constrain 하위 탭).

        Attribute Editor 의 constraint 에 있는 **Update** 버튼과 같은 일을 한다 —
        `parentConstraint -e -maintainOffset <targets> <constraint>`. AE 는 한 번에
        하나씩만 누를 수 있어서, 여기서는 리스트에 담은 constraint 전부에 돌린다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        note = QLabel(
            "Move the constrained objects first, then re-bake their offsets here.\n"
            "Same as the Update button in the Attribute Editor, run on every "
            "listed constraint at once.")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.tsl_cupd_cons = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Constraints", select_label="Select",
            list_min_height=220, log_callback=self.log)
        self.tsl_cupd_cons.setToolTip(
            "Constraint nodes, or objects that carry constraints (expanded to "
            "their constraint children).\n"
            "Pick rows to work on a subset - with nothing picked the whole list "
            "is used.")
        layout.addWidget(self.tsl_cupd_cons)

        btn = QPushButton("Update Offset")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Recompute the maintain offset of every listed constraint from the "
            "current pose,\n"
            "so each driven object stays where it is now.\n"
            "Types: parent / point / orient / scale / aim / point on poly.\n"
            "geometry / normal / tangent / pole vector have no offset and are "
            "skipped.\n"
            "A constraint nothing has moved is left with the values it already "
            "had (logged as 'no change').")
        btn.clicked.connect(self.on_update_constraint_offset)
        layout.addWidget(btn)

        return page

    # --------------------------------------------------------------
    # Tab : Connect  (하위 탭 : Connect / List Connected / Pair)
    # --------------------------------------------------------------

    # Connect 페이지의 두 패널 역할 -> 화면에 쓰는 이름. 연결 방향 로그/라벨에 쓴다.
    ROLE_LABELS = {"src": "Source", "dst": "Destination"}

    # Connect 하위 탭: (탭 라벨, 툴팁 = 설명, 빌더 메서드 이름).
    CONNECT_PAGES = (
        ("Connect", "Connect attributes from the source objects to the "
         "destination objects (+ Match from Source, 52 facial)",
         "_build_connect_page"),
        ("List Connected", "Explore the nodes up / down stream of the listed "
         "objects, by node type", "_build_list_connected_page"),
        ("Pair", "Pair Driver <-> Driven by name or by proximity, then "
         "constrain the pairs (was 'Connect Closest')",
         "_build_connect_closest_page"),
    )

    def _build_connect_tab(self):
        """Connect 탭 — 어트리뷰트/노드 연결 기능을 하나로 묶은 **중첩 탭**.

        Connect / List Connected / Pair 는 모두 "연결" 작업이라 최상위에
        따로 있을 이유가 없었다. Constrain 탭과 같은 방식으로 하위 탭에 모은다.
        """
        self.connect_tabs = self._build_sub_tabs(self.CONNECT_PAGES)
        return self.connect_tabs

    def _build_connect_page(self):
        """어트리뷰트 연결 UI (Connect 하위 탭). 양방향 모두 지원한다."""
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(self._build_connect_io("src", "Source Objects"))
        layout.addWidget(self._build_connect_io("dst", "Destination Objects"))

        # 두 방향을 나란히 둔다. 어느 쪽이 드라이버인지 화살표로 바로 읽힌다.
        dir_row = QHBoxLayout()

        btn_connect = QPushButton("Source  ->  Destination")
        btn_connect.setMinimumHeight(32)
        btn_connect.setToolTip(
            "Connect the selected Source attributes to the selected Destination\n"
            "attributes (Source drives Destination).")
        btn_connect.clicked.connect(self.on_connect_attrs)
        dir_row.addWidget(btn_connect)

        btn_connect_rev = QPushButton("Destination  ->  Source")
        btn_connect_rev.setMinimumHeight(32)
        btn_connect_rev.setToolTip(
            "The other way round: connect the selected Destination attributes to\n"
            "the selected Source attributes (Destination drives Source).\n"
            "Same pairing rules, only the direction is flipped.")
        btn_connect_rev.clicked.connect(self.on_connect_attrs_reverse)
        dir_row.addWidget(btn_connect_rev)

        layout.addLayout(dir_row)

        btn_facial = QPushButton("Connect 52 Facial Target")
        btn_facial.setToolTip(
            "Connect the 52 ARKit facial attributes by name, Source -> Destination.")
        btn_facial.clicked.connect(self.on_connect_52_facial)
        layout.addWidget(btn_facial)

        layout.addStretch(1)
        return page

    def _build_connect_io(self, role, title):
        """Connect 하위 탭의 Source/Destination 한 섹션을 만든다 (접이식).

        이 둘은 나란히 놓고 **동시에** 봐야 해서 탭이 아니라 접이식으로 둔다.
        """
        box = CollapsibleBox(title)

        tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=120, log_callback=self.log)

        attr_list = QListWidget()
        attr_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        attr_list.setMinimumHeight(120)

        btn_list = QPushButton("List Attributes")

        # 기본은 채널박스에 보이는 것만 — 연결 대상은 거의 다 채널박스 어트리뷰트다.
        cb_channel_box = QCheckBox("Channel Box Only")
        cb_channel_box.setChecked(True)
        cb_channel_box.setToolTip(
            "List only the attributes shown in the Channel Box\n"
            "(keyable + channel box, not hidden). Blend shape targets are kept.\n"
            "Uncheck to list every attribute of the node.")

        body = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(tsl)
        left.addWidget(btn_list)
        left.addWidget(cb_channel_box)

        right = QVBoxLayout()
        head = QHBoxLayout()
        head.addWidget(QLabel("Attributes"))
        head.addStretch(1)
        lbl_number = QLabel("Number: 0")
        head.addWidget(lbl_number)
        right.addLayout(head)
        right.addWidget(attr_list)

        # 검색 = 공용 Filter 위젯. 입력하는 즉시 일치하는 것만 남고 나머지는 숨는다.
        flt = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            attr_list, placeholder="Type any part of an attribute name",
            number_label=lbl_number)
        right.addWidget(flt)

        btn_all = QPushButton("Select All")
        btn_all.setToolTip("Select every attribute currently visible in the list.")
        btn_all.clicked.connect(flt.select_all_visible)
        right.addWidget(btn_all)

        # Destination 쪽에만: 소스에서 고른 어트리뷰트와 **이름이 비슷한** 것을 찾아
        # 소스 순서 그대로 목록 맨 위에 정렬 + 선택한다. 곧바로 Connect 로 이어진다.
        if role == "dst":
            right.addLayout(self._build_match_row())

        body.addLayout(left)
        body.addLayout(right)
        box.addLayout(body)

        self._connect_widgets[role] = {
            "tsl": tsl,
            "attrs": attr_list,
            "filter": flt,
            "channel_box": cb_channel_box,
        }

        btn_list.clicked.connect(lambda: self.on_list_attrs(role))
        # 이미 리스트가 채워져 있으면 토글 즉시 다시 채운다.
        cb_channel_box.toggled.connect(
            lambda _checked: attr_list.count() and self.on_list_attrs(role))

        return box

    def _build_match_row(self):
        """Destination 패널의 매칭 행 (버튼 2개 + 옵션 3개).

        매칭 방식이 두 가지(이름이 비슷한 것 / 이름이 똑같은 것)라 버튼과 옵션을 두 줄로
        나눈다. 옵션은 두 버튼이 **공유**한다 (`Min` 만 'Match from Source' 전용).
        """
        rows = QVBoxLayout()
        rows.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()

        btn = QPushButton("Match from Source")
        btn.setToolTip(
            "Find the destination attribute whose NAME is most similar to each "
            "source attribute.\n"
            "The matches are lined up with this list IN SOURCE ORDER and "
            "selected,\n"
            "so 'Source -> Destination' pairs them up right away.\n"
            "\n"
            "Example: source brow_up / brow_down against\n"
            "  lod0_mesh_body_eye_L_up, lod0_mesh_body_eye_L_down,\n"
            "  lod0_mesh_body_brow_up,  lod0_mesh_body_brow_down\n"
            "  ->  lod0_mesh_body_brow_up, lod0_mesh_body_brow_down\n"
            "\n"
            "Names are compared by tokens (brow_up == browUp), so a shared "
            "boilerplate\n"
            "prefix like lod0_mesh_body_ is ignored automatically.")
        btn.clicked.connect(self.on_match_from_source)
        row.addWidget(btn, 1)

        btn_same = QPushButton("Match Same Name")
        btn_same.setToolTip(
            "Only pair attributes whose names are EXACTLY the same "
            "(case sensitive).\n"
            "No similarity, no guessing - 'Min' is ignored.\n"
            "\n"
            "Example: source ab / abc / abcd against\n"
            "  bcd, cd, abcd, ab\n"
            "  ->  ab, {0}, abcd      ('abc' has no counterpart)\n"
            "\n"
            "Use it when both sides already share a naming convention, where a "
            "loose\n"
            "match would be worse than no match.".format(attr_match.NULL_TARGET))
        btn_same.clicked.connect(self.on_match_same_name)
        row.addWidget(btn_same, 1)

        rows.addLayout(row)

        # --- 옵션 행 (두 매칭 버튼이 함께 쓴다) ---
        row = QHBoxLayout()

        # 기본 ON : 짝이 어긋난 채 연결되는 사고를 막는 쪽이 기본값이어야 한다.
        self.cb_match_only = QCheckBox("Show Match Only")
        self.cb_match_only.setChecked(True)
        self.cb_match_only.setToolTip(
            "On  : keep only the rows that line up 1:1 with the source "
            "attributes.\n"
            "      A source with no counterpart gets a '{0}' row, so the "
            "pairing keeps\n"
            "      its order - those pairs are skipped when connecting.\n"
            "      Press 'List Attributes' to get the full list back.\n"
            "Off : the matches are moved to the top of the full list and "
            "selected\n"
            "      (unmatched sources leave the two sides out of "
            "step).".format(attr_match.NULL_TARGET))
        row.addWidget(self.cb_match_only)

        self.cb_match_unique = QCheckBox("Unique")
        self.cb_match_unique.setChecked(True)
        self.cb_match_unique.setToolTip(
            "On  : one destination attribute is never used twice.\n"
            "Off : two source attributes may match the same destination.")
        row.addWidget(self.cb_match_unique)

        row.addStretch(1)

        row.addWidget(QLabel("Min"))
        self.sb_match_min = QDoubleSpinBox()
        self.sb_match_min.setRange(0.0, 1.0)
        self.sb_match_min.setSingleStep(0.05)
        self.sb_match_min.setDecimals(2)
        self.sb_match_min.setValue(attr_match.DEFAULT_MIN_SCORE)
        self.sb_match_min.setKeyboardTracking(False)
        self.sb_match_min.setMaximumWidth(70)
        self.sb_match_min.setToolTip(
            "How much of the source name must be explained by the match (0-1).\n"
            "1.00 = every distinctive word of the source appears in the match.\n"
            "Raise it to reject loose matches, lower it to force a best guess.\n"
            "'Match Same Name' ignores this.")
        row.addWidget(self.sb_match_min)

        rows.addLayout(row)

        return rows

    # --------------------------------------------------------------
    # Tab : Attribute
    # --------------------------------------------------------------

    # Attribute 하위 탭: (탭 라벨, 툴팁 = 설명, 빌더 메서드 이름).
    ATTRIBUTE_PAGES = (
        ("Edit", "Pick existing attributes and reorder / copy / delete them",
         "_build_attribute_edit_page"),
        ("Create", "Create attributes from a saved profile (name / type / range) "
         "on the listed objects", "_build_attribute_create_page"),
        ("Set Value", "Set an attribute the listed objects share, all at once - "
         "number with a step, or enum item by name", "_build_attribute_value_page"),
    )

    def _build_attribute_tab(self):
        """Attribute 탭 — **있는 것을 다루는 Edit** 과 **없는 것을 만드는 Create**.

        v01.43 에서 Copy / Delete 를 Edit 하나로 합쳤다. 둘은 화면이 이미 같았다 —
        오브젝트를 담고 → 어트리뷰트를 나열하고 → 고른 것에 무언가를 한다. 다른 것은
        마지막 버튼 하나뿐이라, 같은 목록을 두 탭에서 따로 채우는 것이 낭비였다.
        순서 바꾸기(Up / Down)도 "고른 것에 무언가를 한다" 라 같은 자리에 들어간다.

        Create 는 합치지 않았다 — 씬에서 아무것도 읽지 않고 저장된 프로파일로 만드는,
        입력의 출처가 다른 작업이다.
        """
        self.attribute_tabs = self._build_sub_tabs(self.ATTRIBUTE_PAGES)
        return self.attribute_tabs

    # --------------------------------------------------------------
    # Attribute > Edit   (있는 어트리뷰트를 고르고 옮기고 복사하고 지우기)
    # --------------------------------------------------------------

    def _build_attribute_edit_page(self):
        """이미 있는 어트리뷰트를 **고르고 → 옮기거나 · 복사하거나 · 지운다**.

        ★ v01.43 에서 Copy 와 Delete 를 여기 하나로 합쳤다. 둘은 화면 구조가 이미 같았다 —
        `오브젝트 TSL -> List Attributes -> 어트리뷰트 목록(+필터) -> 실행 버튼`. 다른 것은
        **끝의 동작 하나**뿐이라 목록을 두 벌 유지할 이유가 없었다. 순서 바꾸기(Up / Down)도
        같은 목록에 붙는 일이라 함께 들어왔다.

        (`Create` 는 합치지 않았다 — 씬에서 어트리뷰트를 읽지 않고 저장된 프로파일로
        만드는, 성격이 다른 작업이다.)

        선택이 아니라 **체크박스**로 고른다. 필터를 걸어도 체크는 남으므로 여러 번 걸러
        가며 고른 것을 모을 수 있다.
        """
        content = QWidget()
        layout = QVBoxLayout(content)

        # --- 오브젝트 + 어트리뷰트 목록 (세 동작이 함께 쓴다) ---
        src_box = QGroupBox("Objects and their attributes")
        src_layout = QHBoxLayout(src_box)

        left = QVBoxLayout()
        self.tsl_aedit_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=170, log_callback=self.log)
        left.addWidget(self.tsl_aedit_objs)

        btn_list = QPushButton("List Attributes")
        btn_list.setToolTip(
            "List the attributes of every object in the list.\n"
            "The order shown is the order in the scene - that is what Up / Down "
            "changes.")
        btn_list.clicked.connect(self.on_aedit_list)
        left.addWidget(btn_list)
        src_layout.addLayout(left, 1)

        right = QVBoxLayout()
        head = QHBoxLayout()
        head.addWidget(QLabel("Attributes"))
        head.addStretch(1)
        self.lbl_aedit_number = QLabel("Number: 0")
        head.addWidget(self.lbl_aedit_number)
        right.addLayout(head)

        self.lw_aedit_attrs = QListWidget()
        self.lw_aedit_attrs.setMinimumHeight(170)
        self.lw_aedit_attrs.setToolTip(
            "Check the attributes to work on.\n"
            "Shift / Ctrl click to select several rows - clicking the check box of a\n"
            "selected row (or Space) checks or unchecks every selected row.\n"
            "Hover a row to see which objects carry it.\n"
            "Rows that cannot be reordered (built-ins) are shown in grey.")
        self.lw_aedit_attrs.itemChanged.connect(self._update_attr_preview)
        # v01.49 : Shift/Ctrl 다중 선택 + 고른 행 한꺼번에 체크 (Framework 공용 동작).
        self.chk_aedit_attrs = JUN_mod_checkList_qt.JUN_mod_checkList_qt_v01(
            self.lw_aedit_attrs)
        right.addWidget(self.lw_aedit_attrs, 1)

        # 기본값 ON : 리깅에서 다루는 것은 거의 항상 사용자 정의 어트리뷰트다.
        self.cb_attr_user_only = QCheckBox("User defined only")
        self.cb_attr_user_only.setChecked(True)
        self.cb_attr_user_only.setToolTip(
            "On  : only custom (user defined) attributes.\n"
            "Off : every attribute, including built-ins like translateX.\n"
            "Built-ins can be copied but NOT reordered - Maya cannot delete them.")
        right.addWidget(self.cb_attr_user_only)

        search_row = QHBoxLayout()
        self.flt_aedit = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.lw_aedit_attrs, placeholder="Type any part of an attribute name",
            number_label=self.lbl_aedit_number)
        search_row.addWidget(self.flt_aedit, 1)
        btn_check_all = QPushButton("Check All")
        btn_check_all.setToolTip("Check every attribute currently visible.")
        btn_check_all.clicked.connect(lambda: self._aedit_set_all(True))
        search_row.addWidget(btn_check_all)
        btn_uncheck = QPushButton("Clear Checks")
        btn_uncheck.setToolTip("Uncheck everything, visible or not.")
        btn_uncheck.clicked.connect(lambda: self._aedit_set_all(False))
        search_row.addWidget(btn_uncheck)
        right.addLayout(search_row)

        # ★ 필터에 가려진 채 체크된 것을 대상에 넣을지. 기본은 꺼 둔다 —
        #   "보이는 것이 작업 대상" 이 이 저장소의 규칙이고, 안 보이는 것을 건드리는 쪽이
        #   사고가 크다. 켜면 가려진 것까지 포함한다. 어느 쪽이든 몇 개가 가려졌는지 로그로 알린다.
        self.cb_aedit_hidden = QCheckBox("Include attributes hidden by the filter")
        self.cb_aedit_hidden.setChecked(False)
        self.cb_aedit_hidden.setToolTip(
            "Off (default) : only what you can see is acted on.\n"
            "On            : checked attributes hidden by the filter are included too.\n"
            "Either way the log tells you how many checked ones are hidden.")
        right.addWidget(self.cb_aedit_hidden)

        # --- 순서 바꾸기 ---
        order_row = QHBoxLayout()
        order_row.addWidget(QLabel("Order"))
        btn_up = QPushButton("Up")
        btn_up.setToolTip(
            "Move the checked attributes one slot up, on every listed object.\n"
            "Maya has no reorder command - this deletes and undoes each attribute,\n"
            "which keeps values, connections and keys. It cannot be undone with Ctrl+Z.")
        btn_up.clicked.connect(lambda: self.on_aedit_move(True))
        order_row.addWidget(btn_up)
        btn_down = QPushButton("Down")
        btn_down.setToolTip("Move the checked attributes one slot down.")
        btn_down.clicked.connect(lambda: self.on_aedit_move(False))
        order_row.addWidget(btn_down)
        order_row.addStretch(1)
        right.addLayout(order_row)

        # 옮기기 전 연결을 이름으로 적어 두고 옮긴 뒤 어긋난 것을 되돌린다 (v01.46).
        # Up/Down 줄 끝에 붙이면 오른쪽 열이 넓어져 따로 한 줄로 둔다.
        self.cb_aedit_keep_conn = QCheckBox("Maintain connections")
        self.cb_aedit_keep_conn.setChecked(True)
        self.cb_aedit_keep_conn.setToolTip(
            "On (default) : every connection keeps its attribute names after the move.\n"
            "               e.g. obj_01.attr_a -> obj_02.attr_a stays that way even when\n"
            "               attr_a and attr_b swap places on obj_02.\n"
            "               Connections are recorded before the move, compared after it,\n"
            "               and only the ones that differ are reconnected.\n"
            "Off          : the move does not check connections.")
        right.addWidget(self.cb_aedit_keep_conn)

        # --- 채널박스 표시 고치기 (v01.52) ---
        # 이미 숨은 채로 만들어져 버린 어트리뷰트를 되살리는 자리다. 새로 만드는 쪽은
        # 아래 Copy 와 Create 탭이 알아서 보이게 만든다.
        display_row = QHBoxLayout()
        display_row.addWidget(QLabel("Display"))
        btn_show_cb = QPushButton("Show in Channel Box")
        btn_show_cb.setToolTip(
            "Bring the checked attributes back into the channel box on every listed\n"
            "object. Keyable ones stay keyable; the rest become 'non-keyable displayed'.\n"
            "Attributes that came in from a REFERENCE cannot be changed - Maya refuses -\n"
            "so those have to be fixed in the rig scene and saved.")
        btn_show_cb.clicked.connect(self.on_aedit_show_cb)
        display_row.addWidget(btn_show_cb)
        display_row.addStretch(1)
        right.addLayout(display_row)

        src_layout.addLayout(right, 1)
        layout.addWidget(src_box)

        # --- 복사 ---
        copy_box = QGroupBox("Copy to other objects")
        copy_layout = QVBoxLayout(copy_box)

        self.tsl_attr_tgt = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets (new attributes here)", select_label="Select",
            list_min_height=130, log_callback=self.log)
        copy_layout.addWidget(self.tsl_attr_tgt)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Prefix"))
        self.le_attr_prefix = QLineEdit()
        self.le_attr_prefix.setPlaceholderText("e.g. L_")
        self.le_attr_prefix.textChanged.connect(self._update_attr_preview)
        name_row.addWidget(self.le_attr_prefix)
        name_row.addWidget(QLabel("Suffix"))
        self.le_attr_suffix = QLineEdit()
        self.le_attr_suffix.setPlaceholderText("e.g. _ctrl")
        self.le_attr_suffix.textChanged.connect(self._update_attr_preview)
        name_row.addWidget(self.le_attr_suffix)
        copy_layout.addLayout(name_row)

        self.lbl_attr_preview = QLabel("Preview : -")
        copy_layout.addWidget(self.lbl_attr_preview)

        self.cb_attr_value = QCheckBox("Copy current value")
        self.cb_attr_value.setChecked(True)
        self.cb_attr_value.setToolTip(
            "Also set the source value on the new attribute.")
        copy_layout.addWidget(self.cb_attr_value)

        self.cb_attr_show_cb = QCheckBox("Show in Channel Box")
        self.cb_attr_show_cb.setChecked(True)
        self.cb_attr_show_cb.setToolTip(
            "On (default) : the new attribute is always visible in the channel box,\n"
            "               even when the source attribute is hidden. Keyable sources\n"
            "               stay keyable, the rest become 'non-keyable displayed'.\n"
            "Off          : the copy keeps the display state of the source.\n\n"
            "Worth leaving on : once the object is loaded as a REFERENCE, Maya refuses\n"
            "to change the channel box state, so a hidden attribute stays hidden.")
        copy_layout.addWidget(self.cb_attr_show_cb)

        btn_copy = QPushButton("Copy Checked Attributes to Targets")
        btn_copy.setMinimumHeight(32)
        btn_copy.setToolTip(
            "Create the checked attributes on every object in the Targets list,\n"
            "keeping type / range / default / keyable. The definition is read from\n"
            "the FIRST object in the Objects list.\n"
            "Targets that already have the attribute are skipped.")
        btn_copy.clicked.connect(self.on_aedit_copy)
        copy_layout.addWidget(btn_copy)
        layout.addWidget(copy_box)

        # --- 지우기 ---
        btn_delete = QPushButton("Delete Checked Attributes")
        btn_delete.setMinimumHeight(32)
        btn_delete.setToolTip(
            "Delete the checked attributes from every object in the Objects list\n"
            "that has them. Locked attributes are reported, not force-unlocked.")
        btn_delete.clicked.connect(self.on_aedit_delete)
        layout.addWidget(btn_delete)

        layout.addStretch(1)
        return content

    # ==============================================================
    # Handlers : Attribute > Edit   (목록 · 순서 · 복사 · 삭제가 한 목록을 쓴다)
    # ==============================================================

    def _aedit_set_all(self, checked):
        """Check All / Clear Checks.

        켤 때는 **보이는 것만** 켠다(필터가 걸려 있으면 그 안에서). 끌 때는 **전부** 끈다 —
        안 보이는 곳에 체크가 남아 있는 것이 사고의 씨앗이기 때문이다.
        """
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.lw_aedit_attrs.count()):
            item = self.lw_aedit_attrs.item(i)
            if checked and item.isHidden():
                continue
            item.setCheckState(state)

    def _aedit_checked(self, warn=True):
        """체크된 어트리뷰트 이름. `Include hidden` 설정을 따른다.

        체크됐는데 필터에 가려진 것이 있으면 **어느 쪽을 택했든 로그로 알린다** —
        포함했으면 "안 보이는 것까지 건드렸다", 뺐으면 "고른 게 빠졌다" 를 모르면 안 된다.
        """
        visible, hidden = [], []
        for i in range(self.lw_aedit_attrs.count()):
            item = self.lw_aedit_attrs.item(i)
            if item.checkState() != Qt.Checked:
                continue
            (hidden if item.isHidden() else visible).append(item.text())

        include = self.cb_aedit_hidden.isChecked()
        if warn and hidden:
            if include:
                self.log("[INFO] {0} checked attribute(s) are hidden by the filter "
                         "- included ('Include attributes hidden by the filter' is "
                         "on)".format(len(hidden)))
            else:
                self.log("[INFO] {0} checked attribute(s) hidden by the filter were "
                         "skipped - tick 'Include attributes hidden by the filter' "
                         "to use them".format(len(hidden)))

        return visible + hidden if include else visible

    def _update_attr_preview(self, *_args):
        """Prefix/Suffix 를 적용한 새 이름을 첫 체크 항목으로 미리 보여준다."""
        if not hasattr(self, "lbl_attr_preview"):
            return
        checked = self._aedit_checked(warn=False)
        if not checked:
            self.lbl_attr_preview.setText("Preview : -")
            return
        new_name = att_mgr.build_new_name(
            checked[0],
            self.le_attr_prefix.text().strip(),
            self.le_attr_suffix.text().strip())
        more = "" if len(checked) == 1 else "   (+{0} more)".format(len(checked) - 1)
        self.lbl_attr_preview.setText(
            "Preview : {0}  ->  {1}{2}".format(checked[0], new_name, more))

    def on_aedit_list(self):
        """오브젝트들의 어트리뷰트를 **씬 순서 그대로** 목록에 채운다."""
        objects = self.tsl_aedit_objs.get_all_items()
        if not objects:
            self.log("[ERR] List Attributes : Objects list is empty")
            return

        user_only = self.cb_attr_user_only.isChecked()
        try:
            rows, missing = att_mgr.list_attributes_multi(objects, user_only)
        except Exception as e:
            self.log("[ERR] List Attributes : {0}".format(e))
            cmds.warning(str(e))
            return

        # 채우는 동안 itemChanged 가 매번 튀지 않도록 잠깐 막는다.
        self.lw_aedit_attrs.blockSignals(True)
        self.lw_aedit_attrs.clear()
        total_objs = len(objects) - len(missing)

        for row in rows:
            item = QListWidgetItem(row["name"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)

            tip = "on {0} of {1} object(s):\n  {2}".format(
                len(row["owners"]), total_objs, "\n  ".join(row["owners"][:12]))
            if not row["movable"]:
                tip += "\n\nBuilt-in - can be copied but NOT reordered."
                item.setForeground(QBrush(QColor("#808080")))
            if row["locked"]:
                tip += "\n\nLOCKED on {0} object(s)".format(len(row["locked"]))
                item.setForeground(QBrush(QColor("#e0a030")))
            item.setToolTip(tip)
            self.lw_aedit_attrs.addItem(item)

        self.lw_aedit_attrs.blockSignals(False)

        shown, total = self.flt_aedit.refresh()
        self._update_attr_preview()

        for obj in missing:
            self.log("[WARN] {0} : object not found in scene".format(obj))
        msg = "[OK] List Attributes : {0} attr(s) on {1} object(s){2}".format(
            total, total_objs, ", user defined" if user_only else "")
        if shown != total:
            msg += " - filter '{0}' shows {1}".format(
                self.flt_aedit.text().strip(), shown)
        self.log(msg)

    def on_aedit_move(self, up):
        """체크한 어트리뷰트를 한 칸 위/아래로 — 씬의 실제 순서가 바뀐다."""
        objects = self.tsl_aedit_objs.get_all_items()
        attrs = self._aedit_checked()
        keep_conn = self.cb_aedit_keep_conn.isChecked()

        def _do():
            logs, changed = aord_mgr.move_attributes(
                objects, attrs, up, maintain_connections=keep_conn)
            for line in logs:
                self.log(line)

        self._run("Move Attributes {0}".format("Up" if up else "Down"), _do)

        # 순서가 바뀌었으므로 목록을 다시 읽어 화면과 씬을 맞춘다(체크는 다시 살린다).
        if objects and attrs:
            checked = set(attrs)
            self.on_aedit_list()
            self.lw_aedit_attrs.blockSignals(True)
            for i in range(self.lw_aedit_attrs.count()):
                item = self.lw_aedit_attrs.item(i)
                if item.text() in checked:
                    item.setCheckState(Qt.Checked)
            self.lw_aedit_attrs.blockSignals(False)
            self._update_attr_preview()

    def on_aedit_copy(self):
        """체크한 어트리뷰트를 Targets 에 같은 정의로 새로 만든다."""
        objects = self.tsl_aedit_objs.get_all_items()
        source = objects[0] if objects else ""
        attrs = self._aedit_checked()
        targets = self.tsl_attr_tgt.get_all_items()
        prefix = self.le_attr_prefix.text().strip()
        suffix = self.le_attr_suffix.text().strip()
        copy_value = self.cb_attr_value.isChecked()
        show_cb = self.cb_attr_show_cb.isChecked()

        # 목록은 오브젝트들의 합집합이라, 첫 오브젝트에 없는 것이 체크될 수 있다.
        # 정의를 읽을 곳이 없으므로 미리 걸러 이유를 말한다.
        if source:
            missing = [a for a in attrs
                       if not cmds.attributeQuery(a, node=source, exists=True)]
            if missing:
                self.log("[WARN] {0} does not have {1} - copy reads the definition "
                         "from the first object".format(source, ", ".join(missing[:6])))
                attrs = [a for a in attrs if a not in missing]

        def _do():
            created, skipped = att_mgr.copy_attributes(
                source, attrs, targets, prefix, suffix, copy_value,
                show_in_channel_box=show_cb)
            for target, name, reason in skipped:
                self.log("[WARN] {0}.{1} : {2}".format(target, name, reason))
            self.log("       {0} attribute(s) created on {1} target(s)".format(
                len(created), len(targets)))

        self._run("Copy Attributes", _do)

    def on_aedit_show_cb(self):
        """체크한 어트리뷰트를 채널박스에 보이게 한다 (이미 숨어 있는 것 되살리기).

        새로 만들 때는 Copy / Create 가 알아서 보이게 하므로, 이 버튼은 **예전에 숨은
        채로 만들어진 것**을 위한 것이다. 레퍼런스에서 온 어트리뷰트는 마야가 표시 변경을
        거부하므로 여기서 고칠 수 없다 - 이유를 그대로 로그에 적는다.
        """
        objects = self.tsl_aedit_objs.get_all_items()
        attrs = self._aedit_checked()

        def _do():
            shown, skipped = adisp.show_attributes(objects, attrs)
            for obj, name, reason in skipped:
                self.log("[WARN] {0}.{1} : {2}".format(obj, name, reason))
            self.log("       {0} attribute(s) now visible in the channel box".format(
                len(shown)))

        self._run("Show in Channel Box", _do)

    def on_aedit_delete(self):
        """체크한 어트리뷰트를 Objects 목록의 오브젝트들에서 지운다."""
        objects = self.tsl_aedit_objs.get_all_items()
        attrs = self._aedit_checked()

        if attrs and QMessageBox.question(
                self, "Attribute",
                "Delete {0} attribute(s) from {1} object(s)?\n\n{2}".format(
                    len(attrs), len(objects),
                    ", ".join(attrs[:8]))) != QMessageBox.Yes:
            return

        def _do():
            deleted, failed = adel_mgr.delete_attributes(objects, attrs)
            for obj, name, reason in failed:
                self.log("[WARN] {0}.{1} : {2}".format(obj, name, reason))
            self.log("       {0} attribute(s) deleted from {1} object(s)".format(
                len(deleted), len(objects)))

        self._run("Delete Attributes", _do)
        # 지운 뒤에는 목록이 실제와 어긋나므로 다시 읽는다.
        if objects:
            self.on_aedit_list()

    # --------------------------------------------------------------
    # Attribute > Set Value   (여러 오브젝트의 공통 어트리뷰트를 한 번에 바꾸기)
    # --------------------------------------------------------------

    def _build_attribute_value_page(self):
        """옛 Number Tool(`JUN_PY_numberTool_V01_01`) 이식.

        오브젝트들을 담고 → **공통으로 가진** 어트리뷰트를 나열하고 → 고른 어트리뷰트를
        한 번에 바꾼다. 원본은 실수 하나로만 넣어서 enum 도 정수로 넣어야 했다. 여기서는
        고른 어트리뷰트의 종류에 따라 입력칸이 바뀐다:
          - float / int : 시작값 + Step (int 는 소수점 없는 칸)
          - enum / bool : 항목 **이름**을 콤보에서 고르고, Step 은 "몇 항목씩 건너뛸지"
        Step 은 **오브젝트 리스트 순서대로** 누적되고, Repeat 가 N 이면 N 개마다 처음으로.
        적용 전에 표에서 오브젝트마다 현재 값 -> 새 값을 미리 본다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # --- 오브젝트 + 공통 어트리뷰트 ---
        src_box = QGroupBox("Objects and the attributes they share")
        src_layout = QHBoxLayout(src_box)

        left = QVBoxLayout()
        # Step 이 리스트 순서대로 쌓이므로 Up / Down / Sort 가 의미 있다.
        self.tsl_aval_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects (order = step order)", select_label="Select",
            list_min_height=170, log_callback=self.log)
        left.addWidget(self.tsl_aval_objs)
        btn_list = QPushButton("List Attributes")
        btn_list.setToolTip(
            "List the attributes EVERY object in the list has, that take a\n"
            "number or an enum item (float / int / bool / enum).\n"
            "With 'Include Non-Common' on, attributes only some objects have are listed too.\n"
            "[k/n] = k of the n listed objects have the attribute.")
        btn_list.clicked.connect(self.on_aval_list)
        left.addWidget(btn_list)
        src_layout.addLayout(left, 1)

        right = QVBoxLayout()
        head = QHBoxLayout()
        self.lbl_aval_attrs_title = QLabel("Common Attributes")
        head.addWidget(self.lbl_aval_attrs_title)
        head.addStretch(1)
        self.lbl_aval_number = QLabel("Number: 0")
        head.addWidget(self.lbl_aval_number)
        right.addLayout(head)

        self.lw_aval_attrs = QListWidget()
        self.lw_aval_attrs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_aval_attrs.setMinimumHeight(170)
        self.lw_aval_attrs.setToolTip(
            "Select the attribute(s) to set.\n"
            "The value editor follows the first selected attribute's type;\n"
            "selected attributes of another type are skipped.")
        self.lw_aval_attrs.itemSelectionChanged.connect(self._aval_on_attr_changed)
        right.addWidget(self.lw_aval_attrs, 1)

        self.cb_aval_channel_box = QCheckBox("Channel Box Only")
        self.cb_aval_channel_box.setChecked(True)
        self.cb_aval_channel_box.setToolTip(
            "On  : only attributes shown in the Channel Box.\n"
            "Off : every number / enum attribute of the nodes.")
        self.cb_aval_channel_box.toggled.connect(
            lambda _c: self.lw_aval_attrs.count() and self.on_aval_list())
        # 겹치지 않는 어트리뷰트도 (v01.56). 체크박스 둘은 한 줄에 - 세로 공간을 아낀다.
        self.cb_aval_partial = QCheckBox("Include Non-Common")
        self.cb_aval_partial.setChecked(False)
        self.cb_aval_partial.setToolTip(
            "Off : only the attributes EVERY object has.\n"
            "On  : also the attributes only some objects have.\n"
            "[k/n] after a name = k of the n objects have it; objects without it\n"
            "are skipped by Set Values (shown in the preview).")
        self.cb_aval_partial.toggled.connect(
            lambda _c: self.lw_aval_attrs.count() and self.on_aval_list())
        cb_row = QHBoxLayout()
        cb_row.addWidget(self.cb_aval_channel_box)
        cb_row.addWidget(self.cb_aval_partial)
        cb_row.addStretch(1)
        right.addLayout(cb_row)

        self.flt_aval = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.lw_aval_attrs, placeholder="Type any part of an attribute name",
            number_label=self.lbl_aval_number)
        right.addWidget(self.flt_aval)
        src_layout.addLayout(right, 1)
        layout.addWidget(src_box)

        # --- 값 ---
        val_box = QGroupBox("Value")
        val_layout = QVBoxLayout(val_box)

        self.lbl_aval_info = QLabel("Attribute : -")
        val_layout.addWidget(self.lbl_aval_info)

        self.stk_aval = QStackedWidget()

        # 0 : 숫자 (float / int)
        num_page = QWidget()
        num_row = QHBoxLayout(num_page)
        num_row.setContentsMargins(0, 0, 0, 0)
        num_row.addWidget(QLabel("Start"))
        self.sp_aval_start = QDoubleSpinBox()
        self.sp_aval_step = QDoubleSpinBox()
        for sp in (self.sp_aval_start, self.sp_aval_step):
            sp.setRange(-1e9, 1e9)
            sp.setDecimals(4)
            sp.setKeyboardTracking(False)
            sp.valueChanged.connect(self._aval_update_preview)
        self.sp_aval_start.setToolTip("Value for the first object in the list.")
        num_row.addWidget(self.sp_aval_start, 1)
        num_row.addWidget(QLabel("Step"))
        self.sp_aval_step.setToolTip(
            "Added per object, in list order: object i gets Start + i * Step.\n"
            "0 = every object gets the same value.")
        num_row.addWidget(self.sp_aval_step, 1)
        self.stk_aval.addWidget(num_page)

        # 1 : 항목 (enum / bool)
        enum_page = QWidget()
        enum_row = QHBoxLayout(enum_page)
        enum_row.setContentsMargins(0, 0, 0, 0)
        enum_row.addWidget(QLabel("Item"))
        self.cmb_aval_item = QComboBox()
        self.cmb_aval_item.setToolTip("Item for the first object in the list.")
        self.cmb_aval_item.currentIndexChanged.connect(self._aval_update_preview)
        enum_row.addWidget(self.cmb_aval_item, 1)
        enum_row.addWidget(QLabel("Step"))
        self.sp_aval_item_step = QSpinBox()
        self.sp_aval_item_step.setRange(-999, 999)
        self.sp_aval_item_step.setKeyboardTracking(False)
        self.sp_aval_item_step.setToolTip(
            "Items to move forward per object, in list order (wraps around).\n"
            "0 = every object gets the same item.")
        self.sp_aval_item_step.valueChanged.connect(self._aval_update_preview)
        enum_row.addWidget(self.sp_aval_item_step)
        self.stk_aval.addWidget(enum_page)

        val_layout.addWidget(self.stk_aval)

        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("Repeat every"))
        self.sp_aval_repeat = QSpinBox()
        self.sp_aval_repeat.setRange(0, 99999)
        self.sp_aval_repeat.setKeyboardTracking(False)
        self.sp_aval_repeat.setSpecialValueText("Off")
        self.sp_aval_repeat.setToolTip(
            "Go back to the start value every N objects.\n"
            "e.g. Start 0, Step 1, Repeat 3 -> 0, 1, 2, 0, 1, 2 ...\n"
            "Off = keep stepping to the end of the list.")
        self.sp_aval_repeat.valueChanged.connect(self._aval_update_preview)
        opt_row.addWidget(self.sp_aval_repeat)
        opt_row.addWidget(QLabel("objects"))
        opt_row.addSpacing(12)
        self.cb_aval_clamp = QCheckBox("Clamp to range")
        self.cb_aval_clamp.setChecked(True)
        self.cb_aval_clamp.setToolTip(
            "On  : values past the attribute's min / max are clamped.\n"
            "Off : Maya refuses them and the object is reported as failed.")
        self.cb_aval_clamp.toggled.connect(self._aval_update_preview)
        opt_row.addWidget(self.cb_aval_clamp)
        opt_row.addStretch(1)
        btn_get = QPushButton("Get")
        btn_get.setToolTip("Read the current value of the first object as the start.")
        btn_get.clicked.connect(self.on_aval_get)
        opt_row.addWidget(btn_get)
        val_layout.addLayout(opt_row)

        # 미리보기: 오브젝트마다 현재 값 -> 새 값. 건너뛸 것은 이유를 적는다.
        self.tw_aval_preview = QTreeWidget()
        self.tw_aval_preview.setHeaderLabels(["Object", "Current", "New", "Note"])
        self.tw_aval_preview.setRootIsDecorated(False)
        self.tw_aval_preview.setMinimumHeight(150)
        self.tw_aval_preview.setToolTip(
            "What Set Values will do. Grey rows are skipped (see Note).")
        val_layout.addWidget(self.tw_aval_preview, 1)

        btn_set = QPushButton("Set Values")
        btn_set.setMinimumHeight(32)
        btn_set.setToolTip(
            "Set the selected attribute(s) on every listed object as previewed.\n"
            "Keyed attributes get a key at the current frame. One undo step.")
        btn_set.clicked.connect(self.on_aval_set)
        val_layout.addWidget(btn_set)

        layout.addWidget(val_box, 1)
        return page

    # ==============================================================
    # Handlers : Attribute > Set Value
    # ==============================================================

    def _aval_selected_attrs(self):
        """선택된(필터에 보이는) 어트리뷰트 이름, 목록 순서대로.

        행 글자에는 `[k/n]` 이 붙으므로 이름은 UserRole 에서 읽는다.
        """
        return [self.lw_aval_attrs.item(i).data(Qt.UserRole)
                for i in range(self.lw_aval_attrs.count())
                if self.lw_aval_attrs.item(i).isSelected()
                and not self.lw_aval_attrs.item(i).isHidden()]

    def _aval_owner(self, objects, attr):
        """리스트에서 그 어트리뷰트를 가진 첫 오브젝트. 없으면 None.

        Include Non-Common 이면 첫 오브젝트에 없는 어트리뷰트도 고를 수 있어서,
        종류·범위·Get 은 **그것을 가진** 첫 오브젝트에서 읽는다.
        """
        for obj in objects:
            if cmds.objExists(obj) and aval_mgr.attr_info(obj, attr) is not None:
                return obj
        return None

    def _aval_current_info(self):
        """첫 선택 어트리뷰트의 정보(그것을 가진 첫 오브젝트 기준). 없으면 None."""
        objects = self.tsl_aval_objs.get_all_items()
        attrs = self._aval_selected_attrs()
        if not objects or not attrs:
            return None
        owner = self._aval_owner(objects, attrs[0])
        if owner is None:
            return None
        return aval_mgr.attr_info(owner, attrs[0])

    def on_aval_list(self):
        """오브젝트들의 어트리뷰트를 채운다. 고른 것은 이어받는다.

        기본은 모두가 가진 것만, Include Non-Common 이면 일부만 가진 것도.
        행마다 `[k/n]` = n 개 오브젝트 중 k 개가 가졌다(Target Edit 의 Targets 와 같은 표기).
        """
        objects = self.tsl_aval_objs.get_all_items()
        if not objects:
            self.log("[ERR] List Attributes : Objects list is empty")
            return
        cb_only = self.cb_aval_channel_box.isChecked()
        partial = self.cb_aval_partial.isChecked()
        self.lbl_aval_attrs_title.setText("Attributes" if partial else "Common Attributes")
        try:
            rows, missing = aval_mgr.list_common_attrs(
                objects, cb_only, include_partial=partial)
        except Exception as e:
            self.log("[ERR] List Attributes : {0}".format(e))
            cmds.warning(str(e))
            return

        keep = set(self._aval_selected_attrs())
        self.lw_aval_attrs.blockSignals(True)
        self.lw_aval_attrs.clear()
        for row in rows:
            item = QListWidgetItem("{0}   [{1}/{2}]".format(
                row["name"], row["count"], row["total"]))
            item.setData(Qt.UserRole, row["name"])
            tip = "{0}\nOn {1} of {2} object(s)".format(
                row["kind"], row["count"], row["total"])
            if row["count"] < row["total"]:
                lacking = [o for o in objects
                           if o not in row["owners"] and o not in missing]
                tip += "\nMissing on (skipped by Set Values):\n  " + "\n  ".join(lacking)
            item.setToolTip(tip)
            self.lw_aval_attrs.addItem(item)
            item.setSelected(row["name"] in keep)
        self.lw_aval_attrs.blockSignals(False)
        shown, total = self.flt_aval.refresh()
        self._aval_on_attr_changed()

        for obj in missing:
            self.log("[WARN] {0} : object not found in scene".format(obj))
        present = len(objects) - len(missing)
        if partial:
            common = sum(1 for r in rows if r["count"] == r["total"])
            msg = ("[OK] List Attributes : {0} attr(s) on {1} object(s) - {2} common, "
                   "{3} on some only{4}").format(
                total, present, common, total - common,
                ", channel box only" if cb_only else "")
        else:
            msg = "[OK] List Attributes : {0} attr(s) shared by {1} object(s){2}".format(
                total, present, ", channel box only" if cb_only else "")
        if shown != total:
            msg += " - filter '{0}' shows {1}".format(self.flt_aval.text().strip(), shown)
        self.log(msg)

    def _aval_on_attr_changed(self):
        """첫 선택 어트리뷰트의 종류에 맞춰 입력칸(숫자 / 항목)을 바꾼다."""
        info = self._aval_current_info()
        attrs = self._aval_selected_attrs()
        if info is None:
            self.lbl_aval_info.setText("Attribute : -")
            self._aval_update_preview()
            return

        kind = info["kind"]
        text = "Attribute : {0}   ({1}".format(attrs[0], info["type"])
        if info["min"] is not None or info["max"] is not None:
            text += ", range {0} ~ {1}".format(
                "-" if info["min"] is None else aval_mgr._fmt(info["min"], kind),
                "-" if info["max"] is None else aval_mgr._fmt(info["max"], kind))
        text += ")"
        if len(attrs) > 1:
            text += "   +{0} more".format(len(attrs) - 1)
        self.lbl_aval_info.setText(text)

        if kind in (aval_mgr.KIND_ENUM, aval_mgr.KIND_BOOL):
            prev = self.cmb_aval_item.currentText()
            self.cmb_aval_item.blockSignals(True)
            self.cmb_aval_item.clear()
            for name, value in info["items"]:
                self.cmb_aval_item.addItem("{0}  ({1})".format(name, value), name)
            idx = self.cmb_aval_item.findText(prev)
            self.cmb_aval_item.setCurrentIndex(max(idx, 0))
            self.cmb_aval_item.blockSignals(False)
            self.stk_aval.setCurrentIndex(1)
        else:
            decimals = 0 if kind == aval_mgr.KIND_INT else 4
            for sp in (self.sp_aval_start, self.sp_aval_step):
                sp.blockSignals(True)
                sp.setDecimals(decimals)
                sp.blockSignals(False)
            self.stk_aval.setCurrentIndex(0)
        self.cb_aval_clamp.setEnabled(kind in (aval_mgr.KIND_FLOAT, aval_mgr.KIND_INT))
        self._aval_update_preview()

    def _aval_plan(self):
        """현재 입력으로 (선택 어트리뷰트마다) 적용 계획을 만든다. (rows, kind)."""
        objects = self.tsl_aval_objs.get_all_items()
        attrs = self._aval_selected_attrs()
        info = self._aval_current_info()
        if info is None:
            return [], None
        kind = info["kind"]
        repeat = self.sp_aval_repeat.value()
        if kind in (aval_mgr.KIND_ENUM, aval_mgr.KIND_BOOL):
            values = aval_mgr.build_enum_values(
                len(objects), info["items"], max(self.cmb_aval_item.currentIndex(), 0),
                self.sp_aval_item_step.value(), repeat)
        else:
            values = aval_mgr.build_values(
                len(objects), self.sp_aval_start.value(),
                self.sp_aval_step.value(), repeat)

        rows = []
        for attr in attrs:
            rows.extend(aval_mgr.plan(objects, attr, kind, values,
                                      clamp=self.cb_aval_clamp.isChecked()))
        return rows, kind

    def _aval_update_preview(self, *_args):
        if not hasattr(self, "tw_aval_preview"):
            return
        self.tw_aval_preview.clear()
        try:
            rows, _kind = self._aval_plan()
        except Exception as e:
            self.log("[ERR] Set Value preview : {0}".format(e))
            return
        grey = QBrush(QColor("#808080"))
        for row in rows:
            item = QTreeWidgetItem([row["plug"], row["current"], row["shown"], row["note"]])
            if row["status"] != "ok":
                for col in range(4):
                    item.setForeground(col, grey)
            self.tw_aval_preview.addTopLevelItem(item)
        for col in range(3):
            self.tw_aval_preview.resizeColumnToContents(col)

    def on_aval_get(self):
        """첫 오브젝트의 현재 값을 시작값(또는 시작 항목)으로 읽어 온다."""
        objects = self.tsl_aval_objs.get_all_items()
        attrs = self._aval_selected_attrs()
        info = self._aval_current_info()
        if info is None:
            self.log("[ERR] Get : list objects and select an attribute first")
            return
        # 그 어트리뷰트를 가진 첫 오브젝트에서 읽는다 (Include Non-Common 이면 [0] 에 없을 수 있다)
        owner = self._aval_owner(objects, attrs[0])
        value = cmds.getAttr("{0}.{1}".format(owner, attrs[0]))
        if info["kind"] in (aval_mgr.KIND_ENUM, aval_mgr.KIND_BOOL):
            values = [v for _n, v in info["items"]]
            if int(value) in values:
                self.cmb_aval_item.setCurrentIndex(values.index(int(value)))
        else:
            self.sp_aval_start.setValue(value)
        self.log("[OK] Get : {0}.{1} = {2}".format(owner, attrs[0], value))

    def on_aval_set(self):
        """미리보기대로 값을 넣는다 (undo 한 번)."""
        attrs = self._aval_selected_attrs()
        if not self.tsl_aval_objs.get_all_items() or not attrs:
            self.log("[ERR] Set Values : list objects and select an attribute first")
            return
        rows, kind = self._aval_plan()

        def _do():
            done, keyed, failed = aval_mgr.apply(rows)
            for row in rows:
                if row["status"] != "ok":
                    self.log("[WARN] {0} : skipped - {1}".format(row["plug"], row["note"]))
            for plug, reason in failed:
                self.log("[WARN] {0} : {1}".format(plug, reason))
            self.log("       {0} value(s) set ({1}){2}".format(
                done, kind, ", {0} keyed".format(keyed) if keyed else ""))

        self._run("Set Values : {0}".format(", ".join(attrs[:4])), _do)
        self._aval_update_preview()

    # --------------------------------------------------------------
    # Attribute > Create   (프로파일에 적어 둔 정의로 새로 만들기)
    # --------------------------------------------------------------

    def _build_attribute_create_page(self):
        """왼쪽 = 대상 오브젝트, 오른쪽 = 프로파일에 저장해 둔 어트리뷰트 정의.

        Copy 탭과 달리 **씬에 원본이 없어도** 된다. 리그마다 늘 같은 어트리뷰트
        (World / Root / Shoulder 같은 [0,1] 실수)를 손으로 addAttr 하던 일을 없애는
        것이 목적이라, 정의는 프로파일 JSON 에 남아 다음 씬에서도 그대로 쓰인다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        body = QHBoxLayout()
        layout.addLayout(body)

        # --- 왼쪽 : 어트리뷰트를 만들 오브젝트들
        # Up/Down/Order 를 끈 이유는 폭 때문만이 아니다 — 여기서는 **순서가 아무 뜻도
        # 없다**(체크한 어트리뷰트를 리스트의 모든 오브젝트에 똑같이 만든다). 그리고 그
        # 버튼 행이 TSL 최소 폭의 대부분이라(실측 322 -> 179px), 좌우로 나란히 놓는 이
        # 탭에서는 켜 두면 창 폭을 넘겨 오른쪽이 잘린다.
        # 제목이 길면 그 라벨이 TSL 최소 폭을 그대로 밀어 올린다(실측 263 -> 160px).
        # 설명은 툴팁으로 옮긴다.
        self.tsl_acr_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            show_up=False, show_down=False, show_order=False,
            list_min_height=220, log_callback=self.log)
        self.tsl_acr_objs.setToolTip(
            "Objects to create the checked attributes on.\n"
            "Order does not matter - every object in the list gets the same set.")
        body.addWidget(self.tsl_acr_objs, 1)

        # --- 오른쪽 : 프로파일 + 그 프로파일의 어트리뷰트 목록
        right = QVBoxLayout()
        body.addLayout(right, 1)

        right.addWidget(self._build_attr_profile_group())

        head = QHBoxLayout()
        head.addWidget(QLabel("Attributes"))
        head.addStretch(1)
        self.lbl_acr_number = QLabel("Number: 0")
        head.addWidget(self.lbl_acr_number)
        right.addLayout(head)

        # 체크박스로 만들 것을 고른다(A00290_BSTool 의 Mix Targets 와 같은 방식).
        # 선택(하이라이트)은 Edit / Remove 대상이고, 체크는 Create 대상이다.
        self.lw_acr_attrs = QListWidget()
        self.lw_acr_attrs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_acr_attrs.setMinimumHeight(160)
        self.lw_acr_attrs.setToolTip(
            "Check the attributes to create.\n"
            "Shift / Ctrl click to select several rows - clicking the check box of a\n"
            "selected row (or Space) checks or unchecks every selected row.\n"
            "Select (highlight) a row and use Edit / Remove to change the profile.\n"
            "Double-click a row to edit it.")
        self.lw_acr_attrs.itemChanged.connect(self._acr_on_item_changed)
        # v01.50 : 고른 행 한꺼번에 체크 (Edit 탭과 같은 Framework 공용 동작).
        self.chk_acr_attrs = JUN_mod_checkList_qt.JUN_mod_checkList_qt_v01(
            self.lw_acr_attrs)
        self.lw_acr_attrs.itemDoubleClicked.connect(
            lambda _item: self.on_acr_edit_attr())
        right.addWidget(self.lw_acr_attrs, 1)

        self.flt_acr = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.lw_acr_attrs, placeholder="Type any part of an attribute name",
            number_label=self.lbl_acr_number)
        right.addWidget(self.flt_acr)

        all_row = QHBoxLayout()
        self.chk_acr_all = QCheckBox("Check All (visible)")
        self.chk_acr_all.setTristate(True)
        self.chk_acr_all.setToolTip(
            "Check or uncheck every attribute currently visible in this list.\n"
            "Partially filled means some are checked.")
        self.chk_acr_all.clicked.connect(self.on_acr_check_all)
        all_row.addWidget(self.chk_acr_all)
        all_row.addStretch(1)
        self.lbl_acr_checked = QLabel("Checked: 0")
        all_row.addWidget(self.lbl_acr_checked)
        right.addLayout(all_row)

        edit_row = QHBoxLayout()
        for label, tip, slot in (
                ("Add", "Add a new attribute definition to this profile",
                 self.on_acr_add_attr),
                ("Edit", "Edit the selected attribute definition",
                 self.on_acr_edit_attr),
                ("Remove", "Remove the selected attribute definitions from "
                 "this profile", self.on_acr_remove_attr)):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            edit_row.addWidget(btn)
        right.addLayout(edit_row)

        btn_create = QPushButton("Create Checked Attributes")
        btn_create.setMinimumHeight(32)
        btn_create.setToolTip(
            "Create every CHECKED attribute on every object in the list on the "
            "left.\nObjects that already have the attribute are skipped - "
            "nothing is overwritten.")
        btn_create.clicked.connect(self.on_acr_create)
        layout.addWidget(btn_create)

        # 창을 열 때 마지막으로 쓰던 프로파일을 그대로 불러온다.
        self._acr_profile = aprefs.get_active()
        self._acr_data = aprefs.load_profile(self._acr_profile)
        self._acr_refresh_profiles()
        self._acr_render_attrs()

        return page

    def _build_attr_profile_group(self):
        """프로파일 콤보 + New / Rename / Delete (A00340_SelectionTool 과 같은 구성).

        A00340 은 넷을 **한 줄**에 놓지만 여기서는 **두 줄**로 나눈다. 이 탭은 좌우로
        나뉘어 있어 이 그룹이 창 폭의 절반만 쓰는데, 한 줄이면 그룹 하나가 최소 363px 를
        요구해(실측) 오른쪽이 잘린다. 두 줄이면 261px 로 내려간다 — 콤보가 길어질수록
        (프로파일 이름이 길수록) 이득이 커진다.
        """
        group = QGroupBox("Profile")
        outer = QVBoxLayout(group)

        self.cmb_acr_profile = QComboBox()
        # 긴 프로파일 이름 때문에 콤보가 통째로 넓어지지 않도록 줄여서 보여 준다.
        self.cmb_acr_profile.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_acr_profile.setMinimumContentsLength(8)
        self.cmb_acr_profile.setToolTip(
            "Active profile - a saved set of attribute definitions\n"
            "(each profile is its own JSON under the tool's data folder).")
        self.cmb_acr_profile.currentTextChanged.connect(self.on_acr_profile_changed)
        outer.addWidget(self.cmb_acr_profile)

        row = QHBoxLayout()
        for label, tip, slot in (
                ("New", "Create a new profile", self.on_acr_new_profile),
                ("Rename", "Rename the current profile", self.on_acr_rename_profile),
                ("Delete", "Delete the current profile", self.on_acr_delete_profile)):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        outer.addLayout(row)

        return group

    # --------------------------------------------------------------
    # Attribute > Delete
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    # Connect > List Connected
    # --------------------------------------------------------------

    def _build_list_connected_page(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        row = QHBoxLayout()

        # Objects
        self.tsl_stream_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=220, log_callback=self.log)
        row.addWidget(self.tsl_stream_objs)

        # Types
        types_box = QVBoxLayout()
        types_box.addWidget(QLabel("Types"))
        self.list_types = QListWidget()
        self.list_types.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_types.setMinimumHeight(180)
        types_box.addWidget(self.list_types)
        btn_up = QPushButton("List UpStream")
        btn_dn = QPushButton("List DownStream")
        btn_up.clicked.connect(lambda: self.on_list_stream(True))
        btn_dn.clicked.connect(lambda: self.on_list_stream(False))
        types_box.addWidget(btn_up)
        types_box.addWidget(btn_dn)
        row.addLayout(types_box)

        # Nodes
        nodes_box = QVBoxLayout()
        nodes_box.addWidget(QLabel("Nodes"))
        self.list_nodes = QListWidget()
        self.list_nodes.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_nodes.setMinimumHeight(180)
        self.list_nodes.itemSelectionChanged.connect(self.on_nodes_selection_changed)
        nodes_box.addWidget(self.list_nodes)
        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.on_search_nodes)
        nodes_box.addWidget(btn_search)
        row.addLayout(nodes_box)

        layout.addLayout(row)
        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Connect > Pair  (A00140 ConnectClosest 이식 + 이름 매칭)
    # --------------------------------------------------------------

    def _build_connect_closest_page(self):
        """Driver <-> Driven 짝짓기 + constraint (Connect 하위 탭 'Pair').

        짝을 세우는 방법이 둘이다 — **거리**(Get Closest, A00140 이식)와 **이름**
        (Match by Name, v01.37). 어느 쪽이든 결과는 Driven 리스트가 Driver 순서에
        맞춰 서는 것이고, 짝이 없는 자리는 `(Null)` 이 지킨다.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        set_box = QGroupBox("Set Up")
        set_rows = QVBoxLayout(set_box)
        list_row = QHBoxLayout()
        self.cc_driven = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Driven",
            list_min_height=200, log_callback=self.log)
        self.cc_driver = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Driver",
            list_min_height=200, log_callback=self.log)
        # 각 Driver 에 가장 가까운 오브젝트를 찾아 Driven 을 driver 순서대로 채운다.
        # 후보 풀: Driven 에 항목이 있으면 그걸, 없으면 현재 씬 선택.
        self.cc_driver.add_button("Get Closest", self.on_get_closest)
        # 같은 자리에 '이름으로' 찾는 버튼도 둔다 (후보 풀 규칙도 동일).
        self.cc_driver.add_button("Match by Name", self.on_match_by_name)
        list_row.addWidget(self.cc_driven)
        list_row.addWidget(self.cc_driver)
        set_rows.addLayout(list_row)

        # 두 리스트 **아래 전체 폭**으로 (각 리스트의 Sort 버튼 밑). 리스트 하나에
        # 딸린 버튼이 아니라 **둘 다에 걸리는** 동작이라 폭을 상자 전체로 둔다.
        btn_swap = QPushButton("Swap")
        btn_swap.setToolTip(
            "Swap the two lists: what is now Driven becomes Driver and back.\n"
            "Row order is kept, so pairs built with 'Match by Name' (and the "
            "'{0}' rows)\n"
            "stay lined up - only the direction of the constraint is "
            "flipped.".format(obj_match.NULL_TARGET))
        btn_swap.clicked.connect(self.on_pair_swap)
        set_rows.addWidget(btn_swap)

        layout.addWidget(set_box)

        layout.addWidget(self._build_object_match_box())
        layout.addWidget(self._build_pairing_box())

        opt_box = QGroupBox("Constraint Type")
        opt_layout = QVBoxLayout(opt_box)
        cb_row = QHBoxLayout()
        self.cc_checkboxes = {}
        for key, label, _method in CONSTRAINT_TYPES:
            cb = QCheckBox(label)
            self.cc_checkboxes[key] = cb
            cb_row.addWidget(cb)
        self.cc_checkboxes["parent"].setChecked(True)
        opt_layout.addLayout(cb_row)
        self.cc_maintain = QCheckBox("Maintain Offset")
        self.cc_maintain.setChecked(True)
        opt_layout.addWidget(self.cc_maintain)
        layout.addWidget(opt_box)

        btn = QPushButton("Connect")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Constrain each Driven object to its Driver.\n"
            "Which object goes with which is decided by the Pairing option above.")
        btn.clicked.connect(self.on_connect_closest)
        layout.addWidget(btn)

        layout.addStretch(1)
        return tab

    def _build_object_match_box(self):
        """'Match by Name' 옵션 상자 (Connect 하위 탭 'Pair').

        Connect > Connect 의 어트리뷰트 매칭 옵션과 **같은 이름·같은 뜻**으로 둔다
        (`Unique` / `Min`). 오브젝트에만 있는 것은 `Ignore Namespace` 하나다.
        """
        box = QGroupBox("Match by Name")
        rows = QVBoxLayout(box)

        row = QHBoxLayout()

        self.cb_om_exact = QCheckBox("Same Name Only")
        self.cb_om_exact.setChecked(False)
        self.cb_om_exact.setToolTip(
            "On  : pair only objects whose names are EXACTLY the same "
            "(case sensitive, 'Min' is ignored).\n"
            "      Use it when both sides already share a naming convention, "
            "where a loose match\n"
            "      would be worse than no match.\n"
            "Off : pair by name similarity - names are compared by tokens "
            "(ctrl_L_arm == ctrlLArm),\n"
            "      so a prefix both sides carry is ignored automatically.")
        row.addWidget(self.cb_om_exact)

        self.cb_om_unique = QCheckBox("Unique")
        self.cb_om_unique.setChecked(True)
        self.cb_om_unique.setToolTip(
            "On  : one Driven object is never used twice.\n"
            "Off : two Drivers may match the same Driven object.")
        row.addWidget(self.cb_om_unique)

        self.cb_om_namespace = QCheckBox("Ignore Namespace")
        self.cb_om_namespace.setChecked(True)
        self.cb_om_namespace.setToolTip(
            "On  : compare 'rig:jnt_L_arm' as 'jnt_L_arm' - the usual case when "
            "one side is referenced.\n"
            "Off : the namespace is part of the name, so 'rig:jnt_L_arm' and "
            "'jnt_L_arm' score lower.\n"
            "The DAG path (|grp|...) is always dropped before comparing; the "
            "full path is still what gets connected.")
        row.addWidget(self.cb_om_namespace)

        row.addStretch(1)

        row.addWidget(QLabel("Min"))
        self.sb_om_min = QDoubleSpinBox()
        self.sb_om_min.setRange(0.0, 1.0)
        self.sb_om_min.setSingleStep(0.05)
        self.sb_om_min.setDecimals(2)
        self.sb_om_min.setValue(obj_match.DEFAULT_MIN_SCORE)
        self.sb_om_min.setKeyboardTracking(False)
        self.sb_om_min.setMaximumWidth(70)
        self.sb_om_min.setToolTip(
            "How much of the Driver name must be explained by the match (0-1).\n"
            "1.00 = every distinctive word of the Driver name appears in the "
            "Driven name.\n"
            "Raise it to reject loose matches, lower it to force a best guess.\n"
            "'Same Name Only' ignores this.")
        row.addWidget(self.sb_om_min)

        rows.addLayout(row)
        return box

    def _build_pairing_box(self):
        """Connect 가 무엇을 짝으로 볼지 (Connect 하위 탭 'Pair').

        예전에는 Connect 가 **언제나 거리로 다시 계산**했다. 그러면 Match by Name 으로
        세운 짝이나 Up/Down 으로 맞춘 순서가 연결 순간에 조용히 뒤집힌다. 그래서
        짝짓는 방법을 눈에 보이게 꺼냈다.
        """
        box = QGroupBox("Pairing")
        row = QHBoxLayout(box)

        self.rb_cc_group = QButtonGroup(self)

        self.rb_cc_closest = QRadioButton("Closest distance")
        self.rb_cc_closest.setChecked(True)
        self.rb_cc_group.addButton(self.rb_cc_closest)
        self.rb_cc_closest.setToolTip(
            "Ignore the row order: for each Driver, find the nearest Driven "
            "object again (greedy 1:1).\n"
            "This is what the tab has always done.")
        row.addWidget(self.rb_cc_closest)

        self.rb_cc_order = QRadioButton("List order")
        self.rb_cc_group.addButton(self.rb_cc_order)
        self.rb_cc_order.setToolTip(
            "Pair row by row, exactly as the two lists read (Driver row 1 with "
            "Driven row 1, ...).\n"
            "Use it after 'Match by Name', or after ordering the lists by hand "
            "with Up / Down.\n"
            "'{0}' rows are skipped as a pair, so the rest stay lined "
            "up.".format(obj_match.NULL_TARGET))
        row.addWidget(self.rb_cc_order)

        row.addStretch(1)
        return box

    # ==============================================================
    # UI helpers
    # ==============================================================

    def _selected_texts(self, list_widget):
        return [it.text() for it in list_widget.selectedItems()]

    def _all_texts(self, list_widget):   # noqa: 유틸 (현재 호출부 없음)
        return [list_widget.item(i).text() for i in range(list_widget.count())]

    def log(self, text):
        self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "RigConnect v{0}\n"
            "Written by Ji Hun Park\n"
            "Update date : {1}\n"
            "\n"
            "Match       : match followers to targets (rotateOrder safe)\n"
            "              options: Translation / Rotation / Scale (world) / Parent\n"
            "              + create locators/sphere/cube at targets + vertex normal (+Y)\n"
            "              followers may be components too - a vertex/CV is moved\n"
            "                             to the target position (position only)\n"
            "              {2}+ items are summarized instead of listed ('List All')\n"
            "              Cache Targets: remember world T/R/S with no nodes,\n"
            "                             then Swap + Match to put things back\n"
            "              Keep Children in Place: only the follower moves,\n"
            "                             everything under it stays (off by default)\n"
            "Constrain   : sub-tabs -\n"
            "              Constraint   : multi target -> follower (+ Matrix)\n"
            "              Skin Weight  : constrain by the selected vertices'\n"
            "                             skin weights (+ auto Locators)\n"
            "              Group Create : zero-out offset nodes\n"
            "              Transfer     : move a constraint onto another object\n"
            "              Target Repl. : swap a constraint target, offset kept\n"
            "Connect     : sub-tabs -\n"
            "              Connect      : connect attributes BOTH ways\n"
            "                             (Source -> Destination and back),\n"
            "                             3 broadcast patterns + 52 facial\n"
            "                             + Match from Source (find look-alike\n"
            "                             destination attributes, in order)\n"
            "              List Conn.   : explore up/down stream nodes by type\n"
            "              Pair         : pair Driver <-> Driven 1:1, then\n"
            "                             constrain - Get Closest (distance)\n"
            "                             or Match by Name (similar / same\n"
            "                             name, unmatched rows kept as (Null))\n"
            "                             + Swap to flip Driven <-> Driver\n"
            "Attribute   : Edit   : list the attributes of the listed objects and,\n"
            "                       on the checked ones, change their order\n"
            "                       (Up / Down), copy them onto other objects,\n"
            "                       or delete them. Reorder changes the real order\n"
            "                       in the scene and CANNOT be undone with Ctrl+Z.\n"
            "              Create : create attributes from a saved profile\n"
            "                       (name / type / range), checkbox per attr\n"
            "Mirror      : mirror the listed objects and everything under them -\n"
            "              names swap L/R with the shared token rules, and skin\n"
            "              weights, constraints and clusters are rebuilt on the\n"
            "              other side (YZ/XY/XZ plane, Behavior / Orientation)\n"
            "              Apply (Source -> Target): nothing is created - each\n"
            "              Target object takes the mirrored position / rotation\n"
            "              of the Source object in the same row, its children\n"
            "              kept in place (Keep Children in Place)".format(
                VERSION, LAST_UPDATE, MATCH_LIST_LIMIT))

    def _run(self, label, func):
        """undo chunk 로 감싸 실행하고 결과를 로그에 남긴다."""
        with undo_chunk():
            try:
                func()
                self.log("[OK] {0}".format(label))
            except Exception as e:
                self.log("[ERR] {0} : {1}".format(label, e))
                cmds.warning(str(e))

    # ==============================================================
    # Handlers : Mirror
    # ==============================================================

    def on_mirror(self):
        if self.rb_mirror_apply.isChecked():
            self.on_mirror_apply()
            return

        objects = self.tsl_mirror.get_all_items()
        plane = self._mirror_key(self.rb_mirror_plane)
        joint_mode = self._mirror_key(self.rb_mirror_joint)
        other_mode = self._mirror_key(self.rb_mirror_other)
        disable_token_check = self.cb_mirror_no_token.isChecked()
        do_skin = self.cb_mirror_skin.isChecked()
        do_constraints = self.cb_mirror_constraints.isChecked()
        do_clusters = self.cb_mirror_clusters.isChecked()
        do_networks = self.cb_mirror_networks.isChecked()

        self.log("--- Mirror ({0} plane, joints {1}, others {2}) ---".format(
            plane.upper(), joint_mode, other_mode))

        def _do():
            try:
                created, warns, infos = mir_mgr.mirror(
                    objects, plane=plane, joint_mode=joint_mode, other_mode=other_mode,
                    disable_token_check=disable_token_check,
                    do_skin=do_skin, do_constraints=do_constraints,
                    do_clusters=do_clusters, do_networks=do_networks)
            except mir_mgr.MissingTokenError as e:
                # 예외로 나가면 반환값(경고)이 통째로 사라진다. 이름 목록을 먼저 찍고
                # 다시 던져 _run 이 [ERR] 로 마무리하게 둔다.
                for line in e.report:
                    self.log("[WARN] {0}".format(line))
                if e.set_name:
                    # 세트를 만들어 놓고 아웃라이너에서 찾게 두면 소용이 적다.
                    # (cmds.select 는 세트를 주면 멤버를 펼쳐 선택한다)
                    cmds.select(e.set_name, replace=True)
                    self.log("       members of '{0}' are selected.".format(e.set_name))
                raise
            for warn in warns:
                self.log("[WARN] {0}".format(warn))
            for info in infos:
                self.log("       {0}".format(info))
            if created:
                cmds.select(created)

        self._run("Mirror", _do)

    def on_mirror_apply(self):
        """Source -> Target : 새로 만들지 않고 Target 오브젝트를 Source 의 미러 위치 / 회전으로."""
        sources = self.tsl_mirror_source.get_all_items()
        targets = self.tsl_mirror_target.get_all_items()
        plane = self._mirror_key(self.rb_mirror_plane)
        joint_mode = self._mirror_key(self.rb_mirror_joint)
        other_mode = self._mirror_key(self.rb_mirror_other)
        translate = self.cb_mirror_translate.isChecked()
        rotate = self.cb_mirror_rotate.isChecked()
        keep_children = self.cb_mirror_keep_children.isChecked()

        self.log("--- Mirror Source -> Target ({0} plane, joints {1}, others {2}, "
                 "translation {3}, rotation {4}, keep children {5}) ---".format(
                     plane.upper(), joint_mode, other_mode,
                     "on" if translate else "off", "on" if rotate else "off",
                     "on" if keep_children else "off"))

        def _do():
            moved, warns, infos = mir_mgr.mirror_onto(
                sources, targets, plane=plane, joint_mode=joint_mode,
                other_mode=other_mode, translate=translate, rotate=rotate,
                keep_children=keep_children)
            for warn in warns:
                self.log("[WARN] {0}".format(warn))
            for info in infos:
                self.log("       {0}".format(info))
            if moved:
                cmds.select(moved)

        self._run("Mirror Source -> Target", _do)

    # ==============================================================
    # Handlers : Match
    # ==============================================================

    def on_match(self):
        targets = self.tsl_match_tgt.get_all_items()
        followers = self.tsl_match_flw.get_all_items()
        one_to_many = self.cb_mt_one_to_many.isChecked()

        # 모드 판정은 코어와 **같은 함수**로 한다(두 군데로 갈라지면 로그와 동작이 어긋난다).
        pairs, fan_out, unpaired = mch_mgr.resolve_pairs(
            targets, followers, one_to_many)

        if fan_out:
            self.log("       1 <- n : {0} follower(s) -> 1 target".format(
                len(pairs)))
        elif unpaired:
            # 개수 불일치 경고는 n <- n 일 때만 뜻이 있다(1 <- n 은 달라도 정상).
            self.log("[WARN] Match : target/follower counts differ "
                     "({0} vs {1}) - matching {2} pair(s)".format(
                         len(targets), len(followers), len(pairs)))
            if one_to_many and len(targets) > 1:
                self.log("       (1 <- n needs exactly 1 target, got {0})".format(
                    len(targets)))

        translate = self.cb_mt_translate.isChecked()
        rotate = self.cb_mt_rotate.isChecked()
        scale = self.cb_mt_scale.isChecked()
        parent = self.cb_mt_parent.isChecked()
        keep_children = self.cb_mt_keep_children.isChecked()
        if not (translate or rotate or scale or parent):
            self.log("[WARN] Match : no channel selected "
                     "(Translation/Rotation/Scale/Parent all off)")
            return

        # 캐시(스냅샷) 타겟은 씬을 읽지 않으므로 몇 개인지 알려 준다.
        cached = sum(1 for tgt, _flw in pairs if snap_mgr.is_snapshot(tgt))

        def _do():
            notes = []
            matched, skipped = mch_mgr.match(
                targets, followers,
                translate=translate, rotate=rotate,
                scale=scale, parent=parent,
                cache=self.snapshots, notes=notes,
                one_to_many=one_to_many, keep_children=keep_children)
            self.log("       {0} matched, {1} skipped [{2}] ({3})".format(
                matched, skipped,
                "".join(c for c, on in (
                    ("T", translate), ("R", rotate),
                    ("S", scale), ("P", parent),
                    ("K", keep_children)) if on),
                "1 <- n" if fan_out else "n <- n"))
            if cached:
                self.log("       {0} cached target(s) - restored from memory, "
                         "no scene nodes read".format(cached))
                if not scale:
                    # 캐시는 스케일도 들고 있는데 채널이 꺼져 있으면 그대로 남는다.
                    self.log("       [note] Scale is off - the cached scale was "
                             "not restored. Tick Scale for an exact restore "
                             "(it is also the fastest path).")
            for note in notes:
                # 정보성 줄(NOTE_PREFIX)은 실패가 아니다 - [skip] 으로 찍으면 오해를 부른다.
                if note.startswith(mch_mgr.NOTE_PREFIX):
                    self.log("       [note] {0}".format(
                        note[len(mch_mgr.NOTE_PREFIX):]))
                else:
                    self.log("       [skip] {0}".format(note))

        self._run("Match", _do)

    # ---- Cache (추상 스냅샷)

    def _update_cache_label(self):
        count = len(self.snapshots)
        self.lbl_match_cache.setText(
            "Cached: {0}".format(count) if count else "Cached: none")

    def on_match_cache(self):
        """Targets 의 월드 T/R/S 를 값으로 기억하고 Followers 에 캐시 항목을 채운다.

        씬을 바꾸지 않으므로(값만 읽는다) undo chunk 로 감싸지 않는다.
        """
        targets = self.tsl_match_tgt.get_all_items()
        if not targets:
            self.log("[WARN] Cache Targets : the Targets list is empty")
            return

        notes = []
        try:
            keys = mch_mgr.capture(targets, self.snapshots, notes=notes)
        except Exception as e:
            self.log("[ERR] Cache Targets : {0}".format(e))
            cmds.warning(str(e))
            return

        self.tsl_match_flw.set_items(keys)
        self._update_cache_label()
        self.log("[OK] Cache Targets")
        self.log("       cached {0} item(s) - no nodes created. Swap, move "
                 "things, then Match to put them back.".format(len(keys)))
        for note in notes:
            self.log("       [skip] {0}".format(note))

    def on_match_cache_clear(self):
        """캐시를 비우고, 두 리스트에 남은 캐시 항목도 함께 걷어낸다."""
        removed = self.snapshots.clear()
        dropped = 0
        for tsl in (self.tsl_match_tgt, self.tsl_match_flw):
            items = tsl.get_all_items()
            kept = [t for t in items if not snap_mgr.is_snapshot(t)]
            if len(kept) != len(items):
                dropped += len(items) - len(kept)
                tsl.set_items(kept)
        self._update_cache_label()
        self.log("[OK] Clear Cache : {0} cached transform(s) dropped, "
                 "{1} list item(s) removed".format(removed, dropped))

    def on_match_create(self, ctl_type):
        targets = self.tsl_match_tgt.get_all_items()

        def _do():
            created = mch_mgr.create_and_match(
                targets, ctl_type, cache=self.snapshots)
            # 생성한 컨트롤을 Followers 목록에 채우고 씬에서 선택.
            self.tsl_match_flw.set_items(created)
            if created:
                cmds.select(created)
            self.log("       created and matched {0} {1}(s)".format(
                len(created), ctl_type))

        self._run("Create {0}".format(ctl_type), _do)

    def on_match_swap(self):
        targets = self.tsl_match_tgt.get_all_items()
        followers = self.tsl_match_flw.get_all_items()
        self.tsl_match_tgt.set_items(followers)
        self.tsl_match_flw.set_items(targets)
        self.log("[OK] Swap : targets <-> followers")

    # ==============================================================
    # Handlers : Constrain
    # ==============================================================

    def on_constrain(self):
        targets = self.tsl_targets.get_all_items()
        followers = self.tsl_followers.get_all_items()
        maintain_offset = self.cb_con_maintain.isChecked()

        if self.cb_con_matrix.isChecked():
            translate = self.cb_mtx_t.isChecked()
            rotate = self.cb_mtx_r.isChecked()
            scale = self.cb_mtx_s.isChecked()

            def _do():
                made, errors = mtx_mgr.matrix_constraint(
                    targets, followers, maintain_offset,
                    translate, rotate, scale)
                for err in errors:
                    self.log("[WARN] {0}".format(err))
                self.log("       {0} matrix constraint(s) created".format(
                    len(made)))

            self._run("Matrix Constraint", _do)
            return

        con_types = self._checked_con_types()
        labels = dict(con_mgr.CONSTRAIN_TYPES)

        def _do():
            made, errors = con_mgr.constrain_types(
                targets, followers, con_types, maintain_offset)
            for err in errors:
                self.log("[WARN] {0}".format(err))
            for key in con_types:
                count = sum(1 for k, _node in made if k == key)
                self.log("       {0} {1} constraint(s) created".format(count, labels[key]))

        self._run("Constrain ({0})".format(" + ".join(labels[k] for k in con_types)), _do)

    def _skin_con_type(self):
        """Skin Weight to Constraint 박스에서 선택한 constraint 타입 key."""
        return skn_mgr.SKIN_CONSTRAIN_TYPES[self.rb_skin_con_group.checkedId()][0]

    def on_skin_weight_to_constraint(self):
        vertices = self.tsl_skin_verts.get_all_items()
        followers = self.tsl_skin_followers.get_all_items()
        max_influence = self.sb_skin_max_inf.value()
        maintain_offset = self.cb_skin_maintain.isChecked()
        per_vertex = self.cb_skin_per_vertex.isChecked()
        con_type = self._skin_con_type()

        def _do():
            made = skn_mgr.skin_weight_to_constraint(
                vertices, followers, max_influence, maintain_offset, per_vertex,
                con_type)
            self.log("       {0} {1} constraint(s) created".format(
                len(made), con_type))

        self._run("Skin Weight to Constraint", _do)

    def on_skin_weight_to_locators(self):
        vertices = self.tsl_skin_verts.get_all_items()
        max_influence = self.sb_skin_max_inf.value()
        maintain_offset = self.cb_skin_maintain.isChecked()
        per_vertex = self.cb_skin_per_vertex.isChecked()
        con_type = self._skin_con_type()

        def _do():
            created, made = skn_mgr.create_locators_and_constrain(
                vertices, max_influence, maintain_offset, per_vertex, con_type)
            # 생성한 로케이터를 Followers 목록에 채우고 씬에서 선택.
            self.tsl_skin_followers.set_items(created)
            if created:
                cmds.select(created)
            self.log("       {0} locator(s) created, "
                     "{1} constraint(s) applied".format(len(created), len(made)))

        self._run("Skin Weight to Locators", _do)

    def on_group_create(self):
        objs = self.tsl_group_objs.get_all_items()
        count = self.sb_group_count.value()
        suffix = self.le_group_suffix.text().strip()
        padding = self.sb_group_padding.value()
        match_type = (self.rb_group_type.checkedId() == 1)
        do_parent = self.cb_group_parent.isChecked()
        do_child = self.cb_group_child.isChecked()

        def _do():
            created, warns = grp_mgr.create_offset_nodes(
                objs, count=count, suffix=suffix, match_type=match_type,
                create_parent=do_parent, create_child=do_child, padding=padding)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            self.log("       {0} node(s) created for {1} object(s)".format(
                len(created), len(objs)))
            # 생성한 노드를 씬에서 선택.
            if created:
                cmds.select(created)

        self._run("Group Create", _do)

    def on_transfer_constraint(self):
        cons = self.tsl_cxfer_cons.get_all_items()
        objs = self.tsl_cxfer_objs.get_all_items()

        def _do():
            created, warns = cxfer_mgr.transfer_constraints(cons, objs)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            self.log("       {0} constraint(s) transferred".format(len(created)))

        self._run("Constraint Transfer", _do)

    # ==============================================================
    # Handlers : Target Replace
    # ==============================================================

    def _tedit_picked_targets(self, warn=False):
        """Targets 목록에서 **보이면서 선택된** 타깃 이름들.

        Qt 는 필터로 숨긴 항목의 선택도 유지하므로, 가려진 것까지 교체해 버리지
        않도록 걸러 낸다. 표시 텍스트에는 '[2/3]' 같은 사용 횟수가 붙으므로 실제
        노드 이름은 항목 데이터에서 꺼낸다.
        """
        names = []
        hidden = 0
        for item in self.lw_tedit_targets.selectedItems():
            if item.isHidden():
                hidden += 1
                continue
            names.append(item.data(Qt.UserRole) or item.text())
        if warn and hidden:
            self.log("[INFO] {0} picked target(s) hidden by the filter were "
                     "skipped".format(hidden))
        return names

    def _tedit_constraints(self, warn=False):
        """작업 대상 constraint 이름들 — 리스트에서 **고른 항목**, 없으면 전체.

        한 리스트로 여러 constraint 를 다루다 보면 그중 일부에만 타깃을 붙이고 싶을
        때가 많다. 고른 게 없으면 예전처럼 리스트 전체를 쓴다.
        """
        picked = self.tsl_tedit_cons.selected_items()
        if picked:
            if warn:
                self.log("[INFO] using {0} picked constraint(s) of {1}".format(
                    len(picked), self.tsl_tedit_cons.count()))
            return picked
        return self.tsl_tedit_cons.get_all_items()

    def on_tedit_list(self):
        cons = self._tedit_constraints(warn=True)
        if not cons:
            self.log("[ERR] List Targets : constraint list is empty")
            return
        try:
            rows, warns = ctgt_mgr.list_targets(cons)
        except Exception as e:
            self.log("[ERR] List Targets : {0}".format(e))
            cmds.warning(str(e))
            return

        for w in warns:
            self.log("[WARN] {0}".format(w))

        self.lw_tedit_targets.clear()
        for row in rows:
            item = QListWidgetItem("{0}   [{1}/{2}]".format(
                row["name"], len(row["constraints"]), row["total"]))
            item.setData(Qt.UserRole, row["name"])
            item.setToolTip("Used by:\n  {0}".format(
                "\n  ".join(row["constraints"])))
            self.lw_tedit_targets.addItem(item)

        shown, total = self.flt_tedit.refresh()
        msg = "[OK] List Targets : {0} target(s)".format(total)
        if shown != total:
            msg += " - filter '{0}' shows {1}".format(
                self.flt_tedit.text().strip(), shown)
        self.log(msg)

    def on_tedit_select(self):
        picked = self._tedit_picked_targets(warn=True)
        if not picked:
            self.log("[ERR] Select : pick target(s) in the Targets list")
            return
        try:
            cmds.select(picked, replace=True)
        except Exception as e:
            self.log("[ERR] Select : {0}".format(e))
            cmds.warning(str(e))
            return
        self.log("[OK] Select : {0} target(s)".format(len(picked)))

    def _tedit_refresh(self):
        """편집 결과가 바로 보이도록 Targets 목록을 다시 채운다."""
        if self.tsl_tedit_cons.count():
            self.on_tedit_list()

    def on_replace_target(self):
        cons = self._tedit_constraints(warn=True)
        picked = self._tedit_picked_targets(warn=True)
        new_targets = self.tsl_tedit_new.get_all_items()
        maintain_offset = self.cb_tedit_keep.isChecked()
        rename_weight = self.cb_tedit_rename.isChecked()

        def _do():
            results, warns = ctgt_mgr.replace_targets(
                cons, picked, new_targets, maintain_offset, rename_weight)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            for r in results:
                self.log("       {0} : {1} -> {2}{3}".format(
                    r["constraint"], r["old"], r["new"],
                    "  ({0})".format(r["note"]) if r["note"] else ""))
            self.log("       {0} target slot(s) replaced".format(len(results)))

        self._run("Replace Target", _do)
        self._tedit_refresh()

    def on_add_target(self):
        cons = self._tedit_constraints(warn=True)
        new_targets = self.tsl_tedit_new.get_all_items()
        maintain_offset = self.cb_tedit_keep.isChecked()
        weight = self.sb_tedit_weight.value()

        def _do():
            results, warns = ctgt_mgr.add_targets(
                cons, new_targets, maintain_offset, weight)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            for r in results:
                self.log("       {0} : + {1}{2}".format(
                    r["constraint"], r["target"],
                    "  ({0})".format(r["note"]) if r["note"] else ""))
            self.log("       {0} target(s) added".format(len(results)))

        self._run("Add Target", _do)
        self._tedit_refresh()

    def on_remove_target(self):
        cons = self._tedit_constraints(warn=True)
        picked = self._tedit_picked_targets(warn=True)
        maintain_offset = self.cb_tedit_keep.isChecked()
        delete_empty = self.cb_tedit_delete_empty.isChecked()

        def _do():
            results, warns = ctgt_mgr.remove_targets(
                cons, picked, maintain_offset, delete_empty)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            removed = 0
            for r in results:
                removed += len(r["removed"])
                self.log("       {0} : - {1}{2}".format(
                    r["constraint"], ", ".join(r["removed"]),
                    "  ({0})".format(r["note"]) if r["note"] else ""))
            deleted = len([r for r in results if r["deleted"]])
            self.log("       {0} target(s) removed from {1} constraint(s)"
                     "{2}".format(removed, len(results),
                                  ", {0} constraint(s) deleted".format(deleted)
                                  if deleted else ""))

        self._run("Remove Target", _do)
        self._tedit_refresh()

    # ==============================================================
    # Handlers : Update Offset
    # ==============================================================

    def _cupd_constraints(self, warn=False):
        """작업 대상 constraint 이름들 — 고른 항목, 없으면 리스트 전체.

        Target Edit 과 같은 규칙이다(고른 게 있으면 그것만).
        """
        picked = self.tsl_cupd_cons.selected_items()
        if picked:
            if warn:
                self.log("[INFO] using {0} picked constraint(s) of {1}".format(
                    len(picked), self.tsl_cupd_cons.count()))
            return picked
        return self.tsl_cupd_cons.get_all_items()

    def on_update_constraint_offset(self):
        cons = self._cupd_constraints(warn=True)

        def _do():
            results, warns = cupd_mgr.update_offsets(cons)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            updated = 0
            for r in results:
                if r["changed"]:
                    updated += 1
                self.log("       {0} ({1}) : {2}  <- {3}{4}".format(
                    r["constraint"], r["type"],
                    "updated" if r["changed"] else "no change",
                    ", ".join(r["targets"]),
                    "  ({0})".format(r["note"]) if r["note"] else ""))
            self.log("       {0} of {1} constraint(s) re-baked".format(
                updated, len(results)))

        self._run("Update Offset", _do)

    def on_list_attrs(self, role):
        w = self._connect_widgets[role]
        objs = w["tsl"].get_all_items()
        if not objs:
            self.log("[ERR] List Attributes : object list is empty")
            return
        try:
            cb_only = w["channel_box"].isChecked()
            attrs = cnt_mgr.list_attrs(objs[0], channel_box_only=cb_only)
        except Exception as e:
            self.log("[ERR] List Attributes : {0}".format(e))
            cmds.warning(str(e))
            return
        w["attrs"].clear()
        w["attrs"].addItems(attrs)
        # 새로 채운 항목에도 현재 필터를 다시 먹인다(필터가 유지되도록).
        shown, total = w["filter"].refresh()

        msg = "[OK] List Attributes : {0} ({1} attrs{2})".format(
            objs[0], total, ", channel box only" if cb_only else "")
        if shown != total:
            msg += " - filter '{0}' shows {1}".format(w["filter"].text().strip(), shown)
        self.log(msg)

    # ==============================================================
    # Handlers : Attribute
    # ==============================================================

    def _acr_items(self):
        return [self.lw_acr_attrs.item(i)
                for i in range(self.lw_acr_attrs.count())]

    def _acr_specs(self):
        """현재 프로파일의 스펙 리스트(리스트 위젯이 아니라 데이터가 원본)."""
        return self._acr_data.get("attributes", [])

    def _acr_save(self):
        aprefs.save_profile(self._acr_profile, self._acr_data)

    def _acr_render_attrs(self, keep_checked=True):
        """프로파일 데이터를 리스트 위젯에 그린다.

        keep_checked=True (같은 프로파일 안에서 Add/Edit/Remove 한 뒤)면 체크 상태를
        **이름 기준**으로 이어받는다 — Edit 로 정의만 바꿨는데 체크가 풀리면 Create 를
        다시 눌러야 하는 걸 잊기 쉽다.

        keep_checked=False (프로파일을 새로 불러올 때)면 **전부 체크**된 상태로 시작한다.
        프로파일은 사용자가 직접 골라 담은 묶음이라 "이 프로파일을 만든다" 가 기본
        의도이고, 매번 전체 체크를 다시 누르게 하는 것은 군더더기다.
        """
        carry = set()
        if keep_checked:
            carry = {it.data(Qt.UserRole) for it in self._acr_items()
                     if it.checkState() == Qt.Checked}

        self._acr_updating = True
        try:
            self.lw_acr_attrs.clear()
            for spec in self._acr_specs():
                item = QListWidgetItem("{0}      {1}".format(
                    spec["name"], aprefs.describe_spec(spec)))
                item.setData(Qt.UserRole, spec["name"])
                on = (spec["name"] in carry) if keep_checked else True
                item.setCheckState(Qt.Checked if on else Qt.Unchecked)
                self.lw_acr_attrs.addItem(item)
        finally:
            self._acr_updating = False

        # 목록을 새로 채웠으니 필터를 다시 먹인다(숨김 상태가 초기화돼 있다).
        self.flt_acr.refresh()
        self._acr_refresh_counts()

    def _acr_refresh_counts(self):
        checked = [it for it in self._acr_items()
                   if it.checkState() == Qt.Checked]
        hidden = sum(1 for it in checked if it.isHidden())
        text = "Checked: {0}".format(len(checked))
        if hidden:
            text += " ({0} hidden)".format(hidden)
        self.lbl_acr_checked.setText(text)

        # 전체 체크박스는 **보이는 행** 기준(동작 범위와 같게).
        visible = [it for it in self._acr_items() if not it.isHidden()]
        visible_checked = [it for it in visible if it.checkState() == Qt.Checked]
        if not visible or not visible_checked:
            state = Qt.Unchecked
        elif len(visible_checked) == len(visible):
            state = Qt.Checked
        else:
            state = Qt.PartiallyChecked
        self.chk_acr_all.blockSignals(True)
        self.chk_acr_all.setCheckState(state)
        self.chk_acr_all.blockSignals(False)

    def _acr_on_item_changed(self, _item):
        if getattr(self, "_acr_updating", False):
            return
        self._acr_refresh_counts()

    def on_acr_check_all(self, _checked=False):
        """전체 체크박스: 지금 보이는 행을 모두 켜거나 끈다.

        판단 기준은 **체크박스의 상태가 아니라 리스트의 상태**다. 3-state 체크박스는
        클릭할 때마다 부분 체크까지 순환하는데, 그 순환에 기대면 "부분 상태에서 누르면
        전부 켠다" 는 의도가 위젯 내부 동작에 딸려 다닌다(코드로 부르면 다르게 동작하고,
        그래서 테스트도 못 한다). 보이는 행이 **전부 켜져 있으면 끄고, 아니면 전부 켠다** —
        결과는 사용자가 기대하는 것과 같으면서 상태가 어디서 오든 똑같이 동작한다.
        """
        visible = [it for it in self._acr_items() if not it.isHidden()]
        turn_on = not (visible and
                       all(it.checkState() == Qt.Checked for it in visible))
        state = Qt.Checked if turn_on else Qt.Unchecked
        self._acr_updating = True
        try:
            for item in self._acr_items():
                if not item.isHidden():
                    item.setCheckState(state)
        finally:
            self._acr_updating = False
        self._acr_refresh_counts()

    def _acr_selected_names(self):
        """보이면서 선택된 행의 어트리뷰트 이름(표시 텍스트가 아니라 UserRole)."""
        names = []
        for item in self.lw_acr_attrs.selectedItems():
            if not item.isHidden():
                names.append(item.data(Qt.UserRole))
        return names

    # --- 프로파일

    def _acr_refresh_profiles(self):
        self.cmb_acr_profile.blockSignals(True)
        self.cmb_acr_profile.clear()
        self.cmb_acr_profile.addItems(aprefs.list_profiles())
        index = self.cmb_acr_profile.findText(self._acr_profile)
        if index >= 0:
            self.cmb_acr_profile.setCurrentIndex(index)
        self.cmb_acr_profile.blockSignals(False)

    def on_acr_profile_changed(self, name):
        if not name or name == self._acr_profile:
            return
        self._acr_profile = name
        aprefs.set_active(name)
        self._acr_data = aprefs.load_profile(name)
        # 프로파일이 바뀌면 어트리뷰트도 통째로 바뀌므로 체크를 이어받지 않는다.
        self._acr_render_attrs(keep_checked=False)
        self.log("[OK] Attribute profile : switched to '{0}' ({1} attr(s))".format(
            name, len(self._acr_specs())))

    def on_acr_new_profile(self):
        raw, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if not ok:
            return
        name = aprefs.sanitize_name(raw)
        if not name:
            return
        if name in aprefs.list_profiles():
            QMessageBox.warning(
                self, "Attribute", "Profile '{0}' already exists.".format(name))
            return

        aprefs.save_profile(name, {"attributes": []})
        aprefs.set_active(name)
        self._acr_profile = name
        self._acr_data = aprefs.load_profile(name)
        self._acr_refresh_profiles()
        self._acr_render_attrs(keep_checked=False)
        self.log("[OK] Attribute profile : created '{0}'".format(name))

    def on_acr_rename_profile(self):
        old = self._acr_profile
        raw, ok = QInputDialog.getText(
            self, "Rename Profile", "New name:", text=old)
        if not ok:
            return
        new = aprefs.sanitize_name(raw)
        if not new or new == old:
            return
        if new in aprefs.list_profiles():
            QMessageBox.warning(
                self, "Attribute", "Profile '{0}' already exists.".format(new))
            return

        aprefs.rename_profile(old, new)
        self._acr_profile = new
        self._acr_refresh_profiles()
        self.log("[OK] Attribute profile : renamed '{0}' -> '{1}'".format(old, new))

    def on_acr_delete_profile(self):
        name = self._acr_profile
        if len(aprefs.list_profiles()) <= 1:
            QMessageBox.information(
                self, "Attribute", "At least one profile must remain.")
            return
        if QMessageBox.question(
                self, "Attribute",
                "Delete profile '{0}' and its {1} attribute(s)?".format(
                    name, len(self._acr_specs()))) != QMessageBox.Yes:
            return

        aprefs.delete_profile(name)
        remaining = aprefs.list_profiles()
        self._acr_profile = remaining[0]
        aprefs.set_active(self._acr_profile)
        self._acr_data = aprefs.load_profile(self._acr_profile)
        self._acr_refresh_profiles()
        self._acr_render_attrs(keep_checked=False)
        self.log("[OK] Attribute profile : deleted '{0}'".format(name))

    # --- 어트리뷰트 정의 편집

    def on_acr_add_attr(self):
        dialog = AttrSpecDialog(self, title="New Attribute")
        if dialog.exec_() != QDialog.Accepted:
            return
        spec = dialog.spec()

        if any(s["name"] == spec["name"] for s in self._acr_specs()):
            QMessageBox.warning(
                self, "Attribute",
                "'{0}' is already in this profile.".format(spec["name"]))
            return

        self._acr_specs().append(spec)
        self._acr_save()
        self._acr_render_attrs()
        # 방금 적은 것은 만들 생각으로 적은 것이다 — 체크해 둔다(carry 에는 없다).
        self._acr_set_checked(spec["name"], True)
        self.log("[OK] Attribute profile : added '{0}' ({1})".format(
            spec["name"], aprefs.describe_spec(spec)))

    def _acr_set_checked(self, name, checked):
        for item in self._acr_items():
            if item.data(Qt.UserRole) == name:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
                break

    def on_acr_edit_attr(self):
        names = self._acr_selected_names()
        if not names:
            self.log("[ERR] Edit Attribute : select one attribute in the list")
            return
        if len(names) > 1:
            self.log("[INFO] Edit Attribute : editing the first of {0} selected "
                     "({1})".format(len(names), names[0]))

        specs = self._acr_specs()
        index = next((i for i, s in enumerate(specs) if s["name"] == names[0]), -1)
        if index < 0:
            return

        old_name = specs[index]["name"]
        dialog = AttrSpecDialog(self, spec=specs[index], title="Edit Attribute")
        if dialog.exec_() != QDialog.Accepted:
            return
        spec = dialog.spec()

        if spec["name"] != old_name and any(
                s["name"] == spec["name"] for s in specs):
            QMessageBox.warning(
                self, "Attribute",
                "'{0}' is already in this profile.".format(spec["name"]))
            return

        specs[index] = spec
        self._acr_save()
        # 이름이 바뀌었으면 체크 상태를 그 이름으로 옮겨 준다(이름 기준으로 잇기 때문).
        if spec["name"] != old_name:
            for item in self._acr_items():
                if item.data(Qt.UserRole) == old_name:
                    item.setData(Qt.UserRole, spec["name"])
        self._acr_render_attrs()
        self.log("[OK] Attribute profile : edited '{0}' -> '{1}' ({2})".format(
            old_name, spec["name"], aprefs.describe_spec(spec)))

    def on_acr_remove_attr(self):
        names = self._acr_selected_names()
        if not names:
            self.log("[ERR] Remove Attribute : select attributes in the list")
            return
        if QMessageBox.question(
                self, "Attribute",
                "Remove {0} attribute(s) from profile '{1}'?\n\n{2}".format(
                    len(names), self._acr_profile,
                    ", ".join(names[:8]))) != QMessageBox.Yes:
            return

        drop = set(names)
        self._acr_data["attributes"] = [
            s for s in self._acr_specs() if s["name"] not in drop]
        self._acr_save()
        self._acr_render_attrs()
        self.log("[OK] Attribute profile : removed {0} attribute(s) - {1}".format(
            len(names), ", ".join(names[:8])))

    # --- 생성

    def _acr_checked_specs(self):
        """체크된 스펙들 + 필터에 가려진 체크 수.

        가려진 것도 **체크돼 있으면 만든다** — 체크는 명시적인 의사표시라 필터에
        가렸다고 없던 일로 하면 오히려 놀랍다. 대신 몇 개가 가려져 있었는지 알린다.
        """
        by_name = {s["name"]: s for s in self._acr_specs()}
        specs, hidden = [], 0
        for item in self._acr_items():
            if item.checkState() != Qt.Checked:
                continue
            spec = by_name.get(item.data(Qt.UserRole))
            if spec is None:
                continue
            specs.append(spec)
            if item.isHidden():
                hidden += 1
        return specs, hidden

    def on_acr_create(self):
        objects = self.tsl_acr_objs.get_all_items()
        specs, hidden = self._acr_checked_specs()
        if hidden:
            self.log("[INFO] {0} checked attribute(s) are hidden by the filter - "
                     "they are created too".format(hidden))

        def _do():
            created, skipped = acreate_mgr.create_attributes(objects, specs)
            for obj, name, reason in skipped:
                self.log("[WARN] {0}.{1} : {2}".format(obj, name, reason))
            self.log("       {0} attribute(s) created on {1} object(s) "
                     "from profile '{2}'".format(
                         len(created), len(objects), self._acr_profile))

        self._run("Create Attributes", _do)

    # ==============================================================
    # Handlers : Attribute > Delete
    # ==============================================================

    def _filtered_attrs(self, role, label):
        """Connect 탭 한쪽의 **보이면서 선택된** 어트리뷰트.

        Qt 는 숨긴 항목의 선택을 유지하므로, 필터에 가려진 항목까지 연결해 버리지
        않도록 여기서 걸러 낸다. 가려진 선택이 있으면 조용히 넘기지 않고 알린다.
        """
        names, hidden = self._connect_widgets[role]["filter"].visible_selected()
        if hidden:
            self.log("[INFO] {0} : {1} selected attribute(s) hidden by the filter "
                     "were skipped".format(label, hidden))
        return names

    def on_match_from_source(self):
        """이름이 **가장 비슷한** destination 어트리뷰트를 찾는다."""
        self._match_destination(exact=False)

    def on_match_same_name(self):
        """이름이 **완전히 같은** destination 어트리뷰트만 찾는다."""
        self._match_destination(exact=True)

    def _match_destination(self, exact):
        """소스 어트리뷰트에 대응하는 destination 어트리뷰트를 찾아 목록을 다시 짠다.

        찾은 것들을 **소스 순서 그대로** destination 목록에 놓고 선택한다.
        `connect_attrs` 가 `src[i] <-> dst[i]` 를 순서로 짝짓기 때문에, 이 상태에서 바로
        'Source -> Destination' 을 누르면 그대로 연결된다.

        `Show Match Only` 가 켜져 있으면(기본) 목록을 **소스와 1:1 로 맞춘 자리만** 남기고,
        짝이 없는 자리는 `(Null)` 로 채운다. 자리를 비우지 않는 게 핵심이다 — 순서로 짝짓는
        연결에서 한 자리만 빠져도 그 뒤가 통째로 밀려 **엉뚱한 짝이 이어지기** 때문이다.
        연결할 때 그 짝은 양쪽에서 함께 빠진다(`attr_match.strip_null_pairs`).

        Args:
            exact: True 면 이름이 완전히 같은 것만(`match_exact_names`),
                False 면 이름이 가장 비슷한 것(`match_attributes`).
        """
        label = "Match Same Name" if exact else "Match from Source"

        src = self._connect_widgets["src"]
        dst = self._connect_widgets["dst"]

        # 소스: 고른 게 있으면 그것, 없으면 지금 보이는 전체.
        sources, hidden = src["filter"].visible_selected()
        if hidden:
            self.log("[INFO] {0} : {1} selected source attribute(s) hidden by the "
                     "filter were skipped".format(label, hidden))
        if not sources:
            sources = src["filter"].visible_texts()
            if sources:
                self.log("[INFO] {0} : nothing selected in Source - using all "
                         "{1} visible attribute(s)".format(label, len(sources)))

        if not sources:
            self.log("[ERR] {0} : source attribute list is empty. Press "
                     "'List Attributes' on the Source side first.".format(label))
            return

        dst_list = dst["attrs"]

        # 지난 매칭이 남긴 (Null) 자리는 후보가 아니다 — 실제 어트리뷰트가 아니다.
        candidates = [dst_list.item(i).text() for i in range(dst_list.count())
                      if dst_list.item(i).text() != attr_match.NULL_TARGET]
        if not candidates:
            self.log("[ERR] {0} : destination attribute list is empty. Press "
                     "'List Attributes' on the Destination side first.".format(label))
            return

        unique = self.cb_match_unique.isChecked()
        min_score = self.sb_match_min.value()

        try:
            if exact:
                matches, unmatched = attr_match.match_exact_names(
                    sources, candidates, unique=unique)
            else:
                matches, unmatched = attr_match.match_attributes(
                    sources, candidates, unique=unique, min_score=min_score)
        except Exception as e:
            self.log("[ERR] {0} : {1}".format(label, e))
            cmds.warning(str(e))
            return

        match_only = self.cb_match_only.isChecked()

        if match_only:
            # 소스와 자리를 맞춘 목록. 짝이 없는 자리는 (Null) 로 채운다.
            ordered = attr_match.aligned_names(sources, matches)
            selected = len(ordered)
        else:
            # 예전 동작: 매칭된 것을 소스 순서대로 앞에, 나머지는 원래 순서로 뒤에.
            matched_rows = [m["index"] for m in matches]
            taken = set(matched_rows)
            ordered = ([candidates[i] for i in matched_rows]
                       + [c for i, c in enumerate(candidates) if i not in taken])
            selected = len(matches)

        # 선택이 필터에 가려지면 연결 대상에서 빠지므로 필터를 비운다.
        if dst["filter"].text().strip():
            self.log("[INFO] {0} : destination filter cleared so the matched "
                     "attributes are all visible.".format(label))
            dst["filter"].clear()

        dst_list.clear()
        dst_list.addItems(ordered)
        dst["filter"].refresh()

        dst_list.clearSelection()
        for row in range(selected):
            dst_list.item(row).setSelected(True)
        self._mark_null_rows(dst_list)
        if ordered:
            dst_list.scrollToItem(dst_list.item(0))

        self._log_match_result(label, exact, sources, candidates,
                               matches, unmatched, unique, min_score, match_only)

    def _mark_null_rows(self, list_widget):
        """`(Null)` 자리를 **빨갛게** 칠한다 - 실제 어트리뷰트가 아니라는 신호.

        이 리스트는 TSL 을 거치지 않고 `addItems` 로 직접 채우므로(위 `_match_destination`),
        공용 TSL 이 자동으로 칠해 주는 경로를 타지 않는다. 그래서 같은 규칙을 **공용 함수**로
        직접 부른다 - 색이 툴마다 달라지지 않게(`Framework.qt.MOD_tsl_qt_v01`).
        """
        return JUN_mod_tsl_qt.mark_null_items(
            list_widget,
            texts=(attr_match.NULL_TARGET,),
            tooltip=("The matching source attribute has no counterpart here.\n"
                     "This row only holds the pairing order - it is skipped when "
                     "connecting."))

    def _log_match_result(self, label, exact, sources, candidates,
                          matches, unmatched, unique, min_score, match_only):
        """매칭 결과를 로그로 푼다.

        짝을 못 찾은 것을 조용히 넘기지 않는다 — 무엇이 왜 빠졌는지 이름까지 찍어야
        "왜 일부만 연결됐지?" 가 안 된다.
        """
        head = "[OK] {0} : {1}/{2} matched ({3}".format(
            label, len(matches), len(sources),
            "unique" if unique else "duplicates allowed")
        if not exact:
            head += ", min {0:.2f}".format(min_score)
        self.log(head + ")")

        for m in matches:
            self.log("       {0}  ->  {1}   ({2:.2f}{3})".format(
                m["source"], m["target"], m["score"],
                ", ambiguous" if m["ambiguous"] else ""))

        for u in unmatched:
            if exact and u["best"]:
                # 이름은 있었는데 Unique 때문에 앞 소스가 이미 가져간 경우.
                self.log("[WARN] '{0}' : the destination attribute of the same "
                         "name was already taken by an earlier source (Unique "
                         "is on).".format(u["source"]))
            elif exact:
                self.log("[WARN] no attribute named '{0}' in the destination "
                         "list.".format(u["source"]))
            elif u["best"]:
                self.log("[WARN] no match for '{0}' - closest was '{1}' "
                         "({2:.2f} < {3:.2f})".format(
                             u["source"], u["best"], u["score"], min_score))
            else:
                self.log("[WARN] no match for '{0}' - nothing similar in the "
                         "destination list.".format(u["source"]))

        if not match_only:
            if unmatched:
                self.log("[INFO] {0} : source and destination selections no longer "
                         "line up 1:1 ({1} source attribute(s) unmatched). Turn "
                         "'Show Match Only' on, or deselect those on the Source "
                         "side before connecting.".format(label, len(unmatched)))
            return

        if unmatched:
            self.log("[INFO] {0} : {1} unmatched source attribute(s) hold a '{2}' "
                     "row each so the pairing keeps its order - those pairs are "
                     "skipped when connecting.".format(
                         label, len(unmatched), attr_match.NULL_TARGET))

        # Show Match Only 는 짝이 안 된 destination 어트리뷰트를 목록에서 뺀다.
        # 사라진 게 아니라 다시 나열하면 된다는 걸 알려 준다.
        left_out = len(candidates) - len(set(m["index"] for m in matches))
        if left_out > 0:
            self.log("[INFO] {0} : {1} destination attribute(s) are not shown "
                     "(Show Match Only) - press 'List Attributes' to get the "
                     "full list back.".format(label, left_out))

    def on_connect_attrs(self):
        """Source 어트리뷰트 -> Destination 어트리뷰트."""
        self._connect_in_direction("src", "dst")

    def on_connect_attrs_reverse(self):
        """Destination 어트리뷰트 -> Source 어트리뷰트 (역방향)."""
        self._connect_in_direction("dst", "src")

    def _connect_in_direction(self, from_role, to_role):
        """한쪽 패널을 드라이버로, 다른 쪽을 구동 대상으로 연결한다.

        두 방향의 차이는 `connect_attrs` 에 넘기는 **인자 순서뿐**이다. 브로드캐스트
        패턴(오브젝트 1개 -> 다수 등)도 그대로 뒤집혀 적용된다.

        버튼 두 개를 각각 이 메서드로 감싼 이유: `clicked` 시그널은 `checked`(bool)를
        넘기므로, 방향을 기본 인자로 받는 단일 슬롯에 직접 연결하면 그 bool 이 방향
        인자로 들어갈 수 있다.
        """
        from_label = self.ROLE_LABELS[from_role]
        to_label = self.ROLE_LABELS[to_role]

        from_objs = self._connect_widgets[from_role]["tsl"].get_all_items()
        to_objs = self._connect_widgets[to_role]["tsl"].get_all_items()
        from_attrs = self._filtered_attrs(from_role, from_label)
        to_attrs = self._filtered_attrs(to_role, to_label)

        # 매칭에서 짝을 못 찾아 (Null) 로 남은 자리는 연결하지 않는다. 연결은 순서로
        # 짝짓기 때문에 **양쪽에서 같은 자리를 함께** 빼야 뒤 짝이 안 밀린다.
        from_attrs, to_attrs, dropped = attr_match.strip_null_pairs(
            from_attrs, to_attrs)
        if dropped:
            self.log("[INFO] {0} '{1}' pair(s) had no counterpart and were "
                     "skipped".format(dropped, attr_match.NULL_TARGET))
            if not (from_attrs and to_attrs):
                self.log("[ERR] Connect {0} to {1} : every selected pair was "
                         "'{2}' - nothing to connect.".format(
                             from_label, to_label, attr_match.NULL_TARGET))
                return

        def _do():
            count, mode, report = cnt_mgr.connect_attrs(
                from_objs, to_objs, from_attrs, to_attrs)
            self.log("       {0} connection(s) [{1}]  {2} -> {3}".format(
                count, mode, from_label, to_label))
            self._log_connect_report(report, from_label, to_label)

        self._run("Connect {0} to {1}".format(from_label, to_label), _do)

    def _log_connect_report(self, report, from_label, to_label):
        """개수가 안 맞아 남겨 둔 항목과 실패한 연결을 로그로 알린다.

        조용히 넘기면 "왜 일부만 연결됐지?" 가 되므로, 무엇이 남았는지 이름까지 찍는다.
        """
        for key, label in (("unused_driver_attrs", from_label + " attribute"),
                           ("unused_driven_attrs", to_label + " attribute"),
                           ("unused_driver_objs", from_label + " object"),
                           ("unused_driven_objs", to_label + " object")):
            left = report.get(key) or []
            if not left:
                continue
            shown = ", ".join(left[:8])
            if len(left) > 8:
                shown += ", ... (+{0})".format(len(left) - 8)
            self.log("[INFO] {0} {1}(s) had no counterpart and were left "
                     "untouched: {2}".format(len(left), label, shown))

        for src_plug, dst_plug, reason in (report.get("failed") or []):
            self.log("[WARN] could not connect {0} -> {1} : {2}".format(
                src_plug, dst_plug, reason))

    def on_connect_52_facial(self):
        src = self._connect_widgets["src"]
        dst = self._connect_widgets["dst"]
        src_objs = src["tsl"].get_all_items()
        dst_objs = dst["tsl"].get_all_items()

        def _do():
            connected, skipped = cnt_mgr.connect_52_facial(src_objs, dst_objs)
            self.log("       {0} connected, {1} skipped".format(connected, skipped))

        self._run("Connect 52 Facial Target", _do)

    # ==============================================================
    # Handlers : List Connected
    # ==============================================================

    def on_list_stream(self, upstream):
        objs = self.tsl_stream_objs.get_all_items()
        if not objs:
            self.log("[ERR] List Stream : object list is empty")
            return
        self._stream_upstream = upstream
        try:
            types = stm_mgr.list_stream_types(objs, upstream)
        except Exception as e:
            self.log("[ERR] List Stream : {0}".format(e))
            cmds.warning(str(e))
            return
        self.list_types.clear()
        self.list_types.addItems(types)
        self.list_nodes.clear()
        self.log("[OK] List {0}Stream : {1} type(s)".format(
            "Up" if upstream else "Down", len(types)))

    def on_search_nodes(self):
        objs = self.tsl_stream_objs.get_all_items()
        types = self._selected_texts(self.list_types)
        if not objs:
            self.log("[ERR] Search Nodes : object list is empty")
            return
        if not types:
            self.log("[ERR] Search Nodes : select one or more types")
            return
        try:
            nodes = stm_mgr.nodes_by_types(objs, types, self._stream_upstream)
        except Exception as e:
            self.log("[ERR] Search Nodes : {0}".format(e))
            cmds.warning(str(e))
            return
        self.list_nodes.clear()
        self.list_nodes.addItems(nodes)
        self.log("[OK] Search Nodes : {0} node(s)".format(len(nodes)))

    def on_nodes_selection_changed(self):
        sel = self._selected_texts(self.list_nodes)
        try:
            if sel:
                cmds.select(sel)
            else:
                cmds.select(clear=True)
        except Exception as e:
            cmds.warning(str(e))

    # ==============================================================
    # Handlers : Pair (Get Closest / Match by Name / Connect)
    # ==============================================================

    def on_get_closest(self):
        """각 Driver 의 가장 가까운 오브젝트를 찾아 Driven 을 driver 순서대로 채운다.

        후보 풀은 Driven 리스트에 항목이 있으면 그것을, 없으면 현재 씬 선택을 쓴다.
        결과(찾은 오브젝트)는 뷰포트에서도 선택해 눈으로 확인할 수 있게 한다.
        매칭 로직은 connect_closest 와 동일(greedy 1:1)이라 Connect 결과의 미리보기다.
        """
        drivers = self.cc_driver.get_all_items()
        self.log("--- Get Closest ---")

        if not drivers:
            self.log("[WARN] Driver list is empty. Add objects to the Driver list.")
            return

        pool, note = self._cc_candidate_pool(drivers, "Get Closest")
        if pool is None:
            return
        self.log(note)

        pairs, errors = find_closest_for_drivers(drivers, pool)

        for err in errors:
            self.log("[WARN] {0}".format(err))

        if not pairs:
            self.log("No closest match found.")
            return

        drivens = [driven for _driver, driven, _dist in pairs]
        self.cc_driven.set_items(drivens)

        for driver, driven, dist in pairs:
            self.log("Closest: {0} -> {1} (dist {2:.3f})".format(
                driver, driven, dist))

        # 발견 검증용: 찾은 오브젝트를 뷰포트에서 선택.
        try:
            cmds.select(drivens, replace=True)
        except Exception:
            pass

        self.log("Done. {0} closest object(s) listed in Driven.".format(
            len(pairs)))

    def _cc_candidate_pool(self, drivers, label):
        """Driver 와 짝지을 후보 풀. (pool, 로그 문자열) — 없으면 (None, None).

        Get Closest 와 Match by Name 이 **같은 규칙**을 쓴다: Driven 리스트에 항목이
        있으면 그것을, 없으면 현재 씬 선택을 후보로 본다. driver 자신은 뺀다 —
        거리로는 자기 자신이 언제나 최단이고, 이름으로는 자기 이름이 언제나 만점이다.
        """
        candidates = self.cc_driven.get_all_items()
        source = "Driven list"
        if not candidates:
            candidates = cmds.ls(sl=True, fl=True) or []
            source = "current selection"
        if not candidates:
            self.log("[WARN] No candidates. Fill the Driven list or "
                     "select objects in the scene.")
            return None, None

        driver_set = set(drivers)
        pool = [c for c in candidates if c not in driver_set]
        dropped = len(candidates) - len(pool)

        if not pool:
            self.log("[WARN] {0} : every candidate is also a Driver.".format(label))
            return None, None

        note = "Candidate pool: {0} ({1} object(s))".format(source, len(pool))
        if dropped:
            note += " - {0} driver(s) excluded".format(dropped)
        return pool, note

    def on_match_by_name(self):
        """Driver 이름과 가장 비슷한 오브젝트를 찾아 Driven 을 driver 순서로 세운다.

        Get Closest 의 이름 버전이다 — 거리 대신 이름으로 짝을 찾고, 짝을 못 찾은
        자리는 `(Null)` 이 지킨다(그래야 뒤의 짝이 밀리지 않는다). 세운 순서를 그대로
        연결해야 하므로 Pairing 을 **List order** 로 돌려 놓는다.
        """
        drivers = self.cc_driver.get_all_items()
        self.log("--- Match by Name ---")

        if not drivers:
            self.log("[WARN] Driver list is empty. Add objects to the Driver list.")
            return

        pool, note = self._cc_candidate_pool(drivers, "Match by Name")
        if pool is None:
            return
        self.log(note)

        exact = self.cb_om_exact.isChecked()
        rows = obj_match.match_objects(
            drivers, pool,
            exact=exact,
            unique=self.cb_om_unique.isChecked(),
            min_score=self.sb_om_min.value(),
            ignore_namespace=self.cb_om_namespace.isChecked())

        aligned = obj_match.aligned_targets(rows)
        self.cc_driven.set_items(aligned)

        matched = 0
        for row in rows:
            if row["target"]:
                matched += 1
                self.log("Match: {0} -> {1} ({2:.2f}){3}".format(
                    row["source"], row["target"], row["score"],
                    "  [ambiguous]" if row["ambiguous"] else ""))
            else:
                best = ""
                if row["best"]:
                    best = "  (best: {0} {1:.2f})".format(row["best"], row["score"])
                self.log("Match: {0} -> {1}{2}".format(
                    row["source"], obj_match.NULL_TARGET, best))

        # 세운 순서대로 연결해야 뜻이 있다. 거리로 다시 짝지으면 이 정렬이 무의미해진다.
        self.rb_cc_order.setChecked(True)

        self.log("{0} of {1} driver(s) matched by {2} name. Pairing set to "
                 "'List order'.".format(
                     matched, len(rows), "exact" if exact else "similar"))

        # 발견 검증용: 찾은 오브젝트를 뷰포트에서 선택 ((Null) 은 노드가 아니다).
        found = [row["target"] for row in rows if row["target"]]
        if found:
            try:
                cmds.select(found, replace=True)
            except Exception as e:
                self.log("[WARN] could not select the matches: {0}".format(e))

    def on_pair_swap(self):
        """Driven <-> Driver 목록 교환 (Connect > Pair).

        Match 탭의 `Swap` 과 같은 동작이다. 짝은 **자리**로 서 있으므로
        (`(Null)` 자리까지 포함해) 두 리스트를 통째로 맞바꾸면 짝은 그대로 남고
        constraint 방향만 반대가 된다. Pairing 설정은 건드리지 않는다.
        """
        driven = self.cc_driven.get_all_items()
        driver = self.cc_driver.get_all_items()
        self.cc_driven.set_items(driver)
        self.cc_driver.set_items(driven)
        self.log("[OK] Swap : Driven <-> Driver")

    def on_connect_closest(self):
        drivers = self.cc_driver.get_all_items()
        drivens = self.cc_driven.get_all_items()
        keys = [key for key, cb in self.cc_checkboxes.items() if cb.isChecked()]
        maintain_offset = self.cc_maintain.isChecked()
        order_mode = self.rb_cc_order.isChecked()

        self.log("--- Connect ({0}) ---".format(
            "list order" if order_mode else "closest distance"))

        results, errors = connect_closest(
            drivers, drivens, keys, maintain_offset,
            pairing=PAIRING_ORDER if order_mode else PAIRING_CLOSEST)

        for err in errors:
            self.log("[WARN] {0}".format(err))

        for r in results:
            self.log(
                "Connected: {driver} -> {driven} "
                "(dist {dist:.3f}, {cons})".format(
                    driver=r["driver"],
                    driven=r["driven"],
                    dist=r["distance"],
                    cons=", ".join(r["constraints"]),
                )
            )

        self.log("Done. {0} connection(s) made.".format(len(results)))
