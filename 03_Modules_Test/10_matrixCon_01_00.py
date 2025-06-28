import maya.cmds as cmds

def JUN_makeUI_PY_matrixConstraintTool():
    win_title = "Connection Tool V04"
    win_name = "junnyWin_Connection_Tool_Window"
    win_width = 480
    win_height = 800
    tsl_height_tab2 = int(win_height * 0.27)

    color_mainDark = [0.65, 0.4, 0.4];
    color_main = [0.824, 0.457, 0.039];
    color_sub = [0.937, 0.597, 0.488];
    color_btn = [1.0, 0.8, 0.7];
    color_back = [1.0, 0.761, 0.6289];

    if cmds.window(win_name, exists=True):
        cmds.deleteUI(win_name)

    cmds.window(win_name, title=win_title, menuBar=True, resizeToFitChildren=True, bgc=color_main)

    # Help menu
    cmds.menuBarLayout (bgc=color_mainDark); 
    cmds.menu(label="Help", parent=win_name)
    cmds.menuItem(
        label="About",
        command=lambda *args: cmds.confirmDialog(
            title="About",
            messageAlign="left",
            message="Connection Tool V04\nWritten by Ji Hun Park\nUpdate date : 18-May-2022"
        )
    )

    # Main layout
    cmds.columnLayout(adjustableColumn=True, columnAttach=["both", 10])

    # Tab Layout
    tab_layout_all = cmds.tabLayout()

    # Tab 1: Multi Constrain
    tab_multi_cst = cmds.columnLayout(adjustableColumn=True, columnAttach=["both", 10], bgc=color_mainDark)

    # Pane layout for targets and followers
    cmds.paneLayout(configuration="vertical2")

    # Targets
    cmds.columnLayout(adjustableColumn=True, columnAttach=["both", 5], rowSpacing=5)
    cmds.frameLayout(bgc=[0.265625]*3, label="Targets")
    name_tex_num_tgt = cmds.text(label="Number : 0", align="left")
    name_tsl_tgt = cmds.textScrollList(h=win_height*0.5, numberOfRows=8, allowMultiSelection=True)
    cmds.setParent("..")

    cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
    cmds.button(label="Select", bgc=(0, 0.6, 0),
                command=lambda *args: JUN_cmd_upd_tex_numTsl(name_tsl_tgt, name_tex_num_tgt))
    cmds.setParent("..")

    cmds.rowLayout(nc=4)
    for label, func in [
        ("Add", "append"),
        ("Delete", "delete"),
        ("Up", 1),
        ("down", 0),
    ]:
        cmds.button(
            label=label,
            width=(win_width/8 - 12),
            command=lambda *args, f=func: (
                JUN_cmd_append_selected(name_tsl_tgt) if f == "append"
                else JUN_cmd_delete_selected(name_tsl_tgt) if f == "delete"
                else JUN_cmd_selMov(name_tsl_tgt, f)
            )
        )
    cmds.setParent("..")
    cmds.setParent("..")

    # Followers
    cmds.columnLayout(adjustableColumn=True, columnAttach=["both", 5], rowSpacing=5)
    cmds.frameLayout(bgc=[0.265625]*3, label="Followers")
    name_tex_num_flw = cmds.text(label="Number : 0", align="left")
    name_tsl_flw = cmds.textScrollList(h=win_height*0.5, numberOfRows=8, allowMultiSelection=True)
    cmds.setParent("..")

    cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
    cmds.button(label="Select", bgc=(0, 0.6, 0),
                command=lambda *args: JUN_cmd_upd_tex_numTsl(name_tsl_flw, name_tex_num_flw))
    cmds.setParent("..")

    cmds.rowLayout(nc=4)
    for label, func in [
        ("Add", "append"),
        ("Delete", "delete"),
        ("Up", 1),
        ("down", 0),
    ]:
        cmds.button(
            label=label,
            width=(win_width/8 - 12),
            command=lambda *args, f=func: (
                JUN_cmd_append_selected(name_tsl_flw) if f == "append"
                else JUN_cmd_delete_selected(name_tsl_flw) if f == "delete"
                else JUN_cmd_selMov(name_tsl_flw, f)
            )
        )
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    # Constrain options
    cmds.columnLayout(adjustableColumn=True, columnAttach=["both", 10], width=win_width)
    cmds.frameLayout(bgc=[0.265625]*3, label="Options")
    cmds.columnLayout(adjustableColumn=True)
    name_cb_maintain_off = cmds.checkBox(label="Maintain Offset")
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=5, columnWidth3=(60, 60, 60))
    name_rb_con_type = cmds.radioCollection()
    radio_buttons = [
        cmds.radioButton(label="Parent"),
        cmds.radioButton(label="Scale"),
        cmds.radioButton(label="Point"),
        cmds.radioButton(label="Orient"),
        cmds.radioButton(label="Point On Poly")
    ]
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    # Constrain button
    cmds.paneLayout(configuration="single")
    cmds.columnLayout(adjustableColumn=True, columnAttach=["both", 10], rowSpacing=10)
    cmds.button(
        label="Constrain",
        command=lambda *args: JUN_cmd_constrain_tgt_to_flw(
            name_tsl_tgt, name_tsl_flw, name_cb_maintain_off, name_rb_con_type
        )
    )
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.setParent("..")
    cmds.setParent("..")

    cmds.tabLayout(tab_layout_all, edit=True, tabLabel=((tab_multi_cst, "Constrain"),))

    cmds.text(label="Copyright (c) Ji Hun Park. All rights reserved.", align="right")

    cmds.showWindow(win_name)
    cmds.window(win_name, edit=True, widthHeight=(win_width, win_height))


# Call the function
JUN_makeUI_PY_matrixConstraintTool()