# last Update date 25 09 25
# Python Script by Ji Hun Park

# Control Rig Tool V01.04
# 25 09 23    v01.03 : deleting joints for matching cage's objects
#                        fix joints orientation for leg, spine
# 25 09 25    v01.04 : set pole vector on helping joints  




import maya.cmds as cmds;
import maya.mel as mel;
import copy

def JUN_cmd_toolSel_btn ( str_selTool_tsl_selList, str_selTool_t_selNum ):

    str_selList = cmds.ls ( sl=True, fl=True );

    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList );
    
    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );

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
        str_objsShape = cmds.listRelatives ( str_obj, allDescendents=True, path=True, shapes=True );
        if str_objsShape is not None:
            for str_tgtShape in str_tgtShapesList:
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
# start (JUN_cmd_controlRig_setup_btn)

def JUN_cmd_controlRig_setup_btn(cage_glo, name_rig_name_tsl, text_state):

    str_token_option_ctl = "OptionAll_xx_ctl";

    str_selList = cmds.ls ( sl=True, fl=True );
    str_selList_object = []
    str_selList_Set = []
    str_cageRoot = ""

    str_CR_objChild = set();
    cmds.textScrollList( name_rig_name_tsl, e=True, removeAll=True );

    # set Maya set and object
    for str_selItem in str_selList :
        cmds.textScrollList( name_rig_name_tsl, e=True, append = str_selItem );
        if cmds.objectType(str_selItem) in "objectSet":
            str_selList_Set.append(str_selItem)
        else :
            str_selList_object.append(str_selItem)

    str_CR_objChild = BF_SELECTION_makeList_hierarchy(str_selList_object, 1, 1);

    # check if exist option controller
    str_CR_grp = [];
    for str_CR_obj in str_CR_objChild :
        if str_token_option_ctl in str_CR_obj :
            str_CR_grp.append(str_CR_obj);
            break

    if len(str_CR_grp) ==0 :
        cmds.text(text_state, e=True, bgc = [1, 0, 0], label= 'State : Fail to find objects for setup (' + str_token_option_ctl + ')');
        return 0;

    # set cage root
    for str_sel_set in str_selList_Set:
        if cage_glo.MSN_tkn_Cage_root in str_sel_set:
            str_cageRoot = str_sel_set
            break

    '''
    Set cage rooot set 
    MSN_rnm_Cage_01_pos_childe
    MSN_rnm_Cage_03_Tgt_childe
    '''

    str_setChild = cmds.sets(str_cageRoot, query=True)

    for str_set in str_setChild:
        if cage_glo.MSN_tkn_Cage_01_pos in str_set:
            cage_glo.set_rnm_str_pos_root(str_set)
        if cage_glo.MSN_tkn_Cage_03_Tgt in str_set:
            cage_glo.set_rnm_str_tgt_root(str_set)
        if cage_glo.MSN_tkn_Cage_04_helper in str_set:
            cage_glo.set_rnm_str_helper(str_set)

    cage_glo.set_rnm_lst_all()
    cage_glo.set_idx_for_cbg()
    cage_glo.dbg_print_rnm()
    cage_glo.dbg_print_idx()

    cmds.text(text_state, e=True, backgroundColor = [0, 1, 0], label= 'State : Sucess');

# end (JUN_cmd_controlRig_setup_btn)
#===================================================================================
def JUN_add_suffix_to_children(parent_object, suffix="_new"):
    child_new = []
    if not cmds.objExists(parent_object):
        cmds.warning(f"Parent object '{parent_object}' does not exist.")
        return

    children = cmds.listRelatives(parent_object, allDescendents=True, fullPath=True)
    
    if not children:
        print(f"Object '{parent_object}' has no children. Nothing to rename.")
        return

    children = children + [parent_object]
    children.sort(reverse = True)

    for child in children:
        short_name = child.split('|')[-1]
        new_name = short_name + suffix
        renamed_child = cmds.rename(child, new_name)
        child_new.append(renamed_child)

    child_new.reverse()

    print(f"child new : '{child_new}'...")
    return child_new


def JUN_MATCH_twoObjects ( str_tgtList, str_flwList, int_rotOrder, int_rotAxis, int_trs, int_rot ):     

    if not isinstance(str_flwList, list):
        str_tgtList = [str_tgtList]

    if not isinstance(str_flwList, list):
        str_flwList = [str_flwList]

    for i in range( 0, len(str_tgtList) ):

        str_rotOrder = cmds.xform ( str_tgtList[i], q = True, rotateOrder = True );
        vec_rotAixs  = cmds.xform ( str_tgtList[i], q = True, rotateAxis  = True );
        vec_trs      = cmds.xform ( str_tgtList[i], q = True,  worldSpace = True, translation = True );
        vec_rot      = cmds.xform ( str_tgtList[i], q = True,  worldSpace = True, rotation    = True );
        
        # print(str_flwList[i])
        try:
            print("match=================================")
            print(str_tgtList)
            print("flw")
            print(str_flwList)
            print("match end =================================")
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
        except:
            print("------------------------------------------------------------match error")


def JUN_create_ik_with_polevector(start_joint, end_joint, pv_object, solver="ikRPsolver", pole_name="pole_defualt"):
    """
    Create an IK handle between two joints and connect a pole vector control.
    
    Args:
        start_joint (str): The start joint of the IK chain.
        end_joint   (str): The end joint of the IK chain.
        pv_object   (str): The object to use as the pole vector control.
        solver      (str): IK solver type (default 'ikRPsolver'). single chain : "ikSCsolver"
    
    Returns:
        tuple: (ikHandle, effector, poleVectorConstraint)
    """
    pv_constraint = ""
    pv_object_new = ""

    # Create IK handle
    if solver is "ikRPsolver":
        pv_object_new = cmds.duplicate(pv_object)[0]
        pv_object_new = cmds.rename(pv_object_new, pole_name)
        cmds.parent(pv_object_new, world=True)

    ik_handle, effector = cmds.ikHandle(
        sj=start_joint,
        ee=end_joint,
        sol=solver
    )
    # Rename IK handle for clarity
    ik_handle = cmds.rename(ik_handle, f"{end_joint}_ikHandle")
    
    # Add pole vector constraint
    if solver is "ikRPsolver":
        pv_constraint = cmds.poleVectorConstraint(pv_object_new, ik_handle)[0]

    return ik_handle, effector, pv_constraint, pv_object_new


#=========================================================================================
# Set class : Cage (open)

class JUN_cage():
    '''
    MSN : Maya Set Name
    tkn : token
    rnm : real name
    onm : object name
    PA  : prefered angle
    '''
    def __init__(self):

        # set token : set name

        self.MSN_tkn_Cage_root = "Cage"

        self.MSN_tkn_Cage_01_pos = "Cage_01_pos"
        self.MSN_tkn_Cage_03_Tgt = "Cage_03_Tgt"
        self.MSN_tkn_Cage_04_helper = "Cage_04_helper"

        self.MSN_tkn_spine = "A00_Spine"

        self.MSN_tkn_C01_Fingers_zro_L = "C01_Fingers_zro_L"
        self.MSN_tkn_C01_Fingers_zro_R = "C01_Fingers_zro_R"

        self.MSN_tkn_A01_Arm_L_01_UpperArm = "A01_Arm_L_01_UpperArm"
        self.MSN_tkn_A01_Arm_L_02_LowerArm = "A01_Arm_L_02_LowerArm"
        self.MSN_tkn_A01_Arm_L_03_Wrist = "A01_Arm_L_03_Wrist"
        self.MSN_tkn_A01_Arm_L_04_Pole = "A01_Arm_L_04_Pole"

        self.MSN_tkn_A02_Arm_R_01_UpperArm = "A02_Arm_R_01_UpperArm"
        self.MSN_tkn_A02_Arm_R_02_LowerArm = "A02_Arm_R_02_LowerArm"
        self.MSN_tkn_A02_Arm_R_03_Wrist = "A02_Arm_R_03_Wrist"
        self.MSN_tkn_A02_Arm_R_04_Pole = "A02_Arm_R_04_Pole"

        self.MSN_tkn_A02_Arm_R_05_Wrist_WS = "Arm_R_03_Wrist_World"
        self.MSN_tkn_A02_Arm_R_05_Wrist_LS = "Arm_R_03_Wrist_Local"
        self.MSN_tkn_A02_Arm_R_05_FK_Ydwn = "Arm_R_03_Wrist_FK_Ydwn"

        self.MSN_tkn_B01_Leg_L_01 = "B01_Leg_L_01"
        self.MSN_tkn_B01_Leg_L_02 = "B01_Leg_L_02"
        self.MSN_tkn_B01_Leg_L_03 = "B01_Leg_L_03"
        self.MSN_tkn_B01_Leg_L_04 = "B01_Leg_L_04"
        self.MSN_tkn_B01_Leg_L_05 = "B01_Leg_L_05"
        self.MSN_tkn_B01_Leg_L_06_pole = "B01_Leg_L_06_pole"

        self.MSN_tkn_B02_Leg_R_01 = "B02_Leg_R_01"
        self.MSN_tkn_B02_Leg_R_02 = "B02_Leg_R_02"
        self.MSN_tkn_B02_Leg_R_03 = "B02_Leg_R_03"
        self.MSN_tkn_B02_Leg_R_04 = "B02_Leg_R_04"
        self.MSN_tkn_B02_Leg_R_05 = "B02_Leg_R_05"
        self.MSN_tkn_B02_Leg_R_06_pole = "B02_Leg_R_06_pole"

        self.MSN_tkn_A01_helper_arm_l = "A01_helper_arm_l"
        self.MSN_tkn_A01_helper_arm_r = "A02_helper_arm_r"
        self.MSN_tkn_A01_helper_leg_l = "A03_helper_leg_l"
        self.MSN_tkn_A01_helper_leg_r = "A04_helper_leg_r"

        # set token : real name

        self.tkn_poleObj_armLeft = "CH_l_ArmPoleSetup_xx_pos"
        self.tkn_poleObj_armRight = "CH_r_ArmPoleSetup_xx_pos"
        self.tkn_poleObj_legLefg = "CH_l_LegPoleSetup_xx_pos"
        self.tkn_poleObj_legRight = "CH_r_LegPoleSetup_xx_pos"

        # set token : prefred angle

        self.MSN_tkn_armJnt_l_PA = "A01_Arm_L_02_LowerArm"
        self.MSN_tkn_armJnt_r_PA = "A02_Arm_R_02_LowerArm"
        self.MSN_tkn_legJnt_l_PA = "B01_Leg_L_02"
        self.MSN_tkn_legJnt_r_PA = "B02_Leg_R_02"

        self.onm_tkn_armJnt_l_PA = "l_LowerArm_xx_ikjnt"
        self.onm_tkn_armJnt_r_PA = "r_LowerArm_xx_ikjnt"
        self.onm_tkn_legJnt_l_PA = "l_knee_ikjnt"
        self.onm_tkn_legJnt_r_PA = "r_knee_ikjnt"

        self.MSN_tkn_lst_Arm_L = [self.MSN_tkn_A01_Arm_L_01_UpperArm, self.MSN_tkn_A01_Arm_L_02_LowerArm, self.MSN_tkn_A01_Arm_L_03_Wrist, self.MSN_tkn_A01_Arm_L_04_Pole]
        self.MSN_tkn_lst_Arm_R = [self.MSN_tkn_A02_Arm_R_01_UpperArm, self.MSN_tkn_A02_Arm_R_02_LowerArm, self.MSN_tkn_A02_Arm_R_03_Wrist, self.MSN_tkn_A02_Arm_R_04_Pole]

        self.MSN_tkn_lst_leg_L = [self.MSN_tkn_B01_Leg_L_01, self.MSN_tkn_B01_Leg_L_02, self.MSN_tkn_B01_Leg_L_03, self.MSN_tkn_B01_Leg_L_04, self.MSN_tkn_B01_Leg_L_05, self.MSN_tkn_B01_Leg_L_06_pole]
        self.MSN_tkn_lst_leg_R = [self.MSN_tkn_B02_Leg_R_01, self.MSN_tkn_B02_Leg_R_02, self.MSN_tkn_B02_Leg_R_03, self.MSN_tkn_B02_Leg_R_04, self.MSN_tkn_B02_Leg_R_05, self.MSN_tkn_B02_Leg_R_06_pole]

        # create real name

        self.MSN_rnm_Cage_01_pos_root = ""
        self.MSN_rnm_Cage_03_Tgt_root = ""

        self.MSN_rnm_wrist_r_WS = []
        self.MSN_rnm_wrist_r_LS = []

        self.MSN_rnm_Cage_01_pos_childe = None
        self.MSN_rnm_Cage_03_Tgt_childe = None

        self.MSN_rnm_lst_spine = []
        self.MSN_rnm_lst_shoulders = []

        self.MSN_rnm_lst_fingers_l = []
        self.MSN_rnm_lst_fingers_r = []

        self.MSN_rnm_lst_arm_l = []
        self.MSN_rnm_lst_arm_r = []
        self.MSN_rnm_lst_leg_l = []
        self.MSN_rnm_lst_leg_r = []

        self.MSN_rnm_lst_wrist_l_WS = []
        self.MSN_rnm_lst_wrist_l_LS = []
        self.MSN_rnm_lst_wrist_r_WS = []
        self.MSN_rnm_lst_wrist_r_LS = []
        self.MSN_rnm_lst_wrist_FK_Ydwn = []

        self.rnm_armJnt_l_PA = []
        self.rnm_armJnt_r_PA = []
        self.rnm_legJnt_l_PA = []
        self.rnm_legJnt_r_PA = []

        self.rnm_poleObj_armLeft = []
        self.rnm_poleObj_armRight = []
        self.rnm_poleObj_legLefg = []
        self.rnm_poleObj_legRight = []

        self.rnm_helperJnts_arm_l = []
        self.rnm_helperJnts_arm_r = []
        self.rnm_helperJnts_leg_l = []
        self.rnm_helperJnts_leg_r = []

        #===================================================================
        # dictionary for setting rnm(open)

        # id for dictionary's key

        self.idStart_lst_of_MSN = 0
        self.arm_l = 0              # 001
        self.arm_r = 1              # 002
        self.leg_l = 2              # 003
        self.leg_r = 3              # 004

        self.idStart_SingleMSN = 100  
        self.spine = 100            # 100 
        self.fingers_l = 101        # 101 
        self.fingers_r = 102        # 102 
        self.shoulder_all = 103     # 103 
        self.shoulder_l = 104       # 104 
        self.shoulder_r = 105       # 105
        self.wirst_l_WS = 106       # 106
        self.wirst_l_LS = 107       # 107
        self.wirst_r_WS = 108       # 108
        self.wirst_r_LS = 109       # 109
        self.wirst_r_FK_ydwn = 110  # 110

        self.idStart_PA = 200 
        self.elbowJnt_l = 200       # 200
        self.elbowJnt_r = 201       # 201
        self.kneeJnt_l = 202        # 202
        self.kneeJnt_r = 203        # 203

        self.idStart_poleVectorObjects = 300 
        self.poleVecObj_arm_l= 300  # 300
        self.poleVecObj_arm_r= 301  # 301
        self.poleVecObj_leg_l= 302  # 302
        self.poleVecObj_leg_r= 303  # 303

        self.idStart_helperJnts = 400
        self.key_helperJnts_arm_l = 400 # 400
        self.key_helperJnts_arm_r = 401 # 401
        self.key_helperJnts_leg_l = 402 # 402
        self.key_helperJnts_leg_r = 403 # 403

        self.idEnd = 999

        # dictionary which value is list which member is MSN

        self.tkn_lstDic = { self.arm_l : self.MSN_tkn_lst_Arm_L,
                            self.arm_r : self.MSN_tkn_lst_Arm_R,
                            self.leg_l : self.MSN_tkn_lst_leg_L,
                            self.leg_r : self.MSN_tkn_lst_leg_R}
                            

        self.rnm_lstDic = { self.arm_l : self.MSN_rnm_lst_arm_l,
                            self.arm_r : self.MSN_rnm_lst_arm_r,
                            self.leg_l : self.MSN_rnm_lst_leg_l,
                            self.leg_r : self.MSN_rnm_lst_leg_r}
                            
                                                              

        # dictionary which value is stirng

        self.tkn_strDic = { self.spine     : self.MSN_tkn_spine,
                            self.fingers_l : self.MSN_tkn_C01_Fingers_zro_L,
                            self.fingers_r : self.MSN_tkn_C01_Fingers_zro_R,
                            self.wirst_l_WS : None,
                            self.wirst_l_LS : None,
                            self.wirst_r_WS : self.MSN_tkn_A02_Arm_R_05_Wrist_WS,
                            self.wirst_r_LS : self.MSN_tkn_A02_Arm_R_05_Wrist_LS,
                            self.wirst_r_FK_ydwn : self.MSN_tkn_A02_Arm_R_05_FK_Ydwn}


        self.rnm_strDic = { self.spine     : self.MSN_rnm_lst_spine,
                            self.fingers_l : self.MSN_rnm_lst_fingers_l,
                            self.fingers_r : self.MSN_rnm_lst_fingers_r,
                            self.wirst_l_WS : None,
                            self.wirst_l_LS : None,
                            self.wirst_r_WS : self.MSN_rnm_lst_wrist_r_WS,
                            self.wirst_r_LS : self.MSN_rnm_lst_wrist_r_LS,
                            self.wirst_r_FK_ydwn : self.MSN_rnm_lst_wrist_FK_Ydwn}


        # dictionary which value is for setting prefered angle (joint)
        
        self.tkn_MSN_PA = { self.elbowJnt_l  : self.MSN_tkn_armJnt_l_PA,
                            self.elbowJnt_r  : self.MSN_tkn_armJnt_r_PA,
                            self.kneeJnt_l   : self.MSN_tkn_legJnt_l_PA,
                            self.kneeJnt_r   : self.MSN_tkn_legJnt_r_PA}

        self.tkn_onm_PA = { self.elbowJnt_l  : self.onm_tkn_armJnt_l_PA,
                            self.elbowJnt_r  : self.onm_tkn_armJnt_r_PA,
                            self.kneeJnt_l   : self.onm_tkn_legJnt_l_PA,
                            self.kneeJnt_r   : self.onm_tkn_legJnt_r_PA}


        self.rnm_onm_PA = { self.elbowJnt_l  : self.rnm_armJnt_l_PA ,
                            self.elbowJnt_r  : self.rnm_armJnt_r_PA ,
                            self.kneeJnt_l   : self.rnm_legJnt_l_PA ,
                            self.kneeJnt_r   : self.rnm_legJnt_r_PA }

        # dictionary which value is pole vecotr object for setting ik to helper joints
        
        self.dic_tkn_poleVecObjs = {self.poleVecObj_arm_l : self.tkn_poleObj_armLeft,
                                    self.poleVecObj_arm_r : self.tkn_poleObj_armRight,
                                    self.poleVecObj_leg_l : self.tkn_poleObj_legLefg,
                                    self.poleVecObj_leg_r : self.tkn_poleObj_legRight}

        self.dic_rnm_poleVecObjs = {self.poleVecObj_arm_l : self.rnm_poleObj_armLeft, 
                                    self.poleVecObj_arm_r : self.rnm_poleObj_armRight, 
                                    self.poleVecObj_leg_l : self.rnm_poleObj_legLefg, 
                                    self.poleVecObj_leg_r : self.rnm_poleObj_legRight}

        self.dic_rnm_helperObjs = {self.key_helperJnts_arm_l : self.rnm_helperJnts_arm_l,
                                   self.key_helperJnts_arm_r : self.rnm_helperJnts_arm_r,
                                   self.key_helperJnts_leg_l : self.rnm_helperJnts_leg_l,
                                   self.key_helperJnts_leg_r : self.rnm_helperJnts_leg_r}

        # dictionary for setting rnm(close)
        #===================================================================

        #===================================================================
        # dictionary for cage set name (open)

        self.tkn_MSN = {self.wirst_r_WS : self.MSN_rnm_wrist_r_WS,
                        self.wirst_r_LS : self.MSN_rnm_wrist_r_LS}

        # dictionary for cage set name (open)
        #===================================================================

        #===================================================================
        # dictionary, list for communicate with checker(open)

        self.rnm_dic_all = {    self.spine :        self.MSN_rnm_lst_spine,
                                self.shoulder_all : self.MSN_rnm_lst_shoulders,
                                self.arm_l :        self.MSN_rnm_lst_arm_l,
                                self.arm_r :        self.MSN_rnm_lst_arm_r,
                                self.leg_l :        self.MSN_rnm_lst_leg_l,
                                self.leg_r :        self.MSN_rnm_lst_leg_r,
                                self.fingers_l :    self.MSN_rnm_lst_fingers_l,
                                self.fingers_r :    self.MSN_rnm_lst_fingers_r}

        self.rnm_lst_all = [    self.MSN_rnm_lst_spine,
                                self.MSN_rnm_lst_shoulders,
                                self.MSN_rnm_lst_arm_l,
                                self.MSN_rnm_lst_arm_r,
                                self.MSN_rnm_lst_leg_l,
                                self.MSN_rnm_lst_leg_r,
                                self.MSN_rnm_lst_fingers_l,
                                self.MSN_rnm_lst_fingers_r]

        self.rnm_lst_PA = [ None,
                            None,
                            self.rnm_armJnt_l_PA,
                            self.rnm_armJnt_r_PA,
                            self.rnm_legJnt_l_PA,
                            self.rnm_legJnt_r_PA,
                            None,
                            None]

        # dictionary, list for communicate with checker(close)
        #===================================================================

        #===================================================================
        # int value for cbg (open)

        self.idx_spine = [-1]
        self.idx_shoulder  = [-1]
        self.idx_arm_l = [-1]
        self.idx_arm_r = [-1]
        self.idx_leg_l = [-1]
        self.idx_leg_r = [-1]
        self.idx_fingers_l = [-1]
        self.idx_fingers_r = [-1]

        self.lst_idx =  [    self.idx_spine,
                             self.idx_shoulder,
                             self.idx_arm_l,
                             self.idx_arm_r,
                             self.idx_leg_l,
                             self.idx_leg_r,
                             self.idx_fingers_l,
                             self.idx_fingers_r  ]

        self.len_lst_idx = len(self.lst_idx)

        # int value for cbg (close)
        #===================================================================

    #===================================================================
    # is__ (open)

    def is_JUN(self, idx_given, idx_set):
        return True if idx_given == idx_set else False

    def is_spine(self, idx):
        return self.is_JUN(idx, self.idx_spine[0])

    def is_arm_left(self, idx):
        return self.is_JUN(idx, self.idx_arm_l[0])

    def is_arm_right(self, idx):
        return self.is_JUN(idx, self.idx_arm_r[0])

    def is_leg_left(self, idx):
        return self.is_JUN(idx, self.idx_leg_l[0])
    
    def is_leg_right(self, idx):
        return self.is_JUN(idx, self.idx_leg_r[0])

    def is_fingers_left(self, idx):
        return self.is_JUN(idx, self.idx_fingers_l[0])

    def is_fingers_right(self, idx):
        return self.is_JUN(idx, self.idx_fingers_r[0])


    # is__ (close)
    #===================================================================

    def set_rnm_str_pos_root(self, str_rnm):
        self.MSN_rnm_Cage_01_pos_root = str_rnm

    def set_rnm_str_tgt_root(self, str_rnm):
        self.MSN_rnm_Cage_03_Tgt_root = str_rnm

    def set_rnm_str_helper(self, str_rnm):
        str_setChild = cmds.sets(str_rnm, query=True)
        for str_set in str_setChild:
            if self.MSN_tkn_A01_helper_arm_l in str_set:
                str_helperMember = cmds.sets(str_set, query=True)
                self.rnm_helperJnts_arm_l.extend(str_helperMember)
                self.rnm_helperJnts_arm_l.sort()

            if self.MSN_tkn_A01_helper_arm_r in str_set:
                str_helperMember = cmds.sets(str_set, query=True)
                self.rnm_helperJnts_arm_r.extend(str_helperMember)
                self.rnm_helperJnts_arm_r.sort()

            if self.MSN_tkn_A01_helper_leg_l in str_set:
                str_helperMember = cmds.sets(str_set, query=True)
                self.rnm_helperJnts_leg_l.extend(str_helperMember)
                self.rnm_helperJnts_leg_l.sort()

            if self.MSN_tkn_A01_helper_leg_r in str_set:
                str_helperMember = cmds.sets(str_set, query=True)
                self.rnm_helperJnts_leg_r.extend(str_helperMember)
                self.rnm_helperJnts_leg_r.sort()

        print("helpers")
        print(self.rnm_helperJnts_arm_l)
        print(self.rnm_helperJnts_arm_r)
        print(self.rnm_helperJnts_leg_l)
        print(self.rnm_helperJnts_leg_r)


    def set_rnm_lst_pos_child(self):
        if self.MSN_rnm_Cage_01_pos_root is not None:
            self.MSN_rnm_Cage_01_pos_childe = cmds.sets(self.MSN_rnm_Cage_01_pos_root, query=True)
            self.MSN_rnm_Cage_01_pos_childe.sort()

    def set_rnm_lst_tgt_child(self):
        if self.MSN_rnm_Cage_03_Tgt_root is not None:
            self.MSN_rnm_Cage_03_Tgt_childe = cmds.sets(self.MSN_rnm_Cage_03_Tgt_root, query=True)
            self.MSN_rnm_Cage_03_Tgt_childe.sort()

    def set_rnm_lst_member_spine(self):
        for MSN_rnm_pos in self.MSN_rnm_Cage_01_pos_childe:
            if self.MSN_tkn_spine in MSN_rnm_pos:
                self.MSN_rnm_lst_spine = cmds.sets(MSN_rnm_pos, query=True)
                self.MSN_rnm_lst_spine.sort()

    def value_is_singleMSN(self, key_input):
        return True if key_input >= self.idStart_SingleMSN and key_input < self.idStart_PA else False

    def value_is_jnt_for_PA(self, key_input):
        return True if key_input >= self.idStart_PA and key_input < self.idStart_poleVectorObjects else False

    def value_is_poleVectorObject(self, key_input):
        return True if key_input >= self.idStart_poleVectorObjects and key_input < self.idStart_helperJnts else False
    
    def value_is_helper_jnts(self, key_input):
        return True if key_input >= self.idStart_helperJnts and key_input < self.idEnd else False

    def set_MSN_rnm_for_given_key(self, key_input, MSN_rnm_pos):
        try:
            self.tkn_MSN[key_input].append(MSN_rnm_pos)
        except:
            print("heyhey")

    def find_object_by_name(self, substring):
        all_objs = cmds.ls("*:*", long=True) + cmds.ls("*", long=True)  # includes namespaced + non-namespaced
        matches = []
    
        for obj in all_objs:
            short_name = obj.split(":")[-1]  # strip namespace
            if substring in short_name:
                matches.append(obj)
    
        return matches

    def set_rnm_lst_member(self, key_input):
        
        if self.value_is_singleMSN(key_input):
            tkn_str_input = self.tkn_strDic[key_input]
            rnm_str_input = self.rnm_strDic[key_input]

            for MSN_rnm_pos in self.MSN_rnm_Cage_01_pos_childe:
                if tkn_str_input in MSN_rnm_pos:
                    self.set_MSN_rnm_for_given_key(key_input, MSN_rnm_pos)
                    for str_obj in cmds.sets(MSN_rnm_pos, query=True):
                        rnm_str_input.append(str_obj)


            rnm_str_input.sort()
            

        elif self.value_is_jnt_for_PA(key_input):

            tkn_MSN_PA_keyed = self.tkn_MSN_PA[key_input]
            tkn_onm_PA_keyed = self.tkn_onm_PA[key_input]
            rnm_onm_PA_keyed = self.rnm_onm_PA[key_input]

            for MSN_rnm_pos in self.MSN_rnm_Cage_01_pos_childe:
                if tkn_MSN_PA_keyed in MSN_rnm_pos:
                    self.set_MSN_rnm_for_given_key(key_input, MSN_rnm_pos)
                    for rnm_onm_from_set in cmds.sets(MSN_rnm_pos, query=True):
                        if tkn_onm_PA_keyed in rnm_onm_from_set:
                            rnm_onm_PA_keyed.append(rnm_onm_from_set)
        
        elif self.value_is_poleVectorObject(key_input):
            tkn_poleVecObj = self.dic_tkn_poleVecObjs[key_input]
            cage_rnm_poleVecObj = self.dic_rnm_poleVecObjs[key_input]
            secne_rnm_poleVecObj = self.find_object_by_name(tkn_poleVecObj)
            cage_rnm_poleVecObj.append(secne_rnm_poleVecObj)

            print("cage_rnm_poleVecObj==============================")
            print(cage_rnm_poleVecObj)

#        elif self.value_is_helper_jnts(key_input):

        else:
            tkn_lst_input = self.tkn_lstDic[key_input]
            rnm_lst_input = self.rnm_lstDic[key_input]

            for tkn_setName in tkn_lst_input:
                for rnm_setName in self.MSN_rnm_Cage_01_pos_childe:
                    if tkn_setName in rnm_setName:
                        rnm_lst_input.append(rnm_setName)

            rnm_lst_input.sort()
            

    def clear_all(self):
        self.MSN_rnm_lst_spine.clear()
        self.MSN_rnm_lst_shoulders.clear()

        self.MSN_rnm_lst_fingers_l.clear()
        self.MSN_rnm_lst_fingers_r.clear()

        self.MSN_rnm_lst_arm_l.clear()
        self.MSN_rnm_lst_arm_r.clear()
        self.MSN_rnm_lst_leg_l.clear()
        self.MSN_rnm_lst_leg_r.clear()

        self.MSN_rnm_lst_wrist_l_WS.clear()
        self.MSN_rnm_lst_wrist_l_LS.clear()
        self.MSN_rnm_lst_wrist_r_WS.clear()
        self.MSN_rnm_lst_wrist_r_LS.clear()

        self.rnm_armJnt_l_PA.clear()
        self.rnm_armJnt_r_PA.clear()
        self.rnm_legJnt_l_PA.clear()
        self.rnm_legJnt_r_PA.clear()

        self.rnm_poleObj_armLeft.clear()
        self.rnm_poleObj_armRight.clear()
        self.rnm_poleObj_legLefg.clear()
        self.rnm_poleObj_legRight.clear()

        #self.rnm_helperJnts_arm_l.clear()
        #self.rnm_helperJnts_arm_r.clear()
        #self.rnm_helperJnts_leg_l.clear()
        #self.rnm_helperJnts_leg_r.clear()

    def set_rnm_lst_all(self):
        self.clear_all()
        self.set_rnm_lst_pos_child()
        self.set_rnm_lst_tgt_child()

        self.set_rnm_lst_member(self.arm_l)
        self.set_rnm_lst_member(self.arm_r)
        self.set_rnm_lst_member(self.leg_l)
        self.set_rnm_lst_member(self.leg_r)

        self.set_rnm_lst_member(self.wirst_r_WS)
        self.set_rnm_lst_member(self.wirst_r_LS)
        self.set_rnm_lst_member(self.wirst_r_FK_ydwn)

        self.set_rnm_lst_member(self.spine)
        self.set_rnm_lst_member(self.fingers_l)
        self.set_rnm_lst_member(self.fingers_r)

        self.set_rnm_lst_member(self.elbowJnt_l)
        self.set_rnm_lst_member(self.elbowJnt_r)
        self.set_rnm_lst_member(self.kneeJnt_l)
        self.set_rnm_lst_member(self.kneeJnt_r)    

        self.set_rnm_lst_member(self.poleVecObj_arm_l)    
        self.set_rnm_lst_member(self.poleVecObj_arm_r)    
        self.set_rnm_lst_member(self.poleVecObj_leg_l)    
        self.set_rnm_lst_member(self.poleVecObj_leg_r)    

    def set_idx_for_cbg(self):
        for idx in range(self.len_lst_idx):
            self.lst_idx[idx][0] = idx
    
    # getter for communicate with checker

    def get_rnm_dic(self, key_input):
        return self.rnm_dic_all[key_input]

    def get_rnm_lst(self, idx):
        return self.rnm_lst_all[idx]

    def get_rnm_PA(self, idx):
        return self.rnm_lst_PA[idx]

    def dbg_print_rnm(self):
        print("print real name")
        print(self.MSN_rnm_Cage_01_pos_childe)
        print(self.MSN_rnm_Cage_03_Tgt_childe)
        print(self.MSN_rnm_lst_arm_l)
        print(self.MSN_rnm_lst_arm_r)
        print(self.MSN_rnm_lst_leg_l)
        print(self.MSN_rnm_lst_leg_r)

        print(self.MSN_rnm_lst_spine)
        print(self.MSN_rnm_lst_fingers_l)
        print(self.MSN_rnm_lst_fingers_r)

        print(self.rnm_armJnt_l_PA)
        print(self.rnm_armJnt_r_PA)
        print(self.rnm_legJnt_l_PA)
        print(self.rnm_legJnt_r_PA)

        print(self.MSN_rnm_lst_wrist_r_WS)
        print(self.MSN_rnm_lst_wrist_r_LS)

        print(self.MSN_rnm_wrist_r_WS)
        print(self.MSN_rnm_wrist_r_LS)

        print("print real name end")

    def dbg_print_idx(self):
        for idx in range(self.len_lst_idx):
            print(self.lst_idx[idx][0])

        print("print for each")
        print(self.idx_spine)
        print(self.idx_shoulder)
        print(self.idx_arm_l)
        print(self.idx_arm_r)
        print(self.idx_leg_l)
        print(self.idx_leg_r)
        print(self.idx_fingers_l)
        print(self.idx_fingers_r)

# Set class : Cage (close)
#=========================================================================================

#=========================================================================================
# Set class : Checker (open)

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

    def dbg_print_lst_checked(self):
        print(self.lst_checked__)

# Set class : Checker (close)
#=========================================================================================


#=========================================================================================
# Set class : matcher_V02 (open)

class JUN_matcher_v02():
    def __init__(self):
        self.tgt = None
        self.flw = None

        self.tsl_tgt = None
        self.tsl_flw = None

        self.num_iter = 0

    def mtacher_create_joint_chain(self, objs, jntOrd="xyz", secAxOri="yup", suffix="_jnt", ):
        joints = []
        cmds.select(clear=True)  # start clean

        for idx, obj in enumerate(objs):

            if not cmds.objExists(obj):
                cmds.warning(f"Object '{obj}' does not exist, skipping.")
                continue

            # Get world position of object
            pos = cmds.xform(obj, q=True, ws=True, t=True)

            # Create a joint at that position
            jnt = cmds.joint(name=f"{obj}{suffix}", position=pos)
            joints.append(jnt)
        
        # Orient the joint chain nicely
        if joints:
            cmds.joint(joints[0], edit=True, orientJoint=f"{jntOrd}", secondaryAxisOrient=f"{secAxOri}", children=True, zeroScaleOrient=True)
            cmds.joint(joints[-1], e=True, oj='none', ch=True, zso=True)

        return joints
        
    
    def matcher_vector_element_wise_multiply(self, v1, v2):
        return  [a * b for a, b in zip(v1, v2)]


    def set_tgt_lst_from_tsl(self, str_tsl):
        self.tgt = cmds.textScrollList( str_tsl, q=True, allItems=True )

    def set_flw_lst_from_tsl(self, str_tsl):
        self.flw = cmds.textScrollList( str_tsl, q=True, allItems=True )

    def set_matcher(self, str_tsl_tgt, str_tsl_flw):
        self.set_tgt_lst_from_tsl(str_tsl_tgt)
        self.set_flw_lst_from_tsl(str_tsl_flw)

        num_inter_tgt = cmds.textScrollList( str_tsl_tgt, q=True, numberOfItems=True )
        num_inter_flw = cmds.textScrollList( str_tsl_flw, q=True, numberOfItems=True )

        self.num_iter = num_inter_tgt if num_inter_tgt < num_inter_flw else num_inter_flw
    
    def type_is_set(self, type_input):
        return True if cmds.objectType(type_input) in "objectSet" else False

    def match_set_members_to_single_tgt(self, str_tgt_single, str_setName):
        lst_tgt_single = [str_tgt_single]
        lst_members_from_set = cmds.sets(str_setName, q=True)

        for str_member_from_set in lst_members_from_set:
            lst_member_from_set = [str_member_from_set]
            JUN_MATCH_twoObjects(lst_tgt_single, lst_member_from_set, 1, 1, 1, 1)

    def match_lst_to_single_tgt(self, str_tgt_single, str_lstName):
        if not isinstance(str_tgt_single, list): #if str_tgt_single is not a list, make it to list
            str_tgt_single = [str_tgt_single]
        for i in range(0, len(str_lstName)):
            JUN_MATCH_twoObjects(str_tgt_single, str_lstName[i], 1, 1, 1, 1)

    def lock_translation(self, objs):
        for obj in objs:
            for axis in ["tx", "ty", "tz"]:
                attr = f"{obj}.{axis}"
                if cmds.objExists(attr):
                    cmds.setAttr(attr, lock=True)

    def group_list_items(self, objs, name="newGroup"):
        """
        Group all valid objects in the given list under a single group.
        Invalid entries like "" or None are ignored.

        Args:
            objs (list): List of object names to group.
            name (str): Name of the new group.

        Returns:
            str: The created group name.
        """
        # Filter out invalid names
        valid_objs = [obj for obj in objs if obj and cmds.objExists(obj)]

        if not valid_objs:
            raise ValueError("No valid objects found in the list.")

        grp = cmds.group(valid_objs, name=name)
        return grp
    
    def filter_ik_handles(self, objs):
        """
        Filter a list so it only contains IK handles.

        Args:
            objs (list): List of object names.

        Returns:
            list: A new list containing only IK handles.
        """
        iks = [obj for obj in objs if cmds.objExists(obj) and cmds.objectType(obj) == "ikHandle"]
        return iks

    def match(self, orient_to_joint=False, jntOrd="xyz", secAxOri="yup", is_leg=False, is_spine__=False, set_ik=False, pole_obj=None, helper_objs=None, tgt_given=None):
        member_tgts = copy.deepcopy(self.tgt)
        member_flws = copy.deepcopy(self.flw)
        lst_remain = []

        if orient_to_joint:
            member_tgts = self.mtacher_create_joint_chain(member_tgts, jntOrd, secAxOri)

        if tgt_given:
            cmds.delete(member_tgts)
            member_tgts = tgt_given

        if is_leg:
            cmds.joint(member_tgts[-2], edit=True, orientJoint="xzy", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
            cmds.joint(member_tgts[-1], edit=True, orientJoint="none", children=True, zeroScaleOrient=True)
            JUN_MATCH_twoObjects(member_tgts, helper_objs, 1, 1, 1, 1)
            lst_remain_A = JUN_create_ik_with_polevector(helper_objs[-2], helper_objs[-1], pole_obj, "ikSCsolver")
            lst_remain_B = JUN_create_ik_with_polevector(helper_objs[-3], helper_objs[-2], pole_obj, "ikSCsolver")

            lst_remain = [*lst_remain_A, *lst_remain_B]
            lst_remain_ik = self.filter_ik_handles(lst_remain)
            grp_remain = self.group_list_items(lst_remain_ik)

            lst_remain_C = JUN_create_ik_with_polevector(helper_objs[0], helper_objs[2], pole_obj)
            lst_remain = [*lst_remain_A, *lst_remain_B, *lst_remain_C, grp_remain]


        elif is_spine__:
            cmds.joint(member_tgts, edit=True, orientJoint="none", children=True, zeroScaleOrient=True)
        elif set_ik and helper_objs:
            JUN_MATCH_twoObjects(member_tgts, helper_objs, 1, 1, 1, 1)
            lst_remain = JUN_create_ik_with_polevector(helper_objs[0], helper_objs[2], pole_obj)

        for i in range(0, self.num_iter):
            member_flw = member_flws[i]
            member_tgt = member_tgts[i]

            if self.type_is_set(member_flw):
                if helper_objs:
                    helper_obj = helper_objs[i]
                    self.match_set_members_to_single_tgt(helper_obj, member_flw)
                else:
                    try:
                        self.match_set_members_to_single_tgt(member_tgt, member_flw)
                    except:
                        print("error 1072")

            else:   
                member_flw = [member_flw]
                member_tgt = [member_tgt]
                JUN_MATCH_twoObjects(member_tgt, member_flw, 1, 1, 1, 1)
        
        
        if orient_to_joint:
            cmds.delete(member_tgts)

        for item in lst_remain:
            try:
                cmds.delete(item)
            except:
                print("error 1087")

    def match_cage_spine(self):
        self.match(True, "yzx", "zup", False, True)

    def get_worldSpace_obj(self, obj):
        pos = cmds.xform(obj, query=True, translation=True, worldSpace = True)
        loc = cmds.spaceLocator()[0]
        cmds.xform(loc, ws=True, t=pos)
        return loc

    def match_flw_to_tgt_zro_rotate(self, tgt_idx=0, flw_idx=0, flw_given=None):
        member_flws = copy.deepcopy(self.flw)
        member_tgts = copy.deepcopy(self.tgt)
        if flw_given:
            member_flws = flw_given

        ws_obj = self.get_worldSpace_obj(member_tgts[tgt_idx])
        self.match_set_members_to_single_tgt(ws_obj, member_flws[flw_idx])

        cmds.delete(ws_obj)

#=========================================================================================

    def match_cage_arm_left(self, pole_obj=None, helper_objs=None):
        self.match(True, "xyz", "yup", False, False, True, pole_obj, helper_objs)
        self.match_flw_to_tgt_zro_rotate(tgt_idx=2, flw_idx=2)


    def match_cage_arm_right(self, pole_obj=None, cage_given =None, helper_objs=None):
        jnts_arm_r_primX = self.mtacher_create_joint_chain(self.tgt, suffix = "_r_jnt")
        jnts_arm_l_from_oriRightArm = cmds.mirrorJoint(jnts_arm_r_primX[0], mirrorYZ=True, mirrorBehavior=True, searchReplace=["_r_", "_l_"])
        jnts_arm_l_primX = self.mtacher_create_joint_chain(jnts_arm_l_from_oriRightArm, suffix = "_l_jnt_yUp")
        jnts_arm_r_primMX_yDwn = cmds.mirrorJoint(jnts_arm_l_primX[0], mirrorYZ=True, mirrorBehavior=True, searchReplace=["_l_jnt_yUp", "_r_jnt_yDwn"])

        self.match(True, "xyz", "yup", False, False, True, pole_obj, helper_objs, tgt_given=jnts_arm_r_primMX_yDwn)
        self.match_flw_to_tgt_zro_rotate(tgt_idx=2, flw_idx=0, flw_given=cage_given.MSN_rnm_wrist_r_WS)
        
        member_tgts = copy.deepcopy(self.tgt)
        obj_wrist_r_Ydwn = self.get_worldSpace_obj(member_tgts[2])
        cmds.rotate(180, 0, 0, obj_wrist_r_Ydwn, relative=True, objectSpace=True)
        self.match_lst_to_single_tgt(obj_wrist_r_Ydwn, cage_given.MSN_rnm_lst_wrist_FK_Ydwn)

        dele_lst = [*jnts_arm_r_primX,*jnts_arm_l_from_oriRightArm,*jnts_arm_l_primX,*jnts_arm_r_primMX_yDwn, obj_wrist_r_Ydwn]
        for i in range(0, len(dele_lst)):
            try:
                cmds.delete(dele_lst[i])
            except:
                print("error 1140")
        
    def match_cage_leg_l(self, pole_obj=None, helper_obj=None):
        self.match(True, "xzy", "zup", True, False, True, pole_obj, helper_obj)

    def match_cage_leg_r(self, pole_obj=None, helper_obj=None):
        self.match(True, "xzy", "zup", True, False, True, pole_obj, helper_obj)

            
# Set class : matcher_V02 (close)
#=========================================================================================

def JUN_CR_setUp_followers( cage_glo,
                            targetsPos_tsl, 
                            followersCtl_tsl,
                            spn_cbg,
                            sdr_cbg,
                            arm_l_cbg,
                            arm_r_cbg,
                            leg_l_cbg,
                            leg_r_cbg,
                            fgr_l_cbg,
                            fgr_r_cbg):

    ckr = JUN_checker()
    lst_cbg = [ spn_cbg,
                sdr_cbg,
                arm_l_cbg,
                arm_r_cbg,
                leg_l_cbg,
                leg_r_cbg,
                fgr_l_cbg,
                fgr_r_cbg ]


    ckr.set_lst_checked(lst_cbg)
    ckr.dbg_print_lst_checked()

    cmds.textScrollList( followersCtl_tsl, e=True, removeAll=True ); 

    for idx, is_checked in enumerate(ckr.get_lst_stat()):
        if is_checked:
            lst_or_str_from_cage = cage_glo.get_rnm_lst(idx)
            cmds.textScrollList( followersCtl_tsl, e=True, append = lst_or_str_from_cage );

#####

#===================================================================================
# match fk ik End
#===================================================================================


def JUN_CR_match( cage_glo, lst_cbg_name, tsl_tgt, tsl_flw):
    mcr = JUN_matcher_v02()
    mcr.set_matcher(tsl_tgt, tsl_flw)

    checked = True
    ckr = JUN_checker()
    ckr.set_lst_checked(lst_cbg_name)

    cage_glo.dbg_print_idx()
    # mcr.match(orient_to_joint=True)

    for idx, checkbox__ in enumerate(ckr.get_lst_stat()):
        if checkbox__ is checked:
            if cage_glo.is_spine(idx):
                mcr.match_cage_spine()
                idx_hid = mcr.num_iter
                obj_hid = mcr.flw[idx_hid]                
                cmds.setAttr(obj_hid+".visibility", False)

            if cage_glo.is_arm_left(idx):
                mcr.match_cage_arm_left(cage_glo.rnm_poleObj_armLeft[0], helper_objs = cage_glo.rnm_helperJnts_arm_l)

            if cage_glo.is_arm_right(idx):
                mcr.match_cage_arm_right(cage_glo.rnm_poleObj_armRight[0], cage_given= cage_glo, helper_objs = cage_glo.rnm_helperJnts_arm_r)

            if cage_glo.is_leg_left(idx):
                mcr.match_cage_leg_l(cage_glo.rnm_poleObj_legLefg[0], cage_glo.rnm_helperJnts_leg_l)

            if cage_glo.is_leg_right(idx):
                mcr.match_cage_leg_r(cage_glo.rnm_poleObj_legRight[0], cage_glo.rnm_helperJnts_leg_r)
                
            if cage_glo.is_fingers_left(idx):
                print("fig l")
            if cage_glo.is_fingers_right(idx):
                print("fig r")
    
def JUN_CR_setUp_IK(cage_glo, lst_cbg_name):
    checked = True
    ckr = JUN_checker()
    ckr.set_lst_checked(lst_cbg_name)

    print("set preferred angle")
    for idx, checkbox__ in enumerate(ckr.get_lst_stat()):
        if checkbox__ is checked:
            rnm_jnt_to_set_PA = cage_glo.get_rnm_PA(idx)
            if rnm_jnt_to_set_PA is not None:
                print(rnm_jnt_to_set_PA)
                cmds.joint(rnm_jnt_to_set_PA, edit=True, setPreferredAngles=True)
    print("set preferred angle End")


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

def PY_JUN_makeUI_ContrlRigTool ():
    str_winTitle = "Control Rig Tool";
    str_winName = "Junny_win_ControlRig_Tool";
    win_width = 480;
    win_height = 800;

    width_tsl = 80;

    color_white = [1.0, 1.0, 1.0];
    color_mainDark = [0.0, 0.2, 0.0];
    color_main = [0.3, 0.65, 0.2];
    color_sub = [0.3, 0.6, 0.1];
    color_btn = [0.95, 0.7, 0.5];
    color_back = [0.96, 0.96, 0.96];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );

    # create cage for global use
    JUN_cage_glo = JUN_cage();
    #print(JUN_cage_glo.MSN_tkn_Cage_01_pos)
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="Control Rig Tool V01.04" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 23-SEP-2025\')".format(color_main)

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
    
    cmds.frameLayout( label='Tool : Setup control rig', collapsable= True, bgc =color_main );

    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    # 

    #rowLayout : Select Rig (close)
    cmds.rowLayout( numberOfColumns=2 );


    cmds.textScrollList("JUN_name_CR_name_tsl", 
                        bgc = color_white,
                        height = (60),
                        numberOfRows=1, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_name_CR_name_tsl\")');

    cmds.button( "name_btn_setup_controlRig_name",
                 label='Select Objects',
                 bgc =color_btn,
                 command= lambda *argv : JUN_cmd_controlRig_setup_btn(JUN_cage_glo, "JUN_name_CR_name_tsl", "JUN_CR_text_state"));

    #rowLayout : Select Rig (close)
    cmds.setParent( '..' )


    cmds.rowLayout( numberOfColumns=1 );

    cmds.text( "JUN_CR_text_state", height = 20 , align="left", backgroundColor = [1, 1, 1], font = "boldLabelFont",  label='State : Searching...' );
    
    cmds.setParent( '..' )

    # paneLayout : vertical2(open)                                                      
    
    #==============================================================================
    # frameLayout : cage part (open)
    cmds.frameLayout( label='Cage Part', collapsable= True, bgc =color_main );

    #==============================================================================
    # paneLayout : vertical2(close)                                                     
    cmds.paneLayout( configuration= "vertical2" )

    #------------------------------------------------------------------
    # columnLayout : Select Base (close)                                         
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    #cmds.text( "JUN_name_checkBoxGrp_Arm", align="left", font = "boldLabelFont",  label='Arm' );

    cmds.checkBoxGrp( "JUN_CR_spine_cbg", label='Spine', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );
    cmds.checkBoxGrp( "JUN_CR_shoulder_cbg", label='Shoulders', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );
    cmds.checkBoxGrp( "JUN_CR_arm_l_cbg", label='Arm Left', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );
    cmds.checkBoxGrp( "JUN_CR_arm_r_cbg", label='Arm Right', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );

    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    #cmds.text( "JUN_name_checkBoxGrp_Leg", align="left", font = "boldLabelFont",  label='Leg' );

    cmds.checkBoxGrp( "JUN_CR_leg_l_cbg", label='Leg Left', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );
    cmds.checkBoxGrp( "JUN_CR_leg_r_cbg", label='Leg Right', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );
    cmds.checkBoxGrp( "JUN_CR_fingers_l_cbg", label='Fingers Left', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );
    cmds.checkBoxGrp( "JUN_CR_fingers_r_cbg", label='Fingers Right', columnWidth2=(100, 20) ,columnAlign = (1, "left"), columnAttach2 = ("both", "both") , value1 = False );
    
    # columnLayout : Select Base (close)                                         
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    cmds.setParent( '..' )
    # paneLayout : vertical2(close)                                                     
    #==============================================================================
    
    cmds.setParent( '..' )
    # frameLayout : cage part (close)                                                     
    #==============================================================================

    lst_cbg_name = [    "JUN_CR_spine_cbg",
                        "JUN_CR_shoulder_cbg",
                        "JUN_CR_arm_l_cbg",
                        "JUN_CR_arm_r_cbg",
                        "JUN_CR_leg_l_cbg",
                        "JUN_CR_leg_r_cbg",
                        "JUN_CR_fingers_l_cbg",
                        "JUN_CR_fingers_r_cbg",]

    #===================================================================================
    # frameLayout : set up (open)                                                        
    #===================================================================================                                           
    
    cmds.frameLayout( label='Set Up', collapsable= True, bgc =color_main );

    cmds.paneLayout( configuration= "vertical2" )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_CR_selectTgt", 
                 label='Select targets', 
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_CT_tgts_tsl\", \"JUN_CT_tgts\")');

    cmds.paneLayout( configuration= "vertical2", paneSize=[1,1,100] )

    cmds.text( "JUN_CT_tgts_01", align="left", font = "boldLabelFont",  label='Targets ' );
    cmds.text( "JUN_CT_tgts", align="left", font = "boldLabelFont",  label='Number: ' );

    cmds.setParent('..')

    cmds.textScrollList("JUN_CT_tgts_tsl", 
                        height = (win_height*0.2),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_CT_tgts_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_CT_tgts_tsl\", \"JUN_CT_tgts\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_CT_tgts_tsl\", \"JUN_CT_tgts\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_CT_tgts_tsl\", \"JUN_CT_tgts\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_CT_tgts_tsl\", \"JUN_CT_tgts\" )' );

    cmds.setParent( '..' )

    cmds.setParent( '..' )

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_CR_selectFlw", 
                 label='Select followers', 
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_CT_flw_tsl\", \"JUN_CT_followers\")');

    cmds.paneLayout( configuration= "vertical2", paneSize=[1,1,100] )

    cmds.text( "JUN_CT_followers_01", align="left", font = "boldLabelFont",  label='Followers ' );
    cmds.text( "JUN_CT_followers", align="left", font = "boldLabelFont",  label='Number: ' );

    cmds.setParent('..')

    cmds.textScrollList("JUN_CT_flw_tsl", 
                        height = (win_height*0.2),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_CT_flw_tsl\")');
                        
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_CT_flw_tsl\", \"JUN_CT_followers\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_CT_flw_tsl\", \"JUN_CT_followers\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_CT_flw_tsl\", \"JUN_CT_followers\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_CT_flw_tsl\", \"JUN_CT_followers\" )' );


    cmds.setParent( '..' )
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )
    
    # Shader Endgine(SG) Tool (close)                                            
    #------------------------------------------------------------------
    #cmds.setParent( '..' )

    # paneLayout : vertical2(close)                                                     
    #==============================================================================
    cmds.setParent( '..' )

    #==============================================================================
    # paneLayout : frameLayout(close)                                                     
    #==============================================================================
    cmds.setParent( '..' )

    #===================================================================================
    # frameLayout : Tool : Selection(close)
    #===================================================================================
    #cmds.setParent( '..' )


    #===================================================================================
    # frameLayout : Select By Shape (open)                                                        
    #===================================================================================

    cmds.frameLayout( label=' Tool : Match IK and FK', collapsable= True, bgc =color_main );

    # cmds.text( height = 20 , align="left", font = "boldLabelFont",  label='Match' );

    cmds.button( "name_btn_CR_setup", 
                 h = win_height/24,
                 label='Set up Followers', 
                 bgc=color_btn, 
                 command= lambda *argv : JUN_CR_setUp_followers(JUN_cage_glo,   "JUN_CT_tgts_tsl", 
                                                                                "JUN_CT_flw_tsl",
                                                                                "JUN_CR_spine_cbg",
                                                                                "JUN_CR_shoulder_cbg", 
                                                                                "JUN_CR_arm_l_cbg",
                                                                                "JUN_CR_arm_r_cbg",
                                                                                "JUN_CR_leg_l_cbg",
                                                                                "JUN_CR_leg_r_cbg",
                                                                                "JUN_CR_fingers_l_cbg",
                                                                                "JUN_CR_fingers_r_cbg"));

    cmds.button( "name_btn_CR_match", 
                 h = win_height/24,
                 label='Match', 
                 bgc=color_btn, 
                 command= lambda *argv : JUN_CR_match(JUN_cage_glo, lst_cbg_name, "JUN_CT_tgts_tsl", 
                                                                                  "JUN_CT_flw_tsl"));
    # edit tgt tsl. fill it to drivers
    cmds.button( "name_btn_CR_setup_IK", 
                 h = win_height/24,
                 label='Set up IK', 
                 bgc=color_btn, 
                 command= lambda *argv : JUN_CR_setUp_IK(JUN_cage_glo, lst_cbg_name))

    cmds.button( "name_btn_CR_connect", 
                 h = win_height/24,
                 label='Connect', 
                 bgc=color_btn, 
                 command='JUN_CR_setUp_followers(\"JUN_FKIK_targetsPos_tsl\", \"JUN_FKIK_followersCtl_tsl\",\"JUN_name_FKIK_arm_l_cbg\",\"JUN_name_FKIK_arm_r_cbg\", \"JUN_name_FKIK_leg_l_cbg\",\"JUN_name_FKIK_leg_r_cbg\", 0)');

    cmds.setParent( '..' )

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_ControlRigTool_V01_04():
    PY_JUN_makeUI_ContrlRigTool();

PY_JUN_makeUI_ContrlRigTool();