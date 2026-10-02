# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-02
# Framework - 토큰 이름 위젯 (공용, PySide). A00330_NamingTool Rename > Token 탭(v01.08)에서 올려 왔다.
#
# 이름을 `_` 로 이은 토큰 칸으로 짓는 화면 한 벌.
#   - Profile : 토큰 규칙 한 벌을 json 으로 저장/불러오기 (Save / New / Rename / Delete).
#               칸을 고쳐도 **저장하지 않는다** - `Save` 를 눌러야 지금 칸이 그 프로파일의 기본이 된다
#               (2026-10-01, 예전엔 고칠 때마다 바로 저장돼서 다시 열면 고친 칸이 기본으로 나왔다).
#               저장 안 한 칸은 프로파일을 바꾸거나 창을 닫으면 버려진다. 새 프로파일은 지금 칸을 복사한다.
#   - Tokens  : 칸마다 규칙 콤보 (Custom / Enum / Numbering / Set's Name - 툴이 고른 것만).
#               Enum (2026-10-02) : 정해진 값 중 하나를 콤보로 고른다. 칸 이름(role) 은 콤보 위에,
#               값 목록 · 칸 이름은 `Values...` 로 고친다 (Save 를 눌러야 프로파일에 남는다).
#               rules_editable=False (배포본, A00330 v01.14) : `Values...` 가 없고, Enum 칸은 규칙을 못 바꾸고
#               지울 수 없다 - 공유받은 사람은 정해진 값 중에서 고르기만 한다.
#               v01.17 : 배포본에서는 `Add Token` / `Delete Token` 도 없다 - 칸 구성 자체가 정해진 규칙이다.
#               mode_toggle=True (개발자 모드에서만) : `Dev Mode` 토글 버튼 - 개발 / 배포 화면을 번갈아 본다.
#               칸 머리(Token N)를 눌러 고른 뒤
#                 Add Token    : 고른 칸 **오른쪽**에 새 칸
#                 Delete Token : 고른 칸 삭제 (마지막 한 칸은 남긴다)
#               칸이 창보다 많아지면 가로 스크롤. 아래 줄에 미리보기.
#
# 규칙 · 검사 · 저장은 Framework.core.token_naming (TokenRuleSet / TokenProfileStore).
# 이 위젯은 **이름을 실제로 적용하지 않는다** - 툴이 `tokens()` 를 읽어 rename / 파일명에 쓴다.
#
# 사용:
#     from Framework.core import token_naming
#     from Framework.qt.MOD_tokenName_qt_v01 import JUN_mod_tokenName_qt_v01
#
#     store = token_naming.TokenProfileStore(data_dir, default_tokens, token_naming.MAYA_NODE_RULES)
#     w = JUN_mod_tokenName_qt_v01(store, log=self._log, log_prefix="Token")
#     tokens = w.tokens(); errors = w.ruleset.validate(tokens)

from Framework.qt.qt import *


# 칸 폭 (A00330 v01.08: 120 -> 80). 80px 에 넣으려고 칸 여백 0, 콤보 padding · 화살표 폭을 줄이고,
# Numbering 의 Start / Pad 0 라벨을 스핀박스 **위**로 올렸다(한 줄이면 실측 107px 필요).
COLUMN_WIDTH = 80


class TokenScrollArea(QScrollArea):
    """가로로만 스크롤하는 영역. 높이는 칸 높이 + 가로 스크롤바만큼 **고정** - 세로로 잘리지 않게.

    크기 힌트만 돌려주면 레이아웃이 옛 값(테마 전 글자 크기)을 캐시해 칸 아래가 8px 잘렸다(실측).
    그래서 안쪽 위젯이 레이아웃을 다시 잡거나 스타일이 바뀔 때마다 높이를 직접 고정한다.
    """

    def setWidget(self, widget):
        super().setWidget(widget)
        widget.installEventFilter(self)
        self.fit_height()

    def fit_height(self):
        widget = self.widget()
        inner = widget.sizeHint().height() if widget else 0
        height = inner + self.horizontalScrollBar().sizeHint().height() + 2 * self.frameWidth()
        if self.height() != height or self.minimumHeight() != height:
            self.setFixedHeight(height)

    def eventFilter(self, watched, event):
        if watched is self.widget() and event.type() in (
                QEvent.LayoutRequest, QEvent.StyleChange, QEvent.Polish):
            self.fit_height()
        return super().eventFilter(watched, event)

    def event(self, event):
        if event.type() in (QEvent.StyleChange, QEvent.Polish, QEvent.Show):
            self.fit_height()
        return super().event(event)


class EnumValuesDialog(QDialog):
    """Enum 칸의 이름(role) 과 값 목록을 고치는 창. 값은 쉼표로 나눈다."""

    def __init__(self, role, values, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enum Values")
        self.setMinimumWidth(380)
        form = QFormLayout(self)
        self.le_role = QLineEdit(role)
        self.le_role.setPlaceholderText("e.g. character")
        self.le_role.setToolTip("What this token is (shown above the values). Not part of the name.")
        form.addRow("Token name:", self.le_role)
        self.le_values = QLineEdit(", ".join(values))
        self.le_values.setPlaceholderText("e.g. CHN, DHA, LUN, SIN, TBM")
        self.le_values.setToolTip("The values to pick from, separated by commas.")
        form.addRow("Values:", self.le_values)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def result_values(self):
        return (self.le_role.text().strip(),
                [v.strip() for v in self.le_values.text().split(",")])


class TokenColumn(QFrame):
    """토큰 칸 하나 - 머리 버튼 / 규칙 콤보 / 규칙별 입력.

    Custom 글자 · Enum 값 콤보 · Numbering Start + Pad 0 · Set's Name(입력 없음 - 안내 글자만).
    """

    def __init__(self, token, ruleset, on_changed, rules_editable=True, parent=None):
        super().__init__(parent)
        self._ruleset = ruleset
        self._on_changed = on_changed
        self._rules_editable = rules_editable
        self._pages = {}          # rule key -> stack index
        self._enum_values = []    # Enum 값 목록 (콤보 항목과 같다)
        self._enum_role = ""      # Enum 칸 이름 - 이름에는 안 들어간다
        self.setFixedWidth(COLUMN_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(4)

        # 머리 = 칸 고르기 (Add / Delete Token 의 기준 자리)
        self.header = QPushButton("Token")
        self.header.setCheckable(True)
        self.header.setToolTip("Click to pick this token for Add Token / Delete Token.")
        # 테마 qss 에 QPushButton:checked 가 없어 고른 칸이 안 보인다 → 이 버튼에만 강조색.
        self.header.setStyleSheet(
            "QPushButton:checked { background-color: #d9a441; color: #1e1e1e;"
            " border: 1px solid #f0c060; font-weight: bold; }")
        layout.addWidget(self.header)

        self.combo = QComboBox()
        for key, label in ruleset.rule_items():
            self.combo.addItem(label, key)
        # 테마 padding 이면 'Numbering' 콤보가 89px 을 요구해 잘린다(실측) → 이 콤보만 줄인다.
        self.combo.setStyleSheet(
            "QComboBox { padding: 1px 1px; } QComboBox::drop-down { width: 12px; }")
        self.combo.setToolTip(ruleset.rule_tooltip())
        layout.addWidget(self.combo)

        self.stack = QStackedWidget()

        # 규칙별 페이지는 모두 [이름 줄] -> [입력칸] 순서다 (2026-10-02). 이름 줄이 없는 페이지가 있으면
        # 입력칸이 한 줄 위로 붙어 옆 칸과 어긋난다(ref_02.png - Custom 의 SetXXX 가 Enum 의 CHN 보다 위).
        # 입력칸 높이는 _match_input_heights 가 하나로 맞춘다.

        # Custom
        self.le_text = QLineEdit()
        self.le_text.setPlaceholderText("text")
        custom_page, custom_layout = self._new_page()
        custom_layout.addWidget(self._caption("Text"))
        custom_layout.addWidget(self.le_text)
        custom_layout.addStretch(1)
        self._add_page("custom", custom_page)

        # Enum - 칸 이름 / 값 콤보 / Values... (Numbering 페이지 4줄보다 낮아 칸 높이는 그대로)
        self.lbl_role = self._caption("")
        self.cmb_value = QComboBox()
        self.cmb_value.setStyleSheet(
            "QComboBox { padding: 1px 1px; } QComboBox::drop-down { width: 12px; }")
        self.cmb_value.setToolTip("Pick one of the fixed values.")
        self.btn_values = QPushButton("Values...")
        self.btn_values.setStyleSheet("QPushButton { padding: 2px; }")
        self.btn_values.setToolTip("Edit this token's name and the list of values.")
        self.btn_values.clicked.connect(self._edit_enum_values)
        enum_page, enum_layout = self._new_page()
        enum_layout.addWidget(self.lbl_role)
        enum_layout.addWidget(self.cmb_value)
        enum_layout.addWidget(self.btn_values)
        enum_layout.addStretch(1)
        self._add_page("enum", enum_page)
        self._set_enum("", [], "")   # Custom 칸을 Enum 으로 바꿨을 때의 빈 상태

        # Numbering
        self.sp_start = QSpinBox()
        self.sp_start.setRange(0, 999999)
        self.sp_start.setToolTip("First number.")
        self.sp_pad = QSpinBox()
        self.sp_pad.setRange(0, 10)
        self.sp_pad.setToolTip("Zero padding - 2 gives 00, 01, 02 ...")
        number_page, number_layout = self._new_page()
        number_layout.addWidget(self._caption("Start"))
        number_layout.addWidget(self.sp_start)
        number_layout.addWidget(self._caption("Pad 0"))
        number_layout.addWidget(self.sp_pad)
        # 다른 페이지처럼 아래 stretch - 없으면 남는 높이가 이름 줄로 나뉘어 입력칸이 6px 내려간다(실측)
        number_layout.addStretch(1)
        self._add_page("numbering", number_page)

        # Set's Name - 입력 없음. 칸이 무엇으로 채워지는지만 보인다.
        setname_page, setname_layout = self._new_page()
        self.le_setname = QLineEdit(ruleset.sample_context)
        self.le_setname.setEnabled(False)
        self.le_setname.setToolTip("Filled with each set's name.")
        setname_layout.addWidget(self._caption("Set"))
        setname_layout.addWidget(self.le_setname)
        setname_layout.addStretch(1)
        self._add_page("setname", setname_page)

        layout.addWidget(self.stack)

        # 높이를 맞출 입력칸 - 값이 보이는 칸 전부
        self._inputs = (self.le_text, self.cmb_value, self.sp_start, self.sp_pad, self.le_setname)

        self.set_token(token)
        self._apply_rule_lock()

        self.combo.currentIndexChanged.connect(self._on_rule_changed)
        self.le_text.textChanged.connect(self._emit)
        self.sp_start.valueChanged.connect(self._emit)
        self.sp_pad.valueChanged.connect(self._emit)
        self.cmb_value.currentIndexChanged.connect(self._emit)

    @staticmethod
    def _new_page():
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(1)
        return page, page_layout

    @staticmethod
    def _caption(text):
        """입력칸 위 이름 줄 (Text / character / Start ...). 모든 페이지가 같은 모양."""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        return label

    def _match_input_heights(self):
        """입력칸(글자 · Enum 값 · 스핀박스) 높이를 하나로 (2026-10-02, ref_02.png).

        Enum 값 콤보는 80px 칸에 글자가 들어가도록 padding 을 줄여서 테마 그대로인 QLineEdit /
        QSpinBox 보다 낮았다. 테마마다 높이가 다르므로 고정값이 아니라 **테마를 입힌 뒤의**
        QLineEdit · QSpinBox 높이 중 큰 값으로 맞춘다 (테마가 바뀌면 다시 맞춘다).
        """
        if not getattr(self, "_inputs", None):
            return
        for widget in self._inputs:
            widget.ensurePolished()
        height = max(self.le_text.sizeHint().height(), self.sp_start.sizeHint().height())
        for widget in self._inputs:
            if widget.minimumHeight() != height or widget.maximumHeight() != height:
                widget.setFixedHeight(height)

    def event(self, event):
        if event.type() in (QEvent.Polish, QEvent.StyleChange, QEvent.Show):
            self._match_input_heights()
        return super().event(event)

    def _add_page(self, key, page):
        self._pages[key] = self.stack.addWidget(page)

    def is_enum(self):
        return self.combo.currentData() == "enum"

    def _apply_rule_lock(self):
        """rules_editable=False 면 정해진 규칙(Enum 칸)을 못 바꾸게 한다 (배포본).

        - `Values...` 를 숨긴다 - 칸 이름 · 값 목록 편집 불가.
        - Enum 칸은 규칙 콤보를 잠근다 - Custom 으로 바꿔 아무 글자나 넣는 길을 막는다.
        - Enum 이 아닌 칸의 규칙 콤보에서는 Enum 을 뺀다 - 값 목록을 만들 수 없으니 빈 Enum 만 생긴다.
        - 칸 머리(Token N)를 숨긴다 (A00330 v01.22) - Add / Delete Token 의 기준 칸을 고르는 버튼이라
          배포 화면(Add / Delete Token 없음)에서는 할 일이 없다.
        Enum 칸 삭제는 위젯(on_delete_token)이 막는다.
        """
        if self._rules_editable:
            return
        self.btn_values.hide()
        self.header.hide()
        if self.is_enum():
            self.combo.setEnabled(False)
            self.combo.setToolTip("This token is a fixed rule - pick one of its values below.")
            return
        index = self.combo.findData("enum")
        if index >= 0:
            self.combo.blockSignals(True)
            self.combo.removeItem(index)
            self.combo.blockSignals(False)

    def _show_page(self):
        self.stack.setCurrentIndex(self._pages.get(self.combo.currentData(), 0))

    def set_token(self, token):
        token = self._ruleset.normalize_token(token)
        self.combo.blockSignals(True)
        self.combo.setCurrentIndex(max(0, self.combo.findData(token["rule"])))
        self.combo.blockSignals(False)
        for widget in (self.le_text, self.sp_start, self.sp_pad, self.cmb_value):
            widget.blockSignals(True)
        if token["rule"] == "numbering":
            self.sp_start.setValue(token["start"])
            self.sp_pad.setValue(token["pad"])
        elif token["rule"] == "custom":
            self.le_text.setText(token["text"])
        elif token["rule"] == "enum":
            self._set_enum(token.get("role", ""), token["values"], token["value"])
        for widget in (self.le_text, self.sp_start, self.sp_pad, self.cmb_value):
            widget.blockSignals(False)
        self._show_page()

    def _set_enum(self, role, values, value):
        """Enum 칸 이름 · 값 목록 · 고른 값을 화면에. 신호는 호출 측이 막는다."""
        self._enum_role = role
        self._enum_values = list(values)
        self.lbl_role.setText(role or "(enum)")
        self.lbl_role.setToolTip(role or "No token name - set one with Values...")
        self.cmb_value.clear()
        self.cmb_value.addItems(self._enum_values)
        index = self.cmb_value.findText(value)
        self.cmb_value.setCurrentIndex(index if index >= 0 else (0 if values else -1))

    def _edit_enum_values(self):
        dialog = EnumValuesDialog(self._enum_role, self._enum_values, self)
        if dialog.exec_() != QDialog.Accepted:
            return
        role, raw_values = dialog.result_values()
        token = self._ruleset.normalize_token({
            "rule": "enum", "role": role, "values": raw_values,
            "value": self.cmb_value.currentText()})
        self.cmb_value.blockSignals(True)
        self._set_enum(token.get("role", ""), token["values"], token["value"])
        self.cmb_value.blockSignals(False)
        self._emit()

    def token(self):
        rule = self.combo.currentData()
        if rule == "numbering":
            return {"rule": "numbering",
                    "start": self.sp_start.value(), "pad": self.sp_pad.value()}
        if rule == "setname":
            return {"rule": "setname"}
        if rule == "enum":
            token = {"rule": "enum", "values": list(self._enum_values),
                     "value": self.cmb_value.currentText()}
            if self._enum_role:
                token["role"] = self._enum_role
            return token
        return {"rule": "custom", "text": self.le_text.text()}

    def _on_rule_changed(self, _index):
        self._show_page()
        self._emit()

    def _emit(self, *args):
        if self._on_changed:
            self._on_changed()


class JUN_mod_tokenName_qt_v01(QWidget):
    """Profile + Tokens 화면 한 벌.

    store      : Framework.core.token_naming.TokenProfileStore (규칙 묶음은 store.ruleset)
    log        : log(message) 콜백 (툴 로그창)
    log_prefix : 로그 · 다이얼로그 제목 앞말 ("Token", "Naming" ...)
    framed     : True = Profile / Tokens 를 각각 QGroupBox 로 감싼다 (A00330 Token 탭).
                 False = 테두리 없이, Profile 과 Add / Delete Token 을 **한 줄**에 - 이미 그룹 박스
                 안에 넣을 때, 세로 공간을 아낄 때 (A00480 Export > Naming).

    rules_editable : False = 배포본처럼 정해진 규칙을 못 바꾸게 (Enum 칸의 Values... 없음 · 규칙 잠금 ·
                 삭제 불가 · Add / Delete Token 없음). 툴이 개발자 모드 여부로 넘긴다 (A00330 v01.14, v01.17).
    mode_toggle : True = `Dev Mode` 토글 버튼을 단다 - 켜면 개발 화면, 끄면 배포 화면 (A00330 v01.17).
                 개발자 모드인 툴만 True 로 넘긴다 (배포본에는 버튼이 없다). set_rules_editable() 로도 바꾼다.

    preview_row : 미리보기 줄 QHBoxLayout - 툴 버튼을 오른쪽에 붙일 자리.

    신호 tokensChanged(list) : 칸이 바뀔 때마다(프로파일 전환 포함) 지금 토큰 목록.

    칸을 고쳐도 프로파일 json 은 그대로다 - `Save` 버튼(save_profile)을 눌러야 저장된다.
    is_dirty() : 저장된 칸과 지금 칸이 다른지.
    """

    tokensChanged = Signal(list)

    #: 개발 / 배포 화면이 바뀔 때 (set_rules_editable · Dev Mode 토글). True = 개발 화면.
    #: 툴이 배포 화면에 맞춰 다른 UI 를 막는 데 쓴다 (A00330 v01.17 - Token 말고 다른 탭 잠금).
    rulesEditableChanged = Signal(bool)

    def __init__(self, store, log=None, log_prefix="Token", framed=True, rules_editable=True,
                 mode_toggle=False, parent=None):
        super().__init__(parent)
        self.store = store
        self._rules_editable = rules_editable
        self._mode_toggle = mode_toggle
        self.btn_dev_mode = None
        # 지금 프로파일이 free_tokens 인가 (A00330 `Custom` 프로파일, v01.23) - load_tokens 가 정한다
        self._free_tokens = False
        self.ruleset = store.ruleset
        self._log_callback = log
        self._prefix = log_prefix
        self._framed = framed
        self.columns = []
        self._profile = store.get_active()
        self._loading = False
        # 프로파일에 저장된 칸 (Save 를 누르기 전까지의 기준). 칸 형식 그대로 비교하려고
        # json 이 아니라 로드 직후 tokens() 로 잡는다.
        self._saved_tokens = []

        self.build_ui()
        self.load_tokens(store.load_profile(self._profile))
        self._refresh_profiles()
        self._apply_mode_buttons()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        if self._framed:
            profile_box = QGroupBox("Profile")
            self._add_profile_widgets(QHBoxLayout(profile_box))
            root.addWidget(profile_box)

            token_box = QGroupBox("Tokens")
            token_layout = QVBoxLayout(token_box)
            buttons = QHBoxLayout()
            self._add_token_buttons(buttons)
            buttons.addStretch(1)
            self._add_mode_toggle(buttons)
            token_layout.addLayout(buttons)
            self._add_token_area(token_layout)
            root.addWidget(token_box)
            return

        # 테두리 없음 - Profile 과 Add / Delete Token 을 한 줄에 (세로 공간 절약)
        row = QHBoxLayout()
        row.addWidget(QLabel("Profile"))
        self._add_profile_widgets(row)
        row.addSpacing(16)
        self._add_token_buttons(row)
        self._add_mode_toggle(row)
        root.addLayout(row)
        self._add_token_area(root)

    def _add_profile_widgets(self, row):
        self.cmb_profile = QComboBox()
        self.cmb_profile.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_profile.setMinimumContentsLength(10)
        self.cmb_profile.setToolTip(
            "Active profile - a saved set of token rules\n"
            "(each profile is its own JSON under the tool's data folder).\n"
            "Edited tokens are NOT saved until you click Save.")
        self.cmb_profile.currentTextChanged.connect(self.on_profile_changed)
        row.addWidget(self.cmb_profile, stretch=1)

        self.btn_save_profile = QPushButton("Save")
        self.btn_save_profile.setToolTip(
            "Save the tokens shown now as this profile's default.\n"
            "Until you click it, edits are not saved - switching profile\n"
            "or closing the tool drops them.")
        self.btn_save_profile.clicked.connect(self.on_save_profile)
        row.addWidget(self.btn_save_profile)

        for label, tip, slot in (
                ("New", "Create a new profile from the tokens shown now", self.on_new_profile),
                ("Rename", "Rename the current profile", self.on_rename_profile),
                ("Delete", "Delete the current profile", self.on_delete_profile)):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row.addWidget(btn)
            # 배포 화면에서 숨긴다 (A00330 New v01.20, Rename / Delete v01.21)
            setattr(self, "btn_{0}_profile".format(label.lower()), btn)

    def _add_token_buttons(self, buttons):
        self.btn_add_token = QPushButton("Add Token")
        self.btn_add_token.setToolTip(
            "Insert a new token to the RIGHT of the picked token\n"
            "(click a token's header to pick it).")
        self.btn_add_token.clicked.connect(self.on_add_token)
        buttons.addWidget(self.btn_add_token)
        self.btn_delete_token = QPushButton("Delete Token")
        self.btn_delete_token.setToolTip("Delete the picked token. One token always stays.")
        self.btn_delete_token.clicked.connect(self.on_delete_token)
        buttons.addWidget(self.btn_delete_token)

    def _add_mode_toggle(self, row):
        """`Dev Mode` 토글 (mode_toggle=True 일 때만). 켜짐 = 개발 화면, 꺼짐 = 배포 화면."""
        if not self._mode_toggle:
            return
        self.btn_dev_mode = QPushButton("Dev Mode")
        self.btn_dev_mode.setCheckable(True)
        self.btn_dev_mode.setChecked(self._rules_editable)
        self.btn_dev_mode.setToolTip(
            "On  : developer view - Values..., Add Token / Delete Token, Enum rules can change.\n"
            "Off : the view people get in the shared tool - fixed rules, pick values only.\n"
            "Only shown in developer mode. Tokens shown now are kept when you switch.")
        # 테마 qss 에 :checked 가 없어 켜진 게 안 보인다 → 칸 머리와 같은 강조색
        self.btn_dev_mode.setStyleSheet(
            "QPushButton:checked { background-color: #d9a441; color: #1e1e1e;"
            " border: 1px solid #f0c060; font-weight: bold; }")
        self.btn_dev_mode.toggled.connect(self.set_rules_editable)
        row.addWidget(self.btn_dev_mode)

    def rules_editable(self):
        return self._rules_editable

    def set_rules_editable(self, editable):
        """개발 화면(True) / 배포 화면(False) 으로 바꾼다. 지금 칸 · 저장 기준은 그대로 둔다.

        Enum 칸의 잠금은 칸을 만들 때 정해지므로(콤보에서 Enum 을 빼는 등) 칸을 다시 만든다.
        """
        editable = bool(editable)
        if self.btn_dev_mode is not None and self.btn_dev_mode.isChecked() != editable:
            self.btn_dev_mode.blockSignals(True)
            self.btn_dev_mode.setChecked(editable)
            self.btn_dev_mode.blockSignals(False)
        if editable == self._rules_editable:
            return
        self._rules_editable = editable
        tokens, saved = self.tokens(), self._saved_tokens
        picked = self.selected_index()
        self.load_tokens(tokens)
        self._saved_tokens = saved      # load_tokens 가 지금 칸을 저장 기준으로 잡으므로 되돌린다
        if 0 <= picked < len(self.columns):
            self.select_column(picked)
        self._after_edit()
        self._apply_mode_buttons()
        self._log("{0} : {1} view.".format(
            self._prefix, "developer" if editable else "release (shared tool)"))
        self.rulesEditableChanged.emit(editable)

    def _apply_mode_buttons(self):
        """배포 화면에서는 Add / Delete Token (v01.17) 과 Profile 줄의 Save / New (A00330 v01.20) ·
        Rename / Delete (v01.21) 를 숨긴다 - Profile 줄에는 고르는 콤보만 남는다.

        Save · New 가 있으면 고친 칸을 프로파일로 남길 수 있고, Rename · Delete 가 있으면 정해진
        프로파일(규칙)을 지우거나 이름을 바꿀 수 있다 - 공유받은 사람이 규칙을 임의로 바꾸지 못하게 한다.
        칸 편집은 이번 Rename 에만 쓰이고 프로파일 json 은 그대로다.
        """
        for button in (self.btn_save_profile, self.btn_new_profile,
                       self.btn_rename_profile, self.btn_delete_profile):
            button.setVisible(self._rules_editable)
        # Add / Delete Token 과 칸 머리(칸 고르기)는 free_tokens 프로파일이면 배포 화면에서도 보인다 (v01.23)
        free = self.tokens_addable()
        for button in (self.btn_add_token, self.btn_delete_token):
            button.setVisible(free)
        for column in self.columns:
            column.header.setVisible(free)

    def tokens_addable(self):
        """칸을 더하고 뺄 수 있는가 - 개발 화면이거나, 지금 프로파일이 free_tokens(`Custom`) 이면."""
        return self._rules_editable or self._free_tokens

    def _add_token_area(self, outer):
        # 토큰 칸 줄 - 칸이 늘면 가로 스크롤
        self.column_host = QWidget()
        self.column_layout = QHBoxLayout(self.column_host)
        self.column_layout.setContentsMargins(0, 0, 0, 0)
        self.column_layout.setSpacing(4)
        self.column_layout.addStretch(1)

        self.scroll = TokenScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.column_host)
        outer.addWidget(self.scroll)

        self.header_group = QButtonGroup(self)
        self.header_group.setExclusive(True)

        self.lbl_preview = QLabel()
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setToolTip("The first name, and how the numbers move on.")
        # 미리보기 줄 - 툴이 실행 버튼을 오른쪽에 붙일 수 있다 (preview_row.addWidget(btn)).
        self.preview_row = QHBoxLayout()
        self.preview_row.addWidget(self.lbl_preview, stretch=1)
        outer.addLayout(self.preview_row)

    # ================================================================
    # 토큰 칸
    # ================================================================

    def profile(self):
        """현재 프로파일 이름."""
        return self._profile

    def tokens(self):
        return [column.token() for column in self.columns]

    def validate(self):
        """지금 칸의 문제 목록 (빈 리스트면 실행 가능)."""
        return self.ruleset.validate(self.tokens())

    def load_tokens(self, tokens):
        """칸을 전부 다시 만든다 (프로파일 전환)."""
        self._free_tokens = self.store.profile_flag(self._profile, "free_tokens")
        self._loading = True
        for column in self.columns:
            self.header_group.removeButton(column.header)
            self.column_layout.removeWidget(column)
            column.deleteLater()
        self.columns = []
        for token in tokens:
            self._insert_column(len(self.columns), token)
        self._loading = False
        if self.columns:
            self.select_column(len(self.columns) - 1)
        self._saved_tokens = self.tokens()
        self._after_edit()
        if hasattr(self, "btn_add_token"):
            self._apply_mode_buttons()

    def _insert_column(self, index, token):
        column = TokenColumn(token, self.ruleset, self._on_token_changed,
                             rules_editable=self._rules_editable)
        self.header_group.addButton(column.header)
        # 배포 화면이면 칸이 머리를 숨기지만, free_tokens 프로파일은 칸을 골라야 하므로 보인다
        column.header.setVisible(self.tokens_addable())
        self.columns.insert(index, column)
        # 마지막 항목은 stretch 라서 칸은 그 앞에 넣는다
        self.column_layout.insertWidget(index, column)
        self._renumber()
        return column

    def _renumber(self):
        for number, column in enumerate(self.columns, 1):
            column.header.setText("Token {0}".format(number))

    def selected_index(self):
        for index, column in enumerate(self.columns):
            if column.header.isChecked():
                return index
        return -1

    def select_column(self, index):
        # 배타 그룹이라 끄기는 무시된다 - 켜려는 칸을 직접 켠다.
        column = self.columns[index]
        column.header.setChecked(True)
        self.scroll.ensureWidgetVisible(column)

    def on_add_token(self):
        picked = self.selected_index()
        index = picked + 1 if picked >= 0 else len(self.columns)
        self._insert_column(index, {"rule": "custom", "text": ""})
        self.select_column(index)
        # 레이아웃이 끝난 뒤에야 새 칸 위치를 안다 → 한 번 더 보이게.
        QTimer.singleShot(0, lambda: self.columns and self.scroll.ensureWidgetVisible(
            self.columns[min(index, len(self.columns) - 1)]))
        self._after_edit()
        self._log("{0} : added Token {1}.".format(self._prefix, index + 1))

    def on_delete_token(self):
        if len(self.columns) <= 1:
            self._log("[WARN] {0} : one token must remain.".format(self._prefix))
            return
        index = self.selected_index()
        if index < 0:
            self._log("[WARN] {0} : click a token's header to pick the one to delete.".format(
                self._prefix))
            return
        if not self._rules_editable and self.columns[index].is_enum():
            self._log("[WARN] {0} : Token {1} is a fixed rule and cannot be deleted.".format(
                self._prefix, index + 1))
            return
        column = self.columns.pop(index)
        self.header_group.removeButton(column.header)
        self.column_layout.removeWidget(column)
        column.deleteLater()
        self._renumber()
        self.select_column(min(index, len(self.columns) - 1))
        self._after_edit()
        self._log("{0} : deleted Token {1}.".format(self._prefix, index + 1))

    def _on_token_changed(self):
        if not self._loading:
            self._after_edit()

    def _after_edit(self):
        # 미리보기 · Save 버튼 상태만 갱신한다. 저장은 Save 버튼(save_profile)만 한다.
        tokens = self.tokens()
        self.lbl_preview.setText("Preview : " + self.ruleset.preview(tokens))
        self.btn_save_profile.setEnabled(tokens != self._saved_tokens)
        self.tokensChanged.emit(tokens)

    def is_dirty(self):
        """저장 안 한 칸 변경이 있는지."""
        return self.tokens() != self._saved_tokens

    # ================================================================
    # Profile
    # ================================================================

    def _refresh_profiles(self):
        self.cmb_profile.blockSignals(True)
        self.cmb_profile.clear()
        self.cmb_profile.addItems(self.store.list_profiles())
        index = self.cmb_profile.findText(self._profile)
        if index >= 0:
            self.cmb_profile.setCurrentIndex(index)
        self.cmb_profile.blockSignals(False)

    def on_save_profile(self):
        self.save_profile()

    def save_profile(self):
        """지금 칸을 현재 프로파일의 기본으로 저장한다 (Save 버튼)."""
        if not self._profile:
            return
        tokens = self.tokens()
        self.store.save_profile(self._profile, tokens)
        self._saved_tokens = tokens
        self.btn_save_profile.setEnabled(False)
        self._log("[OK] {0} profile : saved '{1}' ({2} token(s)).".format(
            self._prefix, self._profile, len(tokens)))

    def on_profile_changed(self, name):
        if not name or name == self._profile:
            return
        if self.is_dirty():
            self._log("[WARN] {0} profile : unsaved edits to '{1}' were dropped.".format(
                self._prefix, self._profile))
        self._profile = name
        self.store.set_active(name)
        tokens = self.store.load_profile(name)
        self.load_tokens(tokens)
        self._log("[OK] {0} profile : switched to '{1}' ({2} token(s)).".format(
            self._prefix, name, len(tokens)))

    def _ask_profile_name(self, title, label, text=""):
        raw, ok = QInputDialog.getText(self, title, label, text=text)
        if not ok:
            return None
        name = self.store.sanitize_name(raw)
        if not name:
            return None
        if name in self.store.list_profiles():
            QMessageBox.warning(self, self._prefix, "Profile '{0}' already exists.".format(name))
            return None
        return name

    def on_new_profile(self):
        name = self._ask_profile_name("New Profile", "Profile name (copies the tokens shown now):")
        if not name:
            return
        self.create_profile(name)

    def create_profile(self, name):
        """지금 칸을 복사해 새 프로파일을 만들고 그쪽으로 바꾼다."""
        tokens = self.tokens()
        self.store.save_profile(name, tokens)
        self.store.set_active(name)
        self._profile = name
        # 새 프로파일엔 지금 칸이 저장됐다. 원래 프로파일은 Save 전 그대로다.
        self._saved_tokens = tokens
        self.btn_save_profile.setEnabled(False)
        self._refresh_profiles()
        self._log("[OK] {0} profile : created '{1}'.".format(self._prefix, name))

    def on_rename_profile(self):
        old = self._profile
        new = self._ask_profile_name("Rename Profile", "New name:", text=old)
        if not new:
            return
        self.store.rename_profile(old, new)
        self._profile = new
        self._refresh_profiles()
        self._log("[OK] {0} profile : renamed '{1}' -> '{2}'.".format(self._prefix, old, new))

    def on_delete_profile(self):
        name = self._profile
        if len(self.store.list_profiles()) <= 1:
            QMessageBox.information(self, self._prefix, "At least one profile must remain.")
            return
        if QMessageBox.question(
                self, self._prefix, "Delete profile '{0}'?".format(name)) != QMessageBox.Yes:
            return
        self.delete_profile(name)

    def delete_profile(self, name):
        self.store.delete_profile(name)
        self._profile = self.store.list_profiles()[0]
        self.store.set_active(self._profile)
        self._refresh_profiles()
        self.load_tokens(self.store.load_profile(self._profile))
        self._log("[OK] {0} profile : deleted '{1}'.".format(self._prefix, name))

    # ================================================================
    # Helper
    # ================================================================

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
