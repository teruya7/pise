import json
from collections import defaultdict
import os
import subprocess
import argparse
import delete_duplication

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--functional', default = "pbesol")
parser.add_argument('-d', '--dopant_list', nargs="*", default = None)
parser.add_argument('-s', '--substitution_target', default = None)
args = parser.parse_args()

#defaults
functional = args.functional
home = os.environ['HOME']
shell_scripts_path =f"{home}/pise"
dopant_list = args.dopant_list
substitution_target = args.substitution_target

#preparation_listを準備
if functional=="pbesol":
    preparation_list = ["unitcell", "cpd", "defect", "band_nsc"]
else:
    preparation_list = ["unitcell", "cpd", "defect"]

if dopant_list is not None:
    for dopant in dopant_list:
        preparation_list.append(f"{dopant}_cpd")
        preparation_list.append(f"{dopant}_defect")

with open("target_info.json") as f:
    target_list = json.load(f)

for material in target_list:
    formula = material["pretty_formula"]
    mpcode = material["task_id"]
    elements = material["elements"]
    element1 = elements[0]
    element2 = elements[1]
    try:
        element3 = elements[2]
        composition = 3 
    except IndexError:
        composition = 2

    print(f"Parsing {formula}_{mpcode}")
    path = f"{formula}_{mpcode}/{functional}"
    os.chdir(path)

    #preparation_info.jsonを読み込み
    if os.path.isfile("preparation_info.json"):
        print("Loading preparation_info.json")
        with open('preparation_info.json') as f:
            preparation_info_dict = json.load(f)
        for i in preparation_list:
            preparation_info_dict.setdefault(i, False)
    else:
        preparation_info_dict = defaultdict(dict)
        print("Making preparation_info.json")
        for i in preparation_list:
            preparation_info_dict[i] = False
    
    #calc_info.jsonを読み込み。
    with open('calc_info.json') as f:
        calc_info = json.load(f)
    
    #unitcellの計算インプットの準備
    if calc_info["unitcell"]["opt"] and not preparation_info_dict["unitcell"]:
        subprocess.run([f"sh {shell_scripts_path}/preparation_unitcell.sh"], shell=True)
        preparation_info_dict["unitcell"] = True
        print("Preparation of unitcell successfully finished.")
    elif not calc_info["unitcell"]["opt"]:
        print("Optimization calculation has not finished yet.")
    elif preparation_info_dict["unitcell"]:
        print("Preparation of unitcell has already done")
    
    #cpdの計算インプットの準備
    if not preparation_info_dict["cpd"]:     
        if composition==2:
            subprocess.run([f"sh {shell_scripts_path}/preparation_cpd.sh {element1} {element2}"], shell=True)
            preparation_info_dict["cpd"] = True
            print("Preparation of cpd successfully finished.")
        else:
            subprocess.run([f"sh {shell_scripts_path}/preparation_cpd.sh {element1} {element2}  {element3}"], shell=True)
            preparation_info_dict["cpd"] = True
            print("Preparation of cpd successfully finished.")
    else:
        print("Preparation of cpd has already done")

    #defectの計算インプットの準備
    if calc_info["unitcell"]["dos"] and not preparation_info_dict["defect"]:
        subprocess.run([f"sh {shell_scripts_path}/preparation_defect.sh"], shell=True)
        preparation_info_dict["defect"] = True
        print("Preparation of defect successfully finished.")
    elif not calc_info["unitcell"]["dos"]:
        print("dos calculation has not finished yet.")
    elif preparation_info_dict["defect"]:
        print("Preparation of defect has already done")

    #band_nscの計算インプットの準備
    if calc_info["unitcell"]["band"] and calc_info["unitcell"]["dielectric_rpa"] and not preparation_info_dict["band_nsc"]:
        #_info.jsonを読み込み。
        if os.path.isfile('aexx_info.json'):
            with open('aexx_info.json') as f:
                AEXX_info = json.load(f)
            AEXX = AEXX_info["AEXX"]
            subprocess.run([f"sh {shell_scripts_path}/preparation_band_nsc.sh {AEXX}"], shell=True)
            preparation_info_dict["band_nsc"] = True
            print("Preparation of band_nsc successfully finished.")
        else:
            print("aexx_info.json doesn't exist.")
    elif not calc_info["unitcell"]["band"] and not calc_info["unitcell"]["dielectric_rpa"]:
        print("Both band and dielectric_rpa calculation has not finished yet.")
    elif not calc_info["unitcell"]["band"]:
        print("band calculation has not finished yet.")
    elif not calc_info["unitcell"]["dielectric_rpa"]:
        print("dielectric_rpa calculation has not finished yet.")
    elif preparation_info_dict["band_nsc"]:
        print("Preparation of band_nsc has already done")
    
    if dopant_list is None:
        print("No dopants are considered.")
    else:
        for dopant in dopant_list:
            #cpdの計算インプットの準備
            if not preparation_info_dict[f"{dopant}_cpd"]:
                if composition==2:
                    subprocess.run([f"sh {shell_scripts_path}/preparation_dopant_cpd.sh {dopant} {element1} {element2}"], shell=True)
                    preparation_info_dict[f"{dopant}_cpd"] = True
                    print(f"Preparation of {dopant}_cpd successfully finished.")
                else:
                    subprocess.run([f"sh {shell_scripts_path}/preparation_dopant_cpd.sh {dopant} {element1} {element2}  {element3}"], shell=True)
                    preparation_info_dict[f"{dopant}_cpd"] = True
                    print(f"Preparation of {dopant}_cpd successfully finished.")
            else:
                print(f"Preparation of {dopant}_cpd has already done")
            #cpd内の重複を削除
            delete_duplication.delete_duplication("cpd", f"{dopant}/cpd")

            #defectの計算インプットの準備
            if preparation_info_dict["defect"] and not preparation_info_dict[f"{dopant}_defect"]:
                subprocess.run([f"sh {shell_scripts_path}/preparation_dopant_defect.sh {dopant} {substitution_target}"], shell=True)
                preparation_info_dict[f"{dopant}_defect"] = True
                print(f"Preparation of {dopant}_defect has already done")
            elif not preparation_info_dict["defect"]:
                print("Preparation of has not finished yet.")
            elif preparation_info_dict[f"{dopant}_defect"]:
                print(f"Preparation of {dopant}_defect has already done")
    print()
    #preparation_info.jsonを保存
    with open("preparation_info.json", "w") as f:
        json.dump(preparation_info_dict, f, indent=4)

    os.chdir("../../")

