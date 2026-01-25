# last Update date 26 01 26
# Python Script by Ji Hun Park

# Quickk Tool V01.04
# V01.04 : Create Create tool

import maya.cmds as cmds;
import maya.mel as mel
from functools import partial

#====================================================================
# call back functions (Start)

def JUN_cmd_update_window_for_anim(*is_selected_only, **kw_args):
    if is_selected_only[0]:
        cmds.playbackOptions(view ="active") 
    else:
        cmds.playbackOptions(view ="all") 

def JUN_cmd_print_selected(*args, **kwargs):
    print(cmds.ls(sl = True))

def JUN_cmd_importFBX_nrm(*args, **kwargs):
    mel.eval('FBXProperty "Import|IncludeGrp|Geometry|OverrideNormalsLock" -v 1')

def JUN_cmd_create_tex_file(*args, **kwargs):
    file__ =  mel.eval("shadingNode -asTexture -isColorManaged file")
    place2Tex__ =  mel.eval("shadingNode -asUtility place2dTexture;")

    lst_attr = ["coverage",
                "translateFrame",
                "rotateFrame",
                "mirrorU",
                "mirrorV",
                "stagger",
                "wrapU",
                "wrapV",
                "repeatUV",
                "offset",
                "rotateUV",
                "noiseUV",
                "vertexUvOne",
                "vertexUvTwo",
                "vertexUvThree",
                "vertexCameraOne"]

    for i in range(len(lst_attr)):
        cmds.connectAttr( place2Tex__ + "." + lst_attr[i], file__ + "." + lst_attr[i])

    cmds.connectAttr( place2Tex__ + ".outUV", file__ + ".uv")
    cmds.connectAttr( place2Tex__ + ".outUvFilterSize", file__ + ".uvFilterSize")


# call back functions (End)
#====================================================================


class JUN_ToolUI_QuickTool:
    def __init__(self):
        self.str_winTitle = "Quick Tool V01.04"
        self.str_headTitle = self.str_winTitle
        self.str_winName = "Junny_win_Quick_tool_V01_04"
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
        self.idx_importFBX_nrm = 2
        self.idx_create_tex_file = 3

        self.menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 26-JAN-2026\')".format(self.color_main)

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
        
        # Update window (open)

        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );
    
        cmds.text( align="left", label='Update window' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_updateWin])

        cmds.setParent( '..' )

        # Update window (close)


        # Print tool (open)

        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='print' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_printTool])

        cmds.setParent( '..' )

        # Print tool (close)

        # Import tool (open)
        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='Import option' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_importFBX_nrm])

        cmds.setParent( '..' )
        # Import tool (close)

        # Create tool (open)
        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='Create tool' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_create_tex_file])

        cmds.setParent( '..' )
        # Create tool (close)

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

           
def JUN_PY_Quick_tool_v01_04():
    JUN_Win_QuickTool = JUN_ToolUI_QuickTool()
    btn_specs =  [
                    # idx_updateWin : 0
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
                    # idx_printTool : 1
                    [
                        {
                            "label": "Print Selected",
                            "callback": JUN_cmd_print_selected,
                        }
                    ],
                    # idx_importFBX_nrm : 2
                    [
                        {
                            "label": "Import FBX normal",
                            "callback": JUN_cmd_importFBX_nrm
                        }
                    ],
                    # idx_create_tex_file : 3
                    [
                        {
                            "label": "Create texture file",
                            "callback": JUN_cmd_create_tex_file
                        }

                    ]
                ]
    
    JUN_Win_QuickTool.build(btn_specs)


#JUN_PY_Quick_tool_v01_04()
