# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - "Tree" tab (Qt, standalone)
#
# 사용자가 입력한 경로를 트리뷰로 보여준다(A00210 Path Structure 의 트리 표시와 동일 취지).
# 추가 기능:
#   1) Depth   : 보여줄 트리 깊이 제한(0 = 전체).
#   2) Show files : 폴더만 볼지, 파일까지 볼지 토글.
#   3) File Types : 스캔에서 발견된 확장자 중 표시할 것만 체크(A00210 File Manager 와 동일).
#   4) Expand  : 창이 작을 때 큰 창에서 트리를 본다.
#   5) 우클릭  : Reveal in File Explorer — 그 항목을 탐색기에서 연다(폴더=열기, 파일=선택).

import os

from Framework.qt.qt import (
    Qt,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QCheckBox,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
    QStyle,
)

from ..core import tree_scanner
from ..core import path_opener


class _CheckableMenu(QMenu):
    """체크 가능한 항목을 토글해도 닫히지 않는 메뉴(여러 확장자 연속 선택용)."""

    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action is not None and action.isEnabled() and action.isCheckable():
            action.trigger()
            return
        super().mouseReleaseEvent(event)


class TreeTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root_path = ""      # 마지막으로 빌드한 경로
        self._tree = None         # tree_scanner.build_tree() 결과(모든 파일 포함, 필터 전)
        self._type_states = {}    # 확장자(점 없음) -> 체크 여부
        self._type_actions = {}   # 확장자 -> File Types 메뉴 QAction

        # 지금 살아 있는 트리 위젯들(메인 + Expand 창). 필터·접기 규칙을 함께 먹인다.
        self._trees = []
        # Shift 로 한꺼번에 펼치는 중에는 itemExpanded 가 다시 들어와도 무시한다.
        # (안 그러면 자식마다 같은 작업을 반복해 깊은 트리에서 폭발한다)
        self._bulk = False

        # 폴더/파일 구분용 표준 아이콘(테마 무관). 1회 만들어 재사용한다.
        self._icon_dir = self.style().standardIcon(QStyle.SP_DirIcon)
        self._icon_file = self.style().standardIcon(QStyle.SP_FileIcon)

        self._build_ui()

    # ============================================================== build UI

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(self._build_controls())

        self.tree = self._make_tree_widget()
        root.addWidget(self.tree, stretch=1)

    def _build_controls(self):
        group = QGroupBox("Path Tree")
        layout = QVBoxLayout(group)

        # 경로 입력 + Browse
        path_row = QHBoxLayout()
        self.ipf_path = QLineEdit()
        self.ipf_path.setPlaceholderText("Folder path to show as a tree")
        self.ipf_path.returnPressed.connect(self.on_build)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._on_browse)
        path_row.addWidget(QLabel("Path"))
        path_row.addWidget(self.ipf_path, stretch=1)
        path_row.addWidget(btn_browse)
        layout.addLayout(path_row)

        # 옵션 행: Depth / Show files / File Types / Build / Expand
        opt_row = QHBoxLayout()

        opt_row.addWidget(QLabel("Depth"))
        self.spn_depth = QSpinBox()
        self.spn_depth.setRange(0, 99)
        self.spn_depth.setValue(3)
        self.spn_depth.setSpecialValueText("All")   # 0 일 때 'All' 로 표시
        self.spn_depth.setToolTip("How many levels deep to show (0 = All).")
        self.spn_depth.valueChanged.connect(self._on_depth_changed)
        opt_row.addWidget(self.spn_depth)

        # 폴더만 볼지(해제), 파일까지 볼지(체크).
        self.chk_show_files = QCheckBox("Show files")
        self.chk_show_files.setChecked(True)
        self.chk_show_files.setToolTip("Off = folders only.")
        self.chk_show_files.toggled.connect(self._on_show_files_toggled)
        opt_row.addWidget(self.chk_show_files)

        # 발견된 확장자 중 표시할 것만 고르는 체크 드롭다운(파일 표시일 때만 의미).
        self.btn_file_types = QToolButton()
        self.btn_file_types.setText("File Types")
        self.btn_file_types.setToolTip(
            "Choose which file extensions to show (after Build).")
        self.btn_file_types.setPopupMode(QToolButton.InstantPopup)
        self._types_menu = _CheckableMenu(self.btn_file_types)
        self.btn_file_types.setMenu(self._types_menu)
        opt_row.addWidget(self.btn_file_types)

        opt_row.addStretch(1)

        btn_build = QPushButton("Build Tree")
        btn_build.clicked.connect(self.on_build)
        opt_row.addWidget(btn_build)

        self.btn_expand = QPushButton("Expand")
        self.btn_expand.setToolTip("Open the tree in a larger window")
        self.btn_expand.clicked.connect(self.on_expand)
        opt_row.addWidget(self.btn_expand)

        layout.addLayout(opt_row)

        # 필터 행: 경로/파일 이름으로 찾기
        flt_row = QHBoxLayout()
        flt_row.addWidget(QLabel("Filter"))
        self.ipf_filter = QLineEdit()
        self.ipf_filter.setPlaceholderText("Find by name or path (space = AND)")
        self.ipf_filter.setToolTip(
            "Type part of a file/folder name, or part of the path.\n"
            "Several words separated by spaces must all match (AND).\n"
            "Matches stay visible with their parent folders, opened down to the hit.")
        self.ipf_filter.textChanged.connect(self._on_filter_changed)
        flt_row.addWidget(self.ipf_filter, stretch=1)

        btn_clear = QPushButton("Clear")
        btn_clear.setToolTip("Clear the filter and fold the tree back.")
        btn_clear.clicked.connect(self.ipf_filter.clear)
        flt_row.addWidget(btn_clear)

        self.lbl_filter_count = QLabel("")
        flt_row.addWidget(self.lbl_filter_count)

        layout.addLayout(flt_row)
        return group

    def _make_tree_widget(self):
        """우클릭 Reveal 컨텍스트 메뉴가 붙은 QTreeWidget 을 만든다(메인/Expand 공용)."""
        tree = QTreeWidget()
        tree.setHeaderLabels(["Name"])
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        # Shift 를 누른 채 펼치면/접으면 그 아래 전부에 같은 것을 적용한다.
        tree.itemExpanded.connect(self._on_item_expanded)
        tree.itemCollapsed.connect(self._on_item_collapsed)
        self._trees.append(tree)
        return tree

    # =============================================== 펼치기 규칙 (Shift 재귀)

    def _shift_held(self):
        return bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)

    def _on_item_expanded(self, item):
        if self._shift_held():
            self._set_expanded_deep(item, True)

    def _on_item_collapsed(self, item):
        if self._shift_held():
            self._set_expanded_deep(item, False)

    def _set_expanded_deep(self, item, expanded):
        """item 아래 **전부**를 펼치거나 접는다.

        ★ 재귀를 쓰지 않는다 - 경로는 수십 단계로 깊어질 수 있고, 더 중요하게는
        `setExpanded` 가 `itemExpanded` 를 **다시 쏘기** 때문이다. Shift 는 여전히
        눌려 있으므로 핸들러가 또 불려 같은 일을 반복한다. `_bulk` 로 한 번만 돌게 막고,
        명시적 스택으로 훑는다.

        접을 때 자손까지 접어 두는 것이 이 규칙의 핵심이다 - 그래야 **다시 그냥 펼쳤을 때
        한 단계만** 열린다(Qt 는 접어도 자식의 펼침 상태를 기억한다).
        """
        if self._bulk:
            return

        self._bulk = True
        try:
            stack = [item]
            while stack:
                node = stack.pop()
                node.setExpanded(expanded)
                for i in range(node.childCount()):
                    stack.append(node.child(i))
        finally:
            self._bulk = False

    def _fold_to_default(self, tree):
        """기본 상태로 접는다 - **루트만 펼치고 그 아래는 전부 접는다.**

        예전에는 `expandAll()` 이라 최하위까지 전부 열린 채로 나왔다. 루트(입력한 경로)만
        열어 두는 것은 빌드 직후 한 줄만 보이는 것을 막기 위해서다 - 루트 아래의 폴더는
        하나도 펼쳐져 있지 않다. Depth 를 바꾸면 다시 빌드되므로 그때도 이 상태로 돌아온다.
        """
        tree.collapseAll()
        root = tree.topLevelItem(0)
        if root is not None:
            self._set_expanded_deep(root, False)
            root.setExpanded(True)

    # ============================================================== actions

    def _on_browse(self):
        start = self.ipf_path.text().strip() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Folder", start)
        if path:
            self.ipf_path.setText(path)
            self.on_build()

    def on_build(self):
        """입력 경로를 (모든 파일 포함) 스캔해 캐시하고, File Types 메뉴를 갱신 후 그린다."""
        path = self.ipf_path.text().strip()
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "Tree", "Select a valid folder path.")
            return

        self._root_path = os.path.abspath(path)
        # 확장자 필터는 뷰 단계에서 적용하므로 스캔은 항상 전체 파일을 담는다.
        self._tree = tree_scanner.build_tree(
            self._root_path, max_depth=self.spn_depth.value())
        self._rebuild_type_menu(sorted(tree_scanner.collect_extensions(self._tree)))
        self._fill_tree(self.tree)

    def _on_depth_changed(self, _value):
        # 깊이는 스캔에 영향 → 이미 빌드한 경로가 있으면 다시 빌드한다.
        if self._root_path:
            self.on_build()

    def _on_show_files_toggled(self, checked):
        # 파일을 안 보이면 File Types 선택은 의미가 없으므로 비활성화.
        self.btn_file_types.setEnabled(checked)
        self._fill_tree(self.tree)

    # ------------------------------------------------- File Types 확장자 필터

    def _rebuild_type_menu(self, exts):
        """발견된 확장자들로 File Types 메뉴를 다시 만든다(이전 선택은 이름 기준 보존)."""
        self._type_states = {x: self._type_states.get(x, True) for x in exts}

        self._types_menu.clear()
        self._type_actions = {}

        self.act_all_types = self._types_menu.addAction("All")
        self.act_all_types.setCheckable(True)
        self.act_all_types.triggered.connect(self._on_all_types_toggled)
        self._types_menu.addSeparator()

        for x in exts:
            label = ("." + x) if x else "(no ext)"
            act = self._types_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(self._type_states[x])
            act.triggered.connect(
                lambda checked, ex=x: self._on_type_toggled(ex, checked))
            self._type_actions[x] = act

        self._sync_all_types_action()
        self._update_types_button_text()
        self.btn_file_types.setEnabled(self.chk_show_files.isChecked())

    def _on_type_toggled(self, ext, checked):
        self._type_states[ext] = checked
        self._sync_all_types_action()
        self._update_types_button_text()
        self._fill_tree(self.tree)

    def _on_all_types_toggled(self, checked):
        for ext, act in self._type_actions.items():
            act.setChecked(checked)
            self._type_states[ext] = checked
        self._update_types_button_text()
        self._fill_tree(self.tree)

    def _sync_all_types_action(self):
        all_on = all(self._type_states.values()) if self._type_states else True
        self.act_all_types.setChecked(all_on)

    def _update_types_button_text(self):
        if not self._type_actions:
            self.btn_file_types.setText("File Types")
            return
        selected = [x for x, on in self._type_states.items() if on]
        if len(selected) == len(self._type_actions):
            self.btn_file_types.setText("File Types: All")
        elif not selected:
            self.btn_file_types.setText("File Types: none")
        else:
            shown = ", ".join((x or "(no ext)") for x in selected[:3])
            more = "" if len(selected) <= 3 else f" +{len(selected) - 3}"
            self.btn_file_types.setText(f"File Types: {shown}{more}")

    def _checked_exts(self):
        """표시할 확장자 집합. 전부 체크(또는 메뉴 비어있음)면 None(=필터 없음)."""
        if not self._type_actions:
            return None
        checked = {x for x, on in self._type_states.items() if on}
        if len(checked) == len(self._type_actions):
            return None
        return checked

    # ------------------------------------------------------- tree rendering

    def _fill_tree(self, tree):
        """캐시된 트리에 현재 필터(Show files / File Types)를 적용해 위젯을 채운다."""
        tree.clear()
        if self._tree is None:
            return

        show_files = self.chk_show_files.isChecked()
        exts = self._checked_exts()

        root_item = self._make_item(self._tree, show_files, exts)
        tree.addTopLevelItem(root_item)

        # 기본은 접힌 상태. 필터가 걸려 있으면 그 규칙이 다시 펼쳐 준다.
        self._fold_to_default(tree)
        self._apply_filter(tree)

    def _make_item(self, node, show_files, exts):
        """node(폴더 가정)와 그 자식을 필터에 맞춰 QTreeWidgetItem 트리로 만든다."""
        item = QTreeWidgetItem([node["name"]])
        item.setData(0, Qt.UserRole, node["path"])
        item.setIcon(0, self._icon_dir)

        for child in node["children"]:
            if child["is_dir"]:
                item.addChild(self._make_item(child, show_files, exts))
            else:
                if not show_files:
                    continue
                if exts is not None and child.get("ext", "") not in exts:
                    continue
                leaf = QTreeWidgetItem([child["name"]])
                leaf.setData(0, Qt.UserRole, child["path"])
                leaf.setIcon(0, self._icon_file)
                item.addChild(leaf)

        return item

    # ============================================================== 필터

    def _on_filter_changed(self, _text):
        for tree in list(self._trees):
            self._apply_filter(tree)

    def _filter_tokens(self):
        """공백으로 나눈 토큰들(소문자). 비어 있으면 빈 리스트 = 필터 없음.

        ★ 구분자를 `/` 로 통일한다. 저장된 경로는 윈도우라 `\\` 인데 사람은 `tex/deep` 처럼
        `/` 로도 친다 - 안 맞춰 두면 같은 경로를 쳐도 안 걸린다(실측으로 밟았다).
        """
        text = self.ipf_filter.text().strip().lower().replace("\\", "/")
        return [t for t in text.split() if t]

    def _apply_filter(self, tree):
        """이름 **또는 경로**로 걸러 맞는 것과 그 부모만 남긴다.

        - 토큰은 **AND** 다(`char tex` -> 둘 다 들어간 것만). 공용 필터 위젯과 같은 규칙.
        - **전체 경로**로 본다. 이름은 경로의 일부라 이름 검색도 그대로 되고, 폴더 이름을
          치면 그 아래가 통째로 남는다("경로로 찾기").
        - 맞은 항목의 **부모는 함께 보여 준다** - 안 그러면 트리에서 닿을 수가 없다.
          그리고 맞은 곳까지 **펼쳐 준다**(접혀 있으면 찾아 놓고도 안 보인다).
        - 필터를 지우면 **기본 접힘 상태로 되돌린다**(3번 규칙과 같은 모양).

        재귀 대신 후위 순회 스택을 쓴다 - 자식의 판정이 부모에 올라와야 하므로 아래에서
        위로 접어 올린다.
        """
        if tree is None:
            return

        tokens = self._filter_tokens()
        root = tree.topLevelItem(0)
        if root is None:
            self.lbl_filter_count.setText("")
            return

        if not tokens:
            # 필터 없음 - 전부 보이게 하고 기본 접힘으로.
            stack = [root]
            while stack:
                node = stack.pop()
                node.setHidden(False)
                for i in range(node.childCount()):
                    stack.append(node.child(i))
            self._fold_to_default(tree)
            self.lbl_filter_count.setText("")
            return

        matched = self._mark_matches(root, tokens)

        # 맞은 것이 하나도 없으면 루트만 남는다(빈 화면보다 낫다).
        self.lbl_filter_count.setText("{0} match(es)".format(matched))

    def _mark_matches(self, root, tokens):
        """맞는 항목/조상만 보이게 하고 맞은 개수를 돌려준다."""
        # 1) 후위 순회 순서를 만든다(자식 -> 부모).
        order = []
        stack = [root]
        while stack:
            node = stack.pop()
            order.append(node)
            for i in range(node.childCount()):
                stack.append(node.child(i))
        order.reverse()

        matched = 0
        keep = {}          # id(item) -> 보여야 하는가

        for node in order:
            path = (node.data(0, Qt.UserRole) or node.text(0) or "")
            path = path.lower().replace("\\", "/")   # 토큰과 같은 구분자로
            self_hit = all(t in path for t in tokens)
            child_hit = any(keep.get(id(node.child(i)), False)
                            for i in range(node.childCount()))

            keep[id(node)] = self_hit or child_hit
            if self_hit:
                matched += 1

        # 2) 보이기/숨기기 + 맞은 곳까지 펼치기(자식이 맞은 폴더만 연다).
        self._bulk = True
        try:
            for node in order:
                show = keep.get(id(node), False)
                node.setHidden(not show)
                if show and node.childCount():
                    node.setExpanded(
                        any(keep.get(id(node.child(i)), False)
                            for i in range(node.childCount())))
        finally:
            self._bulk = False

        root.setHidden(False)      # 루트는 언제나 보인다(닿는 길)
        root.setExpanded(True)
        return matched

    # ----------------------------------------------------- expand / reveal

    def on_expand(self):
        if self._tree is None:
            QMessageBox.information(self, "Tree", "Build the tree first.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Tree — {self._root_path}")
        dlg.resize(800, 620)

        v = QVBoxLayout(dlg)
        big = self._make_tree_widget()
        self._fill_tree(big)
        v.addWidget(big, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dlg.reject)
        v.addWidget(buttons)

        try:
            dlg.exec_()
        finally:
            # 닫힌 창의 트리를 목록에 남겨 두면 다음 필터 입력이 죽은 위젯을 건드린다.
            if big in self._trees:
                self._trees.remove(big)

    def _on_tree_context_menu(self, pos):
        tree = self.sender()
        item = tree.itemAt(pos)
        if item is None:
            return

        menu = QMenu(tree)
        act_reveal = menu.addAction("Reveal in File Explorer")
        act_copy = menu.addAction("Copy file path")
        chosen = menu.exec_(tree.viewport().mapToGlobal(pos))

        if chosen == act_reveal:
            self._reveal(item.data(0, Qt.UserRole))
        elif chosen == act_copy:
            self._copy_path(item.data(0, Qt.UserRole))

    def _copy_path(self, path):
        """그 항목(폴더든 파일이든)의 **절대 경로**를 클립보드에 넣는다.

        경로는 OS 네이티브 모양(윈도우는 `\\`)으로 바꿔 탐색기 주소창·파일 다이얼로그에
        그대로 붙여넣을 수 있게 한다(`ShortCut` 탭이 경로를 다루는 방식과 같다).
        """
        if not path:
            return

        text = os.path.normpath(os.path.abspath(path))

        clipboard = QApplication.clipboard()
        if clipboard is None:
            QMessageBox.warning(self, "Tree", "Could not access the system clipboard.")
            return

        clipboard.setText(text)

    def _reveal(self, path):
        if not path:
            return
        try:
            path_opener.open_path(path)
        except FileNotFoundError:
            QMessageBox.warning(self, "Tree", f"Path does not exist:\n{path}")
        except Exception as exc:  # noqa: BLE001 - 어떤 OS 오류도 사용자에게 안내
            QMessageBox.warning(self, "Tree", f"Could not open path:\n{exc}")
