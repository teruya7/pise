import json
import yaml
import os

class PiseSet():
    def __init__(self):
        
        #pise_defaults.yamからスパコンの情報とviseのコマンド設定を読み込む
        home = os.environ['HOME']
        with open(f"{home}/.pise_defaults.yaml") as file:
            #スパコンの環境変数
            pise_defaults = yaml.safe_load(file)
            self.limit_jobs = pise_defaults["limit_jobs"]
            self.submit_command = pise_defaults["submit_command"]
            self.num_jobs_command = pise_defaults["num_jobs_command"]
            self.job_script_path = pise_defaults["job_script_path"]
            self.submission_ready = pise_defaults["submission_ready"]

            #job_scriptの設定
            self.job_script_small = pise_defaults["job_script_small"]
            self.small_task = pise_defaults["small_task"]
            self.job_script_large = pise_defaults["job_script_large"]
            self.large_task = pise_defaults["large_task"]

            #vise_task_command
            self.vise_task_command_opt = pise_defaults["vise_task_command_opt"]
            self.vise_task_command_band = pise_defaults["vise_task_command_band"]
            self.vise_task_command_band_nsc = pise_defaults["vise_task_command_band_nsc"]
            self.vise_task_command_dos = pise_defaults["vise_task_command_dos"]
            self.vise_task_command_dielectric = pise_defaults["vise_task_command_dielectric"]
            self.vise_task_command_dielectric_rpa = pise_defaults["vise_task_command_dielectric_rpa"]
            self.vise_task_command_dielectric_hybrid = pise_defaults["vise_task_command_dielectric_hybrid"]
            self.vise_task_command_abs = pise_defaults["vise_task_command_abs"]
            self.vise_task_command_defect = pise_defaults["vise_task_command_defect"]

            self.local_path = pise_defaults["local_path"]

            
        #pise.yamから設定を読み込む
        with open("pise.yaml") as file:
            pise = yaml.safe_load(file)
            self.dopants = pise["dopants"]
            self.substitution_site = pise["substitution_site"]
            self.functional = pise["functional"]
            self.path_tp_poscar = pise["path_to_poscar"]
            if self.functional == "pbesol":
                self.unitcell = ["opt", "band", "dos", "dielectric", "band_nsc", "dielectric_rpa", "abs"]
            else:
                self.unitcell = ["opt", "band", "dos", "dielectric", "abs"]


        #target_info.jsonを読み込み
        with open("target_info.json") as f:
            target_info = json.load(f)
            self.target_info = target_info
        
        #vise.yamlを作成
        vise_yaml = {
                            'outcar': 'OUTCAR-finish',
                            'contcar': 'POSCAR-finish',
                            'overridden_potcar': 'Ga',
                            'xc': 'pbesol',
                            'user_incar_settings': {
                                'ENCUT': 400
                            },
                            'options': {
                                'set_hubbard_u': True
                            }
                            }
        if self.functional == "hse":
            vise_yaml["xc"] = "hse"
            vise_yaml["user_incar_settings"]["ALGO"] = "Normal"
        elif self.functional == "pbe0":
            vise_yaml["xc"] = "pbe0"
            vise_yaml["user_incar_settings"]["ALGO"] = "Normal"
        self.vise_yaml = vise_yaml


if __name__ == '__main__':
    print()