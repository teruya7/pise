from pise_set import PiseSet
from target import TargetHandler
import os
import json
from pydefect.analyzer.defect_energy import DefectEnergySummary
from pydefect.analyzer.defect_energy import ChargeEnergies
from cpd import get_label_from_chempotdiag
from collections import defaultdict

def pinning_levels_from_charge_energies(charge_energies: ChargeEnergies):

    result = []
    for name, charge_energy in charge_energies.charge_energies_dict.items():
        pin_levels = charge_energy.pinning_level(0, charge_energies.e_max)
        h_pin, e_pin = "-", "-"
        if pin_levels[0]:
            h_pin = f"charge {pin_levels[0][1]}, level {pin_levels[0][0]:.2f}"
        if pin_levels[1]:
            e_pin = f"charge {pin_levels[1][1]}, level {pin_levels[1][0]:.2f}"
        result.append([name, h_pin, e_pin])

    headers = ["defect", "hole pinning", "electron pinning"]
    return tabulate(result, headers=headers)

def show_pinning_levels(path_to_defect_energy_summary, label, allow_shallow=False, with_corrections=True):
    defect_energy_summary = DefectEnergySummary(path_to_defect_energy_summary)
    charge_energies = defect_energy_summary.charge_energies(label, allow_shallow, with_corrections,(0.0, defect_energy_summary.cbm))
    print(pinning_levels_from_charge_energies(charge_energies))

# def show_pinning_levels(args) -> None:
#     des: DefectEnergySummary = args.defect_energy_summary
#     charge_energies = des.charge_energies(args.label,
#                                           args.allow_shallow,
#                                           args.with_corrections,
#                                           (0.0, des.cbm))
#     print(pinning_levels_from_charge_energies(charge_energies))

def strict_pinning_level(target_material, analysis_info):
    if not analysis_info["cpd"] or not analysis_info["defect"]:
        return 
    
    electron_pinning_from_cbm = 0
    hole_pinning_from_vbm = 0

    defect_energy_summary: DefectEnergySummary("defect/defect_energy_summary.json")
    cbm = defect_energy_summary.cbm

    for label in get_label_from_chempotdiag("cpd/chem_pot_diag.json"):
        charge_energies = ChargeEnergies(defect_energy_summary.charge_energies(label,(0.0, cbm)))
        for name, charge_energy in charge_energies.charge_energies_dict.items():
            pin_levels = charge_energy.pinning_level(0, charge_energies.e_max)
            if pin_levels[0]:
                if hole_pinning_from_vbm < pin_levels[0][0]:
                    hole_pinning_from_vbm = pin_levels[0][0]
                    major_cause_of_hole_compensation = name
            if pin_levels[1]:
                if electron_pinning_from_cbm < abs(cbm - pin_levels[1][0]):
                    electron_pinning_from_cbm = abs(cbm - pin_levels[1][0])
                    major_cause_of_electron_compensation = name
    
    pinning_level_dict = defaultdict(dict)
    pinning_level_dict["target"] = target_material.formula_pretty + "_" + target_material.material_id
    pinning_level_dict["hole_pinning_from_vbm"] = {major_cause_of_hole_compensation : hole_pinning_from_vbm}
    pinning_level_dict["electron_pinning_from_cbm"] = {major_cause_of_electron_compensation : electron_pinning_from_cbm} 

    with open("pinning_level_info.json", "w") as f:
        json.dump(pinning_level_dict, f, indent=4)       


class PinningLevel():
    def __init__(self):
        piseset = PiseSet()

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                with open('analysis_info.json') as f:
                    analysis_info = json.load(f)

                strict_pinning_level(target_material, analysis_info)

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")