import itertools
import os
import string
import subprocess
import json
import yaml
from calculation import make_dir_list
from pymatgen.core.composition import Composition
from pymatgen.core.periodic_table import Element

#preparation--------------------------------
def delete_duplication(path_to_criteria, path_to_target):
    #元のパスの記録
    cwd = os.getcwd()
    os.chdir(path_to_criteria)
    criteria_list = make_dir_list()

    os.chdir(cwd)
    os.chdir(path_to_target)
    target_list = make_dir_list()

    for i in target_list:
        if i in criteria_list:
            subprocess.run([f"rm -r {i}"], shell=True)
            print(f"{i} is duplication. So {i} has deleted.")
    os.chdir(cwd)

#analysis-----------------------------------
#unstable_errorに対処し、target_vertices.yamlを作成する
def avoid_unstable_error(flag, target_material, dopant=None):
    while not flag:
        if not os.path.isfile("unstable_error.txt"):
            subprocess.run(["touch unstable_error.txt"], shell=True)
        with open("relative_energies.yaml") as file:
            relative_energies = yaml.safe_load(file)
            try:
                relative_energies[target_material.formula_pretty] -= 0.01
            except KeyError:
                print(f"Target {target_material.formula_pretty} is not in relative energy compounds, so stop here.")
                break
        with open("relative_energies.yaml", 'w') as file:
            yaml.dump(relative_energies, file)

        if dopant is not None:
            pydefect_cv_dopant(target_material, dopant)
        else:
            subprocess.run([f"pydefect cv -t {target_material.formula_pretty}"], shell=True)

        if os.path.isfile("target_vertices.yaml"):
            flag = True

def pydefect_cv_dopant(target_material, dopant):
    elements = target_material.elements
    if len(elements) == 2:
        subprocess.run([f"pydefect cv -t {target_material.formula_pretty} -e {elements[0]} {elements[1]} {dopant}"], shell=True)
    elif len(elements) == 3:
        subprocess.run([f"pydefect cv -t {target_material.formula_pretty} -e {elements[0]} {elements[1]} {elements[2]} {dopant}"], shell=True)
    elif len(elements) == 4:
        subprocess.run([f"pydefect cv -t {target_material.formula_pretty} -e {elements[0]} {elements[1]} {elements[2]} {elements[3]} {dopant}"], shell=True)

def reduced_cpd(dopant):
    #label作成用のアルファベットのリスト
    uppercase_list = list(itertools.chain(string.ascii_uppercase,("".join(pair) for pair in itertools.product(string.ascii_uppercase, repeat=2))))
    
    with open("chem_pot_diag.json") as f:
        chem_pot_diag = json.load(f)

    #取り除くverticesをリストにまとめる
    removed_vertices = []
    for label, target_vertices_dict in chem_pot_diag["target_vertices_dict"].items():
        competing_phases_list = [Composition(competing_phases) for competing_phases in target_vertices_dict["competing_phases"]]
        for competing_phase in competing_phases_list:
            if Element(dopant) in competing_phase:
                flag = False
                break
            else:
                flag = True
                continue
        if flag:
            removed_vertices.append(label)
    
    #新しいverticesを作成する
    reduced_target_vertices_dict = {}
    n_counter = 0
    for label, target_vertices_dict in chem_pot_diag["target_vertices_dict"].items():
        if label not in removed_vertices:
            reduced_target_vertices_dict[uppercase_list[n_counter]] = target_vertices_dict
            n_counter += 1
        if label in removed_vertices:
            print(f"Removed vertices: {label}, ", "competing_phases:", target_vertices_dict["competing_phases"])

    chem_pot_diag["target_vertices_dict"] = reduced_target_vertices_dict
    with open("chem_pot_diag.json", "w") as f:
        json.dump(chem_pot_diag, f)
    

    #target_verticesを作成する
    with open("target_vertices.yaml") as f:
        target_vertices = yaml.safe_load(f)

    reduced_target_vertices = {}
    reduced_target_vertices["target"] = target_vertices["target"]
    n_counter = 0
    for label, target_vertices_dict in target_vertices.items():
        if label == "target":
            continue
        if label not in removed_vertices:
            reduced_target_vertices[uppercase_list[n_counter]] = target_vertices_dict
            n_counter += 1

    with open("target_vertices.yaml", "w") as f:
        yaml.safe_dump(reduced_target_vertices, f, sort_keys=False)

def get_label_from_chempotdiag(path_chem_pot_diag):
    labels = []
    with open(path_chem_pot_diag) as f:
        chem_pot = json.load(f)
    for label in chem_pot["target_vertices_dict"]:
        labels.append(label)
    return labels
