# last Update date : 
# Python Script by Ji Hun Park

# base V01.00
# V01.xx : 


import maya.cmds as cmds;
import maya.mel as mel
from functools import partial

from . import config
from .utility import *
from Framework.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem, JUN_mod_tfg, JUN_mod_omg, JUN_mod_cbg

class JUN_ToolUI_base:
    def __init__(self):
        self.str_headTitle = "Base Tool V01.00"
        self.str_winName = "Junny_win_base_tool_V01_00"
        self.win_width = 300;
        self.win_height = 500;
        self.btn_hight = self.win_height/40
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
        
        
        #
        # create content here
        #


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
    JUN_Win_base = JUN_ToolUI_base()
    
    JUN_Win_base.build()

# Do not rename build__ funcion
def build__():
    base__()
