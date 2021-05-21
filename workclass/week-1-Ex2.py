
# EX 2 ลากเส้นหาพื้นที่

'''
n =  1      p = 2
n =  2      p = 4
n =  3      p = 7

2 + 2 + 3 + 4 + 5 + 6 + 7 + ... + n 
1 + 1 + 2 + 3 + 4 + 5 + 6 + 7 + ... + n  
1 + ( n ( n + 1 ) / 2 )

'''

n = int(input("Enter Number of line  : "))

if n >= 0 :
    p = 1 + n*(n+1) // 2 
    print(p)

