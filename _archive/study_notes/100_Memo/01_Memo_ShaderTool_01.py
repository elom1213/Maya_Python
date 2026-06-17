# last Update date 22 03 13
# Python Script by Ji Hun Park

# Shader Tool V01

import maya.cmds as cmds;

GLB_dict_SGs_tgtGrpChildren = {};

def cmd_tsl_select(name_tsl_SGs):
    str_objs_seleted = cmds.textScrollList(name_tsl_SGs, q = True, selectItem = True);
    cmds.select(str_objs_seleted);

def cmd_upd_tf_selected (name_tf):
    str_objs_selected = cmds.ls(sl = True, fl = True);
    cmds.textField(name_tf, e = True, text = str_objs_selected[0]);

def cmd_select_assignedObjs(name_tsl_SGs, name_tf_targetGroup):
    SG_selected = cmds.textScrollList(name_tsl_SGs, q =True, selectItem = True);
    cmds.select(GLB_dict_SGs_tgtGrpChildren[SG_selected[0]]);

def cmd_upd_grpDescend(name_tf_baseGroup, name_tsl_groupDescendents):
    # update textField
    cmd_upd_tf_selected (name_tf_baseGroup);

    str_objs_selected = cmds.ls(sl = True, fl = True);
    str_obj_descendents = cmds.listRelatives(str_objs_selected[0], f = True, allDescendents = True);

    # update textScrollList
    cmds.textScrollList(name_tsl_groupDescendents, e = True, removeAll = True);

    for str_obj_descendent in str_obj_descendents:
        # get mesh shape node
        str_obj_relatives = cmds.listRelatives(str_obj_descendent, f = True, children = True);
        # check obj is mesh
        if(cmds.nodeType(str_obj_descendent) == "transform" and 
           cmds.nodeType(str_obj_relatives) == "mesh"):
            cmds.textScrollList(name_tsl_groupDescendents, e = True, append = str_obj_descendent);


def cmd_upd_tsl_SGs (name_tsl_SGs):
    str_objs_selected = cmds.ls(sl = True, fl = True);

    # get mesh shape node
    str_obj_descendents = cmds.listRelatives(str_objs_selected[0], f = True, children = True);
    str_obj_meshShape = str_obj_descendents[0];

    # get upStreamNodes from mesh
    str_upStreams_fromObj = cmds.hyperShade(listUpstreamNodes = str_obj_meshShape);

    cmds.textScrollList(name_tsl_SGs, e = True, removeAll = True);
    for str_upStream in str_upStreams_fromObj:
        if(cmds.nodeType(str_upStream) == "shadingEngine"):
            cmds.textScrollList(name_tsl_SGs, e = True, append = str_upStream);


def cmd_separate(name_tsl_groupDescendents,
                 name_tsl_SGs,
                 name_tf_targetGroup,
                 name_tf_Status):
    str_SGs = cmds.textScrollList(name_tsl_SGs, q = True, allItems = True);
    str_objs = cmds.textScrollList(name_tsl_groupDescendents, q = True, allItems = True);

    str_tgtGrp = cmds.textField(name_tf_targetGroup, q = True, text = True);
    str_tgtGrpChildren = cmds.listRelatives(str_tgtGrp, f = True, allDescendents = True);

    # remove shape nodes from str_tgtGrpChildren
    for str_tgtObj in str_tgtGrpChildren:
        if(cmds.nodeType(str_tgtObj) != "transform"):
            del str_tgtGrpChildren[str_tgtGrpChildren.index(str_tgtObj)];
            
    # create dictionary
    # list() -> return empty list
    dict_SGs = {SG_key : list() for SG_key in str_SGs} 

    global GLB_dict_SGs_tgtGrpChildren;
    GLB_dict_SGs_tgtGrpChildren.clear();
    GLB_dict_SGs_tgtGrpChildren = {SG_key : list() for SG_key in str_SGs} 
    
    # update dict_SGs
    for str_obj in str_objs:
        # get mesh shape node
        str_obj_descendents = cmds.listRelatives(str_obj, f = True, children = True);
        str_obj_meshShape = str_obj_descendents[0];

        # get upStreamNodes from mesh
        str_upStreams_fromObj = cmds.hyperShade(listUpstreamNodes = str_obj_meshShape);

        for str_upStream in str_upStreams_fromObj:
            if(cmds.nodeType(str_upStream) == "shadingEngine"):
                int_index_obj = str_objs.index(str_obj);
                dict_SGs[str_upStream].append(int_index_obj);

    # update dict_SGs_tgtGrpChildren
    for key_SGs in dict_SGs:
        for obj_index in dict_SGs[key_SGs]:
            tgtObj = str_tgtGrpChildren[obj_index];
            GLB_dict_SGs_tgtGrpChildren[key_SGs].append(tgtObj);
    
    str_status = "Success : Separate "+str(len(str_objs))+" objects to "+str(len(str_SGs))+" types";
    cmds.textField(name_tf_Status, e = True, text = str_status);




#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_shaderTool ():
    str_winTitle = "Shader Tool";
    str_winName = "Junny_win_Shader_Tools";
    win_width = 480;
    win_height = 500;
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc =[ 0.12, 0.13, 0.21 ], title="Shader Tool V01" );
        
    #----------------------------------------------------------------------------
    # UI: MenuBar
    #----------------------------------------------------------------------------

    cmds.menuBarLayout ( bgc =[ 0.12, 0.13, 0.21 ]); 
      
    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = """cmds.confirmDialog( title=\'About\', icon =\"information\", bgc =[0.27, 0.34, 0.48], button = \"OK\", messageAlign = \"center\", 
                                                message=\' Written by Ji Hun Park. \\n Update date: 13-Mar-2022\' )""" );
    

    #===================================================================================
    # UI: Colum Layout(open)
    #===================================================================================
    
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=6, bgc =[ 0.12, 0.13, 0.21 ], width = 390 );
         
    #===================================================================================
    # frameLayout : Base group(open)
    #===================================================================================
    
    cmds.frameLayout( label='Base Group', collapsable= True, bgc =[ 0.27, 0.34, 0.48 ] );

    #===================================================================================
    # paneLayout : vertical2(open)
    #===================================================================================
    
    cmds.paneLayout( configuration= "vertical2" )

    #----------------------------------------------------------------------------
    # columnLayout : Left Section(open)
    #----------------------------------------------------------------------------
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =[ 0.5, 0.55, 0.63 ] );
    
    
    cmds.button( "name_btn_list_groupDescendents", 
                 label='Select Group', 
                 bgc =[ 0.85, 0.38, 0.2 ], 
                 command='cmd_upd_grpDescend(\"name_tf_baseGroup\", \"name_tsl_groupDescendents\")');

    cmds.textField( "name_tf_baseGroup" );

    cmds.textScrollList("name_tsl_groupDescendents", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand     = 'CMD_ToolSel_tsl_select( \"NAM_toolSelTgt_tsl_selList\")');

    # buttons(open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =[ 0.55, 0.63, 0.71 ], command='CMD_ToolSel_b_add  ( \"NAM_toolSelTgt_tsl_selList\", \"NAM_toolSelTgt_t_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =[ 0.55, 0.63, 0.71 ], command='CMD_ToolSel_b_del  ( \"NAM_toolSelTgt_tsl_selList\", \"NAM_toolSelTgt_t_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =[ 0.39, 0.49, 0.63 ], command='CMD_ToolSel_b_up   ( \"NAM_toolSelTgt_tsl_selList\", \"NAM_toolSelTgt_t_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =[ 0.39, 0.49, 0.63 ], command='CMD_ToolSel_b_down ( \"NAM_toolSelTgt_tsl_selList\", \"NAM_toolSelTgt_t_selNum\" )' );
        
    # buttons(close)
    cmds.setParent( '..' )

    #----------------------------------------------------------------------------
    # columnLayout : Left Section(close)
    #----------------------------------------------------------------------------
    cmds.setParent( '..' )
    
    #----------------------------------------------------------------------------
    # List Shader Endgine(SG) (open)
    #----------------------------------------------------------------------------
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =[ 0.5, 0.55, 0.63 ] );

    cmds.button( "name_btn_listSGs", label='List Shadeing Groups', bgc =[ 0.85, 0.38, 0.2 ], command='cmd_upd_tsl_SGs ( \"name_tsl_SGs\" )' );
   
    cmds.textScrollList("name_tsl_SGs", 
                        height = (win_height*0.4),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand= 'cmd_tsl_select( \"name_tsl_SGs\" )', 
                        doubleClickCommand= 'cmd_select_assignedObjs(\"name_tsl_SGs\", \"name_tf_targetGroup\")');

    #----------------------------------------------------------------------------
    # List Shader Endgine(SG) (close)
    #----------------------------------------------------------------------------
    cmds.setParent( '..' )

    #===================================================================================
    # paneLayout : vertical2(close)
    #===================================================================================
    cmds.setParent( '..' )

    #===================================================================================
    # frameLayout : base group(close)
    #===================================================================================
    cmds.setParent( '..' )

    #----------------------------------------------------------------------------
    # List Shader Endgine(SG) (open)
    #----------------------------------------------------------------------------

    cmds.frameLayout( label='Target Group', collapsable= True, bgc =[ 0.27, 0.34, 0.48 ] );

    cmds.rowLayout(nc = 2);
    cmds.textField("name_tf_targetGroup", w = (win_width/4 - 10), backgroundColor = [1, 1, 1]);
    cmds.button("name_btn_upd_tf", 
                label='Select', 
                bgc =[ 0.85, 0.38, 0.2 ],
                command='cmd_upd_tf_selected(\"name_tf_targetGroup\")');
    cmds.setParent( '..' )

    cmds.rowLayout(nc = 1);
    cmds.textField("name_tf_Status",
                    width = (win_width-10),
                    editable = False, 
                    backgroundColor = [1, 1, 1]);
    cmds.setParent( '..' )

    #----------------------------------------------------------------------------
    # List Shader Endgine(SG) (close)
    #----------------------------------------------------------------------------
    cmds.setParent( '..' )

    cmds.button( "name_btn_separate", 
                 label='Separate', 
                 bgc =[ 0.85, 0.38, 0.2 ], 
                 command='cmd_separate(\"name_tsl_groupDescendents\", \"name_tsl_SGs\",\"name_tf_targetGroup\",\"name_tf_Status\")');

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    

PY_JUN_makeUI_shaderTool();