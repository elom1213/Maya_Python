# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-02
# A00340_SelectionTool - "Buttons" tab (Qt, in-Maya)
#
# 사용자가 카테고리와 선택 버튼을 직접 만들고, 버튼을 누르면 그 버튼에 저장된
# 오브젝트들이 마야 씬에서 선택된다. (구성/편집 방식은 A00240_PathTool 의 ShortCut
# 탭을 이식했다. 경로 대신 '현재 선택된 오브젝트 목록'을 버튼에 담는 점만 다르다.)
#
#   - 상단 "Profile" 그룹 : 선택 버튼 세트를 캐릭터/에셋별 JSON 으로 나눠 관리.
#   - 상단 "Create" 그룹  : [Category] / [Selection] 버튼.
#       * Category  : 새 카테고리(QGroupBox) 생성.
#       * Selection : 현재 마야 선택을 캡처해 새 선택 버튼으로 만든다.
#   - 각 카테고리는 QGroupBox, 그 안에 선택 버튼이 쌓인다.
#   - 버튼 클릭     : 저장된 오브젝트를 선택('Add' 체크 시 현재 선택에 누적).
#   - 추가/삭제/정렬/이름변경/선택갱신 : 우클릭 컨텍스트 메뉴로 한다.

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
    QScrollArea,
    QInputDialog,
    QMessageBox,
    QMenu,
    Qt,
)

from ..core import prefs as prefs_mod
from ..core import maya_select


TITLE = "Selection Tool"


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

        # 버튼 클릭 시 현재 선택을 지우지 않고 누적 선택할지.
        self.chk_add = QCheckBox("Add")
        self.chk_add.setToolTip(
            "When on, clicking a button adds to the current selection "
            "instead of replacing it.")

        row.addWidget(btn_category)
        row.addWidget(btn_selection)
        row.addStretch(1)
        row.addWidget(self.chk_add)

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
            empty = QLabel("(no buttons — use 'Selection' to add)")
            empty.setEnabled(False)
            v.addWidget(empty)
        else:
            for btn_data in buttons:
                v.addWidget(self._build_selection_button(cat_name, btn_data))

        return box

    def _build_selection_button(self, cat_name, btn_data):
        objects = btn_data.get("objects", [])
        btn = QPushButton("{0}  ({1})".format(btn_data["name"], len(objects)))

        # 툴팁에 담긴 오브젝트를 보여준다(너무 길면 앞부분만).
        preview = "\n".join(objects[:20])
        if len(objects) > 20:
            preview += "\n... (+{0} more)".format(len(objects) - 20)
        btn.setToolTip(preview or "(empty)")

        name = btn_data["name"]

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
        act_category = menu.addAction("Change Category")
        act_delete = menu.addAction("Delete")

        cat = self._find_category(cat_name)
        buttons = cat.get("buttons", []) if cat else []
        idx = next(
            (i for i, b in enumerate(buttons) if b["name"] == btn_name), -1
        )
        act_up.setEnabled(idx > 0)
        act_down.setEnabled(0 <= idx < len(buttons) - 1)

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
