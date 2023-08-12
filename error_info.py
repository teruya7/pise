import os
import json
import subprocess
from collections import defaultdict
from pise_set import PiseSet
from target_info import TargetHandler
from calc_info import make_dir_list, check_calc_done

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

class ErrorInfoMaker():
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
                if self.piseset.dopants is not None:
                    for dopant in self.piseset.dopants:
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
    
    def print(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                
                subprocess.run(["less error_info.json"], shell=True)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()

    def path(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                
                with open('error_info.json') as f:
                    error_info = json.load(f)
                cwd = os.getcwd()

                if any(error_info):
                    print_error_path("unitcell", error_info, cwd)
                    print_error_path("cpd", error_info, cwd)
                    print_error_path("defect", error_info, cwd)
                if self.piseset.dopants is not None:
                    for dopant in self.piseset.dopants:
                        print_error_path("cpd", error_info, cwd, dopant)
                        print_error_path("cpd", error_info, cwd, dopant)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()

                