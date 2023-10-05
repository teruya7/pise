from pise_set import PiseSet
from target import TargetHandler
import os
import yaml

def get_dopants_list():
    dopants = []
    with open("pise_dopants_and_sites.yaml") as file:
        pise_dopants_and_sites = yaml.safe_load(file)
    for dopant_and_site in pise_dopants_and_sites["dopants_and_sites"]:
        dopants.append(dopant_and_site[0])
    return dopants

class Doping():
    def __init__(self):
        pass

    def add(self, dopant, substitutional_site = None):
        piseset = PiseSet()
        for target in piseset.target_info:
            target_material = TargetHandler(target)
            path = target_material.make_path(piseset.functional)
            if os.path.isdir(path):
                os.chdir(path)

                if os.path.isfile("pise_dopants_and_sites.yaml"):
                    with open("pise_dopants_and_sites.yaml") as file:
                        pise_dopants_and_sites = yaml.safe_load(file)
                else:
                    pise_dopants_and_sites = {"dopants_and_sites": []}
                
                #置換サイトの指定がない時は全てのサイトを置換サイトにする
                if substitutional_site is None:
                    for element in target_material.elements:
                        #重複を防ぐ
                        if not [dopant, substitutional_site] in pise_dopants_and_sites["dopants_and_sites"]:
                            pise_dopants_and_sites["dopants_and_sites"].append([dopant, element])

                        with open("pise_dopants_and_sites.yaml", "w") as f:
                            yaml.dump(pise_dopants_and_sites, f, sort_keys=False)
                else:
                    if substitutional_site in target_material.elements:
                        #重複を防ぐ
                        if not [dopant, substitutional_site] in pise_dopants_and_sites["dopants_and_sites"]:
                            pise_dopants_and_sites["dopants_and_sites"].append([dopant, substitutional_site])

                        with open("pise_dopants_and_sites.yaml", "w") as f:
                            yaml.dump(pise_dopants_and_sites, f, sort_keys=False)
                    else:
                        print(f"No substitutional sites: {substitutional_site} exists in {target_material.formula_pretty}")

                os.chdir("../../")
            else:
                print(f"No such directory: {path}")
                