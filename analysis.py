import os
import subprocess
from pise_set import PiseSet
from collections import defaultdict
import json
from target import TargetHandler
from calculation import Calculation
from doping import get_dopants_list
from surface import plot_band_alignment, calculation_surface_energy, plot_averaged_locpot
from cpd import avoid_unstable_error, pydefect_cv_dopant, reduced_cpd, get_label_from_chempotdiag

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

def plot_pdf(file_name, vise_analysis_command):
    if not os.path.isfile(file_name):
        subprocess.run([vise_analysis_command], shell=True)
    else:
        print(f"{file_name} has already existed.")

def change_name(former_name, later_name):
    subprocess.run([f"mv {former_name} {later_name}"], shell=True)

def plot_energy_diagram(labels):
    for label in labels:
        subprocess.run([f"pydefect pe -d defect_energy_summary.json -l {label}"], shell=True)
        change_name(f"energy_{label}.pdf", f"energy_{label}_default.pdf")
        change_name(f"energy_{label}.png", f"energy_{label}_default.png")
        
        subprocess.run([f"pydefect pe -y -5 5 -d defect_energy_summary.json -l {label}"], shell=True)
        change_name(f"energy_{label}.pdf", f"energy_{label}_-5_5.pdf")
        change_name(f"energy_{label}.png", f"energy_{label}_-5_5.png")

#---------------------------------------------------------------------------------

def analysis_abs(piseset, calc_info):
    if os.path.isfile("absorption_coeff.png"):
        return None
    
    if calc_info["unitcell"]["abs"]:
        print("Analyzing abs.")
        os.chdir("unitcell/abs")
        plot_pdf("absorption_coeff.pdf", piseset.vise_analysis_command_plot_abs)
        os.chdir("../../")
    else:
        print("Calculation of abs has not finished yet.")
    
    return None
        
def analysis_unitcell(piseset, calc_info, analysis_info):
    #unitcellが解析済みかどうか確認
    if analysis_info["unitcell"]:
        flag = True
        print("Analysis of unitcell has already finished.")
        return flag

    #バンド端補正を行なったか判断
    if piseset.functional == "pbesol":
        band = "band_nsc"
    else:
        band = "band"

    #unitcellの計算が完了しているか確認
    try:
        if not calc_info["unitcell"][band]:
            print(f"{band} calculations have not finished yet. So analysis of unitcell will be skipped.")
            return False
    except KeyError:
        print(f"{band} calculations have not finished yet. So analysis of unitcell will be skipped.")
        return False

    if not calc_info["unitcell"]["dielectric"]:
        print("dielectric calculations have not finished yet. So analysis of unitcell will be skipped.")
        flag = False
        return flag

    print("Analyzing unitcell.")
    os.chdir("unitcell") 
    if band == "band_nsc":
        subprocess.run([piseset.vise_analysis_command_unitcell_nsc], shell=True)
    else:
        subprocess.run([piseset.vise_analysis_command_unitcell_hybrid], shell=True)
    flag = check_analysis_done("unitcell.yaml")

    if os.path.isdir(band):
        os.chdir(band)
        plot_pdf("band.pdf", piseset.vise_analysis_command_plot_band)
        os.chdir("../")
    else:
        flag = False

    if os.path.isdir("dos"):
        os.chdir("dos")
        if not os.path.isfile("effective_mass.json"):
            subprocess.run([piseset.vise_analysis_command_effective_mass], shell=True)
        plot_pdf("dos.pdf", piseset.vise_analysis_command_plot_dos)
        os.chdir("../")
    else:
        flag = False

    os.chdir("../")

    return flag

def analysis_cpd(target_material, piseset, calc_info, analysis_info):
    #cpdが解析済みかどうか確認
    if analysis_info["cpd"]:
        print("Analysis of cpd has already finished.")
        return True

    #データベースからデータを取得
    if piseset.cpd_database:
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
        else:
            return False
    
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
            subprocess.run([f"pydefect cv -t {target_material.name}"], shell=True)
        else:
            subprocess.run([f"pydefect cv -t {target_material.formula_pretty}"], shell=True)
    flag = check_analysis_done("target_vertices.yaml")
    
    avoid_unstable_error(flag, target_material)
    flag = check_analysis_done("target_vertices.yaml")

    #cpd.pdfを作成し、pngとして保存する
    subprocess.run(["pydefect pc"], shell=True)

    os.chdir("../") 
    return flag

def analysis_defect(calc_info, analysis_info):
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
        print("defect calculations have not finished yet. So analysis of defect will be skipped.")
        return False

    print("Analyzing defect.")
    os.chdir("defect") 
    subprocess.run(["pydefect_vasp cr -d *_*/ perfect"], shell=True)
    subprocess.run(["pydefect efnv -d *_*/ -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml"], shell=True)
    subprocess.run(["pydefect dsi -d *_*/"], shell=True)
    subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
    subprocess.run(["pydefect dsi -d *_*/"], shell=True)
    subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
    subprocess.run(["pydefect_vasp pbes -d perfect"], shell=True)
    subprocess.run(["pydefect_vasp beoi -d *_* -pbes perfect/perfect_band_edge_state.json"], shell=True)
    subprocess.run(["pydefect bes -d *_*/ -pbes perfect/perfect_band_edge_state.json"], shell=True)
    subprocess.run(["pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
    subprocess.run(["pydefect des -d *_*/ -u ../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
    subprocess.run(["pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)

    labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
    plot_energy_diagram(labels)
    flag = check_analysis_done("energy_A_default.pdf")

    os.chdir("../") 
        
    return flag

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
    if piseset.cpd_database:
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
        else:
            return False

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
        pydefect_cv_dopant(target_material, dopant)
    flag = check_analysis_done("target_vertices.yaml")

    avoid_unstable_error(flag, target_material, dopant)
    
    #target_verticesを修正する（pydefectにエラーがある）
    reduced_cpd(dopant)

    if os.path.isfile("chem_pot_diag.json"):
        subprocess.run(["pydefect pc"], shell=True)
    os.chdir("../../") 
        
    return flag

def analysis_dopant_defect(dopant, calc_info, analysis_info):
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

    subprocess.run(["pydefect_vasp cr -d *_*/ perfect"], shell=True)
    subprocess.run(["pydefect efnv -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml"], shell=True)
    subprocess.run(["pydefect dsi -d *_*/"], shell=True)
    subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
    subprocess.run(["pydefect dsi -d *_*/"], shell=True)
    subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
    subprocess.run(["pydefect_vasp pbes -d perfect"], shell=True)
    subprocess.run(["pydefect_vasp beoi -d *_* -pbes perfect/perfect_band_edge_state.json"], shell=True)
    subprocess.run(["pydefect bes -d *_*/ -pbes perfect/perfect_band_edge_state.json"], shell=True)

    #無添加相のdefectの情報をシンボリックリンクで持ってくる
    for defect_dir_name in calc_info["defect"].keys():
        if not os.path.isdir(defect_dir_name):
            subprocess.run([f"ln -s ../../defect/{defect_dir_name} ./"], shell=True)

    subprocess.run(["pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
    subprocess.run(["pydefect des -d *_*/ -u ../../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
    subprocess.run(["pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)
        
    #化学ポテンシャルの極限の条件のラベルを取得
    labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
    plot_energy_diagram(labels)

    flag = check_analysis_done("energy_A_default.pdf")

    os.chdir("../../")
        
    return flag

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

    flag = check_analysis_done("band_alignment.pdf")
    os.chdir("../")
    
    return flag

class Analysis():
    def __init__(self):
        piseset = PiseSet()
        #calc_info.jsonの更新
        Calculation()

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

                if piseset.abs:
                    analysis_abs(piseset, calc_info)

                analysis_info.setdefault("cpd", False)
                analysis_info["cpd"] = analysis_cpd(target_material, calc_info, analysis_info)

                analysis_info.setdefault("defect", False)
                analysis_info["defect"] = analysis_defect(calc_info, analysis_info)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        analysis_info.setdefault(f"{dopant}_cpd", False)
                        analysis_info[f"{dopant}_cpd"] = analysis_dopant_cpd(dopant, target_material, calc_info, analysis_info, piseset)
                        analysis_info.setdefault(f"{dopant}_defect", False)
                        analysis_info[f"{dopant}_defect"] = analysis_dopant_defect(dopant, calc_info, analysis_info)
                
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