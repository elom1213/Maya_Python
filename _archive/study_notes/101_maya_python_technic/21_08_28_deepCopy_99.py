import copy
a = [1, 2, 3]
def just_copy(c):
    c[2] = 7
def deep_copy(c):
    d = copy.copy(c)
    d[2] = 9
    print("d =>")
    print(d)

just_copy(a)
print(a) ## [1, 2, 7]

deep_copy(a)
print("a => ")
print(a)
