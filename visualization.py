from pise_set import PiseSet
from target import TargetHandler
import os
import json

def get_cwd_name(cwd):
    return os.path.basename(cwd)

class Visualization():
    def __init__(self):
        piseset = PiseSet()

        try:
            os.mkdir("vstx")
        except FileExistsError:
            print("vstx directory exists")

        cwd_name = get_cwd_name(os.getcwd())
        os.chdir("vstx")
        for target in piseset.target_info:
            target_material = TargetHandler(target)
            dir_name = f"{target_material.formula_pretty}_{target_material.material_id}"
            host_path = target_material.make_path(piseset.functional)

            vstx_primitivecell = '''
            -open {local_path}/{cwd_name}/{host_path}/unitcell/opt/POSCAR-finish
            -export_img {local_path}/{cwd_name}/{host_path}/unitcell/opt/primitivecell.png
            -close
            '''.format(local_path = piseset.local_path, cwd_name = cwd_name, host_path = host_path)
            with open(f"{dir_name}_primitivecell.vstx", mode = 'w') as f:
                f.write(vstx_primitivecell)
            
            vstx_supercell = '''
            -open {local_path}/{cwd_name}/{host_path}/defect/SPOSCAR
            -export_img {local_path}/{cwd_name}/{host_path}/defect/supercell.png
            -close
            '''.format(local_path = piseset.local_path, cwd_name = cwd_name, host_path = host_path)
            with open(f"{dir_name}_supercell.vstx", mode = 'w') as f:
                f.write(vstx_supercell)

        os.chdir("../")




            