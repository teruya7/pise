import os
import glob
import json
import shutil
import subprocess
import pathlib
from pise_set import PiseSet
from target import TargetHandler
from doping import get_dopants_list
from custodian.vasp.handlers import VaspErrorHandler, UnconvergedErrorHandler, AliasingErrorHandler, MeshSymmetryErrorHandler, NonConvergingErrorHandler, PositiveEnergyErrorHandler, PotimErrorHandler, StdErrHandler, WalltimeHandler


#出力ファイルの名前の特定
def get_repeat_directory_name():
    if os.path.isdir("repeat-1"):
        repeat_directory_name = "repeat-1"
    elif os.path.isdir("repeat-2"):
        repeat_directory_name = "repeat-2"
    elif os.path.isdir("repeat-3"):
        repeat_directory_name = "repeat-3"
    elif os.path.isdir("repeat-4"):
        repeat_directory_name = "repeat-4"
    elif os.path.isdir("repeat-5"):
        repeat_directory_name = "repeat-5"
    elif os.path.isdir("repeat-6"):
        repeat_directory_name = "repeat-6"
    elif os.path.isdir("repeat-7"):
        repeat_directory_name = "repeat-7"
    elif os.path.isdir("repeat-8"):
        repeat_directory_name = "repeat-8"
    elif os.path.isdir("repeat-9"):
        repeat_directory_name = "repeat-9"
    elif os.path.isdir("repeat-10"):
        repeat_directory_name = "repeat-10"
    else:
        return None

    return repeat_directory_name

def get_vaspout_name():
    if os.path.isfile("progress-finish"):
        vaspout_name = "progress-finish"
    elif os.path.isfile("progress-10"):
        vaspout_name = "progress-10"
    elif os.path.isfile("progress-9"):
        vaspout_name = "progress-9"
    elif os.path.isfile("progress-8"):
        vaspout_name = "progress-8"
    elif os.path.isfile("progress-7"):
        vaspout_name = "progress-7"
    elif os.path.isfile("progress-6"):
        vaspout_name = "progress-6"
    elif os.path.isfile("progress-5"):
        vaspout_name = "progress-5"
    elif os.path.isfile("progress-4"):
        vaspout_name = "progress-4"
    elif os.path.isfile("progress-3"):
        vaspout_name = "progress-3"
    elif os.path.isfile("progress-2"):
        vaspout_name = "progress-2"
    elif os.path.isfile("progress-1"):
        vaspout_name = "progress-1"
    else:
        return None

    return vaspout_name

def get_running_jobs_list(piseset):
    subprocess.run([f" {piseset.running_jobs_command} | grep {os.getcwd()} > running_jobs.txt"], shell=True)
    with open("running_jobs.txt") as f:
        running_jobs_list = f.read().splitlines()
    subprocess.run(["rm running_jobs.txt"], shell=True)
    return running_jobs_list

def delete_unnecessary_files():
    for outcar in glob.glob('OUTCAR-*'):
        if os.path.isfile(outcar):
            os.remove(outcar)
    
    for progress in glob.glob('progress-*'):
        if os.path.isfile(progress):
            os.remove(progress)
    
    for poscar in glob.glob('POSCAR-*'):
        if os.path.isfile(poscar):
            os.remove(poscar)
    
    for std_out in glob.glob('*.out'):
        if os.path.isfile(std_out):
            os.remove(std_out)
    
    if os.path.isfile("WAVECAR"):
        os.remove("WAVECAR")
    
    if os.path.isfile("vasprun.xml"):
        os.remove("vasprun.xml")
    
    if os.path.isfile("std_err.txt"):
        os.remove("std_err.txt")
    
    if os.path.isdir("gga"):
        shutil.rmtree("gga")
    
    if os.path.isdir(get_repeat_directory_name()):
        shutil.rmtree(get_repeat_directory_name())

def check_and_correct_errors():
    vaspout = get_vaspout_name()
    repeat_directory_name = get_repeat_directory_name()

    if vaspout is None or repeat_directory_name is None:
        return False

    aliasingerrorhandler = AliasingErrorHandler(output_filename=vaspout)
    if aliasingerrorhandler.check():
        aliasingerrorhandler.correct()
        print("AliasingErrorHandler is used to correct an error.")
        return True

    vasperrorhandler = VaspErrorHandler(output_filename=vaspout)
    if vasperrorhandler.check():
        vasperrorhandler.correct()
        print("VaspErrorHandler is used to correct an error.")
        return True

    if os.path.isfile("vasprun.xml"):
        unconvergederrorhandler = UnconvergedErrorHandler(output_filename="vasprun.xml")
        if unconvergederrorhandler.check():
            unconvergederrorhandler.correct()
            print("UnconvergedErrorHandler is used to correct an error.")
            return True
    
    if os.path.isfile("vasprun.xml"):
        meshsymmetryerrorhandler = MeshSymmetryErrorHandler(output_filename=vaspout,output_vasprun="vasprun.xml")
        if meshsymmetryerrorhandler.check():
            meshsymmetryerrorhandler.correct()
            print("MeshSymmetryErrorHandler is used to correct an error.")
            return True

    nonconvergingerrorhandler = NonConvergingErrorHandler(output_filename=f"{repeat_directory_name}/OSZICAR",nionic_steps=5)
    if nonconvergingerrorhandler.check():
        nonconvergingerrorhandler.correct()
        print("NonConvergingErrorHandler is used to correct an error.")
        return True
    
    positiveenergyerrorhandler = PositiveEnergyErrorHandler(output_filename=f"{repeat_directory_name}/OSZICAR")
    if positiveenergyerrorhandler.check():
        positiveenergyerrorhandler.correct()
        print("PositiveEnergyErrorHandler is used to correct an error.")
        return True
    
    potimerrorhandler = PotimErrorHandler(input_filename="POSCAR",output_filename=f"{repeat_directory_name}/OSZICAR")
    if potimerrorhandler.check():
        potimerrorhandler.correct()
        print("PotimErrorHandler is used to correct an error.")
        return True

    #標準出力をstd_err.txtにする必要がある
    if os.path.isfile("std_err.txt"):
        stderrhandler = StdErrHandler(output_filename="std_err.txt")
        if stderrhandler.check():
            stderrhandler.correct()
            print("StdErrHandler is used to correct an error.")
            return True
    
def error_handling(target_dir, calc_info, cwd, running_jobs_list):
    try:
        for directory_name, is_finished in calc_info[target_dir].items():
            if not is_finished and f"{cwd}/{target_dir}/{directory_name}" not in running_jobs_list:
                os.chdir(f"{target_dir}/{directory_name}")
                print()
                print(f"{cwd}/{target_dir}/{directory_name}")

                if os.path.isfile("ready_for_submission.txt"):
                    print("This job has not been submitted yet.")
                elif os.path.isfile("POSCAR-10"):
                    print("Calculations have not converged.")
                    subprocess.run(["cp POSCAR-10 POSCAR"], shell=True)
                    delete_unnecessary_files()
                    touch = pathlib.Path("ready_for_submission.txt")
                    touch.touch()
                elif check_and_correct_errors():
                    delete_unnecessary_files()
                    touch = pathlib.Path("ready_for_submission.txt")
                    touch.touch()
                else:
                    print("Unknown error!!")

                os.chdir("../../")
    except KeyError:
        pass

class ErrorHandler():
    def __init__(self):
        piseset = PiseSet()
        running_jobs_list = get_running_jobs_list(piseset)

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                cwd_native = os.getcwd()  
                with open('calc_info.json') as f:
                    calc_info = json.load(f)
                
                error_handling("unitcell", calc_info, cwd_native, running_jobs_list)
                if piseset.is_hybrid[piseset.functional]:
                    error_handling("cpd", calc_info, cwd_native, running_jobs_list)
                error_handling("defect", calc_info, cwd_native, running_jobs_list)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            cwd_dopnat = os.getcwd()  
                            error_handling("cpd", calc_info, cwd_dopnat, running_jobs_list)
                            error_handling("defect", calc_info, cwd_dopnat, running_jobs_list)
                            os.chdir("../")
                
                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
