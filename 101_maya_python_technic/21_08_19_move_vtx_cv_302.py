# 21_08_19 move vertex and control vertex by cmds.move

import maya.cmds as cmds
import random

sel_objs = cmds.ls(sl = True)
random_range = (-1, 1)

for sel_obj in sel_objs:
    shape_node_type = cmds. nodeType(cmds.listRelatives(sel_obj, shapes = True)[0])
    if shape_node_type == 'mesh':
        vtx_count = cmds.polyEvaluate(sel_obj, vertex = True)
        for num_vtx in range(vtx_count):
            x = random.uniform(*random_range)
            y = random.uniform(*random_range)
            z = random.uniform(*random_range)

            cmds.move(x, y, z, '%s.vtx[%s]' % (sel_obj, num_vtx), relative = True)