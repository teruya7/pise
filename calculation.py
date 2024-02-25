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
    if os.path.isfile(f"{path}/is_converged.txt"):
        return 
    
    if path == "band_nsc" and os.path.isfile(f"{path}/vasprun.xml"):
        touch = pathlib.Path(f"{path}/is_converged.txt")
        touch.touch()
        return
    
    if os.path.isfile(f"{path}/vasprun.xml"):
        try:
            vasprun = Vasprun(f"{path}/vasprun.xml")
            if vasprun.converged:
                touch = pathlib.Path(f"{path}/is_converged.txt")
                touch.touch()
                return 
        except xml.etree.ElementTree.ParseError:
            pass
        except AttributeError:
            pass

def write_result_to_calc_info(calc_info, cwd, first_layer, second_layer, third_layer=None):
    if third_layer is None:
        try:
            if not calc_info[first_layer][second_layer]:
                if os.path.isfile(f"{second_layer}/is_converged.txt"):
                    calc_info[first_layer][second_layer] = True
                else:
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

    if first_layer == "surface":   
        surface_list = make_dir_list()
        for second_layer in surface_list:
            os.chdir(second_layer)
            dir_list = make_dir_list()
            for third_layer in dir_list:
                is_calc_converged(third_layer)
                write_result_to_calc_info(calc_info, cwd, first_layer, second_layer, third_layer)
            os.chdir("../")
        os.chdir("../")
        return calc_info

    if dopant is not None:
        dir_list = make_dir_list()
        for second_layer in dir_list:
            is_calc_converged(second_layer)
            write_result_to_calc_info(calc_info, cwd, f"dopant_{dopant}", first_layer, second_layer)

        os.chdir("../")
        return calc_info

    dir_list = make_dir_list()
    for second_layer in dir_list:
        is_calc_converged(second_layer)
        write_result_to_calc_info(calc_info, cwd, first_layer, second_layer)
    os.chdir("../")

    return calc_info

def update_calc_info_parallel(first_layer, calc_info, cwd, num_process, dopant=None):
    if not os.path.isdir(first_layer):
        return calc_info
    
    os.chdir(first_layer)

    p = Pool(processes=num_process)

    if first_layer == "surface":   
        surface_list = make_dir_list()
        for second_layer in surface_list:
            os.chdir(second_layer)
            dir_list = make_dir_list()
            p.imap(is_calc_converged, dir_list)
            p.close()
            p.join()
            for third_layer in dir_list:
                write_result_to_calc_info(calc_info, cwd, first_layer, second_layer, third_layer)
            os.chdir("../")
        os.chdir("../")
        return calc_info

    if dopant is not None:
        dir_list = make_dir_list()
        p.imap(is_calc_converged, dir_list)
        p.close()
        p.join()
        for second_layer in dir_list:
            write_result_to_calc_info(calc_info, cwd, f"dopant_{dopant}", first_layer, second_layer)
        os.chdir("../")
        return calc_info

    dir_list = make_dir_list()
    p.imap(is_calc_converged, dir_list)
    p.close()
    p.join()
    for second_layer in dir_list:
        write_result_to_calc_info(calc_info, cwd, first_layer, second_layer)
    os.chdir("../")

    return calc_info


class Calculation():
    def __init__(self):

        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()

        #並列処理
        if piseset.parallel:
            num_process = int(cpu_count()*0.5)
            print(f"num_process:{num_process}")
        else:
            print("Multiprocessing is switched off.")

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                
                #calc_info.jsonを初期化
                calc_info = defaultdict(lambda:defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))

                #calc_info.jsonの更新 
                cwd = os.getcwd()
                if piseset.parallel:
                    update_calc_info_parallel("unitcell", calc_info, cwd, num_process)
                    update_calc_info_parallel("cpd", calc_info, cwd, num_process)
                    update_calc_info_parallel("defect", calc_info, cwd, num_process)
                else:
                    update_calc_info("unitcell", calc_info, cwd)
                    update_calc_info("cpd", calc_info, cwd)
                    update_calc_info("defect", calc_info, cwd)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            if piseset.parallel:
                                update_calc_info_parallel("cpd", calc_info, cwd, num_process, dopant=dopant)
                                update_calc_info_parallel("defect", calc_info, cwd, num_process, dopant=dopant)
                            else:
                                update_calc_info("cpd", calc_info, cwd, dopant=dopant)
                                update_calc_info("defect", calc_info, cwd, dopant=dopant)
                            os.chdir("../")

                if piseset.surface:
                    if piseset.parallel:
                        update_calc_info_parallel("surface", calc_info, cwd, num_process)
                    else:
                        update_calc_info("surface", calc_info, cwd)

                #calc_info.jsonの保存
                with open("calc_info.json", "w") as f:
                    json.dump(calc_info, f, indent=4)

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
        
if __name__ == '__main__':
    pass