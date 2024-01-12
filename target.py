from mp_api.client import MPRester
import yaml
import os
import json
import pandas as pd
from collections import defaultdict
from pise_set import PiseSet

def MPDataDoc_to_dict(MPDataDoc):
    #MPDataDocのデータの読み込み
    material_id = MPDataDoc.material_id
    formula_pretty = MPDataDoc.formula_pretty
    elements = MPDataDoc.elements
    composition_reduced = MPDataDoc.composition_reduced
    symmetry = MPDataDoc.symmetry

    element_list = []
    for element in elements:
        str_element = str(element)
        element_list.append(str_element)

    #MPdatadictを作成し、データを追加
    MPdatadict = defaultdict(dict)
    MPdatadict["material_id"] = material_id

    if "(" in formula_pretty:
        MPdatadict["formula_pretty"] = composition_reduced.alphabetical_formula.replace(" ", "")
        MPdatadict["name"] = formula_pretty
    else:
        MPdatadict["formula_pretty"] = formula_pretty

    MPdatadict["elements"] = element_list
    MPdatadict["symmetry"] = str(symmetry.symbol)

    return MPdatadict

class Target():
    def __init__(self):
        self.piseset = PiseSet()
        #Materials projectから取得する値を指定
        self.fields = ["material_id", "formula_pretty", "elements", "composition_reduced", "symmetry"]

        #pise_defaults.yamからAPIキーを読み込む
        home = home = os.environ['HOME']
        with open(f"{home}/.pise_defaults.yaml") as file:
            pise_defaults = yaml.safe_load(file)
            MY_API_KEY = pise_defaults["MY_API_KEY"]
            self.api_key = MY_API_KEY
        
        #target_info.jsonを読み込み
        if os.path.isfile("target_info.json"):
            print("Loading target_info.json")
            with open("target_info.json") as f:
                target_info = json.load(f)
        else:
            print("Making target_info.json")
            target_info = []
        self.target_info = target_info

        #target_summary_info.jsonで計算対象物質を一元管理し、重複をなくす
        if os.path.isfile(f"{self.piseset.path_to_target_summary}/target_summary_info.json"):
            with open(f"{self.piseset.path_to_target_summary}/target_summary_info.json") as f:
                target_summary_info = json.load(f)
        else:
            target_summary_info = defaultdict(dict)
        self.target_summary_info = target_summary_info


    def add(self, material_id):
        #Materials projectからデータを取得
        with MPRester(self.api_key) as mpr:
            MPDataDoc = mpr.summary.search(material_ids=[material_id], fields=self.fields)
        
        #MPDataDocをdictに変換
        MPdatadict = MPDataDoc_to_dict(MPDataDoc[0])

        #symmetry情報をsymmetry_info.jsonに保存
        if os.path.isfile("symmetry_info.json"):
            with open('symmetry_info.json') as f:
                symmetry_info = json.load(f)
        else:
            symmetry_info = defaultdict(dict)
        symmetry_info[material_id] = MPdatadict["symmetry"]
        with open("symmetry_info.json", "w") as f:
            json.dump(symmetry_info, f, indent=4)


        #target_infoにデータを追加
        target_info = self.target_info
        target_summary_info = self.target_summary_info
        material_id = MPdatadict["material_id"]
        formula_pretty = MPdatadict["formula_pretty"]
        
        try:
            if not material_id in target_summary_info.keys():
                target_summary_info[material_id] = formula_pretty
                target_info.append(MPdatadict)
            else:
                print("This target has already been considered.")
        except KeyError:
            target_summary_info[material_id] = formula_pretty
            target_info.append(MPdatadict)

        #target_info.jsonにデータを保存
        with open("target_info.json", "w") as f:
            json.dump(target_info, f, indent=4)
        
        with open(f"{self.piseset.path_to_target_summary}/target_summary_info.json", "w") as f:
            json.dump(target_summary_info, f, indent=4)


    def add_escape(self, material_id):
            #Materials projectからデータを取得
            with MPRester(self.api_key) as mpr:
                MPDataDoc = mpr.summary.search(material_ids=[material_id], fields=self.fields)
            
            #MPDataDocをdictに変換
            MPdatadict = MPDataDoc_to_dict(MPDataDoc[0])

            #symmetry情報をsymmetry_info.jsonに保存
            if os.path.isfile("symmetry_info.json"):
                with open('symmetry_info.json') as f:
                    symmetry_info = json.load(f)
            else:
                symmetry_info = defaultdict(dict)
            symmetry_info[material_id] = MPdatadict["symmetry"]
            with open("symmetry_info.json", "w") as f:
                json.dump(symmetry_info, f, indent=4)


            #target_infoにデータを追加
            target_info = self.target_info
            target_info.append(MPdatadict)

            #target_info.jsonにデータを保存
            with open("target_info.json", "w") as f:
                json.dump(target_info, f, indent=4)
    

class TargetHandler():
    def __init__(self, target):
        self.formula_pretty = target["formula_pretty"]
        self.material_id = target["material_id"]
        self.elements = target["elements"]
        try:
            self.name = target["name"]
        except KeyError:
            pass
        print()
        print(f"Parsing {self.formula_pretty}_{self.material_id}")
    
    def make_path(self, functional):
        path = f"{self.formula_pretty}_{self.material_id}/{functional}"
        return path
        
if __name__ == '__main__':
    pass










