# 21_08_17 random rotation 297

import maya.cmds as cmds
import random

dist = 1.3

for index in range(100):
    rand_mov = random.uniform(0, 10)
    poly = cmds.polyCube(height = (1 + index) - rand_mov)
    cmds.move((-50+index)*dist, 0, 0, poly[0])
    rand_rot = random.uniform(0, 8)
    cmds.rotate(index*4 + rand_rot, 0, 0, poly[0])