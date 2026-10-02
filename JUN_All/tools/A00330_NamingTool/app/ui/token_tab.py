# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-28
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

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.MOD_tokenName_qt_v01 import JUN_mod_tokenName_qt_v01

from tools.A00330_NamingTool.app import core
from tools.A00330_NamingTool.app.core import token_ops
from tools.A00330_NamingTool.app.core import token_profile_prefs as tprefs
from tools.A00330_NamingTool.app.config import dev_mode


class TokenTab(QWidget):

    def __init__(self, log=None, parent=None):
        super(TokenTab, self).__init__(parent)
        self._log_callback = log
        self.build_ui()

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

        # Profile + Tokens (공용 위젯).
        # v01.14 : 개발자 모드가 아니면(배포본) 정해진 규칙을 못 바꾼다 - Enum 칸의 Values... 가 없고,
        #          Enum 칸은 규칙 콤보가 잠기고 지울 수 없다. 값 중에서 고르기만 한다.
        self.token_widget = JUN_mod_tokenName_qt_v01(
            tprefs.STORE, log=self._log, log_prefix="Token",
            rules_editable=dev_mode.is_dev_mode())
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
        self._log("Token : {0} node(s) renamed (profile '{1}').".format(
            count, self.token_widget.profile()))

    # ================================================================
    # Helper
    # ================================================================

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
