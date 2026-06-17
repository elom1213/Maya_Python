# last Update date 26 01 24
# Python Script by Ji Hun Park

# Kangaroo sub tool : move joints weight v01.03

# v01.03 : create meshes to meshes function

import maya.cmds as cmds;
from functools import partial

import kangarooTabTools.weights as weights

from JUN_Tools import config
from JUN_Tools.JUN_ui import JUN_module_tsl, JUN_module_radCol

from JUN_Tools.JUN_ui import JUN_ui_reload_modules

def run_reload():
    if config.DEV_MODE:
        JUN_ui_reload_modules.reload_all()

run_reload()

class JUN_ToolUI_moveSkinWeightTool_01_03:
    def __init__(self):
        self.str_winTitle = "move weight tool V01.03 - KG sub tool"
        self.str_headTitle = self.str_winTitle
        self.str_winName = "kangaroo_sub_tool_move_weight_tool_v01_03"
        self.win_width = 500;
        self.win_height = 500;

        self.winSize_for_mod_tsl = {"window_height" : self.win_height-100,
                                    "window_width" : self.win_width*0.5}
        
        self.btn_hight = self.win_height/40

        self.color_mainDark = [0.10, 0.12, 0.18]
        self.color_main     = [0.14, 0.17, 0.25]
        self.color_sub      = [0.18, 0.22, 0.32]
        self.color_btn      = [0.30, 0.35, 0.45]
        self.color_back     = [0.12, 0.14, 0.20]

        self_color_all = {  "color_mainDark" : self.color_mainDark, 
                            "color_main" : self.color_main, 
                            "color_sub" : self.color_sub, 
                            "color_btn" : self.color_btn, 
                            "color_back" : self.color_back }
        
        # set module : tsl(open)

        self.mod_tsl_from = JUN_module_tsl.JUN_module_tsl_v01()
        self.mod_tsl_to__ = JUN_module_tsl.JUN_module_tsl_v01()

        self.name_tsl_from = "tsl_moveSkinWeight_from"
        self.name_tsl_to__ = "tsl_moveSkinWeight_to__"

        self.tsl_spec_from  = { "name_tsl" : self.name_tsl_from,
                                "name_title" : "From",
                                "num_item" : "num_from",
                                **self_color_all,
                                **self.winSize_for_mod_tsl }
        
        self.tsl_spec_to__  = { "name_tsl" : self.name_tsl_to__,
                                "name_title" : "To",
                                "num_item" : "num_to",
                                **self_color_all,
                                **self.winSize_for_mod_tsl}

        self.mod_tsl_from.set__(self.tsl_spec_from)
        self.mod_tsl_to__.set__(self.tsl_spec_to__)

        # set module : tsl(close)

        # set module : radio collection (open)

        # radCol : radCollecion transfer skin mode
        self.radCol_TSM = JUN_module_radCol.JUN_module_radioCollection_v01_01()

        self.lst_radio_lable = ["Vertex Index", "Closest Vertex", "Closest Point", "ClosestUV", "ClosestUV Point", "Spikes"]
        self.radCol_TSM_spec = { "name_radioCollecion" : "Transfer skin mode",
                                 "lst_label" : self.lst_radio_lable,
                                 "str_selected" : 2}
        
        self.radCol_TSM.set__(self.radCol_TSM_spec)

        # set module : radio collection (close)

        self.menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 24-JAN-2026\')".format(self.color_main)

    def fun_dummy(self, *args , **kwargs):
        print("fun_dummy called")
        print("args :", args)
        print("kwargs :", kwargs)

    def JUN_move_each_skin_weight(self, tsl_from, tsl_to__, *args):
        lst_item_from = cmds.textScrollList( tsl_from, q=True, allItems=True)
        lst_item_to__  = cmds.textScrollList( tsl_to__, q=True, allItems=True)
        item_len = len(lst_item_to__)

        joints_from_to_list =   {
                                f"['{f}']": f"['{t}']"
                                for f, t in zip(lst_item_from, lst_item_to__)
                                }
        weights.moveSkinClusterWeights(xJoints=joints_from_to_list, bDisableIslandCheck=True, sChooseSkinCluster=None, iSmoothBorderMask=1)

    def JUN_transfer_meshes_to_meshes(self, tsl_from, tsl_to__, radCol__, *args):
        lst_item_from = cmds.textScrollList( tsl_from, q=True, allItems=True)
        lst_item_to__  = cmds.textScrollList( tsl_to__, q=True, allItems=True)
        item_len = len(lst_item_to__)

        checked_idx =  radCol__.get_checked_idx()

        for i in range(item_len):
            mesh_from = lst_item_from[i]
            cmds.select(clear = True)
            cmds.select(lst_item_to__[i])
            weights.transferSkinCluster(iMode=checked_idx, sChooseSkinCluster=None, iSmoothBorderMask=1, sFrom=[mesh_from])
        

    def build(self):

        if cmds.window( self.str_winName , exists=True ): 
            cmds.deleteUI( self.str_winName , window=True )
        
        cmds.window( self.str_winName, bgc=self.color_mainDark, title= self.str_headTitle)

        cmds.menuBarLayout (bgc=self.color_mainDark); 
    
        cmds.menu( label='Help' );
        cmds.menuItem( label='About', command = self.menu_cmd);

        # tsl ==================================================
        # frameLayout : Set Up (open)
        cmds.frameLayout( label='Set Up', collapsable= True, bgc =self.color_main );

        # paneLayout vertical2" (open)
        cmds.paneLayout( configuration= "vertical2" )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);
        
        self.mod_tsl_from.build()

        cmds.setParent( '..' )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);

        self.mod_tsl_to__.build()

        cmds.setParent( '..' )

        # paneLayout vertical2" (close)
        cmds.setParent( '..' )

        # frameLayout : Set Up (close)
        cmds.setParent( '..' )
        # tsl ==================================================

        # frameLayout : move skin weight (open)
        cmds.frameLayout( label='move skin weight', collapsable= True, bgc =self.color_main);

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,35,100],[2,65,100]) )

        # create radio collection for transfering mesh to mesh
        
        self.radCol_TSM.build()
        
        form__ = cmds.formLayout()

        btn_jnts_to_jnts =  cmds.button(    "name_move_skin_weight_joints_to_joints_in_single_mesh", 
                                            label='joints to joints in single mesh', 
                                            bgc= self.color_btn, 
                                            command= partial(self.JUN_move_each_skin_weight, self.name_tsl_from, self.name_tsl_to__))
        
        btn_mesh_to_mesh =  cmds.button(    "name_move_skin_weight_meshes_to_meshes", 
                                            label='meshes to meshes', 
                                            bgc= self.color_btn, 
                                            command= partial(self.JUN_transfer_meshes_to_meshes, self.name_tsl_from, self.name_tsl_to__, self.radCol_TSM))
                                            # command= partial(self.radCol_TSM.get_checked_idx))
        
        MARGIN = 6
        SPACEING = 4

        cmds.formLayout(form__, e = True, 
                        attachForm = [
                            (btn_jnts_to_jnts, "left", MARGIN),
                            (btn_jnts_to_jnts, "right", MARGIN),
                            (btn_jnts_to_jnts, "top", MARGIN),

                            (btn_mesh_to_mesh, "left", MARGIN),
                            (btn_mesh_to_mesh, "right", MARGIN),
                        ],
                        attachControl = [(btn_mesh_to_mesh, "top", SPACEING, btn_jnts_to_jnts)]
                        )
        
        cmds.setParent( '..' )

        cmds.setParent( '..' )
        
        # frameLayout : move skin weight (close)
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

           
def JUN_PY_move_skinWeightTool_v01_03():
    JUN_Win_QuickTool = JUN_ToolUI_moveSkinWeightTool_01_03()
    JUN_Win_QuickTool.build()

# JUN_PY_move_skinWeightTool_v01_03()
