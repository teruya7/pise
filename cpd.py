import os
import json
import subprocess
import pathlib
from collections import defaultdict
from pise_set import PiseSet
from calculation import is_calc_converged
from common_function import make_dir_list
from submission import submit_job
from error_handler import get_running_jobs_list, delete_unnecessary_files, check_and_correct_errors, get_repeat_directory_name

def error_handling(calc_info, cwd, running_jobs_list):
    for directory_name, is_finished in calc_info.items():
        if not is_finished and f"{cwd}/{directory_name}" not in running_jobs_list:
            os.chdir(directory_name)
            print()
            print(f"{cwd}/{directory_name}")

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
            elif get_repeat_directory_name() is None and os.path.isfile("ready_for_submission.txt"):
                print("This job has not been submitted yet.")
                touch = pathlib.Path("ready_for_submission.txt")
                touch.touch()
                subprocess.run(["rm ready_for_submission.txt"], shell=True)
            else:
                print("Unknown error!!")

            os.chdir("../")


#カレントディレクトリにpise.yamlがあるならどこでも使えるクラス
class Cpd():
    def __init__(self):
        self.piseset = PiseSet()

        self.path = self.piseset.path_to_cpd_database + "/" + self.piseset.functional
        cwd = os.getcwd()

        if os.path.isdir(f"{self.path}"):
            os.chdir(f"{self.path}")
            
            self.datalist = make_dir_list()

            #元々いたパスに戻る
            os.chdir(cwd)

    def cal(self):
        if os.path.isdir(f"{self.path}"):
            os.chdir(f"{self.path}")
            
            calc_info = defaultdict(dict)
            
            for data in self.datalist:
                if is_calc_converged(data):
                    calc_info[data] = True
                else:
                    calc_info[data] = False
                    print(f"{self.path}/{data}")

            #calc_info.jsonの保存
            with open("calc_info.json", "w") as f:
                json.dump(calc_info, f, indent=4)
        else:
            print(f"No such directory: {self.path}")

    def submit(self):
        if os.path.isdir(self.path):
            os.chdir(self.path)

            with open('calc_info.json') as f:
                calc_info = json.load(f)
            
            for target, is_converged in calc_info.items():
                if not is_converged:
                    submit_job(self.piseset, target)
        else:
            print(f"No such directory: {self.path}")

    def eh(self):
        if os.path.isdir(self.path):
            os.chdir(self.path)

            cwd = os.getcwd()
            with open('calc_info.json') as f:
                calc_info = json.load(f)
            error_handling(calc_info, cwd, get_running_jobs_list(self.piseset))
        else:
            print(f"No such directory: {self.path}")
    