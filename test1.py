

bob = ['james', 'dave', 'steve', 'bill']
b = False
i = 0
while i < len(bob):
    if bob[i] == "dave" and b is not True:
        i = 0
        b = True
    print(bob[i])
    i += 1
