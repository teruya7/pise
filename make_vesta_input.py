import os
import json

local_path = "/Users/nagafuji/mnt/laurel/explore_defect"

try:
    os.mkdir("vstx")
except FileExistsError:
    print("vstx directory exists")


with open("target_info.json") as f:
    target_list = json.load(f)

os.chdir("vstx")
for material in target_list:
    formula = material["pretty_formula"]
    mpcode = material["task_id"]
    target = f"{formula}_{mpcode}"
    print(f"Parsing {formula}_{mpcode}")

    content_primitive = '''
    -open {path}/{target_name}/{functional}/unitcell/opt/POSCAR
    -export_img {path}/{target_name}/{functional}/unitcell/opt/primitive.png
    -close
    '''.format(path = local_path, target_name = target, functional = "pbesol")
    with open(target + '_primitive.vstx', mode = 'w') as f:
        f.write(content_primitive)
    
    content_supercell = '''
    -open {path}/{target_name}/{functional}/defect/SPOSCAR
    -export_img {path}/{target_name}/{functional}/defect/supercell.png
    -close
    '''.format(path = local_path, target_name = target, functional = "pbesol")
    with open(target + '_supercell.vstx', mode = 'w') as f:
        f.write(content_supercell)

