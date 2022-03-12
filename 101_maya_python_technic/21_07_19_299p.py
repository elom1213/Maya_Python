# 21_07_19 299p 
import maya.cmds as cmds
import random

for x in range(20):
    for y in range(20):
        rand = random.uniform(0, 3)
        pl = cmds.polyCube(height = 1, depth = 0.1)
        cmds.move((-10+x)*1.5, (-10+y)*1.5, 0, pl[0])
        cmds.rotate(x*12 + rand, y*12 + rand, 0, pl[0])