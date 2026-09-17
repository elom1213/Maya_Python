# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00330_NamingTool - Rename > Token 탭 (v01.07, 구 Naming Dyn)
#
# 토큰을 `_` 로 이어 오브젝트와 그 transform 자손의 이름을 한 번에 짓는다.
#   - 토큰 칸마다 **규칙**을 고른다 (A00480_FileTool Export 탭의 Naming 처럼 칸 밑에 콤보).
#       Custom    : 적은 글자 그대로
#       Numbering : Start 부터 올라가는 번호 + Pad 0 자리수
#   - 토큰 칸은 **개수가 자유**다. 칸 머리(Token N)를 눌러 고른 뒤
#       Add Token    : 고른 칸 **오른쪽**에 새 칸
#       Delete Token : 고른 칸 삭제 (마지막 한 칸은 남긴다)
#     칸이 창보다 많아지면 가로 스크롤.
#   - **Profile** : 토큰 규칙 한 벌을 json 으로 저장/불러오기 (A00145 Attribute > Create 와 같은 구성).
#     칸을 고치면 **현재 프로파일에 바로 저장**된다. 새 프로파일은 지금 칸을 복사해서 만든다.
# 번호를 세는 규칙 · 검사는 core.token_ops, 파일은 core.token_profile_prefs.

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from tools.A00330_NamingTool.app import core
from tools.A00330_NamingTool.app.core import token_ops
from tools.A00330_NamingTool.app.core import token_profile_prefs as tprefs


# v01.08: 120 -> 80 (2/3). 80px 에 넣으려고 칸 여백 0, 콤보 padding · 화살표 폭을 줄이고,
# Numbering 의 Start / Pad 0 라벨을 스핀박스 **위**로 올렸다(한 줄이면 실측 107px 필요).
COLUMN_WIDTH = 80


class TokenScrollArea(QScrollArea):
    """가로로만 스크롤하는 영역. 높이는 칸 높이 + 가로 스크롤바만큼 **고정** - 세로로 잘리지 않게.

    크기 힌트만 돌려주면 레이아웃이 옛 값(테마 전 글자 크기)을 캐시해 칸 아래가 8px 잘렸다(실측).
    그래서 안쪽 위젯이 레이아웃을 다시 잡거나 스타일이 바뀔 때마다 높이를 직접 고정한다.
    """

    def setWidget(self, widget):
        super(TokenScrollArea, self).setWidget(widget)
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
        return super(TokenScrollArea, self).eventFilter(watched, event)

    def event(self, event):
        if event.type() in (QEvent.StyleChange, QEvent.Polish, QEvent.Show):
            self.fit_height()
        return super(TokenScrollArea, self).event(event)


class TokenColumn(QFrame):
    """토큰 칸 하나 - 머리 버튼 / 규칙 콤보 / 규칙별 입력(Custom 글자 · Numbering Start + Pad 0)."""

    def __init__(self, token, on_changed, parent=None):
        super(TokenColumn, self).__init__(parent)
        self._on_changed = on_changed
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
        for key, label in token_ops.RULES:
            self.combo.addItem(label, key)
        # 테마 padding 이면 'Numbering' 콤보가 89px 을 요구해 잘린다(실측) → 이 콤보만 줄인다.
        self.combo.setStyleSheet(
            "QComboBox { padding: 1px 1px; } QComboBox::drop-down { width: 12px; }")
        self.combo.setToolTip(
            "Custom    : the text as typed\n"
            "Numbering : a number counting up from Start, zero-padded to Pad 0 digits")
        layout.addWidget(self.combo)

        self.stack = QStackedWidget()

        # Custom
        self.le_text = QLineEdit()
        self.le_text.setPlaceholderText("text")
        custom_page = QWidget()
        custom_layout = QVBoxLayout(custom_page)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(self.le_text)
        custom_layout.addStretch(1)
        self.stack.addWidget(custom_page)

        # Numbering
        self.sp_start = QSpinBox()
        self.sp_start.setRange(0, 999999)
        self.sp_start.setToolTip("First number.")
        self.sp_pad = QSpinBox()
        self.sp_pad.setRange(0, token_ops.MAX_PAD)
        self.sp_pad.setToolTip("Zero padding - 2 gives 00, 01, 02 ...")
        number_page = QWidget()
        number_layout = QVBoxLayout(number_page)
        number_layout.setContentsMargins(0, 0, 0, 0)
        number_layout.setSpacing(1)
        number_layout.addWidget(QLabel("Start"))
        number_layout.addWidget(self.sp_start)
        number_layout.addWidget(QLabel("Pad 0"))
        number_layout.addWidget(self.sp_pad)
        self.stack.addWidget(number_page)

        layout.addWidget(self.stack)

        self.set_token(token)

        self.combo.currentIndexChanged.connect(self._on_rule_changed)
        self.le_text.textChanged.connect(self._emit)
        self.sp_start.valueChanged.connect(self._emit)
        self.sp_pad.valueChanged.connect(self._emit)

    def set_token(self, token):
        token = token_ops.normalize_token(token)
        self.combo.blockSignals(True)
        self.combo.setCurrentIndex(max(0, self.combo.findData(token["rule"])))
        self.combo.blockSignals(False)
        for widget in (self.le_text, self.sp_start, self.sp_pad):
            widget.blockSignals(True)
        if token["rule"] == token_ops.RULE_NUMBERING:
            self.sp_start.setValue(token["start"])
            self.sp_pad.setValue(token["pad"])
        else:
            self.le_text.setText(token["text"])
        for widget in (self.le_text, self.sp_start, self.sp_pad):
            widget.blockSignals(False)
        self.stack.setCurrentIndex(self.combo.currentIndex())

    def token(self):
        if self.combo.currentData() == token_ops.RULE_NUMBERING:
            return {"rule": token_ops.RULE_NUMBERING,
                    "start": self.sp_start.value(), "pad": self.sp_pad.value()}
        return {"rule": token_ops.RULE_CUSTOM, "text": self.le_text.text()}

    def _on_rule_changed(self, index):
        self.stack.setCurrentIndex(index)
        self._emit()

    def _emit(self, *args):
        if self._on_changed:
            self._on_changed()


class TokenTab(QWidget):

    def __init__(self, log=None, parent=None):
        super(TokenTab, self).__init__(parent)
        self._log_callback = log
        self.columns = []
        self._profile = tprefs.get_active()
        self._loading = False

        self.build_ui()
        self.load_tokens(tprefs.load_profile(self._profile))
        self._refresh_profiles()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        # Objects 리스트 (Select / Add / Del / Up / Down / Sort)
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Base",
            log_callback=self._log)
        root.addWidget(self.tsl, stretch=1)

        root.addWidget(self._build_profile_group())
        root.addWidget(self._build_token_group())

        self.btn_rename = QPushButton("Rename")
        self.btn_rename.setMinimumHeight(32)
        self.btn_rename.setToolTip(
            "Rename each listed object and its transform descendants with the tokens,\n"
            "joined by '_'. With two Numbering tokens the first counts objects and the\n"
            "second counts nodes inside each object (restarting per object).\n"
            "One undo step.")
        self.btn_rename.clicked.connect(self.on_rename)
        root.addWidget(self.btn_rename)

    def _build_profile_group(self):
        group = QGroupBox("Profile")
        row = QHBoxLayout(group)

        self.cmb_profile = QComboBox()
        self.cmb_profile.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_profile.setMinimumContentsLength(10)
        self.cmb_profile.setToolTip(
            "Active profile - a saved set of token rules\n"
            "(each profile is its own JSON under the tool's data folder).\n"
            "Editing the tokens saves them to this profile right away.")
        self.cmb_profile.currentTextChanged.connect(self.on_profile_changed)
        row.addWidget(self.cmb_profile, stretch=1)

        for label, tip, slot in (
                ("New", "Create a new profile from the tokens shown now", self.on_new_profile),
                ("Rename", "Rename the current profile", self.on_rename_profile),
                ("Delete", "Delete the current profile", self.on_delete_profile)):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        return group

    def _build_token_group(self):
        group = QGroupBox("Tokens")
        outer = QVBoxLayout(group)

        buttons = QHBoxLayout()
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
        buttons.addStretch(1)
        outer.addLayout(buttons)

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
        outer.addWidget(self.lbl_preview)
        return group

    # ================================================================
    # 토큰 칸
    # ================================================================

    def tokens(self):
        return [column.token() for column in self.columns]

    def load_tokens(self, tokens):
        """칸을 전부 다시 만든다 (프로파일 전환)."""
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
        self._after_edit(save=False)

    def _insert_column(self, index, token):
        column = TokenColumn(token, self._on_token_changed)
        self.header_group.addButton(column.header)
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
        self._insert_column(index, {"rule": token_ops.RULE_CUSTOM, "text": ""})
        self.select_column(index)
        # 레이아웃이 끝난 뒤에야 새 칸 위치를 안다 → 한 번 더 보이게.
        QTimer.singleShot(0, lambda: self.columns and self.scroll.ensureWidgetVisible(
            self.columns[min(index, len(self.columns) - 1)]))
        self._after_edit()
        self._log("Token : added Token {0}.".format(index + 1))

    def on_delete_token(self):
        if len(self.columns) <= 1:
            self._log("[WARN] Token : one token must remain.")
            return
        index = self.selected_index()
        if index < 0:
            self._log("[WARN] Token : click a token's header to pick the one to delete.")
            return
        column = self.columns.pop(index)
        self.header_group.removeButton(column.header)
        self.column_layout.removeWidget(column)
        column.deleteLater()
        self._renumber()
        self.select_column(min(index, len(self.columns) - 1))
        self._after_edit()
        self._log("Token : deleted Token {0}.".format(index + 1))

    def _on_token_changed(self):
        if not self._loading:
            self._after_edit()

    def _after_edit(self, save=True):
        tokens = self.tokens()
        self.lbl_preview.setText("Preview : " + token_ops.preview(tokens))
        if save and self._profile:
            tprefs.save_profile(self._profile, tokens)

    # ================================================================
    # Profile
    # ================================================================

    def _refresh_profiles(self):
        self.cmb_profile.blockSignals(True)
        self.cmb_profile.clear()
        self.cmb_profile.addItems(tprefs.list_profiles())
        index = self.cmb_profile.findText(self._profile)
        if index >= 0:
            self.cmb_profile.setCurrentIndex(index)
        self.cmb_profile.blockSignals(False)

    def on_profile_changed(self, name):
        if not name or name == self._profile:
            return
        self._profile = name
        tprefs.set_active(name)
        tokens = tprefs.load_profile(name)
        self.load_tokens(tokens)
        self._log("[OK] Token profile : switched to '{0}' ({1} token(s)).".format(
            name, len(tokens)))

    def _ask_profile_name(self, title, label, text=""):
        raw, ok = QInputDialog.getText(self, title, label, text=text)
        if not ok:
            return None
        name = tprefs.sanitize_name(raw)
        if not name:
            return None
        if name in tprefs.list_profiles():
            QMessageBox.warning(self, "Token", "Profile '{0}' already exists.".format(name))
            return None
        return name

    def on_new_profile(self):
        name = self._ask_profile_name("New Profile", "Profile name (copies the tokens shown now):")
        if not name:
            return
        self.create_profile(name)

    def create_profile(self, name):
        """지금 칸을 복사해 새 프로파일을 만들고 그쪽으로 바꾼다."""
        tprefs.save_profile(name, self.tokens())
        tprefs.set_active(name)
        self._profile = name
        self._refresh_profiles()
        self._log("[OK] Token profile : created '{0}'.".format(name))

    def on_rename_profile(self):
        old = self._profile
        new = self._ask_profile_name("Rename Profile", "New name:", text=old)
        if not new:
            return
        tprefs.rename_profile(old, new)
        self._profile = new
        self._refresh_profiles()
        self._log("[OK] Token profile : renamed '{0}' -> '{1}'.".format(old, new))

    def on_delete_profile(self):
        name = self._profile
        if len(tprefs.list_profiles()) <= 1:
            QMessageBox.information(self, "Token", "At least one profile must remain.")
            return
        if QMessageBox.question(
                self, "Token", "Delete profile '{0}'?".format(name)) != QMessageBox.Yes:
            return
        self.delete_profile(name)

    def delete_profile(self, name):
        tprefs.delete_profile(name)
        self._profile = tprefs.list_profiles()[0]
        tprefs.set_active(self._profile)
        self._refresh_profiles()
        self.load_tokens(tprefs.load_profile(self._profile))
        self._log("[OK] Token profile : deleted '{0}'.".format(name))

    # ================================================================
    # Rename
    # ================================================================

    def on_rename(self):
        objects = self.tsl.get_all_items()
        if not objects:
            self._log("[WARN] Objects list is empty. Use Select Base first.")
            return
        tokens = self.tokens()
        errors = token_ops.validate(tokens)
        if errors:
            for error in errors:
                self._log("[WARN] " + error)
            return

        with core.undo_chunk():
            count, notes = core.rename_tokens(objects, tokens)
        for note in notes:
            self._log(note)
        self._log("Token : {0} node(s) renamed (profile '{1}').".format(count, self._profile))

    # ================================================================
    # Helper
    # ================================================================

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
