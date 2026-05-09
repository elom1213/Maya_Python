import maya.cmds as cmds;
from functools import partial


#===========================================================================
# Example set up in other class
# import JUN_PY_MOD_tsl_01_01 as JUN_module_tsl

class ExampleClass:
    def __init__(self):
        self.color_mainDark = [0.10, 0.12, 0.18]
        self.color_main     = [0.14, 0.17, 0.25]
        self.color_sub      = [0.18, 0.22, 0.32]
        self.color_btn      = [0.30, 0.35, 0.45]
        self.color_back     = [0.12, 0.14, 0.20]

        self_color_all = {  "color_mainDark" : self.color_mainDark, 
                            "color_main" : self.color_main, 
                            "color_sub" : self.color_sub, 
                            "color_btn" : self.color_btn, 
                            "color_back" : self.color_back }

        # set module : tsl(open)

        self.mod_tsl_from = JUN_module_tsl.JUN_mod_tsl_v01()
        self.mod_tsl_to__ = JUN_module_tsl.JUN_mod_tsl_v01()

        self.name_tsl_from = "tsl_moveSkinWeight_from"
        self.name_tsl_to__ = "tsl_moveSkinWeight_to__"

        self.tsl_spec_from  = { "name_tsl" : self.name_tsl_from,
                                "name_title" : "From",
                                "num_item" : "num_from",
                                **self_color_all,
                                **self.win_all_for_mod_tsl }
        self.tsl_spec_to__  = { "name_tsl" : self.name_tsl_to__,
                                "name_title" : "To",
                                "num_item" : "num_to",
                                **self_color_all,
                                **self.win_all_for_mod_tsl}

        self.mod_tsl_from.set__(self.tsl_spec_from)
        self.mod_tsl_to__.set__(self.tsl_spec_to__)

        # set module : tsl(close)
#===========================================================================

class JUN_mod_tsl_v01:
    def __init__(self):
        self.name_tsl = "tsl_name_default"
        self.name_toolSelTgt_selNum = "selNum_deault"
        self.tsl_title = "tsl_title"
        
        self.color_mainDark = [0.10, 0.12, 0.18]
        self.color_main     = [0.14, 0.17, 0.25]
        self.color_sub      = [0.18, 0.22, 0.32]
        self.color_btn      = [0.30, 0.35, 0.45]
        self.color_back     = [0.12, 0.14, 0.20]

        self.win_height = 100
        self.win_width = 100
    
    def set__(self, tsl_spec):
        self.name_tsl = tsl_spec.get("name_tsl", "tsl_name_default")
        self.tsl_title = tsl_spec.get("name_title", "tsl_title")
        self.name_toolSelTgt_selNum = tsl_spec.get("num_item", "num_item_defulat")

        self.color_mainDark = tsl_spec.get("color_mainDark", [0.0, 0.0, 0.0])
        self.color_main = tsl_spec.get("color_main", [0.0, 0.0, 0.0])
        self.color_sub = tsl_spec.get("color_sub", [0.0, 0.0, 0.0])
        self.color_btn = tsl_spec.get("color_btn", [0.0, 0.0, 0.0])
        self.color_back = tsl_spec.get("color_back", [0.0, 0.0, 0.0])

        self.win_height = tsl_spec.get("window_height", self.win_height)
        self.win_width = tsl_spec.get("window_width", self.win_width)

    def JUN_cmd_sort(self, str_name_tsl_input, *args):
        str_list_tsl = cmds.textScrollList(str_name_tsl_input, q = 1, allItems=1);
        str_list_sorted = sorted(str_list_tsl);
        cmds.textScrollList(str_name_tsl_input, e=1, removeAll=1);
        cmds.textScrollList(str_name_tsl_input, e=1, append=str_list_sorted);

    def JUN_cmd_append_tsl(self, 
                           lst_to_append = [], 
                           *args):

        cmds.textScrollList( self.name_tsl, e=True, removeAll=True );
        cmds.textScrollList( self.name_tsl, e=True, append = lst_to_append );
        
        int_numItem = cmds.textScrollList( self.name_tsl, q=True, numberOfItems=True );

        cmds.text( self.name_toolSelTgt_selNum, e=True, label= 'Number: ' + str(int_numItem) );
    
    def JUN_cmd_toolSel_btn ( self, str_selTool_tsl_selList, str_selTool_t_selNum,*args ):

        str_selList = cmds.ls ( sl=True, fl=True );

        self.JUN_cmd_append_tsl(str_selList, *args)

        # cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
        # cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList );
        
        # int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
        
        # cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );
    
    def JUN_cmd_tsl_select ( self, str_selTool_tsl_selList, *args ):

        str_scrollList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True );
        
        cmds.select ( str_scrollList );


    #===================================================================================
    # tsl edit funcionts Detail
    #===================================================================================

    def BF_LIST_moveUp_index ( self, str_inputList, int_moveIndexList, *args ):

        int_resultIndexList = [];

        for i in range( 0, len(int_moveIndexList) ):
        
            str_move = str_inputList.pop( int_moveIndexList[i]-1 );    
            str_inputList.insert( int_moveIndexList[i]-1 - 1, str_move );

            int_resultIndexList.append(int_moveIndexList[i]-1);
        
        return [ str_inputList, int_resultIndexList ];


    def BF_LIST_moveDown_index ( self, str_inputList, int_moveIndexList, *args ):

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


    def CMD_ToolSel_b_add ( self, str_selTool_tsl_selList, str_selTool_t_selNum, *args ):

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


    def CMD_ToolSel_b_del ( self, str_selTool_tsl_selList, str_selTool_t_selNum, *args ):

        str_scrollList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True );

        cmds.textScrollList( str_selTool_tsl_selList, e=True, removeItem = str_scrollList );

        int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
        
        cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) ); 


    def CMD_ToolSel_b_up ( self, str_selTool_tsl_selList, str_selTool_t_selNum, *args ):


        str_allItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, allItems=True          );
        str_selItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True        );
        str_selItemIndexList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectIndexedItem=True );
                
        str_moveIndexList = self.BF_LIST_moveUp_index (  str_allItemList, str_selItemIndexList );
    
        
        cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True ); 
        cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_moveIndexList[0] );       
                
        for i in range( 0, len(str_moveIndexList[1]) ):
        
            cmds.textScrollList( str_selTool_tsl_selList, e=True, selectIndexedItem = str_moveIndexList[1][i] ); 
            
            
    def CMD_ToolSel_b_down ( self, str_selTool_tsl_selList, str_selTool_t_selNum, *args ):


        str_allItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, allItems=True          );
        str_selItemList      = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectItem=True        );
        str_selItemIndexList = cmds.textScrollList( str_selTool_tsl_selList, q=True, selectIndexedItem=True );

        
        str_moveIndexList = self.BF_LIST_moveDown_index (  str_allItemList, str_selItemIndexList );
    
        
        cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True ); 
        cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_moveIndexList[0] );       
                
        for i in range( 0, len(str_moveIndexList[1]) ):
            cmds.textScrollList( str_selTool_tsl_selList, e=True, selectIndexedItem = str_moveIndexList[1][i]+1 ); 
    
    def get_objs_num(self):
        return cmds.textScrollList( self.name_tsl, q=True, numberOfItems=True );

    def get_indexed_item(self, idx):
        cmds.textScrollList( self.name_tsl, e=True, selectIndexedItem = idx)
        selected__ = cmds.textScrollList( self.name_tsl, q=True, selectItem = True)[0]
        cmds.textScrollList( self.name_tsl, e=True, deselectAll = True)
        return selected__
    
    def build(self):
        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.button( self.name_tsl,
                     label='Select Objects',
                     bgc =self.color_btn,
                     command=partial(self.JUN_cmd_toolSel_btn, self.name_tsl, self.name_toolSelTgt_selNum));
        

        # cmds.rowLayout( numberOfColumns=2 , columnWidth2= [self.win_width/2-3, self.win_width/2-3])
        cmds.rowLayout( numberOfColumns=2 )

        cmds.text( align="left", font = "boldLabelFont",  label=self.tsl_title, width = self.win_width * 0.3 );
        cmds.text( self.name_toolSelTgt_selNum, align="right", label='Number:0' , width = self.win_width * 0.3);

        cmds.setParent( '..' )

        cmds.textScrollList(self.name_tsl, 
                            height = (self.win_height*0.45),
                            numberOfRows=15, 
                            allowMultiSelection=True, 
                            selectCommand=partial(self.JUN_cmd_tsl_select, self.name_tsl));

        # rowLayout : edit tsl (open)
        cmds.rowLayout( numberOfColumns=4 );

        cmds.button( "NAM_toolSelTgt_b_add",  width= self.win_width/4 - 10, label='Add', bgc = self.color_btn, command=partial(self.CMD_ToolSel_b_add , self.name_tsl, self.name_toolSelTgt_selNum));
        cmds.button( "NAM_toolSelTgt_b_del",  width= self.win_width/4 - 10, label='Del', bgc = self.color_btn, command=partial(self.CMD_ToolSel_b_del , self.name_tsl, self.name_toolSelTgt_selNum));
        cmds.button( "NAM_toolSelTgt_b_up",   width= self.win_width/4 - 10, label='Up',  bgc = self.color_btn, command=partial(self.CMD_ToolSel_b_up  , self.name_tsl, self.name_toolSelTgt_selNum));
        cmds.button( "NAM_toolSelTgt_b_down", width= self.win_width/4 - 5, label='Down',bgc = self.color_btn, command=partial(self.CMD_ToolSel_b_down, self.name_tsl, self.name_toolSelTgt_selNum));


        cmds.setParent( '..' )

        cmds.button( "name_btn_sortBase",
                 label='Sort', 
                 width=self.win_width/2-10,
                 bgc =self.color_btn, 
                 command=partial(self.JUN_cmd_sort, self.name_tsl));

        # rowLayout : edit tsl (close)
        cmds.setParent( '..' )
