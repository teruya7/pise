import json
import os
import yaml
from pise_set import PiseSet
from target import TargetHandler
from collections import defaultdict
from doping import get_dopants_list


#symmetryをsummary_infoに統合したい
def write_primitivecell_info(markdown, summary_info):
    markdown.write("# unitcell\n")
    markdown.write("![Alt text](unitcell/opt/primitivecell.png)\n")
    markdown.write("|  unitcell (primitive)  |    |\n")
    markdown.write("| ---- | ---- |\n")
    markdown.write(f'|  a  |  {summary_info["POSCAR"]["a"]}  |\n')
    markdown.write(f'|  b  |  {summary_info["POSCAR"]["b"]}  |\n')
    markdown.write(f'|  c  |  {summary_info["POSCAR"]["c"]}  |\n')
    markdown.write(f'|  n_atoms  |  {summary_info["POSCAR"]["n_atoms"]}  |\n')
    markdown.write(f'|  symmetry  |  {summary_info["symmetry"]}  |\n')
    markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_band_info(markdown, summary_info, piseset):

    if piseset.functional == "pbesol":
        band = "band_nsc"
    else:
        band = "band"

    markdown.write("## band\n")
    markdown.write(f'![Alt text](unitcell/{band}/band.png)\n')
    markdown.write("|  band  |    |\n")
    markdown.write("| ---- | ---- |\n")
    markdown.write(f'|  bandgap (eV)  |  {summary_info["band_gap"]}  |\n')
    markdown.write(f'|  vbm (eV)  |  {summary_info["vbm"]}  |\n')
    markdown.write(f'|  cbm (eV)  |  {summary_info["cbm"]}  |\n')
    markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_band_alignment_info(markdown):
    markdown.write("## band_alignment\n")
    markdown.write(f"![Alt text](surface/band_alignment.png)\n")
    markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_dielectric_info(markdown, summary_info):
    markdown.write("## dielectric\n")
    markdown.write("|  dielectric  |    |\n")
    markdown.write("| ---- | ---- |\n")
    markdown.write(f'|  ele_dielectric_const_x |  {summary_info["ele_dielectric_const"]["x"]}  |\n')
    markdown.write(f'|  ele_dielectric_const_y |  {summary_info["ele_dielectric_const"]["y"]}  |\n')
    markdown.write(f'|  ele_dielectric_const_z |  {summary_info["ele_dielectric_const"]["z"]}  |\n')
    markdown.write(f'|  ion_dielectric_const_x |  {summary_info["ion_dielectric_const"]["x"]}  |\n')
    markdown.write(f'|  ion_dielectric_const_y |  {summary_info["ion_dielectric_const"]["y"]}  |\n')
    markdown.write(f'|  ion_dielectric_const_z |  {summary_info["ion_dielectric_const"]["z"]}  |\n')
    # markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_effective_mass_info(markdown, summary_info):
    markdown.write("## effective_mass\n")
    markdown.write("|  effective_mass  |    |\n")
    markdown.write("| ---- | ---- |\n")
    markdown.write(f'|  concentrations |  {summary_info["concentrations"]}  |\n')
    markdown.write(f'|  temperature |  {summary_info["temperature"]}  |\n')
    markdown.write(f'|  p_x |  {summary_info["p"]["x"]}  |\n')
    markdown.write(f'|  p_y |  {summary_info["p"]["y"]}  |\n')
    markdown.write(f'|  p_z |  {summary_info["p"]["z"]}  |\n')
    markdown.write(f'|  n_x |  {summary_info["n"]["x"]}  |\n')
    markdown.write(f'|  n_y |  {summary_info["n"]["y"]}  |\n')
    markdown.write(f'|  n_z |  {summary_info["n"]["z"]}  |\n')
    markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_dos_info(markdown):
    markdown.write("## DOS\n")
    markdown.write("![Alt text](unitcell/dos/dos.png)\n")
    markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_abs_info(markdown):
    markdown.write("## Absorption coefficient\n")
    markdown.write("![Alt text](unitcell/abs/absorption_coeff.png)\n")
    markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_supercell_info(markdown, summary_info):
    markdown.write("# supercell\n")
    markdown.write("![Alt text](defect/supercell.png)\n")
    markdown.write("|  supercell  |    |\n")
    markdown.write("| ---- | ---- |\n")
    markdown.write(f'|  a  |  {summary_info["SPOSCAR"]["a"]}  |\n')
    markdown.write(f'|  b  |  {summary_info["SPOSCAR"]["b"]}  |\n')
    markdown.write(f'|  c  |  {summary_info["SPOSCAR"]["c"]}  |\n')
    markdown.write(f'|  n_atoms  |  {summary_info["SPOSCAR"]["n_atoms"]}  |\n')
    markdown.write(f'|  kpoints  |  {summary_info["KPOINTS"]["kpoints"]}  |\n')
    markdown.write(f'|  shift  |  {summary_info["KPOINTS"]["shift"]}  |\n')
    markdown.write('<div style="page-break-before:always"></div>\n\n')

def write_defect_info(markdown):
    with open("defect/defect_in.yaml") as file:
        defect_in = yaml.safe_load(file)
    markdown.write('## defect_in.yaml\n')
    markdown.write("|  defect  |  charge  |\n")
    markdown.write("| ---- | ---- |\n")
    for defect, charge in defect_in.items():
        markdown.write(f'|  {defect}  |  {charge}  |\n')
    markdown.write(f'<div style="page-break-before:always"></div>\n\n')

def write_defect_formation_info(markdown, label):
    markdown.write(f'## {label}\n')
    markdown.write(f'![Alt text](defect/energy_{label}.png)\n')
    markdown.write(f'<div style="page-break-before:always"></div>\n\n')

def write_dopant_defect_formation_info(markdown, label, dopant):
    markdown.write(f'## {label}\n')
    markdown.write(f'![Alt text](dopant_{dopant}/defect/energy_{label}.png)\n')
    markdown.write(f'<div style="page-break-before:always"></div>\n\n')

class Markdown():
    def __init__(self):
        piseset = PiseSet()

        #markdown_info.jsonを初期化
        markdown_info = defaultdict(dict)

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            markdown_info[f"{target_material.formula_pretty}_{target_material.material_id}"] = False
            if os.path.isdir(path):
                os.chdir(path)

                if not os.path.isfile("defect/supercell_info.json"):
                    print(f"No such directory: defect")
                    os.chdir("../../")
                    continue

                if not os.path.isfile("summary_info.json"):
                    print("No such file: summary_info.json")
                    os.chdir("../../")
                    continue
            
                with open('summary_info.json') as f:
                    summary_info = json.load(f)

                with open(f"{target_material.formula_pretty}_{target_material.material_id}_{summary_info['functional']}.md", mode='w') as markdown:
                    markdown.write(f"{target_material.formula_pretty}_{target_material.material_id}_{summary_info['functional']}\n")
                    
                    write_primitivecell_info(markdown, summary_info)
                    write_band_info(markdown, summary_info, piseset)
                    write_dielectric_info(markdown, summary_info)
                    write_effective_mass_info(markdown, summary_info)
                    write_dos_info(markdown)

                    if piseset.abs:
                        write_abs_info(markdown)

                    if piseset.surface:
                        write_band_alignment_info(markdown)
                        
                    write_supercell_info(markdown, summary_info)

                    
                    write_defect_info(markdown)

                    markdown.write(f"![Alt text](cpd/cpd.png)\n")
                    markdown.write(f'<div style="page-break-before:always"></div>\n\n')

                    for label in summary_info["labels"]:
                        write_defect_formation_info(markdown, label)

                    if os.path.isfile("pise_dopants_and_sites.yaml"):
                        dopants = get_dopants_list()
                        for dopant in dopants:
                            markdown.write(f"# dopant_{dopant}\n")
                            markdown.write(f"![Alt text](dopant_{dopant}/cpd/cpd.png)\n")
                            markdown.write(f'<div style="page-break-before:always"></div>\n\n')
                            try:
                                for label in summary_info[dopant]["labels"]:
                                    write_dopant_defect_formation_info(markdown, label, dopant)
                            except KeyError:
                                pass
                markdown_info[f"{target_material.formula_pretty}_{target_material.material_id}"] = True

                    

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")
            
            #markdown_info.jsonの保存
            with open("markdown_info.json", "w") as f:
                json.dump(markdown_info, f, indent=4)
            