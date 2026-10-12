# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# Framework - 경로 항목의 우클릭 메뉴(Reveal in File Explorer / Copy file path) · 더블클릭 공용 헬퍼 (Qt)
#
# A00240_PathTool Tree 탭이 쓰던 `_on_tree_context_menu` · `_copy_path` · `_reveal` 을 공용으로 뽑았다
# (2026-10-12). 폴더 트리(JUN_mod_fileTree_qt_v01) · A00480 Maya 탭의 Maya File 리스트 · Reference 트리가
# 같은 메뉴 · 같은 문구 · 같은 실패 안내를 쓴다.
#
#   attach_path_context(view, path_of_item)   # 우클릭 메뉴 + 더블클릭(= Reveal) 을 뷰에 붙인다
#   show_path_menu(view, global_pos, path)    # 메뉴만 띄운다(직접 customContextMenuRequested 를 받을 때)
#   reveal_path(parent, path) / copy_path(parent, path)
#
# 탐색기 열기 자체는 Framework/core/file_opener.open_path (OS 비의존) 다.

import os

from Framework.qt.qt import (
    Qt,
    QApplication,
    QMenu,
    QMessageBox,
)
from Framework.core import file_opener

MENU_REVEAL = "Reveal in File Explorer"
MENU_COPY = "Copy file path"


def reveal_path(parent, path, title="Path"):
    """path 를 탐색기에서 연다(폴더=열기, 파일=그 폴더에서 선택). 실패는 다이얼로그로 안내."""
    if not path:
        return False
    try:
        file_opener.open_path(path)
        return True
    except FileNotFoundError:
        QMessageBox.warning(parent, title, "Path does not exist:\n{0}".format(path))
    except Exception as exc:  # noqa: BLE001 - 어떤 OS 오류도 사용자에게 안내
        QMessageBox.warning(parent, title, "Could not open path:\n{0}".format(exc))
    return False


def copy_path(parent, path, title="Path"):
    """path 의 **절대 경로**를 OS 네이티브 모양(윈도우는 `\\`)으로 클립보드에 넣는다.

    탐색기 주소창 · 파일 다이얼로그에 그대로 붙여넣을 수 있게 한다.
    """
    if not path:
        return False
    text = os.path.normpath(os.path.abspath(path))
    clipboard = QApplication.clipboard()
    if clipboard is None:
        QMessageBox.warning(parent, title, "Could not access the system clipboard.")
        return False
    clipboard.setText(text)
    return True


def show_path_menu(view, global_pos, path, title="Path"):
    """Reveal / Copy 두 항목짜리 메뉴를 띄우고 고른 것을 실행한다. path 가 비면 아무것도 안 한다."""
    if not path:
        return None
    menu = QMenu(view)
    act_reveal = menu.addAction(MENU_REVEAL)
    act_copy = menu.addAction(MENU_COPY)
    chosen = menu.exec_(global_pos)
    if chosen == act_reveal:
        reveal_path(view, path, title)
    elif chosen == act_copy:
        copy_path(view, path, title)
    return chosen


def attach_path_context(view, path_of_item, title="Path", double_click=True):
    """QListWidget / QTreeWidget 에 우클릭 메뉴와 더블클릭(= Reveal) 을 붙인다.

    path_of_item(item) -> 절대경로 문자열(없으면 "" - 메뉴도 더블클릭도 무시).
    트리는 Qt 기본 "더블클릭으로 펼치기" 를 끈다(열 때마다 트리가 펼쳐졌다 접히지 않게 -
    펼치기는 화살표로). 리스트는 해당 없음.
    """
    view.setContextMenuPolicy(Qt.CustomContextMenu)

    def _on_menu(pos):
        item = view.itemAt(pos)
        if item is None:
            return
        show_path_menu(view, view.viewport().mapToGlobal(pos), path_of_item(item), title)

    view.customContextMenuRequested.connect(_on_menu)

    if double_click:
        if hasattr(view, "setExpandsOnDoubleClick"):
            view.setExpandsOnDoubleClick(False)

        def _on_double(item, *_args):
            reveal_path(view, path_of_item(item), title)

        view.itemDoubleClicked.connect(_on_double)
