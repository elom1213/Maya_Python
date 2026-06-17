# last Update date 25 06 03
# Python Script by Ji Hun Park

# matrix constriant tool v01.01

import maya.cmds as cmds;
import sys
import traceback

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

'''
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

        

def JUN_cmd_copyKey(str_selTool_tsl_base, str_selTool_tsl_tgt, str_cpyOpt_ifg_strTime, str_cpyOpt_ifg_endTime):
    str_allItemList_base = cmds.textScrollList( str_selTool_tsl_base, q=True, allItems=True);
    str_allItemList_tgt  = cmds.textScrollList( str_selTool_tsl_tgt , q=True, allItems=True);
    int_timeStr = cmds.intFieldGrp(str_cpyOpt_ifg_strTime, q=True, value1=True);
    int_timeEnd = cmds.intFieldGrp(str_cpyOpt_ifg_endTime, q=True, value1=True);
    
    int_num_base = cmds.textScrollList( str_selTool_tsl_base, q=True, numberOfItems=True);

    for i in range(0, int_num_base):
        cmds.copyKey(str_allItemList_base[i] , time = (int_timeStr, int_timeEnd));

        try:
            cmds.pasteKey(str_allItemList_tgt[i]);
        except:
            print("pseted");
'''

#=================================================================================================================

def JUN_parent(child, str_parent):
    grp_parent = str_parent
    if not cmds.objExists(str_parent):
        grp_parent = cmds.group(em=True, name=str_parent)
    try:
        cmds.parent(child, grp_parent)
    except:
        print("prent fail : " + child + "  " + grp_parent)

def JUN_match_twoObjects(str_tgt, str_flw):     
    str_rotOrder = cmds.xform ( str_tgt, q = True, rotateOrder = True );
    vec_rotAixs  = cmds.xform ( str_tgt, q = True, rotateAxis  = True );
    vec_trs      = cmds.xform ( str_tgt, q = True,  worldSpace = True, translation = True );
    vec_rot      = cmds.xform ( str_tgt, q = True,  worldSpace = True, rotation    = True );
    
    cmds.xform ( str_flw, rotateOrder = str_rotOrder );
    cmds.xform ( str_flw, rotateAxis = vec_rotAixs );
    cmds.xform ( str_flw,  worldSpace = True, translation = vec_trs );
    cmds.xform ( str_flw,  worldSpace = True, rotation = vec_rot ); 


def JUN_cmd_make_offsetMat(str_follower, str_tgt):
    str_offsetMat = str_follower + "_offsetMat"

    if cmds.objExists(str_offsetMat):
        cmds.rename(str_offsetMat, str_offsetMat + "_old_01")

    name_offsetMat = cmds.group(em=True, name=str_offsetMat)
    cmds.addAttr(name_offsetMat, ln='offsetAttr', at='matrix');
    cmds.setAttr(name_offsetMat +".visibility", 0)

    tmp_multMat = cmds.createNode('multMatrix', name= 'tmp_multMat')

    # make tmp_posFol for joint which has joint orientation
    '''
    name_tmp_pos = "tmp_posFol"
    cmds.group(em=True, name=name_tmp_pos)
    JUN_match_twoObjects(str_follower, name_tmp_pos)
    cmds.connectAttr(name_tmp_pos + ".worldMatrix[0]", tmp_multMat + ".matrixIn[0]")
    '''
    cmds.connectAttr(str_follower + ".worldMatrix[0]", tmp_multMat + ".matrixIn[0]")
    cmds.connectAttr(str_tgt + ".worldInverseMatrix[0]", tmp_multMat + ".matrixIn[1]")
    cmds.connectAttr(tmp_multMat + ".matrixSum", name_offsetMat + '.offsetAttr')
    cmds.disconnectAttr(tmp_multMat + ".matrixSum",  name_offsetMat + ".offsetAttr");

    cmds.delete(tmp_multMat)

    JUN_parent(name_offsetMat, "JUN_matAll_grp")

    return name_offsetMat

def JUN_make_matrixGroup(str_tgt, attr_matName):
    name_matGrp = str_tgt + "_" + attr_matName

    if cmds.objExists(name_matGrp):
        cmds.rename(name_matGrp, name_matGrp + "_old_01")

    grp_mat = cmds.group(em=True)
    cmds.addAttr(grp_mat, ln='attr_' + attr_matName, at='matrix')
    cmds.setAttr(grp_mat +".visibility", 0)
    grp_mat_rename = cmds.rename(grp_mat, name_matGrp)
    JUN_parent(grp_mat_rename, "JUN_matAll_grp")
    return grp_mat_rename

def JUN_make_rotateOffset_forJoint(fol, grp_mat):
    JUN_match_twoObjects(fol, grp_mat)
    cmds.setAttr(grp_mat+".translateX", 0)
    cmds.setAttr(grp_mat+".translateY", 0)
    cmds.setAttr(grp_mat+".translateZ", 0)

    tmp_comMat = cmds.createNode('composeMatrix', name =  "tmp_comMat")
    cmds.connectAttr(grp_mat + ".rotate", tmp_comMat + ".inputRotate")
    cmds.connectAttr(tmp_comMat + ".outputMatrix", grp_mat + ".attr_parMat")
    cmds.disconnectAttr(tmp_comMat + ".outputMatrix", grp_mat + ".attr_parMat")
    cmds.delete(tmp_comMat)
    return grp_mat

def JUN_cmd_matrixConstraint_01(str_selTool_tsl_targets,
                                str_selTool_tsl_followers,
                                copyKey_maintainOff_cbg,
                                copyKey_tr_cbg,
                                copyKey_ro_cbg,
                                copyKey_sc_cbg):
    str_tgts = cmds.textScrollList( str_selTool_tsl_targets, q=True, allItems=True);
    str_followers  = cmds.textScrollList( str_selTool_tsl_followers , q=True, allItems=True);

    maintainOffset = cmds.checkBoxGrp(copyKey_maintainOff_cbg, q=True, value1=True);
    link_tr = cmds.checkBoxGrp(copyKey_tr_cbg, q=True, value1=True);
    link_ro = cmds.checkBoxGrp(copyKey_ro_cbg, q=True, value1=True);
    link_sc = cmds.checkBoxGrp(copyKey_sc_cbg, q=True, value1=True);
    
    int_num_tgts = cmds.textScrollList( str_selTool_tsl_targets, q=True, numberOfItems=True);

    for i in range(0, int_num_tgts):
        try:
            fol = str_followers[i]
            tgt = str_tgts[i]
            offsetMat = JUN_cmd_make_offsetMat(fol, tgt)
            multMat = cmds.createNode('multMatrix', name= tgt + '_MultMatrix')

            cmds.connectAttr(offsetMat + ".offsetAttr", multMat + ".matrixIn[0]")
            cmds.connectAttr(tgt + ".worldMatrix[0]", multMat + ".matrixIn[1]")

            fol_parent = cmds.listRelatives(fol, parent=True, fullPath=False)

            if not fol_parent:
                fol_parent = JUN_make_matrixGroup(tgt, "unit")
                cmds.connectAttr(fol_parent + ".attr_unit", multMat + ".matrixIn[2]")
            else:
                cmds.connectAttr(fol_parent[0] + ".worldInverseMatrix[0]", multMat + ".matrixIn[2]")
            
            dectMat = cmds.createNode('decomposeMatrix', name= tgt + '_DecMatrix')

            cmds.connectAttr(multMat + ".matrixSum", dectMat + ".inputMatrix")

            if link_tr:
                cmds.connectAttr(dectMat + ".outputTranslate", fol + ".translate")
            if link_ro:
                cmds.connectAttr(dectMat + ".outputRotate", fol + ".rotate")
            if link_tr:
                cmds.connectAttr(dectMat + ".outputScale", fol + ".scale")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_matrixContstraintUI ():
    str_winTitle = "CopyKey Tool";
    str_winName = "Junny_win_matrixConstarint_01";
    win_width = 480;
    win_height = 700;

    color_mainDark = [0.65, 0.4, 0.4];
    color_main = [0.824, 0.457, 0.039];
    color_sub = [0.937, 0.597, 0.488];
    color_btn = [1.0, 0.8, 0.7];
    color_back = [1.0, 0.761, 0.6289];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="matirx constriant tool v01.01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 03-JUN-2025\')".format(color_main)

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
                 label='Select targets', 
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_name_matConTgt_tsl\", \"JUN_name_matConTgt_selNum\")');

    cmds.text( "JUN_name_matConTgt_selNum", align="left", label='Number:0' );     

    cmds.textScrollList("JUN_name_matConTgt_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_name_matConTgt_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_name_matConTgt_tsl\", \"JUN_name_matConTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_name_matConTgt_tsl\", \"JUN_name_matConTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_name_matConTgt_tsl\", \"JUN_name_matConTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_name_matConTgt_tsl\", \"JUN_name_matConTgt_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    #------------------------------------------------------------------
    cmds.setParent( '..' )


    #------------------------------------------------------------------
    # columnLayout : Select Targets (open)                                             

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_toolSel_targets",
                 label='Select followers',
                 bgc =color_btn,
                 command='JUN_cmd_toolSel_btn(\"JUN_name_matConFollower_tsl\", \"JUN_name_matConFollower_selNum\")');
   
    cmds.text( "JUN_name_matConFollower_selNum", align="left", label='Number:0' );

    cmds.textScrollList("JUN_name_matConFollower_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_name_matConFollower_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_name_matConFollower_tsl\", \"JUN_name_matConFollower_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_name_matConFollower_tsl\", \"JUN_name_matConFollower_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_name_matConFollower_tsl\", \"JUN_name_matConFollower_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_name_matConFollower_tsl\", \"JUN_name_matConFollower_selNum\" )' );
    
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

    cmds.frameLayout( label=' Tool : constarint options', collapsable= True, bgc =color_main );

    #===========================================================================
    # buttons(open)
    cmds.rowLayout( numberOfColumns = 2 , bgc = color_sub);

    cmds.button( "name_btn_sortTargets",
                 label='Sort targets', 
                 width=win_width/2-10,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_name_matConTgt_tsl\")');

    cmds.button( "name_btn_sortFollowers",
                 label='Sort followers', 
                 width=win_width/2-10,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_name_matConFollower_tsl\")');
   
        
    # buttons(close)
    #===========================================================================
    cmds.setParent( '..' )

    #------------------------------------------------------------------
    # frameLayout : Copy Key Options (open)                                     
    cmds.setParent( '..' )

    cmds.paneLayout()

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.checkBoxGrp( "JUN_copyKey_MaintainOff_cbg", label='Maintain offset', columnWidth=(1, win_width/2-25) ,columnAlign = (1, "left"), columnAttach = (1,"both", 0) , value1 = True );
    cmds.checkBoxGrp( "JUN_copyKey_translate_cbg", label='translate', columnWidth=(1, win_width/2-25) ,columnAlign = (1, "left"), columnAttach = (1, "both",0) , value1 = True );
    cmds.checkBoxGrp( "JUN_copyKey_rotate_cbg", label='rotate', columnWidth=(1, win_width/2-25) ,columnAlign = (1, "left"), columnAttach = (1, "both",0) , value1 = True );
    cmds.checkBoxGrp( "JUN_copyKey_scale_cbg", label='scale', columnWidth=(1, win_width/2-25) ,columnAlign = (1, "left"), columnAttach = (1, "both",0) , value1 = True );

    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    cmds.setParent( '..' )

    cmds.button( "name_btn_copyKey", 
                 label='Make matrix constraint', 
                 bgc=color_btn, 
                 command='JUN_cmd_matrixConstraint_01(\"JUN_name_matConTgt_tsl\", \"JUN_name_matConFollower_tsl\",\"JUN_copyKey_MaintainOff_cbg\",\"JUN_copyKey_translate_cbg\",\"JUN_copyKey_rotate_cbg\",\"JUN_copyKey_scale_cbg\")');

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_matrixCon_01_01():
    PY_JUN_makeUI_matrixContstraintUI();

PY_JUN_makeUI_matrixContstraintUI();