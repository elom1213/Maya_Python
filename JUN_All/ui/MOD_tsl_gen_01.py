import maya.cmds as cmds

def JUN_gen_tsl_select ( str_tsl_selList):

    str_scrollList = cmds.textScrollList( str_tsl_selList, q=True, selectItem=True );
    
    cmds.select ( str_scrollList );