import os
import json
from collections import defaultdict
from pise_set import PiseSet
from target_info import TargetHandler

#ディレクトリのリストを作成
def make_dir_list():
    list = []
    for f in os.listdir("./"):
        if os.path.isdir(f):
            if not os.path.islink(f):
                list.append(f)
    return list

#計算が終わったかどうかを確認
def check_calc_done(path):
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

#target_dirのsub_dirの計算が終わったかの情報をcalc_infoに記録
def update_calc_info(target_dir, calc_info, unitcell_list=None, dopant=None):
    if os.path.isdir(target_dir):
        os.chdir(target_dir)
        if unitcell_list is None:
            if dopant is None:
                dir_list = make_dir_list()
                for sub_dir in dir_list:
                    if check_calc_done(sub_dir):
                        calc_info[target_dir][sub_dir] = True
                    else:
                        calc_info[target_dir][sub_dir] = False
            else:
                dir_list = make_dir_list()
                for sub_dir in dir_list:
                    if check_calc_done(sub_dir):
                        calc_info[f"dopant_{dopant}"][target_dir][sub_dir] = True
                    else:
                        calc_info[f"dopant_{dopant}"][target_dir][sub_dir] = False
        else:
            for unitcell_dir in unitcell_list:
                if check_calc_done(unitcell_dir):
                    calc_info[target_dir][unitcell_dir] = True
                else:
                    calc_info[target_dir][unitcell_dir] = False
        os.chdir("../")
    return calc_info

class CalcInfoMaker():
    def __init__(self):

        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                
                #calc_info.jsonを初期化
                calc_info = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

                #calc_info.jsonの更新    
                update_calc_info("unitcell", calc_info, piseset.unitcell)
                update_calc_info("cpd", calc_info)
                update_calc_info("defect", calc_info)
                for dopant in piseset.dopants:
                    if os.path.isdir(f"dopant_{dopant}"):
                        os.chdir(f"dopant_{dopant}")
                        update_calc_info("cpd", calc_info, dopant=dopant)
                        update_calc_info("defect", calc_info, dopant=dopant)
                        os.chdir("../")

                #calc_info.jsonの保存
                with open("calc_info.json", "w") as f:
                    json.dump(calc_info, f, indent=4)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()
        
if __name__ == '__main__':
    print()