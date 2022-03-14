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

str_obj_relatives = cmds.listRelatives("polySurface1", f = True, children = True);
print(str_obj_relatives)

di = {"a" : [1,2], "b" : [3, 5]}
allVal = di.values();
print(allVal)
di["b"].append(7)
for i in di:
    print(i);
    print(di.get(i));
    
a= cmds.hyperShade(listUpstreamNodes = "polySurfaceShape889");
print(a)

c = dict.fromkeys(["a", "b", "c"],[])
print(c)
c["b"].append(4);
print(c)

d = ["a", "b", "c", "d"];
del d[2];
print(d);

for i in range(0, 10, 3):
    print(i)
    
cmds.select('Sewing_machineSG2');
a = cmds.ls(sl = True);
print(a)

aa = cmds.hyperShade(listUpstreamNodes = "Sewing_machineSG1");
print(cmds.nodeType("|Sewing_machine_fbx_grp|polySurface3|polySurfaceShape3"));

# select Shader
cmds.select("Glue_Gun_Silicone_Material3", noExpand = 1);

# get shader from SG
print(cmds.connectionInfo("Glue_Gun_Silicone_MaterialSG.surfaceShader", sourceFromDestination = 1))
# Glue_Gun_Silicone_Material.outColor

# try make is_funcion
str_list_upStrms_frmSGs = [cmds.hyperShade(listUpstreamNodes=kk)[0:-1] for kk in str_list_SGs_seleted][0]
str_list_shders_frmUpStrms = [is_connected_surfShder(kk) for kk in str_list_upStrms_frmSGs ]

def is_connected_surfShder(str_node_input):
    str_connecteSrc_frmSG = cmds.connectionInfo(str_node_input + ".surfaceShader", sourceFromDestination = 1);