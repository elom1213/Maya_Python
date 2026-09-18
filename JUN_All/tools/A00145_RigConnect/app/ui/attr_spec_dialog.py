# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00145_RigConnect - Attribute > Create 탭의 어트리뷰트 정의 편집 다이얼로그
#
# 프로파일에 담을 어트리뷰트 하나를 적거나 고치는 작은 창이다. A00340_SelectionTool 의
# 프로파일 UI 에는 "항목의 속성을 편집" 하는 창이 없어(거긴 오브젝트 이름 목록만 담는다)
# 이것만 새로 만들었다.
#
#   Name     [ World          ]
#   Type     [ float  v ]   [x] Keyable
#   Min      [x] [ 0.000 ]        <- 체크를 끄면 "제한 없음"
#   Max      [x] [ 1.000 ]
#   Default      [ 0.000 ]
#
# Min/Max 를 **체크박스로 켜고 끄는** 이유: 마야에서 "범위 없음" 과 "범위 0" 은 다른데,
# 스핀박스만 두면 그 둘을 구분해 넣을 방법이 없다.
#
# v01.48 : enum / string 타입 추가. 타입에 따라 보이는 칸이 바뀐다.
#   enum   : Items [ left, mid, right ]  +  Default [ mid v ]  (항목 번호가 아니라 이름에서 고른다)
#   string : Default [ text ]            +  Keyable 칸이 "Channel Box" 로 바뀐다
#            (string 은 키를 못 걸어서, 체크의 뜻을 "채널박스에 보이게" 로 읽는다)

from Framework.qt.qt import *

from tools.A00145_RigConnect.app.core import attr_profile_prefs as prefs


class AttrSpecDialog(QDialog):
    """어트리뷰트 정의 1개를 편집한다. `spec()` 으로 정규화된 dict 를 얻는다."""

    def __init__(self, parent=None, spec=None, title="New Attribute"):
        super(AttrSpecDialog, self).__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(320)

        spec = spec or {"name": "", "type": "float", "min": 0.0, "max": 1.0,
                        "default": 0.0, "keyable": True}

        layout = QVBoxLayout(self)
        form = QGridLayout()
        layout.addLayout(form)

        # --- 이름
        form.addWidget(QLabel("Name"), 0, 0)
        self.le_name = QLineEdit(spec.get("name", ""))
        self.le_name.setPlaceholderText("e.g. World")
        self.le_name.setToolTip(
            "Attribute long name. Letters, digits and underscore only,\n"
            "starting with a letter or underscore.")
        form.addWidget(self.le_name, 0, 1, 1, 2)

        # --- 타입 + keyable
        form.addWidget(QLabel("Type"), 1, 0)
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(list(prefs.ATTR_TYPES))
        index = self.cmb_type.findText(spec.get("type", "float"))
        self.cmb_type.setCurrentIndex(index if index >= 0 else 0)
        self.cmb_type.setToolTip(
            "float : double  -  int : long  -  bool : on / off\n"
            "enum : named choices  -  string : text")
        self.cmb_type.currentTextChanged.connect(self._sync_type)
        form.addWidget(self.cmb_type, 1, 1)

        self.chk_keyable = QCheckBox("Keyable")
        self.chk_keyable.setChecked(bool(spec.get("keyable", True)))
        self.chk_keyable.setToolTip(
            "On  : shows in the channel box and can be keyed.\n"
            "Off : created hidden from the channel box.")
        form.addWidget(self.chk_keyable, 1, 2)

        # --- Min / Max (체크를 끄면 제한 없음)
        self.chk_min = QCheckBox("Min")
        self.chk_min.setChecked(spec.get("min") is not None)
        self.chk_min.setToolTip("Off : no lower limit.")
        self.chk_min.toggled.connect(self._sync_range)
        form.addWidget(self.chk_min, 2, 0)
        self.sp_min = self._spin(spec.get("min"), 0.0)
        form.addWidget(self.sp_min, 2, 1, 1, 2)

        self.chk_max = QCheckBox("Max")
        self.chk_max.setChecked(spec.get("max") is not None)
        self.chk_max.setToolTip("Off : no upper limit.")
        self.chk_max.toggled.connect(self._sync_range)
        form.addWidget(self.chk_max, 3, 0)
        self.sp_max = self._spin(spec.get("max"), 1.0)
        form.addWidget(self.sp_max, 3, 1, 1, 2)

        # --- 기본값
        form.addWidget(QLabel("Default"), 4, 0)
        self.sp_default = self._spin(spec.get("default"), 0.0)
        form.addWidget(self.sp_default, 4, 1, 1, 2)

        self.chk_default_bool = QCheckBox("On")
        self.chk_default_bool.setChecked(bool(spec.get("default")))
        self.chk_default_bool.setToolTip("Default value for a bool attribute.")
        form.addWidget(self.chk_default_bool, 4, 1, 1, 2)

        # --- enum : 항목 + 기본 항목
        self.lbl_items = QLabel("Items")
        form.addWidget(self.lbl_items, 5, 0)
        self.le_items = QLineEdit(", ".join(spec.get("enum") or []))
        self.le_items.setPlaceholderText("e.g. left, mid, right")
        self.le_items.setToolTip(
            "Enum items in order, separated by ',' or ':'.\n"
            "Empty items are dropped.")
        self.le_items.textChanged.connect(self._sync_enum_items)
        form.addWidget(self.le_items, 5, 1, 1, 2)

        self.cmb_default_enum = QComboBox()
        self.cmb_default_enum.setToolTip("Default item of the enum attribute.")
        form.addWidget(self.cmb_default_enum, 4, 1, 1, 2)

        # --- string : 기본 글자
        self.le_default_str = QLineEdit(
            spec.get("default") if isinstance(spec.get("default"), str) else "")
        self.le_default_str.setPlaceholderText("(empty)")
        self.le_default_str.setToolTip("Default text of the string attribute.")
        form.addWidget(self.le_default_str, 4, 1, 1, 2)

        # 편집으로 열었으면 기본 항목을 그 번호로 맞춘다.
        self._sync_enum_items()
        if spec.get("type") == "enum":
            self.cmb_default_enum.setCurrentIndex(
                max(0, min(self.cmb_default_enum.count() - 1,
                           int(spec.get("default") or 0))))

        # 범위 밖 기본값은 addAttr 이 조용히 무시하므로(경고만 낸다), 여기서 알려 준다.
        self.lbl_hint = QLabel("")
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setStyleSheet("color: #e0a030;")
        layout.addWidget(self.lbl_hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        for widget in (self.sp_min, self.sp_max, self.sp_default):
            widget.valueChanged.connect(self._sync_hint)
        self.chk_min.toggled.connect(self._sync_hint)
        self.chk_max.toggled.connect(self._sync_hint)

        self._sync_type(self.cmb_type.currentText())
        self.le_name.setFocus()

    # ------------------------------------------------------------------

    @staticmethod
    def _spin(value, fallback):
        spin = QDoubleSpinBox()
        spin.setDecimals(3)
        spin.setRange(-1e6, 1e6)
        # 값을 되쓰는 스핀박스라 타이핑 중 값이 잘리지 않도록 tracking 을 끈다.
        spin.setKeyboardTracking(False)
        # string 스펙의 default 는 글자라 숫자가 아니면 fallback 을 쓴다.
        try:
            spin.setValue(fallback if value is None else float(value))
        except (TypeError, ValueError):
            spin.setValue(fallback)
        return spin

    def _sync_type(self, type_name):
        """타입에 따라 범위/기본값 위젯을 바꾼다."""
        is_bool = (type_name == "bool")
        is_int = (type_name == "int")
        is_enum = (type_name == "enum")
        is_string = (type_name == "string")
        is_ranged = type_name in prefs.RANGED_TYPES

        for widget in (self.chk_min, self.chk_max, self.sp_min, self.sp_max):
            widget.setVisible(is_ranged)
        self.sp_default.setVisible(is_ranged)
        self.chk_default_bool.setVisible(is_bool)
        self.lbl_items.setVisible(is_enum)
        self.le_items.setVisible(is_enum)
        self.cmb_default_enum.setVisible(is_enum)
        self.le_default_str.setVisible(is_string)

        # string 은 키를 못 건다 - 같은 체크를 "채널박스에 보이게" 로 쓴다.
        if is_string:
            self.chk_keyable.setText("Channel Box")
            self.chk_keyable.setToolTip(
                "String attributes cannot be keyed.\n"
                "On  : shown in the channel box.\n"
                "Off : hidden (Attribute Editor only).")
        else:
            self.chk_keyable.setText("Keyable")
            self.chk_keyable.setToolTip(
                "On  : shows in the channel box and can be keyed.\n"
                "Off : created hidden from the channel box.")

        for spin in (self.sp_min, self.sp_max, self.sp_default):
            spin.setDecimals(0 if is_int else 3)
            spin.setSingleStep(1 if is_int else 0.1)

        self._sync_range()
        self._sync_hint()

    def _sync_enum_items(self, _text=None):
        """Items 칸이 바뀌면 기본 항목 콤보를 다시 채운다. 고른 이름은 가능하면 유지."""
        current = self.cmb_default_enum.currentText()
        items = prefs._enum_items(self.le_items.text())
        self.cmb_default_enum.blockSignals(True)
        self.cmb_default_enum.clear()
        self.cmb_default_enum.addItems(items)
        index = self.cmb_default_enum.findText(current)
        self.cmb_default_enum.setCurrentIndex(index if index >= 0 else 0)
        self.cmb_default_enum.blockSignals(False)

    def _sync_range(self):
        self.sp_min.setEnabled(self.chk_min.isChecked())
        self.sp_max.setEnabled(self.chk_max.isChecked())

    def _sync_hint(self):
        """기본값이 범위를 벗어나면 "잘린다" 고 미리 알려 준다."""
        if self.cmb_type.currentText() not in prefs.RANGED_TYPES:
            self.lbl_hint.setText("")
            return
        value = self.sp_default.value()
        low = self.sp_min.value() if self.chk_min.isChecked() else None
        high = self.sp_max.value() if self.chk_max.isChecked() else None
        if (low is not None and value < low) or (high is not None and value > high):
            self.lbl_hint.setText(
                "Default is outside the range - it will be clamped into it.")
        else:
            self.lbl_hint.setText("")

    # ------------------------------------------------------------------

    def spec(self):
        """정규화된 스펙 dict. 이름이 잘못되면 ValueError."""
        type_name = self.cmb_type.currentText()
        if type_name == "bool":
            raw = {"name": self.le_name.text(), "type": "bool",
                   "default": 1 if self.chk_default_bool.isChecked() else 0,
                   "keyable": self.chk_keyable.isChecked()}
        elif type_name == "enum":
            raw = {"name": self.le_name.text(), "type": "enum",
                   "enum": self.le_items.text(),
                   "default": max(0, self.cmb_default_enum.currentIndex()),
                   "keyable": self.chk_keyable.isChecked()}
        elif type_name == "string":
            raw = {"name": self.le_name.text(), "type": "string",
                   "default": self.le_default_str.text(),
                   "keyable": self.chk_keyable.isChecked()}
        else:
            raw = {
                "name": self.le_name.text(),
                "type": type_name,
                "min": self.sp_min.value() if self.chk_min.isChecked() else None,
                "max": self.sp_max.value() if self.chk_max.isChecked() else None,
                "default": self.sp_default.value(),
                "keyable": self.chk_keyable.isChecked(),
            }
        return prefs.normalize_spec(raw)

    def _on_accept(self):
        try:
            self.spec()
        except ValueError as e:
            QMessageBox.warning(self, "Attribute", str(e))
            return
        self.accept()
