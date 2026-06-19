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
        return group

    def _make_tree_widget(self):
        """우클릭 Reveal 컨텍스트 메뉴가 붙은 QTreeWidget 을 만든다(메인/Expand 공용)."""
        tree = QTreeWidget()
        tree.setHeaderLabels(["Name"])
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        return tree

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
        tree.expandAll()

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

        dlg.exec_()

    def _on_tree_context_menu(self, pos):
        tree = self.sender()
        item = tree.itemAt(pos)
        if item is None:
            return

        menu = QMenu(tree)
        act_reveal = menu.addAction("Reveal in File Explorer")
        chosen = menu.exec_(tree.viewport().mapToGlobal(pos))
        if chosen == act_reveal:
            self._reveal(item.data(0, Qt.UserRole))

    def _reveal(self, path):
        if not path:
            return
        try:
            path_opener.open_path(path)
        except FileNotFoundError:
            QMessageBox.warning(self, "Tree", f"Path does not exist:\n{path}")
        except Exception as exc:  # noqa: BLE001 - 어떤 OS 오류도 사용자에게 안내
            QMessageBox.warning(self, "Tree", f"Could not open path:\n{exc}")
