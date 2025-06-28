# last Update date 25 03 15
# Python Script by Ji Hun Park

# FKIK Tool V02.01

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

#===================================================================================
# start (JUN_cmd_FKIKTool_setup_btn)

def JUN_cmd_FKIKTool_setup_btn(name_rig_name_tsl, text_state, targetsPos_tsl, followersCtl_tsl):

    str_token_BlendFKIKPos_grp = "BlendFKIKPos_grp";

# tgt pos ik

    str_token_pos_r_legPole_fol = "r_LegPole_xx_pos";
    str_token_pos_l_legPole_fol = "l_LegPole_xx_pos";
    str_token_pos_r_armPole_fol = "r_ArmPole_xx_pos";
    str_token_pos_l_armPole_fol = "l_ArmPole_xx_pos";

    str_token_pos_r_foot = "r_LegIkPos_xx_pos";
    str_token_pos_r_Toe = "r_LegToeIkPos_xx_pos";
    str_token_pos_l_foot = "l_LegIkPos_xx_pos";
    str_token_pos_l_Toe = "l_LegToeIkPos_xx_pos";
    str_token_pos_l_hand = "r_ArmIkPos_xx_pos";
    str_token_pos_r_hand = "l_ArmIkPos_xx_pos";

    str_list_tgt_pos_token_ik = [str_token_pos_r_legPole_fol,
                                 str_token_pos_l_legPole_fol,
                                 str_token_pos_r_armPole_fol,
                                 str_token_pos_l_armPole_fol,
                                 str_token_pos_r_foot,
                                 str_token_pos_r_Toe,
                                 str_token_pos_l_foot,
                                 str_token_pos_l_Toe,
                                 str_token_pos_l_hand,
                                 str_token_pos_r_hand]

# tgt pos fk

    str_token_pos_l_arm_fk_up = "l_ArmUpIK_xx_pos"
    str_token_pos_l_arm_fk_low = "l_ArmLowIK_xx_pos"
    str_token_pos_l_arm_fk_hand = "l_HandIK_xx_pos"

    str_token_pos_r_arm_fk_up = "r_ArmUpIK_xx_pos"
    str_token_pos_r_arm_fk_low = "r_ArmLowIK_xx_pos"
    str_token_pos_r_arm_fk_hand = "r_HandIK_xx_pos"

    str_token_pos_r_lef_fk_up = "l_LegUpIK_xx_pos"
    str_token_pos_r_lef_fk_low = "l_LegLowIK_xx_pos"
    str_token_pos_r_lef_fk_ankle = "l_LegAnkleIK_xx_pos"
    str_token_pos_r_lef_fk_ball = "l_LegFootBallIK_xx_pos"

    str_token_pos_l_lef_fk_up = "r_LegUpIK_xx_pos"
    str_token_pos_l_lef_fk_low = "r_LegLowIK_xx_pos"
    str_token_pos_l_lef_fk_ankle = "r_LegAnkleIK_xx_pos"
    str_token_pos_l_lef_fk_ball = "r_LegFootBallIK_xx_pos"

    str_list_tgt_pos_token_fk = [str_token_pos_l_arm_fk_up,
                                 str_token_pos_l_arm_fk_low,
                                 str_token_pos_l_arm_fk_hand,
                                 str_token_pos_r_arm_fk_up,
                                 str_token_pos_r_arm_fk_low,
                                 str_token_pos_r_arm_fk_hand,
                                 str_token_pos_r_lef_fk_up,
                                 str_token_pos_r_lef_fk_low,
                                 str_token_pos_r_lef_fk_ankle,
                                 str_token_pos_r_lef_fk_ball,
                                 str_token_pos_l_lef_fk_up,
                                 str_token_pos_l_lef_fk_low,
                                 str_token_pos_l_lef_fk_ankle,
                                 str_token_pos_l_lef_fk_ball]

# ik ctl

    str_token_ctl_r_legPole = "r_LegPole_xx_ctl"
    str_token_ctl_l_legPole = "l_LegPole_xx_ctl"
    str_token_ctl_r_armPole = "r_ArmPole_xx_ctl"
    str_token_ctl_l_armPole = "l_ArmPole_xx_ctl"

    str_token_ctl_r_foot_ik = "r_foot_xx_ctl"
    str_token_ctl_r_toe_ik = "r_toe_xx_ctl"
    str_token_ctl_l_foot_ik = "l_foot_xx_ctl"
    str_token_ctl_l_toe_ik = "l_toe_xx_ctl"
    str_token_ctl_l_hand_ik = "r_ArmIK_xx_ctl"
    str_token_ctl_r_hand_ik = "l_ArmIK_xx_ctl"

    str_list_ctl_ik_token = [str_token_ctl_r_legPole,
                             str_token_ctl_l_legPole,
                             str_token_ctl_r_armPole,
                             str_token_ctl_l_armPole,
                             str_token_ctl_r_foot_ik,
                             str_token_ctl_r_toe_ik,
                             str_token_ctl_l_foot_ik,
                             str_token_ctl_l_toe_ik,
                             str_token_ctl_l_hand_ik,
                             str_token_ctl_r_hand_ik]

# fk ctl

    str_token_ctl_l_arm_fk_up = "l_UpperArm_xx_ctl"
    str_token_ctl_l_arm_fk_low = "l_LowerArm_xx_ctl"
    str_token_ctl_l_arm_fk_hand = "l_WristFK_xx_ctl"

    str_token_ctl_r_arm_fk_up = "r_UpperArm_xx_ctl"
    str_token_ctl_r_arm_fk_low = "r_LowerArm_xx_ctl"
    str_token_ctl_r_arm_fk_hand = "r_WristFK_xx_ctl"

    str_token_ctl_r_lef_fk_up = "l_UpperLegFK_xx_ctl"
    str_token_ctl_r_lef_fk_low = "l_LowerLegFK_xx_ctl"
    str_token_ctl_r_lef_fk_ankle = "l_ankleFK_xx_ctl"
    str_token_ctl_r_lef_fk_ball = "l_FootFK_xx_ctl"

    str_token_ctl_l_lef_fk_up = "r_UpperLegFK_xx_ctl"
    str_token_ctl_l_lef_fk_low = "r_LowerLegFK_xx_ctl"
    str_token_ctl_l_lef_fk_ankle = "r_ankleFK_xx_ctl"
    str_token_ctl_l_lef_fk_ball = "r_FootFK_xx_ctl"

    str_list_ctl_fk_token = [str_token_ctl_l_arm_fk_up,
                             str_token_ctl_l_arm_fk_low,
                             str_token_ctl_l_arm_fk_hand,
                             str_token_ctl_r_arm_fk_up,
                             str_token_ctl_r_arm_fk_low,
                             str_token_ctl_r_arm_fk_hand,
                             str_token_ctl_r_lef_fk_up,
                             str_token_ctl_r_lef_fk_low,
                             str_token_ctl_r_lef_fk_ankle,
                             str_token_ctl_r_lef_fk_ball,
                             str_token_ctl_l_lef_fk_up,
                             str_token_ctl_l_lef_fk_low,
                             str_token_ctl_l_lef_fk_ankle,
                             str_token_ctl_l_lef_fk_ball];

    str_list_tgt_pos_token_all = []
    str_list_ctl_token_all = []

    num_pos = 24

    str_list_tgt_pos_token_all.extend(str_list_tgt_pos_token_ik)
    str_list_tgt_pos_token_all.extend(str_list_tgt_pos_token_fk)

    str_list_ctl_token_all.extend(str_list_ctl_ik_token)
    str_list_ctl_token_all.extend(str_list_ctl_fk_token)

    str_selList = cmds.ls ( sl=True, fl=True );

# get BlendFKIKPos_grp's 8 objects 

    str_fkik_objChild = set();
    cmds.textScrollList( name_rig_name_tsl, e=True, removeAll=True );
    for str_selItem in str_selList :
        cmds.textScrollList( name_rig_name_tsl, e=True, append = str_selItem );

    str_fkik_objChild = BF_SELECTION_makeList_hierarchy(str_selList, 1, 1);

    #print(str_selList);

    str_BlendFKIKPos_grp = [];
    for str_fkik_obj in str_fkik_objChild :
        if str_token_BlendFKIKPos_grp in str_fkik_obj :
            str_BlendFKIKPos_grp.append(str_fkik_obj);
            break

    if len(str_BlendFKIKPos_grp) ==0 :
        cmds.text(text_state, e=True, bgc = [1, 0, 0], label= 'State : Fail to find objects for setup');
        return 0;
    
    str_fkik_objsPos = BF_SELECTION_makeList_hierarchy(str_BlendFKIKPos_grp, 1, 1);
    
    str_set_posAll = set(JUN_get_list_by_shapes(str_fkik_objsPos, ["follicle", "locator"]))
    
    if len(str_set_posAll) != num_pos:
        cmds.text(text_state, e=True, bgc = [1, 0, 0], label= 'State : Fail. Number of objects error');
        return 0;

# get 24 controlers

    str_list_ctlsAll = JUN_get_list_by_shapes(str_fkik_objChild, ['nurbsCurve'])  
    str_list_ctlsIK = JUN_get_set_by_token(str_list_ctlsAll, str_list_ctl_token_all);

    print(str_list_ctlsIK)

    if len(str_list_ctlsIK) != num_pos:
        cmds.text(text_state, e=True, bgc = [1, 0, 0], label= 'State : Fail. Number of controlers error');
        return 0;

# Update textScrollList : Targets, Followers
  
    str_list_pos = JUN_get_list_ordered_by_token(str_set_posAll, str_list_tgt_pos_token_all)
    str_list_ctl = JUN_get_list_ordered_by_token(str_list_ctlsIK, str_list_ctl_token_all)

    print(str_list_pos)

    cmds.textScrollList( targetsPos_tsl, e=True, removeAll=True );
    cmds.textScrollList( targetsPos_tsl, e=True, append = str_list_pos );

    cmds.textScrollList( followersCtl_tsl, e=True, removeAll=True );
    cmds.textScrollList( followersCtl_tsl, e=True, append = str_list_ctl );

    cmds.text(text_state, e=True, backgroundColor = [0, 1, 0], label= 'State : Sucess');


# end (JUN_cmd_FKIKTool_setup_btn)
#===================================================================================


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
        
    


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_FKIKTool ():
    str_winTitle = "FKIK Tool";
    str_winName = "Junny_win_FKIK_Tool";
    win_width = 480;
    win_height = 800;

    # color_mainDark = [0.652, 0.363, 0.363];
    color_mainDark = [0.65, 0.4, 0.4];
    color_main = [0.824, 0.457, 0.039];
    color_sub = [0.937, 0.597, 0.488];
    color_btn = [1.0, 0.8, 0.7];
    color_back = [1.0, 0.761, 0.6289];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="FKIK Tool V02" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 15-MAR-2025\')".format(color_main)

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
    # frameLayout : Tool  Setup FK to IK(open)
    #===================================================================================
    
    cmds.frameLayout( label='Tool : Setup FK to IK', collapsable= True, bgc =color_main );

    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    # 

    #rowLayout : Select Rig (close)
    cmds.rowLayout( numberOfColumns=2 );


    cmds.textScrollList("JUN_name_rig_name_tsl", 
                        height = (60),
                        numberOfRows=1, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_name_rig_name_tsl\")');

    cmds.button( "name_btn_setup_rig_name",
                 label='Select Objects',
                 bgc =color_btn,
                 command='JUN_cmd_FKIKTool_setup_btn(\"JUN_name_rig_name_tsl\", \"JUN_text_state\", \"JUN_FKIK_targetsPos_tsl\", \"JUN_FKIK_followersCtl_tsl\")');

    #rowLayout : Select Rig (close)
    cmds.setParent( '..' )


    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_text_state", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='State : Searching...' );
    
    cmds.setParent( '..' )
    #cmds.rowLayout( numberOfColumns=1 );

    # paneLayout : vertical2(open)                                                      
    
    cmds.paneLayout( configuration= "vertical2" )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_name_checkBoxGrp_Arm", align="left", font = "boldLabelFont",  label='Arm' );

    cmds.checkBoxGrp( "JUN_name_FKIK_arm_l_cbg", label='Arm Left', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    cmds.checkBoxGrp( "JUN_name_FKIK_arm_r_cbg", label='Arm Right', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    #cmds.checkBoxGrp( "JUN_name_FKIK_arm_pole_left_cbg", label='Pole Left', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    #cmds.checkBoxGrp( "JUN_name_FKIK_arm_pole_right_cbg", label='Pole Right', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );

    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_name_checkBoxGrp_Leg", align="left", font = "boldLabelFont",  label='Leg' );

    cmds.checkBoxGrp( "JUN_name_FKIK_leg_l_cbg", label='Leg Left', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    cmds.checkBoxGrp( "JUN_name_FKIK_leg_r_cbg", label='Leg Right', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    #cmds.checkBoxGrp( "JUN_name_FKIK_leg_pole_left_cbg", label='Pole Left', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    #cmds.checkBoxGrp( "JUN_name_FKIK_leg_pole_right_cbg", label='Pole Right', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = True );
    
    # columnLayout : Select Base (close)                                         
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    cmds.setParent( '..' )
    # paneLayout : vertical2(close)                                                     
    #==============================================================================
    #------------------------------------------------------------------
    # columnLayout : Select Targets (open)                                             

    cmds.paneLayout( configuration= "vertical2" )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_pos", align="left", font = "boldLabelFont",  label='Targets' );
    
    cmds.textScrollList("JUN_FKIK_targetsPos_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_targetsPos_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_FKIK_targetsPos_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_FKIK_targetsPos_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_FKIK_targetsPos_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_FKIK_targetsPos_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );

    cmds.setParent( '..' )

    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_FKIK_followers", align="left", font = "boldLabelFont",  label='Followers' );

    cmds.textScrollList("JUN_FKIK_followersCtl_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_FKIK_followersCtl_tsl\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_FKIK_followersCtl_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_FKIK_followersCtl_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_FKIK_followersCtl_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_FKIK_followersCtl_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );


    cmds.setParent( '..' )
    
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

    cmds.frameLayout( label=' Tool : Match IK and FK', collapsable= True, bgc =color_main );

    FKIK_time_str = int(cmds.playbackOptions(query=True, minTime=True));
    FKIK_time_end = int(cmds.playbackOptions(query=True, maxTime=True));

    cmds.intFieldGrp( 'name_FKIK_ifg_timeStr', 
                        columnAlign = [1, 'right'], 
                        columnWidth2 = [ 100, 280 ], 
                        value1 = FKIK_time_str,
                        label="Start Frame :"    );    

    cmds.intFieldGrp( 'name_FKIK_ifg_timeEnd', 
                        columnAlign= [1, 'right'], 
                        columnWidth2=[ 100, 280 ], 
                        value1 = FKIK_time_end,
                        label="End Frame:"  );  

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5, h = win_height/12, bgc = color_main );

    cmds.text( height = 20 , align="left", font = "boldLabelFont",  label='Match' );

    cmds.button( "name_btn_match_IK_to_FK", 
                 h = win_height/24,
                 label='Match IK', 
                 bgc=color_btn, 
                 command='JUN_cmd_match_IK_and_FK(\"JUN_FKIK_targetsPos_tsl\", \"JUN_FKIK_followersCtl_tsl\",\"JUN_name_FKIK_arm_l_cbg\",\"JUN_name_FKIK_arm_r_cbg\", \"JUN_name_FKIK_leg_l_cbg\",\"JUN_name_FKIK_leg_r_cbg\", 1)');

    cmds.button( "name_btn_match_FK_to_IK", 
                 h = win_height/24,
                 label='Match FK', 
                 bgc=color_btn, 
                 command='JUN_cmd_match_IK_and_FK(\"JUN_FKIK_targetsPos_tsl\", \"JUN_FKIK_followersCtl_tsl\",\"JUN_name_FKIK_arm_l_cbg\",\"JUN_name_FKIK_arm_r_cbg\", \"JUN_name_FKIK_leg_l_cbg\",\"JUN_name_FKIK_leg_r_cbg\", 0)');

    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5, h = win_height/12, bgc = color_main );

    cmds.text( height = 20 , align="left", font = "boldLabelFont",  label='Bake' );

    cmds.button( "name_btn_bake_IK", 
                 h = win_height/24,
                 label='Bake IK', 
                 bgc=color_btn, 
                 command='JUN_cmd_bake_IK_FK(\"JUN_FKIK_targetsPos_tsl\", \"JUN_FKIK_followersCtl_tsl\",\"JUN_name_FKIK_arm_l_cbg\",\"JUN_name_FKIK_arm_r_cbg\", \"JUN_name_FKIK_leg_l_cbg\",\"JUN_name_FKIK_leg_r_cbg\", 1, \"name_FKIK_ifg_timeStr\", \"name_FKIK_ifg_timeEnd\")');

    cmds.button( "name_btn_bake_FK", 
                 h = win_height/24,
                 label='Bake FK', 
                 bgc=color_btn, 
                 command='JUN_cmd_bake_IK_FK(\"JUN_FKIK_targetsPos_tsl\", \"JUN_FKIK_followersCtl_tsl\",\"JUN_name_FKIK_arm_l_cbg\",\"JUN_name_FKIK_arm_r_cbg\", \"JUN_name_FKIK_leg_l_cbg\",\"JUN_name_FKIK_leg_r_cbg\", 0, \"name_FKIK_ifg_timeStr\", \"name_FKIK_ifg_timeEnd\")');
    cmds.setParent( '..' )

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_FKIK_Tool_V02_01():
    PY_JUN_makeUI_FKIKTool();

PY_JUN_makeUI_FKIKTool();