import json
import os
import analysis_info
from collections import defaultdict
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--functional', default = "pbesol")
parser.add_argument('-d', '--dopant_list', nargs="*", default = None)
args = parser.parse_args()

#defaults
functional = args.functional
dopant_list = args.dopant_list

#analysis_listを準備
analysis_list = ["unitcell", "cpd", "defect"]
if dopant_list is not None:
    for dopant in dopant_list:
        analysis_list.append(f"{dopant}_cpd")
        analysis_list.append(f"{dopant}_defect")

with open("target_info.json") as f:
    target_list = json.load(f)

for material in target_list:
    formula = material["pretty_formula"]
    mpcode = material["task_id"]
    print(f"Parsing {formula}_{mpcode}")

    path = f"{formula}_{mpcode}/{functional}"
    os.chdir(path)
    
    #analysis_info.jsonを読み込み
    if os.path.isfile("analysis_info.json"):
        print("Loading analysis_info.json")
        with open('analysis_info.json') as f:
            analysis_info_dict = json.load(f)
        for i in analysis_list:
            analysis_info_dict.setdefault(i, False)
    else:
        analysis_info_dict = defaultdict(dict)
        print("Making analysis_info.json")
        for i in analysis_list:
            analysis_info_dict[i] = False

    with open('calc_info.json') as f:
        calc_info = json.load(f)

    #unitcellの解析を行うか判断
    if analysis_info_dict["unitcell"]:
        print("unitcell has been already analyzed")
    else:
        unitcell_flag = analysis_info.analysis("unitcell", "unitcell", calc_info["unitcell"].values(), analysis_info_dict, "unitcell.yaml")
        if unitcell_flag:
            print("unitcell has been successfully analyzed.")
        else:
            print("Analysis of unitcell failed.")

    #cpdの解析を行うか判断
    if analysis_info_dict["cpd"]:
        print("cpd has been already analyzed")
    else:
        cpd_flag = analysis_info.analysis("cpd", "cpd", calc_info["cpd"].values(), analysis_info_dict, "target_vertices.yaml", formula)
        if cpd_flag:
            print("cpd has been successfully analyzed.")
        else:
            print("Analysis of cpd failed.")

    #defectの解析を行うか判断
    if analysis_info_dict["unitcell"] and analysis_info_dict["cpd"]:
        if analysis_info_dict["defect"]:
            print("defect has been already analyzed")
            print()
        else:
            defect_flag = analysis_info.analysis("defect", "defect", calc_info["defect"].values(), analysis_info_dict, "defect_energy_summary.json")
            if defect_flag:
                print("defect has been successfully analyzed.")
                print()
            else:
                print("Analysis of defect failed.")
                print()
    else:
        print("Analysis of unitcell or cpd has not been completed. So, No analysis of defect will be performed.")
        print()

    for dopant in dopant_list:
        if os.path.isdir(f"dopant_{dopant}"):
            os.chdir(f"dopant_{dopant}")

            #dopant_cpdの解析を行うか判断
            if analysis_info_dict["cpd"]:
                if analysis_info_dict[f"{dopant}_cpd"]:
                    print("cpd has been already analyzed")
                else:
                    cpd_flag = analysis_info.analysis("cpd", "dopant_cpd", calc_info[f"{dopant}_cpd"].values(), analysis_info_dict, "target_vertices.yaml", formula)
                    if cpd_flag:
                        print(f"{dopant}_cpd has been successfully analyzed.")
                    else:
                        print(f"Analysis of {dopant}_cpd failed.")
            else:
                print(f"Analysis of cpd has not been completed. So, No analysis of {dopant}_cpd will be performed.")
            
            #dopant_defectの解析を行うか判断
            if analysis_info_dict["unitcell"] and analysis_info_dict["defect"] and analysis_info_dict[f"{dopant}_cpd"]:
                if analysis_info_dict[f"{dopant}_defect"]:
                    print(f"{dopant}_defect has been already analyzed")
                    print()
                else:
                    defect_flag = analysis_info.analysis("defect", "dopant_defect", calc_info[f"{i}_defect"].values(), analysis_info_dict, "defect_energy_summary.json")
                    if defect_flag:
                        print("defect has been successfully analyzed.")
                        print()
                    else:
                        print("Analysis of defect failed.")
                        print()
            else:
                print(f"Analysis of unitcell or {dopant}_cpd or defect have not been completed. So, No analysis of {dopant}_defect will be performed.")
                print()

            os.chdir("../")
        
    #解析の結果をanalysis_info.jsonに記録
    with open("analysis_info.json", "w") as f:
        json.dump(analysis_info_dict, f, indent=4)

    os.chdir("../../")