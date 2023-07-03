import os


#ディレクトリのリストを作成
def make_dir_list():
    list = []
    for f in os.listdir("./"):
        if os.path.isdir(f):
            if not os.path.islink(f):
                list.append(f)
    return list

#計算が終わったかどうかを確認
def check_calculation(path):
    try:
        os.chdir(path)
        if os.path.isfile("vasprun.xml"):
            flag_1 = True
        else:
            flag_1 = False

        if os.path.isfile("OUTCAR-finish"):    
            flag_2 = True
        else:
            flag_2 = False

        if flag_1 and flag_2:
            os.chdir("../")
            return True
        else:
            os.chdir("../")
            return False
    except FileNotFoundError:
        return False

#calc_infoのデータを作成
def make_calculation_info(path, data_dict, list=None, dopant=None):
    if os.path.isdir(path):
        os.chdir(path)
        if list is None:
            if dopant is None:
                tmp_list = make_dir_list()
                for i in tmp_list:
                    if check_calculation(i):
                        data_dict[path][i] = True
                    else:
                        data_dict[path][i] = False
            else:
                tmp_list = make_dir_list()
                for i in tmp_list:
                    if check_calculation(i):
                        data_dict[path + "_" + dopant][i] = True
                    else:
                        data_dict[path + "_" + dopant][i] = False
        else:
            if dopant is None:
                for i in list:
                    if check_calculation(i):
                        data_dict[path][i] = True
                    else:
                        data_dict[path][i] = False
            else:
                for i in list:
                    if check_calculation(i):
                        data_dict[path + "_" + dopant][i] = True
                    else:
                        data_dict[path + "_" + dopant][i] = False
        os.chdir("../")
    return data_dict

if __name__ == '__main__':
    print("これは自作モジュールです")