# last Update date : 26.05.29
# Python Script by Ji Hun Park

# jointTool V02.05
# V02.00 : Create
# V02.01 : Updaet max joint num
# V02.02 : Update removing curves by length
# V02.03 : create separate curve util
# V02.04 : set joint radius on revere joints
# V02.05 : create select unused joints 


import maya.cmds as cmds;
import maya.mel as mel
from functools import partial

from . import config
from .utility import *
from Framework.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem, JUN_mod_tfg, JUN_mod_omg, JUN_mod_cbg

class JUN_ToolUI_base:
    def __init__(self):
        self.jntTool_version = "V02.05"
        self.jntTool_version__ = self.jntTool_version.replace(".", "_")
        self.str_headTitle = f"jointTool {self.jntTool_version}"
        self.str_winName = f"Junny_win_joint_tool_{self.jntTool_version__}"
        self.win_width = 300;
        self.win_height = 600;
        self.btn_hight = self.win_height/20
        self.updated = "29-MAY-2026"

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

        # =============================================================
        # tsl : main tsl (open)

        self.winSize_for_tsl_jointTool_main = { "window_height" : self.win_height-350,
                                                "window_width" : self.win_width-20}
        
        self.name_tsl_jointTool_name = "tsl_jointTool_main"

        self.tsl_jointTool_main = JUN_mod_tsl.JUN_mod_tsl_v01()

        self.tsl_spec_jointTool_main  = {   "name_tsl" : self.name_tsl_jointTool_name,
                                            "name_title" : "Joint Tool",
                                            "num_item" : "num_jointTool_main",
                                            **self.color_all,
                                            **self.winSize_for_tsl_jointTool_main }
        

        self.tsl_jointTool_main.set__(self.tsl_spec_jointTool_main)


        # tsl : main tsl (close)
        # =============================================================


        # =============================================================
        # cbg : remove origin (open)

        self.cbg_remove_origin = JUN_mod_cbg.JUN_mod_cbg_v01()  
        self.cbg_remove_origin_name = "remove_origin"
        self.cbg_remove_origin_Width = self.win_width *0.45
        self.cbg_remove_origin_columnWidth = (1, self.win_width * 0.3)
        self.cbg_remove_origin_lalbel = "Remove origin"
        self.cbg_remove_origin_value1 = True
        self.cbg_spec = {   "cbg_name" : self.cbg_remove_origin_name, 
                            "cbg_label" : self.cbg_remove_origin_lalbel,
                            "cbg_Width" : self.cbg_remove_origin_Width, 
                            "cbg_columnWidth" : self.cbg_remove_origin_columnWidth, 
                            "cbg_value1" : self.cbg_remove_origin_value1 }
        
        self.cbg_remove_origin.set__(self.cbg_spec)

        # cbg : remove origin (close)
        # =============================================================


        # =============================================================
        # tfg : tfg for every n cm (open)


        self.tfg_max_crv_len    = JUN_mod_tfg.JUN_mod_tfg_v01()  
        self.tfg_for_every_n_cm = JUN_mod_tfg.JUN_mod_tfg_v01()  
        self.tfg_max_jnts       = JUN_mod_tfg.JUN_mod_tfg_v01()  

        self.tfg_max_crv_len_name = "name_tfg_max_crv_len"
        self.tfg_max_crv_len_colWidth = [self.win_width * 0.25, self.win_width * 0.25]
        self.tfg_max_crv_len_lalbel = "Max Length :  "
        self.tfg_spec_tfg_max_crv_len = {   "tfg_name" : self.tfg_max_crv_len_name, 
                                            "tfg_columWidth" : self.tfg_max_crv_len_colWidth, 
                                            "tfg_label" : self.tfg_max_crv_len_lalbel,
                                            "tfg_is_editable" : True,
                                            "tfg_bck_color" : [1, 1, 1],
                                            "tfg_text" : "0.8" }
        
        self.tfg_for_every_n_cm_name = "name_tfg_for_every_n_cm"
        self.tfg_for_every_n_cm_colWidth = [self.win_width * 0.25, self.win_width * 0.25]
        self.tfg_for_every_n_cm_lalbel = "Interval :  "
        self.tfg_spec_export = {  "tfg_name" : self.tfg_for_every_n_cm_name, 
                                  "tfg_columWidth" : self.tfg_for_every_n_cm_colWidth, 
                                  "tfg_label" : self.tfg_for_every_n_cm_lalbel,
                                  "tfg_is_editable" : True,
                                  "tfg_bck_color" : [1, 1, 1],
                                  "tfg_text" : "2.5" }
        
        self.tfg_max_jnts_name = "name_tfg_max_jnts"
        self.tfg_max_jnts_colWidth = [self.win_width * 0.25, self.win_width * 0.25]
        self.tfg_max_jnts_lalbel = "Max joints :  "
        self.tfg_spec_max_jnts = {  "tfg_name" : self.tfg_max_jnts_name, 
                                  "tfg_columWidth" : self.tfg_max_jnts_colWidth, 
                                  "tfg_label" : self.tfg_max_jnts_lalbel,
                                  "tfg_is_editable" : True,
                                  "tfg_bck_color" : [1, 1, 1],
                                  "tfg_text" : "5" }
        
        self.tfg_max_crv_len.set__(self.tfg_spec_tfg_max_crv_len)
        self.tfg_for_every_n_cm.set__(self.tfg_spec_export)
        self.tfg_max_jnts.set__(self.tfg_spec_max_jnts)
        

        # tfg : tfg for every n cm (close)
        # =============================================================
      
        self.btn_specs =    { 
                                "separate_crv" :
                                [
                                    { 
                                        "label": "Separate Curve",
                                        "callback": JUN_separate_crv,
                                        "kwargs": {
                                                    "tsl_jointTool_main" : self.tsl_jointTool_main
                                                }
                                    }
                                ], 
                                "remove_crv_by_length" :
                                [
                                    { 
                                        "label": "Remove Curve",
                                        "callback": JUN_remove_crv_by_len,
                                        "kwargs": {
                                                    "tsl_jointTool_main" : self.tsl_jointTool_main,
                                                    "tfg_max_crv_len" : self.tfg_max_crv_len,
                                                }
                                    }
                                ], 
                                "rebuild_by_cv_count" :
                                [
                                    { 
                                        "label": "Rebuild Curve",
                                        "callback": JUN_rebuild_crv,
                                        "btn_hight": 50,
                                        "kwargs": {
                                                    "tsl_jointTool_main" : self.tsl_jointTool_main,
                                                    "tfg_for_every_n_cm" : self.tfg_for_every_n_cm,
                                                    "tfg_max_jnts" : self.tfg_max_jnts,
                                                }
                                    }
                                ], 
                                "reverse_joint" :
                                [
                                    { 
                                        "label": "Reverse joint chain ",
                                        "callback": JUN_reverse_joint,
                                        "kwargs": {
                                                    "tsl_jointTool_main" : self.tsl_jointTool_main,
                                                    "cbg_remove_origin" : self.cbg_remove_origin,
                                                }
                                    }
                                ],
                                "select_unused_joints" :
                                [
                                    { 
                                        "label": "Select Unused Joints ",
                                        "callback": select_unused_joints,
                                        "kwargs": {
                                                    "tsl_jointTool_main" : self.tsl_jointTool_main
                                                }
                                    }
                                ]
                            }
        
        

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
        
        # tsl ==================================================
        # tsl joint tool (open)

        cmds.frameLayout( label='Set Up', collapsable= True, bgc =self.color_main );

        # paneLayout vertical2" (open)

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);
        
        self.tsl_jointTool_main.build()

        cmds.setParent( '..' )

        cmds.setParent( '..' )

        # tsl joint tool (close)
        # tsl ==================================================

        # ==================================================
        # Sub Tool : Curve (open)

        cmds.frameLayout( label='Sub Tool : Curve', collapsable= True, bgc =self.color_main );

        self.create_buttons(self.btn_specs["separate_crv"])        

        cmds.paneLayout( configuration= "vertical2" )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);

        self.tfg_max_crv_len.build()        

        cmds.setParent( '..' )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);

        self.create_buttons(self.btn_specs["remove_crv_by_length"])        


        cmds.setParent( '..' )

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2" )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);

        self.tfg_for_every_n_cm.build()        
        self.tfg_max_jnts.build()        

        cmds.setParent( '..' )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);

        self.create_buttons(self.btn_specs["rebuild_by_cv_count"])        


        cmds.setParent( '..' )

        cmds.setParent( '..' )

        cmds.setParent( '..' )

        # Sub Tool : Curve (close)
        # ==================================================


        # ==================================================
        # Tool : Edit (open)

        cmds.frameLayout( label='Tool : Edit', collapsable= True, bgc =self.color_main );

        cmds.paneLayout( configuration= "vertical2" )

        self.cbg_remove_origin.build()

        self.create_buttons(self.btn_specs["reverse_joint"])        

        cmds.setParent( '..' )

        self.create_buttons(self.btn_specs["select_unused_joints"])        

        cmds.setParent( '..' )

        # Tool : Edit (close)
        # ==================================================

        cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

        cmds.showWindow(self.str_winName);
        cmds.window(self.str_winName, e = True, widthHeight = [self.win_width, self.win_height]);


    def create_buttons(self, button_specs):
        for spec in button_specs:
            self.create_btn(spec.get("label", "default"),
                            spec.get("callback", self.fun_dummy),
                            spec.get("btn_hight", self.btn_hight),
                            *spec.get("args", []),
                            **spec.get("kwargs", {}))
            
    def create_btn(self, flag_lable = "default", flag_command = None, btn_hight = None ,*cb_args, **cb_kwargs):
        if flag_command is None:
            flag_command = self.fun_dummy
        if btn_hight is None:
            btn_hight = self.btn_hight
        cmds.button( h = btn_hight,
                     label= flag_lable, 
                     bgc=self.color_btn, 
                     command=partial(flag_command, *cb_args, **cb_kwargs));

           
def base__():
    JUN_Win_base = JUN_ToolUI_base()
    
    JUN_Win_base.build()

# Do not rename build__ funcion
def build__():
    base__()
