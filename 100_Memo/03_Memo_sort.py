a = cmds.ls(sl = True);
print(a)
a = sorted(a)
print(a)
# ['GlueStick1', 'Metal_Front1', 'Cable1', 'Holder1', 'Trigger1', 'Nozzle1', 'GlueGun1', 'Glue_Gun_Group']
# ['Cable1', 'GlueGun1', 'GlueStick1', 'Glue_Gun_Group', 'Holder1', 'Metal_Front1', 'Nozzle1', 'Trigger1']
cmds.group(a)
# work!
