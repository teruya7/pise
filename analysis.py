import os
import subprocess
import string
import itertools
from pise_set import PiseSet
from collections import defaultdict
import json
import yaml
from target import TargetHandler
from calculation import Calculation
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pymatgen.core.composition import Composition
from pymatgen.core.periodic_table import Element
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.outputs import Vasprun, Locpot, VolumetricData, Outcar


#unstable_errorに対処し、target_vertices.yamlを作成する
def avoid_unstable_error(flag, target_material, dopant=None):
    while not flag:
        if not os.path.isfile("unstable_error.txt"):
            subprocess.run(["touch unstable_error.txt"], shell=True)
        with open("relative_energies.yaml") as file:
            relative_energies = yaml.safe_load(file)
            try:
                relative_energies[target_material.formula_pretty] -= 0.01
            except KeyError:
                print(f"Target {target_material.formula_pretty} is not in relative energy compounds, so stop here.")
                break
        with open("relative_energies.yaml", 'w') as file:
            yaml.dump(relative_energies, file)

        if dopant is not None:
            pydefect_cv_dopant(target_material, dopant)
        else:
            subprocess.run([f"pydefect cv -t {target_material.formula_pretty}"], shell=True)

        flag = check_analysis_done("target_vertices.yaml")

def pydefect_cv_dopant(target_material, dopant):
    elements = target_material.elements
    if len(elements) == 2:
        subprocess.run([f"pydefect cv -t {target_material.formula_pretty} -e {elements[0]} {elements[1]} {dopant}"], shell=True)
    elif len(elements) == 3:
        subprocess.run([f"pydefect cv -t {target_material.formula_pretty} -e {elements[0]} {elements[1]} {elements[2]} {dopant}"], shell=True)
    elif len(elements) == 4:
        subprocess.run([f"pydefect cv -t {target_material.formula_pretty} -e {elements[0]} {elements[1]} {elements[2]} {elements[3]} {dopant}"], shell=True)

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

def initialize_analysis_info(analysis_target_list):
    if os.path.isfile("analysis_info.json"):
        print("Loading analysis_info.json")
        print()
        with open('analysis_info.json') as f:
            analysis_info = json.load(f)
        for i in analysis_target_list:
            analysis_info.setdefault(i, False)
    else:
        analysis_info = defaultdict(dict)
        print("Making analysis_info.json")
        print()
        for i in analysis_target_list:
            analysis_info[i] = False
    return analysis_info

def check_calc_alldone(list):
    for i in list:
        if i:
            flag = True
        else:
            flag = False
            break
    return flag

def check_analysis_done(target_file):
    if os.path.isfile(target_file):
        return True
    else:
        return False

def get_label_from_chempotdiag(path_chem_pot_diag):
    labels = []
    with open(path_chem_pot_diag) as f:
        chem_pot = json.load(f)
    for label in chem_pot["target_vertices_dict"]:
        labels.append(label)
    return labels

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

def calculation_surface_energy(surface_target_info):
    #bulkの計算結果をを取得
    bulk_structure = Structure.from_file("../unitcell/opt/POSCAR-finish")
    bulk_vasprun = Vasprun("../unitcell/opt/vasprun.xml")
    bulk_totalenergy = bulk_vasprun.final_energy / bulk_structure.num_sites
    
    #最初のsurface_energyの比較用
    min_surface_energy = float("inf")

    for target in surface_target_info:
        surface_index = target["surface_index"]
        identifier = target["identifier"]
        cell_multiplicity = target["cell_multiplicity"]
        path = surface_index + "/" + identifier
        
        #surfaceの計算結果を取得
        surface_structure = Structure.from_file(f"{path}/POSCAR-finish")
        surface_vasprun = Vasprun(f"{path}/vasprun.xml")
        surface_totalenergy = surface_vasprun.final_energy / surface_structure.num_sites
        surface_area = 2 * np.linalg.norm(np.cross(surface_structure.lattice.matrix[0], surface_structure.lattice.matrix[1]))
        surface_energy = (surface_totalenergy - bulk_totalenergy) / surface_area
        
        surface_energy_dict = defaultdict(dict)
        surface_energy_dict["surface_index"] = surface_index
        surface_energy_dict["identifier"] = identifier
        surface_energy_dict["surface_totalenergy"] = surface_totalenergy
        surface_energy_dict["surface_area"] = surface_area
        surface_energy_dict["surface_energy"] = surface_energy
        surface_energy_dict["surface_energy_min"] = False

        #window（移動平均の幅）を求める
        outcar = Outcar(f"{path}/OUTCAR-finish")
        ngfz = outcar.ngf[2]
        window = int(ngfz) // int(cell_multiplicity)
        surface_energy_dict["window"] = window

        #surface_energy_info.jsonにデータを保存
        with open(f"{path}/surface_energy_info.json", "w") as f:
            json.dump(surface_energy_dict, f, indent=4)

        if surface_energy < min_surface_energy: 
            path_to_surface_energy_min = path

    #表面エネルギーが最小となる表面を特定する
    with open(f'{path_to_surface_energy_min}/surface_energy_info.json') as f:
        surface_energy_info = json.load(f)
    surface_energy_info["surface_energy_min"] = True
    with open(f"{path_to_surface_energy_min}/surface_energy_info.json", "w") as f:
            json.dump(surface_energy_info, f, indent=4)

def plot_averaged_locpot(surface_energy_info):
    #repeatのファイル名の取得
    path = Path('./')
    for repeat in path.glob('repeat-*'):
        locpot = Locpot.from_file(f"{repeat}/LOCPOT")

    structure = locpot.structure
    sites = structure.sites
    window = surface_energy_info["window"] 

    formula = structure.composition.reduced_formula
    surface_index_formatted = surface_energy_info["surface_index"].replace("_","")
    target = (f"{formula}({surface_index_formatted})")

    #z軸方向にslabモデルを作成したとする(x=0,y=1,z=2)
    axis_lable = "z"
    axis = 2
    num_grid = locpot.dim[axis]
    #slabモデルの原子の分率座標が0~1になるように変更する(後で利用しやすいように)
    coordinates_of_slab_atom = [ site.c if site.c < 0.9 else site.c - 1 for site in sites ]

    #bluk_center_grid番目のgridをbulkの代表点にする
    bulk_center_coordinate = (max(coordinates_of_slab_atom)+min(coordinates_of_slab_atom)) / 2
    bluk_center_grid = round(num_grid * bulk_center_coordinate)

    #vacuum_center_grid番目のgridをvaccumeの代表点にする
    vacuum_center_coordinate = (1+max(coordinates_of_slab_atom)) / 2
    vacuum_center_grid = round(num_grid * vacuum_center_coordinate)

    ### parse locpot
    coordinates_of_grid = VolumetricData.get_axis_grid(locpot, axis)
    potential = VolumetricData.get_average_along_axis(locpot, axis)

    pd.set_option("display.max_rows", None)
    dim2list = [[coordinates_of_grid[i], potential[i]] for i in range(len(coordinates_of_grid))]
    df = pd.DataFrame(dim2list, columns=["coordinate", "potential"])
    df_extended = pd.concat([df, df, df], ignore_index=True)
    df_extended["rolling"] = df_extended["potential"].rolling(window, center=True).mean()
    df_extended["re-rolling"] = df_extended["rolling"].rolling(window, center=True).mean()

    df_periodic = df_extended.iloc[range(len(df), len(df) * 2), :]
    df_periodic.reset_index(drop=True, inplace=True)

    ### write json
    bulk_like_potential = df_periodic["re-rolling"][bluk_center_grid - 1]
    vacuum_potential = df_periodic["re-rolling"][vacuum_center_grid - 1]
    potential_difference = vacuum_potential - bulk_like_potential
    with open("../../../unitcell/unitcell.yaml") as f:
        unitcell = yaml.safe_load(f)
        vbm = unitcell["vbm"] - potential_difference
        cbm = unitcell["cbm"] - potential_difference
        band_gap = cbm - vbm

    surface_energy_info["target"] = target
    surface_energy_info["bulk_like_potential"] = bulk_like_potential
    surface_energy_info["vacuum_potential"] = vacuum_potential
    surface_energy_info["potential_difference"] = potential_difference
    surface_energy_info["vbm"] = vbm
    surface_energy_info["cbm"] = cbm
    surface_energy_info["band_gap"] = band_gap

    with open("surface_energy_info.json", "w") as f:
        json.dump(surface_energy_info, f, indent=4)
    
    ### plot potentials
    plt.rcParams["axes.xmargin"] = 0
    fig = plt.figure()

    ax = fig.subplots()
    ax.set_xlabel(fr"Cartesian coordinate in ${axis_lable}$ direction ($\mathrm{{\AA}}$)")
    ax.set_ylabel("Potential energy (eV)")
    ax.plot(df["coordinate"], df["potential"], color="k", label="Planar average")
    ax.plot(df_periodic["coordinate"], df_periodic["rolling"], color="b", label=fr"Macroscopic average ($n$={window})")
    ax.plot(df_periodic["coordinate"], df_periodic["re-rolling"], color="r", label=fr"Averaged macroscopic average ($m$={window})")
    
    ax.legend()
    ax.plot(df["coordinate"][bluk_center_grid - 1], df_periodic["re-rolling"][bluk_center_grid - 1], 
            marker="|", color="r", markeredgewidth=1.5, markersize=8)
    ax.plot(df["coordinate"][vacuum_center_grid - 1], df_periodic["re-rolling"][vacuum_center_grid - 1], 
            marker="|", color="r", markeredgewidth=1.5, markersize=8)

    plt.title(target)
    plt.savefig("local_potenrials.pdf")
    plt.savefig("local_potenrials.png")

    # メモリ解放
    plt.clf()
    plt.close()

#---------------------------------------------------------------------------------

def analysis_abs(piseset, calc_info):
    if os.path.isfile("absorption_coeff.png"):
        return None
    
    if calc_info["unitcell"]["abs"]:
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
    if not calc_info["unitcell"][band]:
        print(f"{band} calculations have not finished yet. So analysis of unitcell will be skipped.")
        flag = False
        return flag
    
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

def analysis_cpd(target_material, calc_info, analysis_info):
    #cpdが解析済みかどうか確認
    if analysis_info["cpd"]:
        print("Analysis of cpd has already finished.")
        flag = True
        return flag
    
    #cpdの計算が完了しているか確認
    if not check_calc_alldone(calc_info["cpd"].values()):
        print("cpd calculations have not finished yet. So analysis of cpd will be skipped.")
        flag = False
        return flag

    print("Analyzing cpd.")
    os.chdir("cpd") 
    if not os.path.isdir("host"):
        subprocess.run(["ln -s ../unitcell/opt host"], shell=True)
    if not os.path.isfile("composition_energies.yaml"):
        subprocess.run(["pydefect_vasp mce -d */"], shell=True)
    if not os.path.isfile("relative_energies.yaml"):
        subprocess.run(["pydefect sre"], shell=True)
    if not os.path.isfile("target_vertices.yaml"):
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
        flag = True
        return flag
    
    #unitcellが解析済みかどうか確認
    if not analysis_info["unitcell"]:
        print("Analysis of unitcell has not finished yet. So analysis of defect will be skipped.")
        flag = False
        return flag
    
    #unitcellが解析済みかどうか確認
    if not analysis_info["cpd"]:
        print("Analysis of cpd has not finished yet. So analysis of defect will be skipped.")
        flag = False
        return flag

    #defectの計算が完了しているか確認
    if not check_calc_alldone(calc_info["defect"].values()):
        print("defect calculations have not finished yet. So analysis of defect will be skipped.")
        flag = False
        return flag

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

def analysis_dopant_cpd(dopant, target_material, calc_info, analysis_info):
    #dopantのcpdが解析済みかどうか確認
    if analysis_info[f"{dopant}_cpd"]:
        print(f"Analysis of {dopant}_cpd has already finished.")
        flag = True
        return flag
    
    #cpdが解析済みかどうか確認
    if not analysis_info["cpd"]:
        print(f"Analysis of cpd has not finished yet. So analysis of {dopant}_cpd will be skipped.")
        flag = False
        return flag
    
    #dopantのcpdフォルダがあるか確認
    if not os.path.isdir(f"dopant_{dopant}/cpd"):
        print(f"No such directory: cpd in dopant_{dopant}")
        flag = False
        return flag

    #dopantのcpdの計算が完了しているか確認
    if not check_calc_alldone(calc_info[f"dopant_{dopant}"]["cpd"].values()):
        print(f"dopant_{dopant}'s cpd calculations have not finished yet. So analysis of dopant_{dopant}'s cpd will be skipped.")
        flag = False
        return flag

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
        flag = True
        return flag
    
    #defectが解析済みかどうか確認
    if not analysis_info["defect"]:
        print(f"Analysis of defect has not finished yet. So analysis of {dopant}_defect will be skipped.")
        flag = False
        return flag
    
    #dopantのcpdが解析済みかどうか確認
    if not analysis_info[f"{dopant}_cpd"]:
        print(f"Analysis of {dopant}_cpd has not finished yet. So analysis of {dopant}_defect will be skipped.")
        flag = False
        return flag

    #dopnatのdefectフォルダがあるか確認
    if not os.path.isdir(f"dopant_{dopant}/defect"):
        print(f"No such directory: dopant_{dopant}'s defect")
        flag = False
        return flag
    
    #dopantのdefectの計算が完了しているか確認
    if not check_calc_alldone(calc_info[f"dopant_{dopant}"]["defect"].values()):
        print(f"dopant_{dopant}'s defect calculations have not finished yet. So analysis of dopant_{dopant}'s defect will be skipped.")
        flag = False
        return flag
    
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
        flag = True
        print("Analysis of surface has already finished.")
        return flag
    
    #surfaceの計算が完了しているか確認
    for surface in calc_info["surface"].keys():
        if not check_calc_alldone(calc_info["surface"][surface].values()):
            print("surface calculations have not finished yet. So analysis of cpd will be skipped.")
            flag = False
            return flag
        
    print("Analyzing surface.")
    os.chdir("surface") 
    with open('surface_target_info.json') as f:
        surface_target_info = json.load(f)

    calculation_surface_energy(surface_target_info)

    for target in surface_target_info:
        surface_index = target["surface_index"]
        identifier = target["identifier"]
        path = surface_index + "/" + identifier

        os.chdir(path)

        with open('surface_energy_info.json') as f:
            surface_energy_info = json.load(f)
        
        plot_averaged_locpot(surface_energy_info)
        os.chdir("../../")
        


    flag = False
    os.chdir("../")
    
    return flag

class Analysis():
    def __init__(self):
        piseset = PiseSet()
        #calc_info.jsonの更新
        Calculation()

        #analysis_target_listを作成
        analysis_target_list = ["unitcell","cpd", "defect"]
        if piseset.dopants is not None:
            for dopant in piseset.dopants:
                analysis_target_list.append(f"{dopant}_cpd")
                analysis_target_list.append(f"{dopant}_defect")
        analysis_target_list = analysis_target_list

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                #analysis_info.jsonとcalc_info.jsonの読み込み
                analysis_info = initialize_analysis_info(analysis_target_list)
                with open('calc_info.json') as f:
                    calc_info = json.load(f)

                #解析を実行
                analysis_info["unitcell"] = analysis_unitcell(piseset, calc_info, analysis_info)
                analysis_info["cpd"] = analysis_cpd(target_material, calc_info, analysis_info)
                analysis_info["defect"] = analysis_defect(calc_info, analysis_info)

                if piseset.abs:
                    analysis_abs(piseset, calc_info)
                
                if piseset.surface:
                    analysis_info.setdefault("surface", False)
                    analysis_surface(calc_info, analysis_info)

                if piseset.dopants is not None:
                    for dopant in piseset.dopants:
                        analysis_info[f"{dopant}_cpd"] = analysis_dopant_cpd(dopant, target_material, calc_info, analysis_info)
                        analysis_info[f"{dopant}_defect"] = analysis_dopant_defect(dopant, calc_info, analysis_info)
                    
                with open("analysis_info.json", "w") as f:
                    json.dump(analysis_info, f, indent=4)

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")

if __name__ == '__main__':
    print()