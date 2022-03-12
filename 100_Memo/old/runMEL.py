import maya.cmds as cmds
import maya.mel as mel

def runMEL(str_script_name):
    print("Running MEL from Python")
    mel.eval('source ' + str_script_name + ';')