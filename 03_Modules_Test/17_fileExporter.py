
import maya.cmds as cmds

# Get the currently selected object
selected_objects = cmds.ls(selection=True)




export_path = "C:/Users/USER/Desktop/JP/0001_PJ/JP__02.Art/JP__Asset/JP__CH/__tmp"
cmds.select(selected_objects)
FileName = (selected_objects)

for i in FileName:
    #extension = ".FBX"
    mainpath = export_path+ "/" +i
    cmds.file(mainpath, force=True, options="v=0;", typ="FBX export", pr=True, ea=True)