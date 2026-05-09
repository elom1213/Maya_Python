# last Update date 2026. 05. 09
# Python Script by Ji Hun Park

# file_exporter_v01 V01.00
# V01.00 : create


import maya.cmds as cmds;
import maya.mel as mel
import copy
from functools import partial
from .utility import *

import config
from Framework.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem, JUN_mod_tfg, JUN_mod_omg


class JUN_ToolUI_file_exporter:
    def __init__(self):
        self.str_headTitle = "File exporter Tool V01.00"
        self.str_winName = "Junny_win_file_exporter_tool_V01_00"
        self.win_width = 500;
        self.win_height = 600;
        self.btn_hight = self.win_height/25

        # set color them (open)
        colorThem_name = "blue_01"
        colorThem__ = JUN_mod_colorThem.ColorThemeRegistry.get(colorThem_name)

        self.color_mainDark = colorThem__.get("color_mainDark")
        self.color_main     = colorThem__.get("color_main")
        self.color_sub      = colorThem__.get("color_sub")
        self.color_btn      = colorThem__.get("color_btn")
        self.color_back     = colorThem__.get("color_back")

        self.color_all = colorThem__.as_dict()
        # set color them (close)

        self.menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 14-APR-2026\')".format(self.color_main)

        # custom


        #===================================================
        # tfg : Browser (open)

        self.tfg_export_path = JUN_mod_tfg.JUN_mod_tfg_v01()  

        self.tfg_export_path_name = "name_export_path__"
        self.tfg_export_path_colWidth = [100, 300]
        self.tfg_export_path_lalbel = "Export path  :  "
        self.tfg_spec_export = {  "tfg_name" : self.tfg_export_path_name, 
                                  "tfg_columWidth" : self.tfg_export_path_colWidth, 
                                  "tfg_label" : self.tfg_export_path_lalbel,
                                  "tfg_is_editable" : False,
                                  "tfg_bck_color" : [1, 1, 1],
                                  "tfg_text" : "" }
        
        self.tfg_export_path.set__(self.tfg_spec_export)
        
        # tfg : Browser (open)
        #===================================================



        #===================================================
        # tsl : Set name, result name (open)

        self.winSize_for_mod_tsl = {"window_height" : self.win_height-300,
                                    "window_width" : self.win_width*0.5}

        self.cls_tsl_selected_set = JUN_mod_tsl.JUN_mod_tsl_v01()
        self.cls_tsl_result_name_ = JUN_mod_tsl.JUN_mod_tsl_v01()

        self.name_tsl_selected_set = "tsl_selected_set"
        self.name_tsl_result_name_ = "tsl_result_name_"

        self.tsl_spec_Set_name__  = { "name_tsl" : self.name_tsl_selected_set,
                                      "name_title" : "Set's Name",
                                      "num_item" : "num_Set_Name",
                                      **self.color_all,
                                      **self.winSize_for_mod_tsl }
        
        self.tsl_spec_result_name  = { "name_tsl" : self.name_tsl_result_name_,
                                       "name_title" : "File name",
                                       "num_item" : "num_file_name",
                                       **self.color_all,
                                       **self.winSize_for_mod_tsl}

        self.cls_tsl_selected_set.set__(self.tsl_spec_Set_name__)
        self.cls_tsl_result_name_.set__(self.tsl_spec_result_name)

        # tsl : Set name, result name (close)
        #===================================================


        #===================================================
        # optionMenuGrp : Set text type (open)

        self.lst_omg_text_type = []
        self.num_token = 6
        # self.lst_label = ["Custom", "Set's Name", "Version"]
        self.menu_specs = {
                            "Custom"        :   {
                                              "callback_on_set_name_btn_click"  : get_tf_text, 
                                              "callback_on_change"              : able_tf, 
                                             },
                            "Set's Name"    :   {
                                              "callback_on_set_name_btn_click"  : get_obj_name, 
                                              "callback_on_change"              : disable_tf, 
                                             }

                            # "Version"    :   {
                                            #   "callback": test_03
                                            #  }

                           }

        self.omg_spec_base = {
                                "omg_name" : "omg_token_",
                                # "omg_label_main" : 
                                # "extraLabel" : 
                                # "col_width" : 
                                "lst_label" : self.menu_specs,
                                "changeCommand" : None
                             }

        for i in range(0, self.num_token):
            self.omg_tmp = JUN_mod_omg.JUN_mod_omg_v01()
            self.omg_copied = self.omg_spec_base.copy()
            self.omg_copied["omg_name"] = self.omg_copied["omg_name"] + str(i)
            # print(self.omg_copied["omg_name"])
            self.omg_tmp.set__(self.omg_copied)
            self.lst_omg_text_type.append(copy.deepcopy(self.omg_tmp))


        # optionMenuGrp : Set text type (close)
        #===================================================

        #===================================================
        # optionMenuGrp (open)

        self.num_col = 6
        self.col_space = 4
        self.lst_tf = []
        self.matrix_name = []

        self.lst_lable_on_text  = ["SK", "MANU", "CH", "Name", "Type", "Version"]
        self.lst_text_on_tf     = ["SK", "MANU", "CH", "Name", "Basic", "Version"]

        self.tf_bckColor = [0, 0, 0]

        # optionMenuGrp (close)
        #===================================================


        #===================================================
        # btn spec (open)
        self.idx_brows_path     = 0
        self.idx_set_name       = 1
        self.idx_export_file    = 2

        self.subSpec_tsl = {
                            "tsl_selected_set"  : self.cls_tsl_selected_set, 
                            "tsl_result_name_"  : self.cls_tsl_result_name_ 
                            }

        self.btn_specs = [
                            # idx_brows_path : 0
                            [
                                { 
                                    "label": "Brows",
                                    "callback": JUN_cmd_brows_path,
                                    "args": [self.tfg_export_path]
                                }
                            ],

                            # idx_set_name : 1
                            [
                                { 
                                    "label": "Set name",
                                    "callback": JUN_cmd_set_name,
                                    "kwargs":   {
                                                "lst_tf"            : self.lst_tf,
                                                "lst_omg_text_type" : self.lst_omg_text_type,
                                                "menu_specs"        : self.menu_specs,
                                                **self.subSpec_tsl
                                                }
                                }
                            ],

                            # idx_export_file : 2
                            [

                                { 
                                    "label": "Export",
                                    "callback": JUN_cmd_export,
                                    "kwargs": {
                                                "tfg_export_path"   : self.tfg_export_path,
                                                **self.subSpec_tsl
                                                }
                                    
                                }
                            ]
                        ]
        
        # btn spec (close)
        #===================================================

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
        cmds.menuItem( label='About', command = self.menu_cmd);

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_mainDark);
        
        # Brows path ==================================================
        # frameLayout : Brows path (open)
        cmds.frameLayout( label='Brows path', collapsable= True, bgc =self.color_main);

        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        # cmds.paneLayout( configuration= "vertical2", paneSize = ([1,35,100],[2,65,100]) )

        self.tfg_export_path.build()

        self.create_buttons(self.btn_specs[self.idx_brows_path])

        cmds.setParent( '..' )

        cmds.setParent( '..' )

        # frameLayout : Brows path (close)
        # Brows path ==================================================


        # ==================================================
        # tsl (open)
        # frameLayout : Set Up (open)
        cmds.frameLayout( label='Set Up', collapsable= True, bgc =self.color_main );

        # paneLayout vertical2" (open)
        cmds.paneLayout( configuration= "vertical2" )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);
        
        self.cls_tsl_selected_set.build()

        cmds.setParent( '..' )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);

        self.cls_tsl_result_name_.build()

        cmds.setParent( '..' )

        # paneLayout vertical2" (close)
        cmds.setParent( '..' )

        # frameLayout : Set Up (close)
        cmds.setParent( '..' )

        # tsl (close)
        # ==================================================

        # ==================================================
        # nameing (open)

        
        col_width_ = int(self.win_width / self.num_col - 10)
        lst_col_spacing = [(i, self.col_space) for i in range(2, self.num_col + 1)]
        lst_col_width = [(i+1, col_width_) for i in range(0, self.num_col)]

 
        specs_tf_all = {
                            "textfield_name" : None,
                            **self.menu_specs
                        }

        cmds.frameLayout( label='Naming', collapsable= True, bgc =self.color_main );

        cmds.rowColumnLayout( numberOfColumns=self.num_col, 
                              cs= lst_col_spacing, 
                              cw= lst_col_width);
        
        for i in range(0, self.num_col):
            cmds.text( label=self.lst_lable_on_text[i], align = 'center' )
        
        for i in range(0, self.num_col):
            tmp_tf = cmds.textField( text = self.lst_text_on_tf[i], backgroundColor = self.tf_bckColor);    
            self.lst_tf.append(tmp_tf)    
        
        for i in range(0, self.num_col):
            self.lst_omg_text_type[i].build()
            specs_tf_tmp = specs_tf_all.copy()
            specs_tf_tmp["textfield_name"] = self.lst_tf[i]
            self.lst_omg_text_type[i].set_callback(partial(on_option_changed, specs_tf_tmp))


                      
        cmds.setParent( '..' )

        self.create_buttons(self.btn_specs[self.idx_set_name])
        self.create_buttons(self.btn_specs[self.idx_export_file])

        cmds.setParent( '..' )

        # nameing (close)
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

           
def JUN_PY_file_exporter_tool_v01_01():
    JUN_Win_base = JUN_ToolUI_file_exporter()
    JUN_Win_base.build()

def build__():
    JUN_PY_file_exporter_tool_v01_01()
