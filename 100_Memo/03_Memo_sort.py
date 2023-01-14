a = cmds.ls(sl = True);
print(a)
a = sorted(a)
print(a)
# ['GlueStick1', 'Metal_Front1', 'Cable1', 'Holder1', 'Trigger1', 'Nozzle1', 'GlueGun1', 'Glue_Gun_Group']
# ['Cable1', 'GlueGun1', 'GlueStick1', 'Glue_Gun_Group', 'Holder1', 'Metal_Front1', 'Nozzle1', 'Trigger1']
cmds.group(a)
# work!

# https://www.programiz.com/python-programming/methods/list/sort
emp = {'Name': 'Alan Turing', 'age': 25, 'salary': 10000}

h = emp.get("age");

print(h) # 25

# take second element for sort
def takeSecond(elem):
    return elem[1]

# random list
random = [(2, 2), (3, 4), (4, 1), (1, 3)]

# sort list with key
random.sort(key=takeSecond)

# print list
print('Sorted list:', random)
