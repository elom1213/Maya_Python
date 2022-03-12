import maya.cmds as cmds;

str_SGs_inScene = cmds.ls ( type = "shadingEngine");
str_SG_upstream = cmds.hyperShade(listUpstreamNodes = "Sewing_machineSG");
for i in str_SG_upstream:
    if(cmds.nodeType(i) == "transform"):
        print(i + "\n");

for i in range(0, len(str_SG_upstream)):
    print(str_SG_upstream[i] + "\n");


for i in range(0, len(str_SGs_inScene)):
    print(str_SGs_inScene[i]);