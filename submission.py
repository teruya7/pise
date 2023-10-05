import os
import subprocess
from calculation import make_dir_list
from pise_set import PiseSet
from target import TargetHandler
import yaml
from doping import get_dopants_list

def submit_jobs(piseset, target_dir):
    if os.path.isdir(target_dir):
        os.chdir(target_dir)
        sub_dir_list = make_dir_list()
        for sub_dir in sub_dir_list:
            print(sub_dir)

            #ジョブ数の制限を超えていないか確認
            if piseset.num_jobs_command is not None:
                num_jobs = subprocess.run([f"{piseset.num_jobs_command}"], capture_output=True, text=True, shell=True).stdout
                print(num_jobs)
                if int(num_jobs) >= int(piseset.limit_jobs):
                    print("The maximum number of calculations has been reached.")
                    break

            os.chdir(sub_dir)
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
        os.chdir("../")
    
class Submission():
    def __init__(self):
        #pise.yamlとtarget_info.jsonの読み込み
        self.piseset = PiseSet()

    #全てのtargetを対象にジョブを投げる
    def all(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                submit_jobs(self.piseset, "unitcell")
                submit_jobs(self.piseset, "cpd")
                submit_jobs(self.piseset, "defect")

                #表面の計算
                if self.piseset.surface and os.path.isdir("surface"):
                    os.chdir("surface")
                    surface_list = make_dir_list()
                    for surface in surface_list:
                        submit_jobs(self.piseset, surface)
                    os.chdir("../")

                #ドーパントの計算
                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            submit_jobs(self.piseset, "cpd")
                            submit_jobs(self.piseset, "defect")
                            os.chdir("../")

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()
   
    #全てのtargetのunitcellを対象にジョブを投げる
    def unitcell(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)
                submit_jobs(self.piseset, "unitcell")
                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()

    #全てのtargetのcpdを対象にジョブを投げる
    def cpd(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                submit_jobs(self.piseset, "cpd")

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    with open("pise_dopants_and_sites.yaml") as file:
                        pise_dopants_and_sites = yaml.safe_load(file)
                    for dopant_and_site in pise_dopants_and_sites["dopants_and_sites"]:
                        dopant = dopant_and_site[0]
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            submit_jobs(self.piseset, "cpd")
                            os.chdir("../")

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()

    #全てのtargetのdefectを対象にジョブを投げる
    def defect(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                submit_jobs(self.piseset, "defect")

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    dopants = get_dopants_list()
                    for dopant in dopants:
                        if os.path.isdir(f"dopant_{dopant}"):
                            os.chdir(f"dopant_{dopant}")
                            submit_jobs(self.piseset, "defect")
                            os.chdir("../")

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()

    #全てのtargetのsurfaceを対象にジョブを投げる
    def surface(self):
        for target in self.piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(self.piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                if self.piseset.surface:
                    os.chdir("surface")
                    surface_list = make_dir_list()
                    for surface in surface_list:
                        submit_jobs(self.piseset, surface)
                    os.chdir("../")

                os.chdir("../../")
                print()
            else:
                print(f"No such directory: {path}")
                print()
