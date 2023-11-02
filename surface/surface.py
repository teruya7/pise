import json
import yaml
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal, getcontext, ROUND_HALF_UP
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.outputs import Vasprun, Locpot, VolumetricData, Outcar

#無極性かつ組成がズレ表面を対象としていることに注意
def calculation_surface_energy(surface_target_info):
    #bulkの計算結果をを取得
    bulk_structure = Structure.from_file("../unitcell/opt/POSCAR-finish")
    bulk_vasprun = Vasprun("../unitcell/opt/vasprun.xml")
    bulk_totalenergy_per_atom = bulk_vasprun.final_energy / bulk_structure.num_sites
    
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
        surface_totalenergy = surface_vasprun.final_energy
        surface_area = 2 * np.linalg.norm(np.cross(surface_structure.lattice.matrix[0], surface_structure.lattice.matrix[1]))
        surface_energy = (surface_totalenergy - bulk_totalenergy_per_atom * surface_structure.num_sites) / surface_area
        
        surface_energy_dict = defaultdict(dict)
        surface_energy_dict["surface_index"] = surface_index
        surface_energy_dict["identifier"] = identifier
        surface_energy_dict["path"] = path
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
        vbm_from_vacuum = unitcell["vbm"] - potential_difference
        cbm_from_vacuum = unitcell["cbm"] - potential_difference
        band_gap = cbm_from_vacuum - vbm_from_vacuum

    surface_energy_info["target"] = target
    surface_energy_info["bulk_like_potential"] = bulk_like_potential
    surface_energy_info["vacuum_potential"] = vacuum_potential
    surface_energy_info["potential_difference"] = potential_difference
    surface_energy_info["vbm_from_vacuum"] = vbm_from_vacuum
    surface_energy_info["cbm_from_vacuum"] = cbm_from_vacuum
    surface_energy_info["band_gap"] = band_gap
    
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

def plot_band_alignment(band_alignment_summary_info):
    c = getcontext()
    c.prec = 3
    c.rounding = ROUND_HALF_UP

    plt.rcParams['axes.xmargin'] = 0
    y_min = -20
    y_max = 0
    text_offset = 0.2

    fig = plt.figure()
    ax = fig.subplots()
    ax.set_ylabel("Energy relative to vacuum level (eV)")
    ax.set_xlim([-0.5, len(band_alignment_summary_info)-0.5])
    ax.set_ylim([y_min, y_max])

    for n, band_alignment_info in enumerate(band_alignment_summary_info):
        ax.bar(str(n) + "-" + band_alignment_info["target"], band_alignment_info["vbm_from_vacuum"]-y_min, bottom=y_min, color="lightblue", width=0.6)
        ax.bar(str(n) + "-" + band_alignment_info["target"], y_max-band_alignment_info["cbm_from_vacuum"], bottom=band_alignment_info["cbm_from_vacuum"], color="lightgreen", width=0.6)
        plt.text(n, band_alignment_info["vbm_from_vacuum"]-text_offset, -Decimal(band_alignment_info["vbm_from_vacuum"]), ha="center", va="top")
        plt.text(n, band_alignment_info["cbm_from_vacuum"]+text_offset, -Decimal(band_alignment_info["cbm_from_vacuum"]), ha="center", va="bottom")

    plt.savefig("band_alignment.pdf")
    plt.savefig("band_alignment.png")
