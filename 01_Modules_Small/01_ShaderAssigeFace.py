selection = cmds.ls(sl=True, o=True)[0]    
faces = cmds.ls(sl=True)
cmds.ConvertSelectionToFaces();
sel_face = selection = cmds.ls(sl=True)

#cmds.select(sel_face);
x = 0
# assign shader
sha = cmds.shadingNode('lambert', asShader=True, name="{}_{}_lambert".format(selection, x))
sg = cmds.sets(empty=True, renderable=True, noSurfaceShader=True,  name="{}_{}_sg".format(selection, x))
cmds.connectAttr( sha+".outColor", sg+".surfaceShader", f=True)
cmds.select(sel_face);
cmds.sets(sel_face, e=True, forceElement=sg)
