import os
import json
from pptx import Presentation
import pptx_functions
from extra_info import make_extra_info_json
from effective_mass import revise_effective_mass_json
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--functional', default = "pbesol")
args = parser.parse_args()

#defaults
functional = args.functional
home = os.environ['HOME']

with open("target_info.json") as f:
    target_list = json.load(f)

cwd = os.getcwd()

for material in target_list:
    formula = material["pretty_formula"]
    mpcode = material["task_id"]
    print(f"Parsing {formula}_{mpcode}")

    if pptx_functions.check_analysis_info(f"{formula}_{mpcode}/{functional}/analysis_info.json"):
        path = f"{formula}_{mpcode}/pbesol/unitcell"
        label = pptx_functions.get_label_from_chempotdiag(f"{formula}_{mpcode}/{functional}/cpd/chem_pot_diag.json")
        os.chdir(path)

        #presentationオブジェクトの作成
        prs = Presentation()

        pptx_functions.make_slide_with_image(prs,"primitive","opt")

        pptx_functions.make_slide_with_data(prs,"unitcell.yaml","../")

        pptx_functions.make_slide_with_image(prs,"band","band_nsc")

        pptx_functions.make_slide_with_image(prs,"dos","../dos")

        revise_effective_mass_json()
        pptx_functions.make_slide_with_data(prs,"effective_mass.yaml","./")

        pptx_functions.make_slide_with_image(prs,"absorption_coeff","../abs")

        pptx_functions.make_slide_with_image(prs,"cpd","../../cpd")

        pptx_functions.make_slide_with_image(prs,"supercell","../defect")

        os.chdir("perfect")
        make_extra_info_json()
        pptx_functions.make_slide_with_data(prs,"extra_info.yaml","./")

        os.chdir("../")
        for alfabet in label:
            pptx_functions.make_slide_with_image(prs,f"energy_{alfabet}","./")

        #結果をpptxとして保存
        if functional == "pbesol":
            functional_label = "PBEsol+U nsc_dd-hybrid"
        elif functional == "hse06":
            functional_label = "HSE06"
        pptx_name = f"{formula}_{mpcode}_{functional_label}"
        save_path = f"{home}/pptx/"
        pptx_functions.save_pptx(prs, pptx_name, save_path)

        os.chdir(cwd)
        print(f"pptx file of {formula}_{mpcode} has been successfully made.")
        print()
    else:
        print(f"Analysis of {formula}_{mpcode} has not yet been completed.")
        print()
