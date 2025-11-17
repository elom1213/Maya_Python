# last Update date 25 11 17
# Python Script by Ji Hun Park

# Giant Step - invert shape tool v01.01


import maya.cmds as cmds;

#===================================================================================
# Global Value
#===================================================================================

#--------------------------------------------------------------------------------------------------------------------
def BF_LIST_remove_repetitionArray ( var_list  ):

    var_resultList = [];

    for i in range( 0, len(var_list) ):

        if var_list[i] not in var_resultList:

            var_resultList.append( var_list[i] );        

    return var_resultList;

#--------------------------------------------------------------------------------------------------------------------
def BF_SELECTION_makeList_hierarchy_withoutShape ( str_obj  ):

    # make hidrarchy with the selected top obj

    str_childrenList = cmds.listRelatives ( str_obj, allDescendents=True, path=True );
    
    str_resultList = [];
    
    if str_childrenList != None:
    
        str_resultList = str_childrenList;
        
        str_resultList.append( str_obj );
    
    else:
    
        str_resultList.append( str_obj );     
    
    # remove shape nodes in the list
      
    str_childrenShapeList = cmds.listRelatives ( str_resultList, allDescendents=True, path=True, shapes=True );
    
    if  str_childrenShapeList != None: 
    
        for i in range( 0, len(str_childrenShapeList) ):
    
            str_resultList.remove( str_childrenShapeList[i] );
        
    return str_resultList;        

#--------------------------------------------------------------------------------------------------------------------
def BF_SELECTION_makeList_hierarchy ( str_objList, int_reverse, int_removeRepetitionArray  ):

    str_resultList = [];

    for i in range( 0, len(str_objList) ):
    
        str_childrenList = BF_SELECTION_makeList_hierarchy_withoutShape ( str_objList[i] );
        
        if int_reverse == 1:
        
            str_childrenList.reverse();           
        
        for j in range( 0, len(str_childrenList) ):
        
            str_resultList.append(str_childrenList[j] );
            
    if int_removeRepetitionArray == 1:
            
        str_resultList = BF_LIST_remove_repetitionArray ( str_resultList  );                   

    return str_resultList;

def JUN_cmd_tsl_select ( str_selTool_tsl_selList ):

    str_scrollList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True );
    
    cmds.select ( str_scrollList );

#===================================================================================
# tsl edit button
#===================================================================================

def JUN_cmd_GS_invertShape_toolSel_btn (str_selTool_tsl_selList, 
                                 str_selTool_t_selNum ):

    str_selList = cmds.ls ( sl=True, fl=True );
    
    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList );
    
    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );

def JUN_get_set_by_token(str_list_objs, str_list_tokenes):
    
    set_search_result = set();

    str_set_objs = set(str_list_objs);
    str_set_tokenes = set(str_list_tokenes);
    for str_obj in str_set_objs :
        for str_token in str_set_tokenes :
            if str_token in str_obj:
                set_search_result.add(str_obj);

    return set_search_result;

def JUN_get_list_ordered_by_token(str_list_objs, str_list_tokenes) :
    
    str_list_result = []

    for i in range(0, len(str_list_tokenes)) :
        for str_obj in str_list_objs:
            if str_list_tokenes[i] is "":
               break;
            if str_obj is "":
               break;
            if str_list_tokenes[i] in str_obj:
                str_list_result.append(str_obj);

    return str_list_result;

#===================================================================================
# start (JUN_cmd_select_riggedMesh)

def JUN_cmd_select_riggedMesh(name_rig_name_tsl):

    str_selList = cmds.ls ( sl=True, fl=True );

    str_fkik_objChild = set();
    cmds.textScrollList( name_rig_name_tsl, e=True, removeAll=True );
    for str_selItem in str_selList :
        cmds.textScrollList( name_rig_name_tsl, e=True, append = str_selItem );



# end (JUN_cmd_select_riggedMesh)
#===================================================================================

#===================================================================================
# tsl edit funcionts Detail
#===================================================================================

def BF_LIST_moveUp_index ( str_inputList, int_moveIndexList ):

    int_resultIndexList = [];

    for i in range( 0, len(int_moveIndexList) ):
    
        str_move = str_inputList.pop( int_moveIndexList[i]-1 );    
        str_inputList.insert( int_moveIndexList[i]-1 - 1, str_move );

        int_resultIndexList.append(int_moveIndexList[i]-1);
    
    return [ str_inputList, int_resultIndexList ];



def BF_LIST_moveDown_index ( str_inputList, int_moveIndexList ):

    int_moveIndexList.reverse();
    
    int_resultIndexList = [];

    for i in range( 0, len(int_moveIndexList) ):
                       
        str_move = str_inputList.pop( int_moveIndexList[i]-1 );
            
        str_inputList.insert( int_moveIndexList[i]-1 + 1, str_move );
        
        int_resultIndexList.append(int_moveIndexList[i]);

    int_resultIndexList.reverse();        
            
    return [ str_inputList, int_resultIndexList ];

#===================================================================================
# tsl edit funcionts
#===================================================================================


def CMD_ToolSel_b_add ( str_selTool_tsl_selList, str_selTool_t_selNum ):

    str_scrollList = cmds.textScrollList( str_selTool_tsl_selList, q=True, allItems=True );

    str_selList = cmds.ls ( sl=True, fl=True );

    for i in range( 0, len(str_selList) ):
    
        try:
    
            str_scrollList.index( str_selList[i] );
            
            print ( str_selList[i] + " is already in the list." );
        
        except:    

            cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList[i] );

            int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
            cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );  

def CMD_ToolSel_b_add_type ( str_selTool_tsl_selList, str_selTool_t_selNum ):

    str_scrollList = cmds.textScrollList( str_selTool_tsl_selList, q=True, allItems=True );

    str_selList = cmds.ls ( sl=True, fl=True );
    types = set();

    for sl in str_selList :
        types.add(cmds.objectType(sl));
    
    types = sorted(list(types));

    for i in range( 0, len(types) ):
    
        try:
    
            str_scrollList.index( str_selList[i] );
            
            print ( str_selList[i] + " is already in the list." );
        
        except:    

            cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList[i] );

            int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
            cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );  


def CMD_ToolSel_b_del ( str_selTool_tsl_selList, str_selTool_t_selNum ):

    str_scrollList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True );

    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeItem = str_scrollList );

    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) ); 


def CMD_ToolSel_b_up ( str_selTool_tsl_selList, str_selTool_t_selNum ):


    str_allItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, allItems=True          );
    str_selItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True        );
    str_selItemIndexList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectIndexedItem=True );
            
    str_moveIndexList = BF_LIST_moveUp_index (  str_allItemList, str_selItemIndexList );
   
       
    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True ); 
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_moveIndexList[0] );       
            
    for i in range( 0, len(str_moveIndexList[1]) ):
    
        cmds.textScrollList( str_selTool_tsl_selList, e=True, selectIndexedItem = str_moveIndexList[1][i] ); 
        
        
def CMD_ToolSel_b_down ( str_selTool_tsl_selList, str_selTool_t_selNum ):


    str_allItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, allItems=True          );
    str_selItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True        );
    str_selItemIndexList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectIndexedItem=True );

    
    str_moveIndexList = BF_LIST_moveDown_index (  str_allItemList, str_selItemIndexList );
   
       
    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True ); 
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_moveIndexList[0] );       
            
    for i in range( 0, len(str_moveIndexList[1]) ):
    
        cmds.textScrollList( str_selTool_tsl_selList, e=True, selectIndexedItem = str_moveIndexList[1][i]+1 ); 
 
def JUN_test_invertShape(riggedMesh, shapedMesh):
    # print("riggedMesh : "+ riggedMesh + " shapedMesh : " + shapedMesh)
    return cmds.duplicate(shapedMesh)[0]
 
#===================================================================================
# functions : UI
#===================================================================================

def JUN_parent(child, str_parent):
    grp_parent = str_parent
    if not cmds.objExists(str_parent):
        grp_parent = cmds.group(em=True, name=str_parent)
    try:
        cmds.parent(child, grp_parent)
    except:
        print("prent fail : " + child + "  " + grp_parent)

    
def JUN_cmd_GS_invertShape_createMeshes(JUN_GS_riggedMesh_tsl, 
                                        JUN_GS_IS_simedMesh_tsl,
                                        GS_IS_name_toolOption_ifg_timeStr,
                                        GS_IS_name_toolOption_ifg_timeEnd,
                                        JUN_fun_callback_invertShape):
    
    riggedMesh = cmds.textScrollList(JUN_GS_riggedMesh_tsl, q=True, allItems=True)[0]
    simedMeshes = cmds.textScrollList(JUN_GS_IS_simedMesh_tsl, q=True, allItems=True)

    int_timeStr = cmds.intFieldGrp(GS_IS_name_toolOption_ifg_timeStr, q=True, value1=True);
    int_timeEnd = cmds.intFieldGrp(GS_IS_name_toolOption_ifg_timeEnd, q=True, value1=True);
    lst_keyed = list(range(int_timeStr, int_timeEnd + 1))
    for i in lst_keyed:
        idx_keyed = lst_keyed.index(i)
        cmds.currentTime(i)
        result_mesh = None
        try :
            result_mesh = JUN_fun_callback_invertShape(riggedMesh, simedMeshes[idx_keyed])
        except:
            print("error 327 : result_mesh ")

        if result_mesh :
            cmds.setAttr(result_mesh + ".visibility", False)
            JUN_parent(result_mesh, "JUN_GS_shapedMesh_grp")
            print("idx : " + str(idx_keyed) +" mesh : "+ simedMeshes[idx_keyed] + " current Time : " + str(i))
    pass
#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_GS_invertShapeToolV01_01():
    str_winTitle = "GS invert shape Tool";
    str_winName = "Junny_win_GS_invertShapeTool";
    win_width = 380;
    win_height = 430;

    color_mainDark = [0.10, 0.12, 0.18]
    color_main     = [0.14, 0.17, 0.25]
    color_sub      = [0.18, 0.22, 0.32]
    color_btn      = [0.30, 0.35, 0.45]
    color_back     = [0.12, 0.14, 0.20]
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="GS Invert Shape V01.01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 17-NOV-2025\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    

    #===================================================================================
    # UI: Colum Layout(open)
    #===================================================================================
    
    cmds.columnLayout(adjustableColumn=True, 
                      columnAttach=('both', 5),
                      rowSpacing=6, 
                      bgc =color_mainDark, 
                      width = 360 );
         
    #===================================================================================
    # frameLayout : Tool  Setup select rigged mesh (open)
    #===================================================================================
    
    cmds.frameLayout( label='Select skinned mesh', collapsable= True, bgc =color_main );

    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    # 

    #rowLayout : Select Rig (close)
    cmds.rowLayout(numberOfColumns=2);


    cmds.textScrollList("JUN_GS_riggedMesh_tsl", 
                        height = (30),
                        numberOfRows=1, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_GS_riggedMesh_tsl\")');

    cmds.button( "name_btn_setup_rigged_mesh",
                 label='Select Objects',
                 bgc =color_btn,
                 command='JUN_cmd_select_riggedMesh(\"JUN_GS_riggedMesh_tsl\")');


    #rowLayout : Select Rig (close)
    cmds.setParent( '..' )

    #===================================================================================
    # frameLayout : Tool  Setup select rigged mesh (close)
    #===================================================================================
    cmds.setParent( '..' )

    # paneLayout : vertical2(open)                                                      
    
    #------------------------------------------------------------------
    # columnLayout : Simulated mesh (open)                                         

    cmds.frameLayout( label='Simulated mesh', collapsable= True, bgc =color_main );

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_GS_invertShape_toolSel_Objects",
                 label='Select Objects',
                 bgc =color_btn,
                 command='JUN_cmd_GS_invertShape_toolSel_btn(\"JUN_GS_IS_simedMesh_tsl\", \"JUN_name_tootSelTgt_selNum\")');

    cmds.text( "JUN_name_tootSelTgt_selNum", align="left", label='Number:0' );
    
    cmds.textScrollList("JUN_GS_IS_simedMesh_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_GS_IS_simedMesh_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= win_width/4 - 5, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_GS_IS_simedMesh_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= win_width/4 - 5, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_GS_IS_simedMesh_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= win_width/4 - 5, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_GS_IS_simedMesh_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= win_width/4 - 5, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_GS_IS_simedMesh_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );


    cmds.setParent( '..' )
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )
    
    # columnLayout (close)                                            
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    # paneLayout : vertical2(close)                                                     
    #==============================================================================
    cmds.setParent( '..' )

    #===================================================================================
    # frameLayout : Tool : Selection(close)
    #===================================================================================
    cmds.setParent( '..' )


    #===================================================================================
    # frameLayout : create by number (open)                                                        
    #===================================================================================

    cmds.frameLayout( label='Create by number', collapsable= True, bgc =color_main );

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    GS_invertShape_time_str = int(cmds.playbackOptions(query=True, minTime=True));
    GS_invertShape_time_end = int(cmds.playbackOptions(query=True, maxTime=True));

    cmds.intFieldGrp( 'GS_IS_name_toolOption_ifg_timeStr', 
                        columnAlign = [1, 'right'], 
                        columnWidth2 = [ 100, 280 ], 
                        value1 = GS_invertShape_time_str,
                        label="Start Frame :"    );    

    cmds.intFieldGrp( 'GS_IS_name_toolOption_ifg_timeEnd', 
                        columnAlign= [1, 'right'], 
                        columnWidth2=[ 100, 280 ], 
                        value1 = GS_invertShape_time_end,
                        label="End Frame:"  );  
    

    cmds.button( "name_btn_GS_invertShape_createMeshes", 
                 label='Copy Key', 
                 bgc=color_btn, 
                 command=lambda *argv : JUN_cmd_GS_invertShape_createMeshes("JUN_GS_riggedMesh_tsl", "JUN_GS_IS_simedMesh_tsl","GS_IS_name_toolOption_ifg_timeStr","GS_IS_name_toolOption_ifg_timeEnd",JUN_test_invertShape));

    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_GS_invertShapeTool_V01_01():
    PY_JUN_makeUI_GS_invertShapeToolV01_01();

JUN_PY_GS_invertShapeTool_V01_01();