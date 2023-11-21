import json
import os
import yaml
from collections import defaultdict
from pymatgen.io.vasp import Poscar
from pymatgen.io.vasp import Kpoints
from pymatgen.io.vasp.outputs import Vasprun
from pise_set import PiseSet
from target import TargetHandler
from common_function import get_label_from_chempotdiag

def check_analysis_alldone(list):
    for i in list:
        if i:
            flag = True
        else:
            flag = False
            break
    return flag

class Summury():
    def __init__(self):
        piseset = PiseSet()

        with open('symmetry_info.json') as f:
            symmetry_info = json.load(f)

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                if os.path.isfile("analysis_info.json"):
                    with open('analysis_info.json') as f:
                        analysis_info = json.load(f)

                    if check_analysis_alldone(analysis_info.values()):
                        print("All analysis has been completed. So making summary.")
                    
                        #summary_info.jsonを読み込み
                        summary_info = defaultdict(dict)

                        summary_info["symmetry"] = symmetry_info[target_material.formula_pretty]

                        summary_info["formula_pretty"] = target_material.formula_pretty
                        summary_info["material_id"] = target_material.material_id
                        if piseset.functional == "pbesol":
                            summary_info["functional"] = "pbesol+U_nsc_dd-hybrid"
                        else:
                            summary_info["functional"] = piseset.functional

                        #unitcellの情報を集める
                        poscar = Poscar.from_file("unitcell/opt/POSCAR-finish")
                        poscar_dict = poscar.as_dict()
                        summary_info["POSCAR"]["a"] = format(poscar_dict["structure"]["lattice"]["a"], ".3f")
                        summary_info["POSCAR"]["b"] = format(poscar_dict["structure"]["lattice"]["b"], ".3f")
                        summary_info["POSCAR"]["c"] = format(poscar_dict["structure"]["lattice"]["c"], ".3f")
                        summary_info["POSCAR"]["n_atoms"] = sum(poscar.natoms)

                        vasprun = Vasprun("unitcell/opt/vasprun.xml")
                        poscar = Poscar.from_file("unitcell/opt/POSCAR-finish")
                        final_energy = vasprun.final_energy
                        natoms = sum(poscar.natoms)
                        energy_per_atom = final_energy / natoms
                        summary_info["energy_per_atom"] = format(energy_per_atom, ".4f")

                        with open("unitcell/unitcell.yaml") as file:
                            unitcell_dict = yaml.safe_load(file)
                        summary_info["vbm"] = format(unitcell_dict["vbm"], ".3f")
                        summary_info["cbm"] = format(unitcell_dict["cbm"], ".3f")
                        summary_info["band_gap"] = format(unitcell_dict["cbm"] - unitcell_dict["vbm"], ".3f") 
                        summary_info["ele_dielectric_const"]["x"] = format(unitcell_dict["ele_dielectric_const"][0][0], ".3f")
                        summary_info["ele_dielectric_const"]["y"] = format(unitcell_dict["ele_dielectric_const"][1][1], ".3f")
                        summary_info["ele_dielectric_const"]["z"] = format(unitcell_dict["ele_dielectric_const"][2][2], ".3f")
                        summary_info["ion_dielectric_const"]["x"] = format(unitcell_dict["ion_dielectric_const"][0][0], ".3f")
                        summary_info["ion_dielectric_const"]["y"] = format(unitcell_dict["ion_dielectric_const"][1][1], ".3f")
                        summary_info["ion_dielectric_const"]["z"] = format(unitcell_dict["ion_dielectric_const"][2][2], ".3f")
                        
                        with open("unitcell/dos/effective_mass.json") as f:
                            effective_mass_dict = json.load(f)
                        summary_info["concentrations"] = effective_mass_dict["concentrations"]
                        summary_info["temperature"] = effective_mass_dict["temperature"]
                        summary_info["p"]["x"] = format(effective_mass_dict["p"][0][0][0], ".3f")
                        summary_info["p"]["y"] = format(effective_mass_dict["p"][0][1][1], ".3f")
                        summary_info["p"]["z"] = format(effective_mass_dict["p"][0][2][2], ".3f")
                        summary_info["n"]["x"] = format(effective_mass_dict["n"][0][0][0], ".3f")
                        summary_info["n"]["y"] = format(effective_mass_dict["n"][0][1][1], ".3f")
                        summary_info["n"]["z"] = format(effective_mass_dict["n"][0][2][2], ".3f")

                        #perfectの情報を集める
                        poscar = Poscar.from_file("defect/perfect/POSCAR")
                        poscar_dict = poscar.as_dict()
                        summary_info["SPOSCAR"]["a"] = format(poscar_dict["structure"]["lattice"]["a"], ".3f")
                        summary_info["SPOSCAR"]["b"] = format(poscar_dict["structure"]["lattice"]["b"], ".3f")
                        summary_info["SPOSCAR"]["c"] = format(poscar_dict["structure"]["lattice"]["c"], ".3f")
                        summary_info["SPOSCAR"]["n_atoms"] = sum(poscar.natoms)

                        kpoints = Kpoints.from_file("defect/perfect/KPOINTS")
                        kpoints_dict = kpoints.as_dict()
                        summary_info["KPOINTS"]["kpoints"] = kpoints_dict["kpoints"]
                        summary_info["KPOINTS"]["shift"] = kpoints_dict["usershift"]

                        #競合相のラベルの取得
                        summary_info["labels"] = get_label_from_chempotdiag("cpd/chem_pot_diag.json")
                        if os.path.isfile("pise_dopants_and_sites.yaml"):
                            with open("pise_dopants_and_sites.yaml") as file:
                                pise_dopants_and_sites = yaml.safe_load(file)
                            for dopant_and_site in pise_dopants_and_sites["dopants_and_sites"]:
                                dopant = dopant_and_site[0]
                                summary_info[dopant]["labels"] = get_label_from_chempotdiag(f"dopant_{dopant}/cpd/chem_pot_diag.json")
                            

                        #summary_info.jsonの保存
                        with open("summary_info.json", "w") as f:
                            json.dump(summary_info, f, indent=4)
                    else:
                        print("Analysis has not completed yet. So making summary will be skipped.")
                else:
                    print(f"No such directory: analysis_info.json. So making summary will be skipped.")

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")
        
if __name__ == '__main__':
    pass

