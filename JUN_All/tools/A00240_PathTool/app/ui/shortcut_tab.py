# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# A00240_PathTool - "ShortCut" tab (Qt, standalone)
#
# 사용자가 카테고리와 경로 버튼을 직접 만들고, 버튼을 누르면 그 경로가
# 탐색기로 열린다.
#   - 상단 "Create" 그룹: [Category] / [Path] 버튼
#       * Category: 새 카테고리(QGroupBox) 생성
#       * Path    : 어느 카테고리에 넣을지 물은 뒤 경로 버튼 생성
#   - 각 카테고리는 QGroupBox 로 구분, 그 안에 경로 버튼이 쌓인다.
#   - 수정/삭제/정렬은 우클릭 컨텍스트 메뉴로 한다(카테고리·버튼 모두
#     Move Up/Move Down 으로 순서 변경 가능). 화면을 깨끗하게 유지하고
#     항목이 늘어나도 잘 확장된다.
#   - 카테고리 헤더(빈 곳)를 좌클릭하면 "Change Profile" 메뉴가 뜬다. 고른
#     프로파일로 카테고리와 그 안의 버튼 전부를 옮긴다(우클릭 메뉴에도 있음).
#   - 색 지정(v01.15, A00340_SelectionTool 의 기능을 그대로 옮김):
#       * 버튼 우클릭 'Set Color...'(팔레트+스포이드) / 'Reset Color' 로 개별 지정.
#       * 'Color' 그룹의 'Color Select' 를 켜면 카테고리를 넘나들며 여러 버튼을
#         체크해 'Apply Color...' 로 한 번에 칠한다('Clear Color' 로 해제).
#         켜져 있는 동안 버튼 클릭은 경로를 열지 않고 체크만 한다.
#       * 색은 프로파일 JSON 의 버튼 dict 에 "color": "#rrggbb" 로 저장(없으면 테마 기본).
#   - 드래그로 순서 바꾸기(v01.28): 경로 버튼을 누른 채 끌어 같은 카테고리 안의 다른 자리나
#     다른 카테고리에 놓는다. 네이티브 QDrag 가 아니라 버튼 서브클래스(_PathButton)의 마우스
#     이벤트만으로 처리한다 - 누른 채 startDragDistance 이상 움직이면 드래그, 그 안에서 놓으면
#     평소 클릭(경로 열기). 끄는 동안 놓일 자리에 가로줄이 보이고, 스크롤 가장자리에서는 저절로
#     스크롤된다. Esc 로 취소. 색칠 모드(체크형)에서는 드래그하지 않는다(체크만).
#   - 버튼 폭은 창 폭을 따른다(v01.30): 모든 버튼(_ElideButton)이 최소 폭을 작게(28px) 두어 라벨 길이가
#     최소 폭을 만들지 않고, 창이 좁아지면 버튼도 함께 좁아지며 라벨은 말줄임(…)된다(전체 이름은 툴팁).
#     Qt 는 setMinimumWidth 가 있으면 minimumSizeHint(글자 폭)를 쓰지 않는다. 프로파일 콤보도 가장 긴 항목
#     폭을 요구하지 않는다. 그래야 창을 줄일 때 버튼 글자가 잘려 안 보이는 일이 없다.

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
    QPushButton,
    QScrollArea,
    QApplication,
    QTimer,
    QFrame,
    QInputDialog,
    QFileDialog,
    QMessageBox,
    QMenu,
    QCheckBox,
    QColorDialog,
    QColor,
    QEvent,
    Qt,
)

from ..core import prefs as prefs_mod
from ..core import path_opener


TITLE = "Path Tool"

# ---------------------------------------------------------------- 버튼 색
# A00340_SelectionTool/app/ui/selection_tab.py 와 같은 규칙 (그대로 옮김).

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

    padding 8px · radius 4px 는 Framework/styles/*.qss 의 QPushButton 과 같은 값이다.
    (A00340 은 4px · 3px 라 색 버튼이 기본 버튼보다 낮다 - 여기서는 높이를 맞췄다.)
    """
    bg = QColor(hex_str)
    text = _contrast_text_hex(bg)
    border = bg.darker(150).name()
    hover = bg.lighter(115).name()
    pressed = bg.darker(115).name()
    return (
        "QPushButton {{"
        " background-color: {bg}; color: {text};"
        " border: 1px solid {border}; border-radius: 4px; padding: 8px; }}"
        "QPushButton:hover {{ background-color: {hover}; }}"
        "QPushButton:pressed {{ background-color: {pressed}; }}"
        "QPushButton:checked {{ border: 2px solid {check}; }}"
    ).format(bg=bg.name(), text=text, border=border, hover=hover,
             pressed=pressed, check=CHECK_HILITE_HEX)


def _global_pos(event):
    """마우스 이벤트의 전역 좌표(QPoint). PySide6 는 globalPosition(), PySide2 는 globalPos()."""
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()


class _ElideButton(QPushButton):
    """창 폭을 따라 줄어드는 버튼 (v01.30) - 라벨이 안 들어가면 말줄임(…)한다.

    QPushButton 의 최소 폭은 글자 폭이라 라벨이 길면 창이 그 아래로 줄지 않고, 억지로 줄이면 글자가
    잘린다. setMinimumWidth(MIN_WIDTH) 를 걸면 Qt 레이아웃이 minimumSizeHint 대신 그 값을 최소로 쓰므로
    버튼이 작아질 수 있고, resizeEvent 에서 라벨을 지금 폭에 맞춰 말줄임한다. 전체 이름은 full_text,
    말줄임 중이면 툴팁 첫 줄에 보인다. 평소(넓을 때) 모양 · 선호 크기는 QPushButton 그대로다.
    """

    #: 이 아래로는 안 줄어든다 (… 하나는 보이게)
    MIN_WIDTH = 40

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.full_text = text
        self._base_tooltip = ""
        self._full_hints = None
        self._text_margin = 0      # 힌트 폭 - 전체 라벨 글자 폭 = 테마 padding · 테두리 · 스타일 여백
        self.setMinimumWidth(self.MIN_WIDTH)
        self._refresh_hints()

    def setText(self, text):
        self.full_text = text
        self._refresh_hints()
        self._apply_elide()

    def changeEvent(self, event):
        super().changeEvent(event)
        # 테마(qss) · 글꼴이 바뀌면 전체 라벨 기준 힌트를 다시 잰다.
        if event.type() in (QEvent.StyleChange, QEvent.FontChange):
            self._refresh_hints()
            self._apply_elide()

    def setToolTip(self, text):
        """기본 툴팁을 기억해 두고, 말줄임 중이면 전체 이름을 첫 줄에 붙인다."""
        self._base_tooltip = text
        self._apply_elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self):
        avail = max(self.width() - self._text_margin, 0)
        shown = self.fontMetrics().elidedText(self.full_text, Qt.ElideRight, avail) if avail else self.full_text
        if shown != QPushButton.text(self):
            QPushButton.setText(self, shown)
        tip = self._base_tooltip
        if shown != self.full_text:
            tip = self.full_text + ("\n" + tip if tip else "")
        if tip != QPushButton.toolTip(self):
            QPushButton.setToolTip(self, tip)

    def is_elided(self):
        return QPushButton.text(self) != self.full_text

    # 선호 · 최소 크기는 **전체 라벨** 기준으로 고정한다. 말줄임된 글자로 재면 힌트가 줄고, 레이아웃이
    # 그만큼 덜 주고, 더 말줄임되는 되먹임이 생겨 한 행의 버튼들이 고르지 않게 줄었다. QPushButton 의
    # 힌트에는 스타일의 최소 폭 바닥이 있어 글자 폭 차로 보정하면 틀리므로, 전체 라벨을 잠깐 넣고 잰다
    # (sizeHint 안이 아니라 생성 · setText · 테마 변경 때만 - 레이아웃 계산 중 updateGeometry 를 피한다).
    def _refresh_hints(self):
        shown = QPushButton.text(self)
        if shown != self.full_text:
            QPushButton.setText(self, self.full_text)
        self._full_hints = (QPushButton.sizeHint(self), QPushButton.minimumSizeHint(self))
        # 라벨 양옆 여백은 테마마다 다르므로(padding · 테두리 · 스타일 여백) 힌트에서 글자 폭을 빼 잰다.
        # 상수로 두면(처음 24px) 힌트 폭 그대로인 버튼도 말줄임되는 일이 있었다(Category: 여백 18).
        self._text_margin = max(
            self._full_hints[0].width() - self.fontMetrics().horizontalAdvance(self.full_text), 0)
        if shown != self.full_text:
            QPushButton.setText(self, shown)

    def sizeHint(self):
        return self._full_hints[0] if self._full_hints else super().sizeHint()

    def minimumSizeHint(self):
        return self._full_hints[1] if self._full_hints else super().minimumSizeHint()


class _PathButton(_ElideButton):
    """드래그로 자리를 옮길 수 있는 경로 버튼 (v01.28).

    왼쪽 버튼을 누른 채 QApplication.startDragDistance() 이상 움직이면 드래그로 보고 owner(ShortcutTab)의
    begin_drag / update_drag / end_drag 를 부른다. 그 거리 안에서 놓으면 평소 클릭이라 clicked 가 나가
    경로가 열린다. 드래그로 끝난 놓음은 QPushButton 에 넘기지 않아 clicked 가 나가지 않는다.
    Qt 는 누른 위젯에 이동 · 놓음을 계속 보내므로(암묵 grab) 커서가 버튼 밖으로 나가도 끝까지 받는다.
    drag_key 는 (카테고리 인덱스, 버튼 인덱스) - 같은 이름의 버튼이 있어도 어느 것이 움직였는지 틀리지 않는다.
    색칠 모드(체크형)에서는 drag_enabled=False 로 두어 체크만 한다.
    폭은 창을 따르고 라벨은 말줄임된다 (_ElideButton, v01.30).
    """

    def __init__(self, text, owner, drag_key, parent=None):
        super().__init__(text, parent)
        self._owner = owner
        self.drag_key = drag_key
        self.drag_enabled = True
        self._press_pos = None      # 누른 전역 좌표 (None = 안 누름)
        self._dragging = False
        self._swallow_release = False   # Esc 로 취소한 뒤 오는 놓음은 클릭이 아니다

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_enabled:
            self._press_pos = _global_pos(event)
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None and (event.buttons() & Qt.LeftButton):
            pos = _global_pos(event)
            if not self._dragging:
                if (pos - self._press_pos).manhattanLength() >= QApplication.startDragDistance():
                    self._dragging = True
                    self._owner.begin_drag(self)
            if self._dragging:
                self._owner.update_drag(pos)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and (self._dragging or self._swallow_release):
            dragging = self._dragging
            self._dragging = False
            self._swallow_release = False
            self._press_pos = None
            self.setDown(False)
            if dragging:
                self._owner.end_drag(_global_pos(event))
            event.accept()
            return
        self._press_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self._dragging and event.key() == Qt.Key_Escape:
            self._dragging = False
            self._swallow_release = True
            self.setDown(False)
            self._owner.cancel_drag()
            event.accept()
            return
        super().keyPressEvent(event)


class AddPathDialog(QDialog):
    """경로 버튼 생성을 한 창에서: 카테고리 선택 → 버튼 이름 → 경로(찾아보기)."""

    def __init__(self, category_names, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Path")
        self.setMinimumWidth(360)

        form = QFormLayout(self)

        # 1) 어느 카테고리에 넣을지
        self.cmb_category = QComboBox()
        self.cmb_category.addItems(category_names)
        form.addRow("Add to category:", self.cmb_category)

        # 2) 버튼 이름
        self.ipf_name = QLineEdit()
        form.addRow("Button name:", self.ipf_name)

        # 3) 경로(직접 입력 가능 + 찾아보기)
        path_row = QHBoxLayout()
        self.ipf_path = QLineEdit()
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse)
        path_row.addWidget(self.ipf_path, stretch=1)
        path_row.addWidget(btn_browse)
        form.addRow("Path:", path_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse(self):
        start = self.ipf_path.text().strip() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Folder", start)
        if path:
            self.ipf_path.setText(path)

    def values(self):
        """(category, name, path) — name/path 는 strip 된 값."""
        return (
            self.cmb_category.currentText(),
            self.ipf_name.text().strip(),
            self.ipf_path.text().strip(),
        )


class _CategoryBox(QGroupBox):
    """좌클릭을 콜백으로 넘기는 카테고리 QGroupBox.

    Path 버튼은 자기 클릭을 소비하므로, 콜백은 헤더나 버튼 사이 빈 곳을
    눌렀을 때만 불린다. Qt 바인딩(Framework.qt)에 Signal 이 없어 콜백으로 둔다.
    """

    def __init__(self, title, on_left_click, parent=None):
        super().__init__(title, parent)
        self._on_left_click = on_left_click

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self._on_left_click(event.pos())
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ShortcutTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # 활성 프로파일과 그 데이터를 읽는다(없으면 Default 자동 생성).
        self._profile = prefs_mod.get_active()
        self._data = prefs_mod.load_profile(self._profile)

        # 색칠 모드 상태. _checked 는 체크된 (카테고리, 버튼) 이름 쌍 - 재렌더에도 유지된다.
        # _color_buttons 는 지금 그려진 체크형 버튼 (위젯, cat, name) - Apply/Clear 직전에
        # 위젯의 실제 isChecked() 로 _checked 를 다시 맞춘다(A00340 v01.03 과 같은 안전장치).
        self._color_mode = False
        self._checked = set()
        self._color_buttons = []

        # 드래그 정렬 상태 (v01.28). _cat_boxes 는 지금 그려진 (카테고리 박스, 카테고리 인덱스, [버튼 위젯]).
        self._cat_boxes = []
        self._drag_source = None        # 끌고 있는 버튼의 drag_key
        self._drag_last_pos = None      # 마지막 전역 커서 좌표 (자동 스크롤 틱에서 다시 계산)

        self._build_ui()
        self._refresh_profiles()
        self._render_categories()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.addWidget(self._build_profile_group())
        root.addWidget(self._build_create_group())
        root.addWidget(self._build_color_group())

        # 카테고리가 계속 늘어나므로 스크롤 영역에 담는다.
        self._cat_container = QWidget()
        self._cat_layout = QVBoxLayout(self._cat_container)
        self._cat_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._cat_container)
        root.addWidget(scroll, stretch=1)
        self._scroll = scroll

        # 드래그 중 놓일 자리를 보여 주는 가로줄 (v01.28). 레이아웃 항목이 아닌 컨테이너의 자식이라
        # 재렌더(_render_categories)에 지워지지 않고, 컨테이너와 함께 스크롤된다.
        self._drop_line = QFrame(self._cat_container)
        self._drop_line.setObjectName("A00240_drop_line")
        self._drop_line.setStyleSheet(
            "QFrame#A00240_drop_line {{ background-color: {c}; border: none; }}".format(c=CHECK_HILITE_HEX))
        self._drop_line.hide()

        # 드래그 중 가장자리 자동 스크롤 - 커서가 멈춰 있어도 내용이 움직이므로 틱마다 다시 계산한다.
        self._drag_timer = QTimer(self)
        self._drag_timer.setInterval(40)
        self._drag_timer.timeout.connect(self._on_drag_tick)

    def _build_profile_group(self):
        # 프로파일(집/회사처럼 JSON 별로 나뉜 경로 묶음) 선택 + 관리.
        group = QGroupBox("Profile")
        row = QHBoxLayout(group)

        self.cmb_profile = QComboBox()
        self.cmb_profile.setToolTip("Active profile (each is its own JSON)")
        # 가장 긴 프로파일 이름이 최소 폭을 만들지 않게 (v01.30) - 좁으면 콤보 글자가 말줄임된다.
        self.cmb_profile.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_profile.setMinimumContentsLength(4)
        self.cmb_profile.currentTextChanged.connect(self.on_profile_changed)

        btn_new = _ElideButton("New")
        btn_new.setToolTip("Create a new profile")
        btn_new.clicked.connect(self.on_new_profile)

        btn_rename = _ElideButton("Rename")
        btn_rename.setToolTip("Rename the current profile")
        btn_rename.clicked.connect(self.on_rename_profile)

        btn_delete = _ElideButton("Delete")
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

        btn_category = _ElideButton("Category")
        btn_category.setToolTip("Create a new category")
        btn_category.clicked.connect(self.on_create_category)

        btn_path = _ElideButton("Path")
        btn_path.setToolTip("Add a path button into a category")
        btn_path.clicked.connect(self.on_create_path)

        row.addWidget(btn_category)
        row.addWidget(btn_path)
        row.addStretch(1)

        return group

    def _build_color_group(self):
        # 색칠 모드: 카테고리를 넘나들며 여러 버튼을 골라 한 색으로 칠한다.
        group = QGroupBox("Color")
        row = QHBoxLayout(group)

        # 모드 토글. 켜면 버튼이 체크형이 되고 클릭이 '경로 열기' 대신 '체크'로 바뀐다.
        self.chk_color_mode = QCheckBox("Color Select")
        self.chk_color_mode.setToolTip(
            "Pick multiple buttons across categories (click to check), "
            "then apply one color to all of them at once.\n"
            "While this is on, clicking a button does not open its path.")
        self.chk_color_mode.toggled.connect(self.on_color_mode_toggled)

        # 체크된 버튼들에 색을 지정 / 색을 지운다. 모드가 켜져 있을 때만 활성.
        # 라벨은 A00340 의 'Apply Color...' / 'Clear Color' 를 줄였다 - 그대로 두면 이 그룹이
        # Profile 그룹보다 넓어져 창 최소 폭이 늘어난다(그룹 제목이 이미 Color).
        self.btn_apply_color = _ElideButton("Apply...")
        self.btn_apply_color.setToolTip(
            "Apply a picked color to all checked buttons")
        self.btn_apply_color.clicked.connect(self.on_apply_color_to_checked)
        self.btn_apply_color.setEnabled(False)

        self.btn_clear_color = _ElideButton("Clear")
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
        # 기존 위젯 제거 후 데이터 기준으로 다시 그린다.
        self._color_buttons = []
        self._cat_boxes = []
        self._drop_line.hide()
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

        for cat_index, cat in enumerate(categories):
            self._cat_layout.addWidget(self._build_category_box(cat_index, cat))

    def _build_category_box(self, cat_index, cat):
        cat_name = cat["name"]
        box = _CategoryBox(
            cat_name,
            lambda pos, n=cat_name: self._show_category_left_menu(n, box, pos),
        )
        box.setToolTip(
            "Left-click: Change Profile / Right-click: edit\n"
            "Drag a path button to reorder it or move it to another category")
        box.setContextMenuPolicy(Qt.CustomContextMenu)
        box.customContextMenuRequested.connect(
            lambda pos, b=box, n=cat_name: self._show_category_menu(n, b, pos)
        )

        v = QVBoxLayout(box)

        buttons = cat.get("buttons", [])
        btn_widgets = []
        if not buttons:
            empty = QLabel("(no paths — use 'Path' to add)")
            empty.setEnabled(False)
            v.addWidget(empty)
        else:
            for btn_index, btn_data in enumerate(buttons):
                btn = self._build_path_button(cat_name, btn_data, (cat_index, btn_index))
                v.addWidget(btn)
                btn_widgets.append(btn)

        self._cat_boxes.append((box, cat_index, btn_widgets))
        return box

    def _build_path_button(self, cat_name, btn_data, drag_key):
        btn = _PathButton(btn_data["name"], self, drag_key)
        btn.setToolTip(btn_data["path"])

        path = btn_data["path"]
        name = btn_data["name"]
        color_hex = btn_data.get("color")

        if self._color_mode:
            # 색칠 모드: 버튼을 체크형으로. 클릭은 '경로 열기' 대신 '체크 토글'. 드래그는 끈다.
            btn.drag_enabled = False
            btn.setCheckable(True)
            # setChecked 는 아래 toggled 연결 '전'에 호출해야 초기 복원이 콜백을 안 부른다.
            btn.setChecked((cat_name, name) in self._checked)
            # 색이 있으면 색 스타일(+:checked 강조), 없으면 강조 테두리만.
            btn.setStyleSheet(
                _button_stylesheet(color_hex) if color_hex else CHECK_ONLY_QSS)
            # 체크 상태 추적은 clicked 가 아니라 toggled(새 상태를 확실히 전달)로 한다.
            btn.toggled.connect(
                lambda checked, c=cat_name, n=name:
                self._on_color_check(c, n, checked))
            self._color_buttons.append((btn, cat_name, name))
        else:
            # 일반 모드: 지정색이 있으면 입히고, 클릭하면 경로를 연다.
            if color_hex:
                btn.setStyleSheet(_button_stylesheet(color_hex))
            btn.clicked.connect(lambda *_a, p=path: self._open_path(p))

        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, w=btn, c=cat_name, n=name:
            self._show_button_menu(c, n, w, pos)
        )

        return btn

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
        return next((b for b in cat.get("buttons", []) if b["name"] == btn_name), None)

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

    def on_new_profile(self):
        raw, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if not ok:
            return
        name = prefs_mod.sanitize_name(raw)
        if not name:
            return
        if name in prefs_mod.list_profiles():
            QMessageBox.warning(
                self, "Path Tool", f"Profile '{name}' already exists."
            )
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
                self, "Path Tool", f"Profile '{new}' already exists."
            )
            return

        prefs_mod.rename_profile(old, new)
        self._profile = new
        self._refresh_profiles()

    def on_delete_profile(self):
        name = self._profile
        if len(prefs_mod.list_profiles()) <= 1:
            QMessageBox.information(
                self, "Path Tool", "At least one profile must remain."
            )
            return
        if QMessageBox.question(
            self, "Path Tool", f"Delete profile '{name}' and all its paths?"
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
                self, "Path Tool", f"Category '{name}' already exists."
            )
            return

        self._data["categories"].append({"name": name, "buttons": []})
        self._save_and_render()

    def on_create_path(self):
        names = self._category_names()
        if not names:
            QMessageBox.information(
                self, "Path Tool", "Create a category first."
            )
            return

        # 카테고리 / 버튼 이름 / 경로를 한 다이얼로그에서 모두 입력받는다.
        # 입력이 비거나 중복이면 안내 후 다이얼로그를 다시 띄워(입력값 유지) 재시도.
        dlg = AddPathDialog(names, self)
        while True:
            if dlg.exec_() != QDialog.Accepted:
                return

            cat_name, label, path = dlg.values()

            if not label:
                QMessageBox.warning(self, "Path Tool", "Button name is required.")
                continue
            if not path:
                QMessageBox.warning(self, "Path Tool", "Path is required.")
                continue

            cat = self._find_category(cat_name)
            if cat is None:
                return
            if any(b["name"] == label for b in cat["buttons"]):
                QMessageBox.warning(
                    self, "Path Tool",
                    f"Button '{label}' already exists in '{cat_name}'."
                )
                continue

            break

        cat["buttons"].append({"name": label, "path": path})
        self._save_and_render()

    # ============================================================= open path

    def _open_path(self, path):
        try:
            path_opener.open_path(path)
        except FileNotFoundError:
            QMessageBox.warning(
                self, "Path Tool", f"Path does not exist:\n{path}"
            )
        except Exception as exc:  # noqa: BLE001 - 어떤 OS 오류도 사용자에게 안내
            QMessageBox.warning(self, "Path Tool", f"Could not open path:\n{exc}")

    # ========================================================= context menus

    def _show_category_menu(self, cat_name, box, pos):
        menu = QMenu(box)
        # 정렬 순서 변경(위/아래로 한 칸). 끝단에서는 비활성화한다.
        act_up = menu.addAction("Move Up")
        act_down = menu.addAction("Move Down")
        menu.addSeparator()
        act_rename = menu.addAction("Rename Category")
        act_profile = menu.addAction("Change Profile")
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
        elif chosen == act_profile:
            self._change_category_profile(cat_name)
        elif chosen == act_delete:
            self._delete_category(cat_name)

    def _show_category_left_menu(self, cat_name, box, pos):
        """카테고리 좌클릭 메뉴 — 지금은 Change Profile 하나."""
        menu = QMenu(box)
        act_profile = menu.addAction("Change Profile")
        if menu.exec_(box.mapToGlobal(pos)) == act_profile:
            self._change_category_profile(cat_name)

    def _show_button_menu(self, cat_name, btn_name, btn_widget, pos):
        menu = QMenu(btn_widget)
        # 카테고리 안에서 버튼 순서 변경(위/아래로 한 칸). 끝단에서는 비활성화한다.
        act_up = menu.addAction("Move Up")
        act_down = menu.addAction("Move Down")
        menu.addSeparator()
        act_rename = menu.addAction("Rename")
        act_path = menu.addAction("Change Path")
        act_category = menu.addAction("Change Category")
        menu.addSeparator()
        act_set_color = menu.addAction("Set Color...")
        act_reset_color = menu.addAction("Reset Color")
        menu.addSeparator()
        act_delete = menu.addAction("Delete")

        cat = self._find_category(cat_name)
        buttons = cat.get("buttons", []) if cat else []
        idx = next(
            (i for i, b in enumerate(buttons) if b["name"] == btn_name), -1
        )
        act_up.setEnabled(idx > 0)
        act_down.setEnabled(0 <= idx < len(buttons) - 1)
        btn_data = buttons[idx] if idx >= 0 else None
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
        elif chosen == act_category:
            self._change_button_category(cat_name, btn_name)
        elif chosen == act_set_color:
            self._set_button_color(cat_name, btn_name)
        elif chosen == act_reset_color:
            self._reset_button_color(cat_name, btn_name)
        elif chosen == act_delete:
            self._delete_button(cat_name, btn_name)

    # ===================================================== drag to reorder (v01.28)

    def begin_drag(self, button):
        """_PathButton 이 드래그 시작을 알린다. 커서를 손 모양으로, 자동 스크롤 틱 시작."""
        self._drag_source = button.drag_key
        self._drag_last_pos = None
        QApplication.setOverrideCursor(Qt.ClosedHandCursor)
        self._drag_timer.start()

    def update_drag(self, global_pos):
        """커서가 움직였다 - 놓일 자리를 다시 구해 가로줄을 옮기고, 가장자리면 스크롤한다."""
        if self._drag_source is None:
            return
        self._drag_last_pos = global_pos
        self._show_drop_line(self._drop_target_at(global_pos))
        self._auto_scroll(global_pos)

    def end_drag(self, global_pos):
        """놓았다 - 자리를 구해 데이터를 옮기고 저장 · 재렌더."""
        source = self._drag_source
        target = self._drop_target_at(global_pos) if source is not None else None
        self.cancel_drag()
        if source is not None and target is not None:
            self._drop_button(source, target)

    def cancel_drag(self):
        """드래그 상태를 모두 걷는다 (Esc · 놓음 공통)."""
        self._drag_timer.stop()
        if self._drag_source is not None:
            QApplication.restoreOverrideCursor()
        self._drag_source = None
        self._drag_last_pos = None
        self._drop_line.hide()

    def _on_drag_tick(self):
        if self._drag_source is not None and self._drag_last_pos is not None:
            self.update_drag(self._drag_last_pos)

    def _drop_target_at(self, global_pos):
        """전역 커서 좌표 -> (카테고리 인덱스, 삽입 인덱스). 카테고리가 없으면 None.

        세로 위치만 본다. 커서 y 를 품는 카테고리 박스를 고르고(없으면 세로로 가장 가까운 박스),
        그 안에서 가운데 y 가 커서보다 위인 버튼 수가 삽입 인덱스다.
        """
        if not self._cat_boxes:
            return None
        local = self._cat_container.mapFromGlobal(global_pos)
        y = local.y()

        chosen = None
        best = None
        for box, cat_index, btn_widgets in self._cat_boxes:
            g = box.geometry()
            if g.top() <= y <= g.bottom():
                chosen = (box, cat_index, btn_widgets)
                break
            dist = g.top() - y if y < g.top() else y - g.bottom()
            if best is None or dist < best[0]:
                best = (dist, (box, cat_index, btn_widgets))
        if chosen is None:
            chosen = best[1]

        box, cat_index, btn_widgets = chosen
        insert = 0
        for btn in btn_widgets:
            center = btn.mapTo(self._cat_container, btn.rect().center()).y()
            if center < y:
                insert += 1
        return (cat_index, insert)

    def _show_drop_line(self, target):
        """target 자리에 가로줄을 그린다 (컨테이너 좌표)."""
        if target is None:
            self._drop_line.hide()
            return
        cat_index, insert = target
        entry = next((e for e in self._cat_boxes if e[1] == cat_index), None)
        if entry is None:
            self._drop_line.hide()
            return
        box, _ci, btn_widgets = entry
        bg = box.geometry()
        m = box.layout().contentsMargins() if box.layout() is not None else None
        left = bg.left() + (m.left() if m else 8)
        width = bg.width() - ((m.left() + m.right()) if m else 16)
        spacing = box.layout().spacing() if box.layout() is not None else 6
        if spacing < 0:
            spacing = 6

        if not btn_widgets:
            # 빈 카테고리 - 안내 라벨 자리 가운데
            y = bg.top() + bg.height() // 2
        elif insert < len(btn_widgets):
            nxt = btn_widgets[insert]
            y = nxt.mapTo(self._cat_container, nxt.rect().topLeft()).y() - spacing // 2
        else:
            last = btn_widgets[-1]
            y = last.mapTo(self._cat_container, last.rect().bottomLeft()).y() + spacing // 2

        self._drop_line.setGeometry(left, y - 1, max(width, 10), 3)
        self._drop_line.show()
        self._drop_line.raise_()

    AUTO_SCROLL_MARGIN = 24   # px, 뷰포트 위/아래 이 안에 커서가 오면 스크롤
    AUTO_SCROLL_STEP = 12     # px / 틱

    def _auto_scroll(self, global_pos):
        viewport = self._scroll.viewport()
        p = viewport.mapFromGlobal(global_pos)
        bar = self._scroll.verticalScrollBar()
        if p.y() < self.AUTO_SCROLL_MARGIN:
            bar.setValue(bar.value() - self.AUTO_SCROLL_STEP)
        elif p.y() > viewport.height() - self.AUTO_SCROLL_MARGIN:
            bar.setValue(bar.value() + self.AUTO_SCROLL_STEP)

    def _drop_button(self, source, target):
        """(cat, idx) 의 버튼을 (cat, insert) 자리로 옮긴다. 같은 자리면 아무 일 없음.

        같은 카테고리 안이면 pop -> insert (인덱스 보정). 다른 카테고리면 Change Category 와 같은
        규칙 - 대상에 같은 이름이 있으면 막는다. 바뀌었으면 저장 · 재렌더.
        """
        s_cat, s_idx = source
        t_cat, t_idx = target
        cats = self._data.get("categories", [])
        if not (0 <= s_cat < len(cats) and 0 <= t_cat < len(cats)):
            return
        src = cats[s_cat].setdefault("buttons", [])
        if not (0 <= s_idx < len(src)):
            return

        if s_cat == t_cat:
            if t_idx in (s_idx, s_idx + 1):
                return
            moved = src.pop(s_idx)
            if t_idx > s_idx:
                t_idx -= 1
            src.insert(max(0, min(t_idx, len(src))), moved)
        else:
            dst = cats[t_cat].setdefault("buttons", [])
            moved = src[s_idx]
            if any(b["name"] == moved["name"] for b in dst):
                QMessageBox.warning(
                    self, "Path Tool",
                    "Button '{0}' already exists in '{1}'.".format(moved["name"], cats[t_cat]["name"]))
                return
            src.pop(s_idx)
            dst.insert(max(0, min(t_idx, len(dst))), moved)

        self._save_and_render()

    # ============================================================ edit/delete

    def _move_category(self, name, delta):
        """카테고리를 목록에서 delta(-1=위, +1=아래)만큼 옮겨 정렬 순서를 바꾼다.

        화면 순서는 곧 self._data["categories"] 의 리스트 순서이므로, 인접 항목과
        자리를 바꾼 뒤 저장·재렌더하면 사용자가 원하는 순서를 만들 수 있다.
        """
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
        """카테고리 안에서 버튼을 delta(-1=위, +1=아래)만큼 옮겨 순서를 바꾼다.

        화면 순서는 곧 cat["buttons"] 의 리스트 순서이므로, 인접 버튼과 자리를
        바꾼 뒤 저장·재렌더하면 사용자가 원하는 순서를 만들 수 있다.
        """
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
                self, "Path Tool", f"Category '{new}' already exists."
            )
            return

        self._find_category(old)["name"] = new
        self._save_and_render()

    def _delete_category(self, name):
        cat = self._find_category(name)
        if cat is None:
            return

        count = len(cat.get("buttons", []))
        msg = f"Delete category '{name}'"
        msg += f" and its {count} path button(s)?" if count else "?"
        if QMessageBox.question(self, "Path Tool", msg) != QMessageBox.Yes:
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
                self, "Path Tool",
                f"Button '{new}' already exists in '{cat_name}'."
            )
            return

        for b in cat["buttons"]:
            if b["name"] == btn_name:
                b["name"] = new
                break
        self._save_and_render()

    def _change_button_category(self, cat_name, btn_name):
        """버튼을 다른 카테고리로 옮긴다(우클릭 → Change Category).

        이동 대상은 현재 카테고리를 뺀 나머지 중에서 고른다. 대상에 같은 이름의 버튼이
        있으면 막고, 아니면 원본에서 떼어 대상 끝에 붙인다(버튼 순서 보존).
        """
        src = self._find_category(cat_name)
        if src is None:
            return

        others = [n for n in self._category_names() if n != cat_name]
        if not others:
            QMessageBox.information(
                self, "Path Tool",
                "There is no other category to move to. Create one first.")
            return

        target_name, ok = QInputDialog.getItem(
            self, "Change Category",
            f"Move '{btn_name}' to category:", others, 0, False)
        if not ok or not target_name:
            return

        target = self._find_category(target_name)
        if target is None:
            return
        if any(b["name"] == btn_name for b in target["buttons"]):
            QMessageBox.warning(
                self, "Path Tool",
                f"Button '{btn_name}' already exists in '{target_name}'.")
            return

        moved = next((b for b in src["buttons"] if b["name"] == btn_name), None)
        if moved is None:
            return

        src["buttons"] = [b for b in src["buttons"] if b["name"] != btn_name]
        target["buttons"].append(moved)
        self._save_and_render()

    def _change_category_profile(self, cat_name):
        """카테고리와 그 안의 버튼 전부를 다른 프로파일로 옮긴다(Change Profile).

        대상은 현재 프로파일을 뺀 나머지 중에서 고른다. 대상에 같은 이름 카테고리가
        있으면 그 끝에 버튼을 합치고, 겹치는 버튼 이름이 있으면 아무것도 옮기지 않는다.
        저장은 대상 → 원본 순(중간에 실패해도 버튼이 사라지지 않게).
        """
        if self._find_category(cat_name) is None:
            return

        others = [n for n in prefs_mod.list_profiles() if n != self._profile]
        if not others:
            QMessageBox.information(
                self, "Path Tool",
                "There is no other profile to move to. Create one first.")
            return

        target_name, ok = QInputDialog.getItem(
            self, "Change Profile",
            f"Move category '{cat_name}' and its paths to profile:",
            others, 0, False)
        if not ok or not target_name:
            return

        dst_data = prefs_mod.load_profile(target_name)
        conflicts = prefs_mod.move_category(self._data, dst_data, cat_name)
        if conflicts is None:
            return
        if conflicts:
            QMessageBox.warning(
                self, "Path Tool",
                f"Category '{cat_name}' already exists in '{target_name}' "
                f"with the same button name(s):\n  " + "\n  ".join(conflicts)
                + "\nRename or remove them first. Nothing was moved.")
            return

        try:
            prefs_mod.save_profile(target_name, dst_data)
        except OSError as exc:
            # 대상 저장 실패 → 원본은 디스크에서 다시 읽어 메모리 변경을 되돌린다.
            self._data = prefs_mod.load_profile(self._profile)
            self._render_categories()
            QMessageBox.warning(
                self, "Path Tool", f"Could not save profile '{target_name}':\n{exc}")
            return
        self._save_and_render()

    def _change_button_path(self, cat_name, btn_name):
        cat = self._find_category(cat_name)
        if cat is None:
            return

        target = next((b for b in cat["buttons"] if b["name"] == btn_name), None)
        if target is None:
            return

        start_dir = target["path"] if os.path.isdir(target["path"]) \
            else os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(
            self, "Select Folder", start_dir
        )
        if not path:
            return

        target["path"] = path
        self._save_and_render()

    def _delete_button(self, cat_name, btn_name):
        cat = self._find_category(cat_name)
        if cat is None:
            return

        if QMessageBox.question(
            self, "Path Tool", f"Delete button '{btn_name}'?"
        ) != QMessageBox.Yes:
            return

        cat["buttons"] = [b for b in cat["buttons"] if b["name"] != btn_name]
        self._save_and_render()

    # =============================================================== color
    # A00340_SelectionTool 의 색 기능을 그대로 옮겼다. 다른 점: 이 툴은 로그창이 없어
    # 성공 메시지는 남기지 않는다(색이 바뀐 게 바로 보인다).

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

    def _reset_button_color(self, cat_name, btn_name):
        """버튼의 지정색을 지워 테마 기본 스타일로 되돌린다."""
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None or not btn_data.get("color"):
            return

        btn_data.pop("color", None)
        self._save_and_render()

    # -------------------------------------------------- color select mode

    def on_color_mode_toggled(self, on):
        """색칠 모드 토글. 켜면 버튼이 체크형이 되어 여러 개를 골라 칠할 수 있다."""
        self._color_mode = on
        if not on:
            self._checked.clear()
        self.btn_apply_color.setEnabled(on)
        self.btn_clear_color.setEnabled(on)
        self._render_categories()

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
                # 재렌더로 이미 폐기된 위젯 - 무시.
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
