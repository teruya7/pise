from mp_api.client import MPRester
import yaml
import os
import json
from collections import defaultdict

def MPDataDoc_to_dict(MPDataDoc):
    #MPDataDocのデータの読み込み
    material_id = MPDataDoc.material_id
    formula_pretty = MPDataDoc.formula_pretty
    elements = MPDataDoc.elements

    element_list = []
    for element in elements:
        str_element = str(element)
        element_list.append(str_element)

    #MPdatadictを作成し、データを追加
    MPdatadict = defaultdict(dict)
    MPdatadict["material_id"] = material_id
    MPdatadict["formula_pretty"] = formula_pretty
    MPdatadict["elements"] = element_list
    return MPdatadict

class TargetInfoMaker():
    def __init__(self):
        self.name = "target_info.json"
        #Materials projectから取得する値を指定
        self.fields = ["material_id", "formula_pretty", "elements"]

        #pise_defaults.yamからAPIキーを読み込む
        home = home = os.environ['HOME']
        with open(f"{home}/pise/pise_defaults.yaml") as file:
            pise_defaults = yaml.safe_load(file)
            MY_API_KEY = pise_defaults["MY_API_KEY"]
            self.api_key = MY_API_KEY
        
        #target_info.jsonを読み込み
        if os.path.isfile(self.name):
            print(f"Loading {self.name}")
            with open(self.name) as f:
                target_info = json.load(f)
        else:
            print(f"Making {self.name}")
            target_info = []
        self.target_info = target_info


    def add(self, material_id):
        #Materials projectからデータを取得
        with MPRester(self.api_key) as mpr:
            MPDataDoc = mpr.summary.search(material_ids=[material_id], fields=self.fields)
        
        #MPDataDocをdictに変換
        MPdatadict = MPDataDoc_to_dict(MPDataDoc[0])

        #target_infoにデータを追加
        target_info = self.target_info
        target_info.append(MPdatadict)

        #target_info.jsonにデータを保存
        with open(self.name, "w") as f:
            json.dump(target_info, f, indent=4)
    
class TargetHandler():
    def __init__(self, target):
        self.formula_pretty = target["formula_pretty"]
        self.material_id = target["material_id"]
        self.elements = target["elements"]
        print(f"Parsing {self.formula_pretty}_{self.material_id}")
    
    def make_path(self, functional):
        path = f"{self.formula_pretty}_{self.material_id}/{functional}"
        return path
        
if __name__ == '__main__':
    print()










