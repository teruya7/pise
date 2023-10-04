import os
import json
from collections import defaultdict
from pise_set import PiseSet
from target import TargetHandler
from doping import get_dopants_list
from pymatgen.io.vasp.outputs import Vasprun
import pathlib
import xml

#ディレクトリのリストを作成
def make_dir_list():
    list = []
    for f in os.listdir("./"):
        if os.path.isdir(f):
            if not os.path.islink(f):
                list.append(f)
    return list

def is_calc_converged(path):
    os.chdir(path)
    if path == "band_nsc" and os.path.isfile("vasprun.xml"):
        os.chdir("../")
        return True
    if os.path.isfile("is_converged.txt"):
        os.chdir("../")
        return True
    if os.path.isfile("vasprun.xml"):
        try:
            vasprun = Vasprun("vasprun.xml")
            if vasprun.converged:
                touch = pathlib.Path("is_converged.txt")
                touch.touch()
                os.chdir("../")
                return True
        except xml.etree.ElementTree.ParseError:
            os.chdir("../")
            return False
        else:
            os.chdir("../")
            return False
    else:
        os.chdir("../")
        return False

#target_dirのsub_dirの計算が終わったかの情報をcalc_infoに記録
def update_calc_info(target_dir, calc_info, dopant=None):
    if not os.path.isdir(target_dir):
        return calc_info
    
    os.chdir(target_dir)

    if target_dir == "surface":   
        surface_list = make_dir_list()
        for surface in surface_list:
            os.chdir(surface)
            dir_list = make_dir_list()
            for sub_dir in dir_list:
                if is_calc_converged(sub_dir):
                    calc_info[target_dir][surface][sub_dir] = True
                else:
                    calc_info[target_dir][surface][sub_dir] = False
            os.chdir("../")
        os.chdir("../")
        return calc_info

    if dopant is not None:
        dir_list = make_dir_list()
        for sub_dir in dir_list:
            if is_calc_converged(sub_dir):
                calc_info[f"dopant_{dopant}"][target_dir][sub_dir] = True
            else:
                calc_info[f"dopant_{dopant}"][target_dir][sub_dir] = False
    else:
        dir_list = make_dir_list()
        for sub_dir in dir_list:
            if is_calc_converged(sub_dir):
                calc_info[target_dir][sub_dir] = True
            else:
                calc_info[target_dir][sub_dir] = False
    os.chdir("../")
    return calc_info

def print_unfinished_path(calc_info, cwd):
    print("Unfinished_calculations:")
    for layer_1 in calc_info.keys():
        for layer_2 in calc_info[layer_1].keys():
            if calc_info[layer_1][layer_2] == True or calc_info[layer_1][layer_2] == False:
                if not calc_info[layer_1][layer_2]:
                    print(f"{cwd}/{layer_1}/{layer_2}")
            else:
                for layer_3 in calc_info[layer_1][layer_2].keys():
                    if not calc_info[layer_1][layer_2][layer_3]:
                        print(f"{cwd}/{layer_1}/{layer_2}/{layer_3}")

class Calculation():
    def __init__(self):

        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                
                #calc_info.jsonを初期化
                calc_info = defaultdict(lambda:defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))

                #calc_info.jsonの更新    
                update_calc_info("unitcell", calc_info)
                update_calc_info("cpd", calc_info)
                update_calc_info("defect", calc_info)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            update_calc_info("cpd", calc_info, dopant=dopant)
                            update_calc_info("defect", calc_info, dopant=dopant)
                            os.chdir("../")

                if piseset.surface:
                    update_calc_info("surface", calc_info)

                cwd = os.getcwd()
                print_unfinished_path(calc_info, cwd)

                #calc_info.jsonの保存
                with open("calc_info.json", "w") as f:
                    json.dump(calc_info, f, indent=4)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
        
if __name__ == '__main__':
    Calculation()