# last Update date 25 12 05
# Python Script by Ji Hun Park

# Quickk Tool V01.01

import maya.cmds as cmds;

def JUN_cmd_update_window_for_anim(is_selected_only):
    if is_selected_only:
        cmds.playbackOptions(view ="active") 
    else:
        cmds.playbackOptions(view ="all") 

def PY_JUN_makeUI_QuickTool_v01_01 ():
    str_winTitle = "Quick Tool V01.01";
    str_winName = "Junny_win_Quick_tool";
    win_width = 300;
    win_height = 400;


    color_mainDark = [0.10, 0.12, 0.18]
    color_main     = [0.14, 0.17, 0.25]
    color_sub      = [0.18, 0.22, 0.32]
    color_btn      = [0.30, 0.35, 0.45]
    color_back     = [0.12, 0.14, 0.20]
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="FKIK General Tool V01.01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: __-NOV-2025\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    

    #===================================================================================
    #===================================================================================
    # Tab All (open)
    #===================================================================================
    #===================================================================================
    
    cmds.columnLayout(adjustableColumn=True, 
                      columnAttach=('both', 5), 
                      rowSpacing=6, 
                      bgc =color_mainDark);
    
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    
    cmds.text( align="left", label='Update window' );

    cmds.setParent( '..' )

    cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))


    cmds.button( h = win_height/40,
                 label='Selected', 
                 bgc=color_btn, 
                 command=f'JUN_cmd_update_window_for_anim({1})');
    
    cmds.button( h = win_height/40,
                 label='All Window', 
                 bgc=color_btn, 
                 command=f'JUN_cmd_update_window_for_anim({0})');

    cmds.setParent( '..' )

    cmds.setParent( '..' )

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_Quick_tool_v01_01():
    PY_JUN_makeUI_QuickTool_v01_01();

PY_JUN_makeUI_QuickTool_v01_01();