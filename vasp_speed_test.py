import os
import subprocess
import yaml
import json
from common_function import make_dir_list
from pise_set import PiseSet
from collections import defaultdict
from pymatgen.io.vasp.outputs import Outcar

def preparation_supercell(x, y, z, path_to_jobscript, submit_command):
    print(f"Preparing {x}{y}{z}.")
    os.makedirs(f"{x}{y}{z}", exist_ok=True)
    os.chdir(f"{x}{y}{z}")
    subprocess.run([f"pydefect s -p ../../../POSCAR --matrix {x} {y} {z}"], shell=True)
    subprocess.run(["pydefect ds -k Va_O"], shell=True)
    subprocess.run(["pydefect_vasp de"], shell=True)

    defect_dir_list = make_dir_list()
    for target_dir in defect_dir_list:
        os.chdir(target_dir)
        subprocess.run([f"cp {path_to_jobscript} ."], shell=True)
        subprocess.run(["vise vs -t defect -uis ALGO Normal SYMPREC 1e-4 NSW 1 --options only_even_num_kpts True"], shell=True)
        subprocess.run([f"{submit_command} *.sh"], shell=True)
        os.chdir("../")

    os.chdir("../")

def make_poscar_MgO():
    if not os.path.isfile("POSCAR"):
        with open("POSCAR", 'w') as f:
            f.write("Mg1 O1\n")
            f.write("   1.00000000000000 \n")
            f.write("     0.0000000000000000    2.1048115551790123    2.1048115551790123\n")
            f.write("     2.1048115551790123    0.0000000000000000    2.1048115551790123\n")
            f.write("     2.1048115551790123    2.1048115551790123    0.0000000000000000\n")
            f.write("   Mg   O\n")
            f.write("     1     1\n")
            f.write("Direct\n")
            f.write("  0.0000000000000000  0.0000000000000000  0.0000000000000000\n")
            f.write("  0.5000000000000000  0.5000000000000000  0.5000000000000000\n")

def make_vise_yaml(piseset):
    vise_yaml = piseset.vise_yaml
    vise_yaml["xc"] = piseset.functional
    if piseset.is_hybrid[piseset.functional] and not piseset.sc_dd_hybrid:
        vise_yaml["user_incar_settings"].setdefault("AEXX", piseset.aexx)
    with open("vise.yaml", "w") as f:
        yaml.dump(vise_yaml, f, sort_keys=False)


class VaspSpeedTest():
    def __init__(self):
        #POSCARの作成
        make_poscar_MgO()

    def pre(self, test_name, path_to_jobscript):
        
        piseset = PiseSet()

        if not os.path.isdir(f"{test_name}/{piseset.functional}"):
            print(f"Preparing {test_name}/{piseset.functional}.")
            os.makedirs(f"{test_name}/{piseset.functional}", exist_ok=True)
            os.chdir(f"{test_name}/{piseset.functional}")

            make_vise_yaml(piseset)

            preparation_supercell(2, 2, 2, path_to_jobscript, piseset.submit_command)
            preparation_supercell(3, 3, 3, path_to_jobscript, piseset.submit_command)

            os.chdir("../../")

    def time(self, test_name):
        piseset = PiseSet()

        if os.path.isdir(f"{test_name}/{piseset.functional}"):
            os.chdir(f"{test_name}/{piseset.functional}")

            time_info = defaultdict(lambda:defaultdict(dict))

            supercell_list = make_dir_list()
            for supercell in supercell_list:
                os.chdir(supercell)
                defect_list = make_dir_list()
                for defect in defect_list:
                    if os.path.isfile(f"{defect}/OUTCAR"):
                        outcar = Outcar(f"{defect}/OUTCAR")
                        try:
                            elapsed_time = outcar.run_stats['Elapsed time (sec)']
                            print(f"{supercell}/{defect}: {elapsed_time} s")
                            time_info[supercell][defect] = elapsed_time
                        except KeyError:
                            print(f"{supercell}/{defect}: null")
                            time_info[supercell][defect] = None
                os.chdir("../")

            #time_info.jsonの保存
            with open("time_info.json", "w") as f:
                json.dump(time_info, f, indent=4)
            
            os.chdir("../../")
        
        else:
            print(f"No such directory: {test_name}")
        


    



