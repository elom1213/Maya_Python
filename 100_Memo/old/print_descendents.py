# 21_07_20
def print_descendents(name):
    import maya.cmds as cmds
    print('\ndescendents : ', cmds.listRelatives(name, allDescendents = 1, allParents = 0, fullPath = 1))
    print('parents     : ', cmds.listRelatives(name, allDescendents = 0, allParents = 1, fullPath = 1))