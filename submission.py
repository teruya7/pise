import os
import subprocess
from common_function import make_dir_list
from pise_set import PiseSet
from target import TargetHandler
import json
from doping import get_dopants_list
from calculation import Calculation

def submit_job(piseset, target):
    #ジョブ数の制限を超えていないか確認
    if piseset.num_jobs_command is not None:
        num_jobs = subprocess.run([f"{piseset.num_jobs_command}"], capture_output=True, text=True, shell=True).stdout
        try:
            if int(num_jobs) >= int(piseset.limit_jobs):
                print("The maximum number of calculations has been reached.")
                return False
        except ValueError:
            pass

    if os.path.isdir(target):
        os.chdir(target)
        print(f"{target}:{num_jobs}")
            
        if os.path.isfile("ready_for_submission.txt"):
            subprocess.run([f"{piseset.submit_command} run*.sh"], shell=True)
            subprocess.run(["rm ready_for_submission.txt"], shell=True)
        
        #計算が収束していなかった時
        elif os.path.isfile("POSCAR-10"):
            print("Calculations have not converged. So the job submitted again.")
            subprocess.run(["cp POSCAR-10 POSCAR"], shell=True)
            subprocess.run(["rm -r OUTCAR-* progress-* POSCAR-* repeat-*"], shell=True)
            subprocess.run([f"{piseset.submit_command} run*.sh"], shell=True)
        else:
            print("No ready_for_submission.txt")
        os.chdir("../")
    return True

def submit_jobs(path, piseset, calc_info_items):
    if not os.path.isdir(path):
        return
    
    os.chdir(path)
    for target, is_converged in calc_info_items:
        if not is_converged:
            if not submit_job(piseset, target):
                break
    os.chdir("../")

class Submission():
    def __init__(self):
        #pise.yamlとtarget_info.jsonの読み込み
        self.piseset = PiseSet()
        Calculation()

    #全てのtargetを対象にジョブを投げる
    def all(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                with open('calc_info.json') as f:
                    calc_info = json.load(f)
                try:
                    submit_jobs("unitcell", self.piseset, calc_info["unitcell"].items())
                except KeyError:
                    pass
                try:
                    submit_jobs("cpd", self.piseset, calc_info["cpd"].items())
                except KeyError:
                    pass
                try:
                    submit_jobs("defect", self.piseset, calc_info["defect"].items())
                except KeyError:
                    pass

                #表面の計算
                if self.piseset.surface and os.path.isdir("surface"):
                    os.chdir("surface")
                    surface_list = make_dir_list()
                    for surface in surface_list:
                        try:
                            submit_jobs(surface, self.piseset, calc_info["surface"][surface][target].items())
                        except KeyError:
                            pass
                    os.chdir("../")

                #ドーパントの計算
                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            try:
                                submit_jobs("cpd", self.piseset, calc_info[f"dopant_{dopant}"]["cpd"].items())
                            except KeyError:
                                pass
                            try:
                                submit_jobs("defect", self.piseset, calc_info[f"dopant_{dopant}"]["defect"].items())
                            except KeyError:
                                pass
                            os.chdir("../")

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")
   
    #全てのtargetのunitcellを対象にジョブを投げる
    def unitcell(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                with open('calc_info.json') as f:
                    calc_info = json.load(f)
                try:
                    submit_jobs("unitcell", self.piseset, calc_info["unitcell"].items())
                except KeyError:
                    pass

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")

    #全てのtargetのcpdを対象にジョブを投げる
    def cpd(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                with open('calc_info.json') as f:
                    calc_info = json.load(f)
                
                try:
                    submit_jobs("cpd", self.piseset, calc_info["cpd"].items())
                except KeyError:
                    pass

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            try:
                                submit_jobs("cpd", self.piseset, calc_info[f"dopant_{dopant}"]["cpd"].items())
                            except KeyError:
                                pass
                            os.chdir("../")

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")

    #全てのtargetのsurfaceを対象にジョブを投げる
    def surface(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                with open('calc_info.json') as f:
                    calc_info = json.load(f)

                if self.piseset.surface and os.path.isdir("surface"):
                    os.chdir("surface")
                    surface_list = make_dir_list()
                    for surface in surface_list:
                        try:
                            submit_jobs(surface, self.piseset, calc_info["surface"][surface][target].items())
                        except KeyError:
                            pass
                    os.chdir("../")

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")

    #全てのtargetのdefectを対象にジョブを投げる
    def defect(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                with open('calc_info.json') as f:
                    calc_info = json.load(f)
                
                try:
                    submit_jobs("defect", self.piseset, calc_info["defect"].items())
                except KeyError:
                    pass


                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            submit_jobs("defect", self.piseset, calc_info[f"dopant_{dopant}"]["defect"].items())
                            os.chdir("../")

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")