import json
import os

def make_dir_list():
    list = []
    for f in os.listdir("./"):
        if os.path.isdir(f):
            if not os.path.islink(f):
                list.append(f)
    return list

def get_label_from_chempotdiag(path_chem_pot_diag):
    labels = []
    with open(path_chem_pot_diag) as f:
        chem_pot = json.load(f)
    for label in chem_pot["target_vertices_dict"]:
        labels.append(label)
    return labels