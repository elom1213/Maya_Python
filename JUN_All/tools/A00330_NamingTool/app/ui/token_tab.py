# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-02
# A00330_NamingTool - Rename > Token 탭 (v01.07, 구 Naming Dyn)
#
# 토큰을 `_` 로 이어 오브젝트와 그 transform 자손의 이름을 한 번에 짓는다.
#   - 토큰 칸마다 **규칙**을 고른다.
#       Custom    : 적은 글자 그대로
#       Numbering : Start 부터 올라가는 번호 + Pad 0 자리수
#   - 토큰 칸은 **개수가 자유**다. 칸 머리(Token N)를 눌러 고른 뒤
#       Add Token    : 고른 칸 **오른쪽**에 새 칸
#       Delete Token : 고른 칸 삭제 (마지막 한 칸은 남긴다)
#     칸이 창보다 많아지면 가로 스크롤.
#   - **Profile** : 토큰 규칙 한 벌을 json 으로 저장/불러오기 (A00145 Attribute > Create 와 같은 구성).
#     칸을 고치면 **현재 프로파일에 바로 저장**된다. 새 프로파일은 지금 칸을 복사해서 만든다.
#
# v01.10 : Profile + Tokens 화면은 공용 위젯 **`Framework.qt.MOD_tokenName_qt_v01`** 로 올렸다
#          (A00480_FileTool Export > Naming 과 같은 화면). 이 탭은 Objects 리스트 + 위젯 + Rename 버튼.
# 번호를 세는 규칙 · 검사는 core.token_ops(→ Framework.core.token_naming), 파일은 core.token_profile_prefs.
#
# v01.15 : Objects 리스트 오른쪽에 **Preview 표** (Quick Rename > Insert 와 같은 모양).
#          Rename 을 누르면 바뀔 노드 전부(오브젝트 + transform 자손)를 계층 그대로 보여 주고
#          Current / New name / Status 를 적는다. 리스트나 토큰이 바뀌면 다시 계산한다 - 씬은 그대로.
#          계산은 core.preview_tokens (rename_tokens 와 같은 순서 · 같은 이름).

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.core import log_levels
from Framework.themes.theme_manager import ThemeManager
from Framework.qt.MOD_tokenName_qt_v01 import JUN_mod_tokenName_qt_v01

from tools.A00330_NamingTool.app import core
from tools.A00330_NamingTool.app.core import token_ops
from tools.A00330_NamingTool.app.core import token_profile_prefs as tprefs
from tools.A00330_NamingTool.app.config import dev_mode


class TokenTab(QWidget):

    #: 미리보기 표 컬럼
    COL_NAME, COL_NEW, COL_STATUS = range(3)

    #: 토큰을 칠 때마다 씬을 조회하지 않도록 미리보기 갱신을 모은다 (ms)
    PREVIEW_DELAY_MS = 150

    def __init__(self, log=None, parent=None):
        super(TokenTab, self).__init__(parent)
        self._log_callback = log
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(self.PREVIEW_DELAY_MS)
        self._preview_timer.timeout.connect(self.update_preview)
        self.build_ui()
        self.update_preview()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        # Objects 리스트 (Select / Add / Del / Up / Down / Sort)
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Base",
            log_callback=self._log)

        # Preview 표 (v01.15) - Quick Rename > Insert 의 Preview 와 같은 모양
        self.preview_tree = QTreeWidget()
        self.preview_tree.setColumnCount(3)
        self.preview_tree.setHeaderLabels(["Current", "New name", "Status"])
        self.preview_tree.setAlternatingRowColors(True)
        self.preview_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.preview_tree.setToolTip(
            "What each object and its transform descendants will be renamed to.\n"
            "Nothing is renamed until you press Rename.")

        preview_box = QWidget()
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(2, 2, 2, 2)
        lbl_preview = QLabel("Preview")
        font = lbl_preview.font()
        font.setBold(True)
        lbl_preview.setFont(font)
        preview_layout.addWidget(lbl_preview)
        preview_layout.addWidget(self.preview_tree, 1)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.tsl)
        split.addWidget(preview_box)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        root.addWidget(split, stretch=1)

        # 리스트가 바뀌면(Select / Add / Del / Up / Down / Sort) 미리보기를 다시 그린다
        model = self.tsl.list_widget.model()
        for signal in (model.rowsInserted, model.rowsRemoved,
                       model.rowsMoved, model.modelReset):
            signal.connect(self.schedule_preview)

        # Profile + Tokens (공용 위젯).
        # v01.14 : 개발자 모드가 아니면(배포본) 정해진 규칙을 못 바꾼다 - Enum 칸의 Values... 가 없고,
        #          Enum 칸은 규칙 콤보가 잠기고 지울 수 없다. 값 중에서 고르기만 한다.
        self.token_widget = JUN_mod_tokenName_qt_v01(
            tprefs.STORE, log=self._log, log_prefix="Token",
            rules_editable=dev_mode.is_dev_mode())
        self.token_widget.tokensChanged.connect(self.schedule_preview)
        root.addWidget(self.token_widget)

        self.btn_rename = QPushButton("Rename")
        self.btn_rename.setMinimumHeight(32)
        self.btn_rename.setToolTip(
            "Rename each listed object and its transform descendants with the tokens,\n"
            "joined by '_'. With two Numbering tokens the first counts objects and the\n"
            "second counts nodes inside each object (restarting per object).\n"
            "One undo step.")
        self.btn_rename.clicked.connect(self.on_rename)
        root.addWidget(self.btn_rename)

    def tokens(self):
        return self.token_widget.tokens()

    # ================================================================
    # Preview (v01.15)
    # ================================================================

    def schedule_preview(self, *args):
        self._preview_timer.start()

    def update_preview(self):
        """미리보기 표를 다시 채운다. 씬은 건드리지 않는다."""
        self._preview_timer.stop()
        self.preview_tree.clear()
        objects = self.tsl.get_all_nodes()
        if not objects:
            return
        rows, _errors = core.preview_tokens(objects, self.tokens())

        dark = ThemeManager.is_dark_theme()
        st = core.set_rename_ops
        colors = {
            st.ST_OK: log_levels.color("OK", dark),
            st.ST_COLLISION: log_levels.color("WARN", dark),
            st.ST_SAME: log_levels.color("SKIP", dark),
        }
        error_color = log_levels.color("ERROR", dark)

        items = {}      # 롱 경로 -> 표 항목 (자손을 그 부모 밑에 단다)
        for row in rows:
            status = row["status"]
            shows_new = status in st.APPLICABLE or status == st.ST_SAME
            item = QTreeWidgetItem([
                row["old_name"],
                row["new_name"] if shows_new else "",
                status if not row["note"] else "{0} - {1}".format(status, row["note"])])
            item.setToolTip(self.COL_NAME, row["path"])
            item.setToolTip(self.COL_NEW, row["new_name"])
            color = colors.get(status, error_color)
            if color:
                item.setForeground(self.COL_STATUS, QBrush(QColor(color)))
            parent_item = items.get(row["parent"])
            if parent_item is not None and not row["root"]:
                parent_item.addChild(item)
            else:
                self.preview_tree.addTopLevelItem(item)
            items[row["path"]] = item
        self.preview_tree.expandAll()
        for col in range(3):
            self.preview_tree.resizeColumnToContents(col)

    # ================================================================
    # Rename
    # ================================================================

    def on_rename(self):
        # v01.15 : 표시 이름이 아니라 UUID 로 찾은 **지금** 경로 - Rename 뒤에도 리스트가 노드를 놓치지 않는다
        objects = self.tsl.get_all_nodes()
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
        self._log("Token : {0} node(s) renamed (profile '{1}').".format(
            count, self.token_widget.profile()))
        # 리스트를 새 이름으로 다시 채운다 (Insert 탭과 같다) -> 미리보기도 따라 갱신된다
        self.tsl.set_items(core.insert_ops.display_names(self.tsl.get_all_nodes()))
        self.update_preview()

    # ================================================================
    # Helper
    # ================================================================

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
