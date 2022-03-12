## https://stackoverflow.com/questions/699866/python-int-to-binary-string
print(bin(257))
#arr = "{0:b}".format(257)
arr = format(257, "010b")
print(type(arr))
for i in arr:
    i = int(i)
    print("%d " % i)

rule = []

def set_rules(code):
  tmp = format(code, "010b")
  for i in tmp:
    rule.append(int(i))

set_rules(257)