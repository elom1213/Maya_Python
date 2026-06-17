import kangarooTabTools.weights as weights
weights.moveSkinClusterWeights(xJoints={"['dyn_skirt_n_01_01']": "['aa_dyn_skirt_n_01_05']"}, bDisableIslandCheck=True, sChooseSkinCluster=None, iSmoothBorderMask=1)

weights.moveSkinClusterWeights(sChooseSkinCluster=None, xJoints={"['dyn_skirt_n_01_01', 'dyn_skirt_n_02_01', 'dyn_skirt_n_03_01']": "['aa_dyn_skirt_n_01_05', 'aa_dyn_skirt_n_02_08']"}, bDisableIslandCheck=True, iSmoothBorderMask=1)

weights.moveSkinClusterWeights(iSmoothBorderMask=1, xJoints={"['aa__Bdy_L_Ear_01']": "['bb__aa__Bdy_L_Ear_03']", "['aa__Bdy_L_Ear_02']": "['bb__aa__Bdy_L_Ear_02']"}, bDisableIslandCheck=True, sChooseSkinCluster=None)

{"['jointFrom1']": "['jointTo1']", "['jointFrom2']": "['jointTo2']"}


shadingNode -asTexture -isColorManaged file;
shadingNode -asUtility place2dTexture;
connectAttr -f place2dTexture16.coverage file3.coverage;
connectAttr -f place2dTexture16.translateFrame file3.translateFrame;
connectAttr -f place2dTexture16.rotateFrame file3.rotateFrame;
connectAttr -f place2dTexture16.mirrorU file3.mirrorU;
connectAttr -f place2dTexture16.mirrorV file3.mirrorV;
connectAttr -f place2dTexture16.stagger file3.stagger;
connectAttr -f place2dTexture16.wrapU file3.wrapU;
connectAttr -f place2dTexture16.wrapV file3.wrapV;
connectAttr -f place2dTexture16.repeatUV file3.repeatUV;
connectAttr -f place2dTexture16.offset file3.offset;
connectAttr -f place2dTexture16.rotateUV file3.rotateUV;
connectAttr -f place2dTexture16.noiseUV file3.noiseUV;
connectAttr -f place2dTexture16.vertexUvOne file3.vertexUvOne;
connectAttr -f place2dTexture16.vertexUvTwo file3.vertexUvTwo;
connectAttr -f place2dTexture16.vertexUvThree file3.vertexUvThree;
connectAttr -f place2dTexture16.vertexCameraOne file3.vertexCameraOne;

connectAttr place2dTexture16.outUV file3.uv;
connectAttr place2dTexture16.outUvFilterSize file3.uvFilterSize;


import maya.mel as mel
import maya.cmds as cmds

file__ =  mel.eval("shadingNode -asTexture -isColorManaged file")
place2Tex__ =  mel.eval("shadingNode -asUtility place2dTexture;")

lst_attr = ["coverage",
            "translateFrame",
            "rotateFrame",
            "mirrorU",
            "mirrorV",
            "stagger",
            "wrapU",
            "wrapV",
            "repeatUV",
            "offset",
            "rotateUV",
            "noiseUV",
            "vertexUvOne",
            "vertexUvTwo",
            "vertexUvThree",
            "vertexCameraOne"]

for i in range(len(lst_attr)):
    cmds.connectAttr( file__ + "." + lst_attr[i], place2Tex__ + "." + lst_attr[i])

cmds.connectAttr( file__ + ".outUV", place2Tex__ + ".uv")
cmds.connectAttr( file__ + ".outUvfilterSize", place2Tex__ + ".uvFilterSize")
