# 21_08_19 ripple cubes 338

import maya.cmds as cmds
import random, math

def get_dist(pos1, pos2):
    x1, y1, z1 = pos1
    x2, y2, z2 = pos2

    dist = math.sqrt(
        math.pow(x1 - x2, 2) +
        math.pow(y1 - y2, 2) +
        math.pow(z1 - z2, 2)
    )k

    return dist

dist_cube = 1.3

for x in range(20):
    for z in range(20):
        box = cmds.polyCube(height = 1, width = 1, depth = 1)
        cmds.move((x - 9) * dist_cube, 0, (z - 9) * dist_cube, box[0])

def ripple(time_):
    for obj in cmds.ls("pCube*", type = "transform"):
        pos = cmds.xform(obj, worldSpace = True, translation = True, query = True)
        pos[1] = 0
        dist_from_origin = get_dist([0, 0, 0], pos)
        move_y = math.sin(dist_from_origin * 0.5 + time_*50) * 2
        cmds.move(move_y, obj, moveY = True)