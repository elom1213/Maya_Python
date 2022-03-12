# 21_07_19
def print_nodetype(name):
    import maya.cmds as cmds
    print('\nnode name : %s' %name, '\nnode type : %s' %cmds.nodeType(name), '\n')