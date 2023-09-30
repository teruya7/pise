import os
import json
from collections import defaultdict
from pise_set import PiseSet
from target import TargetHandler
from calculation import check_calc_done, make_dir_list
import yaml

def print_error_path(target_dir, error_info, cwd, dopant=None):
    if dopant is None:
        if target_dir in error_info:
            for dir_name in error_info[target_dir]:
                print(f"{cwd}/{target_dir}/{dir_name}")
    else:
        try:
            if target_dir in error_info[f"dopant_{dopant}"]:
                for dir_name in error_info[f"dopant_{dopant}"][target_dir]:
                    print(f"{cwd}/dopant_{dopant}/{target_dir}/{dir_name}")
        except KeyError:
            print()

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

class Error():
    def __init__(self):

        #pise.yamlとtarget_info.jsonの読み込み
        self.piseset = PiseSet()

        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                
                error_info = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

                #error_info.jsonの更新    
                update_error_info("unitcell", error_info, self.piseset.unitcell)
                update_error_info("cpd", error_info)
                update_error_info("defect", error_info)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    with open("pise_dopants_and_sites.yaml") as file:
                        pise_dopants_and_sites = yaml.safe_load(file)
                    for dopant_and_site in pise_dopants_and_sites["dopants_and_sites"]:
                        dopant = dopant_and_site[0]
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            update_error_info("cpd", error_info, dopant=dopant)
                            update_error_info("defect", error_info, dopant=dopant)
                            os.chdir("../")

                
                #error_info.jsonの絶対パスの表示
                cwd = os.getcwd()
                if any(error_info):
                    print_error_path("unitcell", error_info, cwd)
                    print_error_path("cpd", error_info, cwd)
                    print_error_path("defect", error_info, cwd)
                    
                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    with open("pise_dopants_and_sites.yaml") as file:
                        pise_dopants_and_sites = yaml.safe_load(file)
                    for dopant_and_site in pise_dopants_and_sites["dopants_and_sites"]:
                        dopant = dopant_and_site[0]
                        print_error_path("cpd", error_info, cwd, dopant)
                        print_error_path("defect", error_info, cwd, dopant)

                #error_info.jsonの保存
                with open("error_info.json", "w") as f:
                    json.dump(error_info, f, indent=4)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()

                