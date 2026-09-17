# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# Framework - 모든 툴 창의 메뉴에 공통으로 들어가는 항목(레지스트리) + 툴 이름 판정.
#
# 툴 창 위의 메뉴(`Help` 등)에 **모든 툴이 똑같이 가져야 하는 항목**을 한 곳에 적는다.
# 여기에 한 줄 더하면 이 레지스트리를 쓰는 모든 툴에 그 항목이 생긴다.
#
#   - PySide 툴     : Framework.qt.MOD_menuBar_qt_v01.JUN_mod_menuBar_qt_v01 (QMenuBar 대체)
#   - maya.cmds 툴  : Framework.ui.MOD_menu_v01.add_common_items (cmds.menu 안에서 호출)
#
# 두 UI 계열이 **같은 목록**을 읽는다 - 항목 정의를 UI 쪽에 두면 계열마다 따로 고쳐야 한다.
#
# 이 모듈은 maya / Qt 를 모듈 수준에서 import 하지 않는다(클립보드는 실행 시점에 lazy import).
# 그래서 standalone 툴이나 mayapy 에서도 import 만으로 깨지지 않는다.
#
# 공통 항목 추가 예:
#
#     def open_tool_folder(ctx):
#         ...
#
#     register_common_item("Help", MenuItemSpec(
#         "Open Tool Folder", open_tool_folder, "Open this tool's folder in Explorer"))
#
# 새 메뉴 제목("Tools" 등)을 주면 그 메뉴가 모든 툴의 메뉴 바에 새로 생긴다.

import os


# 툴 코드가 들어 있는 폴더들의 부모 폴더 이름 (JUN_All/tools/<툴 폴더>)
TOOLS_DIR_NAME = "tools"


# ======================================================================
# 툴 이름
# ======================================================================

def tool_dir_from_path(path):
    """툴 안의 아무 파일 경로(`__file__`)에서 **툴 폴더 경로**를 찾는다. 못 찾으면 None.

    1순위 : 부모가 `tools` 인 폴더 - `.../tools/A00060_jointTool_V03/app/ui/main_window.py`
    2순위 : `app` 폴더를 담은 폴더  - 릴리스/exe 처럼 `tools` 밖으로 복사된 PySide 툴 대비
    """
    if not path:
        return None

    # 폴더를 직접 넘기면 그 폴더부터, 파일이면(존재하지 않는 frozen 경로 포함) 그 파일의 폴더부터
    if os.path.isdir(path):
        cur = os.path.abspath(path)
    else:
        cur = os.path.dirname(os.path.abspath(path))

    # 1순위 : 부모 이름이 tools
    probe = cur
    while True:
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        if os.path.basename(parent).lower() == TOOLS_DIR_NAME:
            return probe
        probe = parent

    # 2순위 : app 폴더의 부모
    probe = cur
    while True:
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        if os.path.basename(probe) == "app":
            return parent
        probe = parent

    return None


def tool_name_from_path(path):
    """툴 폴더 **이름**(예: `A00060_jointTool_V03`). 못 찾으면 None."""
    tool_dir = tool_dir_from_path(path)
    return os.path.basename(tool_dir) if tool_dir else None


# ======================================================================
# 메뉴 항목 정의
# ======================================================================

class MenuContext(object):
    """항목이 눌렸을 때 콜백이 받는 정보.

    tool_name : 툴 폴더 이름 (못 찾았으면 None)
    tool_dir  : 툴 폴더 경로 (못 찾았으면 None)
    window    : 메뉴가 달린 창(QWidget). maya.cmds 툴은 None
    log       : 결과를 알리는 함수 log(message) - 툴 로그창이 있으면 거기로, 없으면 print
    """

    def __init__(self, tool_name=None, tool_dir=None, window=None, log=None):
        self.tool_name = tool_name
        self.tool_dir = tool_dir
        self.window = window
        self.log = log or _print_log


class MenuItemSpec(object):
    """공통 메뉴 항목 하나. callback(ctx: MenuContext) 을 부른다."""

    def __init__(self, label, callback, tooltip=""):
        self.label = label
        self.callback = callback
        self.tooltip = tooltip


def _print_log(message):
    print(message)


# ======================================================================
# 공통 동작
# ======================================================================

def copy_text_to_clipboard(text):
    """클립보드에 글자를 넣는다. 성공하면 True.

    Qt 는 여기서 lazy import 한다 - 마야와 PySide 툴은 늘 QApplication 이 떠 있다.
    """
    try:
        from Framework.qt.qt import QApplication
    except ImportError:
        return False

    app = QApplication.instance()
    if app is None:
        return False

    clipboard = QApplication.clipboard()
    clipboard.setText(text)
    return clipboard.text() == text


def copy_tool_name(ctx):
    """툴 폴더 이름을 클립보드로 - `A00060_jointTool_V03`."""
    if not ctx.tool_name:
        ctx.log("[Copy Tool Name] Could not find the tool folder name.")
        return False

    if not copy_text_to_clipboard(ctx.tool_name):
        ctx.log("[Copy Tool Name] Could not access the clipboard.")
        return False

    ctx.log("[Copy Tool Name] Copied to clipboard : {0}".format(ctx.tool_name))
    return True


# ======================================================================
# 레지스트리
# ======================================================================

# [(메뉴 제목, [MenuItemSpec, ...]), ...] - 리스트 순서가 곧 메뉴 바의 순서 · 메뉴 안의 순서다.
COMMON_MENUS = [
    ("Help", [
        MenuItemSpec(
            "Copy Tool Name",
            copy_tool_name,
            "Copy this tool's folder name (e.g. A00060_jointTool_V03) to the clipboard"),
    ]),
]


def common_menu_titles():
    """공통 메뉴 제목들(순서대로)."""
    return [title for title, _items in COMMON_MENUS]


def common_items(menu_title):
    """그 메뉴의 공통 항목들. 공통 메뉴가 아니면 빈 리스트."""
    for title, items in COMMON_MENUS:
        if title == menu_title:
            return list(items)
    return []


def register_common_item(menu_title, spec):
    """공통 항목을 더한다. 같은 label 이 이미 있으면 교체한다(리로드에 안전).

    **이미 만들어진 메뉴 바에는 반영되지 않는다** - 창을 다시 열면 생긴다.
    """
    for title, items in COMMON_MENUS:
        if title == menu_title:
            for i, item in enumerate(items):
                if item.label == spec.label:
                    items[i] = spec
                    return
            items.append(spec)
            return
    COMMON_MENUS.append((menu_title, [spec]))
