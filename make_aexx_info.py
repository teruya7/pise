import aexx_info
from collections import defaultdict
import json
import os

#defaults
functional = "pbesol"

with open("target_info.json") as f:
    target_list = json.load(f)

for material in target_list:
    formula = material["pretty_formula"]
    mpcode = material["task_id"]
    print(f"Parsing {formula}_{mpcode}")

    path = f"{formula}_{mpcode}/{functional}"
    os.chdir(path)

    with open('calc_info.json') as f:
        calc_info = json.load(f)
    
    if calc_info["unitcell"]["dielectric_rpa"]:
        aexx_info_dict = defaultdict(dict)
        aexx = aexx_info.calc_aexx("unitcell/dielectric_rpa/vasprun.xml")
        aexx_info_dict["AEXX"] = aexx
    else:
        print("dielectric_rpa calculation has not finished yet.")

    #aexx_info.jsonに書き込み
    with open("aexx_info.json", "w") as f:
        json.dump(aexx_info_dict, f, indent=4)
    
    os.chdir("../../")
