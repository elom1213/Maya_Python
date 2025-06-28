# last Update date 23 06 12
# Python Script by Ji Hun Park

# Selction Tool V02.01

# 23 06 12
# Update functions
# JUN_cmd_SelTool_toolSelType_btn_V02
# JUN_cmd_Select_ByType_V02


import maya.cmds as cmds;

#===================================================================================
# Global Value
#===================================================================================


global GLB_JUN_set_constraint 
GLB_JUN_set_constraint = {'aimConstraint', 'orientConstraint', 'pointConstraint', 'scaleConstraint', 'parentConstraint'}

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

#===================================================================================
# tsl edit button
#===================================================================================

def JUN_cmd_SelTool_toolSel_btn (str_toolSelOpt_rbg_option, 
                                 str_selTool_tsl_selList, 
                                 str_selTool_t_selNum ):

    int_selOpt  = cmds.radioButtonGrp( str_toolSelOpt_rbg_option,  q=True, select=True );
    str_selList = [];
    
    if int_selOpt == 2: # sSelected
        str_selList = cmds.ls ( sl=True, fl=True );
    elif int_selOpt == 1 : # Hierarchy
        str_selList = BF_SELECTION_makeList_hierarchy ( cmds.ls ( sl=True, fl=True ), 1, 1 );

    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList );
    
    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );


def JUN_cmd_SelTool_toolSelType_btn (str_toolSelOpt_rbg_option, 
                                     str_selTool_tsl_selList,
                                     str_selTool_t_selNum ):

    int_selOpt  = cmds.radioButtonGrp( str_toolSelOpt_rbg_option,  q=True, select=True );
    str_selList = [];
    
    if int_selOpt == 2: # s Selected
        str_selList = cmds.ls ( sl=True, fl=True );
    elif int_selOpt == 1 : # Hierarchy
        str_selList = BF_SELECTION_makeList_hierarchy ( cmds.ls ( sl=True, fl=True ), 1, 1 );
    
    name_types = set();

    for sl in str_selList :
        name_types.add(cmds.objectType(sl));
    name_types = sorted(list(name_types));

    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = name_types );
    
    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );


def JUN_cmd_SelTool_toolSelType_btn_V02 (str_toolSelOpt_rbg_option, 
                                         str_selTool_tsl_selList,
                                         str_selTool_t_selNum ):

    int_selOpt  = cmds.radioButtonGrp( str_toolSelOpt_rbg_option,  q=True, select=True );
    str_selList = [];
    
    if int_selOpt == 2: # s Selected
        str_selList = cmds.ls ( sl=True, fl=True );
    elif int_selOpt == 1 : # Hierarchy
        str_selList = BF_SELECTION_makeList_hierarchy ( cmds.ls ( sl=True, fl=True ), 1, 1 );
    
    name_types = set();

    for sl in str_selList :

        shape_current = cmds.listRelatives(sl, shapes=True);
        
        if(shape_current) :
            print(str(shape_current) + "\n")
            print(str(shape_current[0]) + "\n")
            shape_current = sl + "|" + shape_current[0]
            type_current =  cmds.objectType(shape_current)
        else :
            type_current = cmds.objectType(sl)

        name_types.add(type_current);

    name_types = sorted(list(name_types));

    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = name_types );
    
    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );


def JUN_cmd_tsl_select ( str_selTool_tsl_selList ):

    str_scrollList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True );
    
    cmds.select ( str_scrollList );

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
 
 
 #===================================================================================
# functions : UI
#===================================================================================


def JUN_cmd_Select_ByName(JUN_name_toolSelTyp_tsl, JUN_name_toolSelObjs_tsl, JUN_name_toolSel_cbg_invertSelect, JUN_name_SelName):

    str_allItemList_type = JUN_name_SelName
    str_allItemList_Objest  = cmds.textScrollList( JUN_name_toolSelObjs_tsl , q=True, allItems=True);
    int_invertSelect = cmds.checkBoxGrp(JUN_name_toolSel_cbg_invertSelect, q=True, value1=True);

    sel_list = set();

    for obj in str_allItemList_Objest :
        shape_current = cmds.listRelatives(obj, shapes=True);
        
        if(shape_current) :
            print(str(shape_current) + "\n")
            print(str(shape_current[0]) + "\n")
            shape_current = obj + "|" + shape_current[0]
            type_current =  cmds.objectType(shape_current)
        else :
            type_current = cmds.objectType(obj)

        print(obj)
        print("shepe : " + str(shape_current))
        print("type  : " + type_current)
        print("\n")

        if type_current in str_allItemList_type :
            sel_list.add(obj);
    
    if(int_invertSelect) :
        sel_list = set(str_allItemList_Objest) - sel_list;

    cmds.select(sel_list);
    cmds.textScrollList( JUN_name_toolSelObjs_tsl, e=True, deselectAll=True);
    cmds.textScrollList( JUN_name_toolSelObjs_tsl, e=True, selectItem=sel_list);

def JUN_cmd_Select_ByType(JUN_name_toolSelTyp_tsl, JUN_name_toolSelObjs_tsl, JUN_name_toolSel_cbg_invertSelect):

    str_allItemList_Types = cmds.textScrollList( JUN_name_toolSelTyp_tsl, q=True, allItems=True);
    str_allItemList_Objest  = cmds.textScrollList( JUN_name_toolSelObjs_tsl , q=True, allItems=True);
    int_invertSelect = cmds.checkBoxGrp(JUN_name_toolSel_cbg_invertSelect, q=True, value1=True);

    sel_list = set();

    for obj in str_allItemList_Objest :
        type_current = cmds.objectType(obj);
        if type_current in str_allItemList_Types :
            sel_list.add(obj);
    
    if(int_invertSelect) :
        sel_list = set(str_allItemList_Objest) - sel_list;

    cmds.select(sel_list);
    cmds.textScrollList( JUN_name_toolSelObjs_tsl, e=True, deselectAll=True);
    cmds.textScrollList( JUN_name_toolSelObjs_tsl, e=True, selectItem=sel_list);


def JUN_cmd_Select_ByType_V02(JUN_name_toolSelTyp_tsl, JUN_name_toolSelObjs_tsl, JUN_name_toolSel_cbg_invertSelect):

    str_slItemList_Shape = cmds.textScrollList( JUN_name_toolSelTyp_tsl, q=True, selectItem=True);

    JUN_cmd_Select_ByName(JUN_name_toolSelTyp_tsl, JUN_name_toolSelObjs_tsl, JUN_name_toolSel_cbg_invertSelect, str_slItemList_Shape);
        


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_SelectionTool ():
    str_winTitle = "Selection Tool";
    str_winName = "Junny_win_Selection_Tool";
    win_width = 480;
    win_height = 500;

    # color_mainDark = [0.652, 0.363, 0.363];
    color_mainDark = [0.65, 0.4, 0.4];
    color_main = [0.824, 0.457, 0.039];
    color_sub = [0.937, 0.597, 0.488];
    color_btn = [1.0, 0.8, 0.7];
    color_back = [1.0, 0.761, 0.6289];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="Selection Tool V02.01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 12-JUN-2023\')".format(color_main)

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
    # frameLayout : Tool  Selection(open)
    #===================================================================================
    
    cmds.frameLayout( label='Tool : Selection', collapsable= True, bgc =color_main );

    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    #                                                                                   
    cmds.radioButtonGrp(  "JUN_name_toolSelOpt_rbg_option", label="Section Option: ", columnWidth3=[ 100, 130, 130], numberOfRadioButtons=2, labelArray2=['Hierarchy', 'Selected' ], select=1 );

    cmds.checkBoxGrp( "JUN_name_toolSel_cbg_invertSelect", label='Invert Select Type', columnWidth2=(100, 130) , columnAttach2 = ("both", "both") , value1 = False );

    cmds.paneLayout( configuration= "vertical2" )

    #------------------------------------------------------------------
    # columnLayout : Select Base (open)                                          

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    
    
    cmds.button( "name_btn_toolSel_Types", 
                 label='Select Type', 
                 bgc=color_btn, 
                 command='JUN_cmd_SelTool_toolSelType_btn_V02(\"JUN_name_toolSelOpt_rbg_option\", \"JUN_name_toolSelTyp_tsl\", \"JUN_name_tootSelBase_selNum\")');

    cmds.text( "JUN_name_tootSelBase_selNum", align="left", label='Number:0' );     

    cmds.textScrollList("JUN_name_toolSelTyp_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        # selectCommand='JUN_cmd_tsl_select(\"JUN_name_toolSelTyp_tsl\")');
                        );

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add_type  ( \"JUN_name_toolSelBase_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_name_toolSelTyp_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_name_toolSelTyp_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_name_toolSelTyp_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    #------------------------------------------------------------------
    cmds.setParent( '..' )


    #------------------------------------------------------------------
    # columnLayout : Select Targets (open)                                             

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_toolSel_Objects",
                 label='Select Objects',
                 bgc =color_btn,
                 command='JUN_cmd_SelTool_toolSel_btn(\"JUN_name_toolSelOpt_rbg_option\",\"JUN_name_toolSelObjs_tsl\", \"JUN_name_tootSelTgt_selNum\")');
   
    cmds.text( "JUN_name_tootSelTgt_selNum", align="left", label='Number:0' );

    cmds.textScrollList("JUN_name_toolSelObjs_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_name_toolSelObjs_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_name_toolSelObjs_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_name_toolSelObjs_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_name_toolSelObjs_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_name_toolSelObjs_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )
    
    # Shader Endgine(SG) Tool (close)                                            
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
    # frameLayout : Select By Shape (open)                                                        
    #===================================================================================

    cmds.frameLayout( label=' Tool : Select By Shape', collapsable= True, bgc =color_main );

    #===========================================================================
    # buttons(open)
    cmds.rowLayout( numberOfColumns = 2 , bgc = color_sub);

    cmds.button( "name_btn_Select_Mesh", 
                 width=win_width/2 -10,
                 label='Mesh', 
                 bgc=color_btn, 
                 command='JUN_cmd_Select_ByName(\"JUN_name_toolSelTyp_tsl\", \"JUN_name_toolSelObjs_tsl\",\"JUN_name_toolSel_cbg_invertSelect\",\"mesh\")');

    cmds.button( "name_btn_Select_Curve", 
                 width=win_width/2 -10,
                 label='nurbsCurve', 
                 bgc=color_btn, 
                 command='JUN_cmd_Select_ByName(\"JUN_name_toolSelTyp_tsl\", \"JUN_name_toolSelObjs_tsl\",\"JUN_name_toolSel_cbg_invertSelect\",\"nurbsCurve\")');

    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns = 2 , bgc = color_sub);

    cmds.button( "name_btn_Select_Joint", 
                 width=win_width/2 -10,
                 label='Joint', 
                 bgc=color_btn, 
                 command='JUN_cmd_Select_ByName(\"JUN_name_toolSelTyp_tsl\", \"JUN_name_toolSelObjs_tsl\",\"JUN_name_toolSel_cbg_invertSelect\",\"joint\")');

    cmds.button( "name_btn_Select_Constraint", 
                 width=win_width/2 -10,
                 label='Constraint', 
                 bgc=color_btn, 
                 command='JUN_cmd_Select_ByName(\"JUN_name_toolSelTyp_tsl\", \"JUN_name_toolSelObjs_tsl\",\"JUN_name_toolSel_cbg_invertSelect\",GLB_JUN_set_constraint)');
    

    #------------------------------------------------------------------
    # frameLayout : Select By Shape (open)                                     
    cmds.setParent( '..' )

    cmds.button( "name_btn_SelectByType", 
                 label='Select By Type', 
                 bgc=color_btn, 
                 command='JUN_cmd_Select_ByType_V02(\"JUN_name_toolSelTyp_tsl\", \"JUN_name_toolSelObjs_tsl\",\"JUN_name_toolSel_cbg_invertSelect\")');

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_SelectionTool_V02_01():
    PY_JUN_makeUI_SelectionTool();

PY_JUN_makeUI_SelectionTool();