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
            self.path_to_tsubo = pise_defaults["path_to_tsubo"]

            self.job_table = pise_defaults["job_table"]

            #vise.yamlの設定
            self.vise_yaml = pise_defaults["vise_yaml"]
            self.vise_surface_yaml = pise_defaults["vise_surface_yaml"]

            #汎関数がhybrid汎関数か否かの判定
            self.is_hybrid = pise_defaults["is_hybrid"]

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
            self.nsc = pise["nsc"]
            self.aexx = pise["aexx"]
            self.abs = pise["abs"]
            self.surface = pise["surface"]
            self.path_to_poscar = pise["path_to_poscar"]

        #target_info.jsonを読み込み
        with open("target_info.json") as f:
            target_info = json.load(f)
            self.target_info = target_info
        
if __name__ == '__main__':
    pass