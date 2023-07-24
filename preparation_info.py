
from target_info import TargetHandler
from calc_info import CalcInfoMaker, make_dir_list
from pise_set import PiseSet
import os
from collections import defaultdict
import json
import subprocess
import shutil
import pathlib
import yaml
from pymatgen.io.vasp.outputs import Vasprun

def delete_duplication(path_to_criteria, path_to_target):
    #元のパスの記録
    cwd = os.getcwd()
    os.chdir(path_to_criteria)
    criteria_list = make_dir_list()

    os.chdir(cwd)
    os.chdir(path_to_target)
    target_list = make_dir_list()

    for i in target_list:
        if i in criteria_list:
            subprocess.run([f"rm -r {i}"], shell=True)
            print(f"{i} is duplication. So {i} has deleted.")
    os.chdir(cwd)

def calc_aexx(vasprun_path):
    vasprun = Vasprun(vasprun_path)
    epsilon_electronic = vasprun.epsilon_static
    AEXX = 1/((epsilon_electronic[0][0] + epsilon_electronic[1][1] + epsilon_electronic[2][2])/3)
    AEXX_formatted = '{:.2g}'.format(AEXX)
    return AEXX_formatted

def initialize_preparetion_info(preparation_target_list):
    if os.path.isfile("preparation_info.json"):
        print("Loading preparation_info.json")
        with open('preparation_info.json') as f:
            preparation_info = json.load(f)
        for i in preparation_target_list:
            preparation_info.setdefault(i, False)
    else:
        preparation_info = defaultdict(dict)
        print("Making preparation_info.json")
        for i in preparation_target_list:
                preparation_info[i] = False
    return preparation_info

def check_preparation_done():
    if os.path.isfile("POTCAR"):
        return True
    else:
        return False
 
def prepare_job_script(piseset, task_name):
    cwd = os.getcwd()
    if task_name in piseset.small_task:
        shutil.copy(f"{piseset.job_script_path}/{piseset.job_script_small}", cwd)
        touch = pathlib.Path(piseset.submission_ready)
        touch.touch()
    elif task_name in piseset.large_task:
        shutil.copy(f"{piseset.job_script_path}/{piseset.job_script_large}", cwd)
        touch = pathlib.Path(piseset.submission_ready)
        touch.touch()
    else:
        print("A job script used for the task is not defined.")

def prepare_input_files(piseset, target_dir, vise_task_command, task_name):
    if not os.path.isdir(task_name):
        print(f"Preparing {target_dir}.")
        os.makedirs(target_dir, exist_ok=True)
        os.chdir(target_dir)
        if not check_preparation_done():
            prepare_job_script(piseset, task_name)
            subprocess.run([vise_task_command], shell=True)
        os.chdir("../")
    else:
        print(f"{task_name} has already prepared.")

def preparation_opt(piseset, material_id, formula_pretty):
    print("Preparing opt.")
    if not os.path.isdir(f"{formula_pretty}_{material_id}/{piseset.functional}/unitcell/opt"):
        os.makedirs(f"{formula_pretty}_{material_id}/{piseset.functional}/unitcell/opt", exist_ok=True)
        os.chdir(f"{formula_pretty}_{material_id}/{piseset.functional}")

        #vise.yamlの作成
        with open("vise.yaml", "w") as f:
            yaml.dump(piseset.vise_yaml, f, sort_keys=False)

        os.chdir("unitcell/opt")
        if material_id is not None:
            if not check_preparation_done():
                subprocess.run([f"vise gp -m {material_id}"], shell=True)
                prepare_job_script(piseset, "opt")
                subprocess.run([piseset.vise_task_command_opt], shell=True)
        else:
            cwd = os.getcwd()
            if not check_preparation_done():
                shutil.copy(f"{piseset.path_to_poscar}/{formula_pretty}_POSCAR", cwd)
                prepare_job_script(piseset, "opt")
                subprocess.run([piseset.vise_task_command_opt], shell=True)
            
def preparation_unitcell(piseset, calc_info, preparation_info):
    if not preparation_info["unitcell"] and calc_info["unitcell"]["opt"]:
        print("Preparing unitcell.")
        os.chdir("unitcell")
        #汎関数によって処理を分ける
        prepare_input_files(piseset, "band", piseset.vise_task_command_band, "band")
        prepare_input_files(piseset, "dos", piseset.vise_task_command_dos, "dos")
        prepare_input_files(piseset, "abs", piseset.vise_task_command_abs, "abs")
        if piseset.functional == "pbesol": 
            prepare_input_files(piseset, "dielectric", piseset.vise_task_command_dielectric, "dielectric")
            prepare_input_files(piseset, "dielectric_rpa", piseset.vise_task_command_dielectric_rpa, "dielectric_rpa")
        else:
            prepare_input_files(piseset, "dielectric", piseset.vise_task_command_dielectric_hybrid, "dielectric")
        os.chdir("../")
        flag = True
    elif preparation_info["unitcell"]:
        print("Preparation of unitcell has already finished.")
        flag = True
    elif not calc_info["unitcell"]["opt"]:
        print("opt calculations have not finished yet. So preparing unitcell will be skipped.")
        flag = False
    return flag

def preparation_band_nsc(piseset, calc_info, preparation_info):
    if not preparation_info["band_nsc"] and calc_info["unitcell"]["band"] and calc_info["unitcell"]["dielectric_rpa"]:
        print("Preparing band_nsc.")
        os.chdir("unitcell")
        aexx = calc_aexx("dielectric_rpa/vasprun.xml")
        os.makedirs("band_nsc", exist_ok=True)
        os.chdir("band_nsc")

        #vise.yamlを作成
        vise_yaml = piseset.vise_yaml
        with open("vise.yaml", "w") as f:
            vise_yaml["options"]["set_hubbard_u"] = False
            yaml.dump(vise_yaml, f, sort_keys=False)

        if not check_preparation_done():
            prepare_job_script(piseset, "band_nsc")
            subprocess.run([f"{piseset.vise_task_command_band_nsc} {aexx}"], shell=True)
            subprocess.run(["cp ../band/WAVECAR ./"], shell=True)
        os.chdir("../../")

        #aexx_info.jsonに保存
        aexx_info = defaultdict(dict)
        aexx_info["AEXX"] = aexx
        with open("aexx_info.json", "w") as f:
            json.dump(aexx_info, f, indent=4)
        flag = True
    elif preparation_info["band_nsc"]:
        print("Preparation of band_nsc has already finished.")
        flag = True
    elif not calc_info["unitcell"]["band"] and calc_info["unitcell"]["dielectric_rpa"]:
        print("Caluculation of band has not finished yet. So preparing band_nsc will be skipped.")
        flag = False
    elif calc_info["unitcell"]["band"] and not calc_info["unitcell"]["dielectric_rpa"]:
        print("Caluculation of dielectric_rpa has not finished yet. So preparing band_nsc will be skipped.")
        flag = False
    elif not calc_info["unitcell"]["band"] and not calc_info["unitcell"]["dielectric_rpa"]:
        print("Caluculation of band and dielectric_rpa have not finished yet. So preparing band_nsc will be skipped.")
        flag = False
    return flag
        
def preparation_cpd(piseset, preparation_info, elements):
    if not preparation_info["cpd"]:
        print("Preparing cpd.")
        os.makedirs("cpd", exist_ok=True)
        os.chdir("cpd")

        #競合相をMaterials projectから取得
        if len(elements) == 2:
            subprocess.run([f"pydefect_vasp mp -e {elements[0]} {elements[1]} --e_above_hull 0.0005"], shell=True)
        elif len(elements) == 3:
            subprocess.run([f"pydefect_vasp mp -e {elements[0]} {elements[1]} {elements[2]} --e_above_hull 0.0005"], shell=True)
        elif len(elements) == 4:
            subprocess.run([f"pydefect_vasp mp -e {elements[0]} {elements[1]} {elements[2]} {elements[3]} --e_above_hull 0.0005"], shell=True)

        #計算インプットの作成
        cpd_dir_list = make_dir_list()
        for target_dir in cpd_dir_list:
            prepare_input_files(piseset, target_dir, piseset.vise_task_command_opt, "opt")
        
        os.chdir("../")
        flag = True
    else:
        print("Preparation of cpd has already finished.")
        flag = True
    return flag

def preparation_defect(piseset, calc_info, preparation_info):
    if not preparation_info["defect"] and calc_info["unitcell"]["dos"]:
        print("Preparing defect.")
        os.makedirs("defect", exist_ok=True)
        os.chdir("defect")
        subprocess.run(["pydefect s -p ../unitcell/dos/POSCAR-finish --max_atoms 150"], shell=True)
        subprocess.run(["pydefect_vasp le -v ../unitcell/dos/repeat-*/AECCAR{0,2} -i all_electron_charge"], shell=True)
        subprocess.run(["pydefect_util ai --local_extrema volumetric_data_local_extrema.json -i 1 2"], shell=True)
        subprocess.run(["pydefect ds"], shell=True)
        subprocess.run(["pydefect_vasp de"], shell=True)

        #計算インプットの作成
        defect_dir_list = make_dir_list()
        for target_dir in defect_dir_list:
            prepare_input_files(piseset, target_dir, piseset.vise_task_command_defect, "defect")
        
        os.chdir("../")
        flag = True

    elif not calc_info["unitcell"]["dos"]:
        print("dos calculations have not finished yet. So preparing defect will be skipped.")
        flag = False

    elif preparation_info["defect"]:
        print("Preparation of defect has already finished.")
        flag = True
    return flag

def preparation_dopant_cpd(piseset, preparation_info, elements, dopant):
    if not preparation_info[f"{dopant}_cpd"]:
        print(f"Preparing {dopant}_cpd.")
        os.makedirs(f"dopant_{dopant}", exist_ok=True)
        os.chdir(f"dopant_{dopant}")
        os.makedirs("cpd", exist_ok=True)
        os.chdir("cpd")
        cwd = os.getcwd()

        #競合相をMaterials projectから取得
        if len(elements) == 2:
            subprocess.run([f"pydefect_vasp mp -e {elements[0]} {elements[1]} {dopant} --e_above_hull 0.0005"], shell=True)
        elif len(elements) == 3:
            subprocess.run([f"pydefect_vasp mp -e {elements[0]} {elements[1]} {elements[2]} {dopant} --e_above_hull 0.0005"], shell=True)
        elif len(elements) == 4:
            subprocess.run([f"pydefect_vasp mp -e {elements[0]} {elements[1]} {elements[2]} {elements[3]} {dopant} --e_above_hull 0.0005"], shell=True)

        #cpd内の重複を削除
        delete_duplication("../../cpd", cwd)

        #計算インプットの作成
        cpd_dir_list = make_dir_list()
        for target_dir in cpd_dir_list:
            prepare_input_files(piseset, target_dir, piseset.vise_task_command_opt, "opt")
        
        os.chdir("../../")
        flag = True
    else:
        print(f"Preparation of {dopant}_cpd has already finished.")
        flag = True
    return flag

def preparation_dopant_defect(piseset, preparation_info, dopant):
    if not preparation_info[f"{dopant}_defect"] and preparation_info["defect"]:
        print(f"Preparing {dopant}_defect.")
        os.makedirs(f"dopant_{dopant}", exist_ok=True)
        os.chdir(f"dopant_{dopant}")
        os.makedirs("defect", exist_ok=True)
        os.chdir("defect")

        subprocess.run(["cp ../../defect/supercell_info.json ./"], shell=True)
        subprocess.run([f"pydefect ds -d {dopant} -k {dopant}_i {dopant}_{piseset.substitution_site}"], shell=True)
        subprocess.run(["pydefect_vasp de"], shell=True)

        #計算インプットの作成
        defect_dir_list = make_dir_list()
        for target_dir in defect_dir_list:
            prepare_input_files(piseset, target_dir, piseset.vise_task_command_defect, "defect")
        
        os.chdir("../../")
        flag = True

    elif not preparation_info["defect"]:
        print(f"defect preparation have not finished yet. So preparing {dopant}_defect will be skipped.")
        flag = False

    elif preparation_info[f"{dopant}_defect"]:
        print(f"Preparation of {dopant}_defect has already finished.")
        flag = True
    return flag

class PreparationInfoMaker():
    def __init__(self):
        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()
        
        #calc_info.jsonの更新
        CalcInfoMaker()

        #preparation_target_listを作成
        if piseset.functional == "pbesol":
            preparation_target_list = ["unitcell","cpd", "defect"]
        else:
            preparation_target_list = ["unitcell","cpd", "defect", "band_nsc"]
        if piseset.dopants is not None:
            for dopant in piseset.dopants:
                preparation_target_list.append(f"{dopant}_cpd")
                preparation_target_list.append(f"{dopant}_defect")

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                #ファイルの読み込み
                preparation_info = initialize_preparetion_info(preparation_target_list)
                with open('calc_info.json') as f:
                    calc_info = json.load(f)
                

                #インプットファイルの準備
                preparation_info["unitcell"] = preparation_unitcell(piseset, calc_info, preparation_info)
                preparation_info["cpd"] = preparation_cpd(piseset, preparation_info, target_material.elements)
                preparation_info["defect"] = preparation_defect(piseset, calc_info, preparation_info)

                if piseset.functional == "pbesol":
                    preparation_info["band_nsc"] = preparation_band_nsc(piseset, calc_info, preparation_info)

                    if piseset.dopants is not None:
                        for dopant in piseset.dopants:
                            preparation_info[f"{dopant}_cpd"] = preparation_dopant_cpd(piseset, preparation_info, target_material.elements, dopant)
                            preparation_info[f"{dopant}_defect"] = preparation_dopant_defect(piseset, preparation_info, dopant)
                
                #preparation_info.jsonの保存
                with open("preparation_info.json", "w") as f:
                    json.dump(preparation_info, f, indent=4)

                os.chdir("../../")
            else:
                print(f"No such directory: {path}. So making {path} directory.")
                preparation_opt(piseset, target_material.material_id, target_material.formula_pretty)
                os.chdir("../../../../")
            
