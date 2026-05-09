import sys
import os

import maya.cmds as cmds;
import maya.mel as mel
from functools import partial



from JUN_All import config
from Framework.ui import MOD_tsl_gen_01
from Framework.ui import JUN_mod_tsl, JUN_mod_radCol, JUN_mod_colorThem, JUN_mod_tsl_gen

class JUN_ToolUI_humanIKTool_01_01:
    def __init__(self):
        self.str_headTitle = "HumanIK tool v01.01"
        self.str_winName = "human_ik_tool_v01_04"
        self.win_width = 350;
        self.win_height = 600;

        self.winSize_for_tsl_jnts = {"window_height" : self.win_height*0.5,
                                    "window_width" : self.win_width*1}
        
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
        
        # set module : tsl(open)

        self.mod_tsl_jnts = JUN_mod_tsl.JUN_mod_tsl_v01()

        self.name_tsl_jnts = "tsl_selected_joints"

        self.tsl_spec_jnts  = { "name_tsl" : self.name_tsl_jnts,
                                "name_title" : "Joints for assgin",
                                "num_item" : "num_jnts",
                                **self.color_all,
                                **self.winSize_for_tsl_jnts }
     
        self.mod_tsl_jnts.set__(self.tsl_spec_jnts)

        # set module : tsl(close)

        # set module : radio collection (open)

        # radCol : bone chain (open)
        self.radCol_joints_chain = JUN_mod_radCol.JUN_module_radioCollection_v01_01()

        self.dict_radio_lable = {"Spine" : [1, 8, 23, 24, 25, 26, 27, 28], 
                                "Shoulder to hand : Left" : [18, 9, 10, 11], 
                                "Fingers : Left" : [50, 51, 52, 54, 55, 56, 58, 59, 60, 62, 63, 64, 66, 67, 68], 
                                "Shoulder to hand : Right" : [19, 12, 13, 14], 
                                "Fingers : Right" : [74, 75, 76, 78, 79, 80, 82, 83, 84, 86, 87, 88, 90, 91, 92],
                                "Neck 1 to head" : [20, 15], 
                                "Neck 2 to head" : [20, 32, 15], 
                                "Leg : Left" : [2, 3, 4, 16], 
                                "Leg : Right" : [5, 6, 7, 17]}
        
        self.lst_radio_lable = list(self.dict_radio_lable.keys()) 

        self.radCol_joints_chain_spec = {   "name_radioCollecion" : "Joints chain",
                                            "lst_label" : self.lst_radio_lable,
                                            "str_selected" : 0}
        
        self.radCol_joints_chain.set__(self.radCol_joints_chain_spec)

        # radCol : bone chain (close)


        self.menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 31-JAN-2026\')".format(self.color_main)

    def fun_dummy(self, *args , **kwargs):
        print("fun_dummy called")
        print("args :", args)
        print("kwargs :", kwargs)

    def JUN_get_HIK_node(self, tsl_HIK, *args):
        objs_all = cmds.ls(fl=True)
        lst_HIK_node = []
        for obj__ in objs_all:
            if cmds.objectType(obj__) == "HIKCharacterNode":
                lst_HIK_node.append(obj__)

        cmds.textScrollList( tsl_HIK, e=True, removeAll=True );
        cmds.textScrollList( tsl_HIK, e=True, append = lst_HIK_node );
        cmds.textScrollList( tsl_HIK, e=True, selectItem =  lst_HIK_node[0]);


    def JUN_assign_joints(self, tsl_joints, tsl_HIK_node, radCol_joints_chain : JUN_mod_radCol.JUN_module_radioCollection_v01_01, *args , **kwargs):
        lst_joints = cmds.textScrollList( tsl_joints, q=True, allItems=True)
        HIK_node = cmds.textScrollList( tsl_HIK_node, q=True, selectItem=True)
        lable_checked = radCol_joints_chain.get_checked_label()
        lst_id = self.dict_radio_lable[lable_checked]

        dict_jnt_id = dict(zip(lst_joints, lst_id))

        for id , (jnt, jnt_id) in enumerate(dict_jnt_id.items()):
            print(f'setCharacterObject(\"{jnt}\",\"{HIK_node[0]}\",{jnt_id},0)')
            try:
                mel.eval(f'setCharacterObject(\"{jnt}\",\"{HIK_node[0]}\",{jnt_id},0)')
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                
        print(f'[{lable_checked}] : Assign joints succeeded')

    
    def build(self):

        if cmds.window( self.str_winName , exists=True ): 
            cmds.deleteUI( self.str_winName , window=True )
        
        cmds.window( self.str_winName, bgc=self.color_mainDark, title= self.str_headTitle)

        cmds.menuBarLayout (bgc=self.color_mainDark); 
    
        cmds.menu( label='Help' );
        cmds.menuItem( label='About', command = self.menu_cmd);


        
        # tsl(open) ==================================================
        # frameLayout : Joints for assign (open)
        cmds.frameLayout( label='Joints for assign', collapsable= True, bgc =self.color_main );

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,75,100],[2,25,100]) )

        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);
        
        tsl_HIK_node = "HIKCharacterNode_node"
        cmds.textScrollList( tsl_HIK_node,
                            height = (self.win_height*0.08),
                            numberOfRows=15, 
                            allowMultiSelection=True, 
                            selectCommand=partial(JUN_mod_tsl_gen.JUN_gen_tsl_select, tsl_HIK_node));

        cmds.setParent( '..' )

        btn_get_all_HIKNode =  cmds.button( "get HIK node", 
                                            label='Get HIK node', 
                                            bgc= self.color_btn, 
                                            command= partial(self.JUN_get_HIK_node, tsl_HIK_node))

        cmds.setParent( '..' )


        cmds.columnLayout(adjustableColumn=True, 
                          columnAttach=('both', 5), 
                          rowSpacing=6, 
                          bgc =self.color_sub);
        
        self.mod_tsl_jnts.build()

        cmds.setParent( '..' )

        # frameLayout : Joints for assign (close)
        cmds.setParent( '..' )
        # tsl(close) ==================================================

        # frameLayout : human ik tool (open)
        cmds.frameLayout( label='Set HumanIK joints', collapsable= True, bgc =self.color_main);

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,35,100],[2,65,100]) )

        # create radio collection for transfering mesh to mesh
        
        self.radCol_joints_chain.build()
        
        form__ = cmds.formLayout()

        btn_jnts_to_jnts =  cmds.button(    "assign joints in humanik", 
                                            label='Assign joints', 
                                            bgc= self.color_btn, 
                                            command= partial(self.JUN_assign_joints, self.name_tsl_jnts, tsl_HIK_node, self.radCol_joints_chain))
        
        btn_empty_01 =  cmds.button(    "name_empty", 
                                            label='empty', 
                                            bgc= self.color_btn)
                                            # command= partial(self.JUN_move_each_skin_weight, self.name_tsl_jnts, self.name_tsl_to__))
        
        MARGIN = 6
        SPACEING = 4

        cmds.formLayout(form__, e = True, 
                        attachForm = [
                            (btn_jnts_to_jnts, "left", MARGIN),
                            (btn_jnts_to_jnts, "right", MARGIN),
                            (btn_jnts_to_jnts, "top", MARGIN),

                            (btn_empty_01, "left", MARGIN),
                            (btn_empty_01, "right", MARGIN),
                        ],
                        attachControl = [(btn_empty_01, "top", SPACEING, btn_jnts_to_jnts)]
                        )
        
        cmds.setParent( '..' )

        cmds.setParent( '..' )
        
        # frameLayout : human ik tool (close)
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

           
def build__():

    JUN_Win_HIK_tool = JUN_ToolUI_humanIKTool_01_01()
    JUN_Win_HIK_tool.build()