# last Update date : 2026. 05. 10
# Python Script by Ji Hun Park

# uvTool V01.00
# V01.00 : create 


import maya.cmds as cmds;
import maya.mel as mel
from functools import partial

from . import config
from .utility import *
from Framework.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem

class JUN_ToolUI_uvTool_v01:
    def __init__(self):
        self.str_headTitle = "uvTool V01.00"
        self.str_winName = "Junny_win_uvTool_v01_V01_00"
        self.win_width = 300;
        self.win_height = 400;
        self.btn_hight = self.win_height/15
        self.updated = "10-MAY-2026"

        # =============================================================
        # set color them (open)
        colorThem_name = "coral_01"
        colorThem__ = JUN_mod_colorThem.ColorThemeRegistry.get(colorThem_name)

        self.color_mainDark = colorThem__.get("color_mainDark")
        self.color_main     = colorThem__.get("color_main")
        self.color_sub      = colorThem__.get("color_sub")
        self.color_btn      = colorThem__.get("color_btn")
        self.color_back     = colorThem__.get("color_back")

        self.color_all = colorThem__.as_dict()
        # set color them (close)
        # =============================================================

        #===================================================
        # tsl : main (open)

        self.cls_tsl_selected_obj = JUN_mod_tsl.JUN_mod_tsl_v01()

        self.name_tsl_uvTool_main = "tsl_uvTool_main"

        self.winSize_for_mod_tsl = {"window_height" : max(1, int(self.win_height*0.9)),
                                    "window_width" : max(1, int(self.win_width*0.5))}

        self.tsl_spec_uvTool_main__  = { "name_tsl" : self.name_tsl_uvTool_main,
                                         "name_title" : "Objects",
                                         "num_item" : "num_object_main",
                                         "able_btn_select" : False,
                                         "able_btn_edit" : False,
                                         **self.color_all,
                                         **self.winSize_for_mod_tsl }
        
        self.cls_tsl_selected_obj.set__(self.tsl_spec_uvTool_main__)

        # tsl : main (close)
        #===================================================


        #===================================================
        # btn spec (open)


        self.idx_set_objects = 0

        self.btn_specs = [
                            # idx_set_objects : 0
                            [
                                { 
                                    "label": "Catch Objects",
                                    "callback": JUN_cmd_set_object_for_uv,
                                    "kwargs": { "tsl_uvTool_main" : self.cls_tsl_selected_obj}
                                }
                            ]
                        ]


        # btn spec (close)
        #===================================================
       
    def show_about(self, *args):

        cmds.confirmDialog(
        title='About',
        icon='information',
        bgc=self.color_main,
        button='OK',
        messageAlign='center',
        message=f'Written by Ji Hun Park.\nUpdate date: {self.updated}'
        )

    def fun_dummy(self, *args , **kwargs):
        print("fun_dummy called")
        print("args :", args)
        print("kwargs :", kwargs)

    def build(self):

        if cmds.window( self.str_winName , exists=True ): 
            cmds.deleteUI( self.str_winName , window=True )
        
        cmds.window( self.str_winName, bgc=self.color_mainDark, title= self.str_headTitle)

        cmds.menuBarLayout (bgc=self.color_mainDark); 
    
        cmds.menu( label='Help' );
        cmds.menuItem( label='About', command = self.show_about);

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_mainDark);
        
        
        # ==================================================
        # tsl (open)
        
        cmds.frameLayout( label='Set Up', collapsable= True, bgc =self.color_main );

        self.create_buttons(self.btn_specs[self.idx_set_objects])

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);
        
        self.cls_tsl_selected_obj.build()

        cmds.setParent( '..' )

        cmds.setParent( '..' )

        # tsl (close)
        # ==================================================


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

           
def base__():
    JUN_Win_base = JUN_ToolUI_uvTool_v01()
    
    JUN_Win_base.build()

# Do not rename build__ funcion
def build__():
    base__()
