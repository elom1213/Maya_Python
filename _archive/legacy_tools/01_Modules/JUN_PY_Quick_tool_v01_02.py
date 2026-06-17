# last Update date 26 01 07
# Python Script by Ji Hun Park

# Quickk Tool V01.02

import maya.cmds as cmds;
from functools import partial

def JUN_cmd_update_window_for_anim(*is_selected_only, **kw_args):
    if is_selected_only[0]:
        cmds.playbackOptions(view ="active") 
    else:
        cmds.playbackOptions(view ="all") 

def JUN_cmd_print_selected(*args, **kwargs):
    print(cmds.ls(sl = True))

class JUN_ToolUI_QuickTool:
    def __init__(self):
        self.str_winTitle = "Quick Tool V01.02";
        self.str_headTitle = "Quick Tool V01.02"
        self.str_winName = "Junny_win_Quick_tool_V01_02";
        self.win_width = 300;
        self.win_height = 400;
        self.btn_hight = self.win_height/40

        self.color_mainDark = [0.10, 0.12, 0.18]
        self.color_main     = [0.14, 0.17, 0.25]
        self.color_sub      = [0.18, 0.22, 0.32]
        self.color_btn      = [0.30, 0.35, 0.45]
        self.color_back     = [0.12, 0.14, 0.20]

        self.idx_updateWin = 0
        self.idx_printTool = 1

        self.menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 07-JAN-2026\')".format(self.color_main)

    def fun_dummy(self, *args , **kwargs):
        print("fun_dummy called")
        print("args :", args)
        print("kwargs :", kwargs)

    def build(self, btn_specs):

        if cmds.window( self.str_winName , exists=True ): 
            cmds.deleteUI( self.str_winName , window=True )
        
        cmds.window( self.str_winName, bgc=self.color_mainDark, title= self.str_headTitle)

        cmds.menuBarLayout (bgc=self.color_mainDark); 
    
        cmds.menu( label='Help' );
        cmds.menuItem( label='About', command = self.menu_cmd);

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_mainDark);
        
        # Update windpws

        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );
    
        cmds.text( align="left", label='Update window' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_updateWin])

        cmds.setParent( '..' )

        # Print tool

        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='print' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_printTool])

        cmds.setParent( '..' )


        cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

        cmds.showWindow(self.str_winName);
        cmds.window(self.str_winName, e = True, widthHeight = [self.win_width, self.win_height]);


    def create_buttons(self, button_specs):
        for spec in button_specs:
            self.create_btn(spec.get("label", "default"),
                            spec.get("callback", self.fun_dummy),
                            *spec.get("args", []),
                            **spec.get("kwargs", {}))
            
    def create_btn(self, flag_lable = "default", flag_command = None, *cb_args, **cb_kwargs):
        if flag_command is None:
            flag_command = self.fun_dummy
        cmds.button( h = self.btn_hight,
                     label= flag_lable, 
                     bgc=self.color_btn, 
                     command=partial(flag_command, *cb_args, **cb_kwargs));

           
def JUN_PY_Quick_tool_v01_02():
    JUN_Win_QuickTool = JUN_ToolUI_QuickTool()
    btn_specs =  [
                    [
                        {
                            "label": "Selected",
                            "callback": JUN_cmd_update_window_for_anim,
                            "args": [1]
                        },
                        {
                            "label": "All Windows",
                            "callback": JUN_cmd_update_window_for_anim,
                            "args": [0]
                        }
                    ],
                    [
                        {
                            "label": "Print Selected",
                            "callback": JUN_cmd_print_selected,
                        }
                    ]
                ]
    
    JUN_Win_QuickTool.build(btn_specs)


# JUN_PY_Quick_tool_v01_02()
