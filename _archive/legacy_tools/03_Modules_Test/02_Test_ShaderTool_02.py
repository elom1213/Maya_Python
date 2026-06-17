# last Update date 22 03 15
# Python Script by Ji Hun Park

# Shader Tool V01.03

# 03.15
# Creatae UI : Buttons Select Faces, Selecte Shader

import maya.cmds as cmds;

''' GLB_dict_SGs_tgtGrpChdrn =
    {SG_A : [obj1, obj2...],
     SG_B : [obj7, obj8...]..}
'''
GLB_dict_SGs_tgtGrpChdrn = {};

def get_meshShapes_from_objs(str_list_objs):
    str_list_objs_descendents = [cmds.listRelatives(str_obj, f = True, allDescendents = True)[0] for str_obj in str_list_objs];
    return [i for i in str_list_objs_descendents if cmds.nodeType(i) == "mesh"];

def cmd_tsl_select_general(name_tsl_input):
    str_objs_seleted = cmds.textScrollList(name_tsl_input, q = True, selectItem = True);
    cmds.select(str_objs_seleted);

def cmd_tsl_selectFaces(name_tsl_input):
    cmd_tsl_select_general(name_tsl_input);

def cmd_tsl_selectNoExpand(name_tsl_input):
    str_objs_seleted = cmds.textScrollList(name_tsl_input, q = True, selectItem=True);
    cmds.select(str_objs_seleted, noExpand=1);

def cmd_sortBaseGrp(name_tsl_baseGrpDesndts):
    str_list_baseGrpDsndts = cmds.textScrollList(name_tsl_baseGrpDesndts, q = 1, allItems=1);
    str_list_sorted = sorted(str_list_baseGrpDsndts);
    cmds.textScrollList(name_tsl_baseGrpDesndts, e=1, removeAll=1);
    cmds.textScrollList(name_tsl_baseGrpDesndts, e=1, append=str_list_sorted);

def cmd_tsl_select_mesh_fromSG(name_tsl_SGs):
    str_SGs_seleted = cmds.textScrollList(name_tsl_SGs, q = True, selectItem = True);

    # get upStream -> [[a, b..], [c, d..]..]
    str_list_upStrms_frmSGs = [cmds.hyperShade(listUpstreamNodes=SG_sl)[0:-1] for SG_sl in str_SGs_seleted];

    # flatten list 
    str_list_upStrms_frmSGs = [item for sublist in str_list_upStrms_frmSGs for item in sublist];
    str_list_selectMesh = [nod_upStrm for nod_upStrm in str_list_upStrms_frmSGs if cmds.nodeType(nod_upStrm) == "mesh"]

    cmds.select(str_list_selectMesh);

def cmd_upd_tf_selected (name_tf):
    str_objs_selected = cmds.ls(sl = True, fl = True);
    cmds.textField(name_tf, e = True, text = str_objs_selected[0]);

def cmd_select_assignedObjs(name_tsl_SGs, name_tf_targetGroup):
    SG_selected = cmds.textScrollList(name_tsl_SGs, q =True, selectItem = True);
    cmds.select(GLB_dict_SGs_tgtGrpChdrn[SG_selected[0]]);

def cmd_upd_tf_tsl_grpDescend(name_tf_baseGroup, name_tsl_groupDescendents):
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
    str_list_objs_selected = cmds.ls(sl = True, fl = True);
    str_list_meshShapes = get_meshShapes_from_objs(str_list_objs_selected)

    str_list_dwnStrm_fromShapes = [cmds.hyperShade(listDownstreamNodes=obj_shpe) for obj_shpe in str_list_meshShapes];
    # flatten
    str_list_dwnStrm_fromShapes = [item for sublist in str_list_dwnStrm_fromShapes for item in sublist];

    cmds.textScrollList(name_tsl_SGs, e = True, removeAll = True);
    str_list_memo = set();
    for str_dwnStream in str_list_dwnStrm_fromShapes:
        if(cmds.nodeType(str_dwnStream) == "shadingEngine" and 
           str_dwnStream not in str_list_memo):
            cmds.textScrollList(name_tsl_SGs, e = True, append = str_dwnStream);
            str_list_memo.add(str_dwnStream);


def cmd_separate(name_tsl_baseGrpDescends,
                 name_tsl_SGs,
                 name_tf_targetGroup,
                 name_tf_Status):
    str_status = "Separating..."
    cmds.textField(name_tf_Status, e = True, text = str_status);
    
    str_SGs = cmds.textScrollList(name_tsl_SGs, q = True, allItems = True);
    str_objs_frmBaseGrp = cmds.textScrollList(name_tsl_baseGrpDescends, q = True, allItems = True);

    str_tgtGrp = cmds.textField(name_tf_targetGroup, q = True, text = True);
    str_tgtGrpChildren = cmds.listRelatives(str_tgtGrp, f = True, allDescendents = True);

    # remove shape nodes from str_tgtGrpChildren
    str_tgtGrpChildren = [tgtObj for tgtObj in str_tgtGrpChildren if cmds.nodeType(tgtObj) == "transform"];
    # create dictionary
    dict_SGs = {SG_key : list() for SG_key in str_SGs} 

    global GLB_dict_SGs_tgtGrpChdrn;
    GLB_dict_SGs_tgtGrpChdrn.clear();
    GLB_dict_SGs_tgtGrpChdrn = {SG_key : list() for SG_key in str_SGs} 
    
    # update dict_SGs
    for str_obj in str_objs_frmBaseGrp:
        # get mesh shape node
        str_obj_descendents = cmds.listRelatives(str_obj, f = True, children = True);
        str_obj_meshShape = str_obj_descendents[0];

        # get upStreamNodes from mesh
        str_dwnStrms_fromObj = cmds.hyperShade(listDownstreamNodes = str_obj_meshShape);

        for str_upStream in str_dwnStrms_fromObj:
            if(cmds.nodeType(str_upStream) == "shadingEngine"):
                int_index_obj = str_objs_frmBaseGrp.index(str_obj);
                dict_SGs[str_upStream].append(int_index_obj);

    # update dict_SGs_tgtGrpChildren
    for key_SGs in dict_SGs:
        for obj_index in dict_SGs[key_SGs]:
            tgtObj = str_tgtGrpChildren[obj_index];
            GLB_dict_SGs_tgtGrpChdrn[key_SGs].append(tgtObj);
    
    str_status = "Success : Separate "+str(len(str_objs_frmBaseGrp))+" objects to "+str(len(str_SGs))+" types";
    if(len(str_objs_frmBaseGrp) != len(str_tgtGrpChildren)):
        str_status = "Warnning : number of Base Group's children("+str(len(str_objs_frmBaseGrp))+") and Taget Group's children("+str(len(str_tgtGrpChildren))+") different";
        
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

    color_mainDark = [0.0, 0.0, 0.30];
    color_main = [0.3, 0.1, 0.5];
    color_sub = [0.4, 0.3, 0.7];
    color_btn = [0.95, 0.2, 0.7];
    color_back = [0.96, 0.96, 0.96];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="Shader Tool V01" );
        
    #----------------------------------------------------------------------------
    # UI: MenuBar
    #----------------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 15-Mar-2022\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    

    #===================================================================================
    # UI: Colum Layout(open)
    #===================================================================================
    
    cmds.columnLayout(adjustableColumn=True, 
                      columnAttach=('both', 5), 
                      rowSpacing=6, 
                      bgc =color_mainDark, 
                      width = 390 );
         
    #===================================================================================
    # frameLayout : Base group(open)
    #===================================================================================
    
    cmds.frameLayout( label='Base Group', collapsable= True, bgc =color_main );

    #===================================================================================┐┐
    # paneLayout : vertical2(open)                                                      ││
    #                                                                                   ││
    
    cmds.paneLayout( configuration= "vertical2" )

    #----------------------------------------------------------------------------┐
    # columnLayout : Left Section(open)                                          │

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    
    
    cmds.button( "name_btn_list_groupDescendents", 
                 label='Select Group', 
                 bgc=color_btn, 
                 command='cmd_upd_tf_tsl_grpDescend(\"name_tf_baseGroup\", \"name_tsl_baseGrpDesndts\")');

    cmds.textField( "name_tf_baseGroup" );

    cmds.textScrollList("name_tsl_baseGrpDesndts", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='cmd_tsl_select(\"name_tsl_baseGrpDesndts\")');

    # buttons(open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "name_btn_sortBaseGrp",
                 width= 40, 
                 label='Sort', 
                 bgc =color_btn, 
                 command='cmd_sortBaseGrp(\"name_tsl_baseGrpDesndts\")');
   
        
    # buttons(close)
    cmds.setParent( '..' )


    # columnLayout : Left Section(close)                                         │
    #----------------------------------------------------------------------------┘
    cmds.setParent( '..' )
    
    #----------------------------------------------------------------------------┐
    # Shader Endgine(SG) Tool (open)                                             │

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_listSGs",
                 label='List Shadeing Groups',
                 bgc =color_btn,
                 command='cmd_upd_tsl_SGs ( \"name_tsl_SGs\" )' );
   
    cmds.textScrollList("name_tsl_SGs", 
                        height = (win_height*0.4),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand= 'cmd_tsl_select_mesh_fromSG( \"name_tsl_SGs\" )', 
                        doubleClickCommand= 'cmd_select_assignedObjs(\"name_tsl_SGs\", \"name_tf_targetGroup\")');
    # Buttons(open)
    cmds.rowLayout(nc = 3);

    cmds.button( "name_btn_selectFace",
                 width = (win_width/4-12),
                 label='Select Faces',
                 bgc =color_btn,
                 command='cmd_tsl_selectFaces( \"name_tsl_SGs\" )' );

    cmds.button( "name_btn_selectNoExpand",
                 width = (win_width/4-12),
                 label='Select Shader',
                 bgc =color_btn,
                 command='cmd_tsl_selectNoExpand( \"name_tsl_SGs\" )' );

    # Buttons(open)
    cmds.setParent( '..' )

    # Shader Endgine(SG) Tool (close)                                            │
    #----------------------------------------------------------------------------┘
    cmds.setParent( '..' )

    #                                                                                   ││
    # paneLayout : vertical2(close)                                                     ││
    #===================================================================================┘┘
    cmds.setParent( '..' )

    #===================================================================================
    # frameLayout : base group(close)
    #===================================================================================
    cmds.setParent( '..' )

    #----------------------------------------------------------------------------┐
    # Target Group (open)                                                        │

    cmds.frameLayout( label='Target Group', collapsable= True, bgc =color_main );
    
    # columnLayout(open)
    cmds.columnLayout(bgc = color_sub);

    cmds.rowLayout(nc = 2);
    cmds.textField("name_tf_targetGroup", w = (win_width/4 - 10), backgroundColor = [1, 1, 1]);
    cmds.button("name_btn_upd_tf", 
                label='Select', 
                bgc=color_btn,
                command='cmd_upd_tf_selected(\"name_tf_targetGroup\")');
    cmds.setParent( '..' )

    cmds.rowLayout(nc = 1);
    cmds.textField("name_tf_Status",
                    width = (win_width-10),
                    editable = False, 
                    backgroundColor = [1, 1, 1]);
    cmds.setParent( '..' )

    # columnLayout(close)
    cmds.setParent( '..' )

    # Target Group (close)                                                       │
    #----------------------------------------------------------------------------┘
    cmds.setParent( '..' )

    cmds.button( "name_btn_separate", 
                 label='Separate', 
                 bgc=color_btn, 
                 command='cmd_separate(\"name_tsl_baseGrpDesndts\", \"name_tsl_SGs\",\"name_tf_targetGroup\",\"name_tf_Status\")');

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    

def JUN_PY_ShaderTool_V01_03():
    PY_JUN_makeUI_shaderTool();