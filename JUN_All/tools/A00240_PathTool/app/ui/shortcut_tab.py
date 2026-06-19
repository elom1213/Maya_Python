# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - "ShortCut" tab (Qt, standalone)
#
# 사용자가 카테고리와 경로 버튼을 직접 만들고, 버튼을 누르면 그 경로가
# 탐색기로 열린다.
#   - 상단 "Create" 그룹: [Category] / [Path] 버튼
#       * Category: 새 카테고리(QGroupBox) 생성
#       * Path    : 어느 카테고리에 넣을지 물은 뒤 경로 버튼 생성
#   - 각 카테고리는 QGroupBox 로 구분, 그 안에 경로 버튼이 쌓인다.
#   - 수정/삭제는 우클릭 컨텍스트 메뉴(카테고리: Rename/Delete,
#     버튼: Rename/Change Path/Delete)로 한다. 화면을 깨끗하게 유지하고
#     항목이 늘어나도 잘 확장된다.

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
    QInputDialog,
    QFileDialog,
    QMessageBox,
    QMenu,
    Qt,
)

from ..core import prefs as prefs_mod
from ..core import path_opener


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


class ShortcutTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # 활성 프로파일과 그 데이터를 읽는다(없으면 Default 자동 생성).
        self._profile = prefs_mod.get_active()
        self._data = prefs_mod.load_profile(self._profile)

        self._build_ui()
        self._refresh_profiles()
        self._render_categories()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.addWidget(self._build_profile_group())
        root.addWidget(self._build_create_group())

        # 카테고리가 계속 늘어나므로 스크롤 영역에 담는다.
        self._cat_container = QWidget()
        self._cat_layout = QVBoxLayout(self._cat_container)
        self._cat_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._cat_container)
        root.addWidget(scroll, stretch=1)

    def _build_profile_group(self):
        # 프로파일(집/회사처럼 JSON 별로 나뉜 경로 묶음) 선택 + 관리.
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

        btn_path = QPushButton("Path")
        btn_path.setToolTip("Add a path button into a category")
        btn_path.clicked.connect(self.on_create_path)

        row.addWidget(btn_category)
        row.addWidget(btn_path)
        row.addStretch(1)

        return group

    # ============================================================ rendering

    def _render_categories(self):
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
            empty = QLabel("(no paths — use 'Path' to add)")
            empty.setEnabled(False)
            v.addWidget(empty)
        else:
            for btn_data in buttons:
                v.addWidget(self._build_path_button(cat_name, btn_data))

        return box

    def _build_path_button(self, cat_name, btn_data):
        btn = QPushButton(btn_data["name"])
        btn.setToolTip(btn_data["path"])

        path = btn_data["path"]
        name = btn_data["name"]

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
        act_rename = menu.addAction("Rename")
        act_path = menu.addAction("Change Path")
        act_category = menu.addAction("Change Category")
        act_delete = menu.addAction("Delete")

        chosen = menu.exec_(btn_widget.mapToGlobal(pos))
        if chosen == act_rename:
            self._rename_button(cat_name, btn_name)
        elif chosen == act_path:
            self._change_button_path(cat_name, btn_name)
        elif chosen == act_category:
            self._change_button_category(cat_name, btn_name)
        elif chosen == act_delete:
            self._delete_button(cat_name, btn_name)

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
