import os
import subprocess
from pise_set import PiseSet
from collections import defaultdict
import json
from target_info import TargetHandler
from calc_info import CalcInfoMaker
from pdf2image import convert_from_path
from pathlib import Path


def initialize_analysis_info(analysis_target_list):
    if os.path.isfile("analysis_info.json"):
        print("Loading analysis_info.json")
        print()
        with open('analysis_info.json') as f:
            analysis_info = json.load(f)
        for i in analysis_target_list:
            analysis_info.setdefault(i, False)
    else:
        analysis_info = defaultdict(dict)
        print("Making analysis_info.json")
        print()
        for i in analysis_target_list:
            analysis_info[i] = False
    return analysis_info

def check_calc_alldone(list):
    for i in list:
        if i:
            flag = True
        else:
            flag = False
            break
    return flag

def check_analysis_done(target_file):
    if os.path.isfile(target_file):
        return True
    else:
        return False

def get_label_from_chempotdiag(path_chem_pot_diag):
    labels = []
    with open(path_chem_pot_diag) as f:
        chem_pot = json.load(f)
    for label in chem_pot["target_vertices_dict"]:
        labels.append(label)
    return labels

def pdf_to_png(pdf_file, img_path, fmt='png', dpi=200):

    #pdf_file、img_pathをPathにする
    pdf_path = Path(pdf_file)
    image_dir = Path(img_path)

    # PDFをImage に変換(pdf2imageの関数)
    pages = convert_from_path(pdf_path, dpi)

    #名前を整える
    for i, page in enumerate(pages):
        file_name = "{}_{:02d}.{}".format(pdf_path.stem,i+1,fmt)
        image_path = image_dir / file_name
        page.save(image_path, fmt)
        before_name = image_path
        after_name = pdf_path.stem + "." + fmt
        os.rename(before_name, after_name)

def plot_pdf(file_name, vise_analysis_command):
    if not os.path.isfile(file_name):
        subprocess.run([vise_analysis_command], shell=True)
    else:
        print(f"{file_name} has already existed.")

def analysis_unitcell(piseset, calc_info, analysis_info):
    #unitcellが解析済みかどうか確認
    if not analysis_info["unitcell"]:     
        #バンド端補正を行なったか判断
        if piseset.functional == "pbesol":
            band = "band_nsc"
        else:
            band = "band" 
        #unitcellの計算が完了しているか確認
        if calc_info["unitcell"][band] and calc_info["unitcell"]["dielectric"] and calc_info["unitcell"]["abs"]:
            os.chdir("unitcell") 
            subprocess.run([f"pydefect_vasp u -vb {band}/vasprun.xml -ob {band}/OUTCAR-finish -odc dielectric/OUTCAR-finish -odi dielectric/OUTCAR-finish"], shell=True)
            flag = check_analysis_done("unitcell.yaml")

            os.chdir(band)
            plot_pdf("band.pdf", "vise pb")
            pdf_to_png("band.pdf", "./")
            os.chdir("../")

            os.chdir("dos")
            if not os.path.isfile("effective_mass.json"):
                subprocess.run(["vise em -t 300 -c 16"], shell=True)
            plot_pdf("dos.pdf", "vise pd")
            pdf_to_png("dos.pdf", "./")
            os.chdir("../")

            os.chdir("abs")
            plot_pdf("absorption_coeff.pdf", "vise pdf -ckk")
            pdf_to_png("absorption_coeff.pdf", "./")
            os.chdir("../")

            os.chdir("../")
        elif not calc_info["unitcell"][band]:
            print(f"{band} calculations have not finished yet.")
            flag = False
        elif not calc_info["unitcell"]["dos"]:
            print("dos calculations have not finished yet.")
            flag = False
        elif not calc_info["unitcell"]["abs"]:
            print("abs calculations have not finished yet.")
            flag = False
    else:
        print("Analysis of unitcell has already finished.")
        flag = True

    return flag

def analysis_cpd(target_material, calc_info, analysis_info):
    #cpdが解析済みかどうか確認
    if not analysis_info["cpd"]:
        #cpdの計算が完了しているか確認
        if check_calc_alldone(calc_info["cpd"].values()):
            os.chdir("cpd") 
            if not os.path.isdir("host"):
                subprocess.run(["ln -s ../unitcell/opt host"], shell=True)
            subprocess.run(["pydefect_vasp mce -d */"], shell=True)
            subprocess.run(["pydefect sre"], shell=True)
            subprocess.run([f"pydefect cv -t {target_material.formula_pretty}"], shell=True)
            flag = check_analysis_done("target_vertices.yaml")
            subprocess.run(["pydefect pc"], shell=True)
            if os.path.isfile("cpd.pdf"):
                pdf_to_png("cpd.pdf", "./")
            os.chdir("../") 
        else:
            print("cpd calculations have not finished yet.")
            flag = False
    else:
        print("Analysis of cpd has already finished.")
        flag = True

    return flag

def analysis_defect(calc_info, analysis_info):
    #defectが解析済みかどうかと解析可能な状況なのか確認
    if not analysis_info["defect"] and analysis_info["unitcell"] and analysis_info["cpd"]:
        #defectの計算が完了しているか確認
        if check_calc_alldone(calc_info["defect"].values()):
            os.chdir("defect") 
            subprocess.run(["pydefect_vasp cr -d *_*/ perfect"], shell=True)
            subprocess.run(["pydefect efnv -d *_*/ -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml"], shell=True)
            subprocess.run(["pydefect dsi -d *_*/"], shell=True)
            subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
            subprocess.run(["pydefect dsi -d *_*/"], shell=True)
            subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
            subprocess.run(["pydefect_vasp pbes -d perfect"], shell=True)
            subprocess.run(["pydefect_vasp beoi -d *_* -pbes perfect/perfect_band_edge_state.json"], shell=True)
            subprocess.run(["pydefect bes -d *_*/ -pbes perfect/perfect_band_edge_state.json"], shell=True)
            subprocess.run(["pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
            subprocess.run(["pydefect des -d *_*/ -u ../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
            subprocess.run(["pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)

            labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
            for label in labels:
                subprocess.run([f"pydefect pe -d defect_energy_summary.json -l {label}"], shell=True)
                pdf_to_png(f"energy_{label}.pdf", "./")
            flag = check_analysis_done("energy_A.pdf")

            os.chdir("../") 
        else:
            print("defect calculations have not finished yet.")
            flag = False

    elif analysis_info["defect"]:
        print("Analysis of defect has already finished.")
        flag = True
    elif analysis_info["unitcell"] and not analysis_info["cpd"]:
        print("Analysis of unitcell has not finished yet.")
        flag = False
    elif not analysis_info["unitcell"] and analysis_info["cpd"]:
        print("Analysis of cpd has not finished yet.")
        flag = False
    elif not analysis_info["unitcell"] and not analysis_info["cpd"]:
        print("Analysis of unitcell and cpd have not finished yet.")
        flag = False

    return flag

def analysis_dopant_cpd(dopant, target_material, calc_info, analysis_info):
    #dopantのcpdが解析済みかどうか確認
    if not analysis_info[f"{dopant}_cpd"] and analysis_info["cpd"]:
        #dopantのcpdフォルダがあるか確認
        if os.path.isdir(f"dopant_{dopant}/cpd"):
            #dopantのcpdの計算が完了しているか確認
            if check_calc_alldone(calc_info[f"dopant_{dopant}"]["cpd"].values()):
                os.chdir(f"dopant_{dopant}/cpd")
                #host情報をシンボリックリンクで持ってくる 
                if not os.path.isdir("host"):
                    subprocess.run(["ln -s ../../unitcell/opt host"], shell=True)

                #無添加相のcpdの情報をシンボリックリンクで持ってくる
                for cpd_dir_name in calc_info["cpd"].keys():
                    if not os.path.isdir(cpd_dir_name):
                        subprocess.run([f"ln -s ../../cpd/{cpd_dir_name} ./"], shell=True)
                
                subprocess.run(["pydefect_vasp mce -d */"], shell=True)
                subprocess.run(["pydefect sre"], shell=True)
                subprocess.run([f"pydefect cv -t {target_material.formula_pretty}"], shell=True)
                flag = check_analysis_done("target_vertices.yaml")
                subprocess.run(["pydefect pc"], shell=True)
                if os.path.isfile("cpd.pdf"):
                    pdf_to_png("cpd.pdf", "./")
                os.chdir("../../") 
            else:
                print(f"dopant_{dopant}'s cpd calculations have not finished yet.")
                flag = False
        else:
            print(f"No such directory: cpd in dopant_{dopant}")
            flag = False
    elif analysis_info[f"{dopant}_cpd"]:
        print(f"Analysis of dopant_{dopant}'s cpd has already finished.")
        flag = True
    elif not analysis_info["cpd"]:
        print(f"Analysis of cpd has not yet finished.")
        flag = False

    return flag

def analysis_dopant_defect(dopant, calc_info, analysis_info):
    #dopantのdefectが解析済みかどうか確認
    if not analysis_info[f"{dopant}_defect"] and analysis_info["defect"] and analysis_info[f"{dopant}_cpd"]:
        #dopnatのdefectフォルダがあるか確認
        if os.path.isdir(f"dopant_{dopant}/defect"):
            #dopantのdefectの計算が完了しているか確認
            if check_calc_alldone(calc_info[f"dopant_{dopant}"]["defect"].values()):
                os.chdir(f"dopant_{dopant}/defect") 
                if not os.path.isdir("perfect"):
                        subprocess.run([f"ln -s ../../defect/perfect ./"], shell=True)

                subprocess.run(["pydefect_vasp cr -d *_*/ perfect"], shell=True)
                subprocess.run(["pydefect efnv -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml"], shell=True)
                subprocess.run(["pydefect dsi -d *_*/"], shell=True)
                subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
                subprocess.run(["pydefect dsi -d *_*/"], shell=True)
                subprocess.run(["pydefect_util dvf -d *_*"], shell=True)
                subprocess.run(["pydefect_vasp pbes -d perfect"], shell=True)
                subprocess.run(["pydefect_vasp beoi -d *_* -pbes perfect/perfect_band_edge_state.json"], shell=True)
                subprocess.run(["pydefect bes -d *_*/ -pbes perfect/perfect_band_edge_state.json"], shell=True)

                #無添加相のdefectの情報をシンボリックリンクで持ってくる
                for defect_dir_name in calc_info["defect"].keys():
                    if not os.path.isdir(defect_dir_name):
                        subprocess.run([f"ln -s ../../defect/{defect_dir_name} ./"], shell=True)

                subprocess.run(["pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml"], shell=True)
                subprocess.run(["pydefect des -d *_*/ -u ../../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml"], shell=True)
                subprocess.run(["pydefect cs -d *_*/ -pcr perfect/calc_results.json"], shell=True)
                    
                #化学ポテンシャルの極限の条件のラベルを取得
                labels = get_label_from_chempotdiag("../cpd/chem_pot_diag.json")
                for label in labels:
                    subprocess.run([f"pydefect pe -d defect_energy_summary.json -l {label}"], shell=True)
                    pdf_to_png(f"energy_{label}.pdf", "./")
                flag = check_analysis_done("energy_A.pdf")

                os.chdir("../../")
            else:
                print(f"dopant_{dopant}'s defect calculations have not finished yet.")
                flag = False
        else:
            print(f"No such directory: defect")
            flag = False
    elif analysis_info[f"{dopant}_defect"]:
        print(f"Analysis of dopant_{dopant}'s defect has already finished.")
        flag = True
    elif not analysis_info["defect"] and analysis_info[f"{dopant}_cpd"]:
        print(f"Analysis of defect has not yet finished.")
        flag = False
    elif not analysis_info[f"{dopant}_cpd"] and analysis_info["defect"]:
        print(f"Analysis of {dopant}_cpd has not yet finished.")
        flag = False
    elif not analysis_info[f"{dopant}_cpd"] and not analysis_info["defect"]:
        print(f"Analysis of defect and {dopant}_cpd have not yet finished.")
        flag = False

    return flag

class AnalysisInfoMaker():
    def __init__(self):
        piseset = PiseSet()
        #calc_info.jsonの更新
        CalcInfoMaker()

        #analysis_target_listを作成
        analysis_target_list = ["unitcell","cpd", "defect"]
        print(piseset.dopants)
        if piseset.dopants is None:
            print("No dopant is considered.")
        else:
            for dopant in piseset.dopants:
                analysis_target_list.append(f"{dopant}_cpd")
                analysis_target_list.append(f"{dopant}_defect")

        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                #analysis_info.jsonとcalc_info.jsonの読み込み
                analysis_info = initialize_analysis_info(analysis_target_list)
                with open('calc_info.json') as f:
                    calc_info = json.load(f)

                #解析を実行
                analysis_info["unitcell"] = analysis_unitcell(piseset, calc_info, analysis_info)
                analysis_info["cpd"] = analysis_cpd(target_material, calc_info, analysis_info)
                analysis_info["defect"] = analysis_defect(calc_info, analysis_info)
                if piseset.dopants is None:
                    print("No dopant is considered.")
                else:
                    for dopant in piseset.dopants:
                        analysis_info[f"{dopant}_cpd"] = analysis_dopant_cpd(dopant, target_material, calc_info, analysis_info)
                        analysis_info[f"{dopant}_defect"] = analysis_dopant_defect(dopant, calc_info, analysis_info)
                    
                with open("analysis_info.json", "w") as f:
                    json.dump(analysis_info, f, indent=4)

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")

if __name__ == '__main__':
    print()