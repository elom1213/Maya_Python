# maya python 289
import maya.cmds as cmds
import random

all_color = ['blinn1', 'blinn2']

sha_eng_list = []

all_cyil = ls_transform('pCyli*')

for mat_ in all_color:
    sha_eng = cmds.listConnections(mat_, type = 'shadingEngine')
    if sha_eng:
        sha_eng_list.append(sha_eng[0])

cmds.sets(all_cyil[0], forceElement = sha_eng_list[1])
cmds.sets(all_cyil[1], forceElement = sha_eng_list[0])
