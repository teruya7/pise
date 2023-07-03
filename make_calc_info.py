import json
from collections import defaultdict
import os
import calc_info
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--functional', default = "pbesol")
args = parser.parse_args()

#defaults
functional = args.functional
dopant_list = ["N", "C", "F", "O"]
if functional == "pbesol":
    unitcell_list = ["opt", "band", "dos", "dielectric", "band_nsc", "dielectric_rpa", "abs"]
else:
    unitcell_list = ["opt", "band", "dos", "dielectric", "abs"]

with open("target_info.json") as f:
    target_list = json.load(f)

for material in target_list:
    formula = material["pretty_formula"]
    mpcode = material["task_id"]
    print(f"Parsing {formula}_{mpcode}")
    calc_info_dict = defaultdict(dict)

    path = f"{formula}_{mpcode}/{functional}"
    os.chdir(path)

    calc_info.make_calculation_info("unitcell", calc_info_dict, unitcell_list)
    calc_info.make_calculation_info("cpd", calc_info_dict)
    calc_info.make_calculation_info("defect", calc_info_dict)

    for i in dopant_list:
        if os.path.isdir(i):
            os.chdir(i)
            calc_info.make_calculation_info("cpd", calc_info_dict, dopant=i)
            calc_info.make_calculation_info("defect", calc_info_dict, dopant=i)
            os.chdir("../")

    with open("calc_info.json", "w") as f:
        json.dump(calc_info_dict, f, indent=4)

    os.chdir("../../")
