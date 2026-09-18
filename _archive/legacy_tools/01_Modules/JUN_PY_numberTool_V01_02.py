# -*- coding: utf-8 -*-
# last Update date 26 09 18
# Python Script by Ji Hun Park

# Number tool V01.02
# V01.01 : 오브젝트 리스트 -> 어트리뷰트 나열 -> 실수 하나 + jump 로 setAttr
# V01.02 : - 어트리뷰트 목록 = 모든 오브젝트가 **공통으로** 가진 것 (float / int / bool / enum)
#          - 고른 어트리뷰트 종류에 따라 입력칸이 바뀐다
#              float : 실수 Start + Step
#              int   : 정수 Start + Step
#              enum / bool : 항목 이름을 optionMenu 에서 고르고, Step = 몇 항목씩 건너뛸지
#          - Repeat every N : N 개마다 시작값으로 되돌아간다 (0,1,2,0,1,2 ...)
#          - 범위(min/max) 밖 값은 잘라서 넣고, 잠긴/연결된 어트리뷰트는 건너뛰고 알린다
#          - 키 걸린 어트리뷰트는 현재 프레임에 키를 찍고 setAttr
#          - 한 번의 undo
#
# 같은 기능이 A00145_RigConnect > Attribute > Set Value 로 이식되어 있다(현행은 그쪽).

import maya.cmds as cmds


WIN = "Junny_win_Number_Tools_V01_02"
TSL_OBJ = "JUN_numberTool_v0102_obj_tsl"
TSL_ATTR = "JUN_numberTool_v0102_attr_tsl"
TXT_OBJ_NUM = "JUN_numberTool_v0102_obj_num"
TXT_ATTR_NUM = "JUN_numberTool_v0102_attr_num"
TXT_INFO = "JUN_numberTool_v0102_info"
CB_CHANNEL = "JUN_numberTool_v0102_cb_channel"
FRM_NUM = "JUN_numberTool_v0102_frm_num"
FRM_ENUM = "JUN_numberTool_v0102_frm_enum"
FF_START = "JUN_numberTool_v0102_ff_start"
FF_STEP = "JUN_numberTool_v0102_ff_step"
IF_START = "JUN_numberTool_v0102_if_start"
IF_STEP = "JUN_numberTool_v0102_if_step"
OM_ITEM = "JUN_numberTool_v0102_om_item"
IF_ITEM_STEP = "JUN_numberTool_v0102_if_item_step"
IF_REPEAT = "JUN_numberTool_v0102_if_repeat"

_TYPE_KIND = {
    "double": "float", "float": "float", "doubleLinear": "float",
    "doubleAngle": "float", "floatLinear": "float", "floatAngle": "float",
    "time": "float",
    "long": "int", "short": "int", "byte": "int", "char": "int",
    "bool": "bool", "enum": "enum",
}


#===================================================================================
# functions : attribute
#===================================================================================

def JUN_attr_kind(obj, attr):
    try:
        if not cmds.attributeQuery(attr, node=obj, exists=True):
            return None
        if cmds.attributeQuery(attr, node=obj, numberOfChildren=True):
            return None
        return _TYPE_KIND.get(cmds.attributeQuery(attr, node=obj, attributeType=True))
    except Exception:
        return None


def JUN_enum_items(obj, attr):
    """[(이름, 값)]. `A:B=5:C` -> A=0, B=5, C=6."""
    if JUN_attr_kind(obj, attr) == "bool":
        return [("Off", 0), ("On", 1)]
    raw = cmds.attributeQuery(attr, node=obj, listEnum=True) or []
    items, value = [], 0
    for token in (raw[0].split(":") if raw else []):
        if not token:
            continue
        name = token
        if "=" in token:
            name, num = token.rsplit("=", 1)
            value = int(num)
        items.append((name, value))
        value += 1
    return items


def JUN_attr_range(obj, attr):
    lo = hi = None
    if cmds.attributeQuery(attr, node=obj, minExists=True):
        lo = cmds.attributeQuery(attr, node=obj, minimum=True)[0]
    if cmds.attributeQuery(attr, node=obj, maxExists=True):
        hi = cmds.attributeQuery(attr, node=obj, maximum=True)[0]
    return lo, hi


def JUN_visible_attrs(obj, channel_box_only):
    if channel_box_only:
        raw = (cmds.listAttr(obj, keyable=True) or []) + \
              (cmds.listAttr(obj, channelBox=True) or [])
        names = set()
        for a in raw:
            if "." in a:
                continue
            try:
                if cmds.attributeQuery(a, node=obj, hidden=True):
                    continue
            except Exception:
                pass
            names.add(a)
    else:
        names = set(a for a in (cmds.listAttr(obj, scalar=True) or []) if "." not in a)
    # blendShape 타겟(weight 별칭)
    if cmds.nodeType(obj) == "blendShape":
        names.update((cmds.aliasAttr(obj, q=True) or [])[::2])
    return names


def JUN_is_animated(plug):
    for node in cmds.listConnections(plug, s=True, d=False, scn=True) or []:
        t = cmds.nodeType(node)
        if t.startswith("animCurve") or t.startswith("animBlendNode"):
            return True
    return False


#===================================================================================
# functions : UI
#===================================================================================

def JUN_update_num(tsl, txt):
    n = cmds.textScrollList(tsl, q=True, numberOfItems=True)
    cmds.text(txt, e=True, label="Number: {0}".format(n))


def JUN_obj_items():
    return cmds.textScrollList(TSL_OBJ, q=True, allItems=True) or []


def JUN_sel_attr():
    sel = cmds.textScrollList(TSL_ATTR, q=True, selectItem=True) or []
    return sel[0] if sel else None


def JUN_cmd_obj_load(*_):
    cmds.textScrollList(TSL_OBJ, e=True, removeAll=True)
    cmds.textScrollList(TSL_OBJ, e=True, append=cmds.ls(sl=True, fl=True) or [])
    JUN_update_num(TSL_OBJ, TXT_OBJ_NUM)


def JUN_cmd_obj_add(*_):
    items = JUN_obj_items()
    for s in cmds.ls(sl=True, fl=True) or []:
        if s not in items:
            cmds.textScrollList(TSL_OBJ, e=True, append=s)
    JUN_update_num(TSL_OBJ, TXT_OBJ_NUM)


def JUN_cmd_obj_del(*_):
    for s in cmds.textScrollList(TSL_OBJ, q=True, selectItem=True) or []:
        cmds.textScrollList(TSL_OBJ, e=True, removeItem=s)
    JUN_update_num(TSL_OBJ, TXT_OBJ_NUM)


def JUN_cmd_obj_move(up, *_):
    items = JUN_obj_items()
    idx = [i - 1 for i in (cmds.textScrollList(TSL_OBJ, q=True, selectIndexedItem=True) or [])]
    if not idx:
        return
    order = idx if up else list(reversed(idx))
    for i in order:
        j = i - 1 if up else i + 1
        if 0 <= j < len(items):
            items[i], items[j] = items[j], items[i]
    new_idx = [max(0, i - 1) if up else min(len(items) - 1, i + 1) for i in idx]
    cmds.textScrollList(TSL_OBJ, e=True, removeAll=True)
    cmds.textScrollList(TSL_OBJ, e=True, append=items)
    for i in new_idx:
        cmds.textScrollList(TSL_OBJ, e=True, selectIndexedItem=i + 1)


def JUN_cmd_obj_sort(*_):
    items = sorted(JUN_obj_items())
    cmds.textScrollList(TSL_OBJ, e=True, removeAll=True)
    cmds.textScrollList(TSL_OBJ, e=True, append=items)


def JUN_cmd_obj_select(*_):
    sel = cmds.textScrollList(TSL_OBJ, q=True, selectItem=True) or []
    cmds.select([s for s in sel if cmds.objExists(s)])


def JUN_cmd_list_common(*_):
    objs = [o for o in JUN_obj_items() if cmds.objExists(o)]
    cmds.textScrollList(TSL_ATTR, e=True, removeAll=True)
    if not objs:
        cmds.warning("Number Tool : object list is empty")
        JUN_update_num(TSL_ATTR, TXT_ATTR_NUM)
        return
    cb_only = cmds.checkBox(CB_CHANNEL, q=True, value=True)
    common = JUN_visible_attrs(objs[0], cb_only)
    for o in objs[1:]:
        common &= JUN_visible_attrs(o, cb_only)
    order = [a for a in (cmds.listAttr(objs[0]) or []) if "." not in a]
    order = sorted(common - set(order)) + order     # 별칭(blendShape 타겟)은 앞에
    seen = set()
    for a in order:
        if a in common and a not in seen and JUN_attr_kind(objs[0], a):
            seen.add(a)
            cmds.textScrollList(TSL_ATTR, e=True, append=a)
    JUN_update_num(TSL_ATTR, TXT_ATTR_NUM)
    JUN_cmd_attr_changed()


def JUN_cmd_search(tf, *_):
    token = cmds.textField(tf, q=True, text=True)
    items = cmds.textScrollList(TSL_ATTR, q=True, allItems=True) or []
    cmds.textScrollList(TSL_ATTR, e=True, deselectAll=True)
    for i, a in enumerate(items):
        if token and token in a:
            cmds.textScrollList(TSL_ATTR, e=True, selectIndexedItem=i + 1)
            cmds.textScrollList(TSL_ATTR, e=True, showIndexedItem=i + 1)
            break
    JUN_cmd_attr_changed()


def JUN_cmd_attr_changed(*_):
    """어트리뷰트 종류에 맞춰 숫자 칸 / 항목 칸을 바꾼다."""
    objs = JUN_obj_items()
    attr = JUN_sel_attr()
    if not objs or not attr or not cmds.objExists(objs[0]):
        cmds.text(TXT_INFO, e=True, label="Attribute : -")
        return
    kind = JUN_attr_kind(objs[0], attr)
    at = cmds.attributeQuery(attr, node=objs[0], attributeType=True)
    info = "Attribute : {0}  ({1}".format(attr, at)
    is_enum = kind in ("enum", "bool")
    if not is_enum:
        lo, hi = JUN_attr_range(objs[0], attr)
        if lo is not None or hi is not None:
            info += ", range {0} ~ {1}".format("-" if lo is None else lo,
                                               "-" if hi is None else hi)
    cmds.text(TXT_INFO, e=True, label=info + ")")

    cmds.frameLayout(FRM_ENUM, e=True, visible=is_enum)
    cmds.frameLayout(FRM_NUM, e=True, visible=not is_enum)
    if is_enum:
        for mi in cmds.optionMenu(OM_ITEM, q=True, itemListLong=True) or []:
            cmds.deleteUI(mi)
        for name, value in JUN_enum_items(objs[0], attr):
            cmds.menuItem(parent=OM_ITEM, label="{0}  ({1})".format(name, value))
    else:
        is_int = kind == "int"
        cmds.rowLayout(FF_START + "_row", e=True, visible=not is_int)
        cmds.rowLayout(IF_START + "_row", e=True, visible=is_int)


def JUN_cmd_get(*_):
    objs = JUN_obj_items()
    attr = JUN_sel_attr()
    if not objs or not attr:
        return
    kind = JUN_attr_kind(objs[0], attr)
    value = cmds.getAttr("{0}.{1}".format(objs[0], attr))
    if kind in ("enum", "bool"):
        values = [v for _n, v in JUN_enum_items(objs[0], attr)]
        if int(value) in values:
            cmds.optionMenu(OM_ITEM, e=True, select=values.index(int(value)) + 1)
    elif kind == "int":
        cmds.intField(IF_START, e=True, value=int(value))
    else:
        cmds.floatField(FF_START, e=True, value=value)


def JUN_cmd_set(*_):
    objs = JUN_obj_items()
    attr = JUN_sel_attr()
    if not objs or not attr or not cmds.objExists(objs[0]):
        cmds.warning("Number Tool : list objects and select an attribute first")
        return
    kind = JUN_attr_kind(objs[0], attr)
    repeat = cmds.intField(IF_REPEAT, q=True, value=True)

    if kind in ("enum", "bool"):
        items = JUN_enum_items(objs[0], attr)
        start = cmds.optionMenu(OM_ITEM, q=True, select=True) - 1
        step = cmds.intField(IF_ITEM_STEP, q=True, value=True)
    elif kind == "int":
        start = cmds.intField(IF_START, q=True, value=True)
        step = cmds.intField(IF_STEP, q=True, value=True)
    else:
        start = cmds.floatField(FF_START, q=True, value=True)
        step = cmds.floatField(FF_STEP, q=True, value=True)

    done, skipped = 0, []
    cmds.undoInfo(openChunk=True, chunkName="NumberTool")
    try:
        for i, obj in enumerate(objs):
            k = i % repeat if repeat > 0 else i
            plug = "{0}.{1}".format(obj, attr)
            obj_kind = JUN_attr_kind(obj, attr) if cmds.objExists(obj) else None
            if obj_kind is None:
                skipped.append((plug, "no settable attribute"))
                continue
            if kind in ("enum", "bool"):
                name = items[(start + k * step) % len(items)][0]
                match = [v for n, v in JUN_enum_items(obj, attr) if n == name]
                if obj_kind not in ("enum", "bool") or not match:
                    skipped.append((plug, "no enum item '{0}'".format(name)))
                    continue
                value = match[0]
            else:
                if obj_kind in ("enum", "bool"):
                    skipped.append((plug, "is {0}".format(obj_kind)))
                    continue
                value = start + k * step
                if obj_kind == "int":
                    value = int(round(value))
                lo, hi = JUN_attr_range(obj, attr)
                if lo is not None and value < lo:
                    value = lo
                if hi is not None and value > hi:
                    value = hi
            if cmds.getAttr(plug, lock=True):
                skipped.append((plug, "locked"))
                continue
            animated = JUN_is_animated(plug)
            if cmds.listConnections(plug, s=True, d=False) and not animated:
                skipped.append((plug, "driven by a connection"))
                continue
            try:
                if animated:
                    cmds.setKeyframe(plug, value=value)
                cmds.setAttr(plug, value)
                done += 1
            except Exception as e:
                skipped.append((plug, str(e).strip()))
    finally:
        cmds.undoInfo(closeChunk=True)

    for plug, reason in skipped:
        print("Number Tool : {0} skipped - {1}".format(plug, reason))
    print("Number Tool : {0} value(s) set on {1}".format(done, attr))
    if skipped:
        cmds.warning("Number Tool : {0} skipped (see Script Editor)".format(len(skipped)))


#===================================================================================
# UI
#===================================================================================

def PY_JUN_makeUI_numberTool():
    win_width, win_height = 520, 640
    color_mainDark = [0.1, 0.15, 0.45]
    color_main = [0.0, 0.45, 0.75]
    color_sub = [0.4, 0.7, 0.9]
    color_btn = [0.7, 0.9, 1.0]
    color_white = [1.0, 1.0, 1.0]

    if cmds.window(WIN, exists=True):
        cmds.deleteUI(WIN, window=True)
    cmds.window(WIN, bgc=color_mainDark, title="Number Tool V01.02")

    cmds.menuBarLayout(bgc=color_mainDark)
    cmds.menu(label="Help")
    cmds.menuItem(label="About", command=lambda *_: cmds.confirmDialog(
        title="About", icon="information", button="OK", messageAlign="center",
        message=" Written by Ji Hun Park. \n Update date: 18-SEP-2026"))

    cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5),
                      rowSpacing=6, bgc=color_mainDark)

    # --- Objects / Common attributes ---
    cmds.frameLayout(label="Objects and the attributes they share",
                     collapsable=True, bgc=color_main)
    cmds.paneLayout(configuration="vertical2")

    cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5),
                      rowSpacing=5, bgc=color_sub)
    cmds.text(TXT_OBJ_NUM, align="left", label="Number: 0")
    cmds.textScrollList(TSL_OBJ, height=win_height * 0.32, allowMultiSelection=True,
                        selectCommand=JUN_cmd_obj_select)
    cmds.rowLayout(numberOfColumns=4)
    cmds.button(width=45, label="Add", bgc=color_btn, command=JUN_cmd_obj_add)
    cmds.button(width=45, label="Del", bgc=color_btn, command=JUN_cmd_obj_del)
    cmds.button(width=45, label="Up", bgc=color_btn,
                command=lambda *_: JUN_cmd_obj_move(True))
    cmds.button(width=45, label="Down", bgc=color_btn,
                command=lambda *_: JUN_cmd_obj_move(False))
    cmds.setParent("..")
    cmds.button(label="Load Selection", bgc=color_btn, command=JUN_cmd_obj_load)
    cmds.button(label="Sort", bgc=color_btn, command=JUN_cmd_obj_sort)
    cmds.setParent("..")

    cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5),
                      rowSpacing=5, bgc=color_sub)
    cmds.text(TXT_ATTR_NUM, align="left", label="Number: 0")
    cmds.textScrollList(TSL_ATTR, height=win_height * 0.32, allowMultiSelection=False,
                        selectCommand=JUN_cmd_attr_changed)
    cmds.checkBox(CB_CHANNEL, label="Channel Box Only", value=True,
                  changeCommand=JUN_cmd_list_common)
    cmds.button(label="List Common Attributes", bgc=color_btn,
                command=JUN_cmd_list_common)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text(label="Search : ")
    tf = cmds.textField(bgc=color_white)
    cmds.textField(tf, e=True, enterCommand=lambda *_: JUN_cmd_search(tf))
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.setParent("..")    # paneLayout
    cmds.setParent("..")    # frameLayout

    # --- Value ---
    cmds.frameLayout(label="Value", collapsable=True, bgc=color_main)
    cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5), rowSpacing=5)
    cmds.text(TXT_INFO, align="left", label="Attribute : -")

    cmds.frameLayout(FRM_NUM, labelVisible=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    cmds.rowLayout(FF_START + "_row", numberOfColumns=4)
    cmds.text(label="Start ", width=50)
    cmds.floatField(FF_START, width=120, precision=4, bgc=color_white)
    cmds.text(label="  Step ", width=50)
    cmds.floatField(FF_STEP, width=120, precision=4, bgc=color_white)
    cmds.setParent("..")
    cmds.rowLayout(IF_START + "_row", numberOfColumns=4, visible=False)
    cmds.text(label="Start ", width=50)
    cmds.intField(IF_START, width=120, bgc=color_white)
    cmds.text(label="  Step ", width=50)
    cmds.intField(IF_STEP, width=120, bgc=color_white)
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(FRM_ENUM, labelVisible=False, visible=False)
    cmds.rowLayout(numberOfColumns=4)
    cmds.text(label="Item ", width=50)
    cmds.optionMenu(OM_ITEM, width=160)
    cmds.text(label="  Step ", width=50)
    cmds.intField(IF_ITEM_STEP, width=80, bgc=color_white)
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=4)
    cmds.text(label="Repeat every ", width=90)
    cmds.intField(IF_REPEAT, width=60, minValue=0, value=0, bgc=color_white)
    cmds.text(label=" objects (0 = off)   ")
    cmds.button(label="Get", width=60, bgc=color_btn, command=JUN_cmd_get)
    cmds.setParent("..")

    cmds.button(label="Set Values", height=32, bgc=color_btn, command=JUN_cmd_set)
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.text(align="center", label="Copyright (c) Park Ji Hun. All rights reserved.")

    cmds.showWindow(WIN)
    cmds.window(WIN, e=True, widthHeight=[win_width, win_height])


def JUN_PY_numberTool_V01_02():
    PY_JUN_makeUI_numberTool()


PY_JUN_makeUI_numberTool()
