# last Update date 
# Python Script by Ji Hun Park

# file_exporter_v01 V01.00
# V01.00 : 


import maya.cmds as cmds;
import maya.mel as mel
from functools import partial

from JUN_All import config
from JUN_All.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem, JUN_mod_tfg

#====================================================================
# call back functions (Start)


# call back functions (End)
#====================================================================


class JUN_ToolUI_file_exporter:
    def __init__(self):
        self.str_headTitle = "File exporter Tool V01.00"
        self.str_winName = "Junny_win_file_exporter_tool_V01_00"
        self.win_width = 500;
        self.win_height = 600;
        self.btn_hight = self.win_height/40

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
        self.tfg_export_path_colWidth = [100, 100]
        self.tfg_export_path_lalbel = "Export path  :  "
        self.tfg_spec_x = {  "tfg_name" : self.tfg_export_path_name, 
                             "tfg_columWidth" : self.tfg_export_path_colWidth, 
                             "tfg_label" : self.tfg_export_path_lalbel,
                             "tfg_text" : "Empty" }
        
        self.tfg_export_path.set__(self.tfg_spec_x)
        
        # tfg : Browser (open)
        #===================================================



        #===================================================
        # tsl : Set name, result name (open)

        self.winSize_for_mod_tsl = {"window_height" : self.win_height-100,
                                    "window_width" : self.win_width*0.5}

        self.cls_tsl_selected_set = JUN_mod_tsl.JUN_mod_tsl_v01()
        self.cls_tsl_result_name_ = JUN_mod_tsl.JUN_mod_tsl_v01()

        self.name_tsl_selected_set = "tsl_selected_set"
        self.name_tsl_result_name_ = "tsl_result_name_"

        self.tsl_spec_Set_name__  = { "name_tsl" : self.name_tsl_selected_set,
                                      "name_title" : "Set Name",
                                      "num_item" : "num_Set_Name",
                                      **self.color_all,
                                      **self.winSize_for_mod_tsl }
        
        self.tsl_spec_result_name  = { "name_tsl" : self.name_tsl_result_name_,
                                       "name_title" : "To",
                                       "num_item" : "num_to",
                                       **self.color_all,
                                       **self.winSize_for_mod_tsl}

        self.cls_tsl_selected_set.set__(self.tsl_spec_Set_name__)
        self.cls_tsl_result_name_.set__(self.tsl_spec_result_name)

        # tsl : Set name, result name (close)
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

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,35,100],[2,65,100]) )

        self.tfg_export_path.build()

        self.create_buttons(btn_specs[self.idx_create_tex_file])

        cmds.setParent( '..' )

        cmds.setParent( '..' )

        # frameLayout : Brows path (close)
        # Brows path ==================================================


        # tsl ==================================================
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
        # tsl ==================================================


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
