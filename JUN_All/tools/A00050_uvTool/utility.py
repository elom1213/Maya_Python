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
