from pise_set import PiseSet
from target import TargetHandler
import os
import json

def calculate_minimun_defect_formation_energy_at_vbm(defect_energy_summary, serach_condition):
    vbm = 0

    labels = []
    for label in defect_energy_summary["rel_chem_pots"]:
        labels.append(label)

    rel_chem_pots = defect_energy_summary["rel_chem_pots"]

    defects = []
    for defect in defect_energy_summary["defect_energies"]:
        defects.append(defect)

    for label in labels:
        min_defect_formation_energy_at_vbm = 100
        rel_chem_pot = rel_chem_pots[label]
        for defect in defects:

            atom_io = defect_energy_summary["defect_energies"][defect]["atom_io"]
            chemical_potential = 0
            for atom, num in atom_io.items():
                chemical_potential += rel_chem_pot[atom] * num

            for charge, defect_energy in zip(defect_energy_summary["defect_energies"][defect]["charges"], defect_energy_summary["defect_energies"][defect]["defect_energies"]):
                defect_formation_energy_at_vbm = defect_energy["formation_energy"] + defect_energy["energy_corrections"]["pc term"] + defect_energy["energy_corrections"]["alignment term"] + charge * vbm - chemical_potential
                if defect_formation_energy_at_vbm < min_defect_formation_energy_at_vbm:
                    min_defect_formation_energy_at_vbm = defect_formation_energy_at_vbm
                    min_defect = defect
                    min_charge = charge

        if min_defect_formation_energy_at_vbm >= serach_condition:
            print(f"label: {label}, defect: {min_defect}_{min_charge}, min_defect_formation_energy_at_vbm: {min_defect_formation_energy_at_vbm}")

def calculate_minimun_defect_formation_energy_at_cbm(defect_energy_summary, serach_condition):
    cbm = defect_energy_summary["cbm"]

    labels = []
    for label in defect_energy_summary["rel_chem_pots"]:
        labels.append(label)

    rel_chem_pots = defect_energy_summary["rel_chem_pots"]

    defects = []
    for defect in defect_energy_summary["defect_energies"]:
        defects.append(defect)

    for label in labels:
        min_defect_formation_energy_at_cbm = 100
        rel_chem_pot = rel_chem_pots[label]
        for defect in defects:

            atom_io = defect_energy_summary["defect_energies"][defect]["atom_io"]
            chemical_potential = 0
            for atom, num in atom_io.items():
                chemical_potential += rel_chem_pot[atom] * num

            for charge, defect_energy in zip(defect_energy_summary["defect_energies"][defect]["charges"], defect_energy_summary["defect_energies"][defect]["defect_energies"]):
                defect_formation_energy_at_cbm = defect_energy["formation_energy"] + defect_energy["energy_corrections"]["pc term"] + defect_energy["energy_corrections"]["alignment term"] + charge * cbm - chemical_potential
                if defect_formation_energy_at_cbm < min_defect_formation_energy_at_cbm:
                    min_defect_formation_energy_at_cbm = defect_formation_energy_at_cbm
                    min_defect = defect
                    min_charge = charge

        if min_defect_formation_energy_at_cbm >= serach_condition:
            print(f"label: {label}, defect: {min_defect}_{min_charge}, min_defect_formation_energy_at_cbm: {min_defect_formation_energy_at_cbm}")



class Search():
    def __init__(self):
        pass

    def vbm(self, serach_condition=-0.5):
        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                try:
                    with open('defect/defect_energy_summary.json') as f:
                        defect_energy_summary = json.load(f)
                        calculate_minimun_defect_formation_energy_at_vbm(defect_energy_summary, serach_condition)
                        os.chdir("../../")
                except FileNotFoundError:
                    print(f"No such file: defect_energy_summary.json")
                    os.chdir("../../")

            else:
                print(f"No such directory: {path}")
    
    def cbm(self, serach_condition=-0.5):
        #pise.yamlとtarget_info.jsonの読み込み
        piseset = PiseSet()

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                try:
                    with open('defect/defect_energy_summary.json') as f:
                        defect_energy_summary = json.load(f)
                        calculate_minimun_defect_formation_energy_at_cbm(defect_energy_summary, serach_condition)
                        os.chdir("../../")
                except FileNotFoundError:
                    print(f"No such file: defect_energy_summary.json")
                    os.chdir("../../")
                
            else:
                print(f"No such directory: {path}")


