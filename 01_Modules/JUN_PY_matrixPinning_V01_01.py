# last Update date 25 09 22
# Python Script by Ji Hun Park

# Matrix Pinning Tool v01.00

# refernce 
# https://rigmarolestudio.com/matrix-pinning-to-surface-in-maya/




import maya.cmds as cmds;
import pymel.core as pm

'''
Author: Chris Lesage, https://rigmarolestudio.com
A script snippet for pinning an object to a nurbs surface in Autodesk Maya.
This results in a surface pin, much like a follicle, but I've found
follicles to be less stable, sometimes flipping since Maya 2018 or so. Details in this thread:
https://tech-artists.org/t/flipping-follicles-in-ribbon-ik/11022/10?u=clesage
sourceObj is an optional parameter. If you pass a PyNode object, it will place the "follicle"
as close to the object as possible. Otherwise, you can specify U and V coordinates.
'''


def pin_to_surface(oNurbs, sourceObj=None, uPos=0.5, vPos=0.5):
    """
    This function replaces what I used to use follicles for.
    It pins an object to a surface's UV coordinates.
    In rare circumstances follicles can flip and jitter. This seems to solve that.
    
    1. oNurbs is the surface you want to pin to.
    Pass a PyNode transform, NurbsSurface or valid string name.
    2. sourceObj is an optional reference transform. If specified the UV coordinates
    will be placed as close as possible. Otherwise, specify U and V coordinates.
    Pass a PyNode transform, shape node or valid string name.
    3. uPos and vPos can be specified, and default to 0.5
    """
    
    #TODO: Can I support polygons?
    # Parse whether it is a nurbsSurface shape or transform
    if type(oNurbs) == str and pm.objExists(oNurbs):
        oNurbs = pm.PyNode(oNurbs)
    if type(oNurbs) == pm.nodetypes.Transform:
        pass
    elif type(oNurbs) == pm.nodetypes.NurbsSurface:
        oNurbs = oNurbs.getTransform()
    elif type(oNurbs) == list:
        pm.warning('Specify a NurbsSurface, not a list.')
        return False
    else:
        pm.warning('Invalid surface object specified.')
        return False
    
    pointOnSurface = pm.createNode('pointOnSurfaceInfo')
    oNurbs.getShape().worldSpace.connect(pointOnSurface.inputSurface)
    # follicles remap from 0-1, but closestPointOnSurface must take minMaxRangeV into account
    paramLengthU = oNurbs.getShape().minMaxRangeU.get()
    paramLengthV = oNurbs.getShape().minMaxRangeV.get()

    if sourceObj:
        # Place the follicle at the position of the sourceObj
        # Otherwise use the UV coordinates passed in the function
        if isinstance(sourceObj, str) and pm.objExists(sourceObj):
            sourceObj = pm.PyNode(sourceObj)
        if isinstance(sourceObj, pm.nodetypes.Transform):
            pass
        elif isinstance(sourceObj, pm.nodetypes.Shape):
            sourceObj = sourceObj.getTransform()
        elif type(sourceObj) == list:
            pm.warning('sourceObj should be a transform, not a list.')
            return False
        else:
            pm.warning('Invalid sourceObj specified.')
            return False        
        oNode = pm.createNode('closestPointOnSurface', n='ZZZTEMP')
        oNurbs.worldSpace.connect(oNode.inputSurface, force=True)
        oNode.inPosition.set(sourceObj.getTranslation(space='world'))
        uPos = oNode.parameterU.get()
        vPos = oNode.parameterV.get()
        pm.delete(oNode)

    pName = '{}_foll#'.format(oNurbs.name())
    result = pm.spaceLocator(n=pName).getShape()
    result.addAttr('parameterU', at='double', keyable=True, dv=uPos)
    result.addAttr('parameterV', at='double', keyable=True, dv=vPos)
    # set min and max ranges for the follicle along the UV limits.
    result.parameterU.setMin(paramLengthU[0])
    result.parameterV.setMin(paramLengthV[0])
    result.parameterU.setMax(paramLengthU[1])
    result.parameterV.setMax(paramLengthV[1])
    result.parameterU.connect(pointOnSurface.parameterU)
    result.parameterV.connect(pointOnSurface.parameterV)
    
    # Compose a 4x4 matrix
    mtx = pm.createNode('fourByFourMatrix')
    outMatrix = pm.createNode('decomposeMatrix')
    mtx.output.connect(outMatrix.inputMatrix)
    outMatrix.outputTranslate.connect(result.getTransform().translate)
    outMatrix.outputRotate.connect(result.getTransform().rotate)

    '''
    Thanks to kiaran at https://forums.cgsociety.org/t/rotations-by-surface-normal/1228039/4
    # Normalize these vectors
    [tanu.x, tanu.y, tanu.z, 0]
    [norm.x, norm.y, norm.z, 0]
    [tanv.x, tanv.y, tanv.z, 0]
    # World space position
    [pos.x, pos.y, pos.z, 1]
    '''

    pointOnSurface.normalizedTangentUX.connect(mtx.in00)
    pointOnSurface.normalizedTangentUY.connect(mtx.in01)
    pointOnSurface.normalizedTangentUZ.connect(mtx.in02)
    mtx.in03.set(0)

    pointOnSurface.normalizedNormalX.connect(mtx.in10)
    pointOnSurface.normalizedNormalY.connect(mtx.in11)
    pointOnSurface.normalizedNormalZ.connect(mtx.in12)
    mtx.in13.set(0)

    pointOnSurface.normalizedTangentVX.connect(mtx.in20)
    pointOnSurface.normalizedTangentVY.connect(mtx.in21)
    pointOnSurface.normalizedTangentVZ.connect(mtx.in22)
    mtx.in23.set(0)

    pointOnSurface.positionX.connect(mtx.in30)
    pointOnSurface.positionY.connect(mtx.in31)
    pointOnSurface.positionZ.connect(mtx.in32)
    mtx.in33.set(1)
    
    return result


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

def JUN_cmd_SelTool_toolSel_btn (str_selTool_tsl_selList, 
                                 str_selTool_t_selNum ):

    str_selList = cmds.ls ( sl=True, fl=True );
    
    cmds.textScrollList( str_selTool_tsl_selList, e=True, removeAll=True );
    cmds.textScrollList( str_selTool_tsl_selList, e=True, append = str_selList );
    
    int_numItem = cmds.textScrollList( str_selTool_tsl_selList, q=True, numberOfItems=True );
    
    cmds.text( str_selTool_t_selNum, e=True, label= 'Number: ' + str(int_numItem) );

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
# start (JUN_cmd_select_nurbs_surface)

def JUN_cmd_select_nurbs_surface(name_rig_name_tsl):

    str_selList = cmds.ls ( sl=True, fl=True );

    str_fkik_objChild = set();
    cmds.textScrollList( name_rig_name_tsl, e=True, removeAll=True );
    for str_selItem in str_selList :
        cmds.textScrollList( name_rig_name_tsl, e=True, append = str_selItem );



# end (JUN_cmd_select_nurbs_surface)
#===================================================================================

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
    
def JUN_cmd_pinOnClosestObjs(JUN_MatPinSfc_tsl, JUN_MatrixPinning_closestObj_tsl):
    str_sfcs = cmds.textScrollList(JUN_MatPinSfc_tsl , q=True, allItems=True)
    str_objs = cmds.textScrollList(JUN_MatrixPinning_closestObj_tsl , q=True, allItems=True)
    plane_name = str_sfcs[0]

    for i in range(0, len(str_objs)):
        pin_to_surface(pm.PyNode(plane_name), sourceObj=str_objs[i])


def JUN_cmd_pinOnSfc_byNumObj(JUN_MatPinSfc_tsl, JUN_MatPin_ifg_numObjs):
    str_sfcs = cmds.textScrollList(JUN_MatPinSfc_tsl , q=True, allItems=True)
    numberOfFollicles = cmds.intFieldGrp(JUN_MatPin_ifg_numObjs, q=True, value1=True);

    plane_name = str_sfcs[0]
    paramLengthU = pm.PyNode(plane_name).getShape().minMaxRangeU.get()

    for i in range(numberOfFollicles):
        uPos = (i/float(numberOfFollicles-1)) * paramLengthU[1]
        pin_to_surface(plane_name, uPos=uPos, vPos=0.5)


#===================================================================================
#===================================================================================
# UI : All Window
#===================================================================================
#===================================================================================

def PY_JUN_makeUI_MatrixPinningTool():
    str_winTitle = "Matrix Pinning Tool";
    str_winName = "Junny_win_MatrixPinningTool";
    win_width = 380;
    win_height = 430;

    # color_mainDark = [0.652, 0.363, 0.363];
    color_mainDark = [0.1, 0.15, 0.45]   
    color_main     = [0.0, 0.45, 0.75]   
    color_sub      = [0.4, 0.7, 0.9]     
    color_btn      = [0.7, 0.9, 1.0]     
    color_back     = [0.85, 0.95, 1.0]   
    if cmds.window( str_winName , exists=True ): cmds.deleteUI( str_winName , window=True );
    
    # window

    cmds.window( str_winName, bgc=color_mainDark, title="Matrix Pinning Tool V01" );
        
    #------------------------------------------------------------------
    # UI: MenuBar
    #------------------------------------------------------------------

    cmds.menuBarLayout (bgc=color_mainDark); 
    
    menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 22-SEP-2025\')".format(color_main)

    cmds.menu( label='Help' );
    cmds.menuItem( label='About', command = menu_cmd);
    

    #===================================================================================
    # UI: Colum Layout(open)
    #===================================================================================
    
    cmds.columnLayout(adjustableColumn=True, 
                      columnAttach=('both', 5),
                      rowSpacing=6, 
                      bgc =color_mainDark, 
                      width = 360 );
         
    #===================================================================================
    # frameLayout : Tool  Setup select nurbs surface (open)
    #===================================================================================
    
    cmds.frameLayout( label='Select nurbs surface', collapsable= True, bgc =color_main );

    #==============================================================================
    # paneLayout : vertical2(open)                                                      
    # 

    #rowLayout : Select Rig (close)
    cmds.rowLayout(numberOfColumns=2);


    cmds.textScrollList("JUN_MatPinSfc_tsl", 
                        height = (30),
                        numberOfRows=1, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_MatPinSfc_tsl\")');

    cmds.button( "name_btn_setup_rig_name",
                 label='Select Objects',
                 bgc =color_btn,
                 command='JUN_cmd_select_nurbs_surface(\"JUN_MatPinSfc_tsl\")');


    #rowLayout : Select Rig (close)
    cmds.setParent( '..' )

    #===================================================================================
    # frameLayout : Tool  Setup select nurbs surface (close)
    #===================================================================================
    cmds.setParent( '..' )

    # paneLayout : vertical2(open)                                                      
    
    #------------------------------------------------------------------
    # columnLayout : closest objects (open)                                         

    cmds.frameLayout( label='Closest Object', collapsable= True, bgc =color_main );

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.button( "name_btn_toolSel_Objects",
                 label='Select Objects',
                 bgc =color_btn,
                 command='JUN_cmd_SelTool_toolSel_btn(\"JUN_MatrixPinning_closestObj_tsl\", \"JUN_name_tootSelTgt_selNum\")');

    cmds.text( "JUN_name_tootSelTgt_selNum", align="left", label='Number:0' );
    
    cmds.textScrollList("JUN_MatrixPinning_closestObj_tsl", 
                        height = (win_height*0.25),
                        numberOfRows=15, 
                        allowMultiSelection=True, 
                        selectCommand='JUN_cmd_tsl_select(\"JUN_MatrixPinning_closestObj_tsl\")');

    # rowLayout : edit tsl (open)
    cmds.rowLayout( numberOfColumns=4 );

    cmds.button( "NAM_toolSelTgt_b_add",  width= win_width/4 - 5, label='Add', bgc =color_btn, command='CMD_ToolSel_b_add  ( \"JUN_MatrixPinning_closestObj_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_del",  width= win_width/4 - 5, label='Del', bgc =color_btn, command='CMD_ToolSel_b_del  ( \"JUN_MatrixPinning_closestObj_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_up",   width= win_width/4 - 5, label='Up',  bgc =color_btn, command='CMD_ToolSel_b_up   ( \"JUN_MatrixPinning_closestObj_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );
    cmds.button( "NAM_toolSelTgt_b_down", width= win_width/4 - 5, label='Down',bgc =color_btn, command='CMD_ToolSel_b_down ( \"JUN_MatrixPinning_closestObj_tsl\", \"JUN_name_tootSelTgt_selNum\" )' );


    cmds.setParent( '..' )

    cmds.button( "name_btn_pinOnClosestObjs",
                 label='Pin to object',
                 bgc =color_btn,
                 command=lambda *argv : JUN_cmd_pinOnClosestObjs("JUN_MatPinSfc_tsl", "JUN_MatrixPinning_closestObj_tsl") )
    
    # rowLayout : edit tsl (close)
    cmds.setParent( '..' )
    
    # columnLayout (close)                                            
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
    # frameLayout : create by number (open)                                                        
    #===================================================================================

    cmds.frameLayout( label='Create by number', collapsable= True, bgc =color_main );

    cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =color_sub );

    cmds.text( "JUN_name_numObjs", align="left", label='number of objects' );

    cmds.intFieldGrp( 'JUN_MatPin_ifg_numObjs', 
                        columnAlign = [1, 'right'], 
                        columnWidth2 = [ 100, 280 ]);    
    
    cmds.button( "name_btn_pinOnSfc_byNumObjs", 
                 label='Pin by given number', 
                 bgc=color_btn, 
                 command= lambda *argv : JUN_cmd_pinOnSfc_byNumObj("JUN_MatPinSfc_tsl","JUN_MatPin_ifg_numObjs"))
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

    cmds.showWindow(str_winName);
    cmds.window(str_winName, e = True, widthHeight = [win_width, win_height]);
    
def JUN_PY_MatrixPinningTool_V01_01():
    PY_JUN_makeUI_MatrixPinningTool();

JUN_PY_MatrixPinningTool_V01_01();