# last Update date 26 04 04
# Python Script by Ji Hun Park

# Naming Tool V03.04
# 03.02 update padding zero rules
# 03.03 rename start function name
# 03.04 remove shapes node in childern's list

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

def JUN_cmd_rename_for_dyn_02(str_NamingDyn_tsl, 
                            namingDyn_tf_dyn, 
                            namingDyn_tf_asset,
                            namingDyn_tf_sid,
                            namingDyn_tf_index_01,
                            namingDyn_tf_index_02,
                            mmx_pad_tf_tokenManual_01,
                            mmx_pad_tf_tokenManual_02):
    use_manual_padding = True

    list_objs = cmds.textScrollList( str_NamingDyn_tsl, q=True, allItems=True);

    str_dyn     = cmds.textField( namingDyn_tf_dyn, q=True, text = True  );    
    str_ast     = cmds.textField( namingDyn_tf_asset, q=True, text = True  );    
    str_sid     = cmds.textField( namingDyn_tf_sid, q=True, text = True  );    
    str_idx_01  = cmds.textField( namingDyn_tf_index_01, q=True, text = True  );    
    str_idx_02  = cmds.textField( namingDyn_tf_index_02, q=True, text = True  );    

    str_mmx_pad_tokenManual_01  = cmds.textField( mmx_pad_tf_tokenManual_01, q=True, text = True  );    
    str_mmx_pad_tokenManual_02  = cmds.textField( mmx_pad_tf_tokenManual_02, q=True, text = True  );    

    int_token_origin_01 = int(str_idx_01);
    int_token_01        = int(str_idx_01);
    int_token_origin_02 = int(str_idx_02);
    int_token_02        = int(str_idx_02);

    int_mmx_pad_tokenManual_01 = int(str_mmx_pad_tokenManual_01)
    int_mmx_pad_tokenManual_02 = int(str_mmx_pad_tokenManual_02)

    list_descds = [];

    len_list_tsl = len(list_objs);

    for idx_list in range(0, len_list_tsl):
        obj_now = list_objs[idx_list];
        list_descd_A = [];
        list_descd_tmp = cmds.listRelatives( obj_now , allDescendents=True)
        list_obj_with_shape = ["transform"]

        if list_descd_tmp is not None:

            if cmds.objectType(obj_now) in list_obj_with_shape:
                list_tmp_02 = list_descd_tmp.copy()
                for idx in range(0, len(list_descd_tmp)):
                    if cmds.objectType(list_descd_tmp[idx]) != "transform":
                        list_tmp_02.remove(list_descd_tmp[idx])
                list_descd_tmp = list_tmp_02

            for descd in list_descd_tmp:
                list_descd_A.append(descd);

        list_descd_A.append(obj_now);

        list_descd_A.reverse();

        list_descds.append(list_descd_A);

    len_descd = len(list_descds);
    mmx_pad_token_01 = len(str(len_descd));


    for idx_descd in range(0, len_descd):
        str_token_01 = 0

        if use_manual_padding == True:
            str_token_01 = get_idx_with_pad(int_mmx_pad_tokenManual_01, int_token_01)
        else:
            str_token_01 = get_idx_with_pad(mmx_pad_token_01, int_token_01)
        
        list_descd_dep_01 = list_descds[idx_descd];

        len_descd_dep_01 = len(list_descd_dep_01);
        max_pad_token_02 = len(str(len_descd_dep_01));

        for idx_descd_dep_01 in range(0, len_descd_dep_01):
            str_token_02 = 0;
            if use_manual_padding == True:
                str_token_02 = get_idx_with_pad(int_mmx_pad_tokenManual_02, int_token_02)
            else:
                str_token_02 = get_idx_with_pad(max_pad_token_02, int_token_02)
            
            list_token = [str_dyn, str_ast, str_sid, str_token_01, str_token_02];

            name_new = get_str_with_space(list_token, "_");
            obj_now = list_descd_dep_01[idx_descd_dep_01];
            cmds.rename(obj_now, name_new);

            int_token_02 += 1;

        int_token_02 = int_token_origin_02;

        int_token_01 += 1;





#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_NamingToolUI ():
    str_winTitle = "Naming Tool";
    str_winName = "Junny_win_Naming_Tools";
    win_width = 480;
    win_height = 480;

    color_mainDark = [0.0, 0.2, 0.0];
    color_main = [0.3, 0.65, 0.2];
    color_sub = [0.3, 0.6, 0.1];
    color_btn = [0.95, 0.7, 0.5];
    color_back = [0.96, 0.96, 0.96];
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="Naming Tool V03.04" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 04-APR-2026\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    
    cmds.columnLayout(adjustableColumn=True, 
                        bgc =color_mainDark, 
                        width = 390 );

    tab_all = cmds.tabLayout();
    #===================================================================================
    # UI: Colum Layout(open)
    # Naming dynamics
    #===================================================================================
    tab_nameingDyn = cmds.columnLayout(adjustableColumn=True, 
                                            columnAttach=('both', 5), 
                                            rowSpacing=6, 
                                            bgc =color_mainDark, 
                                            width = 390 );
    #===================================================================================
    # frameLayout : Tool  Naming dynamic(open)
    #===================================================================================
    
    cmds.frameLayout( label='Tool : Naming dynamics', collapsable= True, bgc =color_main );

    #==============================================================================
    # columnLayout : Naming dynamics (open)                                                      
    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );
    
    
    cmds.button( "name_btn_toolSel_base", 
                 label='Select Base', 
                 bgc=color_btn, 
                 command='JUN_cmd_toolSel_btn(\"name_toolSelBase_NamingDyn_tsl\", \"JUN_name_tootNaingDyn_selNum\")');

    cmds.text( "JUN_name_tootNaingDyn_selNum", align="left", label='Number:0' );     

    cmds.textScrollList("name_toolSelBase_NamingDyn_tsl", 
                        height = (win_height*0.35),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"name_toolSelBase_NamingDyn_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= 40, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"name_toolSelBase_NamingDyn_tsl\", \"JUN_name_tootNaingDyn_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= 40, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"name_toolSelBase_NamingDyn_tsl\", \"JUN_name_tootNaingDyn_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= 40, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"name_toolSelBase_NamingDyn_tsl\", \"JUN_name_tootNaingDyn_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= 40, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"name_toolSelBase_NamingDyn_tsl\", \"JUN_name_tootNaingDyn_selNum\" )' );
   
    cmds.setParent( '..' )
    # rowLayout : edit tsl (close)

    cmds.rowColumnLayout( numberOfColumns=5, 
                            cs=[ (2, 4),(3, 4),(4, 4),(5, 4)], 
                            cw=[ (1,76),(2,76),(3,76),(4,76),(5,76),(6,76),(7,76) ] );

    cmds.text( label=' Token 1', align = 'left' );    
    cmds.text( label=' Token 2', align = 'left' );  
    cmds.text( label=' Token 3', align = 'left' );      
    cmds.text( label=' Index 1', align = 'left' );  
    cmds.text( label=' Index 2', align = 'left' );

    cmds.textField( 'namingDyn_tf_dyn', text = 'dyn');    
    cmds.textField( 'namingDyn_tf_asset', text = 'asset');   
    cmds.textField( 'namingDyn_tf_sid', text = 'side');   
    cmds.textField( 'namingDyn_tf_index_01', text = '0');   
    cmds.textField( 'namingDyn_tf_index_02', text = '0');   
                            
    cmds.text( label='', align = 'left' );    
    cmds.text( label='', align = 'left' );  
    cmds.text( label='', align = 'left' );      
    cmds.text( label='pad 0', align = 'left' );  
    cmds.text( label='pad 0', align = 'left' );

    cmds.text( label='', align = 'left' );    
    cmds.text( label='', align = 'left' );  
    cmds.text( label='', align = 'left' );   
    cmds.textField( 'max_pad_tkn_01', text = '2');   
    cmds.textField( 'max_pad_tkn_02', text = '2');   

    cmds.setParent( '..' )

    cmds.button( 
                    "JUN_namingDyn", 
                    label='Naming dynamics', 
                    bgc = color_btn,
                    command='JUN_cmd_rename_for_dyn_02 ( \"name_toolSelBase_NamingDyn_tsl\", \"namingDyn_tf_dyn\", \"namingDyn_tf_asset\", \"namingDyn_tf_sid\", \"namingDyn_tf_index_01\", \"namingDyn_tf_index_02\", \"max_pad_tkn_01\", \"max_pad_tkn_02\") '                     
                    ); 
   


    cmds.setParent( '..' )
    #==============================================================================
    # columnLayout : Naming dynamics (close)

    cmds.setParent( '..' )
    #===================================================================================
    # frameLayout : Tool  Naming dynamic(close)
    #===================================================================================

    cmds.setParent( '..' )
    #===================================================================================
    # UI: Colum Layout(Close)
    # Naming dynamics
    #===================================================================================

    #===================================================================================
    # UI: Colum Layout(open)
    # Copy name 
    #===================================================================================
    tab_copyName = cmds.columnLayout(adjustableColumn=True, 
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


    cmds.tabLayout( tab_all, edit=True, tabLabel=((tab_copyName, 'Copy name'), (tab_nameingDyn, 'Naming Dyn')));

    cmds.setParent( '..' )

    cmds.setParent( '..' )

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );


    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_NamingTool_V03_04():
    PY_JUN_makeUI_NamingToolUI();

PY_JUN_makeUI_NamingToolUI();