# 21_07_19
def ls_transform(nodeName):
    import maya.cmds as cmds
    return cmds.ls(nodeName, type = 'transform')