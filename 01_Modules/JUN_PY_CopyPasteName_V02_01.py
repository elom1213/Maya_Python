# last Update date 24 08 02
# Python Script by Ji Hun Park

# Copy Name Tool V02.01

import maya.cmds as cmds;

def JUN_cmd_toolSel_btn ( str_selTool_tsl_selList, str_selTool_t_selNum ):

    str_selList = cmds.ls ( sl=True, fl=True );

    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList );
    
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

def JUN_cmd_sort(str_name_tsl_input):
    str_list_tsl = cmds.textScrollList(str_name_tsl_input, q = 1, allItems=1);
    str_list_sorted = sorted(str_list_tsl);
    cmds.textScrollList(str_name_tsl_input, e=1, removeAll=1);
    cmds.textScrollList(str_name_tsl_input, e=1, append=str_list_sorted);


def JUN_cmd_nameMatch(str_selTool_tsl_base, str_selTool_tsl_tgt, str_cpyOpt_tfg_rmove):
    str_allItemList_base = cmds.textScrollList( str_selTool_tsl_base, q=True, allItems=True);
    str_allItemList_tgt  = cmds.textScrollList( str_selTool_tsl_tgt , q=True, allItems=True);
    str_remove = cmds.textFieldGrp(str_cpyOpt_tfg_rmove, q=True, text=True);
    
    int_num_base = cmds.textScrollList( str_selTool_tsl_base, q=True, numberOfItems=True);
    int_num_tgt = cmds.textScrollList( str_selTool_tsl_tgt, q=True, numberOfItems=True);

    set_tgts = set(str_allItemList_tgt);
    set_base = set(str_allItemList_base);

    list_tgt_update = [];
    list_base_toRmove = [];

    for i in range(0, int_num_base):
        str_base_strRemoved = str_allItemList_base[i].replace(str_remove, '');
        if str_base_strRemoved in set_tgts:
            list_tgt_update.append(str_base_strRemoved);
            set_tgts -= {str_base_strRemoved};
        else:
            list_base_toRmove.append(str_base_strRemoved);

    num_update_tgt = len(list_tgt_update);
    list_tgt_update.extend(list(set_tgts));

    cmds.textScrollList( str_selTool_tsl_tgt, e=True, removeAll=True ); 
    cmds.textScrollList( str_selTool_tsl_tgt, e=True, append = list_tgt_update );

    for i in range(1, num_update_tgt+1):
        cmds.textScrollList( str_selTool_tsl_tgt, e=True, selectIndexedItem = i );     

    for j in list_base_toRmove:
        cmds.textScrollList( str_selTool_tsl_base, e=True, selectItem = str_remove + j );     

        
def JUN_cmd_copyName(str_selTool_tsl_base, str_selTool_tsl_tgt, str_toolOption_tfg_prefix):
    str_allItemList_base = cmds.textScrollList( str_selTool_tsl_base, q=True, allItems=True);
    str_allItemList_tgt  = cmds.textScrollList( str_selTool_tsl_tgt , q=True, allItems=True);
    str_prefix = cmds.textFieldGrp( str_toolOption_tfg_prefix , q=True, text=True);
    
    int_num_base = cmds.textScrollList( str_selTool_tsl_base, q=True, numberOfItems=True);
    list_newName = []

    cmds.textScrollList( str_selTool_tsl_tgt, e=True, removeAll=True ); 
    
    for i in range(0, int_num_base):
        name_base = str_prefix + str_allItemList_base[i].split("|")[-1];
        name_result = cmds.rename(str_allItemList_tgt[i], name_base);
        cmds.textScrollList( str_selTool_tsl_tgt, e=True, append = name_result );       
        # try:
        #     cmds.pasteKey(str_allItemList_tgt[i]);
        # except:
        #     print("pseted");


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_copyNameUI ():
    str_winTitle = "CopyName Tool";
    str_winName = "Junny_win_CopyName_Tools";
    win_width = 480;
    win_height = 380;

    color_mainDark = [0.0, 0.2, 0.0];
    color_main = [0.3, 0.65, 0.2];
    color_sub = [0.3, 0.6, 0.1];
    color_btn = [0.95, 0.7, 0.5];
    color_back = [0.96, 0.96, 0.96];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="Copy Name Tool V02" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 02-AUG-2024\')".format(color_main)

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
    
    cmds.paneLayout( configuration= "vertical2" )

    #------------------------------------------------------------------
    # columnLayout : Select Base (open)                                          

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    
    
    cmds.button( "name_btn_toolSel_base", 
                 label='Select Base', 
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_name_toolSelBase_cpyName_tsl\", \"JUN_name_tootSelBase_selNum\")');

    cmds.text( "JUN_name_tootSelBase_selNum", align="left", label='Number:0' );     

    cmds.textScrollList("JUN_name_toolSelBase_cpyName_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_name_toolSelBase_cpyName_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_name_toolSelBase_cpyName_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_name_toolSelBase_cpyName_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_name_toolSelBase_cpyName_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_name_toolSelBase_cpyName_tsl\", \"JUN_name_tootSelBase_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    #------------------------------------------------------------------
    cmds.setParent( '..' )


    #------------------------------------------------------------------
    # columnLayout : Select Targets (open)                                             

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_toolSel_targets",
                 label='Select Targets',
                 bgc =color_btn,
                 command='JUN_cmd_toolSel_btn(\"JUN_name_toolSelTgt_cpyName_tsl\", \"JUN_name_tootSelTgt_selNum\")');
   
    cmds.text( "JUN_name_tootSelTgt_selNum", align="left", label='Number:0' );

    cmds.textScrollList("JUN_name_toolSelTgt_cpyName_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_name_toolSelTgt_cpyName_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_name_toolSelTgt_cpyName_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_name_toolSelTgt_cpyName_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_name_toolSelTgt_cpyName_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_name_toolSelTgt_cpyName_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    
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
    # frameLayout : Copy Key Options (open)                                                        
    #===================================================================================

    cmds.frameLayout( label=' Tool : Copy Options', collapsable= True, bgc =color_main );

    #===========================================================================
    # buttons(open)
    cmds.rowLayout( numberOfColumns = 2 , bgc = color_sub);

    cmds.button( "name_btn_sortBase",
                 label='Sort Base', 
                 width=win_width/2-10,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_name_toolSelBase_cpyName_tsl\")');

    cmds.button( "name_btn_sortTargets",
                 label='Sort Targets', 
                 width=win_width/2-10,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_name_toolSelTgt_cpyName_tsl\")');
   
        
    # buttons(close)
    #===========================================================================
    cmds.setParent( '..' )
    
    cmds.textFieldGrp( 'name_toolOption_tfg_prefix', 
                        columnWidth2=[ 100, 280 ], 
                        label="Prefix :"  );  
    #------------------------------------------------------------------
    # frameLayout : Copy Key Options (open)                                     
    cmds.setParent( '..' )

    cmds.button( "name_btn_copyName", 
                 label='Copy Name', 
                 bgc=color_btn, 
                 command='JUN_cmd_copyName(\"JUN_name_toolSelBase_cpyName_tsl\", \"JUN_name_toolSelTgt_cpyName_tsl\", \"name_toolOption_tfg_prefix\")');

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_CopyPasteName_V02_01():
    PY_JUN_makeUI_copyNameUI();

PY_JUN_makeUI_copyNameUI();