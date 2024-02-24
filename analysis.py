import os
import subprocess
import yaml
import itertools
import string
import copy
from pymatgen.core.composition import Composition
from pymatgen.core.periodic_table import Element
from pise_set import PiseSet
from collections import defaultdict
import json
from target import TargetHandler
from calculation import make_dir_list
from doping import get_dopants_list
from surface import plot_band_alignment, calculation_surface_energy, plot_averaged_locpot
from common_function import get_label_from_chempotdiag
from pydefect.chem_pot_diag.chem_pot_diag import RelativeEnergies, ChemPotDiagMaker, UnstableTargetError
from multiprocessing import Pool, cpu_count

#dopantのデータが消えないバグがある
def make_cpd_and_vertices(target, elements_list):
    rel_energies = RelativeEnergies.from_yaml("relative_energies.yaml")
    elements = elements_list or Composition(target).chemical_system.split("-")
    cpd_maker = ChemPotDiagMaker(rel_energies, elements, target)
    try:
        cpd = cpd_maker.chem_pot_diag
        cpd.to_json_file()
        cpd.to_target_vertices.to_yaml_file()
    except UnstableTargetError:
        avoid_unstable_error(target, elements_list)

def avoid_unstable_error(target, elements_list):
    if not os.path.isfile("unstable_error.txt"):
        subprocess.run(["touch unstable_error.txt"], shell=True)

    with open("relative_energies.yaml") as file:
        relative_energies = yaml.safe_load(file)
    
    relative_energies[target] -= 0.01

    with open("relative_energies.yaml", 'w') as file:
        yaml.dump(relative_energies, file)
    
    make_cpd_and_vertices(target, elements_list)

def reduced_cpd(dopant):
    #label作成用のアルファベットのリスト
    uppercase_list = list(itertools.chain(string.ascii_uppercase,("".join(pair) for pair in itertools.product(string.ascii_uppercase, repeat=2))))
    
    with open("chem_pot_diag.json") as f:
        chem_pot_diag = json.load(f)

    #取り除くverticesをリストにまとめる
    removed_vertices = []
    for label, target_vertices_dict in chem_pot_diag["target_vertices_dict"].items():
        competing_phases_list = [Composition(competing_phases) for competing_phases in target_vertices_dict["competing_phases"]]
        for competing_phase in competing_phases_list:
            if Element(dopant) in competing_phase:
                flag = False
                break
            else:
                flag = True
                continue
        if flag:
            removed_vertices.append(label)
    
    #新しいverticesを作成する
    reduced_target_vertices_dict = {}
    n_counter = 0
    for label, target_vertices_dict in chem_pot_diag["target_vertices_dict"].items():
        if label not in removed_vertices:
            reduced_target_vertices_dict[uppercase_list[n_counter]] = target_vertices_dict
            n_counter += 1
        if label in removed_vertices:
            print(f"Removed vertices: {label}, ", "competing_phases:", target_vertices_dict["competing_phases"])

    chem_pot_diag["target_vertices_dict"] = reduced_target_vertices_dict
    with open("chem_pot_diag.json", "w") as f:
        json.dump(chem_pot_diag, f)
    

    #target_verticesを作成する
    with open("target_vertices.yaml") as f:
        target_vertices = yaml.safe_load(f)

    reduced_target_vertices = {}
    reduced_target_vertices["target"] = target_vertices["target"]
    n_counter = 0
    for label, target_vertices_dict in target_vertices.items():
        if label == "target":
            continue
        if label not in removed_vertices:
            reduced_target_vertices[uppercase_list[n_counter]] = target_vertices_dict
            n_counter += 1

    with open("target_vertices.yaml", "w") as f:
        yaml.safe_dump(reduced_target_vertices, f, sort_keys=False)

def load_analysis_info():
    if os.path.isfile("analysis_info.json"):
        print("Loading analysis_info.json")
        with open('analysis_info.json') as f:
            analysis_info = json.load(f)
    else:
        analysis_info = defaultdict(dict)
        print("Making analysis_info.json")
    return analysis_info

def check_calc_alldone(list):
    for i in list:
        if i:
            flag = True
        else:
            flag = False
            break
    return flag

#特定のファイルの存在で解析が終了したかを判定する
def check_analysis_done(target_file):
    if os.path.isfile(target_file):
        return True
    else:
        return False

def make_calc_results(path):
    if not os.path.isfile(f"{path}/calc_results.json"):
        print(f"make_calc_results:{path}")
        subprocess.run([f"pydefect_vasp cr -d {path}"], shell=True)
    else:
        print(f"calc_results.json exists in {path}")

def make_efnv_correction(path):
    if not os.path.isfile(f"{path}/correction.json"):
        print(f"make_efnv_correction:{path}")
        subprocess.run([f"pydefect efnv -d {path} -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml"], shell=True)
    else:
        print(f"correction.json exists in {path}")

def make_efnv_correction_dopant(path):
    if not os.path.isfile(f"{path}/correction.json"):
        print(f"make_efnv_correction:{path}")
        subprocess.run([f"pydefect efnv -d {path} -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml"], shell=True)
    else:
        print(f"correction.json exists in {path}")

def make_defect_structure_info(path):
    if not os.path.isfile(f"{path}/defect_structure_info.json"):
        print(f"make_defect_structure_info:{path}")
        subprocess.run([f"pydefect dsi -d {path}"], shell=True)
    else:
        print(f"defect_structure_info.json exists in {path}")

def make_band_edge_orb_infos_and_eigval_plot(path):
    if not os.path.isfile(f"{path}/band_edge_orbital_infos.json"):
        print(f"make_band_edge_orb_infos_and_eigval_plot:{path}")
        subprocess.run([f"pydefect_vasp beoi -d {path} -pbes perfect/perfect_band_edge_state.json"], shell=True)
    else:
        print(f"band_edge_orbital_infos.json exists in {path}")

def make_band_edge_states(path):
    if not os.path.isfile(f"{path}/band_edge_states.json"):
        print(f"make_band_edge_states:{path}")
        subprocess.run([f"pydefect bes -d {path} -pbes perfect/perfect_band_edge_state.json"], shell=True)
    else:
        print(f"band_edge_states.json exists in {path}")

def make_perfect_band_edge_state():
    if not os.path.isfile("perfect/perfect_band_edge_state.json"):
        subprocess.run(["pydefect_vasp pbes -d perfect"], shell=True)
    else:
        print(f"perfect_band_edge_state.json exists in perfect")

def plot_energy_diagram(label):
    print(f"plotting defect formation energies : {label}")
    subprocess.run([f"pydefect pe -d defect_energy_summary.json -l {label} --allow_shallow"], shell=True)

def paralell_analysis(function, directory_list, num_process):
    with Pool(processes=num_process) as pool:
        pool.imap(function, directory_list)
        pool.close()
        pool.join()


#---------------------------------------------------------------------------------
def analysis_unitcell(piseset, calc_info, analysis_info):
    #unitcellが解析済みかどうか確認
    if analysis_info["unitcell"]:
        print("Analysis of unitcell has already finished.")
        return True

    #バンド端補正を行なったか判断
    if piseset.functional == "pbesol":
        band = "band_nsc"
    else:
        band = "band"

    #bandの計算が完了しているか確認
    try:
        if not calc_info["unitcell"][band]:
            print(f"{band} calculations have not finished yet. So analysis of unitcell will be skipped.")
            return False
    except KeyError:
        print(f"{band} calculations have not finished yet. So analysis of unitcell will be skipped.")
        return False

    #dielectricの計算が完了しているか確認
    try:
        if not calc_info["unitcell"]["dielectric"]:
            print("dielectric calculations have not finished yet. So analysis of unitcell will be skipped.")
            return False
    except KeyError:
        print("dielectric calculations have not finished yet. So analysis of unitcell will be skipped.")
        return False

    print("Analyzing unitcell.")
    os.chdir("unitcell")

    #unitcell.yamlを作成
    if band == "band_nsc":
        subprocess.run([piseset.vise_analysis_command_unitcell_nsc], shell=True)
    else:
        subprocess.run([piseset.vise_analysis_command_unitcell_hybrid], shell=True)

    #band.pdfを作成
    if os.path.isdir(band) and not os.path.isfile(f"{band}/band.pdf"):
        os.chdir(band)
        subprocess.run(["vise pb"], shell=True)
        os.chdir("../")

    #dos.pdfを作成
    if os.path.isdir("dos") and not os.path.isfile(f"{band}/dos.pdf"):
        os.chdir("dos")
        subprocess.run(["vise pd"], shell=True)
        os.chdir("../")

    #effective_mass.jsonを作成
    if os.path.isdir("dos") and not os.path.isfile("dos/effective_mass.json"):
        os.chdir("dos")
        subprocess.run([piseset.vise_analysis_command_effective_mass], shell=True)
        os.chdir("../")
    
    #absorption_coeff.pdfを作成
    if os.path.isdir("abs") and calc_info["unitcell"]["abs"] and not os.path.isfile("abs/absorption_coeff.pdf"):
        os.chdir("abs")
        subprocess.run(["vise pdf -ckk"], shell=True)
        os.chdir("../")

    os.chdir("../")

    return check_analysis_done("unitcell/unitcell.yaml")

def analysis_cpd(target_material, piseset, calc_info, analysis_info):
    #cpdが解析済みかどうか確認
    if analysis_info["cpd"]:
        print("Analysis of cpd has already finished.")
        return True
    
    #optの計算が終わっているかどうか確認
    if not calc_info["unitcell"]["opt"]:
        print("opt calculation has not finished yet. So analysis of cpd will be skipped.")
        return False

    #データベースからデータを取得
    if not piseset.is_hybrid[piseset.functional]:
        if os.path.isfile('cpd/competing_phases_info.json'):
            with open('cpd/competing_phases_info.json') as f:
                competing_phases_info = json.load(f)
            for competing_phase in competing_phases_info["competing_phases"]:
                try:
                    if calc_info["cpd"][competing_phase]:
                        pass
                    else:
                        subprocess.run([f"cp -r {piseset.path_to_cpd_database}/{piseset.functional}/{competing_phase} cpd/"], shell=True)
                        if os.path.isfile(f"cpd/{competing_phase}/is_converged.txt"):
                            calc_info["cpd"][competing_phase] = True
                except KeyError:
                    subprocess.run([f"cp -r {piseset.path_to_cpd_database}/{piseset.functional}/{competing_phase} cpd/"], shell=True)
                    if os.path.isfile(f"cpd/{competing_phase}/is_converged.txt"):
                        calc_info["cpd"][competing_phase] = True
            
            with open("calc_info.json", "w") as f:
                json.dump(calc_info, f, indent=4)
    
    #cpdの計算が完了しているか確認
    try:
        if not check_calc_alldone(calc_info["cpd"].values()):
            print("cpd calculations have not finished yet. So analysis of cpd will be skipped.")
            return False
    except KeyError:
        print("cpd calculations have not finished yet. So analysis of cpd will be skipped.")
        return False
    
    print("Analyzing cpd.")
    os.chdir("cpd") 
    if not os.path.isdir("host"):
        subprocess.run(["ln -s ../unitcell/opt host"], shell=True)
    if not os.path.isfile("composition_energies.yaml"):
        subprocess.run(["pydefect_vasp mce -d */"], shell=True)
    if not os.path.isfile("relative_energies.yaml"):
        subprocess.run(["pydefect sre"], shell=True)
    if not os.path.isfile("target_vertices.yaml"):
        if hasattr(target_material, "name"):
            make_cpd_and_vertices(target_material.name, target_material.elements)
        else:
            make_cpd_and_vertices(target_material.formula_pretty, target_material.elements)

    subprocess.run(["pydefect pc"], shell=True)

    os.chdir("../") 
    return check_analysis_done("cpd/target_vertices.yaml")

def analysis_defect(piseset, calc_info, analysis_info, num_process):
    #defectが解析済みかどうか確認
    if analysis_info["defect"]:
        print("Analysis of defect has already finished.")
        return True
    
    #unitcellが解析済みかどうか確認
    if not analysis_info["unitcell"]:
        print("Analysis of unitcell has not finished yet. So analysis of defect will be skipped.")
        return False
    
    #unitcellが解析済みかどうか確認
    if not analysis_info["cpd"]:
        print("Analysis of cpd has not finished yet. So analysis of defect will be skipped.")
        return False

    #defectの計算が完了しているか確認
    try:
        if not check_calc_alldone(calc_info["defect"].values()):
            print("defect calculations have not finished yet. So analysis of defect will be skipped.")
            return False
    except KeyError:
        print("defects are not calculated.")
        return False

    print("Analyzing defect.")
    os.chdir("defect")

    if piseset.parallel:
        dir_list = make_dir_list()
        dir_list_no_perfect = make_dir_list()
        dir_list_no_perfect.remove("perfect")

        paralell_analysis(make_calc_results, dir_list, num_process)
        paralell_analysis(make_efnv_correction, dir_list_no_perfect, num_process)
        paralell_analysis(make_defect_structure_info, dir_list_no_perfect, num_process)
        make_perfect_band_edge_state()
        paralell_analysis(make_band_edge_orb_infos_and_eigval_plot, dir_list_no_perfect, num_process)
        paralell_analysis(make_band_edge_states, dir_list_no_perfect, num_process)
        subprocess.run([f"pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
        subprocess.run([f"pydefect des -d *_*/ -u ../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
        subprocess.run([f"pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)

        #欠陥形成エネルギー図の描画
        labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
        paralell_analysis(plot_energy_diagram, labels, num_process)
    else:
        subprocess.run([f"pydefect_vasp cr -d *_*/ perfect"], shell=True)
        subprocess.run([f"pydefect efnv -d *_*/ -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml"], shell=True)
        subprocess.run([f"pydefect dsi -d *_*/ "], shell=True)
        make_perfect_band_edge_state()
        subprocess.run([f"pydefect_vasp beoi -d *_* -pbes perfect/perfect_band_edge_state.json"], shell=True)
        subprocess.run([f"pydefect bes -d *_*/ -pbes perfect/perfect_band_edge_state.json"], shell=True)
        subprocess.run([f"pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
        subprocess.run([f"pydefect des -d *_*/ -u ../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
        subprocess.run([f"pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)
        
        #欠陥形成エネルギー図の描画
        labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
        for label in labels:
            plot_energy_diagram(label)

    os.chdir("../") 
        
    return check_analysis_done("defect/energy_A.pdf")

def analysis_dopant_cpd(dopant, target_material, calc_info, analysis_info, piseset):
    #dopantのcpdが解析済みかどうか確認
    if analysis_info[f"{dopant}_cpd"]:
        print(f"Analysis of {dopant}_cpd has already finished.")
        return True
    
    #cpdが解析済みかどうか確認
    if not analysis_info["cpd"]:
        print(f"Analysis of cpd has not finished yet. So analysis of {dopant}_cpd will be skipped.")
        return False
    
    #dopantのcpdフォルダがあるか確認
    if not os.path.isdir(f"dopant_{dopant}/cpd"):
        print(f"No such directory: cpd in dopant_{dopant}")
        return False

    #データベースからデータを取得
    if os.path.isfile(f'dopant_{dopant}/cpd/competing_phases_info.json'):
        with open(f'dopant_{dopant}/cpd/competing_phases_info.json') as f:
            competing_phases_info = json.load(f)
        for competing_phase in competing_phases_info["competing_phases"]:
            try:
                if calc_info[f"dopant_{dopant}"]["cpd"][competing_phase]: #既にデータがある場合
                    pass
                else: #データはあるが計算が完了しておらず、データベースからデータを取得したい場合
                    subprocess.run([f"cp -r {piseset.path_to_cpd_database}/{piseset.functional}/{competing_phase} dopant_{dopant}/cpd/"], shell=True)
                    if os.path.isfile(f"dopant_{dopant}/cpd/{competing_phase}/is_converged.txt"):
                        calc_info[f"dopant_{dopant}"]["cpd"][competing_phase] = True
            except KeyError: #まだデータベースからデータを取得していない場合
                subprocess.run([f"cp -r {piseset.path_to_cpd_database}/{piseset.functional}/{competing_phase} dopant_{dopant}/cpd/"], shell=True)
                if os.path.isfile(f"dopant_{dopant}/cpd/{competing_phase}/is_converged.txt"):
                    calc_info[f"dopant_{dopant}"]["cpd"][competing_phase] = True
        
        with open("calc_info.json", "w") as f:
            json.dump(calc_info, f, indent=4)


    #dopantのcpdの計算が完了しているか確認
    try:
        if not check_calc_alldone(calc_info[f"dopant_{dopant}"]["cpd"].values()):
            print(f"dopant_{dopant}'s cpd calculations have not finished yet. So analysis of dopant_{dopant}'s cpd will be skipped.")
            return False
    except KeyError:
        print(f"dopant_{dopant}'s cpd calculations have not finished yet. So analysis of dopant_{dopant}'s cpd will be skipped.")
        return False

    print(f"Analyzing dopant_{dopant}'s cpd.")
    os.chdir(f"dopant_{dopant}/cpd")
    #host情報をシンボリックリンクで持ってくる 
    if not os.path.isdir("host"):
        subprocess.run(["ln -s ../../unitcell/opt host"], shell=True)

    #無添加相のcpdの情報をシンボリックリンクで持ってくる
    for cpd_dir_name in calc_info["cpd"].keys():
        if not os.path.isdir(cpd_dir_name):
            subprocess.run([f"ln -s ../../cpd/{cpd_dir_name} ./"], shell=True)
    
    #cpdの解析を行う
    if not os.path.isfile("composition_energies.yaml"):
        subprocess.run(["pydefect_vasp mce -d */"], shell=True)
    if not os.path.isfile("relative_energies.yaml"):
        subprocess.run(["pydefect sre"], shell=True)
    if not os.path.isfile("target_vertices.yaml"):
        #オブジェクトが参照渡しにならないようにdeepcopyを利用
        elements_list = copy.deepcopy(target_material.elements)
        elements_list.append(dopant)
        if hasattr(target_material, "name"):
            make_cpd_and_vertices(target_material.name, elements_list)
        else:
            make_cpd_and_vertices(target_material.formula_pretty, elements_list)
    
    #target_verticesを修正する（pydefectにエラーがある）
    reduced_cpd(dopant)

    if os.path.isfile("chem_pot_diag.json"):
        subprocess.run(["pydefect pc"], shell=True)
    os.chdir("../../") 
        
    return check_analysis_done(f"dopant_{dopant}/cpd/target_vertices.yaml")

def analysis_dopant_defect(dopant, piseset, calc_info, analysis_info, num_process):
    #dopantのdefectが解析済みかどうか確認
    if analysis_info[f"{dopant}_defect"]:
        print(f"Analysis of {dopant}_defect has already finished.")
        return True
    
    #defectが解析済みかどうか確認
    if not analysis_info["defect"]:
        print(f"Analysis of defect has not finished yet. So analysis of {dopant}_defect will be skipped.")
        return False
    
    #dopantのcpdが解析済みかどうか確認
    if not analysis_info[f"{dopant}_cpd"]:
        print(f"Analysis of {dopant}_cpd has not finished yet. So analysis of {dopant}_defect will be skipped.")
        return False

    #dopnatのdefectフォルダがあるか確認
    if not os.path.isdir(f"dopant_{dopant}/defect"):
        print(f"No such directory: dopant_{dopant}'s defect")
        return False
    
    #dopantのdefectの計算が完了しているか確認
    try:
        if not check_calc_alldone(calc_info[f"dopant_{dopant}"]["defect"].values()):
            print(f"dopant_{dopant}'s defect calculations have not finished yet. So analysis of dopant_{dopant}'s defect will be skipped.")
            return False
    except KeyError:
        print(f"dopant_{dopant}'s defect calculations have not finished yet. So analysis of dopant_{dopant}'s defect will be skipped.")
        return False
    
    print(f"Analyzing dopant_{dopant}'s defect.")
    os.chdir(f"dopant_{dopant}/defect") 
    if not os.path.isdir("perfect"):
            subprocess.run([f"ln -s ../../defect/perfect ./"], shell=True)
    
    if piseset.parallel:
        dir_list = make_dir_list()
        
        paralell_analysis(make_calc_results, dir_list, num_process)
        paralell_analysis(make_efnv_correction_dopant, dir_list, num_process)
        paralell_analysis(make_defect_structure_info, dir_list, num_process)
        make_perfect_band_edge_state()
        paralell_analysis(make_band_edge_orb_infos_and_eigval_plot, dir_list, num_process)
        paralell_analysis(make_band_edge_states, dir_list, num_process)

        #無添加相のdefectの情報をシンボリックリンクで持ってくる
        for defect_dir_name in calc_info["defect"].keys():
            if not os.path.isdir(defect_dir_name):
                subprocess.run([f"ln -s ../../defect/{defect_dir_name} ./"], shell=True)

        subprocess.run(["pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
        subprocess.run(["pydefect des -d *_*/ -u ../../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
        subprocess.run(["pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)
            
        #化学ポテンシャルの極限の条件のラベルを取得
        labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
        paralell_analysis(plot_energy_diagram, labels, num_process)
    else:
        subprocess.run([f"pydefect_vasp cr -d *_*/ perfect"], shell=True)
        subprocess.run([f"pydefect efnv -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml"], shell=True)
        subprocess.run([f"pydefect dsi -d *_*/ "], shell=True)
        make_perfect_band_edge_state()
        subprocess.run([f"pydefect_vasp beoi -d *_* -pbes perfect/perfect_band_edge_state.json"], shell=True)
        subprocess.run([f"pydefect bes -d *_*/ -pbes perfect/perfect_band_edge_state.json"], shell=True)
        subprocess.run([f"pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
        subprocess.run([f"pydefect des -d *_*/ -u ../../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
        subprocess.run([f"pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)

        #欠陥形成エネルギー図の描画
        labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
        for label in labels:
            plot_energy_diagram(label)

    os.chdir("../../")
        
    return check_analysis_done(f"dopant_{dopant}/defect/energy_A.pdf")

def analysis_surface(calc_info, analysis_info):
    #surfaceが解析済みかどうか確認
    if analysis_info["surface"]:
        print("Analysis of surface has already finished.")
        return True
    
    #unitcellが解析済みかどうか確認
    if not analysis_info["unitcell"]:
        print("Analysis of unitcell has not finished yet. So analysis of surface will be skipped.")
        return False
    
    #surfaceの計算が完了しているか確認
    for surface in calc_info["surface"].keys():
        if not check_calc_alldone(calc_info["surface"][surface].values()):
            print("surface calculations have not finished yet. So analysis of cpd will be skipped.")
            return False
        
    print("Analyzing surface.")
    os.chdir("surface") 
    with open('surface_target_info.json') as f:
        surface_target_info = json.load(f)

    calculation_surface_energy(surface_target_info)

    band_alignment_summary_info = []

    for target in surface_target_info:
        path = target["path"]

        os.chdir(path)

        with open('surface_energy_info.json') as f:
            surface_energy_info = json.load(f)

        #surface_energy_infoにバンドアラインメントに必要な情報を追加
        plot_averaged_locpot(surface_energy_info)

        band_alignment_dict = defaultdict(dict)
        band_alignment_dict["target"] = surface_energy_info["target"]
        band_alignment_dict["vbm_from_vacuum"] = surface_energy_info["vbm_from_vacuum"]
        band_alignment_dict["cbm_from_vacuum"] = surface_energy_info["cbm_from_vacuum"]
        band_alignment_summary_info.append(band_alignment_dict)

        with open("surface_energy_info.json", "w") as f:
            json.dump(surface_energy_info, f, indent=4)

        os.chdir("../../")
    
    plot_band_alignment(band_alignment_summary_info)

    #band_alignment_summary_info.jsonにデータを保存
    with open("band_alignment_summary_info.json", "w") as f:
        json.dump(band_alignment_summary_info, f, indent=4)    

    os.chdir("../")
    
    return check_analysis_done("surface/band_alignment.pdf")

class Analysis():
    def __init__(self):
        piseset = PiseSet()

        #並列処理
        num_process = int(cpu_count()*0.4)
        if piseset.parallel:
            print(f"num_process:{num_process}")
        else:
            print("Multiprocessing is switched off.")

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                analysis_info = load_analysis_info()

                with open('calc_info.json') as f:
                    calc_info = json.load(f)

                #解析を実行
                analysis_info.setdefault("unitcell", False)
                analysis_info["unitcell"] = analysis_unitcell(piseset, calc_info, analysis_info)

                analysis_info.setdefault("cpd", False)
                analysis_info["cpd"] = analysis_cpd(target_material, piseset, calc_info, analysis_info)

                analysis_info.setdefault("defect", False)
                analysis_info["defect"] = analysis_defect(piseset, calc_info, analysis_info, num_process)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        analysis_info.setdefault(f"{dopant}_cpd", False)
                        analysis_info[f"{dopant}_cpd"] = analysis_dopant_cpd(dopant, target_material, calc_info, analysis_info, piseset)
                        analysis_info.setdefault(f"{dopant}_defect", False)
                        analysis_info[f"{dopant}_defect"] = analysis_dopant_defect(dopant, piseset, calc_info, analysis_info, num_process)
                
                if piseset.surface:
                    analysis_info.setdefault("surface", False)
                    analysis_info["surface"] = analysis_surface(calc_info, analysis_info)

                    
                with open("analysis_info.json", "w") as f:
                    json.dump(analysis_info, f, indent=4)

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")

if __name__ == '__main__':
    print()