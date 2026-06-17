# 21_07_19 299p 
import maya.cmds as cmds
import random

randAng = {'x' : 0, 'y' : 0, 'z': 0}


for x in range(100):
    for i in randAng:
        randAng[i] = random.uniform(0, 360)
    sp = cmds.sphere(radius = 0.2)
    cmds.rotate(randAng.x, randAng.y, randAng.z, sp[0])
    cmds.move(0, 10, 0, sp[0], objectspace = 1)

    # 21_08_19 ripple cubes 338
