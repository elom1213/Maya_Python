# last Update date 25 07 30
# Python Script by Ji Hun Park

# BS tool V01.01
# V01.01 rename "Connect BS Tool" to "BS Tool"

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

        
# name_toolOption_tfg_prefix
def JUN_cmd_copyName(str_selTool_tsl_base, str_selTool_tsl_tgt, str_toolOption_tfg_prefix):
    str_allItemList_base = cmds.textScrollList( str_selTool_tsl_base, q=True, allItems=True);
    str_allItemList_tgt  = cmds.textScrollList( str_selTool_tsl_tgt , q=True, allItems=True);
    str_prefix = cmds.textFieldGrp( str_toolOption_tfg_prefix , q=True, text=True);
    # int_timeStr = cmds.intFieldGrp(str_cpyOpt_ifg_strTime, q=True, value1=True);
    # int_timeEnd = cmds.intFieldGrp(str_cpyOpt_ifg_endTime, q=True, value1=True);
    
    int_num_base = cmds.textScrollList( str_selTool_tsl_base, q=True, numberOfItems=True);
    list_newName = []

    cmds.textScrollList( str_selTool_tsl_tgt, e=True, removeAll=True ); 
    
    for i in range(0, int_num_base):
        # cmds.copyKey(str_allItemList_base[i] , time = (int_timeStr, int_timeEnd));
        name_base = str_prefix + str_allItemList_base[i].split("|")[-1];
        name_result = cmds.rename(str_allItemList_tgt[i], name_base);
        # list_newName.append(name_result[0])
        cmds.textScrollList( str_selTool_tsl_tgt, e=True, append = name_result );       
        # try:
        #     cmds.pasteKey(str_allItemList_tgt[i]);
        # except:
        #     print("pseted");

def get_zero_with_length(int_len):
    if int_len is 0 :
        return '';

    str_zero = '';
    for i in range(0, int_len):
        str_zero += '0'
    return str_zero

def strLen(obj):
    return len(str(obj));

def get_idx_with_pad(int_max_pad, int_idx_now):
    int_len_idx_now = strLen(int_idx_now);
    int_pad_remain = int_max_pad - int_len_idx_now;
    str_zero = get_zero_with_length(int_pad_remain);
    
    return str_zero + str(int_idx_now)

def get_str_with_space(str_list_token, str_space):
    len_list_token = len(str_list_token);
    str_list_final = [];
    str_final = '';
    for idx_token in range(0, len_list_token-1):
        str_list_final.append(str_list_token[idx_token] + str_space);
    str_list_final.append(str_list_token[-1]);

    for str_token in str_list_final:
        str_final += str_token;
    return str_final

def JUN_cmd_rename_for_dyn(str_NamingDyn_tsl, 
                            namingDyn_tf_dyn, 
                            namingDyn_tf_asset,
                            namingDyn_tf_sid,
                            namingDyn_tf_index_01,
                            namingDyn_tf_index_02,):
    list_objs = cmds.textScrollList( str_NamingDyn_tsl, q=True, allItems=True);

    str_dyn     = cmds.textField( namingDyn_tf_dyn, q=True, text = True  );    
    str_ast     = cmds.textField( namingDyn_tf_asset, q=True, text = True  );    
    str_sid     = cmds.textField( namingDyn_tf_sid, q=True, text = True  );    
    str_idx_01  = cmds.textField( namingDyn_tf_index_01, q=True, text = True  );    
    str_idx_02  = cmds.textField( namingDyn_tf_index_02, q=True, text = True  );    

    int_token_origin_01 = int(str_idx_01);
    int_token_01        = int(str_idx_01);
    int_token_origin_02 = int(str_idx_02);
    int_token_02        = int(str_idx_02);

    list_descds = [];

    len_list_tsl = len(list_objs);

    for idx_list in range(0, len_list_tsl):
        obj_now = list_objs[idx_list];
        list_descd_A = [];
        list_descd_tmp = cmds.listRelatives( obj_now , allDescendents=True)
        
        if list_descd_tmp is not None:
            for descd in list_descd_tmp:
                list_descd_A.append(descd);

        list_descd_A.append(obj_now);

        list_descd_A.reverse();

        list_descds.append(list_descd_A);

    len_descd = len(list_descds);
    mmx_pad_token_01 = len(str(len_descd));

    for idx_descd in range(0, len_descd):
        str_token_01 = get_idx_with_pad(mmx_pad_token_01, int_token_01)
        list_descd_dep_01 = list_descds[idx_descd];

        len_descd_dep_01 = len(list_descd_dep_01);
        max_pad_token_02 = len(str(len_descd_dep_01));

        for idx_descd_dep_01 in range(0, len_descd_dep_01):
            str_token_02 = get_idx_with_pad(max_pad_token_02, int_token_02)

            list_token = [str_dyn, str_ast, str_sid, str_token_01, str_token_02];

            name_new = get_str_with_space(list_token, "_");
            obj_now = list_descd_dep_01[idx_descd_dep_01];
            cmds.rename(obj_now, name_new);

            int_token_02 += 1;

        int_token_02 = int_token_origin_02;

        int_token_01 += 1;


def JUN_cmd_getAttr_btn(source_tsl, attr_tsl):
    lst_src = cmds.textScrollList( source_tsl, q=True, allItems=True)
    lst_attrName = cmds.listAttr(lst_src[0])
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


'''
def JUN_get_blendshape_targets(blendshape_node):
    if not cmds.objExists(blendshape_node) or cmds.nodeType(blendshape_node) != 'blendShape':
        cmds.warning(f"'{blendshape_node}' is not a valid blendShape node.")
        return []

    # Query the targets using the 'target' flag with 'query' and 'multi'
    targets = cmds.blendShape(blendshape_node, query=True, target=True)
    return targets if targets else []
'''
def get_weight_index(attr):
    match = re.search(r'\[(\d+)\]', attr)
    return int(match.group(1)) if match else -1


def JUN_get_blendshape_targets(blendshape_node):
    if not cmds.objExists(blendshape_node) or cmds.nodeType(blendshape_node) != "blendShape":
        cmds.warning(f"'{blendshape_node}' is not a valid blendShape node.")
        return []

    aliases = cmds.aliasAttr(blendshape_node, query=True) or []

    grouped = [(aliases[i], aliases[i+1]) for i in range(0, len(aliases), 2)]

    # Optional: sort by alias name
    grouped.sort(key=lambda x: get_weight_index(x[1]))

    # Now you have sorted pairs
    for alias, real_attr in grouped:
        print(f"{alias} => {real_attr}")

    # aliasAttr returns list in format [alias1, attr1, alias2, attr2, ...]
    #target_names = [aliases[i] for i in range(0, len(aliases), 2)]
    grouped_sorted = [item[0] for item in grouped]
    print(grouped_sorted)
    return grouped_sorted
    
def JUN_cmd_connectTgt_btn(source_tsl, attr_tsl, dist_tsl, tgtIdx_tf):
    lst_src = cmds.textScrollList( source_tsl, q=True, allItems=True)
    lst_attr = cmds.textScrollList( attr_tsl, q=True, selectItem=True)
    lst_dist = cmds.textScrollList( dist_tsl, q=True, allItems=True)
    tgt_num = int(cmds.textField(tgtIdx_tf, q=True, text=True))

    len_src = len(lst_src)
    len_dist = len(lst_dist)

    if len_src is 1:
        print("connect 1 attribute to multiple blendshape's targets")
        for idx in range(0, len_dist):
            src_attr = lst_src[0] + "." + lst_attr[0]

            lst_tgtName = JUN_get_blendshape_targets(lst_dist[idx])

            dist_attr = lst_dist[idx] + "." + lst_tgtName[tgt_num]
            cmds.connectAttr(src_attr, dist_attr, force = True)


    for idx in range(0, len_src):
        src_attr = lst_src[idx] + "." + lst_attr[0]

        lst_tgtName = JUN_get_blendshape_targets(lst_dist[idx])

        dist_attr = lst_dist[idx] + "." + lst_tgtName[tgt_num]
        cmds.connectAttr(src_attr, dist_attr, force = True)


def JUN_cmd_keyEverytgt_for_single_BSnode(BS_node_name):
    # lst_tgtName = JUN_get_blendshape_targets(BS_node_name)
    # frame_now = cmds.currentTime( query=True )
    # print(lst_tgtName)

    lst_tgtweight = cmds.blendShape(BS_node_name, query=True, weight=True)
    for idx, member_tgtWeightVal in enumerate(lst_tgtweight):
        BSnode_tgt = BS_node_name + ".weight[" + str(idx) + "]"
        cmds.setKeyframe( BSnode_tgt, t=idx, v= 1)
        cmds.setKeyframe( BSnode_tgt, t=idx-1, v= 0)
        cmds.setKeyframe( BSnode_tgt, t=idx+1, v= 0)


def JUN_cmd_keyEveryTgt(BSnode_tsl):
    lst_BSnode = cmds.textScrollList(BSnode_tsl, q=True, allItems=True)
    len_BSnode = len(lst_BSnode)

    for idx in range(0, len_BSnode):
        BSnodeName = lst_BSnode[idx]
        JUN_cmd_keyEverytgt_for_single_BSnode(BSnodeName)

def JUN_is_mesh(obj_name):
    if not cmds.objExists(obj_name):
        cmds.warning(f"Object '{obj_name}' does not exist.")
        return False

    # Get the shape node if it's a transform
    shapes = cmds.listRelatives(obj_name, shapes=True, fullPath=True) or []
    
    for shape in shapes:
        if cmds.objectType(shape) == 'mesh':
            return True

    # Direct check (in case it's already a shape)
    if cmds.objectType(obj_name) == 'mesh':
        return True

    return False


def JUN_cmd_CopyEveryTgt_and_visOff_for_single_BSnode(BS_node_name):
    lst_tgtName = JUN_get_blendshape_targets(BS_node_name)
    lst_connected = cmds.listHistory(BS_node_name, future = True)
    obj_base = ""
    lst_dup_tgt = []

    for member_obj in lst_connected:
        if JUN_is_mesh(member_obj):
            obj_base = member_obj

    for idx, member_tgtName in enumerate(lst_tgtName):
        cmds.currentTime(idx, edit=True)
        obj_dup = cmds.duplicate(obj_base)
        cmds.setAttr(obj_dup[0] + ".visibility", False)
        obj_dup = cmds.rename(obj_dup, member_tgtName)
        lst_dup_tgt.append(obj_dup)

    cmds.group( lst_dup_tgt, world=True, name='worldGroup')


def JUN_cmd_CopyEveryTgt_and_visOff(BSnode_tsl):
    lst_BSnode = cmds.textScrollList(BSnode_tsl, q=True, allItems=True)
    len_BSnode = len(lst_BSnode)

    for idx in range(0, len_BSnode):
        BSnodeName = lst_BSnode[idx]
        JUN_cmd_CopyEveryTgt_and_visOff_for_single_BSnode(BSnodeName)

def JUN_cmd_CopyEveryTgt(BSnode_tsl):
    JUN_cmd_keyEveryTgt(BSnode_tsl)
    JUN_cmd_CopyEveryTgt_and_visOff(BSnode_tsl)


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_BSTool ():
    str_winTitle = "Blendshape Tool";
    str_winName = "Junny_win_BS_Tools";
    win_width = 480;
    win_height = 900;

    color_mainDark = [0.0, 0.2, 0.0];
    color_main = [0.3, 0.65, 0.2];
    color_sub = [0.3, 0.6, 0.1];
    color_btn = [0.95, 0.7, 0.5];
    color_back = [0.96, 0.96, 0.96];
    color_white = [1.0, 1.0, 1.0];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="BS Tool V01.01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 30-JLY-2025\')".format(color_main)

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

    cmds.textScrollList("JUN_connectBS_source_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_connectBS_source_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_connectBS_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_connectBS_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_connectBS_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_connectBS_source_tsl\", \"JUN_connectBS_source_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )

    # rowLayout : command tsl (open)
    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_toolSel_base", 
                 label='Select Source', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_connectBS_source_tsl\", \"JUN_connectBS_source_selNum\")');

    cmds.setParent( '..' )
    cmds.rowLayout( numberOfColumns=1 );
                 
    cmds.button( "name_btn_sortBase",
                 label='Sort source', 
                 width=win_width/2-15,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_connectBS_source_tsl\")');
    # rowLayout : command tsl (close)
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    cmds.setParent( '..' )


    #------------------------------------------------------------------
    # columnLayout : Source's atttribute (open)                                             

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

   
    cmds.text( "JUN_name_tootSelTgt_selNum", align="left", label='Number:0' );

    cmds.textScrollList("JUN_connectBS_attr_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True)

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_connectBS_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_connectBS_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_connectBS_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_connectBS_attr_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )
    
    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_getAttr_base", 
                 label='List attributes', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_getAttr_btn(\"JUN_connectBS_source_tsl\", \"JUN_connectBS_attr_tsl\")');

    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns=2 );

    cmds.text( label='Search token : ', align = 'left' ,width=win_width/4-30);    
    cmds.textField( 'name_search_tf', bgc=color_white, width=win_width/4-15)
    cmds.textField( 'name_search_tf', edit = True,  enterCommand= 'JUN_cmd_search_btn(\"JUN_connectBS_attr_tsl\", \"name_search_tf\")')

    cmds.setParent( '..' )


    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_search_base", 
                 label='Search', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_search_btn(\"JUN_connectBS_attr_tsl\", \"name_search_tf\")');

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

    cmds.frameLayout( label=' Destination', collapsable= True, bgc =color_main );


    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    #                                                                                   
    
    cmds.paneLayout( configuration= "vertical2" )

    #------------------------------------------------------------------
    # columnLayout : Select Base (open)                                          

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    
    
    

    cmds.text( "JUN_connectBS_dist_selNum", align="left", label='Number:0' );     

    cmds.textScrollList("JUN_connectBS_dist_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_connectBS_dist_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_connectBS_dist_tsl\", \"JUN_connectBS_dist_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_connectBS_dist_tsl\", \"JUN_connectBS_dist_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_connectBS_dist_tsl\", \"JUN_connectBS_dist_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_connectBS_dist_tsl\", \"JUN_connectBS_dist_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )

    # rowLayout : command tsl (open)
    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_toolSel_base", 
                 label='Select Distination', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_connectBS_dist_tsl\", \"JUN_connectBS_dist_selNum\")');

    cmds.setParent( '..' )
    cmds.rowLayout( numberOfColumns=1 );
                 
    cmds.button( "name_btn_sortBase",
                 label='Sort Distination', 
                 width=win_width/2-15,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_connectBS_dist_tsl\")');

    # rowLayout : command tsl (close)
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    cmds.setParent( '..' )


    #------------------------------------------------------------------
    # columnLayout : Source's atttribute (open)                                             

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.rowLayout( numberOfColumns=2 );

    cmds.text( label='Target index : ', align = 'left' ,width=win_width/4-30);    
    cmds.textField( 'name_tgtIdx_tf', bgc=color_white, width=win_width/4-15, text="0" )

    cmds.setParent( '..' )


    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_connectTgt_base", 
                 label='Connect', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_connectTgt_btn(\"JUN_connectBS_source_tsl\", \"JUN_connectBS_attr_tsl\" , \"JUN_connectBS_dist_tsl\", \"name_tgtIdx_tf\")');

    cmds.setParent( '..' )

    # Shader Endgine(SG) Tool (close)                                            
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    # paneLayout : vertical2(close)                                                     
    #==============================================================================
    cmds.setParent( '..' )


    cmds.setParent( '..' )

   #===================================================================================
    # UI: Colum Layout(close)
    # connect BS
    #===================================================================================
    cmds.setParent( '..' )

    #===================================================================================
    # UI: Colum Layout(open)
    # edit BS
    #===================================================================================
    tab_editBS = cmds.columnLayout(adjustableColumn=True, 
                                    columnAttach=('both', 5), 
                                    rowSpacing=6, 
                                    bgc =color_mainDark, 
                                    width = 390 )

    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    #                                                                                   
    
    cmds.paneLayout( configuration= "vertical2" )

    #------------------------------------------------------------------
    # columnLayout : Select Base (open)                                          

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    
    
    

    cmds.text( "JUN_BSnode_selNum", align="left", label='Number:0' );     

    cmds.textScrollList("JUN_BSnode_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_BSnode_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_BSnode_tsl\", \"JUN_BSnode_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_BSnode_tsl\", \"JUN_BSnode_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_BSnode_tsl\", \"JUN_BSnode_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_BSnode_tsl\", \"JUN_BSnode_selNum\" )' );
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )

    # rowLayout : command tsl (open)
    cmds.rowLayout( numberOfColumns=1 );

    cmds.button( "name_btn_toolSel_base", 
                 label='Select Distination', 
                 width=win_width/2-15,
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"JUN_BSnode_tsl\", \"JUN_BSnode_selNum\")');

    cmds.setParent( '..' )
    cmds.rowLayout( numberOfColumns=1 );
                 
    cmds.button( "name_btn_sortBase",
                 label='Sort Distination', 
                 width=win_width/2-15,
                 bgc =color_btn, 
                 command='JUN_cmd_sort(\"JUN_BSnode_tsl\")');

    # rowLayout : command tsl (close)
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    # columnLayout : Select Base (close)                                         
    cmds.setParent( '..' )


    #------------------------------------------------------------------
    # columnLayout : Source's atttribute (open)                                             

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    # cmds.rowLayout( numberOfColumns=1 );
    # cmds.setParent( '..' )

    cmds.button( "name_btn_keyEveryTgt", 
                 label='Key every target', 
                 width=win_width/2-30,
                 bgc=color_btn, 
                 command='JUN_cmd_keyEveryTgt(\"JUN_BSnode_tsl\")');
                 
                 
    cmds.button( "name_btn_CopyEveryTgt", 
                 label='Copy every target', 
                 width=win_width/2-30,
                 bgc=color_btn, 
                 command='JUN_cmd_CopyEveryTgt(\"JUN_BSnode_tsl\")');


    # Shader Endgine(SG) Tool (close)                                            
    #------------------------------------------------------------------
    cmds.setParent( '..' )

    # paneLayout : vertical2(close)                                                     
    #==============================================================================
    cmds.setParent( '..' )


    cmds.setParent( '..' )
    #===================================================================================
    # UI: Colum Layout(open)
    # edit BS
    #===================================================================================

    
    cmds.setParent( '..' )


    cmds.tabLayout( tab_all, edit=True, tabLabel=((tab_connectBS, 'Connect BS'), (tab_editBS, 'Edit BS')))

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );


    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_BSTool_V01_01():
    PY_JUN_makeUI_BSTool();

PY_JUN_makeUI_BSTool();