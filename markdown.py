import json
import os
from pise_set import PiseSet
from target import TargetHandler
from collections import defaultdict
from doping import get_dopants_list


def make_base_markdown(piseset, summary_info):

    if piseset.functional == "pbesol":
        band = "band_nsc"
    else:
        band = "band"

    markdown_summary = """## {formula_pretty}_{material_id} {functional}
# unitcell
![Alt text](unitcell/opt/primitivecell.png)

|  unitcell (primitive)  |    |
| ---- | ---- |
|  a  |  {poscar_a}  |
|  b |  {poscar_b}  |
|  c  |  {poscar_c}  |
|  n_atoms  |  {poscar_n_atoms}  |
|  symmetry  |  {symmetry}  |

## band
|  band  |    |
| ---- | ---- |
|  bandgap (eV)  |  {band_gap}  |
|  vbm (eV)  |  {vbm}  |
|  cbm (eV)  |  {cbm}  |

![Alt text](unitcell/{band}/band.png)

## band_alignment
![Alt text](surface/band_alignment.png)

## dielectric
|  dielectric  |    |
| ---- | ---- |
|  ele_dielectric_const_x |  {ele_dielectric_const_x}  |
|  ele_dielectric_const_y |  {ele_dielectric_const_y}  |
|  ele_dielectric_const_z |  {ele_dielectric_const_z}  |
|  ion_dielectric_const_x |  {ion_dielectric_const_x}  |
|  ion_dielectric_const_y |  {ion_dielectric_const_y}  |
|  ion_dielectric_const_z |  {ion_dielectric_const_z}  |

## effective_mass
|  effective_mass  |    |
| ---- | ---- |
|  concentrations |  {concentrations}  |
|  temperature |  {temperature}  |
|  p_x |  {p_x}  |
|  p_y |  {p_y}  |
|  p_z |  {p_z}  |
|  n_x |  {n_x}  |
|  n_y |  {n_y}  |
|  n_z |  {n_z}  |

## DOS
![Alt text](unitcell/dos/dos.png)

## Absorption coefficient
![Alt text](unitcell/abs/absorption_coeff.png)

## cpd
![Alt text](cpd/cpd.png)

## Supercell
![Alt text](defect/supercell.png)

|  supercell  |    |
| ---- | ---- |
|  a  |  {sposcar_a}  |
|  b |  {sposcar_b}  |
|  c  |  {sposcar_c}  |
|  n_atoms  |  {sposcar_n_atoms}  |
|  kpoints  |  {kpoints}  |
|  shift  |  {shift}  |

# defect formation energy""".format(formula_pretty = summary_info["formula_pretty"], 
                                    material_id = summary_info["material_id"], 
                                    functional = summary_info["functional"],
                                    poscar_a = summary_info["POSCAR"]["a"],
                                    poscar_b = summary_info["POSCAR"]["b"],
                                    poscar_c = summary_info["POSCAR"]["c"],
                                    poscar_n_atoms = summary_info["POSCAR"]["n_atoms"],
                                    symmetry = summary_info["symmetry"],
                                    band_gap = summary_info["band_gap"],
                                    vbm = summary_info["vbm"],
                                    cbm = summary_info["cbm"],
                                    band = band,
                                    ele_dielectric_const_x = summary_info["ele_dielectric_const"]["x"],
                                    ele_dielectric_const_y = summary_info["ele_dielectric_const"]["y"] ,
                                    ele_dielectric_const_z = summary_info["ele_dielectric_const"]["z"],
                                    ion_dielectric_const_x = summary_info["ion_dielectric_const"]["x"],
                                    ion_dielectric_const_y = summary_info["ion_dielectric_const"]["y"],
                                    ion_dielectric_const_z = summary_info["ion_dielectric_const"]["z"],
                                    concentrations = summary_info["concentrations"],
                                    temperature = summary_info["temperature"],
                                    p_x = summary_info["p"]["x"],
                                    p_y = summary_info["p"]["y"],
                                    p_z = summary_info["p"]["z"],
                                    n_x = summary_info["n"]["x"],
                                    n_y = summary_info["n"]["y"],
                                    n_z = summary_info["n"]["z"],
                                    sposcar_a = summary_info["SPOSCAR"]["a"],
                                    sposcar_b = summary_info["SPOSCAR"]["b"],
                                    sposcar_c = summary_info["SPOSCAR"]["c"],
                                    sposcar_n_atoms = summary_info["SPOSCAR"]["n_atoms"],
                                    kpoints = summary_info["KPOINTS"]["kpoints"],
                                    shift = summary_info["KPOINTS"]["shift"]
                                    )
    return markdown_summary

class Markdown():
    def __init__(self):
        piseset = PiseSet()

        #markdown_info.jsonを初期化
        markdown_info = defaultdict(dict)

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
            
                if os.path.isfile('summary_info.json'):
                    print("Loading summary_info.json")
                    with open('summary_info.json') as f:
                        summary_info = json.load(f)

                    summary = make_base_markdown(piseset, summary_info)
                    with open(f"{target_material.formula_pretty}_{target_material.material_id}_{summary_info['functional']}.md", mode='w') as f:
                        f.write(f"{summary}\n")
                        for label in summary_info["labels"]:
                            f.write(f"## {label}\n")
                            f.write(f"### energy_{label}_-5_5\n")
                            f.write(f"![Alt text](defect/energy_{label}_-5_5.png)\n")
                            f.write(f"### energy_{label}_default\n")
                            f.write(f"![Alt text](defect/energy_{label}_default.png)\n")

                        if os.path.isfile("pise_dopants_and_sites.yaml"):
                            dopants = get_dopants_list()
                            for dopant in dopants:
                                f.write(f"# dopant_{dopant}\n")
                                f.write("## cpd\n")
                                f.write(f"![Alt text](dopant_{dopant}/cpd/cpd.png)\n")
                                f.write("# defect formation energy\n")
                                for label in summary_info[dopant]["labels"]:
                                    f.write(f"## {label}\n")
                                    f.write(f"### energy_{label}_-5_5\n")
                                    f.write(f"![Alt text](dopant_{dopant}/defect/energy_{label}_-5_5.png)\n")
                                    f.write(f"### energy_{label}_default\n")
                                    f.write(f"![Alt text](dopant_{dopant}/defect/energy_{label}_default.png)\n")
                    markdown_info[f"{target_material.formula_pretty}_{target_material.material_id}"] = True
                else:
                    print("No such file: summary_info.json")
                    markdown_info[f"{target_material.formula_pretty}_{target_material.material_id}"] = False

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")
            
            #markdown_info.jsonの保存
            with open("markdown_info.json", "w") as f:
                json.dump(markdown_info, f, indent=4)
            