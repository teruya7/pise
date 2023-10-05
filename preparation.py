from target import TargetHandler
from calculation import Calculation, make_dir_list
from pise_set import PiseSet
from cpd import delete_duplication
import os
from collections import defaultdict
import json
import subprocess
import shutil
import pathlib
import yaml
from pymatgen.io.vasp.outputs import Vasprun

#ファイルのリストを作成
def make_file_list():
    list = []
    for f in os.listdir("./"):
        if os.path.isfile(f):
            if not os.path.islink(f):
                list.append(f)
    return list

def calc_aexx(vasprun_path):
    vasprun = Vasprun(vasprun_path)
    epsilon_electronic = vasprun.epsilon_static
    AEXX = 1/((epsilon_electronic[0][0] + epsilon_electronic[1][1] + epsilon_electronic[2][2])/3)
    AEXX_formatted = '{:.2g}'.format(AEXX)
    return AEXX_formatted

def load_preparetion_info():
    if os.path.isfile("preparation_info.json"):
        print("Loading preparation_info.json")
        with open('preparation_info.json') as f:
            preparation_info = json.load(f)
    else:
        preparation_info = defaultdict(dict)
        print("Making preparation_info.json")
    return preparation_info

def check_viseset_done():
    if os.path.isfile("POTCAR"):
        return True
    else:
        return False

def prepare_job_script(job_script_path, job_script):
    cwd = os.getcwd()
    shutil.copy(f"{job_script_path}/{job_script}", cwd)
    touch = pathlib.Path("ready_for_submission.txt")
    touch.touch()

def prepare_vasp_inputs(target_dir, vise_task_command, job_script_path, job_script):
    print(f"Preparing {target_dir}.")
    os.makedirs(target_dir, exist_ok=True)
    os.chdir(target_dir)
    if not check_viseset_done():
        prepare_job_script(job_script_path, job_script)
        subprocess.run([vise_task_command], shell=True)
    os.chdir("../")

#---------------------------------------------------------
def preparation_opt(piseset, material_id, formula_pretty):
    print("Preparing opt.")
    functional = piseset.functional
    if not os.path.isdir(f"{formula_pretty}_{material_id}/{functional}/unitcell/opt"):
        os.makedirs(f"{formula_pretty}_{material_id}/{functional}/unitcell/opt", exist_ok=True)
        os.chdir(f"{formula_pretty}_{material_id}/{functional}")

        #vise.yamlの作成
        vise_yaml = piseset.vise_yaml
        vise_yaml["xc"] = functional
        if piseset.is_hybrid[functional]:
            vise_yaml["user_incar_settings"].setdefault("AEXX", piseset.aexx)
        with open("vise.yaml", "w") as f:
            yaml.dump(vise_yaml, f, sort_keys=False)

        os.chdir("unitcell/opt")
        if material_id != "None":
            if not check_viseset_done():
                subprocess.run([f"vise gp -m {material_id}"], shell=True)
                if piseset.is_hybrid[functional]:
                    prepare_job_script(piseset.job_script_path, piseset.job_table["opt_hybrid"])
                else:
                    prepare_job_script(piseset.job_script_path, piseset.job_table["opt"])
                subprocess.run([piseset.vise_task_command_opt], shell=True)
        else:
            cwd = os.getcwd()
            if not check_viseset_done():
                shutil.copy(f"{piseset.path_to_poscar}/{formula_pretty}_POSCAR", f"{cwd}/POSCAR")
                if piseset.is_hybrid[functional]:
                    prepare_job_script(piseset.job_script_path, piseset.job_table["opt_hybrid"])
                else:
                    prepare_job_script(piseset.job_script_path, piseset.job_table["opt"])
                subprocess.run([piseset.vise_task_command_opt], shell=True)
            
def preparation_unitcell(piseset, calc_info, preparation_info):
    #unitcellが準備済みか確認
    if preparation_info["unitcell"]:
        print("Preparation of unitcell has already finished.")
        flag = True
        return flag
    
    #optの計算が完了しているか確認
    if not calc_info["unitcell"]["opt"]:
        print("opt calculations have not finished yet. So preparing unitcell will be skipped.")
        flag = False
        return flag
    
    print("Preparing unitcell.")
    os.chdir("unitcell")

    if piseset.is_hybrid[piseset.functional]:
        prepare_vasp_inputs("band", piseset.vise_task_command_band, piseset.job_script_path, piseset.job_table["band_hybrid"])
        prepare_vasp_inputs("dos", piseset.vise_task_command_dos, piseset.job_script_path, piseset.job_table["dos_hybrid"])
        prepare_vasp_inputs("dielectric", piseset.vise_task_command_dielectric_hybrid, piseset.job_script_path, piseset.job_table["dielectric_hybrid"])
    else:
        prepare_vasp_inputs("band", piseset.vise_task_command_band, piseset.job_script_path, piseset.job_table["band"])
        prepare_vasp_inputs("dos", piseset.vise_task_command_dos, piseset.job_script_path, piseset.job_table["dos"])
        prepare_vasp_inputs("dielectric", piseset.vise_task_command_dielectric, piseset.job_script_path, piseset.job_table["dielectric"])

    #光吸収係数の計算は欠陥計算には関係ないので計算するかどうかは任意
    if piseset.abs:
        if piseset.is_hybrid[piseset.functional]:
            prepare_vasp_inputs("abs", piseset.vise_task_command_abs, piseset.job_script_path, piseset.job_table["abs_hybrid"])
        else:
            prepare_vasp_inputs("abs", piseset.vise_task_command_abs, piseset.job_script_path, piseset.job_table["abs"])

    if piseset.nsc: 
        prepare_vasp_inputs("dielectric_rpa", piseset.vise_task_command_dielectric_rpa, piseset.job_script_path, piseset.job_table["dielectric_rpa"])
    
    os.chdir("../")
    flag = True

    return flag

def preparation_band_nsc(piseset, calc_info, preparation_info):
    if preparation_info["band_nsc"]:
        print("Preparation of band_nsc has already finished.")
        flag = True
        return flag
    
    calc_info["unitcell"].setdefault("band", False)
    if not calc_info["unitcell"]["band"]:
        print("Caluculation of band has not finished yet. So preparing band_nsc will be skipped.")
        flag = False
        return flag
    
    calc_info["unitcell"].setdefault("dielectric_rpa", False)
    if not calc_info["unitcell"]["dielectric_rpa"]:
        print("Caluculation of dielectric_rpa has not finished yet. So preparing band_nsc will be skipped.")
        flag = False
        return flag
    
    if not os.path.isfile("unitcell/band/WAVECAR"):
        print("No such file: WAVECAR")
        flag = False
        return flag

    #vise.yamlの読み込み
    with open("vise.yaml") as file:
        vise_yaml = yaml.safe_load(file)
        vise_yaml["options"]["set_hubbard_u"] = False

    print("Preparing band_nsc.")
    os.chdir("unitcell")
    aexx = calc_aexx("dielectric_rpa/vasprun.xml")
    os.makedirs("band_nsc", exist_ok=True)
    os.chdir("band_nsc")

    #vise.yamlを作成
    with open("vise.yaml", "w") as f:
        yaml.dump(vise_yaml, f, sort_keys=False)

    if not check_viseset_done():
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

    return flag
        
def preparation_cpd(piseset, preparation_info, elements):
    if preparation_info["cpd"]:
        print("Preparation of cpd has already finished.")
        flag = True
        return flag
    
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
        if piseset.is_hybrid[piseset.functional]:
            prepare_vasp_inputs(target_dir, piseset.vise_task_command_opt, piseset.job_script_path, piseset.job_table["opt_hybrid"])
        else:
            prepare_vasp_inputs(target_dir, piseset.vise_task_command_opt, piseset.job_script_path, piseset.job_table["opt"])
    
    os.chdir("../")
    flag = True

    return flag

def preparation_defect(piseset, calc_info, preparation_info):
    if preparation_info["defect"]:
        print("Preparation of defect has already finished.")
        flag = True
        return flag
    
    calc_info["unitcell"].setdefault("dos", False)
    if not calc_info["unitcell"]["dos"]:
        print("dos calculations have not finished yet. So preparing defect will be skipped.")
        flag = False
        return flag
    
    print("Preparing defect.")
    os.makedirs("defect", exist_ok=True)
    os.chdir("defect")
    subprocess.run(["pydefect s -p ../unitcell/dos/POSCAR-finish --max_atoms 150"], shell=True)

    if os.path.isfile("supercell_info.json"):
        subprocess.run(["pydefect_vasp le -v ../unitcell/dos/repeat-*/AECCAR{0,2} -i all_electron_charge"], shell=True)
        subprocess.run(["pydefect_util ai --local_extrema volumetric_data_local_extrema.json -i 1 2"], shell=True)
        subprocess.run(["pydefect ds"], shell=True)
        subprocess.run(["pydefect_vasp de"], shell=True)
        
        #計算インプットの作成
        defect_dir_list = make_dir_list()
        for target_dir in defect_dir_list:
            if piseset.is_hybrid[piseset.functional]:
                prepare_vasp_inputs(target_dir, piseset.vise_task_command_defect, piseset.job_script_path, piseset.job_table["defect_hybrid"])
            else:
                prepare_vasp_inputs(target_dir, piseset.vise_task_command_defect, piseset.job_script_path, piseset.job_table["defect"])
        
        os.chdir("../")
        flag = True
    else:
        print("No such file: supercell_info.json")
        os.chdir("../")
        flag = False
        
        
    return flag

def preparation_dopant_cpd(piseset, preparation_info, elements, dopant):
    if preparation_info[f"{dopant}_cpd"]:
        print(f"Preparation of {dopant}_cpd has already finished.")
        flag = True
        return flag

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
        if piseset.is_hybrid[piseset.functional]:
            prepare_vasp_inputs(target_dir, piseset.vise_task_command_opt, piseset.job_script_path, piseset.job_table["opt_hybrid"])
        else:
            prepare_vasp_inputs(target_dir, piseset.vise_task_command_opt, piseset.job_script_path, piseset.job_table["opt"])
    
    os.chdir("../../")
    flag = True

    return flag

def preparation_dopant_defect(piseset, preparation_info, dopant, site):
    if preparation_info[f"{dopant}_defect"]:
        print(f"Preparation of {dopant}_defect has already finished.")
        flag = True
        return flag

    if not preparation_info["defect"]:
        print(f"defect preparation have not finished yet. So preparing {dopant}_defect will be skipped.")
        flag = False
        return flag

    if not preparation_info[f"{dopant}_defect"] and preparation_info["defect"]:
        print(f"Preparing {dopant}_defect.")
        os.makedirs(f"dopant_{dopant}", exist_ok=True)
        os.chdir(f"dopant_{dopant}")
        os.makedirs("defect", exist_ok=True)
        os.chdir("defect")

        subprocess.run(["cp ../../defect/supercell_info.json ./"], shell=True)
        
        #dopantがHの時はpydefectでHの格子間のPOSCARを作成しない
        if dopant == "H":
            subprocess.run([f"pydefect ds -d {dopant} -k {dopant}_{site}"], shell=True)
        else:
            subprocess.run([f"pydefect ds -d {dopant} -k {dopant}_i {dopant}_{site}"], shell=True)

        subprocess.run(["pydefect_vasp de"], shell=True)
        subprocess.run(["rm -r perfect"], shell=True)

        #計算インプットの作成
        defect_dir_list = make_dir_list()
        for target_dir in defect_dir_list:
            if piseset.is_hybrid[piseset.functional]:
                prepare_vasp_inputs(target_dir, piseset.vise_task_command_defect, piseset.job_script_path, piseset.job_table["defect_hybrid"])
            else:
                prepare_vasp_inputs(target_dir, piseset.vise_task_command_defect, piseset.job_script_path, piseset.job_table["defect"])
        
        os.chdir("../../")
        flag = True

    return flag

def preparation_surface(piseset, calc_info, preparation_info):
    if not calc_info["unitcell"]["opt"]:
        print("Calculation of opt has not finished yet.")
        flag = False
        return flag
    
    if preparation_info["surface"]:
        print(f"Preparation of surface has already finished.")
        flag = True
        return flag
    
    print("Preparing surface.")
    os.makedirs("surface", exist_ok=True)
    os.chdir("surface")

    #vise_surface_yamlの作成
    functional = piseset.functional
    vise_surface_yaml = piseset.vise_surface_yaml
    vise_surface_yaml["xc"] = functional
    if piseset.is_hybrid[functional]:
        vise_surface_yaml["user_incar_settings"].setdefault("AEXX", piseset.aexx)
    with open("vise.yaml", "w") as f:
        yaml.dump(vise_surface_yaml, f, sort_keys=False)
    
    subprocess.run(["cp ../unitcell/opt/POSCAR-finish POSCAR"], shell=True)
    subprocess.run([f"perl {piseset.path_to_tsubo} --unique_nonpolar {piseset.h} {piseset.k} {piseset.l} {piseset.cap} < POSCAR >| tempfile1"], shell=True)
    subprocess.run([f"perl {piseset.path_to_tsubo} --termination_polarity_list tempfile1 < POSCAR >| tempfile2"], shell=True)
    subprocess.run(["egrep 'A|B' tempfile2 >| tempfile3"], shell=True)
    #slabモデルを作成
    make_surface_log = subprocess.run([f"perl {piseset.path_to_tsubo} --slab_poscar_list tempfile3 {piseset.slab_thickness} {piseset.vaccum_thickness} < POSCAR | grep Nonpolar"], capture_output=True, text=True, shell=True).stdout
    #出力例 Nonpolar type A surface: 1_0_0/POSCAR.NPA.0.E. cell_multiplicity: 13 (tsubo.perlの出力をいじる必要がある)
    print(make_surface_log)

    surface_target_info = []
    for line in make_surface_log.splitlines():
        splited_line = line.split()
        surface_dict = defaultdict(dict)
        #無極性表面のみを検討の対象とする
        if splited_line[2] == "A" or splited_line[2] == "B":
            surface_index = splited_line[4].split("/")[0]
            identifier = splited_line[4].split("/")[1][7:]
            cell_multiplicity = splited_line[6]
            surface_dict["surface_index"] = surface_index
            surface_dict["identifier"] = identifier
            surface_dict["cell_multiplicity"] = cell_multiplicity
            surface_dict["path"] = surface_index + "/" + identifier
            surface_target_info.append(surface_dict)
    
    for target in surface_target_info:
        surface_index = target["surface_index"]
        identifier = target["identifier"]
        os.chdir(surface_index)
        os.makedirs(identifier, exist_ok=True)
        subprocess.run([f"cp POSCAR.{identifier} {identifier}/POSCAR"], shell=True)
        if piseset.is_hybrid[piseset.functional]:
            prepare_vasp_inputs(target, piseset.vise_task_command_surface, piseset.job_script_path, piseset.job_table["surface_hybrid"])
        else:
            prepare_vasp_inputs(target, piseset.vise_task_command_surface, piseset.job_script_path, piseset.job_table["surface"])
        os.chdir("../")

    #surface_info.jsonにデータを保存
    with open("surface_target_info.json", "w") as f:
        json.dump(surface_target_info, f, indent=4)

    os.chdir("../")

    flag = True
        
    return flag
   

class Preparation():
    def __init__(self):
        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()
        
        #calc_info.jsonの更新
        Calculation()

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                preparation_info = load_preparetion_info()

                with open('calc_info.json') as f:
                    calc_info = json.load(f)
                
                preparation_info.setdefault("unitcell", False)
                preparation_info["unitcell"] = preparation_unitcell(piseset, calc_info, preparation_info)

                preparation_info.setdefault("cpd", False)
                preparation_info["cpd"] = preparation_cpd(piseset, preparation_info, target_material.elements)

                preparation_info.setdefault("defect", False)
                preparation_info["defect"] = preparation_defect(piseset, calc_info, preparation_info)

                if piseset.nsc:
                    preparation_info["band_nsc"] = preparation_band_nsc(piseset, calc_info, preparation_info)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    with open("pise_dopants_and_sites.yaml") as file:
                        pise_dopants_and_sites = yaml.safe_load(file)
                    for dopant_and_site in pise_dopants_and_sites["dopants_and_sites"]:
                        dopant = dopant_and_site[0]
                        site = dopant_and_site[1]

                        preparation_info.setdefault(f"{dopant}_cpd", False)
                        preparation_info[f"{dopant}_cpd"] = preparation_dopant_cpd(piseset, preparation_info, target_material.elements, dopant)
                        
                        preparation_info.setdefault(f"{dopant}_defect", False)
                        preparation_info[f"{dopant}_defect"] = preparation_dopant_defect(piseset, preparation_info, dopant, site)
                
                if piseset.surface:
                    preparation_info.setdefault("surface", False)
                    preparation_info["surface"] = preparation_surface(piseset, calc_info, preparation_info)

                #preparation_info.jsonの保存
                with open("preparation_info.json", "w") as f:
                    json.dump(preparation_info, f, indent=4)

                os.chdir("../../")
            else:
                print(f"No such directory: {path}. So making {path} directory.")
                preparation_opt(piseset, target_material.material_id, target_material.formula_pretty)
                os.chdir("../../../../")

            
