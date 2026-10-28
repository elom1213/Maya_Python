# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# A00340_SelectionTool - "Buttons" tab (Qt, in-Maya)
#
# 사용자가 카테고리와 선택 버튼을 직접 만들고, 버튼을 누르면 그 버튼에 저장된
# 오브젝트들이 마야 씬에서 선택된다. (구성/편집 방식은 A00240_PathTool 의 ShortCut
# 탭을 이식했다. 경로 대신 '현재 선택된 오브젝트 목록'을 버튼에 담는 점만 다르다.)
#
#   - 상단 "Profile" 그룹 : 선택 버튼 세트를 캐릭터/에셋별 JSON 으로 나눠 관리.
#   - 상단 "Create" 그룹  : [Category] / [Selection] 버튼.
#   - `Add` 체크 (v01.16~) : 버튼 모음 pane 맨 위 - Controls 를 접거나 숨겨도 보인다.
#       * Category  : 새 카테고리(QGroupBox) 생성.
#       * Selection : 현재 마야 선택을 캡처해 새 선택 버튼으로 만든다.
#   - 각 카테고리는 QGroupBox, 그 안에 선택 버튼이 쌓인다.
#   - 버튼 클릭     : 저장된 오브젝트를 선택('Add' 체크 시 현재 선택에 누적).
#   - 추가/삭제/정렬/이름변경/선택갱신 : 우클릭 컨텍스트 메뉴로 한다.
#   - 색 지정       : 버튼 우클릭 'Set Color...'(팔레트+스포이드)로 개별 지정.
#                     'Color Select' 모드를 켜면 카테고리를 넘나들며 여러 버튼을
#                     체크해 'Apply Color...'로 한 번에 칠한다('Clear Color'로 해제).
#   - 배치            : 상하 스플리터. 위 = Controls(Profile/Create/Color), 아래 = 버튼 모음.
#                     로그창은 이 탭 밖, 창 맨 아래(main_window). v01.08 에서 좌우로 눕혔다가
#                     v01.09 에서 되돌렸다.
#   - 위 칸 높이      : 처음 보일 때 Controls 내용의 최소 높이를 재서 그만큼 연다 - 기본
#                     상태에서 스크롤 없이 Controls 전체가 보인다(_fit_controls_height).
#   - Controls 숨김  : main_window 의 View > Show Controls 가 set_controls_visible() 을
#                     부른다. 접기(CollapsibleBox)는 헤더와 스크롤 영역의 최소 높이가
#                     남지만, 숨김은 위 pane 자체를 숨겨 핸들까지 사라지고 버튼 모음이
#                     창 전체를 쓴다. 상태는 prefs(active.json) 에 남아 다음에도 유지.
#   - 드래그로 순서 바꾸기(v01.15, A00240_PathTool v01.28 과 같은 방식): 선택 버튼을 누른 채 끌어 같은
#     카테고리의 다른 자리나 다른 카테고리에 놓는다. 네이티브 QDrag 가 아니라 버튼 서브클래스(_DragButton)의
#     마우스 이벤트만으로 처리한다 - 누른 채 startDragDistance 이상 움직이면 드래그, 그 안에서 놓으면 평소
#     클릭(선택). 끄는 동안 놓일 자리에 가로줄, 스크롤 가장자리에서 자동 스크롤, Esc 로 취소.
#     색칠 모드(체크형)에서는 드래그하지 않는다(체크만).

from Framework.qt.qt import (
    QApplication,
    QFrame,
    QTimer,
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
    QStyle,
    QInputDialog,
    QMessageBox,
    QColorDialog,
    QColor,
    QMenu,
    Qt,
)

from ..core import prefs as prefs_mod
from ..core import maya_select


TITLE = "Selection Tool"

# active.json 에 저장하는 창 설정 키: Controls pane 표시 여부(View > Show Controls).
SHOW_CONTROLS_KEY = "show_controls"

# 위 Controls 칸의 높이 기본값(px). 실제로는 처음 보일 때 내용 높이로 다시 잡는다.
CONTROLS_HEIGHT_FALLBACK = 230

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


def _global_pos(event):
    """마우스 이벤트의 전역 좌표(QPoint). PySide6 는 globalPosition(), PySide2 는 globalPos()."""
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()


class _DragButton(QPushButton):
    """드래그로 자리를 옮길 수 있는 선택 버튼 (v01.15, A00240 _PathButton 과 같은 방식).

    왼쪽 버튼을 누른 채 QApplication.startDragDistance() 이상 움직이면 드래그로 보고 owner(SelectionTab)의
    begin_drag / update_drag / end_drag 를 부른다. 그 거리 안에서 놓으면 평소 클릭이라 clicked 가 나가
    오브젝트가 선택된다. 드래그로 끝난 놓음은 QPushButton 에 넘기지 않아 clicked 가 나가지 않는다.
    Qt 는 누른 위젯에 이동 · 놓음을 계속 보내므로(암묵 grab) 커서가 버튼 밖으로 나가도 끝까지 받는다.
    drag_key 는 (카테고리 인덱스, 버튼 인덱스) - 같은 이름의 버튼이 있어도 어느 것이 움직였는지 틀리지 않는다.
    색칠 모드(체크형)에서는 drag_enabled=False 로 두어 체크만 한다.
    """

    def __init__(self, text, owner, drag_key, parent=None):
        super().__init__(text, parent)
        self._owner = owner
        self.drag_key = drag_key
        self.drag_enabled = drag_key is not None
        self._press_pos = None          # 누른 전역 좌표 (None = 안 누름)
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


class AddSelectionDialog(QDialog):
    """선택 버튼 생성: 카테고리 선택 → 버튼 이름 (오브젝트는 현재 선택을 캡처)."""

    def __init__(self, category_names, obj_count, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Selection Button")
        self.setMinimumWidth(320)

        form = QFormLayout(self)

        # 1) 어느 카테고리에 넣을지
        self.cmb_category = QComboBox()
        self.cmb_category.addItems(category_names)
        form.addRow("Add to category:", self.cmb_category)

        # 2) 버튼 이름
        self.ipf_name = QLineEdit()
        form.addRow("Button name:", self.ipf_name)

        # 3) 캡처된 오브젝트 수(읽기 전용 안내)
        info = QLabel("Captured {0} object(s) from current selection."
                      .format(obj_count))
        info.setEnabled(False)
        form.addRow(info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        """(category, name) — name 은 strip 된 값."""
        return (
            self.cmb_category.currentText(),
            self.ipf_name.text().strip(),
        )


class SelectionTab(QWidget):

    def __init__(self, log_callback=None, parent=None):
        super().__init__(parent)

        # 로그/상태 보고용 콜백(없으면 무시). main_window 의 공용 로그로 흘려보낸다.
        self._log = log_callback or (lambda _msg: None)

        # 활성 프로파일과 그 데이터를 읽는다(없으면 Default 자동 생성).
        self._profile = prefs_mod.get_active()
        self._data = prefs_mod.load_profile(self._profile)

        # 색칠 모드 상태: 켜지면 버튼이 체크형으로 바뀌어 여러 개를 골라 한 번에 칠한다.
        # 체크된 버튼은 (category, button) 이름 쌍으로 들고 있어 재렌더 후에도 유지된다.
        # _color_buttons 는 현재 렌더된 체크형 버튼 위젯 목록(위젯, cat, name) — Apply/Clear
        # 시 시그널 상태 대신 위젯의 실제 isChecked() 를 진실의 원천으로 쓴다.
        self._color_mode = False
        self._checked = set()
        self._color_buttons = []

        # 드래그로 순서 바꾸기 (v01.15). _cat_boxes = [(QGroupBox, 카테고리 인덱스, [버튼 위젯])]
        self._cat_boxes = []
        self._drag_source = None        # (카테고리 인덱스, 버튼 인덱스) - 드래그 중이 아니면 None
        self._drag_last_pos = None

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
        # 처음 보일 때 _fit_controls_height 가 위 칸을 내용 높이로 다시 잡는다.
        splitter.setSizes([CONTROLS_HEIGHT_FALLBACK, 430])

        root.addWidget(splitter)

        # 지난번에 Controls 를 숨겨 두었으면 그대로 숨긴 채 연다(저장은 다시 하지 않는다).
        if not prefs_mod.get_setting(SHOW_CONTROLS_KEY, True):
            self._controls_pane.setVisible(False)

    def _build_controls_pane(self):
        """상단 pane: Profile/Create/Color 를 '하나의' 접이식 박스로 묶는다.

        세 칸을 개별로 접는 대신 Controls 박스 헤더 하나로 전부 접었다 편다.
        (로그창은 v01.09 부터 창 맨 아래 - Controls 를 숨겨도 로그는 보인다.)
        """
        inner = QVBoxLayout()
        inner.setContentsMargins(6, 2, 6, 6)
        inner.setSpacing(4)

        inner.addWidget(self._build_profile_group())
        inner.addWidget(self._build_create_group())
        inner.addWidget(self._build_color_group())

        self._controls_box = CollapsibleBox("Controls", inner)
        # 접으면 스플리터의 위 pane 도 헤더 높이로 줄여 버튼 영역에 공간을 넘긴다.
        self._controls_box.toggled.connect(self._on_controls_toggled)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._controls_box)
        # View > Show Controls 가 통째로 숨기고 보이는 위 pane.
        self._controls_pane = scroll
        return scroll

    # ---------------------------------------------------- 위 칸 높이 맞춤

    def showEvent(self, event):
        super().showEvent(event)
        # 처음 보일 때 한 번: 테마(폰트)가 입혀진 뒤라 그룹들의 실제 높이를 잴 수 있다.
        if not getattr(self, "_fitted", False):
            self._fitted = True
            self._fit_controls_height()

    def _fit_controls_height(self):
        """위 칸을 Controls 내용의 최소 높이에 맞춰 **스크롤 없이 전부 보이게** 연다.

        폰트·테마에 따라 높이가 달라 상수로 박을 수 없다. 가로 스크롤바가 생기면 그 두께가
        뷰포트를 깎아 세로 스크롤바를 부르므로 그 두께(PM_ScrollBarExtent)를 여유로 더한다.
        사용자가 핸들로 더 줄이는 것은 막지 않는다. 반환: 적용한 위 칸 높이.
        """
        pane = self._controls_pane
        need = (self._controls_box.minimumSizeHint().height()
                + 2 * pane.frameWidth()
                + pane.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 4)
        self._controls_fit_h = need
        if pane.isHidden() or not self._controls_box._header.isChecked():
            return need
        sizes = self._splitter.sizes()
        total = sum(sizes) or (need + 430)
        self._splitter.setSizes([need, max(40, total - need)])
        return need

    # ---------------------------------------------------- Controls 숨김/표시

    def controls_visible(self):
        """위 pane(Controls)이 보이는가. main_window 의 View 메뉴 체크 상태와 맞춘다."""
        return not self._controls_pane.isHidden()

    def set_controls_visible(self, visible):
        """Controls pane 을 통째로 숨기거나 보인다. 돌려주는 값은 적용된 상태.

        접기(CollapsibleBox)와 다르다 - 접기는 헤더 줄과 스크롤 영역의 최소 높이가
        남지만, 숨기면 스플리터가 그 위젯과 핸들을 없는 것으로 치고 버튼 모음이 전체를
        쓴다. 다시 보일 때는 숨기기 직전의 스플리터 비율로 돌아간다.
        상태는 prefs 에 저장해 다음에 열 때도 같다.
        """
        visible = bool(visible)
        if visible == self.controls_visible():
            prefs_mod.set_setting(SHOW_CONTROLS_KEY, visible)
            return visible

        if visible:
            self._controls_pane.setVisible(True)
            sizes = getattr(self, "_sizes_before_hide", None)
            if sizes and sum(sizes) > 0:
                self._splitter.setSizes(sizes)
            else:
                # 숨긴 채로 열렸다가 처음 보이는 경우 - 내용 높이에 맞춘다.
                self._fit_controls_height()
        else:
            self._sizes_before_hide = self._splitter.sizes()
            self._controls_pane.setVisible(False)

        prefs_mod.set_setting(SHOW_CONTROLS_KEY, visible)
        return visible

    def _on_controls_toggled(self, expanded):
        """Controls 박스를 접으면 위 pane 을 헤더만 남기고 아래 pane 을 넓힌다."""
        splitter = getattr(self, "_splitter", None)
        if splitter is None:
            return
        sizes = splitter.sizes()
        total = sum(sizes) or 1
        if expanded:
            # 접기 직전 높이로 복원(없으면 내용에 맞춘 높이).
            top = getattr(self, "_controls_expanded_h",
                          getattr(self, "_controls_fit_h", CONTROLS_HEIGHT_FALLBACK))
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
        self._scroll = scroll

        # 드래그 중 놓일 자리를 보여 주는 가로줄 (v01.15). 레이아웃 항목이 아닌 컨테이너의 자식이라
        # 재렌더(_render_categories)에 지워지지 않고, 컨테이너와 함께 스크롤된다.
        self._drop_line = QFrame(self._cat_container)
        self._drop_line.setObjectName("A00340_drop_line")
        self._drop_line.setStyleSheet(
            "QFrame#A00340_drop_line {{ background-color: {c}; border: none; }}".format(c=CHECK_HILITE_HEX))
        self._drop_line.hide()

        # 드래그 중 가장자리 자동 스크롤 - 커서가 멈춰 있어도 내용이 움직이므로 틱마다 다시 계산한다.
        self._drag_timer = QTimer(self)
        self._drag_timer.setInterval(40)
        self._drag_timer.timeout.connect(self._on_drag_tick)

        # v01.16 : `Add` 체크를 Create 그룹에서 이 pane 맨 위로 옮겼다. 버튼을 누를 때마다 쓰는 옵션인데
        #          Controls 를 접거나(View > Show Controls 로) 숨기면 같이 사라졌다. 이 pane 은 늘 보인다.
        self.chk_add = QCheckBox("Add")
        self.chk_add.setToolTip(
            "When on, clicking a button adds to the current selection "
            "instead of replacing it.")
        add_row = QHBoxLayout()
        add_row.setContentsMargins(2, 0, 2, 0)
        add_row.addWidget(self.chk_add)
        add_row.addStretch(1)

        pane = QWidget()
        pane_layout = QVBoxLayout(pane)
        pane_layout.setContentsMargins(0, 0, 0, 0)
        pane_layout.setSpacing(2)
        pane_layout.addLayout(add_row)
        pane_layout.addWidget(scroll, 1)
        return pane

    def _build_profile_group(self):
        # 프로파일(캐릭터/에셋처럼 JSON 별로 나뉜 선택 버튼 묶음) 선택 + 관리.
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

        btn_selection = QPushButton("Selection")
        btn_selection.setToolTip(
            "Capture the current Maya selection into a new button")
        btn_selection.clicked.connect(self.on_create_selection)

        # `Add` 체크는 v01.16 부터 버튼 모음 pane 위(_build_buttons_pane) - Controls 를 접어도 보이게.
        row.addWidget(btn_category)
        row.addWidget(btn_selection)
        row.addStretch(1)

        return group

    def _build_color_group(self):
        # 색칠 모드: 카테고리를 넘나들며 여러 버튼을 골라 한 색으로 칠한다.
        group = QGroupBox("Color")
        row = QHBoxLayout(group)

        # 모드 토글. 켜면 버튼이 체크형이 되고 클릭이 '선택' 대신 '체크'로 바뀐다.
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
        self._cat_boxes = []
        self._drop_line.hide()
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

        for cat_index, cat in enumerate(categories):
            self._cat_layout.addWidget(self._build_category_box(cat_index, cat))

    def _build_category_box(self, cat_index, cat):
        box = QGroupBox(cat["name"])
        box.setToolTip("Right-click: edit\nDrag a button to reorder it or move it to another category")
        box.setContextMenuPolicy(Qt.CustomContextMenu)
        cat_name = cat["name"]
        box.customContextMenuRequested.connect(
            lambda pos, b=box, n=cat_name: self._show_category_menu(n, b, pos)
        )

        v = QVBoxLayout(box)

        buttons = cat.get("buttons", [])
        btn_widgets = []
        if not buttons:
            empty = QLabel("(no buttons — use 'Selection' to add)")
            empty.setEnabled(False)
            v.addWidget(empty)
        else:
            for btn_index, btn_data in enumerate(buttons):
                btn = self._build_selection_button(cat_name, btn_data, (cat_index, btn_index))
                v.addWidget(btn)
                btn_widgets.append(btn)

        self._cat_boxes.append((box, cat_index, btn_widgets))
        return box

    def _build_selection_button(self, cat_name, btn_data, drag_key=None):
        objects = btn_data.get("objects", [])
        btn = _DragButton("{0}  ({1})".format(btn_data["name"], len(objects)), self, drag_key)

        # 툴팁에 담긴 오브젝트를 보여준다(너무 길면 앞부분만).
        preview = "\n".join(objects[:20])
        if len(objects) > 20:
            preview += "\n... (+{0} more)".format(len(objects) - 20)
        btn.setToolTip(preview or "(empty)")

        name = btn_data["name"]
        color_hex = btn_data.get("color")

        if self._color_mode:
            # 색칠 모드: 버튼을 체크형으로. 클릭은 '선택' 대신 '체크 토글'. 드래그는 끈다.
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
            # Apply/Clear 에서 위젯의 실제 체크 상태를 다시 읽기 위해 보관.
            self._color_buttons.append((btn, cat_name, name))
        else:
            # 일반 모드: 지정색이 있으면 입히고, 클릭하면 오브젝트를 선택한다.
            if color_hex:
                btn.setStyleSheet(_button_stylesheet(color_hex))
            btn.clicked.connect(
                lambda *_a, c=cat_name, n=name: self._on_button_clicked(c, n))

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

    def on_create_selection(self):
        names = self._category_names()
        if not names:
            QMessageBox.information(self, TITLE, "Create a category first.")
            return

        # 현재 마야 선택을 캡처한다. 비었으면 만들지 않는다.
        objects = maya_select.capture_selection()
        if not objects:
            QMessageBox.information(
                self, TITLE, "Select objects in Maya first.")
            return

        # 카테고리 / 버튼 이름을 한 다이얼로그에서 입력받는다(중복 시 재시도).
        dlg = AddSelectionDialog(names, len(objects), self)
        while True:
            if dlg.exec_() != QDialog.Accepted:
                return

            cat_name, label = dlg.values()

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

        cat["buttons"].append({"name": label, "objects": objects})
        self._save_and_render()
        self._log("Created '{0}' with {1} object(s)."
                  .format(label, len(objects)))

    # ============================================================ select

    def _on_button_clicked(self, cat_name, btn_name):
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None:
            return

        objects = btn_data.get("objects", [])
        add = self.chk_add.isChecked()
        found, missing = maya_select.select_objects(objects, add=add)

        msg = "Selected {0} object(s)".format(len(found))
        if add:
            msg += " (added)"
        if missing:
            msg += " — {0} missing: {1}".format(
                len(missing), ", ".join(missing[:5]))
            if len(missing) > 5:
                msg += ", ..."
        self._log(msg)

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
        act_update = menu.addAction("Update Objects (replace with selection)")
        act_add = menu.addAction("Add Objects (append selection)")
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
        elif chosen == act_update:
            self._update_button_objects(cat_name, btn_name, append=False)
        elif chosen == act_add:
            self._update_button_objects(cat_name, btn_name, append=True)
        elif chosen == act_set_color:
            self._set_button_color(cat_name, btn_name)
        elif chosen == act_reset_color:
            self._reset_button_color(cat_name, btn_name)
        elif chosen == act_category:
            self._change_button_category(cat_name, btn_name)
        elif chosen == act_delete:
            self._delete_button(cat_name, btn_name)

    # ============================================================ edit/delete

    # ===================================================== drag to reorder (v01.15)

    def begin_drag(self, button):
        """_DragButton 이 드래그 시작을 알린다. 커서를 손 모양으로, 자동 스크롤 틱 시작."""
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
        y = self._cat_container.mapFromGlobal(global_pos).y()

        chosen = None
        best = None
        for entry in self._cat_boxes:
            g = entry[0].geometry()
            if g.top() <= y <= g.bottom():
                chosen = entry
                break
            dist = g.top() - y if y < g.top() else y - g.bottom()
            if best is None or dist < best[0]:
                best = (dist, entry)
        if chosen is None:
            chosen = best[1]

        _box, cat_index, btn_widgets = chosen
        insert = 0
        for btn in btn_widgets:
            if btn.mapTo(self._cat_container, btn.rect().center()).y() < y:
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
            y = bg.top() + bg.height() // 2         # 빈 카테고리 - 안내 라벨 자리 가운데
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
                    self, TITLE,
                    "Button '{0}' already exists in '{1}'.".format(moved["name"], cats[t_cat]["name"]))
                return
            src.pop(s_idx)
            dst.insert(max(0, min(t_idx, len(dst))), moved)
            self._log("Moved '{0}' to category '{1}'.".format(moved["name"], cats[t_cat]["name"]))

        self._save_and_render()

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

    def _update_button_objects(self, cat_name, btn_name, append):
        """버튼의 오브젝트 목록을 현재 선택으로 교체(append=False)하거나 이어붙인다.

        append=True 면 기존 목록에 없는 것만 뒤에 더한다(순서/중복 보존).
        """
        btn_data = self._find_button(cat_name, btn_name)
        if btn_data is None:
            return

        objects = maya_select.capture_selection()
        if not objects:
            QMessageBox.information(
                self, TITLE, "Select objects in Maya first.")
            return

        if append:
            existing = btn_data.get("objects", [])
            merged = list(existing)
            for obj in objects:
                if obj not in merged:
                    merged.append(obj)
            btn_data["objects"] = merged
            self._log("Added to '{0}': now {1} object(s)."
                      .format(btn_name, len(merged)))
        else:
            btn_data["objects"] = objects
            self._log("Updated '{0}' to {1} object(s)."
                      .format(btn_name, len(objects)))

        self._save_and_render()

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
