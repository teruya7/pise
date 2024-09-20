import json
import os
import yaml
from collections import defaultdict
import pandas as pd
import datetime

class Collect():
    def __init__(self):
        
        home = os.environ['HOME']

        #collect_info.jsonの読み込み
        if os.path.isfile(f"{home}/managed_directories_info.json"):
            with open(f"{home}/managed_directories_info.json") as f:
                managed_directories_info = json.load(f)
        else:
            managed_directories_info = defaultdict(dict)
        
        self.managed_directories_info = managed_directories_info
        self.home = home
    
    #managed_directoryは絶対パスで指定
    def add(self,managed_directory):
        managed_directories_info = self.managed_directories_info

        with open(f"{managed_directory}/pise.yaml") as f:
            pise = yaml.safe_load(f)

        managed_directories_info[managed_directory]  = pise["functional"]

        with open(f"{self.home}/managed_directories_info.json", "w") as f:
            json.dump(managed_directories_info, f, indent=4)

    def csv(self, target_functional):
        managed_directories_info = self.managed_directories_info

        collect_info_dict = defaultdict(dict)

        for managed_directory, functional in managed_directories_info.items():
            if target_functional == functional:
                if os.path.isfile(f"{managed_directory}/markdown_info.json"):
                    with open(f"{managed_directory}/markdown_info.json") as f:
                        markdown_info = json.load(f)
                    collect_info_dict.update(markdown_info)
        
        now = datetime.datetime.now().strftime('%Y_%m_%d')
        collect_info_df = pd.DataFrame(data=collect_info_dict, index=['functional',]).T
        collect_info_df.to_csv(f"{self.home}/collect_info_{target_functional}_{now}.csv")

                