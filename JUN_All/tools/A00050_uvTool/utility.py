import maya.cmds as cmds;
import maya.mel as mel
import copy, os
from functools import partial


def JUN_cmd_set_object_for_uv(*args, **kwargs):
    name_tsl_uvTool_main__ = kwargs.get("tsl_uvTool_main")
    lst_object_to_fix = []

    all_meshes = cmds.ls(type='mesh')

    for i in range(0, len(all_meshes)):
        cmds.select(all_meshes[i])
        lst_uvSets_origin = cmds.polyUVSet(q=True, allUVSets=True)

        if len(lst_uvSets_origin) >= 2:
            mesh_transform = cmds.listRelatives(all_meshes[i], parent=True)[0]
            lst_object_to_fix.append(mesh_transform)
    cmds.select(clear=True)
    name_tsl_uvTool_main__.JUN_cmd_append_tsl(lst_object_to_fix)
    name_tsl_uvTool_main__.select_all_in_tsl()

def JUN_cmd_rename_uvSet(*args, **kwargs):
    objs = cmds.ls(sl = True, fl= True)
    lst_origin_uvSets = []
    lst_new_uvSets = []

    if objs is None:
        name_tsl_uvTool_main__ =  kwargs.get("tsl_uvTool_main")
        objs =  name_tsl_uvTool_main__.get_all_item()
        
    for i in range(len(objs)):
        cmds.select(objs[i])
        lst_uvSets_origin = cmds.polyUVSet(q=True, allUVSets=True)

        lst_origin_uvSets.append(objs[i] + " : " + " ".join(lst_uvSets_origin))
        try :
            cmds.polyUVSet(rename=True,newUVSet="map1", uvSet=lst_uvSets_origin[0])
        except:
            pass
        lst_uvSets_new = cmds.polyUVSet(q=True, allUVSets=True)
        lst_new_uvSets.append(objs[i] + " : " + " ".join(lst_uvSets_new))

    str_origin_uvSets = "\n".join(lst_origin_uvSets)
    str_new_uvSets = "\n".join(lst_new_uvSets)
    print(str_origin_uvSets)
    print("COMPLETE")
    print(str_new_uvSets)
