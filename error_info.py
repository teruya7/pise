import os
import json
from collections import defaultdict
from pise_set import PiseSet
from target_info import TargetHandler
from calc_info import make_dir_list, check_calc_done

#target_dirのsub_dirの計算が終わったかの情報をerror_infoに記録
def update_error_info(target_dir, error_info, unitcell_list=None, dopant=None):
    if os.path.isdir(target_dir):
        os.chdir(target_dir)
        if unitcell_list is None:
            if dopant is None:
                dir_list = make_dir_list()
                for sub_dir in dir_list:
                    if not check_calc_done(sub_dir):
                        error_info[target_dir][sub_dir] = False
            else:
                dir_list = make_dir_list()
                for sub_dir in dir_list:
                    if not check_calc_done(sub_dir):
                        error_info[f"dopant_{dopant}"][target_dir][sub_dir] = False
        else:
            for unitcell_dir in unitcell_list:
                if not check_calc_done(unitcell_dir):
                    error_info[target_dir][unitcell_dir] = False
        os.chdir("../")
    return error_info

class ErrorInfoMaker():
    def __init__(self):

        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                
                error_info = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

                #error_info.jsonの更新    
                update_error_info("unitcell", error_info, piseset.unitcell)
                update_error_info("cpd", error_info)
                update_error_info("defect", error_info)
                for dopant in piseset.dopants:
                    if os.path.isdir(f"dopant_{dopant}"):
                        os.chdir(f"dopant_{dopant}")
                        update_error_info("cpd", error_info, dopant=dopant)
                        update_error_info("defect", error_info, dopant=dopant)
                        os.chdir("../")

                #error_info.jsonの保存
                with open("error_info.json", "w") as f:
                    json.dump(error_info, f, indent=4)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()