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
            self.path_to_tsubo = pise_defaults["path_to_tsubo"]

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
            self.vise_task_command_surface = pise_defaults["vise_task_command_surface"]

            #vise_analysis_command
            self.vise_analysis_command_plot_band = pise_defaults["vise_analysis_command_plot_band"]
            self.vise_analysis_command_plot_dos = pise_defaults["vise_analysis_command_plot_dos"]
            self.vise_analysis_command_effective_mass = pise_defaults["vise_analysis_command_effective_mass"]
            self.vise_analysis_command_plot_abs = pise_defaults["vise_analysis_command_plot_abs"]
            self.vise_analysis_command_unitcell_nsc = pise_defaults["vise_analysis_command_unitcell_nsc"]
            self.vise_analysis_command_unitcell_hybrid = pise_defaults["vise_analysis_command_unitcell_hybrid"]

            self.local_path = pise_defaults["local_path"]

            #surface
            self.slab_thickness = pise_defaults["slab_thickness"]
            self.vaccum_thickness = pise_defaults["vaccum_thickness"]
            self.h = pise_defaults["h"]
            self.k = pise_defaults["k"]
            self.l = pise_defaults["l"]
            self.cap = pise_defaults["cap"]

            
        #pise.yamから設定を読み込む
        with open("pise.yaml") as file:
            pise = yaml.safe_load(file)
            self.functional = pise["functional"]
            
            if "path_to_poscar" in pise:
                self.path_to_poscar = pise["path_to_poscar"]
            else:
                self.path_to_poscar = None
            
            if "aexx" in pise:
                self.aexx = pise["aexx"]
            else:
                self.aexx = None

            if "surface" in pise:
                self.surface = pise["surface"]
            else:
                self.surface = False
            
            if "selftrap" in pise:
                self.selftrap = pise["selftrap"]
            else:
                self.selftrap = False

            if "abs" in pise:
                self.abs = pise["abs"]
            else:
                self.abs = False


            if self.functional == "pbesol":
                unitcell = ["opt", "band", "dos", "dielectric", "band_nsc", "dielectric_rpa"]
            else:
                unitcell = ["opt", "band", "dos", "dielectric"]
            if self.abs:
                unitcell.append("abs")
            
            self.unitcell = unitcell


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
                                'ENCUT': 400,
                                "LWAVE": True
                            },
                            'options': {
                                'set_hubbard_u': True
                            }
                            }
        if self.functional != "pbesol":
            vise_yaml["xc"] = self.functional
            vise_yaml["user_incar_settings"]["ALGO"] = "Normal"
            if pise["aexx"] is not None:
                vise_yaml["user_incar_settings"]["AEXX"] = pise["aexx"]
        self.vise_yaml = vise_yaml

        #vise_surface.yamlを作成
        vise_surface_yaml = {
                            'outcar': 'OUTCAR-finish',
                            'contcar': 'POSCAR-finish',
                            'overridden_potcar': 'Ga',
                            'xc': 'pbesol',
                            'user_incar_settings': {
                                'ENCUT': 400,
                                'LWAVE': True,
                                "EDIFF": 1e-07,
                                "EDIFFG": -0.005,
                                "ISPIN": 1,
                                "LVHAR": True,
                                "LREAL": False
                            },
                            'options': {
                                'set_hubbard_u': True
                            }
                            }
        if self.functional != "pbesol":
            vise_surface_yaml["xc"] = self.functional
            vise_surface_yaml["user_incar_settings"]["ALGO"] = "Normal"
            if pise["aexx"] is not None:
                vise_surface_yaml["user_incar_settings"]["AEXX"] = pise["aexx"]
        self.vise_surface_yaml = vise_surface_yaml


if __name__ == '__main__':
    print()