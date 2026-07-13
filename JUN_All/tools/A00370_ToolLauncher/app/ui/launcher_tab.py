# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00370_ToolLauncher - "Buttons" tab (Qt, in-Maya)
#
# 사용자가 카테고리와 툴 버튼을 직접 만들고, 버튼을 누르면 그 버튼에 저장된 툴 폴더
# 경로의 툴이 마야에서 실행(팝업)된다. (구성/편집 방식은 A00340_SelectionTool 의
# Buttons 탭을 이식했다. 버튼이 '오브젝트 목록' 대신 '실행할 툴 폴더 경로' 를 담는
# 점만 다르다.)
#
#   - 상단 "Profile" 그룹 : 툴 숏컷 세트를 상황별 JSON 으로 나눠 관리.
#   - 상단 "Create" 그룹  : [Category] / [Tool] 버튼 + [Reload on launch] 체크.
#       * Category : 새 카테고리(QGroupBox) 생성.
#       * Tool     : 툴 폴더를 지정해 새 실행 버튼으로 만든다(Browse 로 폴더 선택).
#   - 각 카테고리는 QGroupBox, 그 안에 툴 버튼이 쌓인다.
#   - 버튼 클릭     : 저장된 경로의 툴을 import 해 run() 으로 실행.
#   - 추가/삭제/정렬/이름변경/경로변경 : 우클릭 컨텍스트 메뉴로 한다.
#   - 색 지정       : 버튼 우클릭 'Set Color...'(팔레트+스포이드)로 개별 지정.
#                     'Color Select' 모드를 켜면 카테고리를 넘나들며 여러 버튼을
#                     체크해 'Apply Color...'로 한 번에 칠한다('Clear Color'로 해제).

import os

from Framework.qt.qt import (
    QWidget,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QToolButton,
    QScrollArea,
    QSplitter,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QColorDialog,
    QColor,
    QIcon,
    QSize,
    QMenu,
    Qt,
)

from ..core import prefs as prefs_mod
from ..core import tool_launcher


TITLE = "Tool Launcher"

# 툴 버튼의 고정 높이(px). 아이콘은 이 높이와 같은 변의 정사각형으로 버튼 왼쪽에 둔다.
BUTTON_HEIGHT = 34

# 색이 지정되지 않은(=아직 한 번도 칠하지 않은) 버튼의 컬러 다이얼로그 시작값.
DEFAULT_PICK_HEX = "#5a5a5a"

# 색칠 모드에서 '체크됨' 을 표시하는 강조 테두리 색(색 유무와 무관하게 일관).
CHECK_HILITE_HEX = "#4a90d9"

# 색이 없는(테마 기본) 버튼이 체크됐을 때만 테두리로 강조하는 스타일시트.
CHECK_ONLY_QSS = (
    "QPushButton:checked {{ border: 2px solid {c}; }}".format(c=CHECK_HILITE_HEX)
)


def _contrast_text_hex(qcolor):
    """배경색(qcolor) 위에서 잘 읽히는 글자색(검정/흰색) 을 밝기로 고른다."""
    lum = (qcolor.red() * 299 + qcolor.green() * 587 + qcolor.blue() * 114) / 1000.0
    return "#000000" if lum > 140 else "#FFFFFF"


def _button_stylesheet(hex_str):
    """버튼에 입힐 배경/글자/테두리/hover 스타일시트를 hex 색 하나로 만든다.

    색칠 모드에서 checkable 로 바뀐 버튼이 체크되면 :checked 규칙으로 강조
    테두리가 뜬다(일반 모드에서는 checkable 이 아니라 규칙이 적용되지 않는다).
    """
    bg = QColor(hex_str)
    text = _contrast_text_hex(bg)
    border = bg.darker(150).name()
    hover = bg.lighter(115).name()
    pressed = bg.darker(115).name()
    return (
        "QPushButton {{"
        " background-color: {bg}; color: {text};"
        " border: 1px solid {border}; border-radius: 3px; padding: 4px; }}"
        "QPushButton:hover {{ background-color: {hover}; }}"
        "QPushButton:pressed {{ background-color: {pressed}; }}"
        "QPushButton:checked {{ border: 2px solid {check}; }}"
    ).format(bg=bg.name(), text=text, border=border, hover=hover,
             pressed=pressed, check=CHECK_HILITE_HEX)


class CollapsibleBox(QWidget):
    """제목 바를 클릭하면 내용을 접었다 펼 수 있는 섹션.

    상단 컨트롤(Profile/Create/Color/Log)을 각각 이 위젯으로 감싸, 필요 없는 칸을
    접어 아래 버튼 모음에 공간을 더 내줄 수 있게 한다.
    """

    def __init__(self, title, content_layout=None, expanded=True, parent=None):
        super().__init__(parent)

        # 화살표(▾/▸) + 제목의 클릭형 헤더. 체크 상태 = 펼침 여부.
        self._title = title
        self._header = QToolButton()
        self._header.setText(title)
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self._header.setAutoRaise(True)
        self._header.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; padding: 2px; }")
        self._header.toggled.connect(self._on_toggled)
        # 외부에서 접힘/펼침을 감지할 수 있도록 헤더 토글 시그널을 그대로 노출.
        self.toggled = self._header.toggled

        self._content = QWidget()
        if content_layout is not None:
            self._content.setLayout(content_layout)
        self._content.setVisible(expanded)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header)
        outer.addWidget(self._content)

    def _on_toggled(self, expanded):
        self._header.setArrowType(
            Qt.DownArrow if expanded else Qt.RightArrow)
        self._content.setVisible(expanded)


class AddToolButtonDialog(QDialog):
    """툴 버튼 생성: 카테고리 선택 → 버튼 이름 → 툴 폴더 경로(Browse)."""

    def __init__(self, category_names, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Tool Button")
        self.setMinimumWidth(440)

        form = QFormLayout(self)

        # 1) 어느 카테고리에 넣을지
        self.cmb_category = QComboBox()
        self.cmb_category.addItems(category_names)
        form.addRow("Add to category:", self.cmb_category)

        # 2) 툴 폴더 경로(+ Browse). 폴더를 고르면 이름 칸이 비어 있을 때 자동 채움.
        path_row = QHBoxLayout()
        self.ipf_path = QLineEdit()
        self.ipf_path.setPlaceholderText(
            r"e.g. C:\...\JUN_All\tools\A00080_KWI_creator_V03")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._on_browse)
        path_row.addWidget(self.ipf_path, stretch=1)
        path_row.addWidget(btn_browse)
        form.addRow("Tool folder:", path_row)

        # 3) 버튼 이름
        self.ipf_name = QLineEdit()
        self.ipf_name.setPlaceholderText("(defaults to the folder name)")
        form.addRow("Button name:", self.ipf_name)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_browse(self):
        start = self.ipf_path.text().strip() or ""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Tool Folder", start)
        if not folder:
            return
        self.ipf_path.setText(folder)
        # 이름이 비어 있으면 폴더명으로 자동 채움.
        if not self.ipf_name.text().strip():
            self.ipf_name.setText(tool_launcher.display_name(folder))

    def values(self):
        """(category, name, path) — name/path 는 strip 된 값. name 이 비면 폴더명 사용."""
        path = self.ipf_path.text().strip()
        name = self.ipf_name.text().strip() or tool_launcher.display_name(path)
        return (self.cmb_category.currentText(), name, path)


class LauncherTab(QWidget):

    def __init__(self, log_callback=None, log_widget=None, parent=None):
        super().__init__(parent)

        # 로그/상태 보고용 콜백(없으면 무시). main_window 의 공용 로그로 흘려보낸다.
        self._log = log_callback or (lambda _msg: None)

        # main_window 가 만든 로그 위젯. 있으면 상단 컨트롤의 접이식 'Log' 섹션에 담는다.
        self._log_widget = log_widget

        # 활성 프로파일과 그 데이터를 읽는다(없으면 Default 자동 생성).
        self._profile = prefs_mod.get_active()
        self._data = prefs_mod.load_profile(self._profile)

        # 색칠 모드 상태: 켜지면 버튼이 체크형으로 바뀌어 여러 개를 골라 한 번에 칠한다.
        # 체크된 버튼은 (category, button) 이름 쌍으로 들고 있어 재렌더 후에도 유지된다.
        self._color_mode = False
        self._checked = set()
        self._color_buttons = []

        self._build_ui()
        self._refresh_profiles()
        self._render_categories()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        # 컨트롤(위)과 버튼 모음(아래)을 드래그로 비율 조절하는 상하 스플리터로 나눈다.
        splitter = QSplitter(Qt.Vertical)
        self._splitter = splitter

        splitter.addWidget(self._build_controls_pane())
        splitter.addWidget(self._build_buttons_pane())

        # 컨트롤은 필요한 만큼만, 버튼 모음이 남은 공간을 차지하도록.
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setSizes([230, 430])

        root.addWidget(splitter)

    def _build_controls_pane(self):
        """상단 pane: Profile/Create/Color/Log 를 '하나의' 접이식 박스로 묶는다."""
        inner = QVBoxLayout()
        inner.setContentsMargins(6, 2, 6, 6)
        inner.setSpacing(4)

        inner.addWidget(self._build_env_group())
        inner.addWidget(self._build_profile_group())
        inner.addWidget(self._build_create_group())
        inner.addWidget(self._build_color_group())
        if self._log_widget is not None:
            inner.addWidget(self._build_log_group())

        self._controls_box = CollapsibleBox("Controls", inner)
        # 접으면 스플리터의 위 pane 도 헤더 높이로 줄여 버튼 영역에 공간을 넘긴다.
        self._controls_box.toggled.connect(self._on_controls_toggled)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._controls_box)
        return scroll

    def _on_controls_toggled(self, expanded):
        """Controls 박스를 접으면 위 pane 을 헤더만 남기고 아래 pane 을 넓힌다."""
        splitter = getattr(self, "_splitter", None)
        if splitter is None:
            return
        sizes = splitter.sizes()
        total = sum(sizes) or 1
        if expanded:
            # 접기 직전 높이로 복원(없으면 기본값).
            top = getattr(self, "_controls_expanded_h", 230)
            top = min(top, max(40, total - 40))
            splitter.setSizes([top, max(40, total - top)])
        else:
            self._controls_expanded_h = sizes[0]
            header_h = self._controls_box._header.sizeHint().height() + 6
            splitter.setSizes([header_h, max(40, total - header_h)])

    def _build_buttons_pane(self):
        """하단 pane: 생성한 카테고리/버튼 모음(계속 늘어나므로 스크롤)."""
        self._cat_container = QWidget()
        self._cat_layout = QVBoxLayout(self._cat_container)
        self._cat_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._cat_container)
        return scroll

    def _build_log_group(self):
        # main_window 의 로그 위젯을 'Log' 그룹에 담는다(컨트롤 박스와 함께 접힌다).
        group = QGroupBox("Log")
        lay = QVBoxLayout(group)
        lay.addWidget(self._log_widget)
        return group

    def _build_env_group(self):
        # 환경(이 PC 의 JUN_All 루트) 지정 + 모든 버튼 경로 재설정(Refresh Paths).
        # 버튼 경로는 PC 마다 다른 절대경로로 저장된다. 다른 PC 에서 프로파일을 열면
        # 이 루트를 확인/지정하고 'Refresh Paths' 를 눌러 모든 버튼을 이 PC 기준으로
        # 한 번에 복구/공유할 수 있다. 필드 기본값은 자동 감지한 현재 PC 의 JUN_All.
        group = QGroupBox("Environment")
        col = QVBoxLayout(group)

        row = QHBoxLayout()
        row.addWidget(QLabel("JUN_All Root:"))

        self.ipf_root = QLineEdit()
        self.ipf_root.setText(tool_launcher.jun_all_root())
        self.ipf_root.setToolTip(
            "This PC's JUN_All folder. Buttons store absolute paths, so on a "
            "different PC set this, then click 'Refresh Paths' to re-point "
            "every button to this PC's tools.")

        btn_browse = QPushButton("Browse...")
        btn_browse.setToolTip("Pick this PC's JUN_All folder")
        btn_browse.clicked.connect(self.on_browse_root)

        row.addWidget(self.ipf_root, stretch=1)
        row.addWidget(btn_browse)
        col.addLayout(row)

        action_row = QHBoxLayout()
        btn_detect = QPushButton("Detect")
        btn_detect.setToolTip(
            "Fill the field with the JUN_All this launcher is running from")
        btn_detect.clicked.connect(self.on_detect_root)

        btn_refresh = QPushButton("Refresh Paths")
        btn_refresh.setToolTip(
            "Re-point every button in every profile to the JUN_All Root above "
            "(fixes buttons made on another PC)")
        btn_refresh.clicked.connect(self.on_refresh_paths)

        action_row.addWidget(btn_detect)
        action_row.addStretch(1)
        action_row.addWidget(btn_refresh)
        col.addLayout(action_row)

        return group

    def _build_profile_group(self):
        # 프로파일(상황별로 JSON 별로 나뉜 툴 숏컷 묶음) 선택 + 관리.
        group = QGroupBox("Profile")
        row = QHBoxLayout(group)

        self.cmb_profile = QComboBox()
        self.cmb_profile.setToolTip("Active profile (each is its own JSON)")
        self.cmb_profile.currentTextChanged.connect(self.on_profile_changed)

        btn_new = QPushButton("New")
        btn_new.setToolTip("Create a new profile")
        btn_new.clicked.connect(self.on_new_profile)

        btn_rename = QPushButton("Rename")
        btn_rename.setToolTip("Rename the current profile")
        btn_rename.clicked.connect(self.on_rename_profile)

        btn_delete = QPushButton("Delete")
        btn_delete.setToolTip("Delete the current profile")
        btn_delete.clicked.connect(self.on_delete_profile)

        row.addWidget(self.cmb_profile, stretch=1)
        row.addWidget(btn_new)
        row.addWidget(btn_rename)
        row.addWidget(btn_delete)

        return group

    def _build_create_group(self):
        group = QGroupBox("Create")
        row = QHBoxLayout(group)

        btn_category = QPushButton("Category")
        btn_category.setToolTip("Create a new category")
        btn_category.clicked.connect(self.on_create_category)

        btn_tool = QPushButton("Tool")
        btn_tool.setToolTip(
            "Add a launch button for a tool folder (pick it with Browse)")
        btn_tool.clicked.connect(self.on_create_tool_button)

        # 버튼 클릭 시 툴을 리로드하고 띄울지(dev). 셸프 버튼과 동일하게 기본 ON.
        self.chk_reload = QCheckBox("Reload on launch")
        self.chk_reload.setChecked(True)
        self.chk_reload.setToolTip(
            "Re-import the tool before showing it (matches the shelf button; "
            "turn off to just re-show the already-loaded tool).")

        row.addWidget(btn_category)
        row.addWidget(btn_tool)
        row.addStretch(1)
        row.addWidget(self.chk_reload)

        return group

    def _build_color_group(self):
        # 색칠 모드: 카테고리를 넘나들며 여러 버튼을 골라 한 색으로 칠한다.
        group = QGroupBox("Color")
        row = QHBoxLayout(group)

        # 모드 토글. 켜면 버튼이 체크형이 되고 클릭이 '실행' 대신 '체크'로 바뀐다.
        self.chk_color_mode = QCheckBox("Color Select")
        self.chk_color_mode.setToolTip(
            "Pick multiple buttons across categories (click to check), "
            "then apply one color to all of them at once.")
        self.chk_color_mode.toggled.connect(self.on_color_mode_toggled)

        # 체크된 버튼들에 색을 지정 / 색을 지운다. 모드가 켜져 있을 때만 활성.
        self.btn_apply_color = QPushButton("Apply Color...")
        self.btn_apply_color.setToolTip(
            "Apply a picked color to all checked buttons")
        self.btn_apply_color.clicked.connect(self.on_apply_color_to_checked)
        self.btn_apply_color.setEnabled(False)

        self.btn_clear_color = QPushButton("Clear Color")
        self.btn_clear_color.setToolTip(
            "Reset all checked buttons to the default (theme) style")
        self.btn_clear_color.clicked.connect(self.on_clear_color_from_checked)
        self.btn_clear_color.setEnabled(False)

        row.addWidget(self.chk_color_mode)
        row.addStretch(1)
        row.addWidget(self.btn_apply_color)
        row.addWidget(self.btn_clear_color)

        return group

    # ============================================================ rendering

    def _render_categories(self):
        # 재렌더하면 옛 체크형 버튼 위젯은 폐기되므로 목록을 비우고 다시 채운다.
        self._color_buttons = []
        # 기존 위젯 제거 후 데이터 기준으로 다시 그린다.
        while self._cat_layout.count():
            item = self._cat_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        categories = self._data.get("categories", [])
        if not categories:
            hint = QLabel("No categories yet — click 'Category' to create one.")
            hint.setEnabled(False)
            self._cat_layout.addWidget(hint)
            return

        for cat in categories:
            self._cat_layout.addWidget(self._build_category_box(cat))

    def _build_category_box(self, cat):
        box = QGroupBox(cat["name"])
        box.setContextMenuPolicy(Qt.CustomContextMenu)
        cat_name = cat["name"]
        box.customContextMenuRequested.connect(
            lambda pos, b=box, n=cat_name: self._show_category_menu(n, b, pos)
        )

        v = QVBoxLayout(box)

        buttons = cat.get("buttons", [])
        if not buttons:
            empty = QLabel("(no buttons — use 'Tool' to add)")
            empty.setEnabled(False)
            v.addWidget(empty)
        else:
            for btn_data in buttons:
                v.addWidget(self._build_tool_button(cat_name, btn_data))

        return box

    def _build_tool_button(self, cat_name, btn_data):
        path = btn_data.get("path", "")
        # 버튼은 고정 높이 — 왼쪽 정사각형 아이콘의 한 변과 같게 맞춘다.
        btn = QPushButton(btn_data["name"])
        btn.setFixedHeight(BUTTON_HEIGHT)

        # 툴팁에 경로와 존재 여부를 보여준다.
        ok, _msg = tool_launcher.validate(path)
        tip = path or "(no path set)"
        if path and not ok:
            tip += "\n[!] " + _msg
        btn.setToolTip(tip)

        name = btn_data["name"]
        color_hex = btn_data.get("color")

        if self._color_mode:
            # 색칠 모드: 버튼을 체크형으로. 클릭은 '실행' 대신 '체크 토글'.
            btn.setCheckable(True)
            # setChecked 는 아래 toggled 연결 '전'에 호출해야 초기 복원이 콜백을 안 부른다.
            btn.setChecked((cat_name, name) in self._checked)
            btn.setStyleSheet(
                _button_stylesheet(color_hex) if color_hex else CHECK_ONLY_QSS)
            btn.toggled.connect(
                lambda checked, c=cat_name, n=name:
                self._on_color_check(c, n, checked))
            self._color_buttons.append((btn, cat_name, name))
        else:
            # 일반 모드: 지정색이 있으면 입히고, 클릭하면 툴을 실행한다.
            if color_hex:
                btn.setStyleSheet(_button_stylesheet(color_hex))
            btn.clicked.connect(
                lambda *_a, c=cat_name, n=name: self._on_button_clicked(c, n))

        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, w=btn, c=cat_name, n=name:
            self._show_button_menu(c, n, w, pos)
        )

        # 툴 폴더의 아이콘(icon/<폴더명>.png 등)이 없으면 버튼만 그대로 반환.
        icon_path = tool_launcher.find_icon(path)
        if not icon_path:
            return btn

        # 아이콘을 버튼 '안'이 아니라 '왼쪽'에 정사각형(버튼 높이)으로 크게 배치한다.
        icon_label = QLabel()
        icon_label.setFixedSize(BUTTON_HEIGHT, BUTTON_HEIGHT)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setToolTip(tip)
        pix = QIcon(icon_path).pixmap(QSize(BUTTON_HEIGHT, BUTTON_HEIGHT))
        if not pix.isNull():
            icon_label.setPixmap(pix)

        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        h.addWidget(icon_label)
        h.addWidget(btn, stretch=1)
        return row

    # ========================================================= data helpers

    def _find_category(self, name):
        for cat in self._data.get("categories", []):
            if cat["name"] == name:
                return cat
        return None

    def _find_button(self, cat_name, btn_name):
        cat = self._find_category(cat_name)
        if cat is None:
            return None
        return next(
            (b for b in cat.get("buttons", []) if b["name"] == btn_name), None)

    def _category_names(self):
        return [cat["name"] for cat in self._data.get("categories", [])]

    def _save_and_render(self):
        prefs_mod.save_profile(self._profile, self._data)
        self._render_categories()

    # ============================================================= profiles

    def _refresh_profiles(self):
        """콤보를 현재 프로파일 목록으로 다시 채우고 활성 항목을 선택한다."""
        self.cmb_profile.blockSignals(True)
        self.cmb_profile.clear()
        self.cmb_profile.addItems(prefs_mod.list_profiles())
        idx = self.cmb_profile.findText(self._profile)
        if idx >= 0:
            self.cmb_profile.setCurrentIndex(idx)
        self.cmb_profile.blockSignals(False)

    def on_profile_changed(self, name):
        """콤보에서 다른 프로파일을 고르면 그 프로파일을 로드한다."""
        if not name or name == self._profile:
            return
        self._profile = name
        prefs_mod.set_active(name)
        self._data = prefs_mod.load_profile(name)
        self._checked.clear()  # 프로파일이 바뀌면 체크 상태는 무효
        self._render_categories()
        self._log("Switched to profile '{0}'.".format(name))

    def on_new_profile(self):
        raw, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if not ok:
            return
        name = prefs_mod.sanitize_name(raw)
        if not name:
            return
        if name in prefs_mod.list_profiles():
            QMessageBox.warning(
                self, TITLE, "Profile '{0}' already exists.".format(name))
            return

        prefs_mod.save_profile(name, {"categories": []})
        prefs_mod.set_active(name)
        self._profile = name
        self._data = prefs_mod.load_profile(name)
        self._checked.clear()
        self._refresh_profiles()
        self._render_categories()

    def on_rename_profile(self):
        old = self._profile
        raw, ok = QInputDialog.getText(
            self, "Rename Profile", "New name:", text=old
        )
        if not ok:
            return
        new = prefs_mod.sanitize_name(raw)
        if not new or new == old:
            return
        if new in prefs_mod.list_profiles():
            QMessageBox.warning(
                self, TITLE, "Profile '{0}' already exists.".format(new))
            return

        prefs_mod.rename_profile(old, new)
        self._profile = new
        self._refresh_profiles()

    def on_delete_profile(self):
        name = self._profile
        if len(prefs_mod.list_profiles()) <= 1:
            QMessageBox.information(
                self, TITLE, "At least one profile must remain.")
            return
        if QMessageBox.question(
            self, TITLE,
            "Delete profile '{0}' and all its buttons?".format(name)
        ) != QMessageBox.Yes:
            return

        prefs_mod.delete_profile(name)
        # 남은 프로파일 중 첫 번째로 전환.
        remaining = prefs_mod.list_profiles()
        self._profile = remaining[0]
        prefs_mod.set_active(self._profile)
        self._data = prefs_mod.load_profile(self._profile)
        self._checked.clear()
        self._refresh_profiles()
        self._render_categories()

    # ============================================================ environment

    def on_detect_root(self):
        """필드를 이 런처가 실행 중인 JUN_All 경로로 채운다(자동 감지)."""
        self.ipf_root.setText(tool_launcher.jun_all_root())
        self._log("Detected JUN_All Root: {0}".format(self.ipf_root.text()))

    def on_browse_root(self):
        """이 PC 의 JUN_All 폴더를 탐색기로 고른다."""
        start = self.ipf_root.text().strip() or ""
        folder = QFileDialog.getExistingDirectory(
            self, "Select JUN_All Folder", start)
        if folder:
            self.ipf_root.setText(tool_launcher.normalize_path(folder))

    def on_refresh_paths(self):
        """JUN_All Root 필드 기준으로 모든 프로파일의 버튼 경로를 재설정한다.

        다른 PC 에서 만든 절대경로 버튼들을 이 PC(또는 지정 루트) 기준으로 한 번에
        복구/공유하기 위한 것. 'tools' 앵커가 없는 경로는 손대지 않는다.
        """
        root = self.ipf_root.text().strip()
        if not root:
            QMessageBox.warning(self, TITLE, "JUN_All Root is empty.")
            return
        if not os.path.isdir(root):
            QMessageBox.warning(
                self, TITLE, "Folder not found:\n{0}".format(root))
            return
        if not os.path.isdir(os.path.join(root, "tools")):
            if QMessageBox.question(
                self, TITLE,
                "No 'tools' subfolder under:\n{0}\n\n"
                "This may not be a JUN_All root. Refresh anyway?".format(root)
            ) != QMessageBox.Yes:
                return

        stats = prefs_mod.rebase_all_profiles(root)

        # 활성 프로파일 데이터도 디스크에서 바뀌었을 수 있으니 다시 읽고 그린다.
        self._data = prefs_mod.load_profile(self._profile)
        self._checked.clear()
        self._render_categories()

        self._log(
            "Refresh Paths: {changed} re-pointed, {unchanged} already OK, "
            "{skipped} skipped (no 'tools' anchor) across {profiles} "
            "profile(s).".format(**stats))
        QMessageBox.information(
            self, TITLE,
            "Re-pointed {changed} button(s) to:\n{root}\n\n"
            "Already OK: {unchanged}\n"
            "Skipped (outside JUN_All/tools): {skipped}\n"
            "Profiles updated: {profiles}".format(root=root, **stats))

    # ============================================================== create

    def on_create_category(self):
        name, ok = QInputDialog.getText(
            self, "New Category", "Category name:"
        )
        if not ok:
            return

        name = name.strip()
        if not name:
            return

        if self._find_category(name):
            QMessageBox.warning(
                self, TITLE, "Category '{0}' already exists.".format(name))
            return

        self._data["categories"].append({"name": name, "buttons": []})
        self._save_and_render()

    def on_create_tool_button(self):
        names = self._category_names()
        if not names:
            QMessageBox.information(self, TITLE, "Create a category first.")
            return

        # 카테고리 / 버튼 이름 / 경로를 한 다이얼로그에서 입력받는다(중복·오류 시 재시도).
        dlg = AddToolButtonDialog(names, self)
        while True:
            if dlg.exec_() != QDialog.Accepted:
                return

            cat_name, label, path = dlg.values()

            if not path:
                QMessageBox.warning(self, TITLE, "Tool folder path is required.")
                continue

            ok, msg = tool_launcher.validate(path)
            if not ok:
                QMessageBox.warning(self, TITLE, msg)
                continue

            if not label:
                QMessageBox.warning(self, TITLE, "Button name is required.")
                continue

            cat = self._find_category(cat_name)
            if cat is None:
                return
            if any(b["name"] == label for b in cat["buttons"]):
                QMessageBox.warning(
                    self, TITLE,
                    "Button '{0}' already exists in '{1}'."
                    .format(label, cat_name))
                continue

            break

        cat["buttons"].append(
            {"name": label, "path": tool_launcher.normalize_path(path)})
        self._save_and_render()
        self._log("Added tool button '{0}'.".format(label))

    # ============================================================ launch

    def _on_button_clicked(self, cat_name, btn_name):
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None:
            return

        path = btn_data.get("path", "")
        reload_module = self.chk_reload.isChecked()
        ok, msg = tool_launcher.launch(path, reload_module=reload_module)
        self._log(msg if ok else "[!] " + msg)

    # ========================================================= context menus

    def _show_category_menu(self, cat_name, box, pos):
        menu = QMenu(box)
        # 정렬 순서 변경(위/아래로 한 칸). 끝단에서는 비활성화한다.
        act_up = menu.addAction("Move Up")
        act_down = menu.addAction("Move Down")
        menu.addSeparator()
        act_rename = menu.addAction("Rename Category")
        act_delete = menu.addAction("Delete Category")

        cats = self._data.get("categories", [])
        idx = next((i for i, c in enumerate(cats) if c["name"] == cat_name), -1)
        act_up.setEnabled(idx > 0)
        act_down.setEnabled(0 <= idx < len(cats) - 1)

        chosen = menu.exec_(box.mapToGlobal(pos))
        if chosen == act_up:
            self._move_category(cat_name, -1)
        elif chosen == act_down:
            self._move_category(cat_name, +1)
        elif chosen == act_rename:
            self._rename_category(cat_name)
        elif chosen == act_delete:
            self._delete_category(cat_name)

    def _show_button_menu(self, cat_name, btn_name, btn_widget, pos):
        menu = QMenu(btn_widget)
        # 카테고리 안에서 버튼 순서 변경(위/아래로 한 칸). 끝단에서는 비활성화한다.
        act_up = menu.addAction("Move Up")
        act_down = menu.addAction("Move Down")
        menu.addSeparator()
        act_rename = menu.addAction("Rename")
        act_path = menu.addAction("Change Path...")
        act_reveal = menu.addAction("Reveal in Explorer")
        menu.addSeparator()
        act_set_color = menu.addAction("Set Color...")
        act_reset_color = menu.addAction("Reset Color")
        menu.addSeparator()
        act_category = menu.addAction("Change Category")
        act_delete = menu.addAction("Delete")

        cat = self._find_category(cat_name)
        buttons = cat.get("buttons", []) if cat else []
        idx = next(
            (i for i, b in enumerate(buttons) if b["name"] == btn_name), -1
        )
        act_up.setEnabled(idx > 0)
        act_down.setEnabled(0 <= idx < len(buttons) - 1)
        # 색이 지정된 버튼만 되돌리기 가능.
        btn_data = self._find_button(cat_name, btn_name)
        act_reset_color.setEnabled(bool(btn_data and btn_data.get("color")))

        chosen = menu.exec_(btn_widget.mapToGlobal(pos))
        if chosen == act_up:
            self._move_button(cat_name, btn_name, -1)
        elif chosen == act_down:
            self._move_button(cat_name, btn_name, +1)
        elif chosen == act_rename:
            self._rename_button(cat_name, btn_name)
        elif chosen == act_path:
            self._change_button_path(cat_name, btn_name)
        elif chosen == act_reveal:
            self._reveal_button(cat_name, btn_name)
        elif chosen == act_set_color:
            self._set_button_color(cat_name, btn_name)
        elif chosen == act_reset_color:
            self._reset_button_color(cat_name, btn_name)
        elif chosen == act_category:
            self._change_button_category(cat_name, btn_name)
        elif chosen == act_delete:
            self._delete_button(cat_name, btn_name)

    # ============================================================ edit/delete

    def _move_category(self, name, delta):
        """카테고리를 목록에서 delta(-1=위, +1=아래)만큼 옮겨 정렬 순서를 바꾼다."""
        cats = self._data.get("categories", [])
        idx = next((i for i, c in enumerate(cats) if c["name"] == name), -1)
        if idx < 0:
            return
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(cats):
            return

        cats[idx], cats[new_idx] = cats[new_idx], cats[idx]
        self._save_and_render()

    def _move_button(self, cat_name, btn_name, delta):
        """카테고리 안에서 버튼을 delta(-1=위, +1=아래)만큼 옮겨 순서를 바꾼다."""
        cat = self._find_category(cat_name)
        if cat is None:
            return
        buttons = cat.get("buttons", [])
        idx = next(
            (i for i, b in enumerate(buttons) if b["name"] == btn_name), -1
        )
        if idx < 0:
            return
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(buttons):
            return

        buttons[idx], buttons[new_idx] = buttons[new_idx], buttons[idx]
        self._save_and_render()

    def _rename_category(self, old):
        new, ok = QInputDialog.getText(
            self, "Rename Category", "New name:", text=old
        )
        if not ok:
            return
        new = new.strip()
        if not new or new == old:
            return
        if self._find_category(new):
            QMessageBox.warning(
                self, TITLE, "Category '{0}' already exists.".format(new))
            return

        self._find_category(old)["name"] = new
        self._save_and_render()

    def _delete_category(self, name):
        cat = self._find_category(name)
        if cat is None:
            return

        count = len(cat.get("buttons", []))
        msg = "Delete category '{0}'".format(name)
        msg += " and its {0} button(s)?".format(count) if count else "?"
        if QMessageBox.question(self, TITLE, msg) != QMessageBox.Yes:
            return

        self._data["categories"] = [
            c for c in self._data["categories"] if c["name"] != name
        ]
        self._save_and_render()

    def _rename_button(self, cat_name, btn_name):
        cat = self._find_category(cat_name)
        if cat is None:
            return

        new, ok = QInputDialog.getText(
            self, "Rename", "New button name:", text=btn_name
        )
        if not ok:
            return
        new = new.strip()
        if not new or new == btn_name:
            return
        if any(b["name"] == new for b in cat["buttons"]):
            QMessageBox.warning(
                self, TITLE,
                "Button '{0}' already exists in '{1}'."
                .format(new, cat_name))
            return

        for b in cat["buttons"]:
            if b["name"] == btn_name:
                b["name"] = new
                break
        self._save_and_render()

    def _change_button_path(self, cat_name, btn_name):
        """버튼이 실행할 툴 폴더 경로를 다시 지정한다(우클릭 → Change Path...)."""
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None:
            return

        start = btn_data.get("path", "") or ""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Tool Folder", start)
        if not folder:
            return

        ok, msg = tool_launcher.validate(folder)
        if not ok:
            QMessageBox.warning(self, TITLE, msg)
            return

        btn_data["path"] = tool_launcher.normalize_path(folder)
        self._save_and_render()
        self._log("Set path of '{0}' to {1}.".format(
            btn_name, btn_data["path"]))

    def _reveal_button(self, cat_name, btn_name):
        """버튼의 툴 폴더를 탐색기에서 연다."""
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None:
            return
        ok, msg = tool_launcher.reveal_in_explorer(btn_data.get("path", ""))
        if not ok:
            self._log("[!] " + msg)

    def _change_button_category(self, cat_name, btn_name):
        """버튼을 다른 카테고리로 옮긴다(우클릭 → Change Category)."""
        src = self._find_category(cat_name)
        if src is None:
            return

        others = [n for n in self._category_names() if n != cat_name]
        if not others:
            QMessageBox.information(
                self, TITLE,
                "There is no other category to move to. Create one first.")
            return

        target_name, ok = QInputDialog.getItem(
            self, "Change Category",
            "Move '{0}' to category:".format(btn_name), others, 0, False)
        if not ok or not target_name:
            return

        target = self._find_category(target_name)
        if target is None:
            return
        if any(b["name"] == btn_name for b in target["buttons"]):
            QMessageBox.warning(
                self, TITLE,
                "Button '{0}' already exists in '{1}'."
                .format(btn_name, target_name))
            return

        moved = next((b for b in src["buttons"] if b["name"] == btn_name), None)
        if moved is None:
            return

        src["buttons"] = [b for b in src["buttons"] if b["name"] != btn_name]
        target["buttons"].append(moved)
        self._save_and_render()

    def _delete_button(self, cat_name, btn_name):
        cat = self._find_category(cat_name)
        if cat is None:
            return

        if QMessageBox.question(
            self, TITLE, "Delete button '{0}'?".format(btn_name)
        ) != QMessageBox.Yes:
            return

        cat["buttons"] = [b for b in cat["buttons"] if b["name"] != btn_name]
        self._save_and_render()

    # =============================================================== color

    def _pick_color(self, initial_hex, title):
        """컬러 다이얼로그(팔레트 + 내장 'Pick Screen Color' 스포이드)를 띄운다.

        유효한 색을 고르면 '#rrggbb' 문자열을, 취소하면 None 을 돌려준다.
        """
        initial = QColor(initial_hex or DEFAULT_PICK_HEX)
        chosen = QColorDialog.getColor(initial, self, title)
        if not chosen.isValid():
            return None
        return chosen.name()

    def _set_button_color(self, cat_name, btn_name):
        """버튼 하나의 색을 팔레트/스포이드로 지정한다."""
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None:
            return

        hex_str = self._pick_color(btn_data.get("color"), "Pick Button Color")
        if hex_str is None:
            return

        btn_data["color"] = hex_str
        self._save_and_render()
        self._log("Set color {0} on '{1}'.".format(hex_str, btn_name))

    def _reset_button_color(self, cat_name, btn_name):
        """버튼의 지정색을 지워 테마 기본 스타일로 되돌린다."""
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None or not btn_data.get("color"):
            return

        btn_data.pop("color", None)
        self._save_and_render()
        self._log("Reset color on '{0}'.".format(btn_name))

    # -------------------------------------------------- color select mode

    def on_color_mode_toggled(self, on):
        """색칠 모드 토글. 켜면 버튼이 체크형이 되어 여러 개를 골라 칠할 수 있다."""
        self._color_mode = on
        if not on:
            self._checked.clear()
        self.btn_apply_color.setEnabled(on)
        self.btn_clear_color.setEnabled(on)
        self._render_categories()
        self._log("Color select mode: {0}".format("ON" if on else "OFF"))

    def _on_color_check(self, cat_name, btn_name, checked):
        """색칠 모드에서 버튼을 토글하면 (cat, btn) 을 체크 집합에 넣고 뺀다."""
        key = (cat_name, btn_name)
        if checked:
            self._checked.add(key)
        else:
            self._checked.discard(key)

    def _sync_checked_from_widgets(self):
        """화면 버튼의 실제 isChecked() 로 self._checked 를 다시 맞춘다.

        시그널 누락/타이밍과 무관하게 '지금 눈에 보이는 체크 상태' 를 진실의 원천으로
        삼기 위한 안전장치. 삭제된 위젯은 건너뛴다.
        """
        checked = set()
        for btn, cat_name, btn_name in self._color_buttons:
            try:
                if btn.isChecked():
                    checked.add((cat_name, btn_name))
            except RuntimeError:
                # 재렌더로 이미 폐기된 위젯 — 무시.
                continue
        self._checked = checked

    def _checked_buttons(self):
        """체크된 (cat, btn) 중 실제 존재하는 버튼 dict 만 추려서 돌려준다."""
        found = []
        for cat_name, btn_name in self._checked:
            bd = self._find_button(cat_name, btn_name)
            if bd is not None:
                found.append(bd)
        return found

    def on_apply_color_to_checked(self):
        """체크된 모든 버튼에 팔레트/스포이드로 고른 한 색을 일괄 적용한다."""
        self._sync_checked_from_widgets()
        targets = self._checked_buttons()
        if not targets:
            QMessageBox.information(self, TITLE, "Check one or more buttons first.")
            return

        # 체크된 것 중 이미 색이 있으면 그 색을 다이얼로그 시작값으로.
        current = next((b.get("color") for b in targets if b.get("color")), None)
        hex_str = self._pick_color(current, "Pick Color for Checked Buttons")
        if hex_str is None:
            return

        for b in targets:
            b["color"] = hex_str
        self._save_and_render()  # 체크 상태(_checked)는 그대로라 재렌더 후에도 유지
        self._log("Applied {0} to {1} button(s)."
                  .format(hex_str, len(targets)))

    def on_clear_color_from_checked(self):
        """체크된 버튼들의 지정색을 지워 테마 기본 스타일로 되돌린다."""
        self._sync_checked_from_widgets()
        targets = self._checked_buttons()
        if not targets:
            QMessageBox.information(self, TITLE, "Check one or more buttons first.")
            return

        changed = 0
        for b in targets:
            if b.pop("color", None) is not None:
                changed += 1
        if not changed:
            return

        self._save_and_render()
        self._log("Cleared color on {0} button(s).".format(changed))
