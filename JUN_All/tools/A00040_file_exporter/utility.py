import maya.cmds as cmds;
import maya.mel as mel


def JUN_cmd_brows_path(*args, **kwargs):

    
    file_path = cmds.fileDialog2(
        dialogStyle=2,
        fileMode=2,
        caption="Select Folder"
    )[0]

    if file_path:
        args[0].set_val(file_path)
    else :
        print("Fail : Brows file path")
        return 0


    '''
    export_path = "C:/Users/USER/Desktop/JP/0001_PJ/JP__02.Art/JP__Asset/JP__CH/__tmp"
    cmds.select(selected_objects)
    FileName = (selected_objects)

    for i in FileName:
        #extension = ".FBX"
        mainpath = export_path+ "/" +i
        cmds.file(mainpath, force=True, options="v=0;", typ="FBX export", pr=True, ea=True)
    '''