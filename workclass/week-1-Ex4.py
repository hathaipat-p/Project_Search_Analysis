
# Ex 4 : ผสมสิบ

#โจทย์อาจารย์ได้ 7 ตัว : 1 3 5 7 2 4 8 2 6 3 1 1 2 3 5 6

list_num = input("input : ").split(" ")     #นำมา split เพื่อเก็บค่าใน list 
n = len(list_num)

data = []
for i in range(n):                          
    num = int(list_num[i])                  # ค่าที่ได้ใน list ตอนแรกเป็น string นำมาทำเป็น int
    data.append(num)

count = 0

for i in range(n):                      # i แทนตัวเลขที่ตำแหน่งถัดไปเรื่อยๆ
    if (i % 4 != 3)  :                  # แนวนอน
        sum2 = data[i] + data[i+1]      # นำตัวเลขตำแหน่งที่ i + ตำแหน่งถัดไป
        if sum2 == 10 :                 # ถ้าผลบวกเท่ากับ 10 ให้นับ
            count += 1
        elif sum2 < 10 and i % 4 != 2 : # ถ้าผลบวกน้อยกว่า 10 และไม่ได้อยู่ช่องรองสุดท้ายให้บวกเลขต่อ
            sum2 += data[i+2]
            if sum2 == 10 :             # ถ้าผลบวกเท่ากับ 10 ให้นับ
                count += 1

    if i <= 11 :                         # แนวตั้ง
        sum2 = data[i] + data[i+4]       # นำตัวเลขตำแหน่งที่ i + ตำแหน่งล่าง
        if sum2 == 10 :                  # ถ้าผลบวกเท่ากับ 10 ให้นับ
            count += 1
        elif sum2 < 10 and i <= 7 :      # ถ้าผลบวกน้อยกว่า 10 และไม่ได้อยู่ช่องรองล่างสุดให้บวกเลขต่อ
            sum2 += data[i+4+4]
            if sum2 == 10 :              # ถ้าผลบวกเท่ากับ 10 ให้นับ
                count += 1

print(count)


