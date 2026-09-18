# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00275_skinTool_V01 - Select > By Weight 탭 UI
"""
Select > By Weight - 체크한 조인트의 웨이트가 기준값 이상 / 이하인 버텍스를 고르는 탭.

main_window.py 가 길어서 Layer 탭처럼 위젯 하나로 따로 둔다. 로직은 전부
`app/core/weight_select_manager.py` 에 있다.

  1) Load Mesh / Vertices - 스킨된 메시(전체) 또는 그 메시의 버텍스 일부(범위)를 **저장**하고,
     바인드된 조인트를 TSL 에 체크박스와 함께 올린다.
  2) 조인트를 체크하고 기준값(0~1)과 >= / <= 를 고른다.
  3) Select Vertices - 저장한 범위 안에서 조건에 맞는 버텍스를 선택한다.

조인트 체크: 여러 행을 골라 둔 상태에서 그중 하나의 체크박스를 누르면 **고른 행 전부**가
같은 상태로 바뀐다(Layer 탭 Lock 과 같은 조작). 고른 행은 그대로 남는다.
QListWidget 기본 처리에 맡기면(오프스크린 QTest 실측) 체크 전파는 되지만 **선택이 누른 행 하나로
풀려서** 다음 클릭부터 한 행씩만 바뀐다 - 그래서 체크박스 위 클릭은 eventFilter 에서 직접 처리한다.
v01.28 에서 이 처리를 Framework 공용 동작 `JUN_mod_checkList_qt` 로 옮겼다(이 탭의 코드가 원본이다).

모든 UI 문자열은 영어. (한국어는 주석/독스트링만)
"""

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_checkList_qt

import maya.cmds as cmds

from tools.A00275_skinTool_V01.app.core import weight_select_manager as ws_mgr


# 조인트 항목에 따로 붙이는 UUID (리네임/리페어런트 후에도 같은 조인트를 찾는다)
JOINT_UUID_ROLE = Qt.UserRole + 101

VALUE_SLIDER_STEPS = 1000

_COMBINE_ITEMS = (
    ("Any checked joint", ws_mgr.COMBINE_ANY,
     "A vertex matches when at least one checked joint passes the test."),
    ("All checked joints", ws_mgr.COMBINE_ALL,
     "A vertex matches when every checked joint passes the test."),
    ("Sum of checked joints", ws_mgr.COMBINE_SUM,
     "The weights of the checked joints are added up, then tested."),
)


def _leaf(name):
    return name.split("|")[-1]


class WeightSelectTab(QWidget):

    def __init__(self, log_callback=None, parent=None):
        super(WeightSelectTab, self).__init__(parent)
        self._log = log_callback or (lambda text: None)
        self.scope = None           # weight_select_manager.load_scope() 결과
        self._build_ui()
        self._update_scope_label()

    # ==============================================================
    # UI
    # ==============================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        desc = QLabel(
            "Select the vertices whose skin weight on the checked joints\n"
            "is at least / at most a value.")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        # --- 범위 ---
        scope_box = QGroupBox("Mesh")
        scope_lay = QVBoxLayout(scope_box)
        row = QHBoxLayout()
        self.btn_load = QPushButton("Load Mesh / Vertices")
        self.btn_load.setToolTip(
            "Select a skinned mesh to search all of its vertices,\n"
            "or select some of its vertices (edges / faces also work)\n"
            "to search only those. The scope is stored - picking the\n"
            "result later does not change it.")
        self.btn_load.clicked.connect(self.on_load)
        row.addWidget(self.btn_load, 2)
        self.btn_select_scope = QPushButton("Select Scope")
        self.btn_select_scope.setToolTip("Select the stored mesh or vertices in Maya.")
        self.btn_select_scope.clicked.connect(self.on_select_scope)
        row.addWidget(self.btn_select_scope, 1)
        scope_lay.addLayout(row)
        self.lbl_scope = QLabel()
        self.lbl_scope.setAlignment(Qt.AlignCenter)
        self.lbl_scope.setWordWrap(True)
        scope_lay.addWidget(self.lbl_scope)
        root.addWidget(scope_box)

        # --- 조인트 ---
        self.tsl_joints = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Bound Joints", show_select=False, show_add=False, show_del=False,
            show_up=False, show_down=False, show_sort=False, show_order=False,
            list_min_height=180, log_callback=self._log)
        self.tsl_joints.add_button("Check All", lambda *_: self._set_all_checked(True))
        self.tsl_joints.add_button("Uncheck All", lambda *_: self._set_all_checked(False))
        # 고른 행 한꺼번에 체크 (기본 처리는 고른 행을 클릭한 행 하나로 풀어버린다).
        self.chk_joints = JUN_mod_checkList_qt.JUN_mod_checkList_qt_v01(
            self.tsl_joints.list_widget)
        root.addWidget(self.tsl_joints, 1)

        # --- 조건 ---
        cond_box = QGroupBox("Condition")
        cond_lay = QVBoxLayout(cond_box)

        mode_row = QHBoxLayout()
        self.rb_at_least = QRadioButton("Weight >= Value")
        self.rb_at_least.setToolTip("Vertices weighted at least the value.")
        self.rb_at_most = QRadioButton("Weight <= Value")
        self.rb_at_most.setToolTip(
            "Vertices weighted at most the value.\n"
            "This includes vertices with no weight at all on the joint (0).")
        self.rb_at_least.setChecked(True)
        mode_row.addWidget(self.rb_at_least)
        mode_row.addWidget(self.rb_at_most)
        cond_lay.addLayout(mode_row)

        value_row = QHBoxLayout()
        value_row.addWidget(QLabel("Value"))
        self.spn_value = QDoubleSpinBox()
        self.spn_value.setRange(0.0, 1.0)
        self.spn_value.setDecimals(3)
        self.spn_value.setSingleStep(0.05)
        self.spn_value.setValue(0.5)
        self.spn_value.setKeyboardTracking(False)
        self.spn_value.setToolTip("A value between 0 and 1. The value itself is included.")
        value_row.addWidget(self.spn_value)
        self.sld_value = QSlider(Qt.Horizontal)
        self.sld_value.setRange(0, VALUE_SLIDER_STEPS)
        self.sld_value.setValue(int(round(0.5 * VALUE_SLIDER_STEPS)))
        value_row.addWidget(self.sld_value, 1)
        self.spn_value.valueChanged.connect(self._on_spin_changed)
        self.sld_value.valueChanged.connect(self._on_slider_changed)
        cond_lay.addLayout(value_row)

        combine_row = QHBoxLayout()
        combine_row.addWidget(QLabel("Several joints"))
        self.cmb_combine = QComboBox()
        for index, (label, key, tip) in enumerate(_COMBINE_ITEMS):
            self.cmb_combine.addItem(label, key)
            self.cmb_combine.setItemData(index, tip, Qt.ToolTipRole)
        self.cmb_combine.setToolTip("How the checked joints are tested together.")
        combine_row.addWidget(self.cmb_combine, 1)
        cond_lay.addLayout(combine_row)
        root.addWidget(cond_box)

        self.btn_run = QPushButton("Select Vertices")
        self.btn_run.setMinimumHeight(30)
        self.btn_run.setToolTip(
            "Select the vertices in the stored scope that match the condition.")
        self.btn_run.clicked.connect(self.on_select_vertices)
        root.addWidget(self.btn_run)

    # ==============================================================
    # 값 위젯 동기화
    # ==============================================================

    def _on_spin_changed(self, value):
        self.sld_value.blockSignals(True)
        self.sld_value.setValue(int(round(value * VALUE_SLIDER_STEPS)))
        self.sld_value.blockSignals(False)

    def _on_slider_changed(self, step):
        self.spn_value.blockSignals(True)
        self.spn_value.setValue(step / float(VALUE_SLIDER_STEPS))
        self.spn_value.blockSignals(False)

    # ==============================================================
    # 조인트 리스트
    # ==============================================================

    def _items(self):
        lw = self.tsl_joints.list_widget
        return [lw.item(i) for i in range(lw.count())]

    def _joint_of(self, item):
        uuid = item.data(JOINT_UUID_ROLE)
        found = cmds.ls(uuid, long=True) if uuid else []
        return found[0] if found else None

    def _fill_joints(self, paths, keep_checked=()):
        """조인트 경로를 리스트에 올리고 체크박스를 단다. keep_checked 에 있던 조인트는 체크."""
        names = [(cmds.ls(p) or [_leaf(p)])[0] for p in paths]   # 짧고 유일한 이름
        self.tsl_joints.set_items(names)
        lw = self.tsl_joints.list_widget
        lw.blockSignals(True)
        for item, path in zip(self._items(), paths):
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            uuid = (cmds.ls(path, uuid=True) or [None])[0]
            item.setData(JOINT_UUID_ROLE, uuid)
            item.setCheckState(Qt.Checked if uuid in keep_checked else Qt.Unchecked)
        lw.blockSignals(False)

    def checked_joints(self):
        """체크된 조인트의 현재 롱네임. 씬에서 사라진 것은 빠진다."""
        out = []
        for item in self._items():
            if item.checkState() == Qt.Checked:
                path = self._joint_of(item)
                if path:
                    out.append(path)
        return out

    def _set_all_checked(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        lw = self.tsl_joints.list_widget
        lw.blockSignals(True)
        for item in self._items():
            item.setCheckState(state)
        lw.blockSignals(False)

    # ==============================================================
    # 범위
    # ==============================================================

    def _update_scope_label(self):
        scope = self.scope
        if not scope:
            self.lbl_scope.setText("Nothing loaded.")
            self.btn_select_scope.setEnabled(False)
            return
        self.btn_select_scope.setEnabled(True)
        if scope["vertices"] is None:
            where = "all {0} vertices".format(scope["total"])
        else:
            where = "{0} of {1} vertices".format(len(scope["vertices"]), scope["total"])
        self.lbl_scope.setText("{0}  -  {1}  ({2})".format(
            _leaf(scope["mesh"]), where, scope["skin"]))

    def on_load(self, *_):
        try:
            scope = ws_mgr.load_scope()
        except Exception as e:                              # noqa: BLE001
            self._log("[Warning] By Weight : {0}".format(e))
            return

        # 같은 메시를 다시 불러오면 체크해 둔 조인트를 유지한다.
        keep = set()
        if self.scope and self.scope["mesh"] == scope["mesh"]:
            keep = {item.data(JOINT_UUID_ROLE) for item in self._items()
                    if item.checkState() == Qt.Checked}

        self.scope = scope
        self._fill_joints(scope["influences"], keep_checked=keep)
        self._update_scope_label()
        self._log("By Weight : loaded {0} - {1} joint(s).".format(
            self.lbl_scope.text(), len(scope["influences"])))

    def on_select_scope(self, *_):
        scope = self.scope
        if not scope:
            return
        if not cmds.objExists(scope["mesh"]):
            self._log("[Warning] By Weight : the loaded mesh no longer exists.")
            return
        if scope["vertices"] is None:
            cmds.select(scope["mesh"], replace=True)
        else:
            ws_mgr.select_vertices(scope["mesh"], scope["vertices"])

    # ==============================================================
    # 실행
    # ==============================================================

    def current_mode(self):
        return ws_mgr.MODE_AT_LEAST if self.rb_at_least.isChecked() else ws_mgr.MODE_AT_MOST

    def on_select_vertices(self, *_):
        scope = self.scope
        if not scope:
            self._log("[Warning] By Weight : load a skinned mesh (or some of its "
                      "vertices) first.")
            return
        joints = self.checked_joints()
        if not joints:
            self._log("[Warning] By Weight : check at least one joint.")
            return

        mode = self.current_mode()
        value = self.spn_value.value()
        combine = self.cmb_combine.currentData()
        try:
            ids = ws_mgr.find_vertices(scope["mesh"], joints, value, mode, combine,
                                       vertices=scope["vertices"])
        except Exception as e:                              # noqa: BLE001
            self._log("[Warning] By Weight : {0}".format(e))
            return

        searched = scope["total"] if scope["vertices"] is None else len(scope["vertices"])
        names = (", ".join(_leaf(j) for j in joints) if len(joints) <= 3
                 else "{0} joints".format(len(joints)))
        if len(joints) > 1:
            names += " ({0})".format(self.cmb_combine.currentText())
        condition = "{0} {1} {2:.3f}".format(
            names, ">=" if mode == ws_mgr.MODE_AT_LEAST else "<=", value)
        if not ids:
            self._log("[Warning] By Weight : no vertex matched {0} (searched {1}). "
                      "The selection was not changed.".format(condition, searched))
            return
        ws_mgr.select_vertices(scope["mesh"], ids)
        self._log("By Weight : selected {0} of {1} vertices - {2}.".format(
            len(ids), searched, condition))
