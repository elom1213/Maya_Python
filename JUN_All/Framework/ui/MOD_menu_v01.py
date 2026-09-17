# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
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

import maya.cmds as cmds

from Framework.core import tool_menu


def add_common_items(menu_title, tool_file=None, tool_name=None, divider=True):
    """지금 열려 있는 cmds.menu 에 그 메뉴의 공통 항목을 붙인다. 만든 menuItem 이름들을 돌려준다."""
    specs = tool_menu.common_items(menu_title)
    if not specs:
        return []

    tool_dir = tool_menu.tool_dir_from_path(tool_file) if tool_file else None
    name = tool_name or (tool_menu.tool_name_from_path(tool_file) if tool_file else None)

    created = []
    if divider:
        created.append(cmds.menuItem(divider=True))

    for spec in specs:
        created.append(cmds.menuItem(
            label=spec.label,
            annotation=spec.tooltip,
            command=_make_command(spec, name, tool_dir)))
    return created


def _make_command(spec, tool_name, tool_dir):
    # cmds 는 command 에 checked 값 하나를 넘긴다 - *args 로 받고 버린다.
    def _run(*_args):
        ctx = tool_menu.MenuContext(tool_name=tool_name, tool_dir=tool_dir)
        try:
            spec.callback(ctx)
        except Exception as exc:
            ctx.log("[{0}] Failed : {1}".format(spec.label, exc))
    return _run
