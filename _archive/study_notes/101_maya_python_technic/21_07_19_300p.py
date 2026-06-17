# 21_07_19 300p 
import maya.cmds as cmds
import random

randAng = {'x' : 0, 'y' : 0, 'z': 0}


for k in range(100):
    for i in randAng:
        randAng[i] = random.uniform(0, 360)
    sp = cmds.sphere(radius = 0.2)
    cmds.rotate(randAng['x'], randAng['y'], randAng['z'], sp[0])
    cmds.move(0, 10, 0, sp[0], os = 1)