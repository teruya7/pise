import os
import json
from collections import defaultdict
from pise_set import PiseSet
from target import TargetHandler
from doping import get_dopants_list
from common_function import make_dir_list
from pymatgen.io.vasp.outputs import Vasprun
import pathlib
import xml
from multiprocessing import Pool, cpu_count

def is_calc_converged(path):
    os.chdir(path)
    if path == "band_nsc" and os.path.isfile("vasprun.xml"):
        touch = pathlib.Path("is_converged.txt")
        touch.touch()
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
        except AttributeError:
            os.chdir("../")
            return False
        else:
            os.chdir("../")
            return False
    else:
        os.chdir("../")
        return False

def write_result_to_calc_info(calc_info, cwd, first_layer, second_layer, third_layer=None):
    if third_layer is None:
        try:
            if not calc_info[first_layer][second_layer]:
                if os.path.isfile(f"{second_layer}/is_converged.txt"):
                    calc_info[first_layer][second_layer] = True
                else:
                    calc_info[first_layer][second_layer] = False
                    print(f"{cwd}/{first_layer}/{second_layer}")
        #keyに存在していない場合
        except KeyError:
            if os.path.isfile(f"{second_layer}/is_converged.txt"):
                calc_info[first_layer][second_layer] = True
            else:
                calc_info[first_layer][second_layer] = False
                print(f"{cwd}/{first_layer}/{second_layer}")
    #dopantやsurfaceなど階層構造が深くなる場合
    else:
        try:
            if not calc_info[first_layer][second_layer][third_layer]:
                if os.path.isfile(f"{third_layer}/is_converged.txt"):
                    calc_info[first_layer][second_layer][third_layer] = True
                else:
                    calc_info[first_layer][second_layer][third_layer] = False
                    print(f"{cwd}/{first_layer}/{second_layer}/{third_layer}")
        except KeyError:
            if os.path.isfile(f"{third_layer}/is_converged.txt"):
                calc_info[first_layer][second_layer][third_layer] = True
            else:
                calc_info[first_layer][second_layer][third_layer] = False
                print(f"{cwd}/{first_layer}/{second_layer}/{third_layer}")

def update_calc_info(first_layer, calc_info, cwd, dopant=None):
    if not os.path.isdir(first_layer):
        return calc_info
    
    os.chdir(first_layer)

    p = Pool(processes=int(cpu_count()*0.9))

    if first_layer == "surface":   
        surface_list = make_dir_list()
        for second_layer in surface_list:
            os.chdir(second_layer)
            dir_list = make_dir_list()
            p.imap(is_calc_converged, dir_list)
            for third_layer in dir_list:
                write_result_to_calc_info(calc_info, cwd, first_layer, second_layer, third_layer)
            os.chdir("../")
        os.chdir("../")
        return calc_info

    if dopant is not None:
        dir_list = make_dir_list()
        p.imap(is_calc_converged, dir_list)

        for second_layer in dir_list:
            write_result_to_calc_info(calc_info, cwd, f"dopant_{dopant}", first_layer, second_layer)

        os.chdir("../")
        return calc_info

    dir_list = make_dir_list()
    p.imap(is_calc_converged, dir_list)
    for second_layer in dir_list:
        write_result_to_calc_info(calc_info, cwd, first_layer, second_layer)
    os.chdir("../")

    # 並列処理の終了
    p.close()
    p.join()

    return calc_info


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
                cwd = os.getcwd()  
                update_calc_info("unitcell", calc_info, cwd)
                update_calc_info("cpd", calc_info, cwd)
                update_calc_info("defect", calc_info, cwd)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            update_calc_info("cpd", calc_info, cwd, dopant=dopant)
                            update_calc_info("defect", calc_info, cwd, dopant=dopant)
                            os.chdir("../")

                if piseset.surface:
                    update_calc_info("surface", calc_info, cwd)

                #calc_info.jsonの保存
                with open("calc_info.json", "w") as f:
                    json.dump(calc_info, f, indent=4)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
        
if __name__ == '__main__':
    Calculation()