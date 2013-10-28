def foo(o):
    del o['a']

# a = {'a':1, 'b':2}
# print a
# foo(a)
# print a

a = range(107)
i = 0
while i < len(a):
    print a[i:i+10]
    i += 10