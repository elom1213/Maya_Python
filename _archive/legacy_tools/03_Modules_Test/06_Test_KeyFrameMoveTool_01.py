# last Update date 23 01 24
# Python Script by Ji Hun Park

# KeyFrame Move Tool V01.01

import maya.cmds as cmds;

def JUN_cmd_KeyFrameMove(str_KeyFrameMov_ifg_MovNum):
    KeyFrame_MovNum = cmds.intFieldGrp(str_KeyFrameMov_ifg_MovNum, q=True, value1=True);
    set_AnimNods = set()
    selections = cmds.ls(sl=True,  fl=True)

    for selection in selections:
        JUN_upStreams = cmds.hyperShade(listUpstreamNodes=selection)
        for JUN_upStream in JUN_upStreams:
            upStream_typ = cmds.objectType(JUN_upStream)
            if JUN_upStream not in set_AnimNods and "animCurve" in upStream_typ:
                cmds.keyframe(JUN_upStream, edit=True, includeUpperBound=True, relative=True, option="over", timeChange=KeyFrame_MovNum)
                set_AnimNods.add(JUN_upStream)


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_KeyFrameMovTool ():
    str_winTitle = "KeyFrameMove Tool";
    str_winName = "Junny_win_KeyFrameMove_Tools";
    win_width = 480;
    win_height = 120;

    color_mainDark = [0.65, 0.4, 0.4];
    color_main = [0.824, 0.457, 0.039];
    color_sub = [0.937, 0.597, 0.488];
    color_btn = [1.0, 0.8, 0.7];
    color_back = [1.0, 0.761, 0.6289];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="KeyFrame Move Tool V01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 24-JAN-2023\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    

    #===================================================================================
    # UI: Colum Layout(open)
    #===================================================================================
    
    cmds.columnLayout(adjustableColumn=True, 
                      columnAttach=('both', 5), 
                      rowSpacing=6, 
                      bgc =color_mainDark, 
                      width = 390 );
         
    #===================================================================================
    # frameLayout : Tool  Selection(open)
    #===================================================================================
    
    cmds.frameLayout( label='Tool : KeyFame Move', collapsable= True, bgc =color_main );


    cmds.intFieldGrp( 'name_KeyFrameMov_ifg_MoveNum', 
                        columnAlign = [1, 'right'], 
                        columnWidth2 = [ 100, 280 ], 
                        label="Move number :"    );    


    #===================================================================================
    # frameLayout : Tool : Selection(close)
    #===================================================================================
    cmds.setParent( '..' )


    cmds.button( "name_btn_MoveKey", 
                 label='KeyFrame Move', 
                 bgc=color_btn, 
                 command='JUN_cmd_KeyFrameMove(\"name_KeyFrameMov_ifg_MoveNum\")');

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def KeyFrameMoveTool_V01_01():
    PY_JUN_makeUI_KeyFrameMovTool();

PY_JUN_makeUI_KeyFrameMovTool();