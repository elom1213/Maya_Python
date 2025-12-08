# last Update date 25 11 --
# Python Script by Ji Hun Park

# FKIK General Tool V01.01

import maya.cmds as cmds
import json
import sys
import traceback

from JUN_PY_matrixPinning_V01_01 import *

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


def JUN_get_list_by_shapes(str_objList, str_tgtShapesList):
    str_objList_fin = set();
    for str_obj in str_objList:
        # check iterate
        #if str_obj in str_objList_fin:
        #   print("aaa");
        str_objsShape = cmds.listRelatives ( str_obj, allDescendents=True, path=True, shapes=True );
        if str_objsShape is not None:
            for str_tgtShape in str_tgtShapesList:
#                print(str_obj);
#                print(str_tgtShape);
                str_objType = cmds.objectType(str_objsShape[0]);
                if str_tgtShape in str_objType:
                    str_objList_fin.add(str_obj);
                    break

    return str_objList_fin;

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


def JUN_MATCH_twoObjects ( str_tgtList, str_flwList, int_rotOrder, int_rotAxis, int_trs, int_rot ):     

    for i in range( 0, len(str_tgtList) ):

        str_rotOrder = cmds.xform ( str_tgtList[i], q = True, rotateOrder = True );
        vec_rotAixs  = cmds.xform ( str_tgtList[i], q = True, rotateAxis  = True );
        vec_trs      = cmds.xform ( str_tgtList[i], q = True,  worldSpace = True, translation = True );
        vec_rot      = cmds.xform ( str_tgtList[i], q = True,  worldSpace = True, rotation    = True );
        
        str_rotOrder_ori = cmds.xform ( str_flwList[i], q = True, rotateOrder = True );

        if int_rotOrder == 1: 
            cmds.xform ( str_flwList[i], rotateOrder = str_rotOrder );

        if int_rotAxis == 1: 
            cmds.xform ( str_flwList[i], rotateAxis = vec_rotAixs );

        if int_trs == 1: 
            cmds.xform ( str_flwList[i],  worldSpace = True, translation = vec_trs );
            
        if int_rot == 1: 
            cmds.xform ( str_flwList[i],  worldSpace = True, rotation = vec_rot ); 

        cmds.xform ( str_flwList[i], rotateOrder = str_rotOrder_ori );

class JUN_matcher_FKIK():
    def __init__(self):
        # IK => self.fk_List_tgt => (FK) moves self.fk_List_flw
        self.fk_List_tgt = ["l_ArmUpIK_xx_pos",
                            "l_ArmLowIK_xx_pos",
                            "l_HandIK_xx_pos",
                            "r_ArmUpIK_xx_pos",
                            "r_ArmLowIK_xx_pos",
                            "r_HandIK_xx_pos",
                            "l_LegUpIK_xx_pos",
                            "l_LegLowIK_xx_pos",
                            "l_LegAnkleIK_xx_pos",
                            "l_LegFootBallIK_xx_pos",
                            "r_LegUpIK_xx_pos",
                            "r_LegLowIK_xx_pos",
                            "r_LegAnkleIK_xx_pos",
                            "r_LegFootBallIK_xx_pos"]

        self.fk_List_flw = ["l_UpperArm_xx_ctl",
                            "l_LowerArm_xx_ctl",
                            "l_WristFK_xx_ctl",
                            "r_UpperArm_xx_ctl",
                            "r_LowerArm_xx_ctl",
                            "r_WristFK_xx_ctl",
                            "l_UpperLegFK_xx_ctl",
                            "l_LowerLegFK_xx_ctl",
                            "l_ankleFK_xx_ctl",
                            "l_FootFK_xx_ctl",
                            "r_UpperLegFK_xx_ctl",
                            "r_LowerLegFK_xx_ctl",
                            "r_ankleFK_xx_ctl",
                            "r_FootFK_xx_ctl"]

        # FK => self.fk_List_tgt => (IK) moves self.ik_List_flw
        self.ik_List_tgt = ["r_LegPole_xx_pos",
                            "l_LegPole_xx_pos",
                            "r_ArmPole_xx_pos",
                            "l_ArmPole_xx_pos",
                            "r_LegIkPos_xx_pos",
                            "r_LegToeIkPos_xx_pos",
                            "l_LegIkPos_xx_pos",
                            "l_LegToeIkPos_xx_pos",
                            "r_ArmIkPos_xx_pos",
                            "l_ArmIkPos_xx_pos"]


        self.ik_List_flw = ["r_LegPole_xx_ctl",
                            "l_LegPole_xx_ctl",
                            "r_ArmPole_xx_ctl",
                            "l_ArmPole_xx_ctl",
                            "r_foot_xx_ctl",
                            "r_toe_xx_ctl",
                            "l_foot_xx_ctl",
                            "l_toe_xx_ctl",
                            "r_ArmIK_xx_ctl",
                            "l_ArmIK_xx_ctl"]

        self.tgt_all= []
        self.flw_all= []

    def set_match_objs(self,
                       is_match_arm_left,
                       is_match_arm_right,
                       is_match_leg_left,
                       is_match_leg_right):

        if is_match_arm_left:
            self.tgt_all.extend(["l_ArmPole_xx_pos", "l_ArmIkPos_xx_pos","l_ArmUpIK_xx_pos", "l_ArmLowIK_xx_pos", "l_HandIK_xx_pos"])
            self.flw_all.extend(["l_ArmPole_xx_ctl", "l_ArmIK_xx_ctl", "l_UpperArm_xx_ctl", "l_LowerArm_xx_ctl", "l_WristFK_xx_ctl"])

        if is_match_arm_right:
            self.tgt_all.extend(["r_ArmPole_xx_pos", "r_ArmIkPos_xx_pos", "r_ArmUpIK_xx_pos", "r_ArmLowIK_xx_pos", "r_HandIK_xx_pos"])
            self.flw_all.extend(["r_ArmPole_xx_ctl", "r_ArmIK_xx_ctl", "r_UpperArm_xx_ctl", "r_LowerArm_xx_ctl", "r_WristFK_xx_ctl"])

        if is_match_leg_left:
            self.tgt_all.extend(["l_LegPole_xx_pos", "l_LegIkPos_xx_pos","l_LegToeIkPos_xx_pos","l_LegUpIK_xx_pos", "l_LegLowIK_xx_pos", "l_LegAnkleIK_xx_pos", "l_LegFootBallIK_xx_pos"])
            self.flw_all.extend(["l_LegPole_xx_ctl", "l_foot_xx_ctl","l_toe_xx_ctl", "l_UpperLegFK_xx_ctl", "l_LowerLegFK_xx_ctl", "l_ankleFK_xx_ctl", "l_FootFK_xx_ctl"])

        if is_match_leg_right:
            self.tgt_all.extend(["r_LegPole_xx_pos", "r_LegIkPos_xx_pos","r_LegToeIkPos_xx_pos", "r_LegUpIK_xx_pos", "r_LegLowIK_xx_pos", "r_LegAnkleIK_xx_pos", "r_LegFootBallIK_xx_pos"])
            self.flw_all.extend(["r_LegPole_xx_ctl", "r_foot_xx_ctl","r_toe_xx_ctl", "r_UpperLegFK_xx_ctl", "r_LowerLegFK_xx_ctl", "r_ankleFK_xx_ctl", "r_FootFK_xx_ctl"])

class JUN_cage_FKIK_Gen():
    def __init__(self):
        # [pole object, wrist]
        # [pole object, ankle, toe]
        self.lst_drv_for_baking_IK_arm_left = ["Empty", "Empty"]
        self.lst_drv_for_baking_IK_arm_right = ["Empty", "Empty"]
        self.lst_drv_for_baking_IK_leg_left = ["Empty", "Empty", "Empty"]
        self.lst_drv_for_baking_IK_leg_right = ["Empty", "Empty", "Empty"]

        self.lst_drv_all =[ self.lst_drv_for_baking_IK_arm_left,
                            self.lst_drv_for_baking_IK_arm_right,
                            self.lst_drv_for_baking_IK_leg_left,
                            self.lst_drv_for_baking_IK_leg_right]

    '''
        self.idx_IK_arm_left
        self.idx_IK_arm_right
        self.idx_IK_leg_left
        self.idx_IK_leg_right

        self.dic_lst_drv = {self.idx_IK_arm_left : self.lst_drv_for_baking_IK_arm_left,
                            self.idx_IK_arm_right : self.lst_drv_for_baking_IK_arm_right,
                            self.idx_IK_leg_left : self.lst_drv_for_baking_IK_leg_left,
                            self.idx_IK_leg_right : self.lst_drv_for_baking_IK_leg_right}
    '''
    def set_drv_pole_arm_l(self, obj):
        self.lst_drv_for_baking_IK_arm_left[0] = obj
    def set_drv_pole_arm_r(self, obj):
        self.lst_drv_for_baking_IK_arm_right[0] = obj
    def set_drv_pole_leg_l(self, obj):
        self.lst_drv_for_baking_IK_leg_left[0] = obj
    def set_drv_pole_leg_r(self, obj):
        self.lst_drv_for_baking_IK_leg_right[0] = obj

    def set_drv_wrist_l(self, obj):
        self.lst_drv_for_baking_IK_arm_left[1] = obj
    def set_drv_wrist_r(self, obj):
        self.lst_drv_for_baking_IK_arm_right[1] = obj
    def set_drv_ankle_l(self, obj):
        self.lst_drv_for_baking_IK_leg_left[1] = obj
    def set_drv_ankle_r(self, obj):
        self.lst_drv_for_baking_IK_leg_right[1] = obj

    def set_drv_toe_l(self, obj):
        self.lst_drv_for_baking_IK_leg_left[2] = obj
    def set_drv_toe_r(self, obj):
        self.lst_drv_for_baking_IK_leg_right[2] = obj

    def print_lst_all(self):
        print("lst_arm_left : " + str(self.lst_drv_for_baking_IK_arm_left))        
        print("lst_arm_right : " + str(self.lst_drv_for_baking_IK_arm_right))        
        print("lst_leg_left : " + str(self.lst_drv_for_baking_IK_leg_left))        
        print("lst_leg_right : " + str(self.lst_drv_for_baking_IK_leg_right))            


class JUN_matcher_FKIK_Gen():
    def __init__(self):
        self.tgt_all = []
        self.flw_all = []

    def clear_tgt_flw_lst(self):
        self.tgt_all.clear()
        self.flw_all.clear()
        
    def set_tgt_flw_from_tsl(self, tsl_tgt, tsl_flw):
        self.tgt_all.clear()
        self.flw_all.clear()
        lst_tgt_all = cmds.textScrollList( tsl_tgt, q=True, allItems = True );
        lst_flw_all = cmds.textScrollList( tsl_flw, q=True, allItems = True );

        if isinstance(lst_tgt_all, list):
            for item in lst_tgt_all:
                self.tgt_all.append(item)

        if isinstance(lst_flw_all, list):
            for item in lst_flw_all:
                self.flw_all.append(item)

    def append_to_tgt(self, lst_appending):
        for item in lst_appending:
            self.tgt_all.append(item)

    def append_to_flw(self, lst_appending):
        for item in lst_appending:
            self.flw_all.append(item)

def JUN_cmd_match_IK_and_FK(targetsPos_tsl, 
                           followersCtl_tsl,
                           arm_l_cbg,
                           arm_r_cbg,
                           leg_l_cbg,
                           leg_r_cbg,
                           match_ik_to_fk):

    match_arm_left = cmds.checkBoxGrp(arm_l_cbg, q=True, value1=True);
    match_arm_right = cmds.checkBoxGrp(arm_r_cbg, q=True, value1=True);
    match_leg_left = cmds.checkBoxGrp(leg_l_cbg, q=True, value1=True);
    match_leg_right = cmds.checkBoxGrp(leg_r_cbg, q=True, value1=True);

    matcher = JUN_matcher_FKIK();

    matcher.set_match_objs(match_arm_left,
                           match_arm_right,
                           match_leg_left,
                           match_leg_right)

    cmds.textScrollList( targetsPos_tsl, e=True, deselectAll = 1 );
    cmds.textScrollList( followersCtl_tsl, e=True, deselectAll = 1 );

    itemsAll_flw = cmds.textScrollList( targetsPos_tsl, q=True, allItems = True );
    itemsAll_tgt = cmds.textScrollList( followersCtl_tsl, q=True, allItems = True );

    matcher.tgt_all = JUN_get_list_ordered_by_token(itemsAll_flw, matcher.tgt_all)
    matcher.flw_all = JUN_get_list_ordered_by_token(itemsAll_tgt, matcher.flw_all)

    if match_ik_to_fk :
        matcher.tgt_all = JUN_get_list_ordered_by_token(matcher.tgt_all, matcher.ik_List_tgt)
        matcher.flw_all = JUN_get_list_ordered_by_token(matcher.flw_all, matcher.ik_List_flw)
    else :
        matcher.tgt_all = JUN_get_list_ordered_by_token(matcher.tgt_all, matcher.fk_List_tgt)
        matcher.flw_all = JUN_get_list_ordered_by_token(matcher.flw_all, matcher.fk_List_flw)

    for flw_item in matcher.flw_all:
        cmds.textScrollList( followersCtl_tsl, e=True, selectItem = flw_item );

    for tgt_item in matcher.tgt_all:
        cmds.textScrollList( targetsPos_tsl, e=True, selectItem = tgt_item );

    JUN_MATCH_twoObjects(matcher.tgt_all, matcher.flw_all, 1,1,1,1)
    
    return matcher;

#===================================================================================
# checker Start
#===================================================================================

class JUN_checker():
    def __init__(self):
        self.lst_checked__ = []

    def set_lst_checked(self, lst_str_cbg):
        self.lst_checked__.clear()
        for member_cbg in lst_str_cbg:
            state_checked = cmds.checkBoxGrp(member_cbg, q=True, value1=True)
            self.lst_checked__.append(state_checked)

    def get_lst_stat(self):
        return self.lst_checked__
    
    def is_checked(self, idx):
        return self.lst_checked__[idx]

    def dbg_print_lst_checked(self):
        print(self.lst_checked__)

#===================================================================================
# checker End
#===================================================================================


#===================================================================================
# match fk ik End
#===================================================================================


def JUN_cmd_bake_IK_FK(targetsPos_tsl, 
                        followersCtl_tsl,
                        arm_l_cbg,
                        arm_r_cbg,
                        leg_l_cbg,
                        leg_r_cbg,
                        bake_ik,
                        ifg_timeStr,
                        ifg_timeEnd):

    matcher = JUN_cmd_match_IK_and_FK(targetsPos_tsl, 
                                     followersCtl_tsl,
                                     arm_l_cbg,
                                     arm_r_cbg,
                                     leg_l_cbg,
                                     leg_r_cbg,
                                     bake_ik)

    timeStr = cmds.intFieldGrp(ifg_timeStr, q=True, value1=True);
    timeEnd = cmds.intFieldGrp(ifg_timeEnd, q=True, value1=True);

    for frame_tgt in range(timeStr, timeEnd):
        cmds.currentTime( frame_tgt, edit=True)
        # set fk to ik or ik to fk
        JUN_MATCH_twoObjects(matcher.tgt_all, matcher.flw_all, 1,1,1,1)

        frame_now = cmds.currentTime( query=True )
        cmds.setKeyframe( matcher.flw_all, t=frame_now)

def JUN_cmd_bake_IK_FK_Gen(lst_tsl_match_IK_all, 
                           lst_tsl_match_FK, 
                           lst_cbx_match, bake_ik, 
                           ifg_timeStr, 
                           ifg_timeEnd):
    mcr_FK_arm_left = JUN_matcher_FKIK_Gen()
    mcr_FK_arm_right = JUN_matcher_FKIK_Gen()
    mcr_FK_leg_left = JUN_matcher_FKIK_Gen()
    mcr_FK_leg_right = JUN_matcher_FKIK_Gen()
    mcr_IK_arm_left = JUN_matcher_FKIK_Gen()
    mcr_IK_arm_right = JUN_matcher_FKIK_Gen()
    mcr_IK_leg_left = JUN_matcher_FKIK_Gen()
    mcr_IK_leg_right = JUN_matcher_FKIK_Gen()

    mcr_assemble = JUN_matcher_FKIK_Gen()

    mcr_FK_arm_left.set_tgt_flw_from_tsl(lst_tsl_match_FK[0], lst_tsl_match_FK[1])
    mcr_FK_arm_right.set_tgt_flw_from_tsl(lst_tsl_match_FK[2], lst_tsl_match_FK[3])
    mcr_FK_leg_left.set_tgt_flw_from_tsl(lst_tsl_match_FK[4], lst_tsl_match_FK[5])
    mcr_FK_leg_right.set_tgt_flw_from_tsl(lst_tsl_match_FK[6], lst_tsl_match_FK[7])
    print(lst_tsl_match_FK)

    mcr_IK_arm_left.set_tgt_flw_from_tsl(lst_tsl_match_IK_all[0], lst_tsl_match_IK_all[1])
    mcr_IK_arm_right.set_tgt_flw_from_tsl(lst_tsl_match_IK_all[2], lst_tsl_match_IK_all[3])
    mcr_IK_leg_left.set_tgt_flw_from_tsl(lst_tsl_match_IK_all[4], lst_tsl_match_IK_all[5])
    mcr_IK_leg_right.set_tgt_flw_from_tsl(lst_tsl_match_IK_all[6], lst_tsl_match_IK_all[7])
    
    checker_body_part = JUN_checker()
    checker_body_part.set_lst_checked(lst_cbx_match)

    idx_arm_left = 0
    idx_arm_right = 1
    idx_leg_left = 2
    idx_leg_right = 3

    timeStr = cmds.intFieldGrp(ifg_timeStr, q=True, value1=True);
    timeEnd = cmds.intFieldGrp(ifg_timeEnd, q=True, value1=True);


    if bake_ik:
        if checker_body_part.is_checked(idx_arm_left):
            mcr_assemble.append_to_tgt(mcr_IK_arm_left.tgt_all)
            mcr_assemble.append_to_flw(mcr_IK_arm_left.flw_all)

        if checker_body_part.is_checked(idx_arm_right):
            mcr_assemble.append_to_tgt(mcr_IK_arm_right.tgt_all)
            mcr_assemble.append_to_flw(mcr_IK_arm_right.flw_all)

        if checker_body_part.is_checked(idx_leg_left):
            mcr_assemble.append_to_tgt(mcr_IK_leg_left.tgt_all)
            mcr_assemble.append_to_flw(mcr_IK_leg_left.flw_all)
                
        if checker_body_part.is_checked(idx_leg_right):
            mcr_assemble.append_to_tgt(mcr_IK_leg_right.tgt_all)
            mcr_assemble.append_to_flw(mcr_IK_leg_right.flw_all)
                
    else :
        if checker_body_part.is_checked(idx_arm_left):
            mcr_assemble.append_to_tgt(mcr_FK_arm_left.tgt_all)
            mcr_assemble.append_to_flw(mcr_FK_arm_left.flw_all)
            
        if checker_body_part.is_checked(idx_arm_right):
            mcr_assemble.append_to_tgt(mcr_FK_arm_right.tgt_all)
            mcr_assemble.append_to_flw(mcr_FK_arm_right.flw_all)
                
        if checker_body_part.is_checked(idx_leg_left):
            mcr_assemble.append_to_tgt(mcr_FK_leg_left.tgt_all)
            mcr_assemble.append_to_flw(mcr_FK_leg_left.flw_all)
                
        if checker_body_part.is_checked(idx_leg_right):
            mcr_assemble.append_to_tgt(mcr_FK_leg_right.tgt_all)
            mcr_assemble.append_to_flw(mcr_FK_leg_right.flw_all)
                
    print(mcr_FK_arm_left.tgt_all)
    print(mcr_assemble.tgt_all)
    print(mcr_assemble.flw_all)
    for frame_tgt in range(timeStr, timeEnd):
        cmds.currentTime( frame_tgt, edit=True)
        JUN_MATCH_twoObjects(mcr_assemble.tgt_all, mcr_assemble.flw_all, 1,1,1,1)
        frame_now = cmds.currentTime( query=True )
        cmds.setKeyframe( mcr_assemble.flw_all, t=frame_now)


def JUN_cmd_bake_IK_to_FK(targetsPos_tsl, followersCtl_tsl) :

    list_tgts = cmds.textScrollList( targetsPos_tsl, q=True, selectItem = 1);
    list_flwers = cmds.textScrollList( followersCtl_tsl, q=True, selectItem = 1);
    
    for i in range(0, 8):
        cmds.parentConstraint(list_tgts[i], list_flwers[i], maintainOffset = 1);

    list_flg_simBake = ["tx","ty","tz","rx","ry","rz","sx","sy","sz"];

    int_time_star = cmds.playbackOptions(minTime =True, q=True)
    int_time_end = cmds.playbackOptions(maxTime =True, q=True)

    cmds.bakeSimulation(list_flwers, sb = 1, t = (int_time_star, int_time_end), at = list_flg_simBake, hi = "none")

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
 
def JUN_cmd_FKIK_gen_toolSel_btn (str_selTool_tsl_selList,
                                        str_selTool_t_selNum ):

    str_selList = cmds.ls ( sl=True, fl=True );

    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList );

    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );

    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );
 
 #===================================================================================
# functions : UI
#===================================================================================

def JUN_cmd_Search_By_Token(JUN_name_RigName_tfg, JUN_name_SearchTool_SelObjs_tsl, JUN_name_SearchTool_cbg_invertSelect):

    str_token = cmds.textFieldGrp( JUN_name_RigName_tfg, q=True, text=True);
    str_allItemList_Objest  = cmds.textScrollList( JUN_name_SearchTool_SelObjs_tsl , q=True, allItems=True);
    int_invertSelect = cmds.checkBoxGrp(JUN_name_SearchTool_cbg_invertSelect, q=True, value1=True);

    search_result = set();

    for obj_name in str_allItemList_Objest :
        if str_token in obj_name :
            search_result.add(obj_name);

    if(int_invertSelect) :
        search_result = set(str_allItemList_Objest) - search_result;

    cmds.select(search_result);
    cmds.textScrollList( JUN_name_SearchTool_SelObjs_tsl, e=True, deselectAll=True);
    cmds.textScrollList( JUN_name_SearchTool_SelObjs_tsl, e=True, selectItem=search_result);

    
def JUN_get_world_positions(objects):
    pos = cmds.xform(objects, q=True, ws=True, t=True)
    return pos

def JUN_cmd_create_triangle(lst_pos):
    print(str(lst_pos[0][0]) + "  " + str(lst_pos[0][1]) +"  "+ str(lst_pos[0][2]))
    mesh_out = cmds.polyCreateFacet( p=[(lst_pos[0][0], lst_pos[0][1], lst_pos[0][2]), 
                                        (lst_pos[1][0], lst_pos[1][1], lst_pos[1][2]), 
                                        (lst_pos[2][0], lst_pos[2][1], lst_pos[2][2])] )
    return mesh_out

def JUN_parent(child, str_parent):
    grp_parent = str_parent
    if not cmds.objExists(str_parent):
        grp_parent = cmds.group(em=True, name=str_parent)
    try:
        cmds.parent(child, grp_parent)
    except:
        print("prent fail : " + child + "  " + grp_parent)

def JUN_average_position(points):
    """
    points: list of [x, y, z]
    returns: [avg_x, avg_y, avg_z]
    """

    if not points:
        return None

    # Sum each component
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_z = sum(p[2] for p in points)

    count = len(points)

    return [sum_x / count, sum_y / count, sum_z / count]

def JUN_cmd_FKIK_gen_setup_all_pos_objs(lst_tsl_source, lst_tsl_drv, lst_tsl_match_FK, lst_tsl_match_IK_all):
    lst_tri = {}
    len_for_FK_tsl = 4
    str_name_grp_posObjs = "JUN_posObjs_grp"
    lst_str_name_triMesh = ["CH_l_triArm_sfc",
                            "CH_r_triArm_sfc",
                            "CH_l_triLeg_sfc",
                            "CH_r_triLeg_sfc,"]
    
    if not cmds.objExists(str_name_grp_posObjs):
        cmds.group(em=True, name=str_name_grp_posObjs)

    lst_child_of_posObjs_grp = cmds.listRelatives(str_name_grp_posObjs, children=True, fullPath=False) or []
    
    for i in range(0, len_for_FK_tsl):
        objs_ctls  = cmds.textScrollList( lst_tsl_source[i] , q=True, allItems=True);
        lst_pos_for_tri = []
        tri_nurbs = []

        if objs_ctls is None:
            print(lst_str_name_triMesh[i] + " : Pass")
            continue

        if lst_str_name_triMesh[i] in lst_child_of_posObjs_grp:
            print("Remove exsisting : " + lst_str_name_triMesh[i])
            cmds.delete(lst_str_name_triMesh[i])
           
        tri_nurbs = cmds.nurbsPlane(degree = 1)
        cmds.DeleteHistory(tri_nurbs)

        tri_nurbs_newName = cmds.rename(tri_nurbs[0], lst_str_name_triMesh[i])

        tri_nurbs.clear()
        tri_nurbs.append(tri_nurbs_newName)

        JUN_parent(tri_nurbs[0], str_name_grp_posObjs)

        for j in range(0, 3):
            decomNode = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(objs_ctls[j] + ".worldMatrix", decomNode + ".inputMatrix")
            cmds.connectAttr(decomNode + ".outputTranslate", tri_nurbs[0] + f".controlPoints[{j}]" )

            if j == 2 :
                cmds.connectAttr(decomNode + ".outputTranslate", tri_nurbs[0] + f".controlPoints[{j+1}]" )


            lst_pos = JUN_get_world_positions(objs_ctls[j])
            lst_pos_for_tri.append(lst_pos) # [[],[],[]]


        pos_average = JUN_average_position(lst_pos_for_tri)
        loc_triAverage = cmds.spaceLocator()
        loc_child_of_sfc = loc_triAverage
        cmds.xform(loc_triAverage, translation = pos_average)


        loc_pin_on_sfc_shape = str(pin_to_surface(pm.PyNode(tri_nurbs[0]), sourceObj = loc_triAverage[0]))
        cmds.listRelatives(loc_pin_on_sfc_shape, parent=True, fullPath=False)
        loc_pin_on_sfc_xform = cmds.listRelatives(loc_pin_on_sfc_shape, parent=True, fullPath=False)
        print(loc_pin_on_sfc_xform)
        
        JUN_parent(loc_child_of_sfc, loc_pin_on_sfc_xform[0])
        JUN_parent(loc_pin_on_sfc_xform[0], str_name_grp_posObjs)
        loc_child_of_sfc[0] = cmds.rename(loc_child_of_sfc[0], loc_pin_on_sfc_xform[0] + "_tgt")
        JUN_MATCH_twoObjects( loc_pin_on_sfc_xform, [loc_child_of_sfc], 1, 1, 1, 1)



def JUN_cmd_FKIK_gen_setup_triangle_pos_objs(lst_tsl_source, cage_given=None):
    lst_tri = {}
    len_for_FK_tsl = 4
    str_name_grp_posObjs = "JUN_posObjs_grp"
    lst_str_name_triMesh = ["CH_l_triArm_sfc",
                            "CH_r_triArm_sfc",
                            "CH_l_triLeg_sfc",
                            "CH_r_triLeg_sfc,"]
    
    lst_drv = []
    
    if not cmds.objExists(str_name_grp_posObjs):
        cmds.group(em=True, name=str_name_grp_posObjs)

    lst_child_of_posObjs_grp = cmds.listRelatives(str_name_grp_posObjs, children=True, fullPath=False) or []
    
    for i in range(0, len_for_FK_tsl):
        objs_ctls  = cmds.textScrollList( lst_tsl_source[i] , q=True, allItems=True);
        lst_pos_for_tri = []
        tri_nurbs = []

        if objs_ctls is None:
            print(lst_str_name_triMesh[i] + " : Pass")
            continue

        if lst_str_name_triMesh[i] in lst_child_of_posObjs_grp:
            print("Remove exsisting : " + lst_str_name_triMesh[i])
            cmds.delete(lst_str_name_triMesh[i])
           
        tri_nurbs = cmds.nurbsPlane(degree = 1)
        cmds.DeleteHistory(tri_nurbs)

        tri_nurbs_newName = cmds.rename(tri_nurbs[0], lst_str_name_triMesh[i])

        tri_nurbs.clear()
        tri_nurbs.append(tri_nurbs_newName)

        JUN_parent(tri_nurbs[0], str_name_grp_posObjs)

        for j in range(0, 3):
            decomNode = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(objs_ctls[j] + ".worldMatrix", decomNode + ".inputMatrix")
            cmds.connectAttr(decomNode + ".outputTranslate", tri_nurbs[0] + f".controlPoints[{j}]" )

            if j == 2 :
                cmds.connectAttr(decomNode + ".outputTranslate", tri_nurbs[0] + f".controlPoints[{j+1}]" )


            lst_pos = JUN_get_world_positions(objs_ctls[j])
            lst_pos_for_tri.append(lst_pos) # [[],[],[]]


        pos_average = JUN_average_position(lst_pos_for_tri)
        loc_triAverage = cmds.spaceLocator()
        loc_child_of_sfc = loc_triAverage
        cmds.xform(loc_triAverage, translation = pos_average)


        loc_pin_on_sfc_shape = str(pin_to_surface(pm.PyNode(tri_nurbs[0]), sourceObj = loc_triAverage[0]))
        cmds.listRelatives(loc_pin_on_sfc_shape, parent=True, fullPath=False)
        loc_pin_on_sfc_xform = cmds.listRelatives(loc_pin_on_sfc_shape, parent=True, fullPath=False)
        print(loc_pin_on_sfc_xform)
        
        JUN_parent(loc_child_of_sfc, loc_pin_on_sfc_xform[0])
        JUN_parent(loc_pin_on_sfc_xform[0], str_name_grp_posObjs)
        loc_child_of_sfc[0] = cmds.rename(loc_child_of_sfc[0], loc_pin_on_sfc_xform[0] + "_tgt")
        JUN_MATCH_twoObjects( loc_pin_on_sfc_xform, [loc_child_of_sfc], 1, 1, 1, 1)

        lst_drv.append(loc_child_of_sfc[0])

    funcs = [cage_given.set_drv_pole_arm_l,
             cage_given.set_drv_pole_arm_r,
             cage_given.set_drv_pole_leg_l,
             cage_given.set_drv_pole_leg_r]

    for i, func in enumerate(funcs):
        try:
            func(lst_drv[i])
        except:
            continue

    cage_given.print_lst_all()

        

def JUN_create_loc_for_given_objs(lst_objs):
    lst_loc = []
    for obj_single in lst_objs:
        loc = cmds.spaceLocator()
        JUN_MATCH_twoObjects([obj_single] , [loc], 1, 1 ,1 ,1)
        lst_loc.append(loc[0])
    return  lst_loc

def JUN_cmd_FKIK_gen_create_pos_objs_FKIK_Gen(lst_tsl_source_FK, 
                                              lst_tsl_source_IK,
                                              lst_tsl_match_FK_ctl, 
                                              lst_tsl_match_IK_ctl, 
                                              lst_tsl_match_FK_pose_objs,
                                              lst_tsl_match_IK_pose_objs, 
                                              cage_given = None):
    # for given wrist, ankle, toe FK ctl, create loc and match it rotation to IK ctl


    # create drviers for IK to FK
    # create drivers matched with source IK object, match rotation to FK ctl

    str_name_grp_posObjs = "JUN_posObjs_grp"
    # lst_ctl_FK_for_match_posObjs = []
    # lst_ctl_IK_for_match_posObjs_rot = []
    posObj_flw = []

    if not cmds.objExists(str_name_grp_posObjs):
        cmds.group(em=True, name=str_name_grp_posObjs)

    lst_child_of_posObjs_grp = cmds.listRelatives(str_name_grp_posObjs, children=True, fullPath=False) or []
 
    for i in range(0, 4):
        ctl_FK =  cmds.textScrollList(lst_tsl_match_FK_ctl[i], q=True, allItems=True)
        source_IK =  cmds.textScrollList(lst_tsl_source_IK[i], q=True, allItems=True)
        if source_IK == None:
            print("tsl pass : " +  lst_tsl_source_IK[i])
            continue

        lst_locs_ =  JUN_create_loc_for_given_objs(source_IK)

        if ctl_FK != None:
            # for j in range(0, 3):
            clt_FK_0_to_2 = ctl_FK[:3]
            JUN_MATCH_twoObjects(clt_FK_0_to_2, lst_locs_, 1, 1, 0, 1)

        for j in range(0, len(lst_locs_)):
            name_drv = source_IK[j]+ "_drv"

            if name_drv in lst_child_of_posObjs_grp:
                print("Remove exsisting : " + name_drv)
                cmds.delete(name_drv)

            lst_locs_[j] = cmds.rename(lst_locs_[j], name_drv)
            JUN_parent( lst_locs_[j], str_name_grp_posObjs)

            cmds.parentConstraint(source_IK[j], lst_locs_[j], mo=True)

        cmds.textScrollList(lst_tsl_match_FK_pose_objs[i], e=True, removeAll=True )
        cmds.textScrollList(lst_tsl_match_FK_pose_objs[i], e=True, append = lst_locs_ );
    
    # create driver for FK to IK : wrist and ankle
    lst_locs_wrist_ankle = []
    idx_wrist_and_ankle_FK = 2
    idx_wrist_and_ankle_IK = 1
    for i in range(0,4):
        ctl_FK_all = cmds.textScrollList(lst_tsl_match_FK_ctl[i], q=True, allItems=True)
        ctl_IK_all = cmds.textScrollList(lst_tsl_match_IK_ctl[i], q=True, allItems=True)

        if ctl_FK_all == None:
            print("tsl pass : " +  lst_tsl_match_FK_ctl[i])
            continue

        name_drv = str(ctl_FK_all[idx_wrist_and_ankle_FK]) + "_drv"

        lst_locs_ = JUN_create_loc_for_given_objs([ctl_FK_all[idx_wrist_and_ankle_FK]])

        if ctl_IK_all != None:
            JUN_MATCH_twoObjects([ctl_IK_all[idx_wrist_and_ankle_IK]], lst_locs_, 1, 1, 0, 1)

        if name_drv in lst_child_of_posObjs_grp:
            print("Remove exsisting : " + name_drv)
            cmds.delete(name_drv)

        lst_locs_[0] = cmds.rename(lst_locs_[0], name_drv)
        JUN_parent(lst_locs_[0], str_name_grp_posObjs)
        cmds.parentConstraint( ctl_FK_all[idx_wrist_and_ankle_FK], lst_locs_[0], mo=True)

        lst_locs_wrist_ankle.append(lst_locs_[0])

    funcs = [cage_given.set_drv_wrist_l,
             cage_given.set_drv_wrist_r,
             cage_given.set_drv_ankle_l,
             cage_given.set_drv_ankle_r]
    
    for i, func in enumerate(funcs):
        try:
            func(lst_locs_wrist_ankle[i])
        except:
            continue

    # cage_given.set_drv_wrist_l(lst_locs_wrist_ankle[0])
    # cage_given.set_drv_wrist_r(lst_locs_wrist_ankle[1])
    # cage_given.set_drv_ankle_l(lst_locs_wrist_ankle[2])
    # cage_given.set_drv_ankle_r(lst_locs_wrist_ankle[3])

    # create driver for FK to IK : toe
    lst_locs_toe = []
    idx_toe_FK = 3
    idx_toe_IK = 1
    for i in range(2,4):
        ctl_FK_legOnly = cmds.textScrollList(lst_tsl_match_FK_ctl[i], q=True, allItems=True)
        ctl_IK_legOnly = cmds.textScrollList(lst_tsl_match_IK_ctl[i], q=True, allItems=True)

        if ctl_FK_legOnly == None:
            print("tsl pass : " +  lst_tsl_match_FK_ctl[i])
            continue

        name_drv = str(ctl_FK_legOnly[idx_toe_FK]) + "_drv"

        lst_locs_ = JUN_create_loc_for_given_objs([ctl_FK_legOnly[idx_toe_FK]])

        if ctl_IK_legOnly != None:
            JUN_MATCH_twoObjects([ctl_IK_legOnly[idx_toe_IK]], lst_locs_, 1, 1, 0, 1)

        if name_drv in lst_child_of_posObjs_grp:
            print("Remove exsisting : " + name_drv)
            cmds.delete(name_drv)

        lst_locs_[0] = cmds.rename(lst_locs_[0], name_drv)
        JUN_parent(lst_locs_[0], str_name_grp_posObjs)
        cmds.parentConstraint( ctl_FK_legOnly[idx_toe_FK], lst_locs_[0], mo=True)

        lst_locs_toe.append(lst_locs_[0])

    funcs = [cage_given.set_drv_toe_l,
             cage_given.set_drv_toe_r]
    
    for i, func in enumerate(funcs):
        try:
            func(lst_locs_toe[i])
        except:
            continue

    # cage_given.set_drv_toe_l(lst_locs_toe[0])
    # cage_given.set_drv_toe_r(lst_locs_toe[1])

    cage_given.print_lst_all()

    for i in range(0, 4):
        cmds.textScrollList(lst_tsl_match_IK_pose_objs[i], e=True, removeAll=True )
        try:
            cmds.textScrollList(lst_tsl_match_IK_pose_objs[i], e=True, append =  cage_given.lst_drv_all[i] );
        except:
            continue



    #fill lst_ctl_for_match_posObjs


    # JUN_MATCH_twoObjects(lst_ctl_FK_for_match_posObjs, posObj_flw, 1, 1, 1, 1)
    # JUN_MATCH_twoObjects(lst_ctl_IK_for_match_posObjs_rot, posObj_flw, 1, 1, 0, 1)


    return

def JUN_browse_json_save_path(fileMode_given=0):
    """
    Opens a file explorer dialog and lets the user choose where to save a JSON file.
    Returns selected file path as string, or None if canceled.
    """
    file_path = cmds.fileDialog2(
        dialogStyle=2,
        fileMode=fileMode_given, # 0 = save file, 1 = open file
        caption="Save JSON File",
        fileFilter="JSON Files (*.json)"
    )

    if file_path:
        return file_path[0]  # Maya returns a list
    return None

def save_multiple_tsl_to_json(tsl_list, file_path):
    """
    Save multiple textScrollLists and their items into one JSON file.

    tsl_list: list of textScrollList names
    """
    data = {}

    for tsl in tsl_list:
        if not cmds.textScrollList(tsl, exists=True):
            cmds.warning(f"{tsl} does not exist. Skipping.")
            continue

        items = cmds.textScrollList(tsl, q=True, ai=True) or []
        data[tsl] = items

    # Write JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Saved multiple textScrollLists to: {file_path}")

def load_multiple_tsl_from_json(file_path):
    """
    Read JSON file and restore items into each textScrollList.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for tsl, items in data.items():
        if not cmds.textScrollList(tsl, exists=True):
            cmds.warning(f"{tsl} does not exist in current UI. Skipping.")
            continue

        cmds.textScrollList(tsl, e=True, ra=True)  # remove all existing
        cmds.textScrollList(tsl, e=True, a=items)  # add items

    print("Loaded JSON content into textScrollLists.")

def JUN_cmd_FKIK_gen_save_setting(lst_tsl_match_FK_all, lst_tsl_match_IK_all):
    path_to_save = JUN_browse_json_save_path()
    tsl_to_save = lst_tsl_match_FK_all + lst_tsl_match_IK_all
    save_multiple_tsl_to_json(tsl_to_save, path_to_save)


def JUN_cmd_FKIK_gen_load_setting():
    path_to_load = JUN_browse_json_save_path(1)
    tsl_loaded = load_multiple_tsl_from_json(path_to_load)

#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_general_FKIKTool ():
    str_winTitle = "FKIK General Tool";
    str_winName = "Junny_win_FKIK_General_Tool";
    win_width = 700;
    win_height = 1000;


    color_mainDark = [0.10, 0.12, 0.18]
    color_main     = [0.14, 0.17, 0.25]
    color_sub      = [0.18, 0.22, 0.32]
    color_btn      = [0.30, 0.35, 0.45]
    color_back     = [0.12, 0.14, 0.20]
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="FKIK General Tool V01.01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: __-NOV-2025\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    

    #===================================================================================
    #===================================================================================
    # Tab All (open)
    #===================================================================================
    #===================================================================================
    
    cmds.columnLayout(adjustableColumn=True, 
                      columnAttach=('both', 5), 
                      rowSpacing=6, 
                      bgc =color_mainDark, 
                      width = 390 );
    
    tab_all = cmds.tabLayout();

    #===================================================================================
    # Tab : Source (open)
    #===================================================================================
    
    tab_source = cmds.columnLayout(adjustableColumn=True, 
                                    columnAttach=('both', 5), 
                                    rowSpacing=6, 
                                    bgc =color_mainDark, 
                                    width = 390 );
    
    #===================================================================================
    # frameLayout : Tool  Setup FK source(open)
    #===================================================================================
    
    cmds.frameLayout( label='Tool : Setup Source', collapsable= True, bgc =color_main );

    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_text_ctl_FK", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='Set source : FK ' );
    
    cmds.setParent( '..' )

    cmds.paneLayout( configuration= "vertical4" )

    mult_tsl_ctl_FK_hight = 0.09

    # tsl ctl fk arm left(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_arm_left", align="left", font = "boldLabelFont",  label='Arm Left' );
    cmds.text( "JUN_name_selNum_ctl_IK_arm_left", align="left", label='Number:0' );

    str_tls_ctl_FK_arm_left = "JUN_FKIK_Gen_ctl_FK_arm_left"

    cmds.textScrollList(str_tls_ctl_FK_arm_left, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_FK_arm_left\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_FK_arm_left}", \"JUN_name_selNum_ctl_IK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_FK_arm_left}", \"JUN_name_selNum_ctl_IK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_FK_arm_left}", \"JUN_name_selNum_ctl_IK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_FK_arm_left}", \"JUN_name_selNum_ctl_IK_arm_left\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_FK_arm_left}", \"JUN_name_selNum_ctl_IK_arm_left\")');

    cmds.setParent( '..' )
    # tsl ctl fk arm left(close)

    # tsl ctl fk arm right(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_arm_right", align="left", font = "boldLabelFont",  label='Arm Right' );
    cmds.text( "JUN_name_selNum_ctl_arm_right", align="left", label='Number:0' );

    str_tls_ctl_FK_arm_right = "JUN_FKIK_Gen_ctl_FK_arm_right"
    cmds.textScrollList(str_tls_ctl_FK_arm_right, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_FK_arm_right\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_FK_arm_right}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_FK_arm_right}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_FK_arm_right}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_FK_arm_right}", \"JUN_name_selNum_ctl_arm_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_FK_arm_right}", \"JUN_name_selNum_ctl_arm_right\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk arm right(close)

    # tsl ctl fk leg left(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_leg_left", align="left", font = "boldLabelFont",  label='Leg Left' );
    cmds.text( "JUN_name_selNum_ctl_leg_left", align="left", label='Number:0' );

    str_tls_ctl_FK_leg_left = "JUN_FKIK_Gen_ctl_FK_leg_left"
    cmds.textScrollList(str_tls_ctl_FK_leg_left, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_FK_leg_left\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_FK_leg_left}", \"JUN_name_selNum_ctl_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_FK_leg_left}", \"JUN_name_selNum_ctl_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_FK_leg_left}", \"JUN_name_selNum_ctl_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_FK_leg_left}", \"JUN_name_selNum_ctl_leg_left\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_FK_leg_left}", \"JUN_name_selNum_ctl_leg_left\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk leg left(close)

    # tsl ctl fk leg right(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_leg_right", align="left", font = "boldLabelFont",  label='Leg right' );
    cmds.text( "JUN_name_selNum_ctl_leg_right", align="left", label='Number:0' );

    str_tls_ctl_FK_leg_right = "JUN_FKIK_Gen_ctl_FK_leg_right"
    cmds.textScrollList(str_tls_ctl_FK_leg_right, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_FK_leg_right\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_FK_leg_right}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_FK_leg_right}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_FK_leg_right}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_FK_leg_right}", \"JUN_name_selNum_ctl_leg_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_FK_leg_right}", \"JUN_name_selNum_ctl_leg_right\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk leg right(close)
    
    cmds.setParent( '..' )
    #===================================================================================
    # frameLayout : Tool  Setup FK source(close)
    #===================================================================================

    mult_tsl_ctl_IK_hight = 0.09
    mult_tsl_btn_width_01 = 25
    #===================================================================================
    # frameLayout : Tool  Setup IK source(open)
    #==================================================================================
    
    ###
    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_text_ctl_FK", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='Set source : IK ' );
    
    cmds.setParent( '..' )

    cmds.paneLayout( configuration= "vertical4" )

    # tsl ctl fk arm left(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_arm_left", align="left", font = "boldLabelFont",  label='Arm Left' );
    cmds.text( "JUN_name_selNum_src_IK_arm_left", align="left", label='Number:0' );

    str_tls_ctl_IK_arm_left = "JUN_FKIK_Gen_ctl_IK_arm_left"

    cmds.textScrollList(str_tls_ctl_IK_arm_left, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_IK_arm_left\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_IK_arm_left}", \"JUN_name_selNum_src_IK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_IK_arm_left}", \"JUN_name_selNum_src_IK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_IK_arm_left}", \"JUN_name_selNum_src_IK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_IK_arm_left}", \"JUN_name_selNum_src_IK_arm_left\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_IK_arm_left}", \"JUN_name_selNum_src_IK_arm_left\")');

    cmds.setParent( '..' )
    # tsl ctl fk arm left(close)

    # tsl ctl fk arm right(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_arm_right", align="left", font = "boldLabelFont",  label='Arm Right' );
    cmds.text( "JUN_name_selNum_src_arm_right", align="left", label='Number:0' );

    str_tls_ctl_IK_arm_right = "JUN_FKIK_Gen_ctl_IK_arm_right"
    cmds.textScrollList(str_tls_ctl_IK_arm_right, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_IK_arm_right\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_IK_arm_right}", \"JUN_name_selNum_src_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_IK_arm_right}", \"JUN_name_selNum_src_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_IK_arm_right}", \"JUN_name_selNum_src_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_IK_arm_right}", \"JUN_name_selNum_src_arm_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_IK_arm_right}", \"JUN_name_selNum_src_arm_right\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk arm right(close)

    # tsl ctl fk leg left(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_leg_left", align="left", font = "boldLabelFont",  label='Leg Left' );
    cmds.text( "JUN_name_selNum_src_leg_left", align="left", label='Number:0' );

    str_tls_ctl_IK_leg_left = "JUN_FKIK_Gen_ctl_IK_leg_left"
    cmds.textScrollList(str_tls_ctl_IK_leg_left, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_IK_leg_left\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_IK_leg_left}", \"JUN_name_selNum_src_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_IK_leg_left}", \"JUN_name_selNum_src_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_IK_leg_left}", \"JUN_name_selNum_src_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_IK_leg_left}", \"JUN_name_selNum_src_leg_left\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_IK_leg_left}", \"JUN_name_selNum_src_leg_left\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk leg left(close)

    # tsl ctl fk leg right(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_leg_right", align="left", font = "boldLabelFont",  label='Leg right' );
    cmds.text( "JUN_name_selNum_src_leg_right", align="left", label='Number:0' );

    str_tls_ctl_IK_leg_right = "JUN_FKIK_Gen_ctl_IK_leg_right"
    cmds.textScrollList(str_tls_ctl_IK_leg_right, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_IK_leg_right\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_ctl_IK_leg_right}", \"JUN_name_selNum_src_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_ctl_IK_leg_right}", \"JUN_name_selNum_src_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_ctl_IK_leg_right}", \"JUN_name_selNum_src_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_ctl_IK_leg_right}", \"JUN_name_selNum_src_leg_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_ctl_IK_leg_right}", \"JUN_name_selNum_src_leg_right\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk leg right(close)
    
    cmds.setParent( '..' )
    #===================================================================================
    # frameLayout : Tool  Setup IK source(close)
    #===================================================================================

    cmds.setParent( '..' )

    cmds.setParent( '..' )
    #===================================================================================
    # Tab : Source (close)
    #===================================================================================
    '''
    #===================================================================================
    # Tab Start : IK to FK (drivers)
    #===================================================================================
    tab_drivers = cmds.columnLayout(adjustableColumn=True, 
                                    columnAttach=('both', 5), 
                                    rowSpacing=6, 
                                    bgc =color_mainDark, 
                                    width = 390 );
    cmds.frameLayout( label='Tool : Setup Drivers', collapsable= True, bgc =color_main )
    
    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_text_driver_IK_to_FK", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='Set Drivers : IK to FK' );
    
    cmds.setParent( '..' )

    cmds.paneLayout( configuration= "vertical4" )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_driver_IK_to_FK_arm_left", align="left", font = "boldLabelFont",  label='Arm Left' );
    cmds.text( "JUN_name_selNum_ctl_IK_to_FK_arm_left", align="left", label='Number:0' );

    str_tls_drv_IK_to_FK_arm_left = "JUN_FKIK_Gen_driver_IK_to_FK_arm_left"
    cmds.textScrollList(str_tls_drv_IK_to_FK_arm_left, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_driver_IK_to_FK_arm_left\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_IK_to_FK_arm_left}", \"JUN_name_selNum_ctl_IK_to_FK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_IK_to_FK_arm_left}", \"JUN_name_selNum_ctl_IK_to_FK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_IK_to_FK_arm_left}", \"JUN_name_selNum_ctl_IK_to_FK_arm_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_IK_to_FK_arm_left}", \"JUN_name_selNum_ctl_IK_to_FK_arm_left\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_IK_to_FK_arm_left}", \"JUN_name_selNum_ctl_IK_to_FK_arm_left\")');

    cmds.setParent( '..' )
    # tsl ctl fk arm left(close)

    # tsl ctl fk arm right(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_drivers_IK_to_FK_arm_right", align="left", font = "boldLabelFont",  label='Arm Right' );
    cmds.text( "JUN_name_selNum_drivers_IK_to_FK_arm_right", align="left", label='Number:0' );

    str_tls_drv_IK_to_FK_arm_right = "JUN_FKIK_Gen_drivers_IK_to_FK_arm_right"
    cmds.textScrollList(str_tls_drv_IK_to_FK_arm_right, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_drivers_IK_to_FK_arm_right\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_IK_to_FK_arm_right}", \"JUN_name_selNum_drivers_IK_to_FK_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_IK_to_FK_arm_right}", \"JUN_name_selNum_drivers_IK_to_FK_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_IK_to_FK_arm_right}", \"JUN_name_selNum_drivers_IK_to_FK_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_IK_to_FK_arm_right}", \"JUN_name_selNum_drivers_IK_to_FK_arm_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_drivers_IK_to_FK_arm_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_IK_to_FK_arm_right}", \"JUN_name_selNum_drivers_IK_to_FK_arm_right\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk arm right(close)

    # tsl ctl fk leg left(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_dirvers_IK_to_FK_leg_left", align="left", font = "boldLabelFont",  label='Leg Left' );
    cmds.text( "JUN_name_selNum_drivers_IK_to_FK_leg_left", align="left", label='Number:0' );

    str_tls_drv_IK_to_FK_leg_left = "JUN_FKIK_Gen_drivers_IK_to_FK_leg_left"
    cmds.textScrollList(str_tls_drv_IK_to_FK_leg_left, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_drivers_IK_to_FK_leg_left\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_IK_to_FK_leg_left}", \"JUN_name_selNum_drivers_IK_to_FK_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_IK_to_FK_leg_left}", \"JUN_name_selNum_drivers_IK_to_FK_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_IK_to_FK_leg_left}", \"JUN_name_selNum_drivers_IK_to_FK_leg_left\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_IK_to_FK_leg_left}", \"JUN_name_selNum_drivers_IK_to_FK_leg_left\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_drivers_IK_to_FK_leg_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_IK_to_FK_leg_left}", \"JUN_name_selNum_drivers_IK_to_FK_leg_left\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk leg left(close)

    # tsl ctl fk leg right(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_drivers_IK_to_FK_leg_right", align="left", font = "boldLabelFont",  label='Leg right' );
    cmds.text( "JUN_name_selNum_driver_IK_to_FK_leg_right", align="left", label='Number:0' );

    str_tls_drv_IK_to_FK_leg_right = "JUN_FKIK_Gen_ctl_driver_IK_to_FK_leg_right"
    cmds.textScrollList("JUN_FKIK_Gen_ctl_driver_IK_to_FK_leg_right", 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_ctl_driver_IK_to_FK_leg_right\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_IK_to_FK_leg_right}", \"JUN_name_selNum_driver_IK_to_FK_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_IK_to_FK_leg_right}", \"JUN_name_selNum_driver_IK_to_FK_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_IK_to_FK_leg_right}", \"JUN_name_selNum_driver_IK_to_FK_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_IK_to_FK_leg_right}", \"JUN_name_selNum_driver_IK_to_FK_leg_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_driver_IK_to_FK_leg_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_IK_to_FK_leg_right}", \"JUN_name_selNum_driver_IK_to_FK_leg_right\")');
    
    cmds.setParent( '..' )
    # tsl ctl fk leg right(close)
    
    cmds.setParent( '..' )

    # =================================================================
    # ctl IK (open)
    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_text_driver_FK_to_IK", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='Set Drivers : FK to IK' );
    
    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns=5 , columnWidth = ([1,win_width/5-10],
                                                       [2,win_width/5-10],
                                                       [3,win_width/5-10],
                                                       [4,win_width/5-10],
                                                       [5,win_width/5-10]));

    # tsl ctl Ik pole arm(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('left', 5), rowSpacing=5,  bgc =color_sub, columnWidth = win_width/5-15 );

    cmds.text( "JUN_FKIK_Gen_title_dirver_FK_to_IK_pole_arm", align="left", font = "boldLabelFont",  label='Pole Arm' );
    cmds.text( "JUN_name_selNum_dirver_FK_to_IK_pole_arm", align="left", label='Number:0' );

    str_tls_drv_FK_to_IK_pole_arm = "JUN_FKIK_Gen_driver_FK_to_IK_pole_arm"
    cmds.textScrollList(str_tls_drv_FK_to_IK_pole_arm, 
                        height = (win_height*mult_tsl_ctl_IK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_driver_FK_to_IK_pole_arm\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= mult_tsl_btn_width_01, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_FK_to_IK_pole_arm}", \"JUN_name_selNum_dirver_FK_to_IK_pole_arm\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= mult_tsl_btn_width_01, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_FK_to_IK_pole_arm}", \"JUN_name_selNum_dirver_FK_to_IK_pole_arm\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= mult_tsl_btn_width_01, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_FK_to_IK_pole_arm}", \"JUN_name_selNum_dirver_FK_to_IK_pole_arm\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= mult_tsl_btn_width_01+15, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_FK_to_IK_pole_arm}", \"JUN_name_selNum_dirver_FK_to_IK_pole_arm\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_pole_arm",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_FK_to_IK_pole_arm}", \"JUN_name_selNum_dirver_FK_to_IK_pole_arm\")');

    cmds.setParent( '..' )
    # tsl ctl Ik pole arm(close)

    # tsl ctl Ik pole leg(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('left', 5), rowSpacing=5,  bgc =color_sub, columnWidth = win_width/5-15 );
    
    cmds.text( "JUN_FKIK_Gen_title_drivers_FK_to_IK_pole_leg", align="left", font = "boldLabelFont",  label='Pole leg' );
    cmds.text( "JUN_name_selNum_driver_FK_to_IK_pole_leg", align="left", label='Number:0' );

    str_tls_drv_FK_to_IK_pole_leg = "JUN_FKIK_Gen_driver_FK_to_IK_pole_leg"
    cmds.textScrollList(str_tls_drv_FK_to_IK_pole_leg, 
                        height = (win_height*mult_tsl_ctl_IK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_driver_FK_to_IK_pole_leg\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= mult_tsl_btn_width_01, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_FK_to_IK_pole_leg}", \"JUN_name_selNum_driver_FK_to_IK_pole_leg\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= mult_tsl_btn_width_01, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_FK_to_IK_pole_leg}", \"JUN_name_selNum_driver_FK_to_IK_pole_leg\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= mult_tsl_btn_width_01, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_FK_to_IK_pole_leg}", \"JUN_name_selNum_driver_FK_to_IK_pole_leg\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= mult_tsl_btn_width_01+15, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_FK_to_IK_pole_leg}", \"JUN_name_selNum_driver_FK_to_IK_pole_leg\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_pole_leg",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_FK_to_IK_pole_leg}", \"JUN_name_selNum_driver_FK_to_IK_pole_leg\")');

    cmds.setParent( '..' )
    # tsl ctl Ik pole leg(close)

    # tsl ctl Ik Leg Ankle(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('left', 5), rowSpacing=5,  bgc =color_sub, columnWidth = win_width/5-15 );
    
    cmds.text( "JUN_FKIK_Gen_title_driver_FK_to_IK_leg_ankle", align="left", font = "boldLabelFont",  label='Leg Ankle' );
    cmds.text( "JUN_name_selNum_driver_FK_to_IK_leg_ankle", align="left", label='Number:0' );

    str_tls_drv_FK_to_IK_leg_ankle = "JUN_FKIK_Gen_driver_FK_to_IK_leg_ankle"
    cmds.textScrollList("JUN_FKIK_Gen_driver_FK_to_IK_leg_ankle", 
                        height = (win_height*mult_tsl_ctl_IK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_driver_FK_to_IK_leg_ankle\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= mult_tsl_btn_width_01, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_FK_to_IK_leg_ankle}", \"JUN_name_selNum_driver_FK_to_IK_leg_ankle\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= mult_tsl_btn_width_01, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_FK_to_IK_leg_ankle}", \"JUN_name_selNum_driver_FK_to_IK_leg_ankle\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= mult_tsl_btn_width_01, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_FK_to_IK_leg_ankle}", \"JUN_name_selNum_driver_FK_to_IK_leg_ankle\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= mult_tsl_btn_width_01+15, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_FK_to_IK_leg_ankle}", \"JUN_name_selNum_driver_FK_to_IK_leg_ankle\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_driver_FK_to_IK_leg_ankle",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_FK_to_IK_leg_ankle}", \"JUN_name_selNum_driver_FK_to_IK_leg_ankle\")');

    cmds.setParent( '..' )
    # tsl ctl Ik Leg Ankle(close)

    # tsl ctl Ik Leg Toe(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('left', 5), rowSpacing=5,  bgc =color_sub, columnWidth = win_width/5-15 );
    
    cmds.text( "JUN_FKIK_Gen_title_driver_FK_to_IK_leg_toe", align="left", font = "boldLabelFont",  label='Leg Toe' );
    cmds.text( "JUN_name_selNum_driver_FK_to_IK_leg_toe", align="left", label='Number:0' );

    str_tls_drv_FK_to_IK_leg_toe = "JUN_FKIK_Gen_driver_FK_to_IK_leg_toe"
    cmds.textScrollList(str_tls_drv_FK_to_IK_leg_toe, 
                        height = (win_height*mult_tsl_ctl_IK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_driver_FK_to_IK_leg_toe\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= mult_tsl_btn_width_01, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_FK_to_IK_leg_toe}", \"JUN_name_selNum_driver_FK_to_IK_leg_toe\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= mult_tsl_btn_width_01, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_FK_to_IK_leg_toe}", \"JUN_name_selNum_driver_FK_to_IK_leg_toe\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= mult_tsl_btn_width_01, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_FK_to_IK_leg_toe}", \"JUN_name_selNum_driver_FK_to_IK_leg_toe\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= mult_tsl_btn_width_01+15, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_FK_to_IK_leg_toe}", \"JUN_name_selNum_driver_FK_to_IK_leg_toe\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_IK_leg_toe",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_FK_to_IK_leg_toe}", \"JUN_name_selNum_driver_FK_to_IK_leg_toe\")');

    cmds.setParent( '..' )
    # tsl ctl Ik Leg Toe(close)

    # tsl ctl Ik Wrist(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('left', 5), rowSpacing=5,  bgc =color_sub, columnWidth = win_width/5-15 );
    
    cmds.text( "JUN_FKIK_Gen_title_driver_FK_to_IK_wrist", align="left", font = "boldLabelFont",  label='Wrist' );
    cmds.text( "JUN_name_selNum_driver_FK_to_IK_wrist", align="left", label='Number:0' );

    str_tls_drv_FK_to_IK_wrist = "JUN_FKIK_Gen_driver_FK_to_IK_wrist"
    cmds.textScrollList(str_tls_drv_FK_to_IK_wrist, 
                        height = (win_height*mult_tsl_ctl_IK_hight),
                        width = win_width/5-15,
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_Gen_driver_FK_to_IK_wrist\")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= mult_tsl_btn_width_01, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_drv_FK_to_IK_wrist}", \"JUN_name_selNum_driver_FK_to_IK_wrist\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= mult_tsl_btn_width_01, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_drv_FK_to_IK_wrist}", \"JUN_name_selNum_driver_FK_to_IK_wrist\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= mult_tsl_btn_width_01, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_drv_FK_to_IK_wrist}", \"JUN_name_selNum_driver_FK_to_IK_wrist\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= mult_tsl_btn_width_01+15, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_drv_FK_to_IK_wrist}", \"JUN_name_selNum_driver_FK_to_IK_wrist\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_IK_wrist",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_drv_FK_to_IK_wrist}", \"JUN_name_selNum_driver_FK_to_IK_wrist\")');

    cmds.setParent( '..' )
    # tsl ctl Ik Wrist(close)

    cmds.setParent( '..' )

    cmds.setParent( '..' )

    cmds.setParent( '..' )


    '''
    #===================================================================================
    # Tab End : drivers
    #===================================================================================

    #===================================================================================
    # Tab Start : Matcher FK
    #===================================================================================
    tab_matcher_FK = cmds.columnLayout(adjustableColumn=True, 
                                    columnAttach=('both', 5), 
                                    rowSpacing=6, 
                                    bgc =color_mainDark, 
                                    width = 390 );
    cmds.frameLayout( label='Match FK', collapsable= True, bgc =color_main )

    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_text_match", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='match FK : Arm' );
    
    cmds.setParent( '..' )

    #===================================================================================
    # match ctl to pose objs : arm(close)

    cmds.paneLayout( configuration= "vertical4" )

    mult_tsl_ctl_FK_hight = 0.09

    # tsl match arm left pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text(align="left", font = "boldLabelFont",  label='Arm Left pose obj' );
    cmds.text("JUN_name_selNum_arm_left_pose_objs", align="left", label='Number:0' );

    str_tls_match_FK_arm_left_pose_objs = "JUN_FKIK_Gen_match_IK_to_FK_arm_left_pose_obj"

    cmds.textScrollList(str_tls_match_FK_arm_left_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_arm_left_pose_objs}")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\")');

    cmds.setParent( '..' )
    # tsl match arm left pose objs(close)

    # tsl match arm left ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_arm_right", align="left", font = "boldLabelFont",  label='Arm Left ctl' );
    cmds.text( "JUN_name_selNum_match_arm_left_ctl", align="left", label='Number:0' );

    str_tls_match_FK_arm_left_ctl = "JUN_FKIK_Gen_match_IK_to_FK_arm_left_ctl"
    cmds.textScrollList(str_tls_match_FK_arm_left_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_arm_left_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\")');
    
    cmds.setParent( '..' )
    # tsl match arm left ctl(close)

    # tsl match arm right pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Arm right pose objs' );
    cmds.text( "JUN_name_selNum_ctl_arm_right", align="left", label='Number:0' );

    str_tls_match_FK_arm_right_pose_objs = "JUN_FKIK_Gen_match_IK_to_FK_arm_right_pose_objs"
    cmds.textScrollList(str_tls_match_FK_arm_right_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_arm_right_pose_objs}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\")');
    
    cmds.setParent( '..' )
    # tsl match arm right pose objs(close)

    # tsl ctl arm right ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Arm right ctl' );
    cmds.text( "JUN_name_selNum_ctl_arm_right", align="left", label='Number:0' );

    str_tls_match_FK_arm_right_ctl= "JUN_FKIK_Gen_match_IK_to_FK_arm_right_ctl"
    cmds.textScrollList(str_tls_match_FK_arm_right_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_arm_right_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\")');
    
    cmds.setParent( '..' )
    
    cmds.setParent( '..' )

    # match ctl to pose objs : arm(close)
    #===================================================================================

    cmds.rowLayout( numberOfColumns=1 );

    cmds.text(height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='match FK : Leg' );
    
    cmds.setParent( '..' )

    #===================================================================================
    # match ctl to pose objs : leg (open)
    cmds.paneLayout( configuration= "vertical4" )

    # mult_tsl_ctl_FK_hight = 0.09

    # tsl match leg left pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text(align="left", font = "boldLabelFont",  label='Leg Left pose obj' );
    cmds.text("JUN_name_selNum_leg_left_pose_objs", align="left", label='Number:0' );

    str_tls_match_FK_leg_left_pose_objs = "JUN_FKIK_Gen_match_IK_to_FK_leg_left_pose_obj"

    cmds.textScrollList(str_tls_match_FK_leg_left_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_leg_left_pose_objs}")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );

    cmds.setParent( '..' )

    cmds.button( label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\")');

    cmds.setParent( '..' )
    # tsl match leg left pose objs(close)

    # tsl match leg left ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Leg Left ctl' );
    cmds.text( "JUN_name_selNum_match_leg_left_ctl", align="left", label='Number:0' );

    str_tls_match_FK_leg_left_ctl = "JUN_FKIK_Gen_match_IK_to_FK_leg_left_ctl"
    cmds.textScrollList(str_tls_match_FK_leg_left_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_leg_left_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\")');
    
    cmds.setParent( '..' )
    # tsl match leg left ctl(close)

    # tsl match leg right pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Leg right pose objs' );
    cmds.text( "JUN_name_selNum_pos_leg_right", align="left", label='Number:0' );

    str_tls_match_FK_leg_right_pose_objs = "JUN_FKIK_Gen_match_IK_to_FK_leg_right_pose_objs"
    cmds.textScrollList(str_tls_match_FK_leg_right_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_leg_right_pose_objs}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\")');
    
    cmds.setParent( '..' )
    # tsl match leg right pose objs(close)

    # tsl match leg right ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_leg_right", align="left", font = "boldLabelFont",  label='Leg right ctl' );
    cmds.text( "JUN_name_selNum_ctl_leg_right", align="left", label='Number:0' );

    str_tls_match_FK_leg_right_ctl= "JUN_FKIK_Gen_match_IK_to_FK_leg_right_ctl"
    cmds.textScrollList(str_tls_match_FK_leg_right_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_FK_leg_right_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_FK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_FK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_FK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_FK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_FK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\")');
    
    cmds.setParent( '..' )
    # tsl match leg right ctl(close)
    
    cmds.setParent( '..' )
    # match ctl to pose objs : leg (open)
    #===================================================================================

    cmds.setParent( '..' )

    cmds.setParent( '..' )
    #===================================================================================
    # Tab End : Matcher FK
    #===================================================================================

    #===================================================================================
    # Tab Start : Matcher IK
    #===================================================================================

    tab_matcher_IK = cmds.columnLayout(adjustableColumn=True, 
                                    columnAttach=('both', 5), 
                                    rowSpacing=6, 
                                    bgc =color_mainDark, 
                                    width = 390 );
    cmds.frameLayout( label='Match IK', collapsable= True, bgc =color_main )

    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_text_match", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='match IK : Arm' );
    
    cmds.setParent( '..' )

    #===================================================================================
    # match ctl to pose objs : arm(close)

    cmds.paneLayout( configuration= "vertical4" )

    mult_tsl_ctl_FK_hight = 0.09

    # tsl match arm left pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text(align="left", font = "boldLabelFont",  label='Arm Left pose obj' );
    cmds.text("JUN_name_selNum_arm_left_pose_objs", align="left", label='Number:0' );

    str_tls_match_IK_arm_left_pose_objs = "JUN_FKIK_Gen_match_FK_to_IK_arm_left_pose_obj"

    cmds.textScrollList(str_tls_match_IK_arm_left_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_arm_left_pose_objs}")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\" )' );

    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_arm_left_pose_objs}", \"JUN_name_selNum_arm_left_pose_objs\")');

    cmds.setParent( '..' )
    # tsl match arm left pose objs(close)

    # tsl match arm left ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_arm_right", align="left", font = "boldLabelFont",  label='Arm Left ctl' );
    cmds.text( "JUN_name_selNum_match_arm_left_ctl", align="left", label='Number:0' );

    str_tls_match_IK_arm_left_ctl = "JUN_FKIK_Gen_match_FK_to_IK_arm_left_ctl"
    cmds.textScrollList(str_tls_match_IK_arm_left_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_arm_left_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_arm_left_ctl}", \"JUN_name_selNum_match_arm_left_ctl\")');
    
    cmds.setParent( '..' )
    # tsl match arm left ctl(close)

    # tsl match arm right pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Arm right pose objs' );
    cmds.text( "JUN_name_selNum_ctl_arm_right", align="left", label='Number:0' );

    str_tls_match_IK_arm_right_pose_objs = "JUN_FKIK_Gen_match_FK_to_IK_arm_right_pose_objs"
    cmds.textScrollList(str_tls_match_IK_arm_right_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_arm_right_pose_objs}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_arm_right_pose_objs}", \"JUN_name_selNum_ctl_arm_right\")');
    
    cmds.setParent( '..' )
    # tsl match arm right pose objs(close)

    # tsl ctl arm right ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Arm right ctl' );
    cmds.text( "JUN_name_selNum_ctl_arm_right", align="left", label='Number:0' );

    str_tls_match_IK_arm_right_ctl= "JUN_FKIK_Gen_match_FK_to_IK_arm_right_ctl"
    cmds.textScrollList(str_tls_match_IK_arm_right_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_arm_right_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_arm_right_ctl}", \"JUN_name_selNum_ctl_arm_right\")');
    
    cmds.setParent( '..' )
    
    cmds.setParent( '..' )

    # match ctl to pose objs : arm(close)
    #===================================================================================

    cmds.rowLayout( numberOfColumns=1 );

    cmds.text(height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='match IK : Leg' );
    
    cmds.setParent( '..' )

    #===================================================================================
    # match ctl to pose objs : leg (open)
    cmds.paneLayout( configuration= "vertical4" )

    # mult_tsl_ctl_FK_hight = 0.09

    # tsl match leg left pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text(align="left", font = "boldLabelFont",  label='Leg Left pose obj' );
    cmds.text("JUN_name_selNum_leg_left_pose_objs", align="left", label='Number:0' );

    str_tls_match_IK_leg_left_pose_objs = "JUN_FKIK_Gen_match_FK_to_IK_leg_left_pose_obj"

    cmds.textScrollList(str_tls_match_IK_leg_left_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_leg_left_pose_objs}")');

    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\" )' );

    cmds.setParent( '..' )

    cmds.button( label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_leg_left_pose_objs}", \"JUN_name_selNum_leg_left_pose_objs\")');

    cmds.setParent( '..' )
    # tsl match leg left pose objs(close)

    # tsl match leg left ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Leg Left ctl' );
    cmds.text( "JUN_name_selNum_match_leg_left_ctl", align="left", label='Number:0' );

    str_tls_match_IK_leg_left_ctl = "JUN_FKIK_Gen_match_FK_to_IK_leg_left_ctl"
    cmds.textScrollList(str_tls_match_IK_leg_left_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_leg_left_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_arm_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_leg_left_ctl}", \"JUN_name_selNum_match_leg_left_ctl\")');
    
    cmds.setParent( '..' )
    # tsl match leg left ctl(close)

    # tsl match leg right pose objs(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( align="left", font = "boldLabelFont",  label='Leg right pose objs' );
    cmds.text( "JUN_name_selNum_pos_leg_right", align="left", label='Number:0' );

    str_tls_match_IK_leg_right_pose_objs = "JUN_FKIK_Gen_match_FK_to_IK_leg_right_pose_objs"
    cmds.textScrollList(str_tls_match_IK_leg_right_pose_objs, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_leg_right_pose_objs}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_left",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_leg_right_pose_objs}", \"JUN_name_selNum_pos_leg_right\")');
    
    cmds.setParent( '..' )
    # tsl match leg right pose objs(close)

    # tsl match leg right ctl(open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_Gen_title_ctl_leg_right", align="left", font = "boldLabelFont",  label='Leg right ctl' );
    cmds.text( "JUN_name_selNum_ctl_leg_right", align="left", label='Number:0' );

    str_tls_match_IK_leg_right_ctl= "JUN_FKIK_Gen_match_FK_to_IK_leg_right_ctl"
    cmds.textScrollList(str_tls_match_IK_leg_right_ctl, 
                        height = (win_height*mult_tsl_ctl_FK_hight),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand=f'JUN_cmd_tsl_select("{str_tls_match_IK_leg_right_ctl}")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command=f'CMD_ToolSel_b_add  ( "{str_tls_match_IK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command=f'CMD_ToolSel_b_del  ( "{str_tls_match_IK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command=f'CMD_ToolSel_b_up   ( "{str_tls_match_IK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command=f'CMD_ToolSel_b_down ( "{str_tls_match_IK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_FK_IK_Gen_ctl_fk_leg_right",
                 label='Select Objects',
                 bgc =color_btn,
                 command=f'JUN_cmd_FKIK_gen_toolSel_btn("{str_tls_match_IK_leg_right_ctl}", \"JUN_name_selNum_ctl_leg_right\")');
    
    cmds.setParent( '..' )
    # tsl match leg right ctl(close)
    
    cmds.setParent( '..' )
    # match ctl to pose objs : leg (open)
    #===================================================================================

    cmds.setParent( '..' )

    cmds.setParent( '..' )
    #===================================================================================
    # Tab End : Matcher IK
    #===================================================================================



    cmds.setParent( '..' )
    #===================================================================================
    #===================================================================================
    # Tab All (close)
    #===================================================================================
    #===================================================================================

    cmds.tabLayout( tab_all, edit=True, tabLabel=((tab_source, 'Source'), (tab_matcher_FK, 'Match FK'), (tab_matcher_IK, 'Match IK')));
    
    cmds.frameLayout( label=' Option', collapsable= True, bgc =color_main);

    
    cmds.paneLayout( configuration= "vertical2", paneSize = ([1,35,100],[2,65,100]) )

    str_name_FKIK_gen_arm_l_cbg = "JUN_name_FKIK_arm_l_cbg"
    str_name_FKIK_gen_arm_r_cbg = "JUN_name_FKIK_arm_r_cbg"
    str_name_FKIK_gen_leg_l_cbg = "JUN_name_FKIK_leg_l_cbg"
    str_name_FKIK_gen_leg_r_cbg = "JUN_name_FKIK_leg_r_cbg"

   

    lst_tsl_source_FK = [ str_tls_ctl_FK_arm_left,
                          str_tls_ctl_FK_arm_right,
                          str_tls_ctl_FK_leg_left,
                          str_tls_ctl_FK_leg_right]
                    
    lst_tsl_source_IK = [ str_tls_ctl_IK_arm_left,
                          str_tls_ctl_IK_arm_right,
                          str_tls_ctl_IK_leg_left,
                          str_tls_ctl_IK_leg_right]
    
    lst_tsl_match_FK_all = [str_tls_match_FK_arm_left_pose_objs,
                            str_tls_match_FK_arm_left_ctl,
                            str_tls_match_FK_arm_right_pose_objs,
                            str_tls_match_FK_arm_right_ctl,
                            str_tls_match_FK_leg_left_pose_objs,
                            str_tls_match_FK_leg_left_ctl,
                            str_tls_match_FK_leg_right_pose_objs,
                            str_tls_match_FK_leg_right_ctl]


    lst_tsl_match_FK_ctl = [str_tls_match_FK_arm_left_ctl,
                            str_tls_match_FK_arm_right_ctl,
                            str_tls_match_FK_leg_left_ctl,
                            str_tls_match_FK_leg_right_ctl]
    
    lst_tsl_match_FK_pose_objs = [str_tls_match_FK_arm_left_pose_objs,
                                  str_tls_match_FK_arm_right_pose_objs,
                                  str_tls_match_FK_leg_left_pose_objs,
                                  str_tls_match_FK_leg_right_pose_objs]
    
    lst_tsl_match_IK_all = [str_tls_match_IK_arm_left_pose_objs,
                            str_tls_match_IK_arm_left_ctl,
                            str_tls_match_IK_arm_right_pose_objs,
                            str_tls_match_IK_arm_right_ctl,
                            str_tls_match_IK_leg_left_pose_objs,
                            str_tls_match_IK_leg_left_ctl,
                            str_tls_match_IK_leg_right_pose_objs,
                            str_tls_match_IK_leg_right_ctl]
    
    lst_tsl_match_IK_ctl = [str_tls_match_IK_arm_left_ctl,
                            str_tls_match_IK_arm_right_ctl,
                            str_tls_match_IK_leg_left_ctl,
                            str_tls_match_IK_leg_right_ctl]
    
    lst_tsl_match_IK_pose_objs = [str_tls_match_IK_arm_left_pose_objs,
                            str_tls_match_IK_arm_right_pose_objs,
                            str_tls_match_IK_leg_left_pose_objs,
                            str_tls_match_IK_leg_right_pose_objs]
                            
    lst_cbx_match = [str_name_FKIK_gen_arm_l_cbg,
                     str_name_FKIK_gen_arm_r_cbg,
                     str_name_FKIK_gen_leg_l_cbg,
                     str_name_FKIK_gen_leg_r_cbg]
    
    cage_glo = JUN_cage_FKIK_Gen()

    #==============================================================================
    # buttons for setup pose objects (open)

    cmds.rowColumnLayout( numberOfColumns=2)

    
    cmds.button( "name_btn_setup_triangle_pose_objects", 
                 label='Set up triangle drivers', 
                 bgc=color_btn, 
                 h = win_height/15,
                 command=lambda *argv : JUN_cmd_FKIK_gen_setup_triangle_pos_objs(lst_tsl_source_FK, cage_glo));
    
    cmds.button( "name_btn_create_pose_objects", 
                 label='Drivers for FK IK switch', 
                 bgc=color_btn, 
                 h = win_height/15,
                 command=lambda *argv : JUN_cmd_FKIK_gen_create_pos_objs_FKIK_Gen(lst_tsl_source_FK, 
                                                                                  lst_tsl_source_IK,
                                                                                  lst_tsl_match_FK_ctl, 
                                                                                  lst_tsl_match_IK_ctl, 
                                                                                  lst_tsl_match_FK_pose_objs,
                                                                                  lst_tsl_match_IK_pose_objs, 
                                                                                  cage_glo));
    
    cmds.button( "name_btn_constraint_pose_objects", 
                 label='Load setting', 
                 bgc=color_btn, 
                 h = win_height/15,
                 command=lambda *argv : JUN_cmd_FKIK_gen_load_setting());

    cmds.button( "name_btn_setup_all_pose_objects", 
                 label='Save setting', 
                 bgc=color_btn, 
                 h = win_height/15,
                 command=lambda *argv : JUN_cmd_FKIK_gen_save_setting(lst_tsl_match_FK_all, lst_tsl_match_IK_all));
    
    cmds.setParent( '..' )
    
    # buttons for setup pose objects (close)
    #==============================================================================

    cmds.rowColumnLayout( numberOfColumns=1)
    #===================================================================================
    # paneLayout for check box : vertical2(open)

    cmds.paneLayout( configuration= "vertical2" )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_name_checkBoxGrp_Arm", align="left", font = "boldLabelFont",  label='Arm' );

    cmds.checkBoxGrp( str_name_FKIK_gen_arm_l_cbg, label='Arm Left', width=180 ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    cmds.checkBoxGrp( str_name_FKIK_gen_arm_r_cbg, label='Arm Right', width=180 ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );

    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_name_checkBoxGrp_Leg", align="left", font = "boldLabelFont",  label='Leg' );

    cmds.checkBoxGrp( str_name_FKIK_gen_leg_l_cbg, label='Leg Left', width=180 ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    cmds.checkBoxGrp( str_name_FKIK_gen_leg_r_cbg, label='Leg Right', width=180 ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    
    cmds.setParent( '..' )

    cmds.setParent( '..' )

    # paneLayout for check box : vertical2(close)
    #==============================================================================

    #==============================================================================
    # intFieldGrp for strat end frame (open)


    cmds.rowColumnLayout( numberOfColumns=1)

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    FKIK_time_str = int(cmds.playbackOptions(query=True, minTime=True));
    FKIK_time_end = int(cmds.playbackOptions(query=True, maxTime=True));

    cmds.intFieldGrp( 'name_FKIK_gen_ifg_timeStr', 
                        columnAlign = [1, 'left'], 
                        width = 390, 
                        columnWidth2 = [100,160],
                        value1 = FKIK_time_str,
                        label="Start Frame :"    );    
    
    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.intFieldGrp( 'name_FKIK_gen_ifg_timeEnd', 
                        columnAlign= [1, 'left'], 
                        width = 390, 
                        columnWidth2 = [100,160],
                        value1 = FKIK_time_end,
                        label="End Frame :"  );  

    cmds.setParent( '..' )

    cmds.setParent( '..' )


    # intFieldGrp for strat end frame (close)
    #==============================================================================

    
    cmds.setParent( '..' )
    
    cmds.setParent( '..' )

    cmds.setParent( '..' )

    #==============================================================================
    # tls for pose objects, ctl (open)
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5, bgc = color_main, h = win_height/6 );

 
    #==============================================================================
    # buttons for match (open)

    cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]) )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5, bgc = color_main );


    cmds.text( height = 20 , align="left", font = "boldLabelFont",  label='Match' );

    cmds.button( "name_btn_match_IK_to_FK", 
                 h = win_height/20,
                 label='Match IK', 
                 bgc=color_btn, 
                 command='JUN_cmd_match_IK_and_FK(\"JUN_FKIK_gen_targetsPos_tsl\", \"JUN_FKIK_gen_followersCtl_tsl\",\"JUN_name_FKIK_arm_l_cbg\",\"JUN_name_FKIK_arm_r_cbg\", \"JUN_name_FKIK_leg_l_cbg\",\"JUN_name_FKIK_leg_r_cbg\", 1)');

    cmds.button( "name_btn_match_FK_to_IK", 
                 h = win_height/20,
                 label='Match FK', 
                 bgc=color_btn, 
                 command='JUN_cmd_match_IK_and_FK(\"JUN_FKIK_gen_targetsPos_tsl\", \"JUN_FKIK_gen_followersCtl_tsl\",\"JUN_name_FKIK_arm_l_cbg\",\"JUN_name_FKIK_arm_r_cbg\", \"JUN_name_FKIK_leg_l_cbg\",\"JUN_name_FKIK_leg_r_cbg\", 0)');

    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5, bgc = color_main );

    cmds.text( height = 20 , align="left", font = "boldLabelFont",  label='Bake' );

    cmds.button( "name_btn_bake_IK", 
                 h = win_height/20,
                 label='Bake IK', 
                 bgc=color_btn, 
                 command=f'JUN_cmd_bake_IK_FK_Gen({lst_tsl_match_IK_all}, {lst_tsl_match_FK_all}, {lst_cbx_match}, 1, \"name_FKIK_gen_ifg_timeStr\", \"name_FKIK_gen_ifg_timeEnd\")');

    cmds.button( "name_btn_bake_FK", 
                 h = win_height/20,
                 label='Bake FK', 
                 bgc=color_btn, 
                 command=f'JUN_cmd_bake_IK_FK_Gen({lst_tsl_match_IK_all}, {lst_tsl_match_FK_all}, {lst_cbx_match} ,0, \"name_FKIK_gen_ifg_timeStr\", \"name_FKIK_gen_ifg_timeEnd\")');

    cmds.setParent( '..' )


    cmds.setParent( '..' )
    # buttons for match (close)
    #==============================================================================

    cmds.setParent( '..' )

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_FKIK_Tool_V02_01():
    PY_JUN_makeUI_general_FKIKTool();

PY_JUN_makeUI_general_FKIKTool();