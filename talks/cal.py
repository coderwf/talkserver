# -*- coding:utf-8 -*-

import csv

#-------import---------------------------------------
#读取文件
Z0          = 50

#row_start表示只取其及之后的行即可
def read_file(path,row_start=1):
    datas = []
    with open(path,"r") as f:
        reader = csv.reader(f)
        for row in reader:
            row = row[2:]
            datas.append(row)
    datas = datas[row_start-1:]
    return datas

#
def formula(s11,s21,s12,s22):
    numerator   = (2 * Z0 ) * (1-s11*s22+s12*s21-s12-s21)
    print numerator

    denominator = (1-s11) * (1-s22) - s21 * s12
    print denominator
    return numerator / denominator

#转换为复数
def eval_datas(datas):
    dataps = []
    for data in datas :
        t = (complex(eval(data[0]),eval(data[1])),
             complex(eval(data[2]), eval(data[3])),
             complex(eval(data[4]), eval(data[5])),
             complex(eval(data[6]), eval(data[7])))
        dataps.append(t)
    return dataps

def cal(dataps):
    res = []
    for datap in dataps :
        res.append(formula(*datap))
    return res


def cal_for(path):
    datas = read_file(path, row_start=2)
    dataps = eval_datas(datas)
    res = cal(dataps)
    return res


def write_res(datas):
    with open("res.csv","wb+") as f:
        writer = csv.writer(f,delimiter=' ')
        count = 1
        writer.writerow(("no.","rel","imag"))
        for data in datas :
            writer.writerow((count,data.real,data.imag))
            count+=1

if __name__ == "__main__":
    path = "C:\Users\mayn\Desktop\S-parameters.csv"
    res = cal_for(path)
    write_res(res)
