# last Update date 25 11 07
# Python Script by Ji Hun Park

# Number tool V01.01
# V01.01 

import maya.cmds as cmds;
import re;

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


def JUN_cmd_getAttr_btn_v02(source_tsl, attr_tsl):
    lst_src = cmds.textScrollList( source_tsl, q=True, allItems=True)
    lst_attrName = cmds.listAttr(lst_src[0])
    full_attr = []

    for i in range(0, len(lst_src)):
        for attr in lst_attrName:
            idices = []
            try:
                idices = cmds.getAttr(f"{lst_src[i]}.{attr}", multiIndices=True) or []
            except:
                print("error : " + f"{lst_src[i]}.{attr}")

            for j in idices:
                full_attr.append(f"{attr}[{i}]")

    lst_attrName.extend(full_attr)
    lst_attrName.sort()

    cmds.textScrollList( attr_tsl, e=True, removeAll=True )
    cmds.textScrollList( attr_tsl, e=True, append=lst_attrName)

def JUN_cmd_search_btn(attr_tsl, search_tf):
    lst_attr = cmds.textScrollList( attr_tsl, q=True, allItems=True)
    len_attr = len(lst_attr)

    tkn_attr = cmds.textField(search_tf, q=True, text=True);

    cmds.textScrollList( attr_tsl, e=True, deselectAll=True)
    for idx in range(0, len_attr):
        if tkn_attr in lst_attr[idx]:
            cmds.textScrollList( attr_tsl, e=True, selectIndexedItem=idx+1)
            # lst_select.append(tkn_attr)


def JUN_cmd_set_number(source_tsl, attr_tsl, name_attriName_tf, ifg_inputNum, ifg_jumpNum):
    lst_src = cmds.textScrollList( source_tsl, q=True, allItems=True)
    lst_attr = cmds.textScrollList( attr_tsl, q=True, selectItem=True)
    attriName_forCmd = cmds.textField(name_attriName_tf, q=True, text=True)

    num_input = cmds.floatFieldGrp(ifg_inputNum, q=True, value1=True)
    num_jump = cmds.floatFieldGrp(ifg_jumpNum, q=True, value1=True)
    num_forAdd = num_input

    for i in range(0, len(lst_src)):
        if lst_attr is None:
            cmds.setAttr(lst_src[i] + "." + attriName_forCmd, num_forAdd)
        else:
            cmds.setAttr(lst_src[i] + "." + lst_attr[0], num_forAdd)
        
        num_forAdd += num_jump


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_numberTool ():
    str_winTitle = "Number Tool";
    str_winName = "Junny_win_Number_Tools";
    win_width = 480;
    win_height = 600;

    color_mainDark = [0.1, 0.15, 0.45]   
    color_main     = [0.0, 0.45, 0.75]   
    color_sub      = [0.4, 0.7, 0.9]     
    color_btn      = [0.7, 0.9, 1.0]     
    color_back     = [0.85, 0.95, 1.0]   
    color_white    = [1.0, 1.0, 1.0]

    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="Number Tool V01.01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 07-NOV-2025\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    
    cmds.columnLayout(adjustableColumn=True, 
                        bgc =color_mainDark, 
                        width = 390 );

    tab_all = cmds.tabLayout();

    #===================================================================================
    # UI: Colum Layout(open)
    # connect BS
    #===================================================================================
    tab_connectBS = cmds.columnLayout(adjustableColumn=True, 
                                            columnAttach=('both', 5), 
                                            rowSpacing=6, 
                                            bgc =color_mainDark, 
                                            width = 390 );
         
    #===================================================================================
    # frameLayout : Tool  Selection(open)
    #===================================================================================
    
    cmds.frameLayout( label='Source', collapsable= True, bgc =color_main );

    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    #                                                                                   
    
    cmds.paneLayout( configuration= "vertical2" )

    #------------------------------------------------------------------
    # columnLayout : Select Base (open)                                          

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    

    cmds.text( "JUN_connectBS_source_selNum", align="left", label='Number:0' );     

    cmds.textScrollList("JUN_numberTool_source_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_numberTool_source_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_numberTool_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_numberTool_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_numberTool_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_numberTool_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )

    # rowLayout : command tsl (open)
    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_toolSel_base", 
                 label='Select Source', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_numberTool_source_tsl\", \"JUN_connectBS_source_selNum\")');

    cmds.setParent( '..' )
    cmds.rowLayout( numberOfColumns=1 );
                 
    cmds.button( "name_btn_sortBase",
                 label='Sort source', 
                 width=win_width/2-15,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_numberTool_source_tsl\")');
    # rowLayout : command tsl (close)
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    cmds.setParent( '..' )


    #------------------------------------------------------------------
    # columnLayout : Source's atttribute (open)                                             

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

   
    cmds.text( "JUN_name_tootSelTgt_selNum", align="left", label='Number:0' );

    cmds.textScrollList("JUN_numberTool_attr_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True)

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_numberTool_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_numberTool_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_numberTool_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_numberTool_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )
    
    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_getAttr_base", 
                 label='List attributes', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_getAttr_btn_v02(\"JUN_numberTool_source_tsl\", \"JUN_numberTool_attr_tsl\")');

    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns=2 );

    cmds.text( label='Search token : ', align = 'left' ,width=win_width/4-30);    
    cmds.textField( 'name_search_tf', bgc=color_white, width=win_width/4-15)
    cmds.textField( 'name_search_tf', edit = True,  enterCommand= 'JUN_cmd_search_btn(\"JUN_numberTool_attr_tsl\", \"name_search_tf\")')

    cmds.setParent( '..' )


    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_search_base", 
                 label='Search', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_search_btn(\"JUN_numberTool_attr_tsl\", \"name_search_tf\")');

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

    cmds.frameLayout( label=' Number option', collapsable= True, bgc =color_main );

    cmds.rowLayout( numberOfColumns=2 );
    cmds.text( "JUN_name_numStr", align="left", label='attribute name',width=win_width/4-30 );

    cmds.textField( 'name_attriName_tf', bgc=color_white, width=win_width/4-15)
    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns=2 );
    cmds.text( "JUN_name_numStr", align="left", label='input number',width=win_width/4-30 );

    cmds.floatFieldGrp( 'JUN_numTool_ifg_inputNum', 
                        width=win_width/4-15,
                        columnAlign = [1, 'right'], 
                        columnWidth2 = [ 100, 280 ]);    
    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns=2 );
    cmds.text( "JUN_name_numJump", align="left", label='jump number',width=win_width/4-30 );

    cmds.floatFieldGrp( 'JUN_numTool_ifg_jumpNum', 
                        width=win_width/4-15,
                        columnAlign = [1, 'right'], 
                        columnWidth2 = [ 100, 280 ]);    
    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns=2 );
    
    cmds.button( "name_btn_setNumber", 
                 label='Set Number', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command= lambda *argv : JUN_cmd_set_number("JUN_numberTool_source_tsl", "JUN_numberTool_attr_tsl","name_attriName_tf", "JUN_numTool_ifg_inputNum","JUN_numTool_ifg_jumpNum"));

    cmds.setParent( '..' )

   #===================================================================================
    # UI: Colum Layout(close)
    # connect BS
    #===================================================================================
    cmds.setParent( '..' )

    # cmds.setParent( '..' )


    cmds.tabLayout( tab_all, edit=True, tabLabel=((tab_connectBS, 'Set number')))

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );


    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_GS_invertShapeTool_V01_01():
    PY_JUN_makeUI_numberTool();

JUN_PY_GS_invertShapeTool_V01_01();