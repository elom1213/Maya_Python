
selList = cmds.ls ( sl=True, fl=True);
set_sl = {};
for sl in selList :
#    cmds.select(sl)
    print(cmds.listRelatives(sl, shapes=True))
    shape = cmds.listRelatives(sl, shapes=True)
    if(shape):
        set_sl[sl] = shape[0];
    else :
        set_sl[sl] = 'joint';
print(set_sl);
#{'curve1': 'curveShape1', 'pCube1': 'pCubeShape1', 'joint1': 'joint'}


#=======================================================================================

selList = cmds.ls ( sl=True, fl=True);
set_sl = {};
types = set()
for sl in selList :
#    cmds.select(sl)
    print(cmds.listRelatives(sl, shapes=True))
    shape = cmds.listRelatives(sl, shapes=True)
    if(shape):
        set_sl[sl] = shape[0];
    else :
        set_sl[sl] = 'joint';
for val in set_sl.values() :
    types.add(val)
print(types)
print(set_sl)
# ['curveShape1']
# ['pCubeShape1']
# None
# {'pCubeShape1', 'curveShape1', 'joint'}
# {'curve1': 'curveShape1', 'pCube1': 'pCubeShape1', 'joint1': 'joint'}


#=======================================================================================

'''
Select

curve1
curveShape1
curve2
pCube1
joint1
'''
selList = cmds.ls ( sl=True, fl=True);
set_sl = {};
types = set()
shapes = set()
for sl in selList :
#    cmds.select(sl)
    print(cmds.objectType(sl))
    types.add(cmds.objectType(sl));
#    print(cmds.listRelatives(sl, shapes=True))
    shape = cmds.listRelatives(sl, shapes=True)
    if(shape):
        set_sl[sl] = shape[0];
    else :
        set_sl[sl] = 'joint';
for val in set_sl.values() :
    shapes.add(val)


print(types) # {'transform', 'nurbsCurve', 'joint'}
print(shapes) # {'pCubeShape1', 'curveShape1', 'joint', 'curveShape2'}
print(set_sl) # {'curve1': 'curveShape1', 'curveShape1': 'joint', 'curve2': 'curveShape2', 'pCube1': 'pCubeShape1', 'joint1': 'joint'}

# transform
# nurbsCurve
# transform
# transform
# joint


#=======================================================================================

'''
Select

curve2
pCube1
joint_A
joint_B
'''

selList = cmds.ls ( sl=True, fl=True);
set_sl = {};
for sl in selList :
    typ = cmds.objectType(sl)
    set_sl[sl] = typ;


val = {i for i in set_sl if set_sl[i] == 'joint'}

print(val) # {'joint_A', 'joint_B'}

val = {i for i in set_sl if set_sl[i] != 'joint'}

print(val) # {'curve2', 'pCube1'}


#=======================================================================================

'''
Select joint_B

joint_B
    -pPlane1
        -pPlaneShape1
    -curve2
        -curveShape2
    -joint2
'''
str_obj = cmds.ls ( sl=True, fl=True);
rel = cmds.listRelatives ( str_obj[0], allDescendents=True, path=True );
print(rel); #['pPlaneShape1', 'pPlane1', 'curveShape2', 'curve2', 'joint_B|joint2']