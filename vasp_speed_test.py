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
        else:
            print(f"{test_name} already exists.")

    def time(self, test_name):
        piseset = PiseSet()
            
        if os.path.isdir(f"{test_name}/{piseset.functional}"):
            os.chdir(f"{test_name}/{piseset.functional}")

            elapsed_time_info = defaultdict(lambda:defaultdict(dict))
            one_electronic_step_time_info = defaultdict(lambda:defaultdict(dict))

            print("elapsed_time, one_electronic_step_time")
            supercell_list = make_dir_list()
            for supercell in supercell_list:
                os.chdir(supercell)
                defect_list = make_dir_list()
                defect_list_sorted = sorted(defect_list)
                for defect in defect_list_sorted:
                    os.chdir(defect)
                    if os.path.isfile("OUTCAR"):
                        outcar = Outcar("OUTCAR")
                        try:
                            elapsed_time = outcar.run_stats['Elapsed time (sec)']    
                            elapsed_time_info[supercell][defect] = elapsed_time

                            one_electronic_step_time = subprocess.run(["grep LOOP OUTCAR | awk '{print$7}' | awk 'NR==5'"], capture_output=True, text=True, shell=True).stdout
                            one_electronic_step_time = one_electronic_step_time.replace("\n", "")
                            one_electronic_step_time_info[supercell][defect] = one_electronic_step_time

                            print(f"{supercell}/{defect}, {elapsed_time}, {one_electronic_step_time}")
                        except KeyError:
                            elapsed_time_info[supercell][defect] = None
                            one_electronic_step_time_info[supercell][defect] = None
                            print(f"{supercell}/{defect}: null")
                    else:
                        print(f"No such file: {supercell}{defect}/OUTCAR")
                    os.chdir("../")    
                os.chdir("../")

            #elapsed_time_info.jsonの保存
            with open("elapsed_time_info.json", "w") as f:
                json.dump(elapsed_time_info, f, indent=4)

            #one_electronic_step_time_info.jsonの保存
            with open("one_electronic_step_time_info.json", "w") as f:
                json.dump(one_electronic_step_time_info, f, indent=4)
            
            os.chdir("../../")
        
        else:
            print(f"No such directory: {test_name}")
    

    # def pre(self, test_name, path_to_jobscript, num_core):
        
    #     piseset = PiseSet()

    #     if not os.path.isdir(f"{test_name}/{piseset.functional}"):
    #         print(f"Preparing {test_name}/{piseset.functional}.")
    #         os.makedirs(f"{test_name}/{piseset.functional}", exist_ok=True)
    #         os.chdir(f"{test_name}/{piseset.functional}")

    #         num_core_info = {"num_core": num_core}
    #         with open("num_core_info.json", "w") as f:
    #             json.dump(num_core_info, f, indent=4)
            
    #         make_vise_yaml(piseset)

    #         preparation_supercell(2, 2, 2, path_to_jobscript, piseset.submit_command)
    #         preparation_supercell(3, 3, 3, path_to_jobscript, piseset.submit_command)

    #         os.chdir("../../")
    #     else:
    #         print(f"{test_name} already exists.")

    # def time(self, test_name, path_to_base_time_info=None):
    #     piseset = PiseSet()

    #     if path_to_base_time_info is not None:
    #         with open(path_to_base_time_info) as f:
    #             base_time_info = json.load(f)
    #         base_num_core = base_time_info["num_core"]
            
    #     if os.path.isdir(f"{test_name}/{piseset.functional}"):
    #         os.chdir(f"{test_name}/{piseset.functional}")

    #         time_info = defaultdict(lambda:defaultdict(dict))

    #         with open('num_core_info.json') as f:
    #             num_core_info = json.load(f)
    #         num_core = num_core_info["num_core"]
    #         time_info["num_core"] = num_core

    #         if path_to_base_time_info is not None:
    #             print(f"core_ratio: {num_core / base_num_core}")

    #         supercell_list = make_dir_list()
    #         for supercell in supercell_list:
    #             os.chdir(supercell)
    #             defect_list = make_dir_list()
    #             for defect in defect_list:
    #                 if os.path.isfile(f"{defect}/OUTCAR"):
    #                     outcar = Outcar(f"{defect}/OUTCAR")
    #                     try:
    #                         elapsed_time = outcar.run_stats['Elapsed time (sec)']
    #                         if path_to_base_time_info is not None:
    #                             time_ratio = '{:.2g}'.format(base_time_info[supercell][defect] / elapsed_time)
    #                             print(f"{supercell}/{defect}: {elapsed_time} s, {time_ratio}")
    #                         else:
    #                             print(f"{supercell}/{defect}: {elapsed_time} s")
    #                         time_info[supercell][defect] = elapsed_time
    #                     except KeyError:
    #                         print(f"{supercell}/{defect}: null")
    #                         time_info[supercell][defect] = None
    #                 else:
    #                     print(f"No such file: {defect}/OUTCAR")
    #             os.chdir("../")

    #         #time_info.jsonの保存
    #         with open("time_info.json", "w") as f:
    #             json.dump(time_info, f, indent=4)
            
    #         os.chdir("../../")
        
    #     else:
    #         print(f"No such directory: {test_name}")
        


    



