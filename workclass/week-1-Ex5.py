
# EX 5 : 3-SUM

data = [0,-1,2,-3,1,-2,3]
n = len(data) 

output = []

# จับกลุ่มเลข 3 จำนวน
for i in range(n):                              # i คือตำแหน่งตั้งต้น
    for j in range(i+1,n,1):                    # j คือตำแหน่งที่นำมาบวก โดยเอาตัวถัดจาก i มาเรื่อยๆ
        twosum =  data[i] +  data[j]

        # ถ้าผลบวกไม่เป็น 0 ให้หาว่ามีเลขติดลบผลบวกนั้นไหม ถ้ามีก็ใส่เลข 3 ตัวนั้นใน output list
        if twosum != 0 and -twosum in data and -twosum != data[i] and -twosum != data[j]:
            out = ( data[i] ,  data[j] , -twosum )
            output.append(out)

        # ถ้าผลบวกเป็น 0 ให้หาว่ามีเลข 0 นั้นไหม ถ้ามีก็ใส่เลข 2 ตัวรแรกและ 0 ใน output list
        if twosum == 0 and 0 in data:
            out = ( data[i] ,  data[j] , 0 )
            output.append(out)
        else : pass

# นำคู่ที่ซ้ำกันออกไป
for i in range(len(output)):                     # i คือตำแหน่งตั้งต้น
    for j in range(len(output)-1,0,-1):          # j คือตำแหน่งที่นำมาเปรียบเทียบ โดยเอาตัวจากตำแหน่งหลังไล่มาหน้า
        if j < i :                               # i < j แสดงว่าข้อมูลมาชนกันแล้ว แสดงว่าตัดตัวที่ซ้ำกันไม่มีแล้ว
            break
        else : 
            first =  output[i]
            sec = output[j]
            if first[0] == sec[0] and first[1] == sec[2] :          # ถ้ามีเลขเหมือน 2 ตัว แสดงว่าข้อมูลซ้ำ
                output.remove(sec)                                  # ให้ลบตัวที่นำมาเทียบออก
            elif first[0] != sec[0] and ( first[0] == sec[1] or first[0] == sec[2] ):
                if first[1] == sec[0] or first[1] == sec[1] or first[1] == sec[2] :
                    output.remove(sec)

print(output)
