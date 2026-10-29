# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# Framework.ui - maya.cmds 툴 창의 메뉴에 공통 항목을 넣는 헬퍼.
#
# PySide 툴의 `JUN_mod_menuBar_qt_v01` 과 **같은 목록**(Framework/core/tool_menu.py 의
# COMMON_MENUS)을 읽는다. cmds 메뉴는 "지금 열려 있는 menu 아래에 menuItem 이 붙는" 방식이라
# 위젯이 아니라 함수로 둔다.
#
# 사용법 - cmds.menu 의 항목들 **맨 끝**에서 부른다:
#
#     cmds.menuBarLayout()
#     cmds.menu(label='Help')
#     cmds.menuItem(label='About', command=self.show_about)
#     JUN_mod_menu.add_common_items('Help', tool_file=__file__)
#
# 지금 보이는 탭 (2026-10-29) - `Copy Tool Name + Tabs` 는 창 안의 cmds.tabLayout 중 **보이는 사슬**
# (바깥 tabLayout 의 선택 탭 안에 든 것만)의 선택 탭 라벨을 툴 이름 뒤에 붙인다. 창은 만든 menuItem 의
# 전체 경로(`window|menuBarLayout|menu|menuItem`) 첫 마디에서 알아내므로 툴 쪽 인자는 그대로다.
# 다른 창 이름을 쓰려면 `window=` 로 준다.

import maya.cmds as cmds

from Framework.core import tool_menu


def add_common_items(menu_title, tool_file=None, tool_name=None, divider=True, window=None):
    """지금 열려 있는 cmds.menu 에 그 메뉴의 공통 항목을 붙인다. 만든 menuItem 이름들을 돌려준다.

    window : 탭 경로를 셀 창 이름. 주지 않으면 만든 menuItem 경로의 첫 마디(창)를 쓴다.
    """
    specs = tool_menu.common_items(menu_title)
    if not specs:
        return []

    tool_dir = tool_menu.tool_dir_from_path(tool_file) if tool_file else None
    name = tool_name or (tool_menu.tool_name_from_path(tool_file) if tool_file else None)

    created = []
    if divider:
        created.append(cmds.menuItem(divider=True))

    for spec in specs:
        # 먼저 만들어 전체 경로를 받고, 그 경로에서 창을 알아내 command 를 건다.
        item = cmds.menuItem(label=spec.label, annotation=spec.tooltip)
        item_window = window or _window_of(item)
        cmds.menuItem(item, edit=True,
                      command=_make_command(spec, name, tool_dir, item_window))
        created.append(item)
    return created


def _window_of(ui_path):
    """`window|menuBarLayout|menu|menuItem` 의 첫 마디. 경로가 아니면 None."""
    if not ui_path or "|" not in str(ui_path):
        return None
    return str(ui_path).split("|")[0] or None


def _make_command(spec, tool_name, tool_dir, window=None):
    # cmds 는 command 에 checked 값 하나를 넘긴다 - *args 로 받고 버린다.
    def _run(*_args):
        ctx = tool_menu.MenuContext(
            tool_name=tool_name, tool_dir=tool_dir,
            tab_path=lambda: visible_tab_path(window))
        try:
            spec.callback(ctx)
        except Exception as exc:
            ctx.log("[{0}] Failed : {1}".format(spec.label, exc))
    return _run


# ======================================================================
# 지금 보이는 탭 (cmds.tabLayout)
# ======================================================================

def _tab_layouts_under(window):
    """그 창 아래의 tabLayout 전체 경로들(깊이 순)."""
    layouts = cmds.lsUI(controlLayouts=True, long=True) or []
    prefix = window + "|"
    found = []
    for path in layouts:
        if not path.startswith(prefix):
            continue
        try:
            if cmds.objectTypeUI(path) != "tabLayout":
                continue
        except Exception:
            continue
        found.append(path)
    found.sort(key=lambda p: (p.count("|"), p))
    return found


def _selected_child_path(tab_layout):
    """그 tabLayout 의 **선택된 탭 자식**의 전체 경로. 없으면 None."""
    child = cmds.tabLayout(tab_layout, query=True, selectTab=True)
    if not child:
        return None
    child = str(child)
    if "|" in child:
        return child
    return tab_layout + "|" + child


def _selected_label(tab_layout):
    labels = cmds.tabLayout(tab_layout, query=True, tabLabel=True) or []
    index = cmds.tabLayout(tab_layout, query=True, selectTabIndex=True) or 0
    if 1 <= index <= len(labels):
        return str(labels[index - 1]).strip()
    return ""


def visible_tab_path(window):
    """창(`cmds.window` 이름) 안에서 **지금 보이는 탭 라벨**들을 바깥 → 안쪽 순으로.

    바깥 tabLayout 의 선택 탭 라벨, 그 탭 안의 tabLayout 의 선택 탭 라벨, ... 순.
    다른(선택 안 된) 탭 속의 tabLayout 과 `visible` 이 꺼진 것은 제외. 창이 없으면 빈 리스트.
    """
    if not window:
        return []
    try:
        if not cmds.window(window, exists=True):
            return []
        layouts = _tab_layouts_under(window)
    except Exception:
        return []

    selected = {}
    for path in layouts:
        try:
            selected[path] = _selected_child_path(path)
        except Exception:
            selected[path] = None

    labels = []
    for path in layouts:
        try:
            if not cmds.control(path, query=True, visible=True):
                continue
            on_chain = True
            for other, child in selected.items():
                if other == path or not path.startswith(other + "|"):
                    continue
                if not child or not (path == child or path.startswith(child + "|")):
                    on_chain = False
                    break
            if not on_chain:
                continue
            label = _selected_label(path)
        except Exception:
            continue
        if label:
            labels.append(label)
    return labels
