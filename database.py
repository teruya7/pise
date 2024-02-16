import os
import json
from collections import defaultdict
from pise_set import PiseSet
from calculation import is_calc_converged
from common_function import make_dir_list
from submission import submit_job

#カレントディレクトリにpise.yamlがあるならどこでも使えるクラス
class Database():
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
    